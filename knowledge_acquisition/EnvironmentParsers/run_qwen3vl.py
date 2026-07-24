"""
run_qwen3vl.py
==============
UI element extraction with Qwen3-VL.

Note on the model ID
--------------------
You asked for "Qwen 3.6 27B". Two things to flag:

1. The Qwen3.6 family released so far (Qwen3.6-27B, Qwen3.6-35B-A3B) are
   **text-only** language models. They have no vision encoder, so they
   cannot see screenshots and cannot replace Gemini on this task.

2. The vision-language line in the same generation is **Qwen3-VL**. The
   closest analogue to "27B" with vision is **Qwen3-VL-30B-A3B-Instruct**:
   ~31B total parameters, ~3B active per token (MoE), GUI-grounding
   capabilities trained in. It is also explicitly recommended for "PC/mobile
   GUI element recognition", which is exactly what the original Gemini script
   was doing.

So this script defaults to Qwen3-VL-30B-A3B-Instruct. If you literally need
Qwen3.6-27B for some reason, that model cannot do this task -- use a text-only
caption produced upstream and feed it to Qwen3.6 instead.

Optimal stack on H100 (no flash-attn)
-------------------------------------
Same as the other two scripts:
    vLLM + xformers attention backend + bf16 (or FP8 weights for ~1.6x more
    tok/s if you're memory-bound) + prefix caching + guided JSON.

We pin vLLM to xformers via the VLLM_ATTENTION_BACKEND env var at module
import time so nothing tries to dlopen flash-attn (which is painful to build
on Colab).

For *peak* throughput on a single H100, use the FP8 checkpoint:
    --model Qwen/Qwen3-VL-30B-A3B-Instruct-FP8
The FP8 version is W8A8 block-wise, fits in ~32 GB, and runs faster than bf16
on Hopper. Quality on UI grounding is essentially identical to bf16.

Setup (Colab)
-------------
    !pip install -q --upgrade "vllm>=0.7.3" "transformers>=4.57.0" \
                              "qwen-vl-utils>=0.0.14" pillow pydantic
    # Do NOT install flash-attn -- xformers ships with vLLM.
"""

from __future__ import annotations

import argparse
import os
import time
from typing import Any

# IMPORTANT: pin vLLM to xformers BEFORE importing it. xformers ships with vLLM
# wheels, so this avoids the flash-attn compile dance on Colab.
os.environ.setdefault("VLLM_ATTENTION_BACKEND", "XFORMERS")

from PIL import Image

from common import (
    PROMPT,
    UIAnalysis,
    annotate_and_save,
    discover_images,
    extract_json,
    load_image,
)


def _import_vllm():
    from vllm import LLM, SamplingParams  # type: ignore
    try:
        from vllm.sampling_params import GuidedDecodingParams  # type: ignore
    except ImportError:  # pragma: no cover
        GuidedDecodingParams = None
    return LLM, SamplingParams, GuidedDecodingParams


def build_llm(model_id: str, max_model_len: int):
    LLM, _, _ = _import_vllm()
    print(f"[Qwen3-VL] Loading {model_id} with vLLM ...")
    llm = LLM(
        model=model_id,
        dtype="bfloat16",  # Ignored if the checkpoint is FP8 -- vLLM picks FP8 automatically.
        trust_remote_code=True,
        max_model_len=max_model_len,
        tensor_parallel_size=1,
        limit_mm_per_prompt={"image": 1},
        # 30B-A3B in bf16 is ~62 GB; pushing utilization higher leaves room for KV.
        gpu_memory_utilization=0.92,
        enable_prefix_caching=True,
    )
    print("[Qwen3-VL] Model loaded.")
    return llm


def build_sampling_params(max_new_tokens: int):
    _, SamplingParams, GuidedDecodingParams = _import_vllm()
    guided = None
    if GuidedDecodingParams is not None:
        guided = GuidedDecodingParams(json=UIAnalysis.model_json_schema())
    return SamplingParams(
        temperature=0.0,
        top_p=1.0,
        max_tokens=max_new_tokens,
        guided_decoding=guided,
    )


def make_messages(image: Image.Image) -> list[dict[str, Any]]:
    # Qwen3-VL chat template -- vLLM's llm.chat() applies it internally.
    return [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": PROMPT},
            ],
        }
    ]


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--model",
        default="Qwen/Qwen3-VL-30B-A3B-Instruct",
        help=(
            "HF id of a Qwen3-VL checkpoint with vision. "
            "For ~1.6x more tok/s on H100, use Qwen/Qwen3-VL-30B-A3B-Instruct-FP8. "
            "For a smaller, faster model use Qwen/Qwen3-VL-8B-Instruct."
        ),
    )
    p.add_argument("--input_dir", default="Dismal")
    p.add_argument("--annotated_dir", default="Dismal_annotated_qwen3vl")
    p.add_argument("--json_dir", default="Dismal_json_qwen3vl")
    p.add_argument("--filter", default="step0")
    p.add_argument("--max_model_len", type=int, default=8192)
    p.add_argument("--max_new_tokens", type=int, default=2048)
    args = p.parse_args()

    image_paths = discover_images(args.input_dir, args.filter)
    if not image_paths:
        print(f"No matching images in '{args.input_dir}' (filter={args.filter!r}).")
        return
    print(f"[Qwen3-VL] Found {len(image_paths)} image(s).")

    llm = build_llm(args.model, args.max_model_len)
    sp = build_sampling_params(args.max_new_tokens)

    images = [load_image(pth) for pth in image_paths]
    batched_messages = [make_messages(img) for img in images]

    t0 = time.time()
    outputs = llm.chat(
        messages=batched_messages,
        sampling_params=sp,
        use_tqdm=True,
    )
    dt = time.time() - t0

    total_completion_tokens = 0
    for path, img, out in zip(image_paths, images, outputs):
        filename = os.path.basename(path)
        base = os.path.splitext(filename)[0]
        text = out.outputs[0].text
        total_completion_tokens += len(out.outputs[0].token_ids)

        try:
            data = extract_json(text)
        except Exception as e:
            print(f"[Qwen3-VL] {filename}: JSON extraction failed ({e}).")
            print(f"           raw output: {text[:300]}")
            continue

        annotate_and_save(img, data, base, args.annotated_dir, args.json_dir)

    print(
        f"[Qwen3-VL] Done. {len(image_paths)} images in {dt:.1f}s "
        f"({total_completion_tokens} completion tokens, "
        f"{total_completion_tokens / max(dt, 1e-6):.1f} tok/s)."
    )


if __name__ == "__main__":
    main()

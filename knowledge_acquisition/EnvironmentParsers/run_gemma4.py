"""
run_gemma4.py
=============
UI element extraction with Google Gemma 4 (multimodal).

Note on the model ID
--------------------
You asked for "Gemma 4 8B". Google did not ship an 8B variant of Gemma 4 -- the
released sizes are E2B, E4B, 26B-A4B (MoE, ~4B active), and 31B (dense).
The closest match to "8B" by RAM footprint at bf16 is **Gemma 4 E4B** (~4B
effective parameters, full multimodal, 128K context). It is the natural pick
for a single-H100 throughput run.

If you really want a heavier model, swap --model for one of:
    google/gemma-4-26b-a4b-it    # MoE, ~3.8B active, fits comfortably
    google/gemma-4-31b-it        # dense, fits in bf16 on a single H100 (~62 GB)

Optimal stack on H100 (no flash-attn)
-------------------------------------
Same as the EGM script: vLLM + xformers attention backend + bf16 + prefix
caching + guided JSON. Gemma 4 explicitly supports vLLM in its release notes,
and Gemma's image tokens are packed efficiently (variable resolution) so we
keep gpu_memory_utilization high.

We pin vLLM to xformers via the VLLM_ATTENTION_BACKEND env var at module
import time so nothing in the pipeline tries to load a flash-attn wheel.

Setup (Colab)
-------------
    !pip install -q --upgrade "vllm>=0.7.3" "transformers>=4.57.0" pillow pydantic
    # Do NOT install flash-attn -- xformers ships with vLLM.
    # Gemma 4 is gated. Either log in:
    #   from huggingface_hub import login; login()
    # or set HF_TOKEN in the env before running:
    #   os.environ['HF_TOKEN'] = '...'
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
    print(f"[Gemma4] Loading {model_id} with vLLM ...")
    llm = LLM(
        model=model_id,
        dtype="bfloat16",
        trust_remote_code=True,
        max_model_len=max_model_len,
        tensor_parallel_size=1,
        limit_mm_per_prompt={"image": 1},
        gpu_memory_utilization=0.90,
        enable_prefix_caching=True,
    )
    print("[Gemma4] Model loaded.")
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
    # Gemma 4 uses the standard "user" role with mixed content blocks.
    # vLLM's chat path handles the Gemma chat template internally.
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
    # E4B = closest fit to the "8B" you asked for. Keep it gated-friendly:
    p.add_argument("--model", default="google/gemma-4-E4B-it",
                   help="HF id of the Gemma 4 checkpoint (default: gemma-4-E4B-it).")
    p.add_argument("--input_dir", default="Dismal")
    p.add_argument("--annotated_dir", default="Dismal_annotated_gemma4")
    p.add_argument("--json_dir", default="Dismal_json_gemma4")
    p.add_argument("--filter", default="step0")
    p.add_argument("--max_model_len", type=int, default=8192)
    p.add_argument("--max_new_tokens", type=int, default=2048)
    args = p.parse_args()

    image_paths = discover_images(args.input_dir, args.filter)
    if not image_paths:
        print(f"No matching images in '{args.input_dir}' (filter={args.filter!r}).")
        return
    print(f"[Gemma4] Found {len(image_paths)} image(s).")

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
            print(f"[Gemma4] {filename}: JSON extraction failed ({e}).")
            print(f"         raw output: {text[:300]}")
            continue

        annotate_and_save(img, data, base, args.annotated_dir, args.json_dir)

    print(
        f"[Gemma4] Done. {len(image_paths)} images in {dt:.1f}s "
        f"({total_completion_tokens} completion tokens, "
        f"{total_completion_tokens / max(dt, 1e-6):.1f} tok/s)."
    )


if __name__ == "__main__":
    main()

"""
run_egm.py
==========
UI element extraction with NVIDIA EGM (Efficient visual Grounding Models).

EGM is a family of small VLMs that NVIDIA fine-tuned on top of InternVL-3 and
Qwen3-VL specifically for visual grounding. The 8B Qwen3-VL variant matches the
quality of Qwen3-VL-235B on RefCOCO at roughly 6x lower latency, which makes it
the right pick for high-throughput UI element extraction on a single H100.

Optimal stack on H100 (highest tok/s for this workload, no flash-attn)
----------------------------------------------------------------------
* vLLM 0.7+   -> PagedAttention, CUDA graphs, continuous batching
* xformers    -> attention backend (ships pre-built; no flash-attn compile pain)
* bfloat16    -> H100 native; matches release weights without extra calibration
* prefix cache -> the system prompt + schema is identical for every image,
                 so vLLM's automatic prefix caching gives a big win
* guided JSON  -> grammar-constrained decoding skips invalid tokens entirely,
                 which both removes JSON-parse failures and reduces wasted tokens
* async batch  -> we submit all images concurrently; vLLM's continuous batching
                 packs them onto the GPU more densely than a Python for-loop

We force the xformers attention backend via the VLLM_ATTENTION_BACKEND env var
*before* importing vLLM, so nothing in this pipeline tries to dlopen a
flash-attn wheel.

Colab setup (one-time, see colab_setup.ipynb in this folder)
------------------------------------------------------------
    !pip install -q --upgrade "vllm>=0.7.3" "transformers>=4.57.0" \
                              "qwen-vl-utils>=0.0.14" pillow pydantic
    # NOTE: do NOT install flash-attn. xformers comes with vLLM.

Then run:
    !python run_egm.py --input_dir Dismal \
                       --annotated_dir Dismal_annotated_egm \
                       --json_dir Dismal_json_egm
"""

from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any

# IMPORTANT: must be set BEFORE vLLM is imported anywhere in the process.
# This pins vLLM to the xformers attention kernels, which ship with vLLM's
# wheels and do not require building flash-attn (which is painful on Colab).
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

# vLLM is heavy; import lazily so --help works without GPU.
def _import_vllm():
    from vllm import LLM, SamplingParams  # type: ignore
    try:
        # Newer vLLM
        from vllm.sampling_params import GuidedDecodingParams  # type: ignore
    except ImportError:  # pragma: no cover
        GuidedDecodingParams = None
    return LLM, SamplingParams, GuidedDecodingParams


# ---------------------------------------------------------------------------
# vLLM model setup
# ---------------------------------------------------------------------------
def build_llm(model_id: str, max_model_len: int):
    LLM, _, _ = _import_vllm()
    print(f"[EGM] Loading {model_id} with vLLM ...")
    llm = LLM(
        model=model_id,
        dtype="bfloat16",
        trust_remote_code=True,
        max_model_len=max_model_len,
        # Single H100 = single GPU; tensor_parallel_size=1 keeps overhead minimal
        tensor_parallel_size=1,
        # Limit per-request image count; we send one image per request
        limit_mm_per_prompt={"image": 1},
        # Headroom for KV cache; H100 80 GB handles 0.90 fine for an 8B model
        gpu_memory_utilization=0.90,
        # Prefix caching is the single biggest knob for this workload because
        # every request shares the same long instruction prefix.
        enable_prefix_caching=True,
    )
    print("[EGM] Model loaded.")
    return llm


def build_sampling_params(max_new_tokens: int):
    from vllm import SamplingParams  # type: ignore
    schema = UIAnalysis.model_json_schema()

    # Try the new API first (vLLM >= ~0.10/0.20 V1 engine):
    # SamplingParams(structured_outputs=StructuredOutputsParams(json=...))
    try:
        from vllm.sampling_params import StructuredOutputsParams  # type: ignore
        return SamplingParams(
            temperature=0.0,
            top_p=1.0,
            max_tokens=max_new_tokens,
            structured_outputs=StructuredOutputsParams(json=schema),
        )
    except ImportError:
        pass

    # Older API: SamplingParams(guided_decoding=GuidedDecodingParams(json=...))
    try:
        from vllm.sampling_params import GuidedDecodingParams  # type: ignore
        return SamplingParams(
            temperature=0.0,
            top_p=1.0,
            max_tokens=max_new_tokens,
            guided_decoding=GuidedDecodingParams(json=schema),
        )
    except (ImportError, TypeError):
        pass

    # Last resort: no schema enforcement. extract_json() will still try to recover.
    print("[EGM] Warning: no structured-output API found in this vLLM build; "
          "falling back to free-form decoding.")
    return SamplingParams(
        temperature=0.0,
        top_p=1.0,
        max_tokens=max_new_tokens,
    )



# ---------------------------------------------------------------------------
# Per-image request construction (Qwen3-VL chat template)
# ---------------------------------------------------------------------------
import base64
import io

def _pil_to_data_uri(img: Image.Image) -> str:
    buf = io.BytesIO()
    # Use the image's existing mode where possible; convert palette/alpha-only modes for PNG safety
    if img.mode not in ("RGB", "RGBA", "L"):
        img = img.convert("RGB")
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def make_request(image: Image.Image) -> dict[str, Any]:
    """Build a vLLM chat-style request for a single image."""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": _pil_to_data_uri(image)},
                },
                {"type": "text", "text": PROMPT},
            ],
        }
    ]
    return {"messages": messages}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="nvidia/EGM-8B-SFT",
                   help="HF id of the EGM checkpoint (default: EGM-Qwen3-VL-8B).")
    p.add_argument("--input_dir", default="Dismal")
    p.add_argument("--annotated_dir", default="Dismal_annotated_egm")
    p.add_argument("--json_dir", default="Dismal_json_egm")
    p.add_argument("--filter", default="step0",
                   help="Substring required in filename. Pass '' to disable.")
    p.add_argument("--max_model_len", type=int, default=8192)
    p.add_argument("--max_new_tokens", type=int, default=2048)
    args = p.parse_args()

    image_paths = discover_images(args.input_dir, args.filter)
    if not image_paths:
        print(f"No matching images in '{args.input_dir}' (filter={args.filter!r}).")
        return
    print(f"[EGM] Found {len(image_paths)} image(s).")

    llm = build_llm(args.model, args.max_model_len)
    sp = build_sampling_params(args.max_new_tokens)

    # Pre-load all PIL images, then submit the whole batch to vLLM at once.
    # vLLM's continuous batching packs them automatically; this is the
    # throughput-optimal pattern on a single H100.
    images = [load_image(pth) for pth in image_paths]
    batch = [make_request(img) for img in images]

    t0 = time.time()
    # llm.chat() handles the per-model chat template internally and accepts
    # a list of message lists for batched inference.
    outputs = llm.chat(
        messages=[req["messages"] for req in batch],
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
            print(f"[EGM] {filename}: JSON extraction failed ({e}).")
            print(f"      raw output: {text[:300]}")
            continue

        annotate_and_save(img, data, base, args.annotated_dir, args.json_dir)

    print(
        f"[EGM] Done. {len(image_paths)} images in {dt:.1f}s "
        f"({total_completion_tokens} completion tokens, "
        f"{total_completion_tokens / max(dt, 1e-6):.1f} tok/s)."
    )


if __name__ == "__main__":
    main()

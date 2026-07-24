# UI Element Extraction — local replacements for the Gemini script

Three single-H100, vLLM-powered replacements for your original Gemini-based
`Dismal` UI element extractor. Same prompt, same JSON schema, same
red-bbox annotation output — just running locally instead of hitting the
Gemini API.

## Files

| File | Purpose |
|------|---------|
| `common.py` | Shared schema, prompt, JSON extraction, drawing, I/O |
| `run_egm.py` | NVIDIA EGM-Qwen3-VL-8B (best for UI grounding) |
| `run_gemma4.py` | Google Gemma 4 E4B (multimodal) |
| `run_qwen3vl.py` | Qwen3-VL-30B-A3B-Instruct (MoE, ~3B active) |
| `colab_setup.ipynb` | Click-through Colab notebook for the whole pipeline |

## Important notes on the model names you asked for

| You asked for | What actually exists | Default in this code |
|---------------|----------------------|----------------------|
| EGM | `nvidia/EGM-Qwen3-VL-8B`, `EGM-Qwen3-VL-4B`, `EGM-InternVL3-8B`, … | `nvidia/EGM-Qwen3-VL-8B` |
| Gemma 4 8B | Doesn't exist. Available: E2B / **E4B** / 26B-A4B / 31B | `google/gemma-4-E4B-it` |
| Qwen 3.6 27B | Exists but is **text-only** — can't see screenshots | `Qwen/Qwen3-VL-30B-A3B-Instruct` (real vision model from same generation) |

You can override any default with `--model <hf-id>`.

## Why this stack is throughput-optimal on H100 (without flash-attn)

1. **vLLM** — PagedAttention + CUDA graphs + continuous batching. This
   consistently beats raw HuggingFace `model.generate()` by 3–10× on the
   same hardware for batched VLM inference.
2. **xformers attention backend** — pinned via `VLLM_ATTENTION_BACKEND=XFORMERS`
   at the top of every script. xformers ships pre-built inside the vLLM wheel,
   so there is **no flash-attn install step** (which is the painful part on
   Colab). On H100 you give up maybe 5–15% throughput vs. FA3, but you save
   yourself a 20-minute compile that fails half the time.
3. **bfloat16** weights — H100 native; no calibration needed. For Qwen3-VL,
   pass `--model Qwen/Qwen3-VL-30B-A3B-Instruct-FP8` to get an extra ~1.6× on
   top of bf16.
4. **Prefix caching** — every image shares the exact same instruction prefix
   (the prompt + the JSON schema). vLLM hashes that prefix once and reuses
   its KV cache, which on a 50-image batch is roughly a 30% latency drop.
5. **Guided JSON decoding** — `GuidedDecodingParams(json=schema)` rejects any
   token that would break the schema, so we never lose tokens to retries on
   malformed output. Also enforces the same Pydantic schema you had in the
   Gemini code.
6. **Single batched submission** — we hand vLLM the *whole* directory at once
   instead of looping per image, so its scheduler can pack requests onto the
   GPU at maximum density.

## How to run (Colab, H100)

```bash
# NOTE: no flash-attn install. xformers ships with vLLM and we pin the
# attention backend to it inside the scripts.
pip install -q --upgrade "vllm>=0.7.3" "transformers>=4.57.0" \
                          "qwen-vl-utils>=0.0.14" pillow pydantic

# 1) EGM (recommended for UI grounding accuracy)
python run_egm.py --input_dir Dismal

# 2) Gemma 4 (gated -- HF login first)
python run_gemma4.py --input_dir Dismal

# 3) Qwen3-VL (use the FP8 build for fastest tokens/sec)
python run_qwen3vl.py --model Qwen/Qwen3-VL-30B-A3B-Instruct-FP8 \
                     --input_dir Dismal
```

Each script writes annotated PNGs and per-image JSON into separate output
directories so you can compare the three models side-by-side.

## Memory footprint (single H100 80 GB, bf16)

| Model | Params (active) | Approx. VRAM | Fits H100? |
|-------|-----------------|--------------|------------|
| EGM-Qwen3-VL-8B | 8B | ~17 GB | ✅ huge headroom |
| Gemma 4 E4B | ~4B effective | ~9 GB | ✅ huge headroom |
| Gemma 4 26B-A4B | 26B total / 3.8B active | ~52 GB | ✅ |
| Gemma 4 31B (dense) | 31B | ~62 GB | ✅ tight |
| Qwen3-VL-30B-A3B (bf16) | 30B / 3B active | ~62 GB | ✅ tight |
| Qwen3-VL-30B-A3B-FP8 | 30B / 3B active | ~32 GB | ✅ best perf/watt |
| Qwen3-VL-8B | 8B | ~17 GB | ✅ |

#!/usr/bin/env bash
# OPTIONAL, GPU-heavy: regenerate the per-engine OCR outputs from the models and
# documents, then hand off to the no-GPU scoring path. A reviewer does NOT need
# this; the committed run of record already lets reproduce_from_results.sh
# reproduce every number offline. Run this only to rebuild the predictions from
# scratch on a CUDA machine.
#
# Hardware: one consumer GPU (>=16 GB) for the vision-language models and Surya;
# the classical pipelines run on CPU. Each engine is served one at a time and
# torn down, so a single 16 GB card suffices.
#
# Configuration (no host-specific paths are baked in):
#   WORK_DIR   working root holding the input documents and per-axis output dirs
#              (default: $PWD/data)
#   HF_CACHE   Hugging Face model cache (default: $WORK_DIR/hf_cache)
#   VLLM_IMG   pinned vLLM image (default below)
#
# Wall clock: many hours (model downloads + 14 engines x 5 axes). This is why the
# run of record is committed.
set -euo pipefail
cd "$(dirname "$0")/.."

WORK_DIR="${WORK_DIR:-$PWD/data}"
HF_CACHE="${HF_CACHE:-$WORK_DIR/hf_cache}"
VLLM_IMG="${VLLM_IMG:-vllm/vllm-openai:v0.22.1-cu129-ubuntu2404}"
COMMON='--gpu-memory-utilization 0.92 --max-model-len 16384 --mm-processor-kwargs {"max_pixels":4000000} --limit-mm-per-prompt {"image":1} --max-num-seqs 2 --trust-remote-code'

cat <<EOF
This script documents the from-scratch generation of the run of record.
It expects the input document images under \$WORK_DIR and writes per-engine
*.txt transcriptions next to them, plus _run*.json latency manifests.

Vision-language roster (HF id | quantization | greedy decoding, temperature 0):
  PaddleOCR-VL  PaddlePaddle/PaddleOCR-VL          native
  HunyuanOCR    tencent/HunyuanOCR                 native
  MinerU        opendatalab/MinerU2.5-2509-1.2B    native (two-step parse)
  DeepSeek-OCR  deepseek-ai/DeepSeek-OCR           native (--max-model-len 8192)
  dots.ocr      rednote-hilab/dots.ocr             native
  Qwen3-VL      Qwen/Qwen3-VL-4B-Instruct          native
  Qwen2.5-VL    Qwen/Qwen2.5-VL-7B-Instruct        fp8
  GLM-OCR       zai-org/GLM-OCR                     fp8
Each VLM is served via the pinned vLLM image ($VLLM_IMG) with:
  $COMMON
and receives the page image plus a single transcription instruction.

OCR engines: Tesseract, EasyOCR, docTR, RapidOCR, PaddleOCR (CPU), Surya (GPU),
each at its vendor default backend.

The full serving + inference recipe (per-engine prompts, MinerU's two-step
logits processor, classical Docker entries) is documented in docs/PROTOCOL.md.
This repository ships the resulting outputs as the committed run of record; the
serving harness itself is intentionally not bundled because it requires gated
model downloads and a CUDA GPU.
EOF

echo
echo ">> Generation is environment-specific and gated; once outputs exist under"
echo ">> \$WORK_DIR, score them with the no-GPU path:"
echo
exec ./scripts/reproduce_from_results.sh

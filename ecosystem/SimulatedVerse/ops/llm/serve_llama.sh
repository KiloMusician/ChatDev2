#!/usr/bin/env bash
set -euo pipefail
PORT="${PORT:-11434}"
MODEL_PATH="${MODEL_PATH:-models/ggml-model.gguf}"

if [ ! -f "$MODEL_PATH" ]; then
  echo "Model missing at $MODEL_PATH"; exit 2
fi

# build llama.cpp in userland if needed
if [ ! -x "./llama.cpp/server" ]; then
  git clone --depth=1 https://github.com/ggerganov/llama.cpp || true
  make -C llama.cpp -j server
fi

echo "Starting llama.cpp server on :$PORT"
OPENAI_API_KEY=dummy \
llama.cpp/server -m "$MODEL_PATH" -c 4096 --host 127.0.0.1 --port "$PORT"
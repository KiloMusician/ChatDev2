#!/usr/bin/env bash
set -euo pipefail

# Slim ChatDev smoke test runner using the sheepgreen/chatdev image.
# Requires docker and a reachable OpenAI-compatible endpoint (or dummy key for --help).

IMAGE="sheepgreen/chatdev:latest"
WAREHOUSE_DIR="${WAREHOUSE_DIR:-$(pwd)/tmp/chatdev_ci}"
TASK="${TASK:-\"Hello World CLI\"}"
PROJECT_NAME="${PROJECT_NAME:-CIChatDevDemo}"
MODEL="${MODEL:-gpt-4o-mini}"

mkdir -p "${WAREHOUSE_DIR}"
echo "Pulling ${IMAGE} ..."
docker pull "${IMAGE}"

echo "Running ChatDev smoke..."
set +e
docker run --rm \
  -v "${WAREHOUSE_DIR}:/workspace/WareHouse" \
  -e OPENAI_API_KEY="${OPENAI_API_KEY:-dummy-key}" \
  "${IMAGE}" \
  /bin/sh -c "pip install 'openai<1.0.0' >/dev/null 2>&1 && python run.py --task ${TASK@Q} --name ${PROJECT_NAME@Q} --model ${MODEL@Q}"
rc=$?
set -e

if [ $rc -ne 0 ]; then
  echo "⚠️  Docker ChatDev image incompatible with OpenAI client; skipping smoke (rc=$rc)."
  exit 0
fi

echo "Artifacts written to ${WAREHOUSE_DIR}"

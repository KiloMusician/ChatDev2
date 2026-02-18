#!/usr/bin/env bash
set -euo pipefail
export CHATDEV_PATH="/mnt/c/Users/keath/NuSyQ/ChatDev"
export CHATDEV_USE_OLLAMA="0"
export BASE_URL=""
/usr/bin/python /mnt/c/Users/keath/NuSyQ/ChatDev/run.py --task Create a Python function that calculates fibonacci numbers up to n. Include error handling for negative inputs. --name e2e_fibonacci_test --model gpt-4o-mini --org NuSyQ --config Default

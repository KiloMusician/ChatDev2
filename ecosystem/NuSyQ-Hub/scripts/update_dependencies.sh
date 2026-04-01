#!/usr/bin/env bash
# Update and lock project dependencies
set -e

pip install --quiet --upgrade pip pip-tools

# Update core requirements from pyproject
pip-compile --upgrade pyproject.toml -o requirements.txt

# Update dev requirements
pip-compile --extra dev --upgrade pyproject.toml -o requirements-dev.txt

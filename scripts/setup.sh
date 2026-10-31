#!/usr/bin/env bash
set -euo pipefail
GEMMA_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$GEMMA_ROOT"
if ! command -v uv >/dev/null; then
    echo 'uv is required: https://docs.astral.sh/uv/getting-started/installation/' >&2
    exit 1
fi
# Pinned scikit-learn has no wheels for Python 3.14 or newer.
uv venv --allow-existing --python 3.13 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python scripts/bootstrap.py "$@"

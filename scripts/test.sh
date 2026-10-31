#!/usr/bin/env bash
set -euo pipefail
GEMMA_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$GEMMA_ROOT"
# macOS temp folders are symlinks; tests compare fully resolved paths.
export TMPDIR="$(cd -- "${TMPDIR:-/tmp}" && pwd -P)"
export QT_QPA_PLATFORM=offscreen OPENBLAS_NUM_THREADS=4 OMP_NUM_THREADS=4
export NUMBA_CACHE_DIR="$GEMMA_ROOT/.local/numba-cache"
status=0
./scripts/python.sh -m unittest discover -s archivio_gemma/tests -v || status=1
./scripts/python.sh -m unittest discover -s video_gemma/tests -v || status=1
exit "$status"

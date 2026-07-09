#!/usr/bin/env bash
# Run the same gates as .github/workflows/ci.yml locally.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
PY="${ROOT}/venv/bin/python"
if [[ ! -x "${PY}" ]]; then
  PY=python3
fi
exec "${PY}" scripts/ci_check.py all

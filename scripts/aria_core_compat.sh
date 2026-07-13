#!/usr/bin/env bash
# Aria Core Phase 1 behavioral compatibility harness.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
export JARVIS_NLU_SKIP_BENCHMARK="${JARVIS_NLU_SKIP_BENCHMARK:-1}"
PY="${ROOT}/venv/bin/python"
if [[ ! -x "${PY}" ]]; then
  PY=python3
fi
exec "${PY}" "${ROOT}/scripts/aria_core_compat.py"

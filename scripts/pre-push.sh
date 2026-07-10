#!/usr/bin/env bash
# Pre-push validation for Aria — mirrors GitHub Actions with extended lint/format.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
AI_PLATFORM="${AI_PLATFORM:-$(cd "${ROOT}/.." && pwd)/AI-Platform}"
export AI_ROOT="${AI_ROOT:-/tmp/aria-ci-test}"
export JARVIS_NLU_SKIP_BENCHMARK=1
export MISSION_CONTROL_HOST=127.0.0.1
export MISSION_CONTROL_PORT=8780

mkdir -p "${AI_ROOT}/Data/history" "${AI_ROOT}/Data/memory" "${AI_ROOT}/applications" "${AI_ROOT}/compose"

PY="${ROOT}/venv/bin/python"
if [[ ! -x "${PY}" ]]; then
  PY=python3
fi

if [[ ! -d "${AI_PLATFORM}" ]]; then
  echo "AI-Platform not found at ${AI_PLATFORM} (set AI_PLATFORM env)" >&2
  exit 1
fi

"${PY}" -m pip install -q -e "${AI_PLATFORM}"

MC_PID=""
if curl -sf "http://127.0.0.1:${MISSION_CONTROL_PORT}/api/health" >/dev/null; then
  echo "Mission Control already running on port ${MISSION_CONTROL_PORT}"
else
  "${PY}" -m aiplatform.mission_control.server --host 127.0.0.1 --port "${MISSION_CONTROL_PORT}" &
  MC_PID=$!
  for i in $(seq 1 45); do
    if curl -sf "http://127.0.0.1:${MISSION_CONTROL_PORT}/api/health" >/dev/null; then
      break
    fi
    if [[ "${i}" -eq 45 ]]; then
      echo "Mission Control failed to start" >&2
      exit 1
    fi
    sleep 1
  done
fi
cleanup() { [[ -n "${MC_PID}" ]] && kill "${MC_PID}" 2>/dev/null || true; }
trap cleanup EXIT

echo "==> ruff fix + format"
"${PY}" scripts/ci_check.py format
echo "==> ruff check + format-check + pytest"
exec "${PY}" scripts/ci_check.py all

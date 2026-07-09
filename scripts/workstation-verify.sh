#!/usr/bin/env bash
# Hardware-agnostic workstation verification (exit 1 if critical checks fail).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLATFORM_ROOT="${AI_PLATFORM_ROOT:-$(dirname "$ROOT")/AI-Platform}"
PY="${ROOT}/venv/bin/python"
FAIL=0

ok()   { echo "  OK   $*"; }
miss() { echo "  FAIL $*"; FAIL=1; }
warn() { echo "  WARN $*"; }

echo "=== Aria Workstation Verification ==="
echo ""

echo "Core"
if [[ -x "$PY" ]]; then
  ok "Python venv ($PY)"
  if "$PY" -c "import jarvis" 2>/dev/null; then
    ok "jarvis package importable"
  else
    miss "jarvis import failed — run ./scripts/install.sh"
  fi
else
  miss "venv missing — run ./scripts/install.sh"
fi

if [[ -f "$ROOT/data/jarvis.env" ]]; then
  ok "data/jarvis.env"
else
  warn "data/jarvis.env missing — run: ./scripts/jarvis-ctl.sh configure"
fi
echo ""

echo "Inference (Ollama)"
if command -v ollama >/dev/null 2>&1; then
  ok "ollama binary"
  if curl -sf --max-time 3 "http://127.0.0.1:11434/api/tags" >/dev/null 2>&1; then
    ok "ollama API responding"
    count="$(ollama list 2>/dev/null | tail -n +2 | wc -l | tr -d ' ')"
    if [[ "${count:-0}" -gt 0 ]]; then
      ok "ollama models ($count)"
    else
      warn "no ollama models — run ./scripts/pull-models.sh"
    fi
  else
    warn "ollama not responding — start with: ollama serve"
  fi
else
  warn "ollama not installed — run ./scripts/install-dependencies.sh or install-ollama-latest.sh"
fi
echo ""

echo "Docker (optional)"
if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    ok "docker daemon"
  else
    warn "docker installed but daemon not running"
  fi
else
  warn "docker not installed (optional for postgres/redis/litellm)"
fi
echo ""

echo "Workstation control plane"
if [[ -x "$PY" ]]; then
  if "$PY" -m jarvis.workstation.cli status >/dev/null 2>&1; then
    ready="$("$PY" -m jarvis.workstation.cli status 2>/dev/null | "$PY" -c "import sys,json; print(json.load(sys.stdin).get('ready', False))" 2>/dev/null || echo false)"
    if [[ "$ready" == "True" ]]; then
      ok "workstation status ready"
    else
      warn "workstation not fully ready — run: ./scripts/jarvis-ctl.sh workstation recover"
    fi
  else
    warn "workstation status check failed"
  fi
fi
echo ""

echo "AI-Platform (optional)"
if [[ -d "$PLATFORM_ROOT" && -x "$PY" ]]; then
  if "$PY" -c "import aiplatform" 2>/dev/null; then
    ok "aiplatform importable"
    if "$PY" -m aiplatform.cli doctor >/dev/null 2>&1; then
      ok "aiplatform doctor"
    else
      warn "aiplatform doctor reported issues"
      "$PY" -m aiplatform.cli doctor 2>&1 | head -20 || true
    fi
  else
    warn "AI-Platform repo present but not installed — run ./scripts/install.sh"
  fi
else
  warn "AI-Platform not co-installed (optional)"
fi
echo ""

echo "Aria server"
# shellcheck source=_jarvis-launch-lib.sh
source "$ROOT/scripts/_jarvis-launch-lib.sh"
JARVIS_ROOT="$ROOT"
if jarvis_server_responsive 2>/dev/null; then
  ok "HTTP server responding"
else
  warn "Aria server not running — start with: ./scripts/jarvis-ctl.sh start"
fi
echo ""

if [[ "$FAIL" -eq 0 ]]; then
  echo "Verification passed (warnings may remain)."
  exit 0
fi
echo "Verification failed — fix FAIL items above."
exit 1

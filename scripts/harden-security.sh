#!/usr/bin/env bash
# Audit local AI services for home-LAN-only exposure.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAIL=0

ok()   { echo "  OK   $*"; }
warn() { echo "  WARN $*"; FAIL=1; }
miss() { echo "  MISS $*"; FAIL=1; }

echo "=== Jarvis security audit ==="
echo ""

echo "Jarvis bind address"
HOST=$(grep -E '^export JARVIS_HOST=' "$ROOT/data/jarvis.env" 2>/dev/null | head -1 || true)
if [[ -z "$HOST" ]] || grep -qE '^#.*JARVIS_HOST' "$ROOT/data/jarvis.env" 2>/dev/null && [[ -z "${HOST:-}" ]]; then
  ok "JARVIS_HOST not set (defaults to 127.0.0.1 — localhost only)"
elif echo "$HOST" | grep -q '127.0.0.1\|localhost'; then
  ok "JARVIS_HOST is localhost"
elif echo "$HOST" | grep -q '0.0.0.0'; then
  warn "JARVIS_HOST=0.0.0.0 — LAN-wide; set JARVIS_API_KEY and keep router port-forward OFF"
else
  warn "JARVIS_HOST=$HOST — review bind address"
fi

if grep -qE '^export JARVIS_API_KEY=' "$ROOT/data/jarvis.env" 2>/dev/null && \
   ! grep -qE '^#.*JARVIS_API_KEY' "$ROOT/data/jarvis.env" 2>/dev/null; then
  ok "JARVIS_API_KEY is set"
elif ss -tln 2>/dev/null | grep -qE '0\.0\.0\.0:8765|\*:8765'; then
  miss "Jarvis exposed without JARVIS_API_KEY"
else
  ok "No API key needed (localhost bind)"
fi

echo ""
echo "Listening ports (Jarvis / ComfyUI / Ollama)"
while read -r line; do
  echo "  $line"
  if echo "$line" | grep -qE '0\.0\.0\.0:8765|\*:8765'; then
    warn "Jarvis reachable on all interfaces"
  fi
  if echo "$line" | grep -qE '0\.0\.0\.0:8188|\*:8188'; then
    warn "ComfyUI reachable on all interfaces"
  fi
  if echo "$line" | grep -qE '0\.0\.0\.0:11434|\*:11434'; then
    warn "Ollama on ALL interfaces — run: sudo ./scripts/bind-ollama-localhost.sh"
  fi
done < <(ss -tln 2>/dev/null | grep -E ':8765|:8188|:11434' || true)

echo ""
echo "Router / WAN"
if command -v ufw &>/dev/null && ufw status 2>/dev/null | grep -qi active; then
  ok "ufw active"
else
  warn "No active host firewall detected — ensure router does NOT port-forward 8765/8188/11434"
fi

echo ""
if [[ "$FAIL" -eq 0 ]]; then
  echo "No critical exposure issues found."
else
  echo "Review WARN/MISS lines above."
  exit 1
fi

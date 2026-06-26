#!/usr/bin/env bash
# Enable Jarvis LAN access: bind all interfaces + generate API key.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/data/jarvis.env"
EXAMPLE="$ROOT/data/jarvis.env.example"

mkdir -p "$ROOT/data"
if [[ ! -f "$ENV_FILE" ]]; then
  if [[ -f "$EXAMPLE" ]]; then
    cp "$EXAMPLE" "$ENV_FILE"
  else
    touch "$ENV_FILE"
  fi
fi

KEY="$(python3 - <<'PY'
from jarvis.lan import generate_api_key
print(generate_api_key())
PY
)"

upsert() {
  local name="$1"
  local value="$2"
  if grep -qE "^export ${name}=" "$ENV_FILE" 2>/dev/null; then
    sed -i "s|^export ${name}=.*|export ${name}=\"${value}\"|" "$ENV_FILE"
  elif grep -qE "^# export ${name}=" "$ENV_FILE" 2>/dev/null; then
    sed -i "s|^# export ${name}=.*|export ${name}=\"${value}\"|" "$ENV_FILE"
  else
    printf '\nexport %s="%s"\n' "$name" "$value" >>"$ENV_FILE"
  fi
}

upsert JARVIS_HOST "0.0.0.0"
upsert JARVIS_API_KEY "$KEY"
upsert JARVIS_NETWORK_GUARD "1"
upsert JARVIS_RATE_LIMIT "1"

LAN_IPS="$(python3 - <<'PY'
from jarvis.lan import bind_port, list_lan_ips
port = bind_port()
for ip in list_lan_ips():
    print(f"http://{ip}:{port}")
PY
)"

echo ""
echo "Jarvis LAN access enabled in $ENV_FILE"
echo ""
echo "  JARVIS_HOST=0.0.0.0"
echo "  JARVIS_API_KEY=$KEY"
echo ""
echo "Restart Jarvis, then on your laptop open:"
if [[ -n "$LAN_IPS" ]]; then
  while IFS= read -r url; do
    [[ -z "$url" ]] && continue
    echo "  $url"
  done <<<"$LAN_IPS"
else
  echo "  http://<PC-LAN-IP>:${JARVIS_PORT:-8765}"
fi
echo ""
echo "Enter the API key once in the browser when prompted."
echo "Optional: append ?api_key=... to the URL for first visit (avoid sharing links)."
echo ""
echo "Security:"
echo "  • Do NOT port-forward 8765 to the internet."
echo "  • Keep Ollama on localhost: sudo ./scripts/bind-ollama-localhost.sh"
echo "  • Run ./scripts/harden-security.sh to audit"
echo ""

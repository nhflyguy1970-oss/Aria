#!/usr/bin/env bash
# Configure Jarvis ↔ Home Assistant (optional, off until URL + token are set).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/data/jarvis.env"
EXAMPLE="$ROOT/jarvis.env.example"

mkdir -p "$ROOT/data"
if [[ ! -f "$ENV_FILE" ]]; then
  if [[ -f "$EXAMPLE" ]]; then
    cp "$EXAMPLE" "$ENV_FILE"
  else
    touch "$ENV_FILE"
  fi
fi

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

DEFAULT_URL="${JARVIS_HA_URL:-http://homeassistant.local:8123}"
read -r -p "Home Assistant URL [$DEFAULT_URL]: " HA_URL || true
HA_URL="${HA_URL:-$DEFAULT_URL}"

echo ""
echo "Create a long-lived access token in Home Assistant:"
echo "  Profile → Security → Long-Lived Access Tokens"
echo ""
read -r -s -p "Paste token (hidden): " HA_TOKEN || true
echo ""

if [[ -z "${HA_TOKEN// /}" ]]; then
  echo "No token entered — aborting."
  exit 1
fi

AUTOMATION_SECRET="$(python3 - <<'PY'
from jarvis.lan import generate_api_key
print(generate_api_key())
PY
)"

upsert JARVIS_HA_ENABLED "1"
upsert JARVIS_HA_URL "$HA_URL"
upsert JARVIS_HA_TOKEN "$HA_TOKEN"
upsert JARVIS_AUTOMATION_SECRET "$AUTOMATION_SECRET"

echo ""
echo "Optional: scene entity for \"I'm heading out\" (e.g. scene.leaving)"
read -r -p "JARVIS_HA_SCENE_LEAVE [leave blank to skip]: " LEAVE_SCENE || true
if [[ -n "${LEAVE_SCENE// /}" ]]; then
  upsert JARVIS_HA_SCENE_LEAVE "$LEAVE_SCENE"
fi

echo ""
echo "Saved to $ENV_FILE"
echo ""
echo "Restart Jarvis, then try in chat:"
echo "  house status"
echo "  turn off the living room lights"
echo "  activate scene goodnight"
echo ""
echo "Home Assistant → Jarvis webhook (REST):"
echo "  POST http://<jarvis-host>:8765/api/automation/inbound?secret=$AUTOMATION_SECRET"
echo '  Body: {"action":"chat","message":"morning briefing"}'
echo ""
echo "Test connection:"
python3 - <<PY
from jarvis.env_loader import load_jarvis_env
load_jarvis_env()
from jarvis.home_assistant import check_connection
print(check_connection())
PY

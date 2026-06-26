#!/usr/bin/env bash
# Test and save a Home Assistant long-lived token into data/jarvis.env
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/data/jarvis.env"
HA_URL="${JARVIS_HA_URL:-http://127.0.0.1:8123}"

echo "Home Assistant token setup"
echo "========================"
echo ""
echo "In Home Assistant (http://127.0.0.1:8123):"
echo "  Profile (bottom left) → Security → Long-lived access tokens → Create token"
echo ""
read -r -s -p "Paste token here (hidden): " TOKEN || true
echo ""

if [[ -z "${TOKEN// /}" ]]; then
  echo "No token entered."
  exit 1
fi

echo "Testing $HA_URL …"
HTTP="$(curl -s -o /tmp/jarvis-ha-test.json -w '%{http_code}' \
  -H "Authorization: Bearer ${TOKEN//[$'\r\n ']/}" \
  "$HA_URL/api/")"

if [[ "$HTTP" != "200" ]]; then
  echo ""
  echo "Failed: HTTP $HTTP"
  cat /tmp/jarvis-ha-test.json 2>/dev/null || true
  echo ""
  if [[ "$HTTP" == "401" ]]; then
    echo "That token was rejected. Create a NEW long-lived token in HA and try again."
  elif [[ "$HTTP" == "000" ]]; then
    echo "Home Assistant is not reachable. Run: ./scripts/start-home-assistant.sh"
  fi
  exit 1
fi

VERSION="$(python3 - <<PY
import json
print(json.load(open("/tmp/jarvis-ha-test.json")).get("version", "?"))
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

upsert JARVIS_HA_ENABLED "1"
upsert JARVIS_HA_URL "$HA_URL"
upsert JARVIS_HA_TOKEN "${TOKEN//[$'\r\n ']/}"

echo ""
echo "Success — Home Assistant v$VERSION"
echo "Saved to $ENV_FILE"
echo ""
echo "Jarvis picks this up automatically — try in chat: house status"
echo "(If it still says disconnected, restart Jarvis once.)"

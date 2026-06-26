# Jarvis automation webhook

Jarvis accepts inbound automation calls at:

```
POST http://<jarvis-host>:8765/api/automation/inbound?secret=YOUR_SECRET
```

Set `JARVIS_AUTOMATION_SECRET` in `data/jarvis.env` (or use `./scripts/enable-home-assistant.sh`).

## Actions

| action | Body | Description |
|--------|------|-------------|
| `chat` | `message` or `text` | Run any chat command |
| `briefing` | _(optional)_ | Morning briefing markdown |
| `journal_log` | `text` or `entry` | Append to bullet journal |
| `ha_scene` | `scene` | Activate Home Assistant scene |
| `run_script` | `script` | Run executable in `data/scripts/` only |
| `wake` | `mac` _(optional)_ | Wake-on-LAN (`JARVIS_WOL_MAC`) |
| `resources` | — | GPU/queue snapshot |
| `environment` | — | Full environment snapshot |

## Examples

```bash
# Morning briefing from cron
curl -s -X POST "http://127.0.0.1:8765/api/automation/inbound?secret=$SECRET" \
  -H "Content-Type: application/json" \
  -d '{"action":"briefing"}'

# Chat
curl -s -X POST "http://127.0.0.1:8765/api/automation/inbound?secret=$SECRET" \
  -H "Content-Type: application/json" \
  -d '{"action":"chat","message":"house status"}'

# Whitelisted script (must be chmod +x in data/scripts/)
curl -s -X POST "http://127.0.0.1:8765/api/automation/inbound?secret=$SECRET" \
  -H "Content-Type: application/json" \
  -d '{"action":"run_script","script":"notify-desktop.sh"}'
```

## Home Assistant REST

Use the URL shown in **Smart home** panel or `GET /api/homeassistant/status` → `automation_webhook_url`.

## n8n / Node-RED

Use an HTTP Request node: POST to the inbound URL with JSON body. No custom node required.

## Remote LAN

Enable LAN access with `./scripts/enable-lan.sh` and use your PC IP instead of `127.0.0.1`. Always use the secret — never expose Jarvis without `JARVIS_API_KEY` on untrusted networks.

## Optional calendar in briefing

Set `JARVIS_ICS_URL` to a private ICS feed URL for external calendar events in the morning briefing.

#!/usr/bin/env bash
# Extend AI-Platform compose with workstation services (idempotent).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AI_ROOT="${AI_ROOT:-$(dirname "$ROOT")}"
COMPOSE="$AI_ROOT/compose/compose.yaml"

if [[ ! -f "$COMPOSE" ]]; then
  echo "compose.yaml not found at $COMPOSE" >&2
  exit 1
fi

python3 - "$COMPOSE" <<'PY'
import sys
from pathlib import Path

import yaml

path = Path(sys.argv[1])
data = yaml.safe_load(path.read_text()) or {}
services = data.setdefault("services", {})
volumes = data.setdefault("volumes", {})
networks = data.setdefault("networks", {})
networks.setdefault("ai-platform", {})

def add(name, spec):
    if name in services:
        return False
    services[name] = spec
    return True

added = []

if add("qdrant", {
    "image": "qdrant/qdrant:latest",
    "container_name": "ai-qdrant",
    "ports": ["6333:6333"],
    "volumes": ["qdrant_data:/qdrant/storage"],
    "networks": {"ai-platform": {}},
    "profiles": ["data"],
    "healthcheck": {
        "test": ["CMD-SHELL", "wget -q -O- http://localhost:6333/healthz || exit 1"],
        "interval": "5s",
        "timeout": "5s",
        "retries": 5,
    },
    "restart": "unless-stopped",
}):
    volumes.setdefault("qdrant_data", {})
    added.append("qdrant")

if add("n8n", {
    "image": "n8nio/n8n:latest",
    "container_name": "ai-n8n",
    "ports": ["5678:5678"],
    "environment": ["N8N_HOST=localhost", "N8N_PORT=5678", "N8N_PROTOCOL=http"],
    "volumes": ["n8n_data:/home/node/.n8n"],
    "networks": {"ai-platform": {}},
    "profiles": ["automation"],
    "restart": "unless-stopped",
}):
    volumes.setdefault("n8n_data", {})
    added.append("n8n")

if add("prometheus", {
    "image": "prom/prometheus:latest",
    "container_name": "ai-prometheus",
    "ports": ["9090:9090"],
    "volumes": ["./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro"],
    "networks": {"ai-platform": {}},
    "profiles": ["monitoring"],
    "restart": "unless-stopped",
}):
    added.append("prometheus")

if add("grafana", {
    "image": "grafana/grafana:latest",
    "container_name": "ai-grafana",
    "ports": ["3001:3000"],
    "environment": ["GF_SECURITY_ADMIN_PASSWORD=admin"],
    "volumes": ["grafana_data:/var/lib/grafana"],
    "networks": {"ai-platform": {}},
    "profiles": ["monitoring"],
    "restart": "unless-stopped",
}):
    volumes.setdefault("grafana_data", {})
    added.append("grafana")

litellm = services.get("litellm")
if litellm:
    litellm.pop("depends_on", None)
    litellm.setdefault("extra_hosts", ["host.docker.internal:host-gateway"])
    added.append("litellm-host-ollama")

path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
print("extended:", ", ".join(added) if added else "no changes")
PY

PROM_DIR="$AI_ROOT/compose/prometheus"
mkdir -p "$PROM_DIR"
if [[ ! -f "$PROM_DIR/prometheus.yml" ]]; then
  cat >"$PROM_DIR/prometheus.yml" <<'EOF'
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: ["localhost:9090"]
  - job_name: node
    static_configs:
      - targets: ["host.docker.internal:9100"]
EOF
fi

LITELLM_CFG="$AI_ROOT/compose/litellm/config.yaml"
if [[ -f "$LITELLM_CFG" ]] && ! grep -q host.docker.internal "$LITELLM_CFG"; then
  sed -i 's|api_base: http://ollama:11434|api_base: http://host.docker.internal:11434|' "$LITELLM_CFG"
  echo "Updated litellm config for host Ollama"
fi

#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/common.sh"

compose ps

if ! compose exec -T ollama ollama show bge-m3 >/dev/null; then
  echo "Ollama embedding model is unavailable." >&2
  exit 1
fi

if ! compose exec -T openviking curl -fsS http://127.0.0.1:1933/health >/dev/null; then
  echo "OpenViking health check failed." >&2
  exit 1
fi

if ! compose ps --status running --services | grep -qx hermes; then
  echo "Hermes is not running." >&2
  exit 1
fi

sleep 5
hermes_container="$(compose ps -q hermes)"
if [[ -z "${hermes_container}" ]]; then
  echo "Hermes container ID is unavailable." >&2
  exit 1
fi

restart_count="$(docker inspect --format '{{.RestartCount}}' "${hermes_container}")"
if [[ "${restart_count}" != "0" ]]; then
  echo "Hermes restarted ${restart_count} time(s) during startup." >&2
  exit 1
fi

if ! compose ps --status running --services | grep -qx hermes; then
  echo "Hermes stopped during startup validation." >&2
  exit 1
fi

echo "Stack health checks passed. WhatsApp readiness still depends on pairing and group allowlists."

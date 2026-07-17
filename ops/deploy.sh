#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/common.sh"

"${REPO_ROOT}/ops/bootstrap.sh"

compose pull ollama ollama-init
compose build --pull openviking hermes
if [[ "${TELEGRAM_LOCAL_API_ENABLED:-false}" == "true" ]]; then
  compose build telegram-bot-api
fi
compose up -d ollama
compose run --rm ollama-init
compose up -d openviking

for _ in $(seq 1 30); do
  if compose exec -T openviking curl -fsS http://127.0.0.1:1933/health >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if ! compose exec -T openviking curl -fsS http://127.0.0.1:1933/health >/dev/null 2>&1; then
  echo "OpenViking did not become healthy; Hermes was not restarted." >&2
  exit 1
fi

compose up -d --force-recreate hermes
if [[ "${CLOUDFLARE_TUNNEL_ENABLED:-false}" == "true" ]]; then
  compose up -d cloudflared
fi
"${REPO_ROOT}/ops/healthcheck.sh"

#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/common.sh"

"${REPO_ROOT}/ops/bootstrap.sh"

compose pull hermes ollama ollama-init
compose build --pull openviking
compose up -d ollama
compose run --rm ollama-init
compose up -d openviking

for _ in $(seq 1 30); do
  if compose exec -T openviking curl -fsS http://127.0.0.1:1933/health >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

compose up -d hermes
"${REPO_ROOT}/ops/healthcheck.sh"

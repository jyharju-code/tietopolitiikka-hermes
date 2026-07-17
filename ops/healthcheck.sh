#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/common.sh"

compose ps

if ! compose exec -T ollama ollama show nomic-embed-text >/dev/null; then
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

echo "Stack health checks passed. WhatsApp readiness still depends on pairing and group allowlists."

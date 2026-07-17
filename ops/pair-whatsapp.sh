#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/common.sh"

compose stop hermes >/dev/null 2>&1 || true
compose run --rm --no-deps -e WHATSAPP_ENABLED=true hermes whatsapp
compose up -d hermes

echo "WhatsApp pairing completed. Add the dedicated account to both groups."
echo "Set WHATSAPP_ENABLED=true only after the group notice is approved."

#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/common.sh"

compose stop hermes >/dev/null 2>&1 || true
compose run --rm --service-ports hermes whatsapp
compose up -d hermes

echo "WhatsApp pairing completed. Add the dedicated account to both groups."

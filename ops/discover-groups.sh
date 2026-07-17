#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/common.sh"

echo "Known WhatsApp group JIDs from Hermes state and logs:"
if command -v rg >/dev/null 2>&1; then
  rg -o --no-filename '[0-9]{10,}@g\.us' "${DATA_ROOT}/hermes" 2>/dev/null | sort -u || true
else
  grep -RhoE '[0-9]{10,}@g\.us' "${DATA_ROOT}/hermes" 2>/dev/null | sort -u || true
fi

echo
echo "Send one message mentioning Hermes in each group if the list is empty."
echo "Put only the two approved JIDs in .env.runtime, then run ops/deploy.sh."

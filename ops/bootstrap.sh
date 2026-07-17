#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/common.sh"

: "${DEEPSEEK_API_KEY:?DEEPSEEK_API_KEY is required}"
: "${OPENVIKING_API_KEY:?OPENVIKING_API_KEY is required}"
: "${HERMES_IMAGE:?HERMES_IMAGE is required}"
: "${OLLAMA_IMAGE:?OLLAMA_IMAGE is required}"

umask 077
install -d -m 0700 \
  "${DATA_ROOT}/hermes" \
  "${DATA_ROOT}/hermes/memories" \
  "${DATA_ROOT}/hermes/skills/tietopolitiikka-memory" \
  "${DATA_ROOT}/openviking" \
  "${DATA_ROOT}/ollama" \
  "${BACKUP_ROOT}"

# The OpenViking image runs as uid 10001 and must own its persistent state.
chown 10001:10001 "${DATA_ROOT}/openviking"

install -m 0600 "${REPO_ROOT}/config/hermes/SOUL.md" "${DATA_ROOT}/hermes/SOUL.md"
install -m 0600 "${REPO_ROOT}/config/hermes/memories/MEMORY.md" "${DATA_ROOT}/hermes/memories/MEMORY.md"
install -m 0600 "${REPO_ROOT}/config/hermes/memories/USER.md" "${DATA_ROOT}/hermes/memories/USER.md"
install -m 0600 "${REPO_ROOT}/skills/tietopolitiikka-memory/SKILL.md" "${DATA_ROOT}/hermes/skills/tietopolitiikka-memory/SKILL.md"

python3 "${REPO_ROOT}/ops/render-config.py"

echo "Bootstrap complete at ${DATA_ROOT}"

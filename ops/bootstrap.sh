#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/common.sh"

: "${DEEPSEEK_API_KEY:?DEEPSEEK_API_KEY is required}"
: "${OPENVIKING_API_KEY:?OPENVIKING_API_KEY is required}"
: "${MEMORY_VLM_API_KEY:=${DEEPSEEK_API_KEY}}"
: "${HERMES_IMAGE:?HERMES_IMAGE is required}"
: "${OLLAMA_IMAGE:?OLLAMA_IMAGE is required}"
: "${HERMES_DASHBOARD_BASIC_AUTH_USERNAME:?Dashboard proxy username is required}"
: "${HERMES_DASHBOARD_BASIC_AUTH_PASSWORD:?Dashboard proxy password is required}"

if [[ -n "${TELEGRAM_BOT_TOKEN:-}" && -z "${TELEGRAM_GROUP_ID:-}" ]]; then
  echo "TELEGRAM_GROUP_ID is required when TELEGRAM_BOT_TOKEN is set." >&2
  exit 1
fi

if [[ "${TELEGRAM_LOCAL_API_ENABLED:-false}" == "true" ]]; then
  : "${TELEGRAM_API_ID:?TELEGRAM_API_ID is required for the local Bot API}"
  : "${TELEGRAM_API_HASH:?TELEGRAM_API_HASH is required for the local Bot API}"
fi

umask 077
install -d -m 0700 \
  "${DATA_ROOT}/hermes" \
  "${DATA_ROOT}/hermes/memories" \
  "${DATA_ROOT}/hermes/skills/tietopolitiikka-memory" \
  "${DATA_ROOT}/hermes/skills/tietopolitiikka-files" \
  "${DATA_ROOT}/hermes/skills/tietopolitiikka-site" \
  "${DATA_ROOT}/hermes/dashboard-files" \
  "${DATA_ROOT}/hermes/dashboard-files/uploads" \
  "${DATA_ROOT}/hermes/dashboard-files/links" \
  "${DATA_ROOT}/hermes/dashboard-files/artifacts" \
  "${DATA_ROOT}/hermes/dashboard-files/artifacts/tietopolitiikkasite" \
  "${DATA_ROOT}/openviking" \
  "${DATA_ROOT}/ollama" \
  "${DATA_ROOT}/telegram-bot-api" \
  "${BACKUP_ROOT}"

# The OpenViking image runs as uid 10001 and must own its persistent state.
chown 10001:10001 "${DATA_ROOT}/openviking"
chown 10002:10002 "${DATA_ROOT}/telegram-bot-api"

install -m 0600 "${REPO_ROOT}/config/hermes/SOUL.md" "${DATA_ROOT}/hermes/SOUL.md"
install -m 0600 "${REPO_ROOT}/config/hermes/memories/MEMORY.md" "${DATA_ROOT}/hermes/memories/MEMORY.md"
install -m 0600 "${REPO_ROOT}/config/hermes/memories/USER.md" "${DATA_ROOT}/hermes/memories/USER.md"
install -m 0600 "${REPO_ROOT}/skills/tietopolitiikka-memory/SKILL.md" "${DATA_ROOT}/hermes/skills/tietopolitiikka-memory/SKILL.md"
install -m 0600 "${REPO_ROOT}/skills/tietopolitiikka-files/SKILL.md" "${DATA_ROOT}/hermes/skills/tietopolitiikka-files/SKILL.md"
install -m 0600 "${REPO_ROOT}/skills/tietopolitiikka-site/SKILL.md" "${DATA_ROOT}/hermes/skills/tietopolitiikka-site/SKILL.md"

python3 "${REPO_ROOT}/ops/render-config.py"
chown -R 10000:10000 "${DATA_ROOT}/hermes"

echo "Bootstrap complete at ${DATA_ROOT}"

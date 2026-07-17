#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/common.sh"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
archive="${BACKUP_ROOT}/tietopolitiikka-hermes-${timestamp}.tar.gz"

install -d -m 0700 "${BACKUP_ROOT}"

paused=()
cleanup() {
  if [[ ${#paused[@]} -gt 0 ]]; then
    compose unpause "${paused[@]}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

for service in hermes openviking; do
  if compose ps --status running --services | grep -qx "${service}"; then
    compose pause "${service}" >/dev/null
    paused+=("${service}")
  fi
done

paths=(hermes openviking)
if [[ -d "${DATA_ROOT}/telegram-bot-api" ]]; then
  paths+=(telegram-bot-api)
fi
tar -C "${DATA_ROOT}" -czf "${archive}" "${paths[@]}"
chmod 0600 "${archive}"

cleanup
paused=()
trap - EXIT

find "${BACKUP_ROOT}" \
  -maxdepth 1 \
  -type f \
  -name 'tietopolitiikka-hermes-*.tar.gz' \
  -mtime "+${BACKUP_RETENTION_DAYS}" \
  -delete

echo "Backup created: ${archive}"

#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_ENV="${RUNTIME_ENV:-${REPO_ROOT}/.env.runtime}"

if [[ ! -f "${RUNTIME_ENV}" ]]; then
  echo "Missing ${RUNTIME_ENV}. Copy .env.example and fill it first." >&2
  exit 1
fi

set -a
source "${RUNTIME_ENV}"
set +a

: "${DATA_ROOT:=/srv/tietopolitiikka-hermes}"
: "${BACKUP_ROOT:=/var/backups/tietopolitiikka-hermes}"
: "${BACKUP_RETENTION_DAYS:=14}"

compose() {
  local compose_files=(-f "${REPO_ROOT}/docker-compose.yml")
  if [[ "${WHATSAPP_ENABLED:-false}" == "true" ]]; then
    compose_files+=(-f "${REPO_ROOT}/docker-compose.whatsapp.yml")
  fi

  docker compose \
    --project-directory "${REPO_ROOT}" \
    --env-file "${RUNTIME_ENV}" \
    "${compose_files[@]}" \
    "$@"
}

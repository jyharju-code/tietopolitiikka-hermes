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
  docker compose \
    --project-directory "${REPO_ROOT}" \
    --env-file "${RUNTIME_ENV}" \
    "$@"
}

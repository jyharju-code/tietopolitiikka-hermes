#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${RUNTIME_ENV:-${REPO_ROOT}/.env.runtime}"

IFS= read -r deepseek_key || true
if [[ -z "${deepseek_key}" ]]; then
  echo "Expected the DeepSeek API key on standard input." >&2
  exit 1
fi

openviking_key="$(openssl rand -hex 32)"

umask 077
temporary="$(mktemp "${TARGET}.XXXXXX")"
trap 'rm -f "${temporary}"' EXIT

while IFS= read -r line || [[ -n "${line}" ]]; do
  case "${line}" in
    DEEPSEEK_API_KEY=*) printf 'DEEPSEEK_API_KEY=%s\n' "${deepseek_key}" ;;
    OPENVIKING_API_KEY=*) printf 'OPENVIKING_API_KEY=%s\n' "${openviking_key}" ;;
    *) printf '%s\n' "${line}" ;;
  esac
done < "${REPO_ROOT}/.env.example" > "${temporary}"

chmod 0600 "${temporary}"
mv -f "${temporary}" "${TARGET}"
trap - EXIT
echo "Installed ${TARGET} with mode 600."

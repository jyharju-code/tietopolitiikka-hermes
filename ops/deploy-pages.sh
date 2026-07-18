#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  echo "CLOUDFLARE_API_TOKEN is not set; using the interactive wrangler OAuth session." >&2
fi

cd "${REPO_ROOT}"
npx --yes wrangler@latest pages deploy pages --project-name=tietopolitiikka

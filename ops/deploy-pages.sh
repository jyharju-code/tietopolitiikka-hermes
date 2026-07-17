#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

: "${CLOUDFLARE_API_TOKEN:?CLOUDFLARE_API_TOKEN is required}"

cd "${REPO_ROOT}"
npx --yes wrangler@latest pages deploy pages --project-name=tietopolitiikka

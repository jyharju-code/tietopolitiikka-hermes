#!/usr/bin/env bash
# Publish the agent-built test site to tietopolitiikkasite.pages.dev.
#
# The Hermes container holds no Cloudflare credential on purpose: a Pages token
# is account-wide, so it would also reach the group's live dashboard project,
# and the agent ingests untrusted documents. Publishing therefore stays an
# operator step and runs from a machine that already has Cloudflare access.
#
# Usage:
#   ops/deploy-site.sh            # pull the build from the server, then publish
#   ops/deploy-site.sh <dir>      # publish a local directory instead
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="tietopolitiikkasite"
PRODUCTION_PROJECT="tietopolitiikka"
# The host and key stay out of this public repository. Set them in the
# environment, or in a gitignored ops/deploy-site.env next to this script.
if [[ -f "${REPO_ROOT}/ops/deploy-site.env" ]]; then
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/ops/deploy-site.env"
fi
: "${SITE_REMOTE:?Set SITE_REMOTE=user@host, or put it in ops/deploy-site.env}"
REMOTE="${SITE_REMOTE}"
REMOTE_KEY="${SITE_REMOTE_KEY:-${HOME}/.ssh/hermes_ed25519}"
# The agent keeps a Hugo project on the volume and publishes its rendered
# output. Deploy the build, never the source tree.
REMOTE_DIR="/srv/tietopolitiikka-hermes/hermes/${PROJECT}/public"

if [[ "${PROJECT}" == "${PRODUCTION_PROJECT}" ]]; then
  echo "Refusing to deploy: target is the production dashboard project." >&2
  exit 1
fi

source_dir="${1:-}"
staged=""
if [[ -z "${source_dir}" ]]; then
  staged="$(mktemp -d)"
  trap 'rm -rf "${staged}"' EXIT
  echo "Fetching the build from ${REMOTE}:${REMOTE_DIR}"
  rsync -a -e "ssh -i ${REMOTE_KEY}" "${REMOTE}:${REMOTE_DIR}/" "${staged}/"
  source_dir="${staged}"
fi

if [[ ! -f "${source_dir}/index.html" ]]; then
  echo "No index.html in ${source_dir}; nothing publishable." >&2
  exit 1
fi

files="$(find "${source_dir}" -type f | wc -l | tr -d ' ')"
echo "Publishing ${files} files from ${source_dir} to ${PROJECT}"

cd "${REPO_ROOT}"
npx --yes wrangler@latest pages deploy "${source_dir}" \
  --project-name="${PROJECT}" \
  --branch=main \
  --commit-dirty=true

echo "Published: https://${PROJECT}.pages.dev"

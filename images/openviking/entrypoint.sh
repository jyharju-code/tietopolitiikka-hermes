#!/bin/sh
set -eu

: "${MEMORY_VLM_API_KEY:?MEMORY_VLM_API_KEY is required}"
: "${MEMORY_VLM_API_BASE:=https://api.deepseek.com/v1}"
: "${MEMORY_VLM_MODEL:=deepseek-v4-flash}"
: "${OPENVIKING_API_KEY:?OPENVIKING_API_KEY is required}"

umask 077
envsubst '${MEMORY_VLM_API_KEY} ${MEMORY_VLM_API_BASE} ${MEMORY_VLM_MODEL} ${OPENVIKING_API_KEY}' \
  < /config/ov.conf.template \
  > /run/openviking/ov.conf

exec "$@"

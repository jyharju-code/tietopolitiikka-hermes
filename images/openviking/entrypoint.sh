#!/bin/sh
set -eu

: "${DEEPSEEK_API_KEY:?DEEPSEEK_API_KEY is required}"
: "${DEEPSEEK_MODEL:=deepseek-v4-flash}"

umask 077
envsubst '${DEEPSEEK_API_KEY} ${DEEPSEEK_MODEL}' \
  < /config/ov.conf.template \
  > /run/openviking/ov.conf

exec "$@"

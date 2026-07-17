#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/common.sh"

: "${TELEGRAM_BOT_TOKEN:?TELEGRAM_BOT_TOKEN is required}"

curl -fsS "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getUpdates" \
  | python3 -c '
import json, sys
payload = json.load(sys.stdin)
chats = {}
for update in payload.get("result", []):
    message = update.get("message") or update.get("channel_post") or {}
    chat = message.get("chat") or {}
    if chat.get("id") is not None:
        chats[str(chat["id"])] = {
            "type": chat.get("type"),
            "title": chat.get("title"),
        }
print(json.dumps(chats, ensure_ascii=False, indent=2))
'

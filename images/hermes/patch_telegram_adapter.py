#!/usr/bin/env python3
"""Attach fail-closed local ingestion to the pinned Hermes Telegram adapter."""

from pathlib import Path


TARGET = Path("/opt/hermes/plugins/platforms/telegram/adapter.py")


def replace_once(source: str, old: str, new: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one Telegram adapter patch target, found {count}")
    return source.replace(old, new, 1)


source = TARGET.read_text(encoding="utf-8")
source = replace_once(
    source,
    "class TelegramAdapter(BasePlatformAdapter):\n",
    """class TelegramAdapter(BasePlatformAdapter):
    async def handle_message(self, event):
        # Every accepted group event is durably archived before agent routing.
        # The hook is fail-closed on chat ID and fail-open on transient indexing
        # errors because it writes a local spool before returning.
        from tietopolitiikka_ingest_hook import archive_telegram_event

        await archive_telegram_event(event)
        return await super().handle_message(event)

""",
)
TARGET.write_text(source, encoding="utf-8")

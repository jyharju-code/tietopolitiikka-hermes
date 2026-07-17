#!/usr/bin/env python3
"""Apply a small fail-closed passive-ingest hook to the pinned Hermes image."""

from pathlib import Path


TARGET = Path("/opt/hermes/plugins/platforms/whatsapp/adapter.py")


def replace_once(source: str, old: str, new: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one adapter patch target, found {count}")
    return source.replace(old, new, 1)


source = TARGET.read_text(encoding="utf-8")

source = replace_once(
    source,
    """        try:\n            if not self._should_process_message(data):\n                return None\n\n            # Determine message type\n""",
    """        try:\n            from tietopolitiikka_ingest_hook import (\n                archive_whatsapp_event,\n                is_passive_main_message,\n            )\n\n            should_process = self._should_process_message(data)\n            passive_ingest = False\n            if not should_process:\n                passive_ingest = is_passive_main_message(data, self)\n                if not passive_ingest:\n                    return None\n\n            # Determine message type\n""",
)

source = replace_once(
    source,
    """            return MessageEvent(\n                text=body,\n""",
    """            event = MessageEvent(\n                text=body,\n""",
)

source = replace_once(
    source,
    """                reply_to_is_own_message=reply_to_is_own_message,\n            )\n        except Exception as e:\n""",
    """                reply_to_is_own_message=reply_to_is_own_message,\n            )\n            await archive_whatsapp_event(event, data, passive_ingest=passive_ingest)\n            if passive_ingest:\n                return None\n            return event\n        except Exception as e:\n""",
)

TARGET.write_text(source, encoding="utf-8")

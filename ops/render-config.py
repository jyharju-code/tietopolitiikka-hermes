#!/usr/bin/env python3
"""Render non-secret Hermes configuration from an explicit variable allowlist."""

from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "config" / "hermes" / "config.yaml.template"

ALLOWED = (
    "LLM_PROVIDER",
    "LLM_MODEL",
    "TELEGRAM_GROUP_ID",
    "TELEGRAM_API_BASE_URL",
    "TELEGRAM_LOCAL_MODE",
)

DEFAULTS = {
    "LLM_PROVIDER": "deepseek",
    "LLM_MODEL": "deepseek-v4-flash",
    "TELEGRAM_GROUP_ID": "",
    "TELEGRAM_API_BASE_URL": "",
    "TELEGRAM_LOCAL_MODE": "false",
}


def render(template: str, values: dict[str, str]) -> str:
    result = template
    for name in ALLOWED:
        result = result.replace("${" + name + "}", values.get(name, DEFAULTS[name]))
    unresolved = [name for name in ALLOWED if "${" + name + "}" in result]
    if unresolved:
        raise ValueError(f"Unresolved configuration variables: {', '.join(unresolved)}")
    return result


def main() -> None:
    data_root = Path(os.environ.get("DATA_ROOT", "/srv/tietopolitiikka-hermes"))
    target = data_root / "hermes" / "config.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    values = {name: os.environ.get(name, DEFAULTS[name]) or DEFAULTS[name] for name in ALLOWED}
    if os.environ.get("TELEGRAM_LOCAL_API_ENABLED", "false").lower() == "true":
        values["TELEGRAM_API_BASE_URL"] = "http://telegram-bot-api:8081/bot"
        values["TELEGRAM_LOCAL_MODE"] = "true"
    content = render(TEMPLATE.read_text(encoding="utf-8"), values)
    target.write_text(content, encoding="utf-8")
    target.chmod(0o600)
    print(f"Rendered {target}")


if __name__ == "__main__":
    main()

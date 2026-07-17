#!/usr/bin/env python3
"""Render the non-secret Hermes config from a small allowlist of variables."""

from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "config" / "hermes" / "config.yaml.template"

ALLOWED = (
    "DEEPSEEK_MODEL",
    "WHATSAPP_MAIN_GROUP_JID",
    "WHATSAPP_HERMES_GROUP_JID",
)


def render(template: str, values: dict[str, str]) -> str:
    result = template
    for name in ALLOWED:
        result = result.replace("${" + name + "}", values.get(name, ""))
    unresolved = [name for name in ALLOWED if "${" + name + "}" in result]
    if unresolved:
        raise ValueError(f"Unresolved configuration variables: {', '.join(unresolved)}")
    return result


def main() -> None:
    data_root = Path(os.environ.get("DATA_ROOT", "/srv/tietopolitiikka-hermes"))
    target = data_root / "hermes" / "config.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    values = {name: os.environ.get(name, "") for name in ALLOWED}
    values["DEEPSEEK_MODEL"] = values["DEEPSEEK_MODEL"] or "deepseek-v4-flash"
    content = render(TEMPLATE.read_text(encoding="utf-8"), values)
    target.write_text(content, encoding="utf-8")
    target.chmod(0o600)
    print(f"Rendered {target}")


if __name__ == "__main__":
    main()

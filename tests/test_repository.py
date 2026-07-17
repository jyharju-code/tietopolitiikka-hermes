from __future__ import annotations

import importlib.util
import os
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_render_module():
    path = ROOT / "ops" / "render-config.py"
    spec = importlib.util.spec_from_file_location("render_config", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RepositorySafetyTests(unittest.TestCase):
    def test_runtime_files_are_ignored(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".env.runtime", ignore)
        self.assertIn("runtime/", ignore)
        self.assertIn("backups/", ignore)

    def test_no_private_material_is_committed(self):
        forbidden_literals = (
            "/Users/" + "juhanaharju",
            "204.168." + "230.73",
            "@g.us\" # real group",
        )
        secret_patterns = (
            re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
            re.compile(r"\bgh[opsu]_[A-Za-z0-9]{20,}\b"),
        )
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for literal in forbidden_literals:
                self.assertNotIn(literal, text, f"private literal in {path}")
            for pattern in secret_patterns:
                self.assertIsNone(pattern.search(text), f"possible secret in {path}")

    def test_no_long_dash_characters(self):
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            self.assertNotIn("\u2013", text, f"long dash in {path}")
            self.assertNotIn("\u2014", text, f"long dash in {path}")

    def test_whatsapp_has_restricted_toolsets(self):
        template = (ROOT / "config" / "hermes" / "config.yaml.template").read_text(encoding="utf-8")
        self.assertIn("whatsapp: [skills]", template)
        self.assertNotIn("\nweb:", template)
        whatsapp_block = template.split("platform_toolsets:", 1)[1].split("whatsapp:", 1)[0]
        for forbidden in ("terminal", "file", "browser", "cronjob", "messaging"):
            self.assertNotIn(forbidden, whatsapp_block)

    def test_whatsapp_safe_defaults(self):
        template = (ROOT / "config" / "hermes" / "config.yaml.template").read_text(encoding="utf-8")
        self.assertIn("dm_policy: disabled", template)
        self.assertIn("group_policy: allowlist", template)
        self.assertIn("require_mention: true", template)
        self.assertIn('${WHATSAPP_HERMES_GROUP_JID}', template)

    def test_compose_publishes_no_ports_or_host_socket(self):
        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertNotRegex(compose, r"(?m)^\s+ports:\s*$")
        self.assertNotIn("/var/run/docker.sock", compose)
        self.assertNotIn("network_mode: host", compose)
        for capability in ("CHOWN", "DAC_OVERRIDE", "FOWNER", "KILL", "SETGID", "SETUID"):
            self.assertIn(f"- {capability}", compose)

    def test_openviking_config_uses_supported_fields(self):
        config = (ROOT / "config" / "openviking" / "ov.conf.template").read_text(encoding="utf-8")
        self.assertNotIn("agent_scope_mode", config)
        self.assertNotIn('"version": "v2"', config)
        self.assertIn('"auth_mode": "api_key"', config)
        self.assertIn('"root_api_key": "${OPENVIKING_API_KEY}"', config)

    def test_openviking_key_reaches_both_services(self):
        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertGreaterEqual(compose.count("OPENVIKING_API_KEY: ${OPENVIKING_API_KEY}"), 2)

    def test_durable_resource_requires_explicit_marker(self):
        soul = (ROOT / "config" / "hermes" / "SOUL.md").read_text(encoding="utf-8").lower()
        skill = (ROOT / "skills" / "tietopolitiikka-memory" / "SKILL.md").read_text(encoding="utf-8").lower()
        self.assertIn("muistiin", soul)
        self.assertIn("only when", skill)
        self.assertIn("do not infer consent", skill)


class RenderConfigTests(unittest.TestCase):
    def test_render_replaces_only_expected_values(self):
        module = load_render_module()
        source = "${DEEPSEEK_MODEL}|${WHATSAPP_MAIN_GROUP_JID}|${WHATSAPP_HERMES_GROUP_JID}|${SECRET}"
        rendered = module.render(
            source,
            {
                "DEEPSEEK_MODEL": "deepseek-chat",
                "WHATSAPP_MAIN_GROUP_JID": "11111111111@g.us",
                "WHATSAPP_HERMES_GROUP_JID": "22222222222@g.us",
                "SECRET": "must-not-appear",
            },
        )
        self.assertEqual(
            rendered,
            "deepseek-chat|11111111111@g.us|22222222222@g.us|${SECRET}",
        )

    def test_rendered_empty_group_ids_remain_closed(self):
        module = load_render_module()
        template = (ROOT / "config" / "hermes" / "config.yaml.template").read_text(encoding="utf-8")
        rendered = module.render(
            template,
            {
                "DEEPSEEK_MODEL": "deepseek-chat",
                "WHATSAPP_MAIN_GROUP_JID": "",
                "WHATSAPP_HERMES_GROUP_JID": "",
            },
        )
        self.assertIn("group_policy: allowlist", rendered)
        self.assertNotRegex(rendered, r"[0-9]{10,}@g\.us")

    def test_current_deepseek_default(self):
        example = (ROOT / ".env.example").read_text(encoding="utf-8")
        self.assertIn("DEEPSEEK_MODEL=deepseek-v4-flash", example)


if __name__ == "__main__":
    unittest.main()

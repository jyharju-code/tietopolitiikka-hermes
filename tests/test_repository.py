from __future__ import annotations

import importlib.util
import os
import re
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_render_module():
    path = ROOT / "ops" / "render-config.py"
    spec = importlib.util.spec_from_file_location("render_config", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_ingest_module():
    path = ROOT / "images" / "hermes" / "tietopolitiikka_ingest_hook.py"
    spec = importlib.util.spec_from_file_location("tietopolitiikka_ingest_hook_test", path)
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
        self.assertIn("whatsapp: [skills, memory]", template)
        self.assertNotIn("\nweb:", template)
        whatsapp_block = template.split("platform_toolsets:", 1)[1].split("whatsapp:", 1)[0]
        for forbidden in ("terminal", "file", "browser", "cronjob", "messaging"):
            self.assertNotIn(forbidden, whatsapp_block)

    def test_whatsapp_safe_defaults(self):
        template = (ROOT / "config" / "hermes" / "config.yaml.template").read_text(encoding="utf-8")
        example = (ROOT / ".env.example").read_text(encoding="utf-8")
        self.assertIn("dm_policy: disabled", template)
        self.assertIn("whatsapp:\n  enabled: false", template)
        self.assertIn("group_policy: allowlist", template)
        self.assertIn("require_mention: true", template)
        self.assertIn('${WHATSAPP_HERMES_GROUP_JID}', template)
        free_response = template.split("free_response_chats:", 1)[1].split("unauthorized_dm_behavior:", 1)[0]
        self.assertNotIn('${WHATSAPP_MAIN_GROUP_JID}', free_response)
        self.assertIn('${WHATSAPP_HERMES_GROUP_JID}', free_response)
        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("WHATSAPP_FREE_RESPONSE_CHATS: ${WHATSAPP_HERMES_GROUP_JID:-}", compose)
        self.assertIn("_config_version: 33", template)
        self.assertIn("WHATSAPP_ENABLED=false", example)
        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        overlay = (ROOT / "docker-compose.whatsapp.yml").read_text(encoding="utf-8")
        self.assertNotIn("WHATSAPP_ENABLED", compose)
        self.assertIn('WHATSAPP_ENABLED: "true"', overlay)

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
        self.assertIn('"auth_mode": "trusted"', config)
        self.assertIn('"root_api_key": "${OPENVIKING_API_KEY}"', config)
        self.assertIn('"api_base": "http://ollama:11434/v1"', config)
        self.assertIn('"model": "bge-m3"', config)
        self.assertIn('"dimension": 1024', config)

    def test_openviking_key_reaches_both_services(self):
        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertGreaterEqual(compose.count("OPENVIKING_API_KEY: ${OPENVIKING_API_KEY}"), 2)
        template = (ROOT / "config" / "hermes" / "config.yaml.template").read_text(encoding="utf-8")
        self.assertIn("cli: [skills, memory]", template)

    def test_deploy_recreates_hermes_after_rendering_config(self):
        deploy = (ROOT / "ops" / "deploy.sh").read_text(encoding="utf-8")
        self.assertIn("compose up -d --force-recreate hermes", deploy)

    def test_resources_are_automatically_indexed_locally(self):
        soul = (ROOT / "config" / "hermes" / "SOUL.md").read_text(encoding="utf-8").lower()
        skill = (ROOT / "skills" / "tietopolitiikka-memory" / "SKILL.md").read_text(encoding="utf-8").lower()
        hook = (ROOT / "images" / "hermes" / "tietopolitiikka_ingest_hook.py").read_text(encoding="utf-8")
        self.assertIn("sanaa `muistiin` ei tarvita", soul)
        self.assertIn("every url and attachment", skill)
        self.assertIn("/api/v1/content/write", hook)
        self.assertNotIn("/api/v1/resources", hook)
        self.assertNotIn("DEEPSEEK", hook.upper())

    def test_all_approved_group_conversation_is_archived(self):
        soul = (ROOT / "config" / "hermes" / "SOUL.md").read_text(encoding="utf-8")
        architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
        template = (ROOT / "config" / "hermes" / "config.yaml.template").read_text(encoding="utf-8")
        self.assertIn("jokainen viesti tallentuu ja indeksoituu automaattisesti", soul)
        self.assertIn("Every main-group message enters the local archive", architecture)
        self.assertIn("DeepSeek does not receive these passive messages", architecture)
        self.assertIn("session_inactivity_minutes: 30", template)

    def test_derived_hermes_image_installs_fail_closed_hook(self):
        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        dockerfile = (ROOT / "images" / "hermes" / "Dockerfile").read_text(encoding="utf-8")
        patcher = (ROOT / "images" / "hermes" / "patch_whatsapp_adapter.py").read_text(encoding="utf-8")
        self.assertIn("dockerfile: images/hermes/Dockerfile", compose)
        self.assertIn("HERMES_BASE_IMAGE: ${HERMES_IMAGE}", compose)
        self.assertIn("patch_whatsapp_adapter.py", dockerfile)
        self.assertIn("await archive_whatsapp_event(event, data, passive_ingest=passive_ingest)", patcher)
        self.assertIn("if passive_ingest:\\n                return None", patcher)


class LocalIngestTests(unittest.TestCase):
    def test_only_allowed_main_group_can_use_passive_path(self):
        module = load_ingest_module()

        class Adapter:
            @staticmethod
            def _is_broadcast_chat(chat_id):
                return False

            @staticmethod
            def _is_group_allowed(chat_id):
                return chat_id == "main@g.us"

        with mock.patch.dict(os.environ, {"WHATSAPP_MAIN_GROUP_JID": "main@g.us"}):
            self.assertTrue(
                module.is_passive_main_message(
                    {"chatId": "main@g.us", "isGroup": True}, Adapter()
                )
            )
            self.assertFalse(
                module.is_passive_main_message(
                    {"chatId": "other@g.us", "isGroup": True}, Adapter()
                )
            )
            self.assertFalse(
                module.is_passive_main_message(
                    {"chatId": "main@g.us", "isGroup": False}, Adapter()
                )
            )

    def test_spool_captures_urls_and_local_attachments(self):
        module = load_ingest_module()

        class Event:
            text = "Lue https://example.org/report.pdf."
            media_urls = []
            media_types = []

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            attachment = root / "report.txt"
            attachment.write_text("local attachment", encoding="utf-8")
            Event.media_urls = [str(attachment)]
            Event.media_types = ["text/plain"]
            module.SPOOL_ROOT = root / "spool"
            module.FILE_ROOT = root / "files"
            path = module._create_spool(
                Event(),
                {
                    "chatId": "main@g.us",
                    "messageId": "message-1",
                    "timestamp": 1_700_000_000,
                },
                True,
            )
            payload = __import__("json").loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["urls"], ["https://example.org/report.pdf"])
            self.assertTrue(Path(payload["media"][0]["path"]).is_file())
            self.assertTrue(payload["passive_ingest"])


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

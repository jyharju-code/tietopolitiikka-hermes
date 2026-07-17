from __future__ import annotations

import importlib.util
import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_module(relative_path: str, name: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RepositorySafetyTests(unittest.TestCase):
    def test_runtime_files_are_ignored(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for item in (".env.runtime", "runtime/", "backups/"):
            self.assertIn(item, ignore)

    def test_no_private_material_or_secrets_are_committed(self):
        forbidden_literals = (
            "/Users/" + "juhanaharju",
            "204.168." + "230.73",
            "Iisakki" + "_bot",
        )
        secret_patterns = (
            re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
            re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b"),
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

    def test_telegram_is_fail_closed_and_tool_restricted(self):
        template = (ROOT / "config/hermes/config.yaml.template").read_text(encoding="utf-8")
        example = (ROOT / ".env.example").read_text(encoding="utf-8")
        self.assertIn("telegram: [skills, memory]", template)
        self.assertIn("dm_policy: disabled", template)
        self.assertIn("group_policy: allowlist", template)
        self.assertIn('${TELEGRAM_GROUP_ID}', template)
        self.assertIn("TELEGRAM_BOT_TOKEN=\n", example)
        self.assertIn("TELEGRAM_GROUP_ID=\n", example)
        telegram_tools = template.split("platform_toolsets:", 1)[1].split("telegram:", 1)[0]
        for forbidden in ("terminal", "file", "browser", "cronjob", "messaging"):
            self.assertNotIn(forbidden, telegram_tools)

    def test_large_context_and_provider_switch_are_configured(self):
        template = (ROOT / "config/hermes/config.yaml.template").read_text(encoding="utf-8")
        self.assertIn("provider: ${LLM_PROVIDER}", template)
        self.assertIn("default: ${LLM_MODEL}", template)
        self.assertIn("recall_limit: 160", template)
        self.assertIn("recall_max_injected_chars: 700000", template)
        self.assertIn("protect_last_n: 160", template)

    def test_openviking_uses_memory_provider_variables(self):
        entrypoint = (ROOT / "images/openviking/entrypoint.sh").read_text(encoding="utf-8")
        self.assertIn("MEMORY_VLM_API_KEY", entrypoint)
        self.assertIn("MEMORY_VLM_API_BASE", entrypoint)
        self.assertIn("MEMORY_VLM_MODEL", entrypoint)
        self.assertNotIn("DEEPSEEK_API_KEY", entrypoint)

    def test_deploy_stops_if_openviking_never_becomes_healthy(self):
        deploy = (ROOT / "ops/deploy.sh").read_text(encoding="utf-8")
        self.assertIn("OpenViking did not become healthy", deploy)

    def test_compose_has_no_public_ports_or_host_socket(self):
        for name in ("docker-compose.yml", "docker-compose.tunnel.yml", "docker-compose.telegram-local.yml"):
            compose = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotRegex(compose, r"(?m)^\s+ports:\s*$")
            self.assertNotIn("/var/run/docker.sock", compose)
            self.assertNotIn("network_mode: host", compose)
        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("mem_limit: 1600m", compose)
        self.assertIn("mem_limit: 900m", compose)
        self.assertIn("mem_limit: 1g", compose)

    def test_dashboard_requires_telegram_membership(self):
        worker = (ROOT / "pages/_worker.js").read_text(encoding="utf-8")
        self.assertIn("getChatMember", worker)
        self.assertIn("verifyIdToken", worker)
        self.assertIn("MEMBERSHIP_RECHECK_SECONDS", worker)
        self.assertIn("ORIGIN_BASIC_AUTH_PASSWORD", worker)
        self.assertNotIn("TELEGRAM_BOT_TOKEN =", worker)

    def test_derived_image_patches_telegram_ingestion(self):
        dockerfile = (ROOT / "images/hermes/Dockerfile").read_text(encoding="utf-8")
        patcher = (ROOT / "images/hermes/patch_telegram_adapter.py").read_text(encoding="utf-8")
        hook = (ROOT / "images/hermes/tietopolitiikka_ingest_hook.py").read_text(encoding="utf-8")
        self.assertIn("patch_telegram_adapter.py", dockerfile)
        self.assertIn("await archive_telegram_event(event)", patcher)
        self.assertIn("TELEGRAM_GROUP_ID", hook)
        self.assertIn("/api/v1/content/write", hook)
        self.assertNotIn("DEEPSEEK", hook.upper())


class LocalIngestTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module("images/hermes/tietopolitiikka_ingest_hook.py", "ingest_test")

    @staticmethod
    def event(chat_id="-100123", text="Lue https://example.org/report.pdf."):
        return SimpleNamespace(
            text=text,
            message_id="message-1",
            media_urls=[],
            media_types=[],
            metadata={"sender_name": "Test Member", "timestamp": 1_700_000_000},
            source=SimpleNamespace(chat_id=chat_id, user_id="42", thread_id="7"),
        )

    def test_only_exact_telegram_group_is_accepted(self):
        with mock.patch.dict(os.environ, {"TELEGRAM_GROUP_ID": "-100123"}):
            self.assertTrue(self.module.is_allowed_telegram_event(self.event()))
            self.assertFalse(self.module.is_allowed_telegram_event(self.event("-100999")))
        with mock.patch.dict(os.environ, {"TELEGRAM_GROUP_ID": ""}):
            self.assertFalse(self.module.is_allowed_telegram_event(self.event()))

    def test_spool_captures_urls_topic_and_attachment(self):
        event = self.event()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            attachment = root / "report.txt"
            attachment.write_text("local attachment", encoding="utf-8")
            event.media_urls = [str(attachment)]
            event.media_types = ["text/plain"]
            self.module.SPOOL_ROOT = root / "spool"
            self.module.FILE_ROOT = root / "files"
            data = self.module._telegram_event_data(event)
            path = self.module._create_spool(event, data)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["urls"], ["https://example.org/report.pdf"])
            self.assertEqual(payload["thread_id"], "7")
            self.assertEqual(payload["platform"], "telegram")
            self.assertTrue(Path(payload["media"][0]["path"]).is_file())


class RenderConfigTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module("ops/render-config.py", "render_config_test")

    def test_render_replaces_only_allowed_values(self):
        source = "${LLM_PROVIDER}|${LLM_MODEL}|${TELEGRAM_GROUP_ID}|${TELEGRAM_API_BASE_URL}|${TELEGRAM_LOCAL_MODE}|${SECRET}"
        rendered = self.module.render(source, {
            "LLM_PROVIDER": "mistral",
            "LLM_MODEL": "mistral-small-latest",
            "TELEGRAM_GROUP_ID": "-100123",
            "TELEGRAM_API_BASE_URL": "",
            "TELEGRAM_LOCAL_MODE": "false",
            "SECRET": "must-not-appear",
        })
        self.assertEqual(rendered, "mistral|mistral-small-latest|-100123||false|${SECRET}")

    def test_empty_group_id_remains_closed(self):
        template = (ROOT / "config/hermes/config.yaml.template").read_text(encoding="utf-8")
        rendered = self.module.render(template, self.module.DEFAULTS)
        self.assertIn("group_policy: allowlist", rendered)
        self.assertNotRegex(rendered, r"-100\d{6,}")


if __name__ == "__main__":
    unittest.main()

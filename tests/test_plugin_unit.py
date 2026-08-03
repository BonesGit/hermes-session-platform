"""Unit tests for hermes-session-platform (no core Platform.SESSION required)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
HERMES_ROOT = Path.home() / ".hermes" / "hermes-agent"
if str(HERMES_ROOT) not in sys.path:
    sys.path.insert(0, str(HERMES_ROOT))


def _load_adapter():
    """Load adapter.py as a free module (avoids package relative-import issues)."""
    path = PLUGIN_ROOT / "adapter.py"
    spec = importlib.util.spec_from_file_location("session_platform_adapter", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["session_platform_adapter"] = mod
    spec.loader.exec_module(mod)
    return mod


session_adapter = _load_adapter()


class TestBridgePaths:
    def test_resolve_bridge_script(self):
        p = session_adapter.resolve_bridge_script()
        assert p.name == "session-bridge.mjs"
        assert p.parent.name == "bridge"
        assert p.is_file()

    def test_resolve_bridge_dir(self):
        d = session_adapter.resolve_bridge_dir()
        assert d.name == "bridge"
        assert (d / "package.json").is_file()


class TestPortHelper:
    def test_unused_high_port_not_listening(self):
        # Ephemeral-ish high port; extremely unlikely to be bound.
        assert session_adapter.bridge_port_is_listening(61999) is False

    def test_plugin_version_set(self):
        assert session_adapter.PLUGIN_VERSION
        assert session_adapter.PLUGIN_VERSION[0].isdigit()


class TestGroupAllowlists:
    def test_empty_allowlists_allow(self):
        assert session_adapter.is_group_message_allowed("03aaa", "05bbb", [], [])

    def test_chat_allowlist_blocks_unknown(self):
        assert not session_adapter.is_group_message_allowed(
            chat_id="03deadbeef",
            sender_id="05cafe",
            group_allowed_chats=["03aabb"],
            group_allowed_users=[],
        )

    def test_chat_allowlist_allows_listed(self):
        assert session_adapter.is_group_message_allowed(
            chat_id="03aabb",
            sender_id="05cafe",
            group_allowed_chats=["03aabb"],
            group_allowed_users=[],
        )

    def test_user_allowlist_blocks_unknown_sender(self):
        assert not session_adapter.is_group_message_allowed(
            chat_id="03aabb",
            sender_id="05nope",
            group_allowed_chats=[],
            group_allowed_users=["05yes"],
        )

    def test_user_allowlist_allows_listed_sender(self):
        assert session_adapter.is_group_message_allowed(
            chat_id="03aabb",
            sender_id="05yes",
            group_allowed_chats=[],
            group_allowed_users=["05yes"],
        )


class TestEnvEnablement:
    def test_none_without_bot_id(self, monkeypatch):
        monkeypatch.delenv("SESSION_BOT_ID", raising=False)
        assert session_adapter._env_enablement() is None

    def test_seeds_bot_id(self, monkeypatch):
        monkeypatch.setenv("SESSION_BOT_ID", "05" + "ab" * 32)
        monkeypatch.delenv("SESSION_HOME_CHANNEL", raising=False)
        monkeypatch.delenv("SESSION_BOT_NAME", raising=False)
        seed = session_adapter._env_enablement()
        assert seed is not None
        assert seed["bot_id"].startswith("05")
        assert "bridge_port" in seed
        assert "data_path" in seed
        assert "home_channel" not in seed

    def test_home_channel_seeded(self, monkeypatch):
        monkeypatch.setenv("SESSION_BOT_ID", "05" + "cd" * 32)
        monkeypatch.setenv("SESSION_HOME_CHANNEL", "05home")
        monkeypatch.setenv("SESSION_HOME_CHANNEL_NAME", "Me")
        seed = session_adapter._env_enablement()
        assert seed["home_channel"]["chat_id"] == "05home"
        assert seed["home_channel"]["name"] == "Me"


class TestValidateConfig:
    def test_true_with_env(self, monkeypatch):
        monkeypatch.setenv("SESSION_BOT_ID", "05abc")
        cfg = MagicMock()
        cfg.extra = {}
        assert session_adapter.validate_config(cfg) is True

    def test_true_with_extra(self, monkeypatch):
        monkeypatch.delenv("SESSION_BOT_ID", raising=False)
        cfg = MagicMock()
        cfg.extra = {"bot_id": "05abc"}
        assert session_adapter.validate_config(cfg) is True

    def test_false_without(self, monkeypatch):
        monkeypatch.delenv("SESSION_BOT_ID", raising=False)
        cfg = MagicMock()
        cfg.extra = {}
        assert session_adapter.validate_config(cfg) is False


class TestRequirements:
    def test_false_without_bot_id(self, monkeypatch):
        monkeypatch.delenv("SESSION_BOT_ID", raising=False)
        assert session_adapter.check_requirements() is False


class TestNodeResolution:
    def test_prefers_session_node_override(self, monkeypatch, tmp_path):
        fake = tmp_path / "node"
        fake.write_text("#!/bin/sh\necho v24.12.0\n")
        fake.chmod(0o755)
        monkeypatch.setenv("SESSION_NODE", str(fake))
        monkeypatch.setattr(
            session_adapter,
            "probe_node_version",
            lambda p: "24.12.0" if p == str(fake.resolve()) or p == str(fake) else None,
        )
        # Avoid real NVM / PATH noise
        monkeypatch.setattr(session_adapter, "_nvm_preferred_node_paths", lambda: [])
        monkeypatch.setenv("PATH", "")
        resolved = session_adapter.resolve_session_node()
        assert resolved is not None
        assert resolved.endswith("node")
        assert str(tmp_path) in resolved

    def test_skips_node_22(self, monkeypatch, tmp_path):
        old = tmp_path / "old" / "node"
        old.parent.mkdir()
        old.write_text("#!/bin/sh\necho v22.23.2\n")
        old.chmod(0o755)
        new = tmp_path / "new" / "node"
        new.parent.mkdir()
        new.write_text("#!/bin/sh\necho v24.12.0\n")
        new.chmod(0o755)

        def probe(p):
            if str(old) in p or p == str(old.resolve()):
                return "22.23.2"
            if str(new) in p or p == str(new.resolve()):
                return "24.12.0"
            return None

        monkeypatch.delenv("SESSION_NODE", raising=False)
        monkeypatch.setattr(session_adapter, "probe_node_version", probe)
        monkeypatch.setattr(session_adapter, "_nvm_preferred_node_paths", lambda: [])
        monkeypatch.setenv("PATH", f"{old.parent}:{new.parent}")
        resolved = session_adapter.resolve_session_node()
        assert resolved is not None
        assert str(new.parent) in resolved

    def test_prefers_pinned_nvm_path(self, monkeypatch, tmp_path):
        nvm_node = tmp_path / "versions" / "node" / "v24.12.0" / "bin" / "node"
        nvm_node.parent.mkdir(parents=True)
        nvm_node.write_text("#!/bin/sh\necho v24.12.0\n")
        nvm_node.chmod(0o755)

        hermes22 = tmp_path / "hermes22" / "node"
        hermes22.parent.mkdir()
        hermes22.write_text("#!/bin/sh\necho v22.23.2\n")
        hermes22.chmod(0o755)

        def probe(p):
            if "v24.12.0" in p:
                return "24.12.0"
            if "hermes22" in p:
                return "22.23.2"
            return None

        monkeypatch.delenv("SESSION_NODE", raising=False)
        monkeypatch.setattr(session_adapter, "probe_node_version", probe)
        monkeypatch.setattr(
            session_adapter,
            "_nvm_preferred_node_paths",
            lambda: [str(nvm_node)],
        )
        # Hermes 22 first on PATH — must still pick NVM 24.12
        monkeypatch.setenv("PATH", str(hermes22.parent))
        resolved = session_adapter.resolve_session_node()
        assert resolved is not None
        assert "v24.12.0" in resolved

    def test_node_meets_minimum(self):
        assert session_adapter.node_meets_minimum("24.12.0")
        assert session_adapter.node_meets_minimum("24.15.0")
        assert session_adapter.node_meets_minimum("26.4.0")
        assert not session_adapter.node_meets_minimum("22.23.2")
        assert not session_adapter.node_meets_minimum("24.11.9")


class TestRegister:
    def test_register_calls_ctx(self):
        ctx = MagicMock()
        session_adapter.register(ctx)
        ctx.register_platform.assert_called_once()
        kwargs = ctx.register_platform.call_args.kwargs
        assert kwargs["name"] == "session"
        assert kwargs["label"] == "Session"
        assert kwargs["cron_deliver_env_var"] == "SESSION_HOME_CHANNEL"
        assert kwargs["allowed_users_env"] == "SESSION_ALLOWED_USERS"
        assert kwargs["allow_all_env"] == "SESSION_ALLOW_ALL_USERS"
        assert kwargs["standalone_sender_fn"] is session_adapter._standalone_send
        assert kwargs["setup_fn"] is session_adapter.interactive_setup
        assert kwargs["env_enablement_fn"] is session_adapter._env_enablement
        assert "plain text" in kwargs["platform_hint"].lower()


class TestParseCsv:
    def test_empty(self, monkeypatch):
        monkeypatch.delenv("X_TEST", raising=False)
        assert session_adapter._parse_csv_env("X_TEST") == []

    def test_splits(self, monkeypatch):
        monkeypatch.setenv("X_TEST", "a, b ,c")
        assert session_adapter._parse_csv_env("X_TEST") == ["a", "b", "c"]

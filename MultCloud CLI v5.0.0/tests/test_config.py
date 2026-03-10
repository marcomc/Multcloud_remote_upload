"""Tests for the MultCloud config module."""

import os
import tempfile
from pathlib import Path

from multcloud.config import (
    DEFAULT_API_URL,
    DEFAULT_SESSION_DIR,
    DEFAULT_TIMEOUT,
    MultCloudConfig,
    find_config_file,
    load_config,
)


class TestMultCloudConfigDefaults:
    """Test MultCloudConfig default values."""

    def test_default_email_empty(self):
        cfg = MultCloudConfig()
        assert cfg.email == ""

    def test_default_password_empty(self):
        cfg = MultCloudConfig()
        assert cfg.password == ""

    def test_default_api_url(self):
        cfg = MultCloudConfig()
        assert cfg.api_base_url == DEFAULT_API_URL

    def test_default_timeout(self):
        cfg = MultCloudConfig()
        assert cfg.timeout == DEFAULT_TIMEOUT

    def test_default_debug_false(self):
        cfg = MultCloudConfig()
        assert cfg.debug is False

    def test_default_session_dir(self):
        cfg = MultCloudConfig()
        assert cfg.session_dir == DEFAULT_SESSION_DIR

    def test_default_auto_relogin_true(self):
        cfg = MultCloudConfig()
        assert cfg.auto_relogin is True

    def test_default_output_format_table(self):
        cfg = MultCloudConfig()
        assert cfg.output_format == "table"

    def test_default_config_path_none(self):
        cfg = MultCloudConfig()
        assert cfg.config_path is None

    def test_session_file_property(self):
        cfg = MultCloudConfig()
        assert cfg.session_file == DEFAULT_SESSION_DIR / "session.json"


class TestFindConfigFile:
    """Test config file discovery."""

    def test_returns_none_when_no_config_exists(self):
        # Use a path that definitely doesn't exist
        result = find_config_file("/nonexistent/path/config.toml")
        assert result is None

    def test_explicit_path_found(self):
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            f.write(b"[auth]\nemail = 'test'\n")
            tmppath = f.name
        try:
            result = find_config_file(tmppath)
            assert result == Path(tmppath)
        finally:
            os.unlink(tmppath)

    def test_env_var_overrides_defaults(self):
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            f.write(b"[auth]\nemail = 'env_test'\n")
            tmppath = f.name
        try:
            os.environ["MULTCLOUD_CONFIG"] = tmppath
            result = find_config_file()
            assert result == Path(tmppath)
        finally:
            del os.environ["MULTCLOUD_CONFIG"]
            os.unlink(tmppath)


class TestLoadConfig:
    """Test TOML config loading."""

    def test_load_defaults_when_no_file(self):
        cfg = load_config("/definitely/not/a/real/path.toml")
        assert cfg.email == ""
        assert cfg.api_base_url == DEFAULT_API_URL

    def test_load_from_toml_file(self):
        toml_content = b"""\
[auth]
email = "user@example.com"
password = "secret123"

[api]
base_url = "https://custom.api.com/v2"
timeout = 120
debug = true

[session]
auto_relogin = false

[output]
format = "json"
compact_json = true
"""
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            f.write(toml_content)
            tmppath = f.name
        try:
            cfg = load_config(tmppath)
            assert cfg.email == "user@example.com"
            assert cfg.password == "secret123"
            assert cfg.api_base_url == "https://custom.api.com/v2"
            assert cfg.timeout == 120
            assert cfg.debug is True
            assert cfg.auto_relogin is False
            assert cfg.output_format == "json"
            assert cfg.compact_json is True
            assert cfg.config_path == Path(tmppath)
        finally:
            os.unlink(tmppath)

    def test_partial_config_uses_defaults(self):
        toml_content = b"""\
[auth]
email = "partial@test.com"
"""
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            f.write(toml_content)
            tmppath = f.name
        try:
            cfg = load_config(tmppath)
            assert cfg.email == "partial@test.com"
            # Everything else should be defaults
            assert cfg.password == ""
            assert cfg.api_base_url == DEFAULT_API_URL
            assert cfg.timeout == DEFAULT_TIMEOUT
            assert cfg.debug is False
        finally:
            os.unlink(tmppath)

    def test_invalid_toml_returns_defaults(self):
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            f.write(b"this is not valid toml [[[[")
            tmppath = f.name
        try:
            cfg = load_config(tmppath)
            # Should fall back to defaults without crashing
            assert cfg.email == ""
            assert cfg.api_base_url == DEFAULT_API_URL
        finally:
            os.unlink(tmppath)

    def test_session_dir_expansion(self):
        toml_content = b"""\
[session]
session_dir = "/tmp/test_multcloud_session"
"""
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            f.write(toml_content)
            tmppath = f.name
        try:
            cfg = load_config(tmppath)
            assert cfg.session_dir == Path("/tmp/test_multcloud_session")
            assert cfg.session_file == Path("/tmp/test_multcloud_session/session.json")
        finally:
            os.unlink(tmppath)

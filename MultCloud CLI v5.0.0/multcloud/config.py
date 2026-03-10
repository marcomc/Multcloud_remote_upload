"""
Configuration management for MultCloud CLI.

Loads settings from TOML config file with fallback defaults.
Config resolution order: CLI flags > environment variables > config file > defaults.

Config file locations (first found wins):
    1. Path specified via --config flag or MULTCLOUD_CONFIG env var
    2. ~/.config/multcloud/config.toml
    3. ~/.multcloud/config.toml (legacy)
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Python 3.11+ has tomllib in stdlib; older versions need tomli
try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

CONFIG_SEARCH_PATHS = [
    Path.home() / ".config" / "multcloud" / "config.toml",
    Path.home() / ".multcloud" / "config.toml",
]

DEFAULT_API_URL = "https://app.multcloud.com/api"
DEFAULT_SESSION_DIR = Path.home() / ".multcloud"
DEFAULT_TIMEOUT = 60


@dataclass
class MultCloudConfig:
    """Parsed MultCloud CLI configuration."""

    # Auth
    email: str = ""
    password: str = ""

    # API
    api_base_url: str = DEFAULT_API_URL
    timeout: int = DEFAULT_TIMEOUT
    debug: bool = False

    # Session
    session_dir: Path = field(default_factory=lambda: DEFAULT_SESSION_DIR)
    auto_relogin: bool = True

    # Output
    output_format: str = "table"
    compact_json: bool = False

    # Meta
    config_path: Optional[Path] = None

    @property
    def session_file(self) -> Path:
        return self.session_dir / "session.json"


def find_config_file(explicit_path: str = None) -> Optional[Path]:
    """Find the config file, checking explicit path, env var, then defaults."""
    # 1. Explicit path from --config flag
    if explicit_path:
        p = Path(explicit_path).expanduser()
        if p.exists():
            return p
        print(f"Warning: Config file not found: {p}", file=sys.stderr)

    # 2. Environment variable
    env_path = os.environ.get("MULTCLOUD_CONFIG")
    if env_path:
        p = Path(env_path).expanduser()
        if p.exists():
            return p

    # 3. Search default locations
    for search_path in CONFIG_SEARCH_PATHS:
        if search_path.exists():
            return search_path

    return None


def load_config(config_path: str = None) -> MultCloudConfig:
    """Load configuration from TOML file with fallback defaults.

    Args:
        config_path: Optional explicit path to config file.

    Returns:
        MultCloudConfig with merged settings.
    """
    cfg = MultCloudConfig()
    found = find_config_file(config_path)

    if found is None or not found.exists() or not found.is_file():
        # No config file — use all defaults, that's fine
        return cfg

    cfg.config_path = found

    if tomllib is None:
        # Can't parse TOML without tomllib/tomli, silently use defaults
        print(
            "Warning: TOML parser not available (install tomli for Python <3.11). Using defaults.",
            file=sys.stderr,
        )
        return cfg

    try:
        with open(found, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        print(f"Warning: Could not parse config {found}: {e}", file=sys.stderr)
        return cfg

    # [auth]
    auth = data.get("auth", {})
    cfg.email = auth.get("email", cfg.email) or ""
    cfg.password = auth.get("password", cfg.password) or ""

    # [api]
    api = data.get("api", {})
    cfg.api_base_url = api.get("base_url", cfg.api_base_url) or DEFAULT_API_URL
    cfg.timeout = int(api.get("timeout", cfg.timeout))
    cfg.debug = bool(api.get("debug", cfg.debug))

    # [session]
    session = data.get("session", {})
    session_dir = session.get("session_dir", "")
    if session_dir:
        cfg.session_dir = Path(session_dir).expanduser()
    cfg.auto_relogin = bool(session.get("auto_relogin", cfg.auto_relogin))

    # [output]
    output = data.get("output", {})
    cfg.output_format = output.get("format", cfg.output_format)
    cfg.compact_json = bool(output.get("compact_json", cfg.compact_json))

    return cfg

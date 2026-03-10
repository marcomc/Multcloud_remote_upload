# Changelog

All notable changes to this project will be documented in this file.

## [5.1.0] - 2026-03-10

### Added
- **Makefile** with install/uninstall/test/lint/fmt/clean targets (follows mcpone-cli pattern)
- **TOML configuration** system (`~/.config/multcloud/config.toml`)
  - Interactive `make install-config` prompts for email, password, API URL
  - Config resolution: CLI flags > env vars > config file > defaults
  - `multcloud config show` and `multcloud config path` subcommands
- **Installable CLI** — `multcloud` linked to `~/.local/bin` via venv + symlink
- **Config test suite** — 18 tests for config defaults, file discovery, TOML loading
- `--config` / `-c` CLI flag to specify custom config file path
- `tomli` dependency for Python <3.11 TOML support

### Fixed
- Unused imports and lint warnings across all modules
- `config.py` Path("") bug that treated current directory as a valid config file
- Code formatting compliance (ruff format)

## [5.0.0] - 2026-03-10

### Added
- **Full CLI tool** (`MultCloud CLI v5.0.0/`) with comprehensive command set
- New `multcloud` command with subcommands for all API features:
  - `login`, `logout`, `whoami` - Authentication
  - `drives list|add|delete|rename` - Cloud drive management
  - `files list|mkdir|delete|rename|search|trash|empty-trash` - File operations
  - `tasks list|get|add-transfer|add-sync|add-remote-upload|execute|cancel|delete|progress|running|cleanup|versions` - Task management
  - `sync list|create|enable|disable|delete` - Realtime sync
  - `torrent add|delete|progress` - Torrent/magnet downloads
  - `video analyze|download|list|cancel` - Video saver
  - `share create|list|delete` - File sharing
  - `email list|delete` - Email migration
  - `team list|add|delete` - Sub-account management
  - `subscription redeem` - License management
  - `raw` - Direct API access
- **Updated AES keys** for March 2026 MultCloud frontend
  - Encrypt: `KXrDPHUkQSMKhklkKHHP+Q==`
  - Decrypt: `LIa4CTfB3SwKnfJhu2iJkQ==`
- **Updated login endpoint** from `/user/sign_in` to `/user/sign_in_`
- Separate encrypt/decrypt keys (previously shared single key)
- Session persistence (`~/.multcloud/session.json`)
- CAPTCHA handling with image display
- Support for 35+ cloud providers
- Reverse-engineering script (`scripts/reverse_engineer_api.py`)
- Comprehensive API documentation (`docs/API_REFERENCE.md`)
- CLI usage guide (`docs/CLI_USAGE.md`)
- Reverse-engineering guide (`docs/REVERSE_ENGINEERING.md`)
- Project tracking files (`AGENTS.md`, `TODO.md`)

### Changed
- Complete rewrite of the API client library
- Moved from SQLAlchemy session storage to simple JSON file
- Removed tkinter dependency (CAPTCHA saved as file instead)
- Proper Python packaging with `pyproject.toml`

### Security
- No longer uses `eval()` for data deserialization (was in old v4.6.7 code)
- Removed `verify=False` - TLS verification is now enabled
- No longer uses `exec()` for command mode

## [4.6.7] - 2021 (Original)

### Features
- Remote URL upload to Google Drive
- Bulk upload support
- Multiple account management with SQLAlchemy
- CAPTCHA support with tkinter GUI
- AES key: `Ns1F8bpJ1LJcHvvcH2sqFA==`

## [4.5.5] - 2021 (Original)

### Features
- Initial remote upload functionality
- Basic account management

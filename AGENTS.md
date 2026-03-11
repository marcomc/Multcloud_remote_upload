# AGENTS.md - MultCloud CLI Project

## Project Overview

This is a fork of [ayush1920/Multcloud_remote_upload](https://github.com/ayush1920/Multcloud_remote_upload)
that expands the original remote-upload tool into a comprehensive CLI client for MultCloud's
internal (reverse-engineered) API.

## Repository Structure

```
.
├── Mulcloud API v4.5.5/     # Original API version (legacy, outdated keys)
├── Mulcloud API v4.6.7/     # Updated API version (legacy, outdated keys)
├── MultCloud CLI v5.0.0/    # NEW - Full CLI tool with updated API
│   ├── multcloud/
│   │   ├── __init__.py      # Package init, version string
│   │   ├── __main__.py      # python -m multcloud entry point
│   │   ├── crypto.py        # AES encryption/decryption + MD5 request signing
│   │   ├── client.py        # MultCloudClient - all API endpoint methods
│   │   ├── config.py        # TOML config loading + defaults
│   │   └── cli.py           # argparse CLI with all commands
│   ├── scripts/
│   │   └── reverse_engineer_api.py  # Script to re-extract API from JS bundle
│   ├── tests/
│   │   ├── test_crypto.py   # 17 crypto tests
│   │   └── test_config.py   # 18 config tests
│   ├── Makefile             # install/uninstall/test/lint/fmt/clean targets
│   ├── .multcloud.toml.example  # Config template for make install-config
│   ├── pyproject.toml       # Python packaging config
│   ├── setup.py             # Setuptools fallback for older pip
│   └── requirements.txt     # Dependencies
├── docs/
│   ├── API_REFERENCE.md     # Full API endpoint documentation
│   ├── CLI_USAGE.md         # CLI usage guide with examples
│   └── REVERSE_ENGINEERING.md # How to update the API when MultCloud changes
├── .markdownlint.json       # Markdownlint config (MD013 line length disabled)
├── API_ANALYSIS.md          # Summary of reverse-engineering findings
├── AGENTS.md                # This file - project context for AI agents
├── TODO.md                  # Remaining work items
└── CHANGELOG.md             # Change history
```

## Key Technical Details

### API Architecture
- MultCloud uses AES-ECB encryption for API responses (hex-encoded)
- Requests are signed with MD5-based HMAC using a specific key-value pairing algorithm
- Two signing modes: **salt-based** (authenticated) and **AES-key-based** (unauthenticated)
- The AES keys are constants extracted from MultCloud's webpack JS bundle

### Current AES Keys (March 2026)
- Encrypt: `KXrDPHUkQSMKhklkKHHP+Q==`
- Decrypt: `LIa4CTfB3SwKnfJhu2iJkQ==`
- **Old key** (pre-2026): `Ns1F8bpJ1LJcHvvcH2sqFA==` — no longer works

### Signing Algorithm
1. Sort parameter keys alphabetically
2. Pair keys ascending with values descending
3. For objects/arrays: `JSON.stringify()` -> sort chars -> MD5
4. Concatenate all key+inspect(value) pairs
5. MD5 hash, return `hash[1:-2]`

### Task Types
- Type 1: Cloud Transfer
- Type 3: Remote Upload (URL to cloud)
- Type 6: Cloud Sync / Cloud Backup

## Development Workflow

```bash
cd "MultCloud CLI v5.0.0"
make install      # Create venv, install deps, link to ~/.local/bin, seed config
make test         # Run pytest suite
make lint         # Run ruff linter
make fmt          # Auto-format with ruff
make uninstall    # Remove symlink from ~/.local/bin
make clean        # Remove venv and build artifacts
```

## Markdown Linting

All markdown files in this repo must be linted before committing.
The `.markdownlint.json` config at the repo root disables MD013 (line length).

```bash
# Lint all markdown files
markdownlint '**/*.md'

# Or with npx if not installed globally
npx markdownlint-cli '**/*.md'
```

## When MultCloud Updates Their Frontend

Run the reverse-engineering script:

```bash
python scripts/reverse_engineer_api.py --output ../docs/ --diff --verbose
```

This will detect changes in AES keys, endpoints, and cloud types. See
`docs/REVERSE_ENGINEERING.md` for the full manual process.

## Dependencies

- Python >= 3.9
- pycryptodome (AES encryption)
- requests (HTTP client)
- tomli (TOML parsing for Python < 3.11)

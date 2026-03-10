SHELL := /bin/bash
VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PREFIX ?= $(HOME)/.local
BINDIR ?= $(PREFIX)/bin
INSTALL_NAME ?= multcloud
INSTALL_PATH ?= $(BINDIR)/$(INSTALL_NAME)
CONFIG_SAMPLE ?= .multcloud.toml.example
CONFIG_DIR ?= $(HOME)/.config/multcloud
CONFIG_DEST ?= $(CONFIG_DIR)/config.toml
SESSION_DIR ?= $(HOME)/.multcloud
MARKDOWN_FILES := ../README.md ../CHANGELOG.md ../TODO.md ../AGENTS.md ../docs/*.md

.DEFAULT_GOAL := help

.PHONY: help check-deps venv install install-dev install-link install-config \
        uninstall reinstall lint fmt test run clean

help: ## Show available targets
	@awk 'BEGIN { FS = ":.*##" } /^[a-zA-Z_-]+:.*##/ { printf "  %-18s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

check-deps: ## Verify required system prerequisites
	@echo "Checking prerequisites..."
	@command -v python3 >/dev/null 2>&1 \
		|| { echo "✗ python3 not found"; exit 1; }
	@python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)" \
		|| { echo "✗ Python 3.9+ required (found $$(python3 --version 2>&1))"; exit 1; }
	@echo "✓ python3 $$(python3 --version 2>&1 | awk '{print $$2}')"
	@mkdir -p "$(BINDIR)"
	@echo "✓ $(BINDIR)"
	@if echo "$$PATH" | tr ':' '\n' | grep -Fxq "$(BINDIR)"; then \
		echo "✓ $(BINDIR) is on PATH"; \
	else \
		echo "⚠ $(BINDIR) is not on PATH"; \
		echo "  Add this to your shell profile:"; \
		echo "  export PATH=\"$(BINDIR):\$$PATH\""; \
	fi

venv: ## Create the virtual environment
	@if [ ! -x "$(PY)" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv $(VENV); \
		$(PIP) install --upgrade pip --quiet; \
		echo "✓ Virtual environment created"; \
	else \
		echo "✓ Virtual environment already exists"; \
	fi

install: check-deps venv install-config ## Install runtime deps, config, and link CLI into ~/.local/bin
	$(PIP) install -e . --quiet
	@$(MAKE) install-link
	@echo ""
	@echo "✓ MultCloud CLI installed successfully"
	@echo "  Run: $(INSTALL_NAME) --help"
	@echo "  Config: $(CONFIG_DEST)"

install-dev: check-deps venv ## Install dev deps and link CLI into ~/.local/bin
	$(PIP) install -e ".[dev]" --quiet
	@$(MAKE) install-link

install-link: ## Create symlink in ~/.local/bin
	@mkdir -p "$(BINDIR)"
	@if [ -x "$(CURDIR)/$(VENV)/bin/$(INSTALL_NAME)" ]; then \
		ln -sf "$(CURDIR)/$(VENV)/bin/$(INSTALL_NAME)" "$(INSTALL_PATH)"; \
		echo "✓ Linked $(INSTALL_NAME) → $(INSTALL_PATH)"; \
	else \
		echo "✗ $(CURDIR)/$(VENV)/bin/$(INSTALL_NAME) not found."; \
		echo "  Run 'make install' first."; \
		exit 1; \
	fi

install-config: ## Seed user config from template (interactive, only if missing)
	@mkdir -p "$(CONFIG_DIR)"
	@mkdir -p "$(SESSION_DIR)"
	@if [ ! -f "$(CONFIG_DEST)" ]; then \
		echo ""; \
		echo "── MultCloud Configuration ──"; \
		echo ""; \
		printf "MultCloud email address: "; \
		read -r mc_email; \
		mc_email=$${mc_email:-""}; \
		printf "Store password in config? (leave blank to enter at login) []: "; \
		read -r mc_password; \
		mc_password=$${mc_password:-""}; \
		printf "API base URL [https://app.multcloud.com/api]: "; \
		read -r mc_api_url; \
		mc_api_url=$${mc_api_url:-"https://app.multcloud.com/api"}; \
		sed \
			-e "s|__EMAIL__|$$mc_email|g" \
			-e "s|__PASSWORD__|$$mc_password|g" \
			-e "s|__API_URL__|$$mc_api_url|g" \
			-e "s|__SESSION_DIR__|$(SESSION_DIR)|g" \
			"$(CONFIG_SAMPLE)" > "$(CONFIG_DEST)"; \
		chmod 600 "$(CONFIG_DEST)"; \
		echo ""; \
		echo "✓ Config written to $(CONFIG_DEST) (mode 600)"; \
		if [ -n "$$mc_password" ]; then \
			echo "⚠ Password stored in config — keep this file private!"; \
		fi; \
	else \
		echo "✓ Config already exists at $(CONFIG_DEST) (left unchanged)"; \
	fi

uninstall: ## Remove CLI link from ~/.local/bin (config preserved)
	@rm -f "$(INSTALL_PATH)"
	@echo "✓ Removed $(INSTALL_PATH)"
	@echo "  Config preserved at $(CONFIG_DEST)"
	@echo "  Session preserved at $(SESSION_DIR)"
	@echo "  To remove config:  rm -rf $(CONFIG_DIR)"
	@echo "  To remove session: rm -rf $(SESSION_DIR)"

reinstall: uninstall install ## Reinstall everything

lint: install-dev ## Lint Python and Markdown files
	$(PY) -m ruff check multcloud tests
	$(PY) -m ruff format --check multcloud tests

fmt: install-dev ## Auto-format Python files
	$(PY) -m ruff format multcloud tests

test: install-dev ## Run the test suite
	$(PY) -m pytest tests/ -v

run: install ## Show CLI help
	"$(INSTALL_PATH)" --help

clean: ## Remove virtualenv and build artifacts
	rm -rf $(VENV) .pytest_cache .ruff_cache build dist *.egg-info multcloud_cli.egg-info
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned build artifacts"

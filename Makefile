# Root-level Makefile — delegates to MultCloud CLI v5.0.0/
CLI_DIR := MultCloud\ CLI\ v5.0.0

.DEFAULT_GOAL := help

.PHONY: help check-deps install install-dev install-config uninstall reinstall \
        lint lint-md fmt test run clean

help: ## Show available targets
	@$(MAKE) -C $(CLI_DIR) help

check-deps: ## Verify required system prerequisites
	@$(MAKE) -C $(CLI_DIR) check-deps

install: ## Install runtime deps, config, and link CLI into ~/.local/bin
	@$(MAKE) -C $(CLI_DIR) install

install-dev: ## Install dev deps and link CLI into ~/.local/bin
	@$(MAKE) -C $(CLI_DIR) install-dev

install-config: ## Seed user config from template (interactive, only if missing)
	@$(MAKE) -C $(CLI_DIR) install-config

uninstall: ## Remove CLI link from ~/.local/bin (config preserved)
	@$(MAKE) -C $(CLI_DIR) uninstall

reinstall: ## Reinstall everything
	@$(MAKE) -C $(CLI_DIR) reinstall

lint: ## Lint Python and Markdown files
	@$(MAKE) -C $(CLI_DIR) lint
	@$(MAKE) lint-md

lint-md: ## Lint all Markdown files in the repo
	@if command -v markdownlint >/dev/null 2>&1; then \
		echo "Linting markdown files..."; \
		markdownlint '**/*.md' --ignore '**/node_modules/**' --ignore '**/.venv/**'; \
		echo "✓ Markdown lint passed"; \
	elif command -v npx >/dev/null 2>&1; then \
		echo "Linting markdown files (via npx)..."; \
		npx --yes markdownlint-cli '**/*.md' --ignore '**/node_modules/**' --ignore '**/.venv/**'; \
		echo "✓ Markdown lint passed"; \
	else \
		echo "⚠ markdownlint not found — skipping markdown lint"; \
		echo "  Install: npm install -g markdownlint-cli"; \
	fi

fmt: ## Auto-format Python files
	@$(MAKE) -C $(CLI_DIR) fmt

test: ## Run the test suite
	@$(MAKE) -C $(CLI_DIR) test

run: ## Show CLI help
	@$(MAKE) -C $(CLI_DIR) run

clean: ## Remove virtualenv and build artifacts
	@$(MAKE) -C $(CLI_DIR) clean

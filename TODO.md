# TODO

## Completed
- [x] Fork repo to personal GitHub account
- [x] Analyze MultCloud's current frontend JS for API changes
- [x] Document all discovered API endpoints
- [x] Build crypto module (AES-ECB + MD5 signing)
- [x] Build full API client library (`client.py`)
- [x] Build comprehensive CLI with all commands (`cli.py`)
- [x] Create API reference documentation
- [x] Create CLI usage guide
- [x] Create reverse-engineering script
- [x] Create project tracking files (AGENTS.md, TODO.md, CHANGELOG.md)

## To Do

### High Priority
- [ ] Add unit tests for crypto module (known input/output pairs)
- [ ] Add integration tests (with mock server or real credentials)
- [ ] Test login flow with real MultCloud account
- [ ] Test CAPTCHA handling flow
- [ ] Verify response decryption with real API responses

### Medium Priority
- [ ] Add `--output-format` option (table/json/csv) to all list commands
- [ ] Add `files copy` and `files move` CLI commands with drive:path syntax
- [ ] Add `files restore` CLI command
- [ ] Add `files download` command (download file content locally)
- [ ] Add `tasks add-backup` command specifically for backup tasks
- [ ] Add schedule management (cron-like scheduling for tasks)
- [ ] Add filter options for task creation (file type, size, date filters)
- [ ] Add progress bar for long-running operations
- [ ] Add retry logic with exponential backoff for transient failures
- [ ] Add `--config` option for custom config file location

### Low Priority
- [ ] Add shell completions (bash, zsh, fish)
- [ ] Add `multcloud interactive` mode (REPL)
- [ ] Package for PyPI distribution
- [ ] Add Docker image
- [ ] Add CI/CD pipeline
- [ ] Support for environment variable configuration (MULTCLOUD_EMAIL, etc.)
- [ ] Add `multcloud watch` command to monitor task progress in real-time
- [ ] Add bulk operations (batch delete, batch execute)

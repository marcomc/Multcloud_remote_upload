# MultCloud CLI Usage Guide

## Installation

```bash
cd "MultCloud CLI v5.0.0"
pip install -e .
# or
pip install -r requirements.txt
```

## Quick Start

```bash
# Login
multcloud login --email you@example.com

# List connected drives
multcloud drives list

# List files on a drive
multcloud files list DRIVE_ID

# Trigger an existing sync task
multcloud tasks execute TASK_ID

# List all tasks
multcloud tasks list --all
```

## Authentication

```bash
# Interactive login (prompts for email/password)
multcloud login

# Non-interactive login
multcloud login --email you@example.com --password yourpassword

# Check who you're logged in as
multcloud whoami

# Logout
multcloud logout
```

Session data is saved to `~/.multcloud/session.json` and reused across invocations.
If MultCloud requires a CAPTCHA, the image is saved to `~/.multcloud/captcha.png`
and opened automatically (macOS).

## Drive Management

```bash
# List all connected cloud drives
multcloud drives list

# Add a new cloud drive (opens OAuth URL)
multcloud drives add google_drive

# Rename a drive
multcloud drives rename DRIVE_ID "My Google Drive"

# Remove a drive
multcloud drives delete DRIVE_ID
```

## File Operations

```bash
# List files (root directory)
multcloud files list DRIVE_ID

# List files in a specific folder
multcloud files list DRIVE_ID --path FOLDER_ID

# Create a directory
multcloud files mkdir DRIVE_ID "New Folder" --parent PARENT_ID

# Delete files
multcloud files delete DRIVE_ID FILE_ID1 FILE_ID2

# Rename a file
multcloud files rename DRIVE_ID FILE_ID "new_name.txt"

# Search for files
multcloud files search DRIVE_ID "keyword"

# View recycle bin
multcloud files trash DRIVE_ID

# Empty recycle bin
multcloud files empty-trash DRIVE_ID
```

## Tasks (Transfer / Sync / Backup)

```bash
# List all tasks
multcloud tasks list --all

# List tasks by type (1=Transfer, 3=RemoteUpload, 6=Sync)
multcloud tasks list --type 6

# Get task details
multcloud tasks get TASK_ID

# Create a cloud transfer task
multcloud tasks add-transfer FROM_DRIVE_ID TO_DRIVE_ID --name "Daily Backup"

# Create a cloud sync task
multcloud tasks add-sync FROM_DRIVE_ID TO_DRIVE_ID --sync-mode simple

# Remote upload a URL to cloud
multcloud tasks add-remote-upload "https://example.com/file.zip" "file.zip" DRIVE_ID

# TRIGGER an existing task to run NOW
multcloud tasks execute TASK_ID

# Check task progress
multcloud tasks progress TASK_ID

# Cancel a running task
multcloud tasks cancel TASK_ID

# Delete a task
multcloud tasks delete TASK_ID

# List currently running tasks
multcloud tasks running

# Clean up completed tasks
multcloud tasks cleanup

# List backup versions
multcloud tasks versions TASK_ID
```

## Realtime Sync

```bash
# List realtime syncs
multcloud sync list

# Create a realtime sync
multcloud sync create FROM_DRIVE_ID TO_DRIVE_ID --type two_way

# Enable a realtime sync
multcloud sync enable SYNC_ID

# Disable a realtime sync
multcloud sync disable SYNC_ID

# Delete a realtime sync
multcloud sync delete SYNC_ID
```

## Torrent Downloads

```bash
# Add torrent/magnet download to cloud
multcloud torrent add "magnet:?xt=..." DRIVE_ID

# Check torrent progress
multcloud torrent progress TASK_ID

# Delete torrent task
multcloud torrent delete TASK_ID
```

## Video Saver

```bash
# Analyze a video URL
multcloud video analyze "https://www.youtube.com/watch?v=..."

# Download video to cloud
multcloud video download "https://www.youtube.com/watch?v=..." DRIVE_ID

# List video saver tasks
multcloud video list

# Cancel video download
multcloud video cancel TASK_ID
```

## File Sharing

```bash
# Create a share link
multcloud share create DRIVE_ID FILE_ID --password mypassword

# List all shares
multcloud share list

# Disable a share
multcloud share delete SHARE_ID
```

## Email Migration

```bash
# List email migrations
multcloud email list

# Delete an email migration
multcloud email delete TASK_ID
```

## Team / Sub-accounts

```bash
# List sub-accounts
multcloud team list

# Add a sub-account
multcloud team add user@example.com

# Delete a sub-account
multcloud team delete SUB_ID
```

## Subscription

```bash
# Redeem a license key
multcloud subscription redeem LICENSE_KEY
```

## Raw API Access

For endpoints not covered by the CLI commands:

```bash
# Send any POST request to the API
multcloud raw POST /tasks/list --data '{"type": 1}'

# Use with verbose logging to see full request/response
multcloud -v raw POST /drives/list_categories
```

## Global Options

```bash
# Enable debug/verbose logging
multcloud -v drives list

# Output raw JSON (for piping to jq, etc.)
multcloud --json tasks list --all
```

## Environment

- Session stored at: `~/.multcloud/session.json`
- CAPTCHA images: `~/.multcloud/captcha.png`

## Scripting Examples

```bash
# List all drive IDs
multcloud --json drives list | jq -r '.[].id'

# Trigger all sync tasks
for id in $(multcloud --json tasks list --type 6 | jq -r '.[].id'); do
  multcloud tasks execute "$id"
done

# Monitor a running task
watch -n 5 "multcloud tasks progress TASK_ID"
```

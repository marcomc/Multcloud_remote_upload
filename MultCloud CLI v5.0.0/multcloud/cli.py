#!/usr/bin/env python3
"""
MultCloud CLI - Command-line interface for MultCloud's internal API.

Usage:
    multcloud login [--email EMAIL] [--password PASSWORD]
    multcloud logout
    multcloud whoami
    multcloud drives list
    multcloud drives add <cloud_type>
    multcloud drives delete <drive_id>
    multcloud drives rename <drive_id> <name>
    multcloud files list <drive_id> [--path PATH]
    multcloud files mkdir <drive_id> <name> [--parent PARENT_ID]
    multcloud files delete <drive_id> <file_id>...
    multcloud files rename <drive_id> <file_id> <new_name>
    multcloud files search <drive_id> <keyword>
    multcloud files copy <src_drive>:<src_path> <dst_drive>:<dst_path>
    multcloud files move <src_drive>:<src_path> <dst_drive>:<dst_path>
    multcloud files trash <drive_id>
    multcloud files empty-trash <drive_id>
    multcloud tasks list [--type TYPE] [--all]
    multcloud tasks get <task_id>
    multcloud tasks add-transfer <from_drive_id> <to_drive_id> [--name NAME] [--schedule SCHEDULE]
    multcloud tasks add-sync <from_drive_id> <to_drive_id> [--name NAME] [--sync-mode MODE]
    multcloud tasks add-remote-upload <url> <filename> <drive_id>
    multcloud tasks execute <task_id>
    multcloud tasks cancel <task_id>
    multcloud tasks delete <task_id>
    multcloud tasks progress <task_id>
    multcloud tasks running
    multcloud tasks cleanup
    multcloud tasks versions <task_id>
    multcloud sync list
    multcloud sync create <from_drive_id> <to_drive_id> [--type TYPE]
    multcloud sync enable <sync_id>
    multcloud sync disable <sync_id>
    multcloud sync delete <sync_id>
    multcloud torrent add <magnet_or_url> <drive_id>
    multcloud torrent delete <task_id>
    multcloud torrent progress <task_id>
    multcloud video analyze <url>
    multcloud video download <url> <drive_id>
    multcloud video list
    multcloud video cancel <task_id>
    multcloud share create <drive_id> <file_id> [--password PASSWORD]
    multcloud share list
    multcloud share delete <share_id>
    multcloud email list
    multcloud email delete <task_id>
    multcloud team list
    multcloud team add <email>
    multcloud team delete <sub_id>
    multcloud subscription redeem <license_key>
    multcloud raw <method> <endpoint> [--data JSON]
"""

import argparse
import getpass
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from .client import MultCloudClient, MultCloudError

SESSION_DIR = Path.home() / ".multcloud"
SESSION_FILE = SESSION_DIR / "session.json"
CONFIG_FILE = SESSION_DIR / "config.json"

# Cloud type display names
CLOUD_TYPES = {
    "google_drive": "Google Drive",
    "dropbox": "Dropbox",
    "onedrive": "OneDrive",
    "onedrive4Business": "OneDrive for Business",
    "box": "Box",
    "mega": "MEGA",
    "pcloud": "pCloud",
    "s3": "Amazon S3",
    "ftp": "FTP",
    "sftp": "SFTP",
    "webdav": "WebDAV",
    "google_photos": "Google Photos",
    "flickr": "Flickr",
    "google_workspace": "Google Workspace",
    "sharepoint": "SharePoint",
    "backblaze": "Backblaze B2",
    "wasabi": "Wasabi",
    "icloud_drive": "iCloud Drive",
    "aDrive": "aDrive",
    "baidu": "Baidu Cloud",
    "yandex": "Yandex Disk",
    "hubic": "hubiC",
    "sugarsync": "SugarSync",
    "cloudme": "CloudMe",
    "cubby": "Cubby",
    "myDrive": "MyDrive",
    "webo": "WEB.DE",
    "hidrive": "HiDrive",
    "mediafire": "MediaFire",
    "owncloud": "ownCloud",
    "mysql": "MySQL",
    "nas": "NAS",
    "1fichier": "1Fichier",
    "icedrive": "Icedrive",
    "idrive": "IDrive e2",
    "google_cloud_storage": "Google Cloud Storage",
    "azure_blob": "Azure Blob",
    "dropbox4Business": "Dropbox Business",
}


def get_client() -> MultCloudClient:
    """Create a client and load any saved session."""
    client = MultCloudClient()
    if SESSION_FILE.exists():
        client.load_session(SESSION_FILE)
    return client


def ensure_logged_in(client: MultCloudClient):
    """Verify the client is authenticated."""
    if not client.user:
        print("Error: Not logged in. Run 'multcloud login' first.", file=sys.stderr)
        sys.exit(1)


def print_json(data, compact: bool = False):
    """Pretty-print JSON data."""
    if compact:
        print(json.dumps(data, default=str))
    else:
        print(json.dumps(data, indent=2, default=str))


def print_table(rows: list, headers: list):
    """Print a formatted table."""
    if not rows:
        print("(empty)")
        return
    col_widths = [len(h) for h in headers]
    str_rows = []
    for row in rows:
        str_row = [str(v) for v in row]
        str_rows.append(str_row)
        for i, v in enumerate(str_row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(v))
    fmt = "  ".join(f"{{:<{w}}}" for w in col_widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in col_widths]))
    for row in str_rows:
        # Pad row to match headers length
        while len(row) < len(headers):
            row.append("")
        print(fmt.format(*row[:len(headers)]))


def format_size(size) -> str:
    """Format byte size to human-readable."""
    try:
        size = int(size)
    except (ValueError, TypeError):
        return str(size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size) < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


# ── Command handlers ───────────────────────────────────────────────


def cmd_login(args, client):
    """Handle login command."""
    email = args.email or input("Email: ")
    password = args.password or getpass.getpass("Password: ")

    try:
        user = client.login(email, password)
        client.save_session(SESSION_FILE)
        print(f"Logged in as {user.get('username', user.get('email', email))}")
        if user.get("vip"):
            print(f"  Plan: {user.get('payType', 'N/A')} (Level {user.get('payLevel', 'N/A')})")
    except MultCloudError as e:
        if "verifyCode" in str(e.reason):
            print("CAPTCHA required. Generating...")
            vkey, image_data = client.generate_captcha()
            captcha_path = SESSION_DIR / "captcha.png"
            captcha_path.parent.mkdir(parents=True, exist_ok=True)
            captcha_path.write_bytes(image_data)
            print(f"CAPTCHA image saved to: {captcha_path}")
            try:
                import subprocess
                subprocess.Popen(["open", str(captcha_path)])
            except Exception:
                pass
            vcode = input("Enter CAPTCHA code: ")
            user = client.login_with_captcha(email, password, vkey, vcode)
            client.save_session(SESSION_FILE)
            print(f"Logged in as {user.get('username', user.get('email', email))}")
        else:
            raise


def cmd_logout(args, client):
    """Handle logout command."""
    ensure_logged_in(client)
    try:
        client.logout()
    except MultCloudError:
        pass
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()
    print("Logged out.")


def cmd_whoami(args, client):
    """Show current user info."""
    ensure_logged_in(client)
    user = client.user_get()
    print(f"User ID:  {user.get('id', 'N/A')}")
    print(f"Username: {user.get('username', 'N/A')}")
    print(f"Email:    {user.get('email', 'N/A')}")
    print(f"VIP:      {user.get('vip', False)}")
    if user.get("vip"):
        print(f"Plan:     {user.get('payType', 'N/A')}")
        print(f"Level:    {user.get('payLevel', 'N/A')}")


def cmd_drives_list(args, client):
    """List connected cloud drives."""
    ensure_logged_in(client)
    drives = client.drives_list()
    if not drives:
        print("No cloud drives connected.")
        return
    rows = []
    for d in drives:
        cloud = d.get("cloudType", d.get("appName", "unknown"))
        rows.append([
            d.get("id", ""),
            CLOUD_TYPES.get(cloud, cloud),
            d.get("name", d.get("email", "")),
            d.get("email", ""),
        ])
    print_table(rows, ["ID", "Type", "Name", "Account"])


def cmd_drives_add(args, client):
    """Add a new cloud drive."""
    ensure_logged_in(client)
    cloud_type = args.cloud_type
    if cloud_type not in CLOUD_TYPES and cloud_type not in CLOUD_TYPES.values():
        print(f"Unknown cloud type: {cloud_type}")
        print("\nAvailable cloud types:")
        for k, v in sorted(CLOUD_TYPES.items()):
            print(f"  {k:30s} {v}")
        sys.exit(1)
    result = client.drives_add(cloud_type)
    if isinstance(result, dict) and result.get("authUrl"):
        print(f"Open this URL to authorize:\n{result['authUrl']}")
    else:
        print_json(result)


def cmd_drives_delete(args, client):
    """Delete a cloud drive."""
    ensure_logged_in(client)
    client.drives_delete(args.drive_id)
    print(f"Drive {args.drive_id} deleted.")


def cmd_drives_rename(args, client):
    """Rename a cloud drive."""
    ensure_logged_in(client)
    client.drives_rename(args.drive_id, args.name)
    print(f"Drive {args.drive_id} renamed to '{args.name}'.")


def cmd_files_list(args, client):
    """List files in a directory."""
    ensure_logged_in(client)
    files = client.files_list(args.drive_id, file_id=args.path or "root")
    if not files:
        print("(empty directory)")
        return
    rows = []
    for f in files:
        ftype = "DIR" if f.get("dir") else "FILE"
        rows.append([
            f.get("id", f.get("fileId", "")),
            ftype,
            format_size(f.get("size", 0)),
            f.get("name", ""),
        ])
    print_table(rows, ["ID", "Type", "Size", "Name"])


def cmd_files_mkdir(args, client):
    """Create a directory."""
    ensure_logged_in(client)
    client.files_mkdir(args.drive_id, args.parent or "root", args.name)
    print(f"Directory '{args.name}' created.")


def cmd_files_delete(args, client):
    """Delete files."""
    ensure_logged_in(client)
    client.files_delete(args.drive_id, args.file_ids)
    print(f"Deleted {len(args.file_ids)} item(s).")


def cmd_files_rename(args, client):
    """Rename a file."""
    ensure_logged_in(client)
    client.files_rename(args.drive_id, args.file_id, args.new_name)
    print(f"Renamed to '{args.new_name}'.")


def cmd_files_search(args, client):
    """Search files."""
    ensure_logged_in(client)
    files = client.files_search(args.drive_id, args.keyword)
    if not files:
        print("No results found.")
        return
    rows = []
    for f in files:
        ftype = "DIR" if f.get("dir") else "FILE"
        rows.append([f.get("id", ""), ftype, format_size(f.get("size", 0)), f.get("name", "")])
    print_table(rows, ["ID", "Type", "Size", "Name"])


def cmd_files_trash(args, client):
    """List recycle bin contents."""
    ensure_logged_in(client)
    files = client.files_recycle_bin(args.drive_id)
    if not files:
        print("Recycle bin is empty.")
        return
    rows = []
    for f in files:
        rows.append([f.get("id", ""), format_size(f.get("size", 0)), f.get("name", "")])
    print_table(rows, ["ID", "Size", "Name"])


def cmd_files_empty_trash(args, client):
    """Empty the recycle bin."""
    ensure_logged_in(client)
    client.files_empty_trash(args.drive_id)
    print("Recycle bin emptied.")


def cmd_tasks_list(args, client):
    """List tasks."""
    ensure_logged_in(client)
    if args.all:
        tasks = client.tasks_all_list()
    else:
        task_type = int(args.type) if args.type else None
        tasks = client.tasks_list(task_type)
    if not tasks:
        print("No tasks found.")
        return
    type_names = {1: "Transfer", 3: "Remote Upload", 6: "Sync/Backup"}
    rows = []
    for t in tasks:
        ttype = type_names.get(t.get("type"), str(t.get("type", "?")))
        rows.append([
            t.get("id", ""),
            ttype,
            t.get("name", t.get("n", "")),
            t.get("result", t.get("status", "")),
            format_size(t.get("filesize", 0)),
        ])
    print_table(rows, ["ID", "Type", "Name", "Status", "Size"])


def cmd_tasks_get(args, client):
    """Get task details."""
    ensure_logged_in(client)
    task = client.tasks_get(args.task_id)
    print_json(task)


def cmd_tasks_add_transfer(args, client):
    """Create a cloud transfer task."""
    ensure_logged_in(client)
    from_items = [{"driveId": args.from_drive_id, "fileId": "root", "pid": "root", "isDir": True}]
    to_items = [{"driveId": args.to_drive_id, "fileId": "root", "pid": "root", "isDir": True}]
    options = {}
    if args.schedule:
        options["scheduleTime"] = args.schedule
    result = client.tasks_add(1, from_items, to_items, name=args.name or "", options=options or None)
    print("Transfer task created:")
    print_json(result)


def cmd_tasks_add_sync(args, client):
    """Create a cloud sync task."""
    ensure_logged_in(client)
    from_items = [{"driveId": args.from_drive_id, "fileId": "root", "pid": "root", "isDir": True}]
    to_items = [{"driveId": args.to_drive_id, "fileId": "root", "pid": "root", "isDir": True}]
    options = {}
    if args.sync_mode:
        options["syncMode"] = args.sync_mode
    result = client.tasks_add(6, from_items, to_items, name=args.name or "", options=options or None)
    print("Sync task created:")
    print_json(result)


def cmd_tasks_add_remote_upload(args, client):
    """Add a remote upload task."""
    ensure_logged_in(client)
    result = client.tasks_add_remote_upload(args.url, args.filename, args.drive_id)
    print("Remote upload task created:")
    print_json(result)


def cmd_tasks_execute(args, client):
    """Execute a task."""
    ensure_logged_in(client)
    result = client.tasks_execute(args.task_id)
    print(f"Task {args.task_id} triggered.")
    if isinstance(result, dict):
        print_json(result)


def cmd_tasks_cancel(args, client):
    """Cancel a task."""
    ensure_logged_in(client)
    client.tasks_cancel(args.task_id)
    print(f"Task {args.task_id} cancelled.")


def cmd_tasks_delete(args, client):
    """Delete a task."""
    ensure_logged_in(client)
    client.tasks_delete(args.task_id)
    print(f"Task {args.task_id} deleted.")


def cmd_tasks_progress(args, client):
    """Get task progress."""
    ensure_logged_in(client)
    progress = client.tasks_get_progress(args.task_id)
    print_json(progress)


def cmd_tasks_running(args, client):
    """List running tasks."""
    ensure_logged_in(client)
    tasks = client.tasks_list_running()
    if not tasks:
        print("No running tasks.")
        return
    for t in tasks:
        print(f"  [{t.get('id')}] {t.get('name', 'N/A')} - {t.get('result', 'Running')}")


def cmd_tasks_cleanup(args, client):
    """Remove completed tasks."""
    ensure_logged_in(client)
    client.tasks_remove_completed()
    print("Completed tasks removed.")


def cmd_tasks_versions(args, client):
    """List backup versions."""
    ensure_logged_in(client)
    versions = client.tasks_list_versions(args.task_id)
    if not versions:
        print("No versions found.")
        return
    print_json(versions)


def cmd_sync_list(args, client):
    """List realtime syncs."""
    ensure_logged_in(client)
    syncs = client.realtime_sync_list()
    if not syncs:
        print("No realtime syncs configured.")
        return
    print_json(syncs)


def cmd_sync_create(args, client):
    """Create realtime sync."""
    ensure_logged_in(client)
    from_items = [{"driveId": args.from_drive_id, "fileId": "root", "pid": "root", "isDir": True}]
    to_items = [{"driveId": args.to_drive_id, "fileId": "root", "pid": "root", "isDir": True}]
    result = client.realtime_sync_create(from_items, to_items, sync_type=args.type or "")
    print("Realtime sync created:")
    print_json(result)


def cmd_sync_enable(args, client):
    """Enable realtime sync."""
    ensure_logged_in(client)
    client.realtime_sync_switch_status(args.sync_id, True)
    print(f"Realtime sync {args.sync_id} enabled.")


def cmd_sync_disable(args, client):
    """Disable realtime sync."""
    ensure_logged_in(client)
    client.realtime_sync_switch_status(args.sync_id, False)
    print(f"Realtime sync {args.sync_id} disabled.")


def cmd_sync_delete(args, client):
    """Delete realtime sync."""
    ensure_logged_in(client)
    client.realtime_sync_cancel(args.sync_id)
    print(f"Realtime sync {args.sync_id} deleted.")


def cmd_torrent_add(args, client):
    """Add torrent/magnet download."""
    ensure_logged_in(client)
    to_items = [{"driveId": args.drive_id, "fileId": "root", "pid": "root", "isDir": True}]
    result = client.torrent_add(args.url, to_items)
    print("Torrent task added:")
    print_json(result)


def cmd_torrent_delete(args, client):
    """Delete torrent task."""
    ensure_logged_in(client)
    client.torrent_delete(args.task_id)
    print(f"Torrent task {args.task_id} deleted.")


def cmd_torrent_progress(args, client):
    """Get torrent progress."""
    ensure_logged_in(client)
    progress = client.torrent_progress(args.task_id)
    print_json(progress)


def cmd_video_analyze(args, client):
    """Analyze a video URL."""
    ensure_logged_in(client)
    result = client.video_saver_analyze(args.url)
    print_json(result)


def cmd_video_download(args, client):
    """Download a video."""
    ensure_logged_in(client)
    result = client.video_saver_download(args.url, args.drive_id)
    print("Video download started:")
    print_json(result)


def cmd_video_list(args, client):
    """List video saver tasks."""
    ensure_logged_in(client)
    tasks = client.video_saver_list_tasks()
    if not tasks:
        print("No video saver tasks.")
        return
    print_json(tasks)


def cmd_video_cancel(args, client):
    """Cancel video download."""
    ensure_logged_in(client)
    client.video_saver_cancel(args.task_id)
    print(f"Video task {args.task_id} cancelled.")


def cmd_share_create(args, client):
    """Create a share link."""
    ensure_logged_in(client)
    share_files = {"driveId": args.drive_id, "fileId": args.file_id}
    kwargs = {}
    if args.password:
        kwargs["password"] = args.password
    result = client.share_create_url(share_files, **kwargs)
    print("Share created:")
    print_json(result)


def cmd_share_list(args, client):
    """List all shares."""
    ensure_logged_in(client)
    shares = client.share_list_all()
    if not shares:
        print("No shares found.")
        return
    print_json(shares)


def cmd_share_delete(args, client):
    """Delete a share. (Actually updates share status.)"""
    ensure_logged_in(client)
    client.share_update(args.share_id, status="disabled")
    print(f"Share {args.share_id} disabled.")


def cmd_email_list(args, client):
    """List email migrations."""
    ensure_logged_in(client)
    tasks = client.cloud_email_list()
    if not tasks:
        print("No email migration tasks.")
        return
    print_json(tasks)


def cmd_email_delete(args, client):
    """Delete email migration."""
    ensure_logged_in(client)
    client.cloud_email_delete(args.task_id)
    print(f"Email migration {args.task_id} deleted.")


def cmd_team_list(args, client):
    """List sub-accounts."""
    ensure_logged_in(client)
    accounts = client.subaccount_query()
    if not accounts:
        print("No sub-accounts.")
        return
    print_json(accounts)


def cmd_team_add(args, client):
    """Add sub-account."""
    ensure_logged_in(client)
    result = client.subaccount_add(args.email)
    print("Sub-account added:")
    print_json(result)


def cmd_team_delete(args, client):
    """Delete sub-account."""
    ensure_logged_in(client)
    client.subaccount_delete(args.sub_id)
    print(f"Sub-account {args.sub_id} deleted.")


def cmd_subscription_redeem(args, client):
    """Redeem a license key."""
    ensure_logged_in(client)
    result = client.subscription_redeem_license(args.license_key)
    print("License redeemed:")
    print_json(result)


def cmd_raw(args, client):
    """Send a raw API request."""
    ensure_logged_in(client)
    data = json.loads(args.data) if args.data else {}
    data["ud"] = client._ud()
    method = args.method.upper()
    endpoint = args.endpoint if args.endpoint.startswith("/") else f"/{args.endpoint}"
    if method == "POST":
        result = client._salt_request(endpoint, data)
    else:
        print(f"Unsupported method: {method}", file=sys.stderr)
        sys.exit(1)
    print_json(result)


# ── Argument parser ────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="multcloud",
        description="MultCloud CLI - Unofficial command-line client for MultCloud",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")

    sub = parser.add_subparsers(dest="command", help="Command")

    # login
    p = sub.add_parser("login", help="Sign in to MultCloud")
    p.add_argument("--email", "-e", help="Email address")
    p.add_argument("--password", "-p", help="Password")

    # logout
    sub.add_parser("logout", help="Sign out")

    # whoami
    sub.add_parser("whoami", help="Show current user info")

    # drives
    drives = sub.add_parser("drives", help="Manage cloud drives")
    drives_sub = drives.add_subparsers(dest="drives_cmd")

    drives_sub.add_parser("list", help="List connected drives")

    p = drives_sub.add_parser("add", help="Add a cloud drive")
    p.add_argument("cloud_type", help="Cloud provider type")

    p = drives_sub.add_parser("delete", help="Remove a cloud drive")
    p.add_argument("drive_id", help="Drive ID")

    p = drives_sub.add_parser("rename", help="Rename a cloud drive")
    p.add_argument("drive_id", help="Drive ID")
    p.add_argument("name", help="New name")

    # files
    files = sub.add_parser("files", help="File operations")
    files_sub = files.add_subparsers(dest="files_cmd")

    p = files_sub.add_parser("list", help="List files")
    p.add_argument("drive_id", help="Drive ID")
    p.add_argument("--path", "-p", default="root", help="Directory ID (default: root)")

    p = files_sub.add_parser("mkdir", help="Create directory")
    p.add_argument("drive_id", help="Drive ID")
    p.add_argument("name", help="Directory name")
    p.add_argument("--parent", default="root", help="Parent directory ID")

    p = files_sub.add_parser("delete", help="Delete files")
    p.add_argument("drive_id", help="Drive ID")
    p.add_argument("file_ids", nargs="+", help="File IDs to delete")

    p = files_sub.add_parser("rename", help="Rename file")
    p.add_argument("drive_id", help="Drive ID")
    p.add_argument("file_id", help="File ID")
    p.add_argument("new_name", help="New name")

    p = files_sub.add_parser("search", help="Search files")
    p.add_argument("drive_id", help="Drive ID")
    p.add_argument("keyword", help="Search keyword")

    p = files_sub.add_parser("trash", help="List recycle bin")
    p.add_argument("drive_id", help="Drive ID")

    p = files_sub.add_parser("empty-trash", help="Empty recycle bin")
    p.add_argument("drive_id", help="Drive ID")

    # tasks
    tasks = sub.add_parser("tasks", help="Manage transfer/sync/backup tasks")
    tasks_sub = tasks.add_subparsers(dest="tasks_cmd")

    p = tasks_sub.add_parser("list", help="List tasks")
    p.add_argument("--type", "-t", help="Filter by type (1=Transfer, 3=RemoteUpload, 6=Sync)")
    p.add_argument("--all", "-a", action="store_true", help="List all task types")

    p = tasks_sub.add_parser("get", help="Get task details")
    p.add_argument("task_id", help="Task ID")

    p = tasks_sub.add_parser("add-transfer", help="Create cloud transfer task")
    p.add_argument("from_drive_id", help="Source drive ID")
    p.add_argument("to_drive_id", help="Destination drive ID")
    p.add_argument("--name", "-n", default="", help="Task name")
    p.add_argument("--schedule", "-s", help="Schedule time")

    p = tasks_sub.add_parser("add-sync", help="Create cloud sync task")
    p.add_argument("from_drive_id", help="Source drive ID")
    p.add_argument("to_drive_id", help="Destination drive ID")
    p.add_argument("--name", "-n", default="", help="Task name")
    p.add_argument("--sync-mode", "-m", help="Sync mode")

    p = tasks_sub.add_parser("add-remote-upload", help="Remote upload URL to cloud")
    p.add_argument("url", help="URL to download")
    p.add_argument("filename", help="Filename to save as")
    p.add_argument("drive_id", help="Target drive ID")

    p = tasks_sub.add_parser("execute", help="Trigger a task to run now")
    p.add_argument("task_id", help="Task ID")

    p = tasks_sub.add_parser("cancel", help="Cancel a running task")
    p.add_argument("task_id", help="Task ID")

    p = tasks_sub.add_parser("delete", help="Delete a task")
    p.add_argument("task_id", help="Task ID")

    p = tasks_sub.add_parser("progress", help="Get task progress")
    p.add_argument("task_id", help="Task ID")

    tasks_sub.add_parser("running", help="List running tasks")
    tasks_sub.add_parser("cleanup", help="Remove completed tasks")

    p = tasks_sub.add_parser("versions", help="List backup versions")
    p.add_argument("task_id", help="Task ID")

    # sync (realtime)
    sync = sub.add_parser("sync", help="Manage realtime sync")
    sync_sub = sync.add_subparsers(dest="sync_cmd")

    sync_sub.add_parser("list", help="List realtime syncs")

    p = sync_sub.add_parser("create", help="Create realtime sync")
    p.add_argument("from_drive_id", help="Source drive ID")
    p.add_argument("to_drive_id", help="Destination drive ID")
    p.add_argument("--type", "-t", default="", help="Sync type")

    p = sync_sub.add_parser("enable", help="Enable realtime sync")
    p.add_argument("sync_id", help="Sync ID")

    p = sync_sub.add_parser("disable", help="Disable realtime sync")
    p.add_argument("sync_id", help="Sync ID")

    p = sync_sub.add_parser("delete", help="Delete realtime sync")
    p.add_argument("sync_id", help="Sync ID")

    # torrent
    torrent = sub.add_parser("torrent", help="Torrent/magnet downloads")
    torrent_sub = torrent.add_subparsers(dest="torrent_cmd")

    p = torrent_sub.add_parser("add", help="Add torrent/magnet")
    p.add_argument("url", help="Magnet link or torrent URL")
    p.add_argument("drive_id", help="Target drive ID")

    p = torrent_sub.add_parser("delete", help="Delete torrent task")
    p.add_argument("task_id", help="Task ID")

    p = torrent_sub.add_parser("progress", help="Get torrent progress")
    p.add_argument("task_id", help="Task ID")

    # video
    video = sub.add_parser("video", help="Video saver")
    video_sub = video.add_subparsers(dest="video_cmd")

    p = video_sub.add_parser("analyze", help="Analyze video URL")
    p.add_argument("url", help="Video URL")

    p = video_sub.add_parser("download", help="Download video to cloud")
    p.add_argument("url", help="Video URL")
    p.add_argument("drive_id", help="Target drive ID")

    video_sub.add_parser("list", help="List video tasks")

    p = video_sub.add_parser("cancel", help="Cancel video download")
    p.add_argument("task_id", help="Task ID")

    # share
    share = sub.add_parser("share", help="File sharing")
    share_sub = share.add_subparsers(dest="share_cmd")

    p = share_sub.add_parser("create", help="Create share link")
    p.add_argument("drive_id", help="Drive ID")
    p.add_argument("file_id", help="File ID")
    p.add_argument("--password", "-p", help="Share password")

    share_sub.add_parser("list", help="List shares")

    p = share_sub.add_parser("delete", help="Delete/disable share")
    p.add_argument("share_id", help="Share ID")

    # email
    email = sub.add_parser("email", help="Email migration")
    email_sub = email.add_subparsers(dest="email_cmd")

    email_sub.add_parser("list", help="List email migrations")

    p = email_sub.add_parser("delete", help="Delete email migration")
    p.add_argument("task_id", help="Task ID")

    # team
    team = sub.add_parser("team", help="Sub-account management")
    team_sub = team.add_subparsers(dest="team_cmd")

    team_sub.add_parser("list", help="List sub-accounts")

    p = team_sub.add_parser("add", help="Add sub-account")
    p.add_argument("email", help="Email address")

    p = team_sub.add_parser("delete", help="Delete sub-account")
    p.add_argument("sub_id", help="Sub-account ID")

    # subscription
    subscription = sub.add_parser("subscription", help="Subscription management")
    sub_sub = subscription.add_subparsers(dest="sub_cmd")

    p = sub_sub.add_parser("redeem", help="Redeem license key")
    p.add_argument("license_key", help="License key")

    # raw
    p = sub.add_parser("raw", help="Send raw API request")
    p.add_argument("method", help="HTTP method (POST)")
    p.add_argument("endpoint", help="API endpoint path (e.g., /tasks/list)")
    p.add_argument("--data", "-d", help="JSON request body")

    return parser


# ── Command dispatch ───────────────────────────────────────────────

COMMAND_MAP = {
    ("login", None): cmd_login,
    ("logout", None): cmd_logout,
    ("whoami", None): cmd_whoami,
    ("drives", "list"): cmd_drives_list,
    ("drives", "add"): cmd_drives_add,
    ("drives", "delete"): cmd_drives_delete,
    ("drives", "rename"): cmd_drives_rename,
    ("files", "list"): cmd_files_list,
    ("files", "mkdir"): cmd_files_mkdir,
    ("files", "delete"): cmd_files_delete,
    ("files", "rename"): cmd_files_rename,
    ("files", "search"): cmd_files_search,
    ("files", "trash"): cmd_files_trash,
    ("files", "empty-trash"): cmd_files_empty_trash,
    ("tasks", "list"): cmd_tasks_list,
    ("tasks", "get"): cmd_tasks_get,
    ("tasks", "add-transfer"): cmd_tasks_add_transfer,
    ("tasks", "add-sync"): cmd_tasks_add_sync,
    ("tasks", "add-remote-upload"): cmd_tasks_add_remote_upload,
    ("tasks", "execute"): cmd_tasks_execute,
    ("tasks", "cancel"): cmd_tasks_cancel,
    ("tasks", "delete"): cmd_tasks_delete,
    ("tasks", "progress"): cmd_tasks_progress,
    ("tasks", "running"): cmd_tasks_running,
    ("tasks", "cleanup"): cmd_tasks_cleanup,
    ("tasks", "versions"): cmd_tasks_versions,
    ("sync", "list"): cmd_sync_list,
    ("sync", "create"): cmd_sync_create,
    ("sync", "enable"): cmd_sync_enable,
    ("sync", "disable"): cmd_sync_disable,
    ("sync", "delete"): cmd_sync_delete,
    ("torrent", "add"): cmd_torrent_add,
    ("torrent", "delete"): cmd_torrent_delete,
    ("torrent", "progress"): cmd_torrent_progress,
    ("video", "analyze"): cmd_video_analyze,
    ("video", "download"): cmd_video_download,
    ("video", "list"): cmd_video_list,
    ("video", "cancel"): cmd_video_cancel,
    ("share", "create"): cmd_share_create,
    ("share", "list"): cmd_share_list,
    ("share", "delete"): cmd_share_delete,
    ("email", "list"): cmd_email_list,
    ("email", "delete"): cmd_email_delete,
    ("team", "list"): cmd_team_list,
    ("team", "add"): cmd_team_add,
    ("team", "delete"): cmd_team_delete,
    ("subscription", "redeem"): cmd_subscription_redeem,
    ("raw", None): cmd_raw,
}


def main():
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Determine subcommand
    subcmd = None
    for attr in ["drives_cmd", "files_cmd", "tasks_cmd", "sync_cmd", "torrent_cmd",
                 "video_cmd", "share_cmd", "email_cmd", "team_cmd", "sub_cmd"]:
        val = getattr(args, attr, None)
        if val:
            subcmd = val
            break

    handler = COMMAND_MAP.get((args.command, subcmd))
    if not handler:
        if subcmd is None and args.command in ["drives", "files", "tasks", "sync",
                                                 "torrent", "video", "share", "email", "team", "subscription"]:
            # Print subcommand help
            parser.parse_args([args.command, "--help"])
        print(f"Unknown command: {args.command} {subcmd or ''}", file=sys.stderr)
        sys.exit(1)

    client = get_client()

    try:
        handler(args, client)
    except MultCloudError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()

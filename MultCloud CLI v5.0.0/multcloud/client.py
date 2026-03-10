"""
MultCloud API Client.

Low-level HTTP client that handles session management, request signing,
response decryption, and all API endpoint communication.
"""

import json
import logging
import random
import string
from pathlib import Path
from typing import Any, Optional

import requests

from . import crypto

log = logging.getLogger(__name__)

API_BASE = "https://app.multcloud.com/api"
WEB_BASE = "https://www.multcloud.com/api"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"
)


class MultCloudError(Exception):
    """Raised when MultCloud API returns an error."""

    def __init__(self, status: int, message: str, reason: str = ""):
        self.status = status
        self.message = message
        self.reason = reason
        super().__init__(f"[{status}] {message}" + (f" ({reason})" if reason else ""))


class MultCloudClient:
    """Low-level client for MultCloud's internal API."""

    def __init__(self, api_base: str = API_BASE):
        self.api_base = api_base
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Content-Type": "application/json",
            }
        )
        self.session.verify = True
        self.user: Optional[dict] = None
        self.salt: Optional[str] = None

    # ── Session persistence ──────────────────────────────────────────

    def save_session(self, path: Path):
        """Save session cookies and user data to a JSON file."""
        data = {
            "cookies": [
                {
                    "name": c.name,
                    "value": c.value,
                    "domain": c.domain,
                    "path": c.path,
                }
                for c in self.session.cookies
            ],
            "user": self.user,
            "salt": self.salt,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))

    def load_session(self, path: Path) -> bool:
        """Load session cookies and user data from a JSON file.

        Returns True if session was loaded and is still valid.
        """
        if not path.exists():
            return False
        data = json.loads(path.read_text())
        for cookie in data.get("cookies", []):
            self.session.cookies.set(
                cookie["name"],
                cookie["value"],
                domain=cookie["domain"],
                path=cookie["path"],
            )
        self.user = data.get("user")
        self.salt = data.get("salt")
        if self.user:
            try:
                self.user_get()
                return True
            except MultCloudError:
                return False
        return False

    # ── Request helpers ───────────────────────────────────────────────

    def _post(self, path: str, data: dict) -> dict:
        """Make a POST request to the API and handle response decryption."""
        url = self.api_base + path
        log.debug("POST %s %s", url, json.dumps(data, default=str)[:200])
        resp = self.session.post(url, json=data, timeout=60)
        resp.raise_for_status()
        body = resp.json()
        if isinstance(body, str):
            body = crypto.aes_decrypt(body)
        return body

    def _post_salt(self, path: str, params: dict) -> dict:
        """POST with salt-based signing (authenticated requests)."""
        if not self.salt:
            raise MultCloudError(401, "Not authenticated. Call login() first.")
        signed = crypto.sign_with_salt(params, self.salt)
        return self._post(path, signed)

    def _post_aes(self, path: str, params: dict) -> dict:
        """POST with AES-key signing (unauthenticated requests)."""
        signed = crypto.sign_with_aes_key(params)
        return self._post(path, signed)

    def _parse_response(self, resp: dict, key: str = None) -> Any:
        """Parse API response, raising on errors."""
        code = resp.get("code", resp.get("status", 0))
        if isinstance(code, str):
            code = int(code) if code.isdigit() else 0
        if 200 <= code < 300:
            data = resp.get("data", resp)
            if key and isinstance(data, dict):
                return data.get(key, data)
            return data
        msg = resp.get("message", resp.get("msg", "Unknown error"))
        reason = resp.get("reason", "")
        raise MultCloudError(code, msg, reason)

    def _salt_request(self, path: str, params: dict, key: str = None) -> Any:
        """Authenticated request with response parsing."""
        resp = self._post_salt(path, params)
        return self._parse_response(resp, key)

    def _aes_request(self, path: str, params: dict, key: str = None) -> Any:
        """Unauthenticated request with response parsing."""
        resp = self._post_aes(path, params)
        return self._parse_response(resp, key)

    def _ud(self) -> str:
        """Get the current user's ID."""
        if not self.user:
            raise MultCloudError(401, "Not authenticated.")
        return self.user["id"]

    # ── Authentication ────────────────────────────────────────────────

    def login(self, email: str, password: str) -> dict:
        """Sign in with email and password.

        Returns user data dict on success.
        """
        params = {"email": email, "password": password, "rememberMe": True}
        resp = self._post_aes("/user/sign_in_", params)
        data = self._parse_response(resp)
        user = data.get("user", data)
        self.user = user
        self.salt = user.get("salt", "")
        return user

    def login_with_captcha(
        self, email: str, password: str, vkey: str, vcode: str
    ) -> dict:
        """Sign in with email, password, and CAPTCHA verification."""
        params = {
            "email": email,
            "password": password,
            "rememberMe": True,
            "vkey": vkey,
            "vcode": vcode,
        }
        resp = self._post_aes("/user/sign_in_", params)
        data = self._parse_response(resp)
        user = data.get("user", data)
        self.user = user
        self.salt = user.get("salt", "")
        return user

    def generate_captcha(self):
        """Generate a CAPTCHA image for login.

        Returns (vkey, image_bytes) tuple.
        """
        rand_digit = random.randint(1, 9)
        vkey = str(rand_digit) + "".join(
            random.choices(string.ascii_letters, k=14)
        ) + str(9 - rand_digit)
        params = {"vkey": vkey}
        signed = crypto.sign_with_aes_key(params)
        url = f"{self.api_base}/verify_code/generate?vkey={vkey}&s={signed['s']}"
        resp = self.session.get(url, stream=True, timeout=30)
        resp.raise_for_status()
        return vkey, resp.content

    def direct_sign_in(self) -> dict:
        """Re-authenticate using stored session data."""
        params = {"ud": self._ud()}
        resp = self._post_salt("/user/direct_sign_in", params)
        data = self._parse_response(resp)
        user = data.get("user", data)
        self.user = user
        self.salt = user.get("salt", self.salt)
        return user

    def user_get(self) -> dict:
        """Get current user profile."""
        params = {"ud": self._ud()}
        resp = self._post_salt("/user/get", params)
        data = self._parse_response(resp)
        user = data.get("user", data)
        self.user = user
        self.salt = user.get("salt", self.salt)
        return user

    def user_update(self, **fields) -> dict:
        """Update user profile fields."""
        params = {"ud": self._ud(), **fields}
        return self._salt_request("/user/update", params)

    def logout(self) -> dict:
        """Sign out and invalidate the session."""
        params = {"ud": self._ud()}
        result = self._salt_request("/user/exit", params)
        self.user = None
        self.salt = None
        return result

    def create_tourist(self) -> dict:
        """Create a temporary/guest account."""
        resp = self._post_aes("/user/create_tourist", {})
        data = self._parse_response(resp)
        user = data.get("user", data)
        self.user = user
        self.salt = user.get("salt", "")
        return user

    # ── Drives ────────────────────────────────────────────────────────

    def drives_list(self, show_all: bool = False) -> list:
        """List all connected cloud drives."""
        params = {"ud": self._ud(), "sa": show_all}
        return self._salt_request("/drives/list", params, "drives")

    def drives_get(self, drive_id: str) -> dict:
        """Get details for a specific drive."""
        params = {"ud": self._ud(), "id": drive_id}
        return self._salt_request("/drives/get", params)

    def drives_add(self, cloud_type: str, **kwargs) -> dict:
        """Initiate adding a new cloud drive (starts OAuth flow).

        Args:
            cloud_type: Cloud provider type (e.g., 'google_drive', 'dropbox').
        """
        params = {"ud": self._ud(), "cloudType": cloud_type, **kwargs}
        return self._salt_request("/drives/add", params)

    def drives_delete(self, drive_id: str) -> dict:
        """Remove a connected cloud drive."""
        params = {"ud": self._ud(), "id": drive_id}
        return self._salt_request("/drives/delete", params)

    def drives_rename(self, drive_id: str, name: str) -> dict:
        """Rename a cloud drive."""
        params = {"ud": self._ud(), "id": drive_id, "name": name}
        return self._salt_request("/drives/rename", params)

    def drives_list_categories(self) -> list:
        """List drive categories."""
        params = {"ud": self._ud()}
        return self._salt_request("/drives/list_categories", params)

    # ── Files ─────────────────────────────────────────────────────────

    def files_list(
        self,
        drive_id: str,
        file_id: str = "root",
        cloud_type: str = "",
        **kwargs,
    ) -> list:
        """List files in a directory on a cloud drive."""
        params = {
            "ud": self._ud(),
            "driveId": drive_id,
            "fileId": file_id,
            "cloudType": cloud_type,
            **kwargs,
        }
        return self._salt_request("/files/list", params, "files")

    def files_mkdir(
        self, drive_id: str, parent_id: str, name: str, cloud_type: str = ""
    ) -> dict:
        """Create a directory on a cloud drive."""
        params = {
            "ud": self._ud(),
            "driveId": drive_id,
            "pid": parent_id,
            "name": name,
            "cloudType": cloud_type,
        }
        return self._salt_request("/files/mkdir", params)

    def files_delete(
        self, drive_id: str, file_ids: list, cloud_type: str = ""
    ) -> dict:
        """Delete files from a cloud drive."""
        params = {
            "ud": self._ud(),
            "driveId": drive_id,
            "items": file_ids,
            "cloudType": cloud_type,
        }
        return self._salt_request("/files/delete", params)

    def files_rename(
        self, drive_id: str, file_id: str, new_name: str, cloud_type: str = ""
    ) -> dict:
        """Rename a file or folder."""
        params = {
            "ud": self._ud(),
            "driveId": drive_id,
            "id": file_id,
            "name": new_name,
            "cloudType": cloud_type,
        }
        return self._salt_request("/files/rename", params)

    def files_copy(self, from_items: list, to_items: list) -> dict:
        """Copy files between drives."""
        params = {"ud": self._ud(), "fromItems": from_items, "toItems": to_items}
        return self._salt_request("/files/copy", params)

    def files_move(self, from_items: list, to_items: list) -> dict:
        """Move files between drives."""
        params = {"ud": self._ud(), "fromItems": from_items, "toItems": to_items}
        return self._salt_request("/files/move", params)

    def files_search(self, drive_id: str, keyword: str, cloud_type: str = "") -> list:
        """Search for files on a drive."""
        params = {
            "ud": self._ud(),
            "driveId": drive_id,
            "keyword": keyword,
            "cloudType": cloud_type,
        }
        return self._salt_request("/files/search", params, "files")

    def files_share(self, drive_id: str, file_id: str, cloud_type: str = "") -> dict:
        """Get a sharing link for a file."""
        params = {
            "ud": self._ud(),
            "driveId": drive_id,
            "id": file_id,
            "cloudType": cloud_type,
        }
        return self._salt_request("/files/share", params)

    def files_empty_trash(self, drive_id: str, cloud_type: str = "") -> dict:
        """Empty the trash/recycle bin on a drive."""
        params = {"ud": self._ud(), "driveId": drive_id, "cloudType": cloud_type}
        return self._salt_request("/files/empty_trash", params)

    def files_recycle_bin(self, drive_id: str, cloud_type: str = "") -> list:
        """List files in the recycle bin."""
        params = {"ud": self._ud(), "driveId": drive_id, "cloudType": cloud_type}
        return self._salt_request("/files/recycle_bin", params, "files")

    def files_restore(self, drive_id: str, file_ids: list, cloud_type: str = "") -> dict:
        """Restore files from the recycle bin."""
        params = {
            "ud": self._ud(),
            "driveId": drive_id,
            "items": file_ids,
            "cloudType": cloud_type,
        }
        return self._salt_request("/files/restore", params)

    # ── Tasks (Transfer / Sync / Backup) ──────────────────────────────

    def tasks_add(
        self,
        task_type: int,
        from_items: list,
        to_items: list,
        name: str = "",
        options: dict = None,
    ) -> dict:
        """Create a new transfer/sync/backup task.

        Task types:
            1: Cloud Transfer
            3: Remote Upload (URL to cloud)
            6: Cloud Sync / Cloud Backup

        Args:
            task_type: Task type constant.
            from_items: Source items/drives.
            to_items: Destination items/drives.
            name: Task name.
            options: Task options (schedule, filters, sync mode, etc.)
        """
        import datetime

        params = {
            "ud": self._ud(),
            "type": task_type,
            "fromItems": from_items,
            "toItems": to_items,
        }
        if name:
            params["name"] = name
        if options:
            options.setdefault("timeZone", datetime.datetime.now().astimezone().tzname())
            params["options"] = options
        return self._salt_request("/tasks/add", params, "tasks")

    def tasks_add_remote_upload(
        self,
        url: str,
        file_name: str,
        drive_id: str,
        cloud_type: str = "google_drive",
        category_id: int = 0,
    ) -> dict:
        """Add a remote upload task (download URL to cloud drive).

        This is the main function the original repo provided.
        """
        params = {
            "ud": self._ud(),
            "type": 3,
            "n": file_name,
            "url": url,
            "toItems": [
                {
                    "driveType": cloud_type,
                    "driveId": drive_id,
                    "pid": "root",
                    "fileId": "root",
                    "filename": "Root",
                    "isDir": True,
                    "nodes": [{"fileId": "root", "filename": "Root"}],
                }
            ],
        }
        if category_id:
            params["type"] = int(category_id)
        return self._salt_request("/tasks/add", params, "tasks")

    def tasks_list(self, task_type: int = None) -> list:
        """List all tasks, optionally filtered by type."""
        params = {"ud": self._ud()}
        if task_type is not None:
            params["type"] = task_type
        return self._salt_request("/tasks/list", params, "tasks")

    def tasks_all_list(self) -> list:
        """List all tasks across all types."""
        params = {"ud": self._ud()}
        return self._salt_request("/tasks/all_list", params, "tasks")

    def tasks_get(self, task_id: str) -> dict:
        """Get details for a specific task."""
        params = {"ud": self._ud(), "id": task_id}
        return self._salt_request("/tasks/get", params)

    def tasks_execute(self, task_id: str) -> dict:
        """Trigger/run an existing task immediately."""
        params = {"ud": self._ud(), "id": task_id}
        return self._salt_request("/tasks/execute", params)

    def tasks_cancel(self, task_id: str) -> dict:
        """Cancel a running task."""
        params = {"ud": self._ud(), "id": task_id}
        return self._salt_request("/tasks/cancel", params)

    def tasks_delete(self, task_id: str) -> dict:
        """Delete a task."""
        params = {"ud": self._ud(), "id": task_id}
        return self._salt_request("/tasks/delete", params)

    def tasks_delete_batch(self, task_ids: list) -> dict:
        """Delete multiple tasks at once."""
        params = {"ud": self._ud(), "ids": task_ids}
        return self._salt_request("/tasks/delete_batch", params)

    def tasks_update(self, task_id: str, **fields) -> dict:
        """Update a task's configuration.

        Fields may include: name, options (schedule, filters, etc.)
        """
        params = {"ud": self._ud(), "id": task_id, **fields}
        return self._salt_request("/tasks/update", params)

    def tasks_get_progress(self, task_id: str) -> dict:
        """Get progress for a running task."""
        params = {"ud": self._ud(), "id": task_id}
        return self._salt_request("/tasks/get_progress", params)

    def tasks_list_running(self) -> list:
        """List all currently running tasks."""
        params = {"ud": self._ud()}
        return self._salt_request("/tasks/list_running_tasks", params, "tasks")

    def tasks_list_versions(self, task_id: str) -> list:
        """List backup versions for a task."""
        params = {"ud": self._ud(), "id": task_id}
        return self._salt_request("/tasks/list_versions", params, "versions")

    def tasks_delete_version(self, task_id: str, version_id: str) -> dict:
        """Delete a specific backup version."""
        params = {"ud": self._ud(), "id": task_id, "versionId": version_id}
        return self._salt_request("/tasks/delete_version", params)

    def tasks_list_restore(self, task_id: str) -> list:
        """List restore points for a backup task."""
        params = {"ud": self._ud(), "id": task_id}
        return self._salt_request("/tasks/list_restore", params)

    def tasks_remove_completed(self) -> dict:
        """Remove all completed tasks from the list."""
        params = {"ud": self._ud()}
        return self._salt_request("/tasks/remove_completed_task", params)

    # ── Realtime Sync ─────────────────────────────────────────────────

    def realtime_sync_create(
        self, from_items: list, to_items: list, sync_type: str = "", name: str = ""
    ) -> dict:
        """Create a new realtime sync task."""
        params = {
            "ud": self._ud(),
            "fromItems": from_items,
            "toItems": to_items,
        }
        if sync_type:
            params["syncType"] = sync_type
        if name:
            params["name"] = name
        return self._salt_request("/realtime_sync/create", params)

    def realtime_sync_list(self) -> list:
        """List all realtime sync tasks."""
        params = {"ud": self._ud()}
        return self._salt_request("/realtime_sync/list", params)

    def realtime_sync_get(self, sync_id: str) -> dict:
        """Get details for a realtime sync task."""
        params = {"ud": self._ud(), "id": sync_id}
        return self._salt_request("/realtime_sync/get", params)

    def realtime_sync_switch_status(self, sync_id: str, enabled: bool) -> dict:
        """Enable or disable a realtime sync task."""
        params = {"ud": self._ud(), "id": sync_id, "status": enabled}
        return self._salt_request("/realtime_sync/switch_status", params)

    def realtime_sync_switch_type(self, sync_id: str, sync_type: str) -> dict:
        """Change the sync type for a realtime sync task."""
        params = {"ud": self._ud(), "id": sync_id, "syncType": sync_type}
        return self._salt_request("/realtime_sync/switch_type", params)

    def realtime_sync_cancel(self, sync_id: str) -> dict:
        """Cancel/delete a realtime sync task."""
        params = {"ud": self._ud(), "id": sync_id}
        return self._salt_request("/realtime_sync/cancel", params)

    # ── Torrent / Remote Upload ───────────────────────────────────────

    def torrent_add(self, torrent_data: str, to_items: list) -> dict:
        """Add a torrent/magnet link for remote download."""
        params = {"ud": self._ud(), "url": torrent_data, "toItems": to_items}
        return self._salt_request("/torrent/add", params)

    def torrent_parse(self, torrent_data: str) -> dict:
        """Parse a torrent file or magnet link."""
        params = {"ud": self._ud(), "url": torrent_data}
        return self._salt_request("/torrent/parse", params)

    def torrent_delete(self, task_id: str) -> dict:
        """Delete a torrent download task."""
        params = {"ud": self._ud(), "id": task_id}
        return self._salt_request("/torrent/delete", params)

    def torrent_progress(self, task_id: str) -> dict:
        """Get torrent download progress."""
        params = {"ud": self._ud(), "id": task_id}
        return self._salt_request("/torrent/progress", params)

    # ── Video Saver ───────────────────────────────────────────────────

    def video_saver_analyze(self, url: str) -> dict:
        """Analyze a video URL for available downloads."""
        params = {"ud": self._ud(), "url": url}
        return self._salt_request("/video_saver/analyze_url", params)

    def video_saver_download(self, url: str, drive_id: str, **kwargs) -> dict:
        """Start downloading a video to a cloud drive."""
        params = {"ud": self._ud(), "url": url, "driveId": drive_id, **kwargs}
        return self._salt_request("/video_saver/download_add", params)

    def video_saver_image_download(self, url: str, drive_id: str, **kwargs) -> dict:
        """Download an image to a cloud drive."""
        params = {"ud": self._ud(), "url": url, "driveId": drive_id, **kwargs}
        return self._salt_request("/video_saver/image_download_add", params)

    def video_saver_list_tasks(self) -> list:
        """List video saver tasks."""
        params = {"ud": self._ud()}
        return self._salt_request("/video_saver/list_task", params)

    def video_saver_get_task(self, task_id: str) -> dict:
        """Get video saver task details."""
        params = {"ud": self._ud(), "id": task_id}
        return self._salt_request("/video_saver/get_task", params)

    def video_saver_progress(self, task_id: str) -> dict:
        """Get video download progress."""
        params = {"ud": self._ud(), "id": task_id}
        return self._salt_request("/video_saver/download_progress", params)

    def video_saver_cancel(self, task_id: str) -> dict:
        """Cancel a video download."""
        params = {"ud": self._ud(), "id": task_id}
        return self._salt_request("/video_saver/cancel_task", params)

    def video_saver_retry(self, task_id: str) -> dict:
        """Retry a failed video download."""
        params = {"ud": self._ud(), "id": task_id}
        return self._salt_request("/video_saver/retry_task", params)

    def video_saver_clear_history(self) -> dict:
        """Clear video saver download history."""
        params = {"ud": self._ud()}
        return self._salt_request("/video_saver/clear_history", params)

    def video_saver_save_task(self, task_data: dict) -> dict:
        """Save a video download task."""
        params = {"ud": self._ud(), **task_data}
        return self._salt_request("/video_saver/save_task", params)

    # ── Cloud Email Migration ─────────────────────────────────────────

    def cloud_email_list(self) -> list:
        """List email migration tasks."""
        params = {"ud": self._ud()}
        return self._salt_request("/cloud_email/list", params)

    def cloud_email_delete(self, task_id: str) -> dict:
        """Delete an email migration task."""
        params = {"ud": self._ud(), "id": task_id}
        return self._salt_request("/cloud_email/delete", params)

    def cloud_email_tasks_pause(self, task_id: str) -> dict:
        """Pause an email migration task."""
        params = {"ud": self._ud(), "id": task_id}
        return self._salt_request("/cloud_email_tasks/pause", params)

    # ── Sharing ───────────────────────────────────────────────────────

    def share_create_url(self, share_files: dict, **kwargs) -> dict:
        """Create a share link."""
        params = {"ud": self._ud(), "shareFiles": share_files, **kwargs}
        return self._salt_request("/share/create_share_url", params)

    def share_create_transfer_url(self, share_files: dict, **kwargs) -> dict:
        """Create a transfer share link."""
        params = {"ud": self._ud(), "shareFiles": share_files, **kwargs}
        return self._salt_request("/share/create_share_transfers_url", params)

    def share_check(self, share_id: str) -> dict:
        """Check share link validity."""
        params = {"ud": self._ud(), "shareId": share_id}
        return self._salt_request("/share/check_share", params)

    def share_check_password(self, share_id: str, password: str) -> dict:
        """Verify share link password."""
        params = {"ud": self._ud(), "shareId": share_id, "password": password}
        return self._salt_request("/share/check_password", params)

    def share_update(self, share_id: str, **fields) -> dict:
        """Update share settings."""
        params = {"ud": self._ud(), "shareId": share_id, **fields}
        return self._salt_request("/share/update_share", params)

    def share_list_all(self) -> list:
        """List all shares."""
        params = {"ud": self._ud()}
        return self._salt_request("/share/select_all_share", params)

    def share_list_saved(self) -> list:
        """List saved shares."""
        params = {"ud": self._ud()}
        return self._salt_request("/share/select_all_saved_share", params)

    def share_get_transfers(self, share_id: str) -> list:
        """Get shared transfer files."""
        params = {"ud": self._ud(), "shareId": share_id}
        return self._salt_request("/share/get_share_transfers", params)

    def share_get_transfer_files(self, share_id: str) -> list:
        """Get files in a shared transfer."""
        params = {"ud": self._ud(), "shareId": share_id}
        return self._salt_request("/share/get_share_transfer_files", params)

    def share_toggle_upload(self, share_id: str, enabled: bool) -> dict:
        """Enable/disable upload on a share."""
        params = {"ud": self._ud(), "shareId": share_id, "status": enabled}
        return self._salt_request("/share/change_share_upload_status", params)

    # ── Business Transfer ─────────────────────────────────────────────

    def business_transfer_create(self, **kwargs) -> dict:
        """Create a business transfer."""
        params = {"ud": self._ud(), **kwargs}
        return self._salt_request("/business_transfer/create", params)

    def business_transfer_execute(self, transfer_id: str) -> dict:
        """Execute a business transfer."""
        params = {"ud": self._ud(), "id": transfer_id}
        return self._salt_request("/business_transfer/execute", params)

    def business_transfer_get(self, transfer_id: str) -> dict:
        """Get business transfer details."""
        params = {"ud": self._ud(), "id": transfer_id}
        return self._salt_request("/business_transfer/get", params)

    def business_transfer_update(self, transfer_id: str, **fields) -> dict:
        """Update a business transfer."""
        params = {"ud": self._ud(), "id": transfer_id, **fields}
        return self._salt_request("/business_transfer/update", params)

    def business_transfer_cancel(self, transfer_id: str) -> dict:
        """Cancel a business transfer."""
        params = {"ud": self._ud(), "id": transfer_id}
        return self._salt_request("/business_transfer/cancel", params)

    def business_transfer_delete(self, transfer_id: str) -> dict:
        """Delete a business transfer."""
        params = {"ud": self._ud(), "id": transfer_id}
        return self._salt_request("/business_transfer/delete", params)

    def business_transfer_progress(self, transfer_id: str) -> dict:
        """Get business transfer progress."""
        params = {"ud": self._ud(), "id": transfer_id}
        return self._salt_request("/business_transfer/progress", params)

    def business_transfer_members(self) -> list:
        """List team members for business transfer."""
        params = {"ud": self._ud()}
        return self._salt_request("/business_transfer/members", params)

    # ── Email ─────────────────────────────────────────────────────────

    def email_send_invite(self, emails: list) -> dict:
        """Send invitation emails."""
        params = {"ud": self._ud(), "emails": emails}
        return self._aes_request("/email/send_invite_friends", params)

    def email_send_share_info(self, share_id: str, emails: list) -> dict:
        """Send share notification emails."""
        params = {"ud": self._ud(), "shareId": share_id, "emails": emails}
        return self._aes_request("/email/send_share_infos", params)

    # ── Subscription ──────────────────────────────────────────────────

    def subscription_add_cart(self, product_id: str, coupon: str = "") -> dict:
        """Add item to subscription cart."""
        params = {
            "ud": self._ud(),
            "productId": product_id,
            "source": 1,
        }
        if coupon:
            params["coupon"] = coupon
        return self._salt_request("/subscription/add_cart_records", params)

    def subscription_redeem_license(self, license_key: str) -> dict:
        """Redeem a license key."""
        params = {"ud": self._ud(), "licenseKey": license_key}
        return self._salt_request("/subscription/license_redemption", params)

    # ── Notifications ─────────────────────────────────────────────────

    def notify_version_info(self) -> dict:
        """Check for version/update info."""
        params = {"ud": self._ud()}
        return self._salt_request("/notify/get_version_info", params)

    # ── Sub-accounts / Team ───────────────────────────────────────────

    def subaccount_add(self, email: str, **kwargs) -> dict:
        """Add a sub-account."""
        params = {"ud": self._ud(), "email": email, **kwargs}
        return self._salt_request("/subaccount/add", params)

    def subaccount_delete(self, sub_id: str) -> dict:
        """Delete a sub-account."""
        params = {"ud": self._ud(), "id": sub_id}
        return self._salt_request("/subaccount/del", params)

    def subaccount_edit(self, sub_id: str, **fields) -> dict:
        """Edit a sub-account."""
        params = {"ud": self._ud(), "id": sub_id, **fields}
        return self._salt_request("/subaccount/edit", params)

    def subaccount_query(self) -> list:
        """List all sub-accounts."""
        params = {"ud": self._ud()}
        return self._salt_request("/subaccount/query", params)

    # ── Permissions ───────────────────────────────────────────────────

    def permission_get(self, **kwargs) -> dict:
        """Get permissions."""
        params = {"ud": self._ud(), **kwargs}
        return self._salt_request("/permission/get_permission", params)

    def permission_get_root(self, **kwargs) -> dict:
        """Get root permission."""
        params = {"ud": self._ud(), **kwargs}
        return self._salt_request("/permission/get_root", params)

    # ── Invite Friends ────────────────────────────────────────────────

    def invite_get_info(self) -> dict:
        """Get invite friends information."""
        params = {"ud": self._ud()}
        return self._salt_request("/invite/get_information", params)

# MultCloud API Reference (v5.0.0)

> Reverse-engineered from MultCloud's frontend JS bundle (`app.*.js`)
> Last updated: March 2026

## Overview

MultCloud exposes an internal REST-like API at `https://app.multcloud.com/api`. All
requests use POST with JSON bodies and all responses may be AES-ECB encrypted hex
strings that require decryption.

**This is an unofficial, reverse-engineered API. It may change without notice.**

---

## Base Configuration

| Key             | Value                                  |
|-----------------|----------------------------------------|
| API URL (App)   | `https://app.multcloud.com/api`        |
| API URL (Web)   | `https://www.multcloud.com/api`        |
| AES Encrypt Key | `KXrDPHUkQSMKhklkKHHP+Q==`            |
| AES Decrypt Key | `LIa4CTfB3SwKnfJhu2iJkQ==`            |
| AES Mode        | ECB                                    |
| AES Padding     | PKCS7                                  |
| Old AES Key     | `Ns1F8bpJ1LJcHvvcH2sqFA==` (outdated) |

## Request Signing

Every request includes a signature parameter `s` computed as follows:

1. Collect all parameters (including either `salt` for authenticated or `aesKey` for
   unauthenticated requests).
2. Sort all parameter keys alphabetically (ascending).
3. Pair each key (ascending order) with a value from the descending-ordered keys:
   - `concat = key[0] + inspect(value_of_key[last]) + key[1] + inspect(value_of_key[second_to_last]) + ...`
4. `inspect(value)` rules:
   - Boolean: lowercase string (`"true"` / `"false"`)
   - Object/Array: `JSON.stringify()` -> sort characters -> MD5 hex digest
   - Everything else: `String(value)`
5. Compute: `md5_hex = MD5(concat)`
6. Return: `md5_hex[1:-2]` (strip first char and last two chars)
7. Add result as parameter `s`, then remove `salt` or `aesKey` from the payload.

### Signing Modes

| Mode       | When Used             | Extra Parameter     |
|------------|-----------------------|---------------------|
| Salt-based | Authenticated routes  | `salt = user.salt`  |
| AES-key    | Unauthenticated routes| `aesKey = ENCRYPT_KEY` |

## Response Handling

Responses are standard JSON **or** AES-ECB encrypted hex strings.

```
if response is a string (not JSON object):
    1. Hex-decode the string
    2. AES-ECB decrypt with DECRYPT_KEY
    3. PKCS7 unpad
    4. JSON parse the plaintext
```

---

## Authentication

### POST /user/sign_in_
Sign in with email and password. Uses AES-key signing.

**Parameters:**
| Field        | Type    | Required | Description          |
|--------------|---------|----------|----------------------|
| email        | string  | yes      | User email           |
| password     | string  | yes      | User password        |
| rememberMe   | boolean | no       | Persist session      |
| vkey         | string  | no       | CAPTCHA key          |
| vcode        | string  | no       | CAPTCHA solution     |

**Response:** `{ status: 200, user: { id, username, email, salt, vip, payType, payLevel, ... } }`

### POST /user/direct_sign_in
Re-authenticate with existing session. Uses salt signing.

**Parameters:** `{ ud: userId }`

### POST /user/get
Get current user profile. Uses salt signing.

**Parameters:** `{ ud: userId }`

### POST /user/exit
Sign out. Uses salt signing.

**Parameters:** `{ ud: userId }`

### POST /user/update
Update profile fields. Uses salt signing.

**Parameters:** `{ ud: userId, ...fields }`

### POST /user/create_tourist
Create temporary guest account. Uses AES-key signing.

**Parameters:** `{}`

### POST /user/check_email
Validate email address. Uses AES-key signing.

**Parameters:** `{ email: string }`

### POST /user/reset_pwd
Request password reset. Uses AES-key signing.

**Parameters:** `{ email: string }`

### POST /user/delete
Delete account. Uses salt signing.

**Parameters:** `{ ud: userId }`

### GET /verify_code/generate
Generate CAPTCHA image.

**Parameters (query):** `{ vkey: string, s: signature }`

**Response:** PNG image bytes.

---

## Drives

### POST /drives/list
List all connected cloud drives. Uses salt signing.

**Parameters:**
| Field | Type    | Required | Description               |
|-------|---------|----------|---------------------------|
| ud    | string  | yes      | User ID                   |
| sa    | boolean | no       | Show all (including hidden)|

**Response:** `{ drives: [{ id, cloudType, name, email, ... }] }`

### POST /drives/add
Initiate adding a new cloud drive (triggers OAuth). Uses salt signing.

**Parameters:** `{ ud, cloudType }`

**Response:** `{ authUrl: "https://..." }` (redirect user to this URL)

### POST /drives/delete
Remove a cloud drive. Uses salt signing.

**Parameters:** `{ ud, id: driveId }`

### POST /drives/rename
Rename a cloud drive. Uses salt signing.

**Parameters:** `{ ud, id: driveId, name: newName }`

### POST /drives/get
Get drive details. Uses salt signing.

**Parameters:** `{ ud, id: driveId }`

### POST /drives/list_categories
List drive categories. Uses salt signing.

**Parameters:** `{ ud }`

### POST /drives/send_code
Send auth code for drive verification. Uses salt signing.

**Parameters:** `{ ud, id: driveId }`

### GET /drives/auth
OAuth callback for drive authorization.

**Parameters (query):** `{ state: oauthState }`

---

## Supported Cloud Types

| Internal Name         | Display Name              |
|-----------------------|---------------------------|
| google_drive          | Google Drive               |
| dropbox               | Dropbox                    |
| onedrive              | OneDrive                   |
| onedrive4Business     | OneDrive for Business      |
| box                   | Box                        |
| mega                  | MEGA                       |
| pcloud                | pCloud                     |
| s3                    | Amazon S3                  |
| ftp                   | FTP                        |
| sftp                  | SFTP                       |
| webdav                | WebDAV                     |
| google_photos         | Google Photos              |
| flickr                | Flickr                     |
| google_workspace      | Google Workspace           |
| sharepoint            | SharePoint                 |
| backblaze             | Backblaze B2               |
| wasabi                | Wasabi                     |
| icloud_drive          | iCloud Drive               |
| aDrive                | aDrive                     |
| baidu                 | Baidu Cloud                |
| yandex                | Yandex Disk                |
| hubic                 | hubiC                      |
| sugarsync             | SugarSync                  |
| cloudme               | CloudMe                    |
| cubby                 | Cubby                      |
| myDrive               | MyDrive                    |
| webo                  | WEB.DE                     |
| hidrive               | HiDrive                    |
| mediafire             | MediaFire                  |
| owncloud              | ownCloud                   |
| mysql                 | MySQL                      |
| nas                   | NAS                        |
| 1fichier              | 1Fichier                   |
| icedrive              | Icedrive                   |
| idrive                | IDrive e2                  |
| google_cloud_storage  | Google Cloud Storage       |
| azure_blob            | Azure Blob                 |
| dropbox4Business      | Dropbox Business           |

---

## Files

### POST /files/list
List files/folders in a directory. Uses salt signing.

**Parameters:**
| Field      | Type   | Required | Description                |
|------------|--------|----------|----------------------------|
| ud         | string | yes      | User ID                    |
| driveId    | string | yes      | Drive ID                   |
| fileId     | string | no       | Directory ID (default: root)|
| cloudType  | string | no       | Cloud type hint            |

**Response:** `{ files: [{ id, name, size, dir, modified, ... }] }`

### POST /files/mkdir
Create a directory. Uses salt signing.

**Parameters:** `{ ud, driveId, pid: parentId, name, cloudType? }`

### POST /files/delete
Delete files. Uses salt signing.

**Parameters:** `{ ud, driveId, items: [fileId, ...], cloudType? }`

### POST /files/rename
Rename a file or folder. Uses salt signing.

**Parameters:** `{ ud, driveId, id: fileId, name: newName, cloudType? }`

### POST /files/search
Search for files. Uses salt signing.

**Parameters:** `{ ud, driveId, keyword, cloudType? }`

### POST /files/copy
Copy files between drives. Uses salt signing.

**Parameters:** `{ ud, fromItems: [...], toItems: [...] }`

### POST /files/move
Move files between drives. Uses salt signing.

**Parameters:** `{ ud, fromItems: [...], toItems: [...] }`

### POST /files/share
Get sharing link. Uses salt signing.

**Parameters:** `{ ud, driveId, id: fileId, cloudType? }`

### POST /files/empty_trash
Empty recycle bin. Uses salt signing.

**Parameters:** `{ ud, driveId, cloudType? }`

### POST /files/recycle_bin
List files in recycle bin. Uses salt signing.

**Parameters:** `{ ud, driveId, cloudType? }`

### POST /files/restore
Restore files from recycle bin. Uses salt signing.

**Parameters:** `{ ud, driveId, items: [fileId, ...], cloudType? }`

### POST /files/recover_all
Recover all files from trash. Uses salt signing.

### POST /files/go_drive_site
Get direct link to cloud provider. Uses salt signing.

### GET /files/{id}/content
Download/preview file content. No signing required.

---

## Tasks (Transfer / Sync / Backup)

### Task Types

| Type | Name             | Description                     |
|------|------------------|---------------------------------|
| 1    | Cloud Transfer   | Copy files between clouds       |
| 3    | Remote Upload    | Download URL to cloud drive     |
| 6    | Cloud Sync/Backup| Sync or backup between clouds   |

### POST /tasks/add
Create a new task. Uses salt signing.

**Parameters:**
| Field      | Type   | Required | Description                    |
|------------|--------|----------|--------------------------------|
| ud         | string | yes      | User ID                        |
| type       | int    | yes      | Task type (1, 3, or 6)         |
| fromItems  | array  | yes*     | Source items (* not for type 3) |
| toItems    | array  | yes      | Destination items               |
| name       | string | no       | Task name                      |
| n          | string | no       | Filename (for type 3)          |
| url        | string | no       | Source URL (for type 3)        |
| options    | object | no       | Task options (see below)       |

**Task Options Object:**
| Field         | Type   | Description                         |
|---------------|--------|-------------------------------------|
| timeZone      | string | Timezone (e.g., "UTC")              |
| scheduleTime  | string | Schedule time for execution         |
| syncMode      | string | Sync mode (for type 6)              |
| filter        | object | File filter rules                   |
| deleteSource  | bool   | Delete source after transfer        |
| overwrite     | string | Overwrite behavior                  |

**Item Object Format:**
```json
{
  "driveType": "google_drive",
  "driveId": "abc123",
  "pid": "root",
  "fileId": "root",
  "filename": "Root",
  "isDir": true,
  "nodes": [{"fileId": "root", "filename": "Root"}]
}
```

### POST /tasks/list
List tasks. Uses salt signing.

**Parameters:** `{ ud, type? }`

### POST /tasks/all_list
List all tasks across all types. Uses salt signing.

**Parameters:** `{ ud }`

### POST /tasks/get
Get task details. Uses salt signing.

**Parameters:** `{ ud, id: taskId }`

### POST /tasks/execute
**Trigger/run an existing task immediately.** Uses salt signing.

**Parameters:** `{ ud, id: taskId }`

### POST /tasks/cancel
Cancel a running task. Uses salt signing.

**Parameters:** `{ ud, id: taskId }`

### POST /tasks/delete
Delete a task. Uses salt signing.

**Parameters:** `{ ud, id: taskId }`

### POST /tasks/delete_batch
Delete multiple tasks. Uses salt signing.

**Parameters:** `{ ud, ids: [taskId, ...] }`

### POST /tasks/update
Update task configuration. Uses salt signing.

**Parameters:** `{ ud, id: taskId, ...fields }`

### POST /tasks/get_progress
Get task execution progress. Uses salt signing.

**Parameters:** `{ ud, id: taskId }`

**Response:** `{ progress: number }` (0-100)

### POST /tasks/list_running_tasks
List currently running tasks. Uses salt signing.

**Parameters:** `{ ud }`

### POST /tasks/list_versions
List backup versions for a task. Uses salt signing.

**Parameters:** `{ ud, id: taskId }`

### POST /tasks/delete_version
Delete a backup version. Uses salt signing.

**Parameters:** `{ ud, id: taskId, versionId }`

### POST /tasks/list_restore
List restore points. Uses salt signing.

**Parameters:** `{ ud, id: taskId }`

### POST /tasks/remove_completed_task
Remove all completed tasks. Uses salt signing.

**Parameters:** `{ ud }`

---

## Realtime Sync

### POST /realtime_sync/create
Create a realtime sync task. Uses salt signing.

**Parameters:**
| Field      | Type   | Required | Description          |
|------------|--------|----------|----------------------|
| ud         | string | yes      | User ID              |
| fromItems  | array  | yes      | Source items          |
| toItems    | array  | yes      | Destination items     |
| syncType   | string | no       | Sync type            |
| name       | string | no       | Task name            |

### POST /realtime_sync/list
List realtime sync tasks. Uses salt signing.

**Parameters:** `{ ud }`

### POST /realtime_sync/get
Get realtime sync details. Uses salt signing.

**Parameters:** `{ ud, id: syncId }`

### POST /realtime_sync/switch_status
**Enable/disable a realtime sync task.** Uses salt signing.

**Parameters:** `{ ud, id: syncId, status: boolean }`

### POST /realtime_sync/switch_type
Change sync type. Uses salt signing.

**Parameters:** `{ ud, id: syncId, syncType: string }`

### POST /realtime_sync/cancel
Cancel/delete a realtime sync task. Uses salt signing.

**Parameters:** `{ ud, id: syncId }`

---

## Torrent / Remote Upload

### POST /torrent/add
Add a torrent/magnet for remote download. Uses salt signing.

**Parameters:** `{ ud, url: magnetOrTorrentUrl, toItems: [...] }`

### POST /torrent/parse
Parse a torrent file or magnet link. Uses salt signing.

**Parameters:** `{ ud, url: magnetOrTorrentUrl }`

### POST /torrent/delete
Delete a torrent task. Uses salt signing.

**Parameters:** `{ ud, id: taskId }`

### POST /torrent/progress
Get torrent download progress. Uses salt signing.

**Parameters:** `{ ud, id: taskId }`

---

## Video Saver

### POST /video_saver/analyze_url
Analyze a video URL for available downloads. Uses salt signing.

**Parameters:** `{ ud, url }`

### POST /video_saver/download_add
Start downloading a video to cloud. Uses salt signing.

**Parameters:** `{ ud, url, driveId, ...options }`

### POST /video_saver/image_download_add
Download an image to cloud. Uses salt signing.

**Parameters:** `{ ud, url, driveId, ...options }`

### POST /video_saver/list_task
List video saver tasks. Uses salt signing.

**Parameters:** `{ ud }`

### POST /video_saver/get_task
Get task details. Uses salt signing.

**Parameters:** `{ ud, id: taskId }`

### POST /video_saver/download_progress
Get download progress. Uses salt signing.

**Parameters:** `{ ud, id: taskId }`

### POST /video_saver/cancel_task
Cancel a download. Uses salt signing.

**Parameters:** `{ ud, id: taskId }`

### POST /video_saver/retry_task
Retry a failed download. Uses salt signing.

**Parameters:** `{ ud, id: taskId }`

### POST /video_saver/save_task
Save a download task. Uses salt signing.

### POST /video_saver/clear_history
Clear download history. Uses salt signing.

**Parameters:** `{ ud }`

---

## Cloud Email Migration

### POST /cloud_email/list
List email migrations. Uses salt signing.

**Parameters:** `{ ud }`

### POST /cloud_email/delete
Delete an email migration. Uses salt signing.

**Parameters:** `{ ud, id: taskId }`

### POST /cloud_email_tasks/pause
Pause an email migration task. Uses salt signing.

**Parameters:** `{ ud, id: taskId }`

### GET /cloud_email/{id}/content
Get email content. No signing.

---

## Business Transfer

### POST /business_transfer/create
Create a business transfer. Uses salt signing.

### POST /business_transfer/execute
Execute a business transfer. Uses salt signing.

**Parameters:** `{ ud, id: transferId }`

### POST /business_transfer/get
Get transfer details. Uses salt signing.

**Parameters:** `{ ud, id: transferId }`

### POST /business_transfer/update
Update a transfer. Uses salt signing.

### POST /business_transfer/cancel
Cancel a transfer. Uses salt signing.

**Parameters:** `{ ud, id: transferId }`

### POST /business_transfer/delete
Delete a transfer. Uses salt signing.

**Parameters:** `{ ud, id: transferId }`

### POST /business_transfer/progress
Get progress. Uses salt signing.

**Parameters:** `{ ud, id: transferId }`

### POST /business_transfer/members
List team members. Uses salt signing.

**Parameters:** `{ ud }`

### POST /business_transfer/whole_matching
Match accounts for bulk transfer. Uses salt signing.

### POST /business_transfer/csv_parse
Parse CSV for bulk transfer. Multipart form upload.

### GET /business_transfer/csv_download/
Download CSV template.

### GET /business_transfer/csv_sample/
Download sample CSV.

---

## Sharing

### POST /share/create_share_url
Create a share link. Uses salt signing.

**Parameters:** `{ ud, shareFiles: { driveId, fileId }, password?, ... }`

### POST /share/create_share_transfers_url
Create a transfer share. Uses salt signing.

### POST /share/check_share
Check share validity. Uses salt signing.

**Parameters:** `{ ud, shareId }`

### POST /share/check_password
Verify share password. Uses salt signing.

**Parameters:** `{ ud, shareId, password }`

### POST /share/update_share
Update share settings. Uses salt signing.

**Parameters:** `{ ud, shareId, ...fields }`

### POST /share/select_all_share
List all shares. Uses salt signing.

**Parameters:** `{ ud }`

### POST /share/select_all_saved_share
List saved shares. Uses salt signing.

### POST /share/get_share_transfers
Get shared transfers. Uses salt signing.

### POST /share/get_share_transfer_files
Get shared transfer files. Uses salt signing.

### POST /share/change_share_upload_status
Toggle upload on a share. Uses salt signing.

**Parameters:** `{ ud, shareId, status: boolean }`

---

## Email Notifications

### POST /email/send_activate_code
Send activation email. Uses AES-key signing.

### POST /email/send_forgot_code
Send password reset email. Uses AES-key signing.

### POST /email/send_invite_friends
Send invitation emails. Uses AES-key signing.

**Parameters:** `{ ud, emails: [string, ...] }`

### POST /email/send_share_infos
Send share notification. Uses AES-key signing.

### POST /email/send_test_msg
Test email sending. Uses AES-key signing.

---

## Subscription

### POST /subscription/add_cart_records
Add item to cart. Uses salt signing.

**Parameters:** `{ ud, productId, source: 1, coupon? }`

### POST /subscription/license_redemption
Redeem a license key. Uses salt signing.

**Parameters:** `{ ud, licenseKey }`

---

## Other Endpoints

### POST /notify/get_version_info
Check for updates. Uses salt signing.

### POST /invite/get_information
Get invite info. Uses salt signing.

### POST /subaccount/add
Add sub-account. Uses salt signing.

**Parameters:** `{ ud, email, ...options }`

### POST /subaccount/del
Delete sub-account. Uses salt signing.

**Parameters:** `{ ud, id: subId }`

### POST /subaccount/edit
Edit sub-account. Uses salt signing.

### POST /subaccount/query
List sub-accounts. Uses salt signing.

### POST /permission/*
Permission management endpoints. Uses salt signing.

### POST /dual_verify/*
Two-factor authentication endpoints. Uses salt/AES signing.

### POST /feedback/*
User feedback endpoints. Uses salt signing.

---

## Session Management

- Login sets session cookies (including `JSESSIONID`).
- The `ud` (user ID) parameter is required in most authenticated requests.
- The `salt` comes from the user object returned at login.
- Session can be persisted by saving cookies + user data (id, salt).
- Use `/user/direct_sign_in` to re-authenticate with stored session.

## Error Handling

API responses follow this structure:
```json
{
  "status": 200,
  "message": "OK",
  "data": { ... }
}
```

Error responses:
```json
{
  "status": 4xx,
  "message": "Error description",
  "reason": "detailed_reason_code"
}
```

Common status codes:
- 200: Success
- 401: Unauthorized (session expired)
- 403: Forbidden (insufficient permissions)
- 429: Rate limited
- 500: Server error

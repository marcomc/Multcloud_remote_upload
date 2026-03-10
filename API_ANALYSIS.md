# MultCloud Reverse-Engineered API Analysis (March 2026)

Extracted from `https://app.multcloud.com/static/js/app.6bbab2e3ed982ee96612.js`

## Base Configuration

| Key | Value |
|-----|-------|
| API URL (App) | `https://app.multcloud.com/api` |
| API URL (Preview) | `https://www.multcloud.com/api` |
| AES Encrypt Key | `KXrDPHUkQSMKhklkKHHP+Q==` |
| AES Decrypt Key | `LIa4CTfB3SwKnfJhu2iJkQ==` |
| AES Mode | ECB |
| AES Padding | PKCS7 |
| Signing | MD5-based HMAC on sorted key+value pairs |

## Request Signing

All requests are signed with an `s` parameter calculated via MD5:
1. Sort all parameter keys alphabetically
2. Concatenate: `key[0] + stringify(value[last]) + key[1] + stringify(value[second-to-last]) + ...`
   (keys in ascending order paired with values in descending order of keys)
3. For object/array values: `JSON.stringify() -> sort chars -> MD5`
4. Take MD5 hex digest, strip first and last 2 chars: `md5[1:-2]`
5. Two signing modes:
   - **Salt signing** (`w()`): uses `user.salt` from localStorage
   - **AES key signing** (`M()`): uses the ENCRYPT_KEY constant

## Authentication Endpoints

| Method | Endpoint | Signing | Description |
|--------|----------|---------|-------------|
| POST | `/api/user/sign_in_` | AES key | Login with email/password |
| POST | `/api/user/sign_up` | AES key | Register new account |
| POST | `/api/user/check_email` | AES key | Validate email |
| POST | `/api/user/get` | Salt | Get user profile |
| POST | `/api/user/direct_sign_in` | Salt | Re-auth with stored session |
| POST | `/api/user/exit` | Salt | Logout |
| POST | `/api/user/update` | Salt | Update user profile |
| POST | `/api/user/delete` | Salt | Delete account |
| POST | `/api/user/create_tourist` | AES key | Create temporary account |
| POST | `/api/user/sel_user` | AES key | Lookup user |
| POST | `/api/user/reset_pwd` | AES key | Password reset |
| POST | `/api/user/third_login` | - | OAuth login |
| POST | `/api/verify_code/generate` | AES key | Generate CAPTCHA |

## Drive Management Endpoints

| Method | Endpoint | Signing | Description |
|--------|----------|---------|-------------|
| POST | `/api/drives/list` | Salt | List all connected cloud drives |
| POST | `/api/drives/add` | Salt | Add a new cloud drive |
| POST | `/api/drives/delete` | Salt | Remove a cloud drive |
| POST | `/api/drives/get` | Salt | Get drive details |
| POST | `/api/drives/rename` | Salt | Rename a drive |
| POST | `/api/drives/list_categories` | Salt | List drive categories |
| POST | `/api/drives/send_code` | Salt | Send auth code for drive |
| GET | `/api/drives/auth?state=` | - | OAuth callback for drive auth |

## File Operations Endpoints

| Method | Endpoint | Signing | Description |
|--------|----------|---------|-------------|
| POST | `/api/files/list` | Salt | List files in a directory |
| POST | `/api/files/mkdir` | Salt | Create directory |
| POST | `/api/files/delete` | Salt | Delete files |
| POST | `/api/files/rename` | Salt | Rename file/folder |
| POST | `/api/files/search` | Salt | Search files |
| POST | `/api/files/share` | Salt | Share file |
| POST | `/api/files/copy` | Salt | Copy files between drives |
| POST | `/api/files/move` | Salt | Move files between drives |
| POST | `/api/files/empty_trash` | Salt | Empty trash |
| POST | `/api/files/recycle_bin` | Salt | View recycle bin |
| POST | `/api/files/restore` | Salt | Restore from trash |
| POST | `/api/files/recover_all` | Salt | Recover all from trash |
| POST | `/api/files/go_drive_site` | Salt | Get direct link to cloud provider |
| GET | `/api/files/{id}/content` | - | Download/preview file content |

## Task Management Endpoints (Cloud Transfer / Cloud Sync / Cloud Backup)

| Method | Endpoint | Signing | Description |
|--------|----------|---------|-------------|
| POST | `/api/tasks/add` | Salt | **Create a new transfer/sync/backup task** |
| POST | `/api/tasks/list` | Salt | List tasks for current user |
| POST | `/api/tasks/all_list` | Salt | List all tasks |
| POST | `/api/tasks/get` | Salt | Get task details |
| POST | `/api/tasks/update` | Salt | **Update task (schedule, options, etc.)** |
| POST | `/api/tasks/execute` | Salt | **Trigger/run an existing task** |
| POST | `/api/tasks/cancel` | Salt | Cancel a running task |
| POST | `/api/tasks/delete` | Salt | Delete a task |
| POST | `/api/tasks/delete_batch` | Salt | Delete multiple tasks |
| POST | `/api/tasks/get_progress` | Salt | Get task progress percentage |
| POST | `/api/tasks/list_running_tasks` | Salt | List currently running tasks |
| POST | `/api/tasks/list_versions` | Salt | List backup versions |
| POST | `/api/tasks/delete_version` | Salt | Delete a backup version |
| POST | `/api/tasks/list_restore` | Salt | List restore points |
| POST | `/api/tasks/remove_completed_task` | Salt | Clean up completed tasks |

## Realtime Sync Endpoints

| Method | Endpoint | Signing | Description |
|--------|----------|---------|-------------|
| POST | `/api/realtime_sync/create` | Salt | **Create a realtime sync task** |
| POST | `/api/realtime_sync/list` | Salt | List realtime sync tasks |
| POST | `/api/realtime_sync/get` | Salt | Get realtime sync details |
| POST | `/api/realtime_sync/switch_status` | Salt | **Enable/disable realtime sync** |
| POST | `/api/realtime_sync/switch_type` | Salt | Change sync type |
| POST | `/api/realtime_sync/cancel` | Salt | Cancel realtime sync |

## Torrent/Remote Upload Endpoints

| Method | Endpoint | Signing | Description |
|--------|----------|---------|-------------|
| POST | `/api/torrent/add` | Salt | Add torrent/magnet for remote download |
| POST | `/api/torrent/parse` | Salt | Parse torrent file |
| POST | `/api/torrent/parsefail` | Salt | Handle parse failure |
| POST | `/api/torrent/delete` | Salt | Delete torrent task |
| POST | `/api/torrent/progress` | Salt | Get torrent download progress |

## Video Saver Endpoints

| Method | Endpoint | Signing | Description |
|--------|----------|---------|-------------|
| POST | `/api/video_saver/analyze_url` | Salt | Analyze video URL |
| POST | `/api/video_saver/download_add` | Salt | Start video download |
| POST | `/api/video_saver/image_download_add` | Salt | Start image download |
| POST | `/api/video_saver/save_task` | Salt | Save download task |
| POST | `/api/video_saver/list_task` | Salt | List video saver tasks |
| POST | `/api/video_saver/get_task` | Salt | Get task details |
| POST | `/api/video_saver/download_progress` | Salt | Get download progress |
| POST | `/api/video_saver/cancel_task` | Salt | Cancel download |
| POST | `/api/video_saver/retry_task` | Salt | Retry failed download |
| POST | `/api/video_saver/clear_history` | Salt | Clear download history |

## Cloud Email Migration Endpoints

| Method | Endpoint | Signing | Description |
|--------|----------|---------|-------------|
| POST | `/api/cloud_email/list` | Salt | List email migrations |
| POST | `/api/cloud_email/delete` | Salt | Delete email migration |
| POST | `/api/cloud_email_tasks/pause` | Salt | Pause email migration task |
| GET | `/api/cloud_email/{id}/content` | - | Get email content |

## Business Transfer Endpoints

| Method | Endpoint | Signing | Description |
|--------|----------|---------|-------------|
| POST | `/api/business_transfer/create` | Salt | Create business transfer |
| POST | `/api/business_transfer/execute` | Salt | Execute business transfer |
| POST | `/api/business_transfer/get` | Salt | Get transfer details |
| POST | `/api/business_transfer/update` | Salt | Update transfer |
| POST | `/api/business_transfer/cancel` | Salt | Cancel transfer |
| POST | `/api/business_transfer/delete` | Salt | Delete transfer |
| POST | `/api/business_transfer/progress` | Salt | Get progress |
| POST | `/api/business_transfer/members` | Salt | List team members |
| POST | `/api/business_transfer/whole_matching` | Salt | Match accounts |
| POST | `/api/business_transfer/csv_parse` | multipart | Parse CSV for bulk transfer |
| GET | `/api/business_transfer/csv_download/` | - | Download CSV template |
| GET | `/api/business_transfer/csv_sample/` | - | Download sample CSV |

## Sharing Endpoints

| Method | Endpoint | Signing | Description |
|--------|----------|---------|-------------|
| POST | `/api/share/create_share_url` | Salt | Create share link |
| POST | `/api/share/create_share_transfers_url` | Salt | Create transfer share |
| POST | `/api/share/check_share` | Salt | Check share validity |
| POST | `/api/share/check_password` | Salt | Verify share password |
| POST | `/api/share/update_share` | Salt | Update share settings |
| POST | `/api/share/get_share_transfers` | Salt | Get shared transfers |
| POST | `/api/share/get_share_transfer_files` | Salt | Get shared files |
| POST | `/api/share/select_all_share` | Salt | List all shares |
| POST | `/api/share/select_all_saved_share` | Salt | List saved shares |
| POST | `/api/share/change_share_upload_status` | Salt | Toggle share upload |

## Other Endpoints

| Method | Endpoint | Signing | Description |
|--------|----------|---------|-------------|
| POST | `/api/email/send_activate_code` | AES key | Send activation email |
| POST | `/api/email/send_forgot_code` | AES key | Send password reset |
| POST | `/api/email/send_invite_friends` | AES key | Send invitation |
| POST | `/api/email/send_share_infos` | AES key | Send share notification |
| POST | `/api/email/send_test_msg` | AES key | Test email |
| POST | `/api/subscription/add_cart_records` | Salt | Add to cart |
| POST | `/api/subscription/license_redemption` | Salt | Redeem license |
| POST | `/api/notify/get_version_info` | Salt | Check for updates |
| POST | `/api/backup/{action}` | passthrough | Backup operations |
| POST | `/api/invite/get_information` | Salt | Get invite info |
| POST | `/api/subaccount/add` | Salt | Add sub-account |
| POST | `/api/subaccount/del` | Salt | Delete sub-account |
| POST | `/api/subaccount/edit` | Salt | Edit sub-account |
| POST | `/api/subaccount/query` | Salt | Query sub-accounts |
| POST | `/api/permission/*` | Salt | Permission management |
| POST | `/api/dual_verify/*` | Salt/AES | Two-factor auth |
| POST | `/api/feedback/*` | Salt | User feedback/ratings |
| POST | `/api/active_tag/*` | Salt | Activity tracking |
| POST | `/api/shareFile/list` | Salt | List shared files |
| GET | `/api/imagesaver/downloads?uuid=` | - | Download saved images |

## Key Findings for Cloud Sync Triggering

**YES — you CAN trigger cloud syncs programmatically.** The critical endpoints are:

1. **`/api/tasks/execute`** — Triggers an existing task (transfer/sync/backup) to run immediately
2. **`/api/tasks/add`** — Creates a new task with schedule options
3. **`/api/tasks/update`** — Updates task configuration (schedule, etc.)
4. **`/api/tasks/list`** — Lists all configured tasks
5. **`/api/realtime_sync/switch_status`** — Enables/disables realtime sync
6. **`/api/realtime_sync/create`** — Creates new realtime sync

The `tasks/add` endpoint accepts `options.timeZone` and likely schedule parameters.

## Task Types (from code analysis)

- Type 1: Cloud Transfer
- Type 3: Remote Upload (URL to cloud)
- Type 6: Cloud Sync / Cloud Backup
- Realtime sync uses separate `/realtime_sync/` endpoints

## Notes

- All API responses may be AES-ECB encrypted strings that need decryption with the DECRYPT_KEY
- The `ud` parameter (user ID) is required in most requests
- The `salt` comes from the user object stored in localStorage after login
- Session management uses cookies set during login
- The old repo's AES key (`Ns1F8bpJ1LJcHvvcH2sqFA==`) is **outdated** — new keys are above

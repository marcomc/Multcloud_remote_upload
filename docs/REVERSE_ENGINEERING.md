# Reverse Engineering MultCloud's API

This document describes how to reverse-engineer MultCloud's internal API when
they update their frontend. Use this as a guide to update the API reference
and library code when things change.

## Automated Method

Run the included script:

```bash
cd "MultCloud CLI v5.0.0"
python scripts/reverse_engineer_api.py --output ../docs/ --verbose

# Compare against previous analysis
python scripts/reverse_engineer_api.py --output ../docs/ --diff --previous-report ../docs/api_report.json
```

The script:
1. Fetches `https://app.multcloud.com`
2. Extracts webpack JS bundle URLs from HTML
3. Downloads the JS bundle(s)
4. Uses regex patterns to extract: AES keys, API endpoints, cloud types, signing logic
5. Outputs a structured JSON report with all findings

## Manual Method

### Step 1: Identify the JS Bundle

1. Open `https://app.multcloud.com` in a browser
2. Open Developer Tools (F12) -> Sources tab
3. Look for files matching `app.*.js` or `main.*.js` under `/static/js/`
4. Or check Network tab for the largest JS file loaded

### Step 2: Extract AES Keys

Search the JS for base64-encoded 16-byte keys (24 chars ending in `==`):

```
Search pattern: /[A-Za-z0-9+/]{22}==/
```

Look for context like:
- `ENCRYPT_KEY`, `encryptKey`, `aesKey`
- `DECRYPT_KEY`, `decryptKey`
- Near `AES`, `ECB`, `decrypt`, `encrypt`

There should be two keys:
- **Encrypt key**: Used for signing unauthenticated requests
- **Decrypt key**: Used for decrypting API responses

### Step 3: Extract API Endpoints

Search for URL path patterns:

```
Search pattern: /\/api\/\w+\/\w+/
```

Or look for route definitions:
```
Search pattern: /["']\/(?:user|drives|files|tasks|realtime_sync|torrent|video_saver)\//
```

### Step 4: Verify the Signing Algorithm

Search for the MD5-based signing function:

```
Search pattern: /md5.*sort|sort.*md5/
```

The signing function should:
1. Sort keys alphabetically
2. Pair keys ascending with values descending
3. Concatenate all key+value pairs
4. MD5 hash
5. Strip first and last 2 characters

### Step 5: Check for New Cloud Types

Search for cloud provider identifiers:

```
Search pattern: /cloudType.*?["'](\w+)["']/
Search pattern: /driveType.*?["'](\w+)["']/
```

### Step 6: Check for New Task Types

Search for task type constants:

```
Search pattern: /type:\s*[0-9]+/
```

Known types: 1 (Transfer), 3 (Remote Upload), 6 (Sync/Backup)

## What to Update When Keys/Endpoints Change

1. **AES Keys changed:**
   - Update `ENCRYPT_KEY` and `DECRYPT_KEY` in `multcloud/crypto.py`
   - Update docs: `docs/API_REFERENCE.md` and `API_ANALYSIS.md`

2. **New endpoints found:**
   - Add methods to `multcloud/client.py`
   - Add CLI commands to `multcloud/cli.py`
   - Update docs

3. **Signing algorithm changed:**
   - Update `sign_md5()` in `multcloud/crypto.py`
   - Update algorithm description in docs

4. **New cloud types:**
   - Update `CLOUD_TYPES` dict in `multcloud/cli.py`
   - Update docs

5. **Login endpoint changed:**
   - The old endpoint was `/user/sign_in`, it changed to `/user/sign_in_`
   - Check for any new login endpoints

## Historical Changes

| Date       | Change                                       |
|------------|----------------------------------------------|
| 2021       | Original API with key `Ns1F8bpJ1LJcHvvcH2sqFA==` |
| 2026-03    | New keys: `KXrDPHUkQSMKhklkKHHP+Q==` (encrypt), `LIa4CTfB3SwKnfJhu2iJkQ==` (decrypt) |
| 2026-03    | Login endpoint changed from `/user/sign_in` to `/user/sign_in_` |
| 2026-03    | App URL changed from `www.multcloud.com` to `app.multcloud.com` |
| 2026-03    | Many new endpoints added: video_saver, business_transfer, realtime_sync, cloud_email |

## Caveats

- MultCloud may deploy changes that break the API without notice
- Rate limiting may apply to API requests
- Some endpoints may require a premium subscription
- The AES keys are constants compiled into the frontend JS; they're not per-user
- The user's `salt` from the login response IS per-user and is needed for authenticated signing

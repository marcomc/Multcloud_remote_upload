#!/usr/bin/env python3
"""
MultCloud API Reverse-Engineering Script.

This script automates the process of extracting API endpoints, encryption keys,
and signing logic from MultCloud's frontend JavaScript bundle. Run this when
MultCloud updates their frontend to detect any API changes.

Usage:
    python reverse_engineer_api.py [--output OUTPUT_DIR] [--diff]

The script:
1. Downloads MultCloud's main app page
2. Extracts the webpack JS bundle URL
3. Downloads and parses the JS bundle
4. Extracts: AES keys, API endpoints, signing logic, cloud types, task types
5. Outputs a structured JSON report and optionally a diff against the current known API

Requirements:
    pip install requests beautifulsoup4
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' is required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)

APP_URL = "https://app.multcloud.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"

# Patterns to extract from JS bundle
PATTERNS = {
    "encrypt_key": [
        r'ENCRYPT_KEY\s*[=:]\s*["\']([A-Za-z0-9+/=]{20,})["\']',
        r'encryptKey\s*[=:]\s*["\']([A-Za-z0-9+/=]{20,})["\']',
        r'aesKey\s*[=:]\s*["\']([A-Za-z0-9+/=]{20,})["\']',
        r'["\']([A-Za-z0-9+/=]{24})["\'].*?ECB',
    ],
    "decrypt_key": [
        r'DECRYPT_KEY\s*[=:]\s*["\']([A-Za-z0-9+/=]{20,})["\']',
        r'decryptKey\s*[=:]\s*["\']([A-Za-z0-9+/=]{20,})["\']',
    ],
    "api_base": [
        r'apiUrl\s*[=:]\s*["\']([^"\']+/api)["\']',
        r'API_BASE\s*[=:]\s*["\']([^"\']+/api)["\']',
        r'baseURL\s*[=:]\s*["\']([^"\']+/api)["\']',
    ],
    "api_endpoints": [
        r'["\'](/(?:user|drives|files|tasks|realtime_sync|torrent|video_saver|cloud_email|business_transfer|share|email|subscription|notify|backup|invite|subaccount|permission|dual_verify|feedback|active_tag|shareFile|imagesaver|verify_code)/[a-z_]+)["\']',
    ],
    "cloud_types": [
        r'["\']cloudType["\']\s*:\s*["\'](\w+)["\']',
        r'driveType\s*[=:]\s*["\'](\w+)["\']',
        r'cloud_type\s*[=:]\s*["\'](\w+)["\']',
    ],
    "signing_function": [
        r'(function\s+\w+\s*\([^)]*\)\s*\{[^}]*md5[^}]*sort[^}]*\})',
        r'(\w+\s*=\s*function\s*\([^)]*\)\s*\{[^}]*md5[^}]*sort[^}]*\})',
    ],
}

# Known endpoint prefixes to group
ENDPOINT_GROUPS = {
    "auth": "/user/",
    "drives": "/drives/",
    "files": "/files/",
    "tasks": "/tasks/",
    "realtime_sync": "/realtime_sync/",
    "torrent": "/torrent/",
    "video_saver": "/video_saver/",
    "cloud_email": "/cloud_email",
    "business_transfer": "/business_transfer/",
    "share": "/share/",
    "email": "/email/",
    "subscription": "/subscription/",
    "notify": "/notify/",
    "subaccount": "/subaccount/",
    "permission": "/permission/",
    "other": "",
}


def fetch_url(url: str) -> str:
    """Fetch a URL and return its text content."""
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return resp.text


def find_js_bundles(html: str) -> list[str]:
    """Extract webpack JS bundle URLs from the HTML page."""
    # Look for app.*.js or main.*.js patterns
    patterns = [
        r'src=["\']([^"\']*app\.[a-f0-9]+\.js)["\']',
        r'src=["\']([^"\']*main\.[a-f0-9]+\.js)["\']',
        r'src=["\']([^"\']*chunk[^"\']*\.js)["\']',
        r'src=["\']([^"\']+/static/js/[^"\']+\.js)["\']',
    ]
    bundles = []
    for pattern in patterns:
        matches = re.findall(pattern, html)
        bundles.extend(matches)
    return list(dict.fromkeys(bundles))  # dedupe preserving order


def extract_patterns(js_content: str) -> dict:
    """Extract known patterns from JS bundle content."""
    results = {}
    for key, pattern_list in PATTERNS.items():
        matches = set()
        for pattern in pattern_list:
            found = re.findall(pattern, js_content, re.IGNORECASE)
            matches.update(found)
        results[key] = sorted(matches)
    return results


def extract_aes_key_pairs(js_content: str) -> list[dict]:
    """Try to find AES key pairs (encrypt/decrypt) near each other."""
    pairs = []
    # Look for base64-encoded 16-byte keys (24 chars in base64)
    b64_keys = re.findall(r'["\']([A-Za-z0-9+/]{22}==)["\']', js_content)
    seen = set()
    for key in b64_keys:
        if key not in seen:
            seen.add(key)
            # Find context around the key
            idx = js_content.index(f'"{key}"') if f'"{key}"' in js_content else js_content.index(f"'{key}'")
            context = js_content[max(0, idx - 200):idx + 200]
            pairs.append({"key": key, "context_snippet": context[:100]})
    return pairs


def group_endpoints(endpoints: list[str]) -> dict:
    """Group endpoints by their API category."""
    grouped = {k: [] for k in ENDPOINT_GROUPS}
    for ep in endpoints:
        placed = False
        for group, prefix in ENDPOINT_GROUPS.items():
            if group == "other":
                continue
            if ep.startswith(prefix):
                grouped[group].append(ep)
                placed = True
                break
        if not placed:
            grouped["other"].append(ep)
    # Remove empty groups
    return {k: sorted(v) for k, v in grouped.items() if v}


def compute_bundle_hash(content: str) -> str:
    """Compute hash of the JS bundle for change detection."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def generate_report(extracted: dict, bundle_urls: list, bundle_hash: str) -> dict:
    """Generate the full analysis report."""
    endpoints = extracted.get("api_endpoints", [])
    return {
        "metadata": {
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "bundle_urls": bundle_urls,
            "bundle_hash": bundle_hash,
            "tool_version": "1.0.0",
        },
        "encryption": {
            "encrypt_keys": extracted.get("encrypt_key", []),
            "decrypt_keys": extracted.get("decrypt_key", []),
            "mode": "AES-ECB",
            "padding": "PKCS7",
        },
        "api": {
            "base_urls": extracted.get("api_base", []),
            "endpoints": group_endpoints(endpoints),
            "total_endpoints": len(endpoints),
        },
        "cloud_types": extracted.get("cloud_types", []),
        "signing": {
            "found_functions": len(extracted.get("signing_function", [])),
            "description": "MD5-based HMAC: sort keys ascending, pair with values descending, "
                           "concat key+inspectValue pairs, MD5 hash, strip first and last 2 chars.",
        },
    }


def diff_reports(current: dict, previous: dict) -> dict:
    """Compare two reports and return the differences."""
    changes = {"added": {}, "removed": {}, "changed": {}}

    # Compare keys
    for section in ["encryption", "api", "cloud_types"]:
        cur = current.get(section, {})
        prev = previous.get(section, {})
        if cur != prev:
            changes["changed"][section] = {"current": cur, "previous": prev}

    # Compare endpoints specifically
    cur_eps = set()
    prev_eps = set()
    for group_eps in current.get("api", {}).get("endpoints", {}).values():
        cur_eps.update(group_eps)
    for group_eps in previous.get("api", {}).get("endpoints", {}).values():
        prev_eps.update(group_eps)

    added_eps = cur_eps - prev_eps
    removed_eps = prev_eps - cur_eps
    if added_eps:
        changes["added"]["endpoints"] = sorted(added_eps)
    if removed_eps:
        changes["removed"]["endpoints"] = sorted(removed_eps)

    # Compare keys
    cur_enc = set(current.get("encryption", {}).get("encrypt_keys", []))
    prev_enc = set(previous.get("encryption", {}).get("encrypt_keys", []))
    if cur_enc != prev_enc:
        changes["changed"]["encrypt_keys"] = {
            "added": sorted(cur_enc - prev_enc),
            "removed": sorted(prev_enc - cur_enc),
        }

    return changes


def main():
    parser = argparse.ArgumentParser(
        description="Reverse-engineer MultCloud's API from their frontend JS bundle."
    )
    parser.add_argument(
        "--output", "-o",
        default=".",
        help="Output directory for the report (default: current directory)",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Compare against the previous report and show differences",
    )
    parser.add_argument(
        "--previous-report",
        help="Path to previous report JSON for diff comparison",
    )
    parser.add_argument(
        "--js-url",
        help="Direct URL to the JS bundle (skip auto-detection)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] MultCloud API Reverse-Engineering Tool")
    print(f"[*] Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()

    # Step 1: Get JS bundle
    if args.js_url:
        bundle_urls = [args.js_url]
    else:
        print("[1/4] Fetching MultCloud app page...")
        try:
            html = fetch_url(APP_URL)
        except Exception as e:
            print(f"  ERROR: Could not fetch {APP_URL}: {e}", file=sys.stderr)
            sys.exit(1)

        bundle_urls = find_js_bundles(html)
        if not bundle_urls:
            print("  WARNING: No JS bundles found in HTML page.", file=sys.stderr)
            print("  The page structure may have changed. Check manually.", file=sys.stderr)
            sys.exit(1)
        print(f"  Found {len(bundle_urls)} JS bundle(s)")

    # Step 2: Download and analyze bundles
    print("[2/4] Downloading and analyzing JS bundles...")
    all_js = ""
    for url in bundle_urls:
        if not url.startswith("http"):
            url = APP_URL + url if url.startswith("/") else f"{APP_URL}/{url}"
        if args.verbose:
            print(f"  Fetching: {url}")
        try:
            js = fetch_url(url)
            all_js += "\n" + js
            print(f"  Downloaded: {url.split('/')[-1]} ({len(js):,} bytes)")
        except Exception as e:
            print(f"  WARNING: Could not fetch {url}: {e}", file=sys.stderr)

    if not all_js:
        print("ERROR: No JS content could be fetched.", file=sys.stderr)
        sys.exit(1)

    bundle_hash = compute_bundle_hash(all_js)
    print(f"  Bundle hash: {bundle_hash}")

    # Step 3: Extract patterns
    print("[3/4] Extracting API patterns...")
    extracted = extract_patterns(all_js)
    aes_keys = extract_aes_key_pairs(all_js)

    for key, values in extracted.items():
        if values and key != "signing_function":
            print(f"  {key}: {len(values)} match(es)")
            if args.verbose:
                for v in values[:5]:
                    print(f"    - {v[:80]}")

    if aes_keys:
        print(f"  AES key candidates: {len(aes_keys)}")
        if args.verbose:
            for k in aes_keys:
                print(f"    - {k['key']}")

    # Step 4: Generate report
    print("[4/4] Generating report...")
    report = generate_report(extracted, bundle_urls, bundle_hash)
    report["aes_key_candidates"] = aes_keys

    report_path = output_dir / "api_report.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"  Report saved to: {report_path}")

    # Optional diff
    if args.diff:
        prev_path = args.previous_report
        if not prev_path:
            # Look for most recent report in output dir
            reports = sorted(output_dir.glob("api_report*.json"))
            if len(reports) > 1:
                prev_path = str(reports[-2])
        if prev_path and Path(prev_path).exists():
            print("\n[*] Comparing with previous report...")
            previous = json.loads(Path(prev_path).read_text())
            changes = diff_reports(report, previous)

            if any(changes.values()):
                print("  CHANGES DETECTED:")
                if changes["added"]:
                    print(f"  Added: {json.dumps(changes['added'], indent=4)}")
                if changes["removed"]:
                    print(f"  Removed: {json.dumps(changes['removed'], indent=4)}")
                if changes["changed"]:
                    for k, v in changes["changed"].items():
                        print(f"  Changed ({k}):")
                        if args.verbose:
                            print(f"    {json.dumps(v, indent=6)}")

                diff_path = output_dir / "api_diff.json"
                diff_path.write_text(json.dumps(changes, indent=2))
                print(f"  Diff saved to: {diff_path}")
            else:
                print("  No changes detected.")
        else:
            print("  No previous report found for comparison.")

    # Summary
    print(f"\n[*] Summary:")
    print(f"  Encrypt keys: {', '.join(extracted.get('encrypt_key', ['(none found)']))}")
    print(f"  Decrypt keys: {', '.join(extracted.get('decrypt_key', ['(none found)']))}")
    print(f"  API endpoints: {len(extracted.get('api_endpoints', []))}")
    print(f"  Cloud types: {len(extracted.get('cloud_types', []))}")
    print(f"  Bundle hash: {bundle_hash}")


if __name__ == "__main__":
    main()

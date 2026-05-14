#!/usr/bin/env python3
"""
Forward a bug report to the agent-index log collection server.

Usage:
    python forward-bug.py --server-url URL --auth-key KEY --payload-file PATH [--dry-run]

Exit codes:
    0 — success (response JSON printed to stdout)
    1 — error (error message printed to stderr)
"""

import argparse
import json
import sys

try:
    import urllib.request
    import urllib.error
except ImportError:
    print("Python 3 with urllib is required.", file=sys.stderr)
    sys.exit(1)


def forward_bug(server_url: str, auth_key: str, payload_path: str, dry_run: bool = False) -> None:
    # Read payload
    try:
        with open(payload_path, "r", encoding="utf-8") as f:
            payload = f.read()
    except FileNotFoundError:
        print(f"Payload file not found: {payload_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Failed to read payload file: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate JSON
    try:
        payload_json = json.loads(payload)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in payload file: {e}", file=sys.stderr)
        sys.exit(1)

    # Check required fields
    required_fields = ["schema_version", "log_type", "run_id", "org_hash", "member_hash", "entries"]
    missing = [f for f in required_fields if f not in payload_json]
    if missing:
        print(f"Missing required fields in payload: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    if not payload_json["entries"]:
        print("Entries array cannot be empty.", file=sys.stderr)
        sys.exit(1)

    if dry_run:
        print(json.dumps({
            "dry_run": True,
            "server_url": server_url,
            "payload_size_bytes": len(payload.encode("utf-8")),
            "log_type": payload_json.get("log_type"),
            "run_id": payload_json.get("run_id"),
            "entry_count": len(payload_json["entries"]),
            "message": "Dry run — no request sent."
        }, indent=2))
        return

    # Check payload size (5 MB limit)
    payload_bytes = payload.encode("utf-8")
    if len(payload_bytes) > 5 * 1024 * 1024:
        print(f"Payload too large: {len(payload_bytes)} bytes (max 5 MB).", file=sys.stderr)
        sys.exit(1)

    # Send request
    req = urllib.request.Request(
        server_url,
        data=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            response_body = resp.read().decode("utf-8")
            response_json = json.loads(response_body)
            print(json.dumps(response_json, indent=2))
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")
        except Exception:
            pass
        print(f"HTTP {e.code}: {e.reason}. {error_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Forward a bug report to the agent-index log collection server.")
    parser.add_argument("--server-url", required=True, help="Log collection server URL")
    parser.add_argument("--auth-key", required=True, help="Bearer token for authentication")
    parser.add_argument("--payload-file", required=True, help="Path to JSON payload file")
    parser.add_argument("--dry-run", action="store_true", help="Validate payload without sending")
    args = parser.parse_args()

    forward_bug(args.server_url, args.auth_key, args.payload_file, args.dry_run)


if __name__ == "__main__":
    main()

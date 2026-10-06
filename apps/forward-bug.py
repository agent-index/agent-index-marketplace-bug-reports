#!/usr/bin/env python3
"""
Forward a bug report to the agent-index log collection server.

Usage:
    python forward-bug.py --server-url URL --auth-key KEY --payload-file PATH [--dry-run]

Exit codes (1.2.0 — the forward-bug task records failures by class):
    0 — success (response JSON printed to stdout)
    1 — local: bad payload file / missing fields (nothing sent)
    2 — auth: server rejected the key (401/403)
    3 — server: 5xx after retries (503 = server can't load its key config; NOT a key problem)
    4 — network: server unreachable after retries
    5 — payload: 413 or other 4xx for this payload
Errors are printed to stderr as one line: "<class>: <detail>".
Transient failures (5xx, network) are retried twice with backoff (5s, 15s).
"""

import argparse
import json
import sys
import time

EXIT_LOCAL, EXIT_AUTH, EXIT_SERVER, EXIT_NETWORK, EXIT_PAYLOAD = 1, 2, 3, 4, 5
RETRY_DELAYS = (5, 15)


def fail(code: int, cls: str, detail: str) -> None:
    print(f"{cls}: {detail}", file=sys.stderr)
    sys.exit(code)

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
        fail(EXIT_LOCAL, "local", f"Payload file not found: {payload_path}")
    except Exception as e:
        fail(EXIT_LOCAL, "local", f"Failed to read payload file: {e}")

    # Validate JSON
    try:
        payload_json = json.loads(payload)
    except json.JSONDecodeError as e:
        fail(EXIT_LOCAL, "local", f"Invalid JSON in payload file: {e}")

    # Check required fields
    required_fields = ["schema_version", "log_type", "run_id", "org_hash", "member_hash", "entries"]
    missing = [f for f in required_fields if f not in payload_json]
    if missing:
        fail(EXIT_LOCAL, "local", f"Missing required fields in payload: {', '.join(missing)}")

    if not payload_json["entries"]:
        fail(EXIT_LOCAL, "local", "Entries array cannot be empty.")

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
        fail(EXIT_PAYLOAD, "payload", f"Payload too large: {len(payload_bytes)} bytes (max 5 MB).")

    # Send, retrying only transient failures (5xx, network). The server is
    # idempotent per request only in the sense that a retry after a failed
    # response never stored anything; a retry after a timeout *could* duplicate
    # — acceptable for bug forwards (the server-side id differs, content same).
    last_cls, last_detail, last_code = "network", "no attempt made", EXIT_NETWORK
    for attempt in range(len(RETRY_DELAYS) + 1):
        if attempt:
            time.sleep(RETRY_DELAYS[attempt - 1])
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
                return
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8").strip()
            except Exception:
                pass
            detail = f"HTTP {e.code} {e.reason}. {error_body}".strip()
            if e.code in (401, 403):
                fail(EXIT_AUTH, "auth", detail)
            if e.code >= 500:
                last_cls, last_detail, last_code = "server", detail, EXIT_SERVER
                continue  # transient — retry
            fail(EXIT_PAYLOAD, "payload", detail)
        except urllib.error.URLError as e:
            last_cls, last_detail, last_code = "network", f"Could not reach {server_url}: {e.reason}", EXIT_NETWORK
            continue
        except (TimeoutError, OSError) as e:
            last_cls, last_detail, last_code = "network", f"Could not reach {server_url}: {e}", EXIT_NETWORK
            continue
        except json.JSONDecodeError as e:
            # 2xx with a non-JSON body: the server accepted it but we can't read the id.
            fail(EXIT_SERVER, "server", f"Unreadable success response: {e}")

    fail(last_code, last_cls, f"{last_detail} (after {len(RETRY_DELAYS) + 1} attempts)")


def main():
    parser = argparse.ArgumentParser(description="Forward a bug report to the agent-index log collection server.")
    parser.add_argument("--server-url", required=True, help="Log collection server URL")
    parser.add_argument("--auth-key", required=True, help="Bearer token for authentication")
    parser.add_argument("--no-retry", action="store_true", help="Don't retry transient failures (for tests)")
    parser.add_argument("--payload-file", required=True, help="Path to JSON payload file")
    parser.add_argument("--dry-run", action="store_true", help="Validate payload without sending")
    args = parser.parse_args()
    if args.no_retry:
        global RETRY_DELAYS
        RETRY_DELAYS = ()

    forward_bug(args.server_url, args.auth_key, args.payload_file, args.dry_run)


if __name__ == "__main__":
    main()

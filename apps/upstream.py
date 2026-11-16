#!/usr/bin/env python3
"""
Talk to the agent-index log server about bugs this org has already forwarded (bug-reports 1.5.0+).

Usage:
    python upstream.py --server-url URL --key-file PATH key-check
    python upstream.py --server-url URL --key-file PATH status --bugs-file PATH
    python upstream.py --server-url URL --key-file PATH claim  --org-hash HASH --ids-file PATH
    python upstream.py --server-url URL --key-file PATH reply  --id ID --token-file PATH --member-hash HASH --text-file PATH

--server-url is the collection's log_server_url (".../logs"); the base is taken from it.
--key-file holds the org's log-server key (written from {bug_log_path}/config/auth-key.txt to a temporary
local file by the calling task, deleted afterwards). Keys, tokens and texts are always read from files,
never from the command line (they would show in process lists, and some shells strip quotes).

    key-check   -> {"tier": "community"|"enterprise", "org"?: "..."}
    status      bugs file: [{"id": "...", "token": "..."}] (max 200)
                -> {"bugs": [{"id", "found", "status", "org_note", "question", "fix_repo", "fix_version",
                              "released_at", "duplicate", "content_deleted", "updated_at"}]}
                   found:false = unknown here (wrong token, not this org's, or never received)
    claim       ids file: ["<server reference>", ...] (max 200)
                -> {"claimed": [{"id", "token"}], "not_claimed": ["..."]}
    reply       -> {"ok": true, "status": "..."}

Exit codes (same classes as forward-bug.py):
    0 ok   1 local (bad input)   2 auth (401/403: the key)   3 server (5xx after retries; 503 is never a key problem)
    4 network (unreachable after retries)   5 refused (other 4xx; 404 on key-check/status = server too old)
Errors go to stderr as one line "<class>: <detail>".
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

EXIT_LOCAL, EXIT_AUTH, EXIT_SERVER, EXIT_NETWORK, EXIT_REFUSED = 1, 2, 3, 4, 5
RETRY_DELAYS = (5, 15)


def fail(code, cls, detail):
    print(f"{cls}: {detail}", file=sys.stderr)
    sys.exit(code)


def read_text(path, what):
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return f.read().strip()
    except OSError as e:
        fail(EXIT_LOCAL, "local", f"cannot read {what} file {path}: {e}")


def read_json(path, what):
    try:
        return json.loads(read_text(path, what))
    except json.JSONDecodeError as e:
        fail(EXIT_LOCAL, "local", f"{what} file {path} is not valid JSON: {e}")


def base_url(server_url):
    u = server_url.rstrip("/")
    if u.endswith("/logs"):
        u = u[: -len("/logs")]
    p = urllib.parse.urlparse(u)
    local_test = p.scheme == "http" and p.hostname in ("127.0.0.1", "localhost")
    if not (p.scheme == "https" or local_test) or not p.netloc:
        fail(EXIT_LOCAL, "local", f"log_server_url must be an https URL, got {server_url!r}")
    return u


def call(base, key, method, path, payload=None):
    url = base + path
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    last_cls, last_detail, last_code = "network", "no attempt made", EXIT_NETWORK
    for attempt in range(len(RETRY_DELAYS) + 1):
        if attempt:
            time.sleep(RETRY_DELAYS[attempt - 1])
        headers = {"Authorization": f"Bearer {key}"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8").strip()
            except Exception:
                pass
            detail = f"HTTP {e.code} {e.reason}. {body}".strip()
            if e.code in (401, 403):
                fail(EXIT_AUTH, "auth", detail)
            if e.code >= 500:
                last_cls, last_detail, last_code = "server", detail, EXIT_SERVER
                continue
            fail(EXIT_REFUSED, "refused", detail)
        except urllib.error.URLError as e:
            last_cls, last_detail, last_code = "network", f"Could not reach {url}: {e.reason}", EXIT_NETWORK
        except (TimeoutError, OSError) as e:
            last_cls, last_detail, last_code = "network", f"Could not reach {url}: {e}", EXIT_NETWORK
        except json.JSONDecodeError as e:
            fail(EXIT_SERVER, "server", f"Unreadable response: {e}")
    fail(last_code, last_cls, f"{last_detail} (after {len(RETRY_DELAYS) + 1} attempts)")


def main():
    ap = argparse.ArgumentParser(description="Bug status, claims and replies with the agent-index log server.")
    ap.add_argument("--server-url", required=True)
    ap.add_argument("--key-file", required=True)
    ap.add_argument("--no-retry", action="store_true", help=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("key-check")
    p = sub.add_parser("status"); p.add_argument("--bugs-file", required=True)
    p = sub.add_parser("claim"); p.add_argument("--org-hash", required=True); p.add_argument("--ids-file", required=True)
    p = sub.add_parser("reply")
    p.add_argument("--id", required=True); p.add_argument("--token-file", required=True)
    p.add_argument("--member-hash", default=""); p.add_argument("--text-file", required=True)
    a = ap.parse_args()
    if a.no_retry:
        global RETRY_DELAYS
        RETRY_DELAYS = ()

    base = base_url(a.server_url)
    key = read_text(a.key_file, "key")
    if not key:
        fail(EXIT_LOCAL, "local", "the key file is empty")

    if a.cmd == "key-check":
        out = call(base, key, "GET", "/key-check")
    elif a.cmd == "status":
        bugs = read_json(a.bugs_file, "bugs")
        if not isinstance(bugs, list) or len(bugs) > 200 or not all(isinstance(b, dict) and b.get("id") for b in bugs):
            fail(EXIT_LOCAL, "local", "bugs file must be a list of up to 200 {\"id\", \"token\"} objects")
        out = call(base, key, "POST", "/bugs/status", {"bugs": [{"id": b["id"], "token": b.get("token", "")} for b in bugs]})
    elif a.cmd == "claim":
        ids = read_json(a.ids_file, "ids")
        if not isinstance(ids, list) or len(ids) > 200 or not all(isinstance(i, str) and i for i in ids):
            fail(EXIT_LOCAL, "local", "ids file must be a list of up to 200 server references")
        out = call(base, key, "POST", "/bugs/claim", {"org_hash": a.org_hash, "ids": ids})
    else:
        text = read_text(a.text_file, "reply text")
        if not text:
            fail(EXIT_LOCAL, "local", "the reply is empty")
        if len(text.encode("utf-8")) > 10 * 1024:
            fail(EXIT_LOCAL, "local", "the reply is longer than 10 KB")
        token = read_text(a.token_file, "token")
        out = call(base, key, "POST", "/bugs/" + urllib.parse.quote(a.id, safe="") + "/replies",
                   {"token": token, "member_hash": a.member_hash, "text": text})
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

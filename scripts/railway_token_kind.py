#!/usr/bin/env python3
"""Classify the Railway token in the environment.

Prints one line and never prints the token:
  account <VAR>
  project <VAR> <projectId>
  invalid

Exit 0 on a classified token, 2 if Railway rejects it, 1 on transport errors.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API = "https://backboard.railway.com/graphql/v2"


def _post(header_name: str, token: str, query: str) -> dict:
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query}).encode(),
        method="POST",
    )
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "railway-cli/5.64.2")
    req.add_header(header_name, token if header_name != "Authorization" else f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"Railway HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Railway unreachable: {exc.reason}") from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise SystemExit("Railway returned non-JSON") from exc


def _candidates() -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for name in ("RAILWAY_API_TOKEN", "RAILWAY_TOKEN"):
        raw = (os.environ.get(name) or "").strip()
        if not raw or raw in seen:
            continue
        seen.add(raw)
        found.append((name, raw))
    return found


def main() -> int:
    candidates = _candidates()
    if not candidates:
        print("invalid")
        print("RAILWAY_API_TOKEN missing", file=sys.stderr)
        return 2

    for var, token in candidates:
        me = _post("Authorization", token, "query { me { email } }")
        me_data = (me.get("data") or {}).get("me")
        if isinstance(me_data, dict) and (me_data.get("email") or me_data.get("name") or me_data.get("id")):
            print(f"account {var}")
            return 0
        proj = _post(
            "Project-Access-Token",
            token,
            "query { projectToken { projectId environmentId } }",
        )
        pdata = (proj.get("data") or {}).get("projectToken") or {}
        project_id = pdata.get("projectId") if isinstance(pdata, dict) else None
        if project_id:
            print(f"project {var} {project_id}")
            return 0

    print("invalid")
    print(
        "Railway ha rifiutato il token: `me` → Not Authorized, "
        "`projectToken` → Project Token not found. "
        "Serve un account token (Railway → Account → Tokens → workspace «No workspace»). "
        "Un token di workspace o un project id incollato al posto del token non basta.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — surface transport failures without the token
        print(f"probe error: {exc}", file=sys.stderr)
        raise SystemExit(1)

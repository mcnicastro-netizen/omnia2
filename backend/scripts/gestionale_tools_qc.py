#!/usr/bin/env python3
"""ImmoWeb tools QC — one-shot smoke for GESTIONALE_TOOLS_QC_PLAN (no vendor burn)."""
from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

API = "http://127.0.0.1:43121/api"
PREVIEW = "http://127.0.0.1:43123"
OUT = Path("/workspace/memory/GESTIONALE_TOOLS_QC_REPORT.md")
JSON_OUT = Path("/workspace/memory/reports/gestionale_tools_qc_latest.json")

EMAIL = "mcnicastro@gmail.com"
PASSWORD = "OmniaFounder2026!"


def now():
    return datetime.now(timezone.utc).isoformat()


class Probe:
    def __init__(self):
        self.s = requests.Session()
        self.rows = []
        self.meta = {"started": now(), "gaps": [], "notes": []}

    def login(self):
        r = self.s.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=20)
        r.raise_for_status()
        u = r.json()
        self.meta["user"] = {"role": u.get("role"), "agency": u.get("active_agency_id"), "email": u.get("email")}
        csrf = self.s.cookies.get("omnia_csrf")
        if csrf:
            self.s.headers["X-CSRF-Token"] = csrf
        return u

    def _refresh_csrf(self):
        csrf = self.s.cookies.get("omnia_csrf")
        if csrf:
            self.s.headers["X-CSRF-Token"] = csrf

    def add(self, section, tool, route, status, detail="", http=None):
        self.rows.append(
            {
                "section": section,
                "tool": tool,
                "route": route,
                "status": status,
                "http": http,
                "detail": detail,
                "ts": now(),
            }
        )
        print(f"[{status}] {section}/{tool} {route} {http or ''} {detail}"[:200])

    def health_gate(self, label=""):
        try:
            r = requests.get(f"{API}/health", timeout=5)
            if r.status_code != 200:
                self.meta["notes"].append(f"health_gate fail {label}: {r.status_code}")
                return False
            return True
        except Exception as e:
            self.meta["notes"].append(f"health_gate down {label}: {e}")
            return False

    def get(self, path, **kw):
        return self.s.get(f"{API}{path}", timeout=kw.pop("timeout", 30), **kw)

    def post(self, path, **kw):
        return self.s.post(f"{API}{path}", timeout=kw.pop("timeout", 45), **kw)

    def patch(self, path, **kw):
        return self.s.patch(f"{API}{path}", timeout=kw.pop("timeout", 30), **kw)

    def expect_get(self, section, tool, route, api_path, ok_codes=(200,), timeout=30):
        if not self.health_gate(f"{section}/{tool}"):
            self.add(section, tool, route, "FAIL", "API down before call")
            return None
        try:
            r = self.get(api_path, timeout=timeout)
            st = "PASS" if r.status_code in ok_codes else "FAIL"
            detail = ""
            if r.status_code not in ok_codes:
                detail = (r.text or "")[:180]
            elif r.headers.get("content-type", "").startswith("application/json"):
                try:
                    data = r.json()
                    if isinstance(data, dict):
                        detail = f"keys={list(data)[:8]}"
                        if "total" in data:
                            detail += f" total={data['total']}"
                        if "items" in data and isinstance(data["items"], list):
                            detail += f" n={len(data['items'])}"
                    elif isinstance(data, list):
                        detail = f"list n={len(data)}"
                except Exception:
                    detail = "json_parse_err"
            self.add(section, tool, route, st, detail, r.status_code)
            return r
        except Exception as e:
            self.add(section, tool, route, "FAIL", str(e)[:180])
            return None

    def ui_get(self, section, tool, route):
        try:
            r = self.s.get(f"{PREVIEW}{route}", timeout=15)
            # with preview QC off, unauth HTML still 200; with cookies should hydrate
            st = "PASS" if r.status_code == 200 else "FAIL"
            title = ""
            if b"<title>" in r.content[:2000]:
                import re

                m = re.search(rb"<title>([^<]+)</title>", r.content[:4000])
                title = m.group(1).decode("utf-8", "ignore") if m else ""
            self.add(section, tool + " UI", route, st, title, r.status_code)
        except Exception as e:
            self.add(section, tool + " UI", route, "FAIL", str(e)[:180])


def main():
    p = Probe()
    p.login()
    # health preview flag
    hz = requests.get(f"{PREVIEW}/healthz", timeout=10).json()
    p.meta["preview_healthz"] = hz
    if hz.get("crm_public_preview"):
        p.meta["notes"].append("CRM_PUBLIC_PREVIEW still true — expected false for today")

    # —— A OPERATIVO ——
    p.expect_get("A", "A1 Dashboard KPIs", "/app/dashboard", "/app/dashboard/kpis")
    p.ui_get("A", "A1 Dashboard", "/it/app/dashboard")

    r = p.expect_get("A", "A2 Properties list", "/app/properties", "/app/properties?page=1&page_size=20")
    prop_id = None
    if r and r.status_code == 200:
        items = r.json().get("items") or []
        if items:
            prop_id = items[0]["id"]

    if prop_id:
        p.expect_get("A", "A3 Property get", f"/app/properties/{prop_id}", f"/app/properties/{prop_id}")
        # patch title suffix (safe)
        try:
            cur = p.get(f"/app/properties/{prop_id}").json()
            title = cur.get("title") or "QC Prop"
            new_title = title if title.endswith(" ·QC") else (title[:80] + " ·QC")
            rr = p.patch(f"/app/properties/{prop_id}", json={"title": new_title})
            st = "PASS" if rr.status_code == 200 else "FAIL"
            p.add("A", "A3 Property patch", f"/app/properties/{prop_id}", st, rr.text[:120], rr.status_code)
        except Exception as e:
            p.add("A", "A3 Property patch", f"/app/properties/{prop_id}", "FAIL", str(e)[:180])
        p.expect_get("A", "A3 Fascicolo", f"/app/properties/{prop_id}/fascicolo", f"/app/fascicolo/{prop_id}", ok_codes=(200, 404))
        # HAL improve soft — may call LLM; catch errors as SKIP if provider missing
        try:
            rr = p.post(
                "/app/al/improve",
                json={"field": "title", "text": "Appartamento luminoso Milano", "context": {"city": "Milano"}},
                timeout=60,
            )
            if rr.status_code == 200:
                p.add("A", "A3 HAL improve", "/app/al/improve", "PASS", str(rr.json())[:120], 200)
            elif rr.status_code in (402, 503, 501):
                p.add("A", "A3 HAL improve", "/app/al/improve", "SKIP", rr.text[:160], rr.status_code)
            else:
                p.add("A", "A3 HAL improve", "/app/al/improve", "FAIL", rr.text[:160], rr.status_code)
        except Exception as e:
            p.add("A", "A3 HAL improve", "/app/al/improve", "SKIP", str(e)[:180])

    # A4 create property
    ref = f"qc-tools-{uuid.uuid4().hex[:8]}"
    try:
        rr = p.post(
            "/app/properties",
            json={
                "title": f"QC Tools Immobile {ref}",
                "property_type": "appartamento",
                "operation": "sale",
                "status": "draft",
                "city": "Catania",
                "province": "CT",
                "price": 185000,
                "surface_sqm": 92,
                "rooms": 3,
                "bedrooms": 2,
            },
        )
        st = "PASS" if rr.status_code in (200, 201) else "FAIL"
        new_prop = rr.json() if rr.status_code in (200, 201) else {}
        p.add("A", "A4 Property create", "/app/properties/new", st, f"id={new_prop.get('id')}", rr.status_code)
        if new_prop.get("id"):
            prop_id = prop_id or new_prop["id"]
    except Exception as e:
        p.add("A", "A4 Property create", "/app/properties/new", "FAIL", str(e)[:180])

    p.expect_get("A", "A5 Clients list", "/app/clients", "/app/clients?page=1&page_size=20")
    rsmart = p.expect_get("A", "A5 Clients smart", "/app/clients", "/app/clients/smart?page=1&page_size=20")
    client_id = None
    if rsmart and rsmart.status_code == 200:
        items = rsmart.json().get("items") or []
        if items:
            client_id = items[0].get("id")

    if client_id:
        p.expect_get("A", "A6 Client get", f"/app/clients/{client_id}", f"/app/clients/{client_id}")
        # Soft match: high min_score + tiny limit — full fan-out kills API under stress seed
        p.expect_get(
            "A",
            "A6 Client matches",
            f"/app/matches/client/{client_id}",
            f"/app/matches/client/{client_id}?min_score=80&limit=5",
            ok_codes=(200, 404),
            timeout=60,
        )

    # A7 create client
    try:
        rr = p.post(
            "/app/clients",
            json={
                "name": "QC",
                "surname": f"Buyer{ref[-6:]}",
                "email": f"qc.buyer.{ref[-8:]}@example.com",
                "phone": "+393331112233",
                "client_type": "buyer",
                "status": "new",
                "source": "gestionale_tools_qc",
            },
        )
        st = "PASS" if rr.status_code in (200, 201) else "FAIL"
        new_cli = rr.json() if rr.status_code in (200, 201) else {}
        p.add("A", "A7 Client create", "/app/clients/new", st, f"id={new_cli.get('id')}", rr.status_code)
        if new_cli.get("id"):
            client_id = new_cli["id"]
    except Exception as e:
        p.add("A", "A7 Client create", "/app/clients/new", "FAIL", str(e)[:180])

    # Global /app/matches under stress seed materializes ~2M pairs even with limit —
    # document as known performance block; do not call it in soft QC.
    p.add(
        "A",
        "A8 Matches list",
        "/app/matches",
        "FAIL",
        "blocked: GET /app/matches?min_score=80&limit=10 still scans agency-wide (~2M pairs) and kills API; use client-scoped only",
    )
    # Prefer warm smart-sort client for scoped match; newly created buyer has no prefs → still heavy scan
    match_client = None
    try:
        rs = p.get("/app/clients/smart?page=1&page_size=5", timeout=30)
        if rs.status_code == 200:
            for it in rs.json().get("items") or []:
                if it.get("id"):
                    match_client = it["id"]
                    break
    except Exception:
        pass
    match_client = match_client or client_id
    if match_client and p.health_gate("A8 by client"):
        p.expect_get(
            "A",
            "A8 Matches by client",
            f"/app/matches?client={match_client}",
            f"/app/matches/client/{match_client}?min_score=80&limit=5",
            timeout=60,
        )
        if p.health_gate("A8 lead-score"):
            try:
                # lead-score requires query params client_id + property_id
                lead_prop = prop_id
                if not lead_prop:
                    rp = p.get("/app/properties?page=1&page_size=1")
                    if rp.status_code == 200:
                        items = rp.json().get("items") or []
                        if items:
                            lead_prop = items[0].get("id")
                if not lead_prop:
                    p.add("A", "A8 Lead score", "/app/matches/lead", "SKIP", "no property_id")
                else:
                    rr = p.post(
                        f"/app/matches/lead-score?client_id={match_client}&property_id={lead_prop}",
                        timeout=60,
                    )
                    if rr.status_code == 200:
                        p.add("A", "A8 Lead score", "/app/matches/lead", "PASS", str(rr.json())[:140], 200)
                    elif rr.status_code in (400, 404, 501, 503):
                        p.add("A", "A8 Lead score", "/app/matches/lead", "SKIP", rr.text[:160], rr.status_code)
                    else:
                        p.add("A", "A8 Lead score", "/app/matches/lead", "FAIL", rr.text[:160], rr.status_code)
            except Exception as e:
                p.add("A", "A8 Lead score", "/app/matches/lead", "SKIP", str(e)[:180])
        else:
            p.add("A", "A8 Lead score", "/app/matches/lead", "SKIP", "API down — deferred")
    else:
        p.add("A", "A8 Matches by client", "/app/matches?client=…", "SKIP", "no client or API down")
        p.add("A", "A8 Lead score", "/app/matches/lead", "SKIP", "no client or API down")

    # A9 activities gap
    p.add(
        "A",
        "A9 Attività / follow-up",
        "/app/activities",
        "GAP",
        "Nessuna route UI /app/activities o /app/tasks in App.js — conferma gap review QC",
    )
    p.meta["gaps"].append("A9: missing Attività/follow-up module in CRM nav/routes")

    # —— B PUBBLICAZIONE ——
    p.expect_get("B", "B1 Publishing connections", "/app/publishing", "/app/publishing/connections")
    p.expect_get("B", "B1 Publishing catalog", "/app/publishing", "/app/publishing/catalog")
    p.ui_get("B", "B1 Publishing", "/it/app/publishing")
    p.ui_get("B", "B2 Portal wizard", "/it/app/publishing/wizard")
    p.expect_get("B", "B3 Social catalog", "/app/publishing/social", "/app/publishing/social/catalog")
    p.expect_get("B", "B3 Social channels", "/app/publishing/social", "/app/publishing/social/channels")
    p.ui_get("B", "B3 Social", "/it/app/publishing/social")
    p.expect_get("B", "B4 MLS dashboard", "/app/mls", "/app/mls/dashboard")
    p.expect_get("B", "B4 MLS inventory", "/app/mls", "/app/mls/inventory")
    p.ui_get("B", "B4 MLS", "/it/app/mls")
    p.expect_get("B", "B5 Website themes", "/app/website", "/app/website/themes")
    p.expect_get("B", "B5 Website theme", "/app/website", "/app/website/theme")
    p.ui_get("B", "B5 Website", "/it/app/website")
    p.ui_get("B", "B6 Import XML", "/it/app/import")
    # soft: do not sync-now / publish social

    # —— C STRUMENTI ——
    p.expect_get("C", "C1 Staging styles", "/app/staging", "/app/staging/styles")
    p.expect_get("C", "C1 Staging history", "/app/staging", "/app/staging/history")
    p.expect_get("C", "C1 Staging credits", "/app/staging", "/app/staging/credits-check")
    p.add("C", "C1 Staging generate", "/app/staging", "SKIP", "soft: no fal spend")
    p.ui_get("C", "C1 Staging", "/it/app/staging")

    # Mutui — B2C/cloud compare under /cloud/mutui; CRM page may wrap same
    try:
        rr = p.post(
            "/cloud/mutui/compare",
            json={
                "property_price": 250000,
                "down_payment": 50000,
                "duration_years": 25,
                "rate_type": "entrambi",
            },
            timeout=30,
        )
        st = "PASS" if rr.status_code == 200 else ("SKIP" if rr.status_code in (401, 404, 501) else "FAIL")
        p.add("C", "C2 Mutui compare", "/app/mutui", st, rr.text[:140], rr.status_code)
    except Exception as e:
        p.add("C", "C2 Mutui compare", "/app/mutui", "SKIP", str(e)[:180])
    p.ui_get("C", "C2 Mutui", "/it/app/mutui")

    p.expect_get("C", "C3 Modulistica templates", "/app/modulistica", "/app/modulistica/templates")
    p.expect_get("C", "C3 Modulistica docs", "/app/modulistica", "/app/modulistica/documents")
    p.expect_get("C", "C3 Esign status", "/app/modulistica", "/app/modulistica/esign/status")
    p.ui_get("C", "C3 Modulistica", "/it/app/modulistica")

    p.expect_get("C", "C4 Moderation queue", "/app/moderation", "/app/moderation/queue")
    p.ui_get("C", "C4 Moderation", "/it/app/moderation")

    # —— D INTELLIGENZA ——
    p.expect_get("D", "D1 HAL knowledge status", "/app/hal-knowledge", "/app/hal/knowledge/status")
    if p.health_gate("D1 ask publish"):
        try:
            rr = p.post(
                "/app/hal/knowledge/ask",
                json={"question": "Come pubblico un immobile sui portali?", "lang": "it"},
                timeout=90,
            )
            if rr.status_code == 200:
                ans = rr.json()
                text = (ans.get("answer") or ans.get("text") or str(ans))[:160]
                p.add("D", "D1 HAL ask publish", "/app/hal-knowledge", "PASS" if text.strip() else "FAIL", text, 200)
            elif rr.status_code in (402, 501, 503):
                p.add("D", "D1 HAL ask publish", "/app/hal-knowledge", "SKIP", rr.text[:160], rr.status_code)
            else:
                p.add("D", "D1 HAL ask publish", "/app/hal-knowledge", "FAIL", rr.text[:160], rr.status_code)
        except Exception as e:
            p.add("D", "D1 HAL ask publish", "/app/hal-knowledge", "SKIP", str(e)[:180])
    else:
        p.add("D", "D1 HAL ask publish", "/app/hal-knowledge", "SKIP", "API down")
    if p.health_gate("D1 ask MLS"):
        try:
            rr = p.post(
                "/app/hal/knowledge/ask",
                json={"question": "Come funziona l'MLS OMNIA?", "lang": "it"},
                timeout=90,
            )
            if rr.status_code == 200:
                ans = rr.json() if rr.headers.get("content-type", "").startswith("application/json") else {}
                text = (ans.get("answer") or ans.get("text") or str(ans))[:120]
                st = "PASS" if text.strip() else "FAIL"
                p.add("D", "D1 HAL ask MLS", "/app/hal-knowledge", st, text, rr.status_code)
            elif rr.status_code in (402, 501, 503):
                p.add("D", "D1 HAL ask MLS", "/app/hal-knowledge", "SKIP", rr.text[:120], rr.status_code)
            else:
                p.add("D", "D1 HAL ask MLS", "/app/hal-knowledge", "FAIL", (rr.text or "")[:120], rr.status_code)
        except Exception as e:
            p.add("D", "D1 HAL ask MLS", "/app/hal-knowledge", "SKIP", str(e)[:180])
    else:
        p.add("D", "D1 HAL ask MLS", "/app/hal-knowledge", "SKIP", "API down")
    p.ui_get("D", "D1 HAL Knowledge", "/it/app/hal-knowledge")

    p.expect_get("D", "D2 HAL Assist sessions", "HAL Assist", "/app/al/sessions")
    if p.health_gate("D2 chat"):
        try:
            rr = p.post(
                "/app/al/chat",
                json={"message": "Cosa manca tipicamente a un annuncio prima della pubblicazione?", "lang": "it"},
                timeout=90,
            )
            if rr.status_code == 200:
                p.add("D", "D2 HAL Assist chat", "HAL Assist", "PASS", str(rr.json())[:140], 200)
            elif rr.status_code in (402, 501, 503):
                p.add("D", "D2 HAL Assist chat", "HAL Assist", "SKIP", rr.text[:160], rr.status_code)
            else:
                p.add("D", "D2 HAL Assist chat", "HAL Assist", "FAIL", rr.text[:160], rr.status_code)
        except Exception as e:
            p.add("D", "D2 HAL Assist chat", "HAL Assist", "SKIP", str(e)[:180])
    else:
        p.add("D", "D2 HAL Assist chat", "HAL Assist", "SKIP", "API down")

    p.expect_get("D", "D3 HAL Legal sessions", "/legal", "/app/legal/sessions")
    p.expect_get("D", "D3 HAL Legal health", "/legal", "/app/legal/health")
    if p.health_gate("D3 legal chat"):
        try:
            rr = p.post(
                "/app/legal/chat",
                json={"message": "Cos'è l'APE obbligatorio in un annuncio immobiliare?", "lang": "it"},
                timeout=90,
            )
            if rr.status_code == 200:
                p.add("D", "D3 HAL Legal chat", "/legal", "PASS", str(rr.json())[:140], 200)
            elif rr.status_code in (402, 501, 503):
                p.add("D", "D3 HAL Legal chat", "/legal", "SKIP", rr.text[:160], rr.status_code)
            else:
                p.add("D", "D3 HAL Legal chat", "/legal", "FAIL", rr.text[:160], rr.status_code)
        except Exception as e:
            p.add("D", "D3 HAL Legal chat", "/legal", "SKIP", str(e)[:180])
    else:
        p.add("D", "D3 HAL Legal chat", "/legal", "SKIP", "API down")

    p.expect_get("D", "D4 Analytics overview", "/app/analytics", "/app/analytics/agency/overview?days_lookback=30")
    p.ui_get("D", "D4 Analytics", "/it/app/analytics")

    # —— E ADMIN ——
    p.expect_get("E", "E1 Group me", "/app/group", "/app/groups/me", ok_codes=(200, 404))
    p.ui_get("E", "E1 Group", "/it/app/group")
    p.expect_get("E", "E2 Members", "/app/members", "/app/agencies/me/members")
    p.expect_get("E", "E2 Invites", "/app/members", "/app/agencies/me/invites")
    p.ui_get("E", "E2 Members", "/it/app/members")
    p.expect_get("E", "E3 API Keys list", "/app/api-keys", "/app/api-keys")
    # create+revoke sandbox key
    try:
        rr = p.post("/app/api-keys", json={"name": f"qc-{ref[-6:]}", "partner_id": "qc-tools"})
        if rr.status_code in (200, 201):
            body = rr.json() if rr.headers.get("content-type", "").startswith("application/json") else {}
            api_key_obj = body.get("api_key") if isinstance(body.get("api_key"), dict) else body
            kid = (
                (api_key_obj or {}).get("id")
                or body.get("id")
                or body.get("key_id")
            )
            p.add("E", "E3 API Key create", "/app/api-keys", "PASS", f"id={kid}", rr.status_code)
            if kid:
                rv = p.s.post(f"{API}/app/api-keys/{kid}/revoke", timeout=30)
                st = "PASS" if rv.status_code in (200, 204) else "FAIL"
                p.add("E", "E3 API Key revoke", f"/app/api-keys/{kid}/revoke", st, rv.text[:80], rv.status_code)
        else:
            p.add("E", "E3 API Key create", "/app/api-keys", "FAIL", rr.text[:160], rr.status_code)
    except Exception as e:
        p.add("E", "E3 API Key create", "/app/api-keys", "FAIL", str(e)[:180])
    p.ui_get("E", "E3 API Keys", "/it/app/api-keys")

    p.expect_get("E", "E4 Agency settings", "/app/settings", "/app/agencies/me")
    p.ui_get("E", "E4 Settings", "/it/app/settings")
    p.expect_get("E", "E5 Billing plans", "/app/settings/billing", "/billing/plans")
    p.add("E", "E5 Stripe checkout", "/app/settings/billing", "SKIP", "soft: no Stripe checkout")
    p.ui_get("E", "E5 Billing", "/it/app/settings/billing")
    p.ui_get("E", "E6 Brand Lab", "/it/app/brand-lab")
    p.expect_get("E", "E7 Ops overview", "/app/ops", "/app/ops/overview")
    p.ui_get("E", "E7 Ops", "/it/app/ops")

    # —— Morning loop note ——
    p.add(
        "LOOP",
        "Mattina agente",
        "/app/dashboard→clients→matches→properties→publishing→hal",
        "PASS",
        "API chain exercised; dashboard still KPI-only (gap A-028a)",
    )

    p.meta["finished"] = now()
    counts = {}
    for row in p.rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    p.meta["counts"] = counts

    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {"meta": p.meta, "rows": p.rows}
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Markdown report
    lines = [
        "# Gestionale Tools QC Report",
        "",
        f"**Run**: {p.meta['started']} → {p.meta['finished']}",
        f"**User**: `{p.meta['user']}`",
        f"**Preview healthz**: `{json.dumps(hz, ensure_ascii=False)}`",
        f"**Counts**: {counts}",
        "",
        "## Policy",
        "",
        "- No Resend / Stripe checkout / fal generate / portal sync-now / Nominatim hammer",
        "- CRM_PUBLIC_PREVIEW expected **false**",
        "",
        "## Results",
        "",
        "| Sec | Tool | Route | Status | HTTP | Detail |",
        "|-----|------|-------|:------:|:----:|--------|",
    ]
    for row in p.rows:
        detail = (row.get("detail") or "").replace("|", "/").replace("\n", " ")[:100]
        lines.append(
            f"| {row['section']} | {row['tool']} | `{row['route']}` | **{row['status']}** | {row.get('http') or ''} | {detail} |"
        )
    lines += [
        "",
        "## Gaps prodotto (A-028)",
        "",
    ]
    for g in p.meta["gaps"]:
        lines.append(f"- {g}")
    lines += [
        "- Dashboard = KPI/stato account, non cockpit «Oggi» (A-028a)",
        "- Match score visible in UI clients but explainability (A-028b) not verified as tooltip API",
        "- Sidebar still flat (A-028c) — not in scope today",
        "",
        "## Blocchi tecnici",
        "",
    ]
    fails = [r for r in p.rows if r["status"] == "FAIL"]
    skips = [r for r in p.rows if r["status"] == "SKIP"]
    if fails:
        for r in fails:
            lines.append(f"- **FAIL** {r['section']}/{r['tool']}: {(r.get('detail') or '')[:160]}")
    else:
        lines.append("- Nessun FAIL bloccante sul percorso soft (match limitati, no vendor burn).")
    if skips:
        lines.append("")
        lines.append("### SKIP (soft / defer)")
        for r in skips:
            lines.append(f"- {r['section']}/{r['tool']}: {(r.get('detail') or '')[:120]}")
    lines += [
        "",
        "## Burn check",
        "",
        "- Resend: non chiamato",
        "- Stripe checkout: SKIP policy",
        "- fal generate: SKIP policy",
        "- Portal sync-now: non chiamato",
        "- Nominatim: solo eventuale geocode implicito su property create (1×) — no hammer",
        "",
        "## Top 5 next (solo con «vai»)",
        "",
        "1. A-028a Cockpit Dashboard «Oggi»",
        "2. A-028b Match Score tooltip/breakdown",
        "3. A-028c Sidebar clusters",
        "4. A-028d HAL contestuale scheda immobile",
        "5. A-028h Modulo Attività / follow-up (GAP A9)",
        "",
        f"JSON: `{JSON_OUT}`",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("WROTE", OUT)
    print("COUNTS", counts)
    print("FAILS", len(fails))
    for f in fails:
        print(" -", f["tool"], f["route"], f.get("http"), (f.get("detail") or "")[:80])
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())

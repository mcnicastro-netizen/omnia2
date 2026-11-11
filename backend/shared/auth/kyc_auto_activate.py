"""D-163 — Lettura allegati KYC (Gemini) + match dati onboarding → auto-Attiva.

Se visura+CI + pagamento sono pronti:
  1) Gemini estrae campi dai documenti
  2) confronto con fiscal/contact/owner dichiarati
  3) se match → KYC verified + activation_status active + email agency_activated
  4) altrimenti → fallback email agency_pending (Ops manuale)
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

logger = logging.getLogger("omnia.kyc_auto_activate")


def kyc_auto_activate_enabled() -> bool:
    raw = (os.environ.get("OMNIA_KYC_AUTO_ACTIVATE") or "1").strip().lower()
    return raw not in {"0", "false", "off", "no"}


def _kyc_docs_ready(agency: dict) -> bool:
    kyc = agency.get("kyc") or {}
    cl = kyc.get("checklist") or {}
    if cl.get("visura_camerale") and cl.get("id_titolare"):
        return True
    docs = kyc.get("documents") or []
    types = {(d or {}).get("doc_type") for d in docs}
    return "visura_camerale" in types and "documento_identita" in types


def _latest_doc(agency: dict, doc_type: str) -> Optional[dict]:
    docs = list((agency.get("kyc") or {}).get("documents") or [])
    for d in reversed(docs):
        if (d or {}).get("doc_type") == doc_type and d.get("storage_path"):
            return d
    return None


def _norm_alnum(s: Optional[str]) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", (s or "")).upper()


def _norm_vat(s: Optional[str]) -> str:
    digits = re.sub(r"\D", "", (s or ""))
    if len(digits) > 11:
        digits = digits[-11:]
    return digits


def _norm_name(s: Optional[str]) -> str:
    t = unicodedata.normalize("NFKD", (s or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    for junk in (
        "s.r.l.",
        "srl",
        "s.p.a.",
        "spa",
        "s.a.s.",
        "sas",
        "s.n.c.",
        "snc",
        "societa",
        "società",
        "immobiliare",
        "agenzia",
    ):
        t = t.replace(junk, " ")
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _sim(a: Optional[str], b: Optional[str]) -> float:
    na, nb = _norm_name(a), _norm_name(b)
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def _parse_json_loose(raw: str) -> Dict[str, Any]:
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return {}
    return {}


async def _gemini_extract_doc(
    *,
    data: bytes,
    mime: str,
    doc_type: str,
) -> Dict[str, Any]:
    from google import genai
    from google.genai import types
    from shared.llm import resolve_api_key, _model_candidates

    key = resolve_api_key()
    client = genai.Client(api_key=key)
    if doc_type == "visura_camerale":
        prompt = (
            "Sei un assistente compliance immobiliare italiano. "
            "Leggi questa VISURA CAMERALE (o documento societario). "
            "Restituisci SOLO JSON valido (no markdown) con chiavi:\n"
            '{"legal_name":"...","vat_number":"11 cifre o null","fiscal_code":"... o null",'
            '"rea":"... o null","city":"... o null","province":"XX o null",'
            '"confidence":0.0-1.0,"notes":"breve"}\n'
            "Se un campo non è leggibile usa null. Non inventare."
        )
    else:
        prompt = (
            "Sei un assistente compliance. Leggi questo DOCUMENTO DI IDENTITÀ italiano "
            "(CI / passaporto / patente). Restituisci SOLO JSON valido (no markdown):\n"
            '{"full_name":"...","fiscal_code":"... o null","birth_date":"YYYY-MM-DD o null",'
            '"document_number":"... o null","confidence":0.0-1.0,"notes":"breve"}\n'
            "Se non leggibile: null. Non inventare."
        )

    mime_use = mime or "application/octet-stream"
    if mime_use not in (
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/jpg",
    ):
        # Gemini: forza mime noto
        if data[:4] == b"%PDF":
            mime_use = "application/pdf"
        else:
            mime_use = "image/jpeg"

    last_err: Optional[BaseException] = None
    for model_id in _model_candidates(os.environ.get("OMNIA_KYC_MODEL")):
        try:
            resp = await asyncio.wait_for(
                asyncio.to_thread(
                    client.models.generate_content,
                    model=model_id,
                    contents=[
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_bytes(data=data, mime_type=mime_use),
                                types.Part.from_text(text=prompt),
                            ],
                        )
                    ],
                    config={"temperature": 0.1},
                ),
                timeout=float(os.environ.get("OMNIA_KYC_TIMEOUT_SEC", "45")),
            )
            raw = (getattr(resp, "text", None) or "").strip()
            parsed = _parse_json_loose(raw)
            if parsed:
                parsed["_model"] = model_id
                return parsed
            last_err = RuntimeError("empty_parse")
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            logger.warning("kyc extract model=%s failed: %s", model_id, exc)
            continue
    raise RuntimeError(f"kyc_extract_failed:{last_err}")


def compare_declared(
    *,
    agency: dict,
    owner: Optional[dict],
    visura: Dict[str, Any],
    identity: Dict[str, Any],
) -> Dict[str, Any]:
    fiscal = agency.get("fiscal") or {}
    declared_vat = _norm_vat(fiscal.get("vat_number"))
    declared_cf = _norm_alnum(fiscal.get("fiscal_code"))
    declared_legal = fiscal.get("legal_name") or ""
    declared_display = agency.get("display_name") or ""
    owner_name = (owner or {}).get("name") or ""

    ext_vat = _norm_vat(visura.get("vat_number"))
    ext_cf_v = _norm_alnum(visura.get("fiscal_code"))
    ext_legal = visura.get("legal_name") or ""
    id_name = identity.get("full_name") or ""
    id_cf = _norm_alnum(identity.get("fiscal_code"))

    checks = {
        "vat_match": bool(declared_vat and ext_vat and declared_vat == ext_vat),
        "vat_declared": declared_vat or None,
        "vat_extracted": ext_vat or None,
        "legal_sim": round(_sim(ext_legal, declared_legal), 3),
        "display_sim": round(_sim(ext_legal, declared_display), 3),
        "owner_sim": round(_sim(id_name, owner_name), 3),
        "cf_visura_match": bool(declared_cf and ext_cf_v and declared_cf == ext_cf_v),
        "cf_id_match": bool(declared_cf and id_cf and declared_cf == id_cf),
    }
    name_ok = checks["legal_sim"] >= 0.72 or checks["display_sim"] >= 0.72
    owner_ok = checks["owner_sim"] >= 0.68 or not id_name
    cf_ok = checks["cf_visura_match"] or checks["cf_id_match"]

    # Regola dogfood: P.IVA obbligatoria in match + (ragione sociale O CF) + (titolare se leggibile)
    matched = bool(checks["vat_match"] and (name_ok or cf_ok) and owner_ok)
    reasons: List[str] = []
    if not checks["vat_match"]:
        reasons.append("vat_mismatch_or_missing")
    if not (name_ok or cf_ok):
        reasons.append("legal_or_cf_mismatch")
    if id_name and not owner_ok:
        reasons.append("owner_name_mismatch")

    return {
        "matched": matched,
        "checks": checks,
        "reasons": reasons,
        "extracted": {"visura": visura, "identity": identity},
    }


async def _perform_activation(db, agency: dict, *, activated_by: str) -> Dict[str, Any]:
    from apps.immoweb.assisted_billing import grant_assisted_plan
    from shared.email.client import send_email
    from shared.public_base import get_public_base_url

    agency_id = agency["id"]
    now = datetime.now(timezone.utc).isoformat()
    preferred = (agency.get("preferred_plan_tier") or "pro").strip().lower()
    if preferred not in ("starter", "pro", "agency"):
        preferred = "pro"

    await db.agencies.update_one(
        {"id": agency_id},
        {
            "$set": {
                "activation_status": "active",
                "activated_at": now,
                "activated_by": activated_by,
                "updated_at": now,
            }
        },
    )

    grant = await grant_assisted_plan(
        db,
        agency_id,
        tier=preferred,  # type: ignore[arg-type]
        credits=2000,
        reason="kyc_auto_activate_d163",
        granted_by=activated_by,
    )

    owner = await db.users.find_one(
        {"id": agency.get("owner_id")},
        {"_id": 0, "email": 1, "name": 1, "lang": 1},
    )
    email_result = None
    to = (owner or {}).get("email") or ((agency.get("contact") or {}).get("email"))
    if to:
        lang = ((owner or {}).get("lang") or "it")[:2]
        base = get_public_base_url().rstrip("/")
        try:
            raw = await send_email(
                to=to,
                template="agency_activated",
                lang=lang if lang in ("it", "en", "es") else "it",
                variables={
                    "name": (owner or {}).get("name") or "Colleague",
                    "agency_name": agency.get("display_name") or agency.get("slug") or "",
                    "login_url": f"{base}/{lang}/login",
                    "dashboard_url": f"{base}/{lang}/app/dashboard",
                },
            )
            st = (raw or {}).get("status")
            email_result = {**(raw or {}), "ok": st in ("sent", "mock"), "to": to}
        except Exception as exc:  # noqa: BLE001
            logger.warning("auto-activate email failed: %s", exc)
            email_result = {"ok": False, "error": str(exc)[:200], "to": to}

    return {
        "ok": True,
        "activation_status": "active",
        "activated_at": now,
        "grant": grant,
        "email": email_result,
        "tier": preferred,
    }


async def maybe_auto_activate_from_kyc(db, agency_id: str) -> Dict[str, Any]:
    """Tenta auto-attivazione se docs+pay pronti e Gemini matcha i dati."""
    if not kyc_auto_activate_enabled():
        return {"ok": False, "skipped": "feature_off"}

    agency = await db.agencies.find_one({"id": agency_id}, {"_id": 0})
    if not agency:
        return {"ok": False, "skipped": "agency_not_found"}

    st = (agency.get("activation_status") or "active").lower()
    if st != "pending":
        return {"ok": False, "skipped": "not_pending", "activation_status": st}

    if agency.get("kyc_auto_activate_at"):
        return {"ok": True, "skipped": "already_auto_activated"}

    if not _kyc_docs_ready(agency):
        return {"ok": False, "skipped": "kyc_incomplete"}

    from shared.auth.agency_credentials import agency_payment_ok

    if not await agency_payment_ok(db, agency_id):
        return {"ok": False, "skipped": "payment_incomplete"}

    visura_doc = _latest_doc(agency, "visura_camerale")
    id_doc = _latest_doc(agency, "documento_identita")
    if not visura_doc or not id_doc:
        return {"ok": False, "skipped": "docs_missing"}

    from shared.storage import get_object, ObjStoreError

    try:
        v_bytes, v_mime = get_object(visura_doc["storage_path"])
        i_bytes, i_mime = get_object(id_doc["storage_path"])
    except ObjStoreError as exc:
        logger.warning("kyc auto get_object failed: %s", exc)
        return {"ok": False, "skipped": "storage_error", "error": str(exc)[:160]}

    try:
        visura = await _gemini_extract_doc(
            data=v_bytes, mime=v_mime or "application/pdf", doc_type="visura_camerale"
        )
        identity = await _gemini_extract_doc(
            data=i_bytes, mime=i_mime or "image/jpeg", doc_type="documento_identita"
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("kyc auto extract failed agency=%s: %s", agency_id, exc)
        report = {"matched": False, "error": str(exc)[:200], "stage": "extract"}
        await db.agencies.update_one(
            {"id": agency_id},
            {
                "$set": {
                    "kyc.auto_verify": report,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            },
        )
        return {"ok": False, "skipped": "extract_failed", "report": report}

    owner = await db.users.find_one(
        {"id": agency.get("owner_id")},
        {"_id": 0, "id": 1, "email": 1, "name": 1, "lang": 1},
    )
    report = compare_declared(agency=agency, owner=owner, visura=visura, identity=identity)
    now = datetime.now(timezone.utc).isoformat()

    if not report.get("matched"):
        await db.agencies.update_one(
            {"id": agency_id},
            {
                "$set": {
                    "kyc.auto_verify": {**report, "at": now, "outcome": "mismatch"},
                    "updated_at": now,
                }
            },
        )
        return {"ok": False, "skipped": "mismatch", "report": report}

    # Match → mark KYC verified + activate
    kyc = dict(agency.get("kyc") or {})
    kyc["status"] = "verified"
    kyc["verified_at"] = now
    kyc["verified_by"] = "kyc_auto_activate_d163"
    kyc["auto_verify"] = {**report, "at": now, "outcome": "matched"}

    await db.agencies.update_one(
        {"id": agency_id},
        {"$set": {"kyc": kyc, "updated_at": now}},
    )
    agency = await db.agencies.find_one({"id": agency_id}, {"_id": 0}) or agency

    act = await _perform_activation(
        db, agency, activated_by="kyc_auto_activate_d163"
    )
    await db.agencies.update_one(
        {"id": agency_id},
        {
            "$set": {
                "kyc_auto_activate_at": now,
                "pending_notify_sent_at": agency.get("pending_notify_sent_at") or now,
                "updated_at": now,
            }
        },
    )
    logger.info(
        "kyc auto-activate OK agency=%s email_ok=%s",
        agency_id,
        (act.get("email") or {}).get("ok"),
    )
    return {"ok": True, "auto_activated": True, "report": report, "activation": act}


async def maybe_finalize_agency_onboarding(db, agency_id: str) -> Dict[str, Any]:
    """Orchestratore: prova auto-Attiva; se no → email pending (D-162)."""
    auto = await maybe_auto_activate_from_kyc(db, agency_id)
    if auto.get("ok") and auto.get("auto_activated"):
        return {"ok": True, "path": "auto_activate", **auto}

    from shared.auth.agency_pending_notify import maybe_send_agency_pending_ready

    pending = await maybe_send_agency_pending_ready(db, agency_id)
    return {
        "ok": bool(pending.get("ok") or auto.get("skipped")),
        "path": "pending_or_wait",
        "auto": auto,
        "pending": pending,
    }

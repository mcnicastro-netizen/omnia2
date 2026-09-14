"""OMNIA — Fascicolo Immobile AI (idea ecosistema #1, precursore del paperless).

Vista unica per immobile: dati + valutazione AI + render staging + checklist
documentale per il rogito con analisi AL dei documenti mancanti.
"""
from __future__ import annotations

import base64
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user
from shared.db.connection import Database
from shared.storage import put_object, get_object, ObjStoreError

logger = logging.getLogger("omnia.fascicolo")
router = APIRouter(prefix="/fascicolo", tags=["fascicolo"])

MAX_DOC_MB = 8
CONDO_TYPES = {"appartamento", "attico", "loft", "monolocale"}

DOC_TYPES: List[Dict[str, Any]] = [
    {"key": "ape", "label": "APE — Attestato di Prestazione Energetica", "required": True},
    {"key": "planimetria_catastale", "label": "Planimetria catastale", "required": True},
    {"key": "visura_catastale", "label": "Visura catastale", "required": True},
    {"key": "atto_provenienza", "label": "Atto di provenienza (rogito / successione / donazione)", "required": True},
    {"key": "documento_identita", "label": "Documento d'identità del venditore", "required": True},
    {"key": "conformita_urbanistica", "label": "Conformità urbanistica / titoli edilizi", "required": False},
    {"key": "certificato_agibilita", "label": "Certificato di agibilità", "required": False},
    {"key": "visura_ipotecaria", "label": "Visura ipotecaria", "required": False},
    {"key": "regolamento_condominio", "label": "Regolamento di condominio", "required": False, "condo_only": True},
    {"key": "spese_condominiali", "label": "Attestazione spese condominiali", "required": False, "condo_only": True},
    {"key": "altro", "label": "Altro documento", "required": False},
]

CONDITION_MAP = {"ottime": "ottimo", "buone": "buono"}


class DocumentUploadBody(BaseModel):
    doc_type: str
    name: str = Field(max_length=200)
    mime: str = Field(max_length=100)
    file_data: str  # base64 (no data: prefix)


from shared.auth.tenant import optional_agency_id as _agency_of


async def _get_property(db, user: dict, property_id: str, projection: Optional[dict] = None) -> dict:
    q: Dict[str, Any] = {"id": property_id}
    agency_id = _agency_of(user)
    if agency_id:
        q["agency_id"] = agency_id
    prop = await db.properties.find_one(q, projection or {"_id": 0})
    if not prop:
        raise HTTPException(404, "Immobile non trovato")
    return prop


def _build_checklist(prop: dict) -> List[Dict[str, Any]]:
    docs = prop.get("documents") or []
    by_type: Dict[str, List[dict]] = {}
    for d in docs:
        by_type.setdefault(d.get("doc_type", "altro"), []).append(d)

    is_condo = (prop.get("property_type") or "") in CONDO_TYPES
    checklist = []
    for dt in DOC_TYPES:
        if dt.get("condo_only") and not is_condo:
            continue
        present = dt["key"] in by_type
        item = {
            "key": dt["key"],
            "label": dt["label"],
            "required": dt["required"],
            "present": present,
            "documents": [
                {"id": d["id"], "name": d["name"], "uploaded_at": d.get("uploaded_at")}
                for d in by_type.get(dt["key"], [])
            ],
        }
        if dt["key"] == "ape" and not present:
            eclass = (prop.get("energy") or {}).get("energy_class") or prop.get("energy_class")
            if eclass:
                item["note"] = f"Classe energetica {eclass} dichiarata nell'annuncio ma APE non caricato"
        checklist.append(item)
    return checklist


async def _compute_valuation(prop: dict) -> Optional[Dict[str, Any]]:
    """Best-effort AI valuation of the property via the ImmobilCloud valuator."""
    if not prop.get("city") or not prop.get("surface_sqm"):
        return None
    try:
        from apps.immocloud.valuator import ValuationPayload, _estimate_value_core

        cond = prop.get("condition")
        eclass = (prop.get("energy") or {}).get("energy_class") or prop.get("energy_class")
        payload = ValuationPayload(
            city=prop["city"],
            zone=prop.get("zone"),
            address=prop.get("address"),
            property_type=prop.get("property_type") or "appartamento",
            surface_sqm=int(prop["surface_sqm"]),
            condition=CONDITION_MAP.get(cond, cond) or "buono",
            energy_class=eclass,
            floor=int(prop["floor"]) if prop.get("floor") is not None else None,
        )
        result = await _estimate_value_core(payload)
        return {
            "estimated_value": result.get("estimated_value"),
            "price_per_sqm": result.get("price_per_sqm"),
            "confidence": result.get("confidence"),
            "zone_tier": result.get("zone_tier"),
        }
    except Exception as e:
        logger.warning("Fascicolo valuation failed for %s: %s", prop.get("id"), e)
        return None


def _rule_based_analysis(checklist: List[dict], prop: dict) -> str:
    missing_req = [c["label"] for c in checklist if c["required"] and not c["present"]]
    missing_opt = [c["label"] for c in checklist if not c["required"] and not c["present"]]
    lines = []
    if not missing_req:
        lines.append("✅ Tutti i documenti obbligatori per il rogito sono presenti nel fascicolo.")
    else:
        lines.append(f"⚠️ Mancano {len(missing_req)} documenti obbligatori per andare a rogito:")
        lines.extend(f"• {m}" for m in missing_req)
    if missing_opt:
        lines.append("")
        lines.append("Consigliati ma non ancora caricati:")
        lines.extend(f"• {m}" for m in missing_opt)
    return "\n".join(lines)


# ─── Endpoints ───────────────────────────────────────────────────
@router.get("/{property_id}")
async def get_fascicolo(property_id: str, user=Depends(get_current_user)) -> Dict[str, Any]:
    db = Database.get()
    prop = await _get_property(db, user, property_id, {"_id": 0, "documents.file_data": 0})

    checklist = _build_checklist(prop)
    required_total = sum(1 for c in checklist if c["required"])
    required_done = sum(1 for c in checklist if c["required"] and c["present"])

    staging_jobs = await db.virtual_staging_jobs.find(
        {"property_id": property_id, "status": "done"},
        {"_id": 0, "id": 1, "style": 1, "room_type": 1, "mode": 1, "variants": 1, "variant_url": 1, "created_at": 1},
    ).sort("created_at", -1).limit(12).to_list(length=12)

    valuation = await _compute_valuation(prop)

    photos = prop.get("photos") or []
    cover = next((p["url"] for p in photos if p.get("is_cover")), photos[0]["url"] if photos else None)

    return {
        "property": {
            "id": prop["id"],
            "title": prop.get("title"),
            "city": prop.get("city"),
            "zone": prop.get("zone"),
            "address": prop.get("address"),
            "property_type": prop.get("property_type"),
            "operation": prop.get("operation"),
            "price": prop.get("price"),
            "surface_sqm": prop.get("surface_sqm"),
            "rooms": prop.get("rooms"),
            "energy_class": (prop.get("energy") or {}).get("energy_class"),
            "condition": prop.get("condition"),
            "status": prop.get("status"),
            "description": prop.get("description"),
            "cover_url": cover,
            "photo_count": len(photos),
        },
        "checklist": checklist,
        "progress": {"required_done": required_done, "required_total": required_total},
        "documents": prop.get("documents") or [],
        "staging_jobs": staging_jobs,
        "valuation": valuation,
        "last_analysis": prop.get("fascicolo_analysis"),
    }


@router.post("/{property_id}/documents")
async def upload_document(
    property_id: str,
    body: DocumentUploadBody,
    user=Depends(get_current_user),
) -> Dict[str, Any]:
    db = Database.get()
    if body.doc_type not in {d["key"] for d in DOC_TYPES}:
        raise HTTPException(400, f"Tipo documento non valido: {body.doc_type}")
    try:
        raw = base64.b64decode(body.file_data, validate=True)
    except Exception:
        raise HTTPException(400, "file_data non è base64 valido")
    if len(raw) > MAX_DOC_MB * 1024 * 1024:
        raise HTTPException(413, f"Documento troppo grande (max {MAX_DOC_MB} MB)")

    await _get_property(db, user, property_id, {"_id": 1})

    doc = {
        "id": str(uuid4()),
        "doc_type": body.doc_type,
        "name": body.name,
        "mime": body.mime,
        "size": len(raw),
        "file_data": body.file_data,
        "uploaded_by": user["id"],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.properties.update_one(
        {"id": property_id},
        {"$push": {"documents": doc}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    meta = {k: v for k, v in doc.items() if k != "file_data"}
    return {"ok": True, "document": meta}


@router.post("/{property_id}/documents/upload")
async def upload_document_multipart(
    property_id: str,
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    user=Depends(get_current_user),
) -> Dict[str, Any]:
    """M24 — multipart upload verso Object Storage (niente base64 nel body/DB)."""
    db = Database.get()
    if doc_type not in {d["key"] for d in DOC_TYPES}:
        raise HTTPException(400, f"Tipo documento non valido: {doc_type}")
    raw = await file.read()
    if not raw:
        raise HTTPException(400, "empty_file")
    if len(raw) > MAX_DOC_MB * 1024 * 1024:
        raise HTTPException(413, f"Documento troppo grande (max {MAX_DOC_MB} MB)")

    await _get_property(db, user, property_id, {"_id": 1})

    doc_id = str(uuid4())
    mime = file.content_type or "application/octet-stream"
    storage_path = f"omnia/fascicolo/{property_id}/{doc_id}"
    try:
        put_object(storage_path, raw, mime)
    except ObjStoreError as e:
        logger.exception("fascicolo upload failed prop=%s: %s", property_id, e)
        raise HTTPException(502, "storage_upload_failed") from e

    doc = {
        "id": doc_id,
        "doc_type": doc_type,
        "name": file.filename or doc_id,
        "mime": mime,
        "size": len(raw),
        "storage_path": storage_path,
        "uploaded_by": user["id"],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.properties.update_one(
        {"id": property_id},
        {"$push": {"documents": doc}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    return {"ok": True, "document": doc}


@router.get("/{property_id}/documents/{doc_id}/download")
async def download_document(property_id: str, doc_id: str, user=Depends(get_current_user)) -> Response:
    db = Database.get()
    prop = await _get_property(db, user, property_id, {"_id": 0, "documents": 1})
    doc = next((d for d in (prop.get("documents") or []) if d["id"] == doc_id), None)
    if not doc:
        raise HTTPException(404, "Documento non trovato")
    if doc.get("storage_path"):
        try:
            raw, _ct = get_object(doc["storage_path"])
        except ObjStoreError:
            raise HTTPException(410, "Documento non più disponibile")
    else:
        raw = base64.b64decode(doc["file_data"])  # legacy base64 records
    return Response(
        content=raw,
        media_type=doc.get("mime") or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{doc["name"]}"'},
    )


@router.delete("/{property_id}/documents/{doc_id}")
async def delete_document(property_id: str, doc_id: str, user=Depends(get_current_user)) -> Dict[str, bool]:
    db = Database.get()
    await _get_property(db, user, property_id, {"_id": 1})
    res = await db.properties.update_one(
        {"id": property_id},
        {"$pull": {"documents": {"id": doc_id}}},
    )
    if res.modified_count == 0:
        raise HTTPException(404, "Documento non trovato")
    return {"ok": True}


@router.post("/{property_id}/analyze")
async def analyze_fascicolo(property_id: str, user=Depends(get_current_user)) -> Dict[str, Any]:
    """AL analizza il fascicolo: cosa manca per arrivare al rogito."""
    db = Database.get()
    prop = await _get_property(db, user, property_id, {"_id": 0, "documents.file_data": 0})
    checklist = _build_checklist(prop)
    fallback = _rule_based_analysis(checklist, prop)

    text = fallback
    source = "rule_based"
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if api_key:
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            import json as _json

            ctx = {
                "immobile": {
                    "tipologia": prop.get("property_type"),
                    "città": prop.get("city"),
                    "operazione": prop.get("operation"),
                    "prezzo": prop.get("price"),
                    "classe_energetica": (prop.get("energy") or {}).get("energy_class"),
                    "stato": prop.get("condition"),
                },
                "checklist": [
                    {"documento": c["label"], "obbligatorio": c["required"], "presente": c["present"], "nota": c.get("note")}
                    for c in checklist
                ],
            }
            chat = LlmChat(
                api_key=api_key,
                session_id=f"fascicolo-{property_id}-{uuid4().hex[:6]}",
                system_message=(
                    "Sei HAL, assistente esperto di compravendite immobiliari italiane di OMNIA. "
                    "Analizza il fascicolo documentale di un immobile in vendita e produci un report "
                    "conciso in italiano (max 180 parole) per l'agente: 1) stato di prontezza al rogito, "
                    "2) documenti obbligatori mancanti in ordine di priorità con dove/come ottenerli "
                    "(es. visura → Agenzia Entrate/SISTER, APE → tecnico certificatore), 3) rischi da segnalare. "
                    "Usa elenchi puntati con emoji. Non inventare documenti presenti se risultano mancanti. "
                    "NON dare consulenza legale vincolante: per casi complessi rimanda a notaio."
                ),
            ).with_model("gemini", "gemini-3-flash-preview")
            raw = await chat.send_message(UserMessage(text=_json.dumps(ctx, ensure_ascii=False, default=str)))
            candidate = str(raw).strip()
            if candidate:
                text = candidate
                source = "al"
        except Exception as e:
            logger.warning("Fascicolo AL analysis failed, using rule-based: %s", e)

    analysis = {"text": text, "source": source, "at": datetime.now(timezone.utc).isoformat()}
    await db.properties.update_one({"id": property_id}, {"$set": {"fascicolo_analysis": analysis}})
    return {"ok": True, "analysis": analysis}

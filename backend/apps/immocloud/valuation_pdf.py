"""OMNIA — Report PDF di valutazione brandizzato (idea ecosistema #3).

POST /api/cloud/valuator/report-pdf — riusa la pipeline di stima e genera un
report professionale. Se l'utente è un agente autenticato, il report viene
brandizzato con nome/colori della sua agenzia (strumento di acquisizione).
"""
from __future__ import annotations

import io
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from shared.auth.dependencies import get_optional_user
from shared.db.connection import Database

from apps.billing.b2c_entitlements import (
    check_uni_entitlement,
    hash_valuation_payload,
    is_uni_payload,
)

from .valuator import ValuationPayload, _estimate_value_core

logger = logging.getLogger("omnia.valuation_pdf")
router = APIRouter(prefix="/valuator", tags=["cloud-valuator"])

CONFIDENCE_LABELS = {"high": "Alta", "medium": "Media", "low": "Orientativa"}
ZONE_LABELS = {"center": "Centro", "semicenter": "Semicentro", "periphery": "Periferia",
               "centro": "Centro", "semicentro": "Semicentro", "periferia": "Periferia"}

MERIT_LABELS = {
    "floor_class": "Piano", "exposure": "Esposizione", "view": "Vista",
    "heating": "Riscaldamento", "elevator": "Ascensore", "age": "Vetustà",
    "year_built": "Anno di costruzione", "vincolo_storico": "Vincolo storico",
    "vincolo_paesag": "Vincolo paesaggistico", "locazione_libera_breve": "Locazione breve",
    "locazione_lunga": "Locazione lunga", "nuda_proprieta": "Nuda proprietà",
}


def _eur(v: Any) -> str:
    try:
        return f"€ {int(round(float(v))):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "—"


def _build_pdf(result: Dict[str, Any], payload: ValuationPayload, branding: Dict[str, Any]) -> bytes:
    buf = io.BytesIO()
    primary = colors.HexColor(branding.get("primary_color") or "#0B1E3F")
    accent = colors.HexColor(branding.get("accent_color") or "#C19A6B")

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
        title="Rapporto di Valutazione Immobiliare",
    )
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], fontSize=19, textColor=primary, spaceAfter=2, alignment=0)
    small = ParagraphStyle("small", parent=ss["Normal"], fontSize=8, textColor=colors.HexColor("#78716c"))
    body = ParagraphStyle("body", parent=ss["Normal"], fontSize=9.5, leading=13)
    section = ParagraphStyle("section", parent=ss["Heading2"], fontSize=11, textColor=primary, spaceBefore=12, spaceAfter=4)
    bigval = ParagraphStyle("bigval", parent=ss["Title"], fontSize=26, textColor=colors.white, alignment=1, leading=30)

    story = []

    # Header
    agency_name = branding.get("name") or "OMNIA · ImmobilCloud"
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    story.append(Paragraph(agency_name, ParagraphStyle("ag", parent=ss["Normal"], fontSize=12, textColor=accent, spaceAfter=1)))
    story.append(Paragraph("Rapporto di Valutazione Immobiliare", h1))
    story.append(Paragraph(f"Emesso il {today} · Metodo UNI 10750:1998 / DPR 138/1998", small))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.2, color=accent))
    story.append(Spacer(1, 10))

    # Property summary
    surface = result.get("surface", {})
    zone_txt = payload.zone or payload.address or "—"
    rows = [
        ["Città", (result.get("city_resolved") or payload.city).title(), "Tipologia", (payload.property_type or "—").replace("_", " ").title()],
        ["Zona / Indirizzo", str(zone_txt)[:48], "Fascia zona", ZONE_LABELS.get(result.get("zone_tier"), result.get("zone_tier") or "—")],
        ["Superficie calpestabile", f"{surface.get('calpestabile_mq', payload.surface_sqm)} m²", "Superficie commerciale", f"{surface.get('commercial_mq', '—')} m²"],
        ["Stato", (payload.condition or "—").replace("_", " ").title(), "Classe energetica", payload.energy_class or "n.d."],
    ]
    t = Table(rows, colWidths=[38 * mm, 49 * mm, 40 * mm, 47 * mm])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#78716c")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#78716c")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#e7e5e4")),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # Value box
    est = result.get("estimated_value", {})
    val_table = Table(
        [[Paragraph("VALORE DI MERCATO STIMATO", ParagraphStyle("l", parent=small, textColor=colors.white, alignment=1))],
         [Paragraph(_eur(est.get("avg")), bigval)],
         [Paragraph(f"Range: {_eur(est.get('min'))} — {_eur(est.get('max'))}", ParagraphStyle("r", parent=body, textColor=colors.white, alignment=1))]],
        colWidths=[174 * mm],
    )
    val_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), primary),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
    ]))
    story.append(val_table)
    story.append(Spacer(1, 4))
    psm = result.get("price_per_sqm", {})
    conf = CONFIDENCE_LABELS.get(result.get("confidence"), "—")
    story.append(Paragraph(
        f"Prezzo al m² (commerciale): {_eur(psm.get('min'))} — {_eur(psm.get('max'))} (media {_eur(psm.get('avg'))}) · "
        f"Affidabilità stima: <b>{conf}</b> ({result.get('confidence_score', 0)}/110)", body))

    # Surface breakdown (pro mode)
    breakdown = surface.get("breakdown") or {}
    if len(breakdown) > 1:
        story.append(Paragraph("Superficie commerciale ponderata (UNI 10750)", section))
        srows = [["Componente", "m² reali", "Coeff.", "m² ponderati"]]
        for k, v in breakdown.items():
            if isinstance(v, dict):
                srows.append([k.replace("_mq", "").replace("_", " ").title(), str(v.get("mq", "")), str(v.get("coeff", "")), str(v.get("weighted", ""))])
            else:
                srows.append([k.replace("_mq", "").replace("_", " ").title(), str(v), "1.00", str(v)])
        st = Table(srows, colWidths=[70 * mm, 34 * mm, 30 * mm, 40 * mm])
        st.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f5f5f4")),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#e7e5e4")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(st)

    # Merit factors
    merit = result.get("merit_breakdown") or {}
    if merit:
        story.append(Paragraph("Coefficienti di merito applicati", section))
        mrows = [["Fattore", "Impatto"]]
        for k, v in merit.items():
            pct = v.get("pct") if isinstance(v, dict) else v
            try:
                pct_txt = f"{float(pct) * 100:+.1f}%"
            except (TypeError, ValueError):
                pct_txt = str(pct)
            mrows.append([MERIT_LABELS.get(k, k.replace("_", " ").title()), pct_txt])
        mt = Table(mrows, colWidths=[110 * mm, 64 * mm])
        mt.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f5f5f4")),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#e7e5e4")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(mt)

    # Comparables
    comps = result.get("comparables") or []
    if comps:
        story.append(Paragraph("Immobili comparabili sul mercato", section))
        crows = [["Immobile", "Zona", "m²", "Prezzo", "€/m²"]]
        for c in comps[:5]:
            crows.append([
                str(c.get("title", ""))[:38], str(c.get("zone") or c.get("city") or "")[:20],
                str(c.get("surface_sqm", "")), _eur(c.get("price")), _eur(c.get("price_per_sqm")),
            ])
        ct = Table(crows, colWidths=[62 * mm, 36 * mm, 16 * mm, 32 * mm, 28 * mm])
        ct.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f5f5f4")),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#e7e5e4")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(ct)

    # Methodology + disclaimer
    story.append(Paragraph("Metodologia", section))
    story.append(Paragraph(result.get("methodology", ""), small))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Fonte dati: {result.get('data_source', '—')} · Dataset 2025", small))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#e7e5e4")))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<i>{result.get('disclaimer', '')}</i>", small))
    contact_bits = [b for b in [branding.get("email"), branding.get("phone")] if b]
    footer = f"Report generato da {agency_name} con OMNIA ImmobilCloud"
    if contact_bits:
        footer += " · " + " · ".join(contact_bits)
    story.append(Spacer(1, 4))
    story.append(Paragraph(footer, small))

    doc.build(story)
    return buf.getvalue()


@router.post("/report-pdf")
async def valuation_report_pdf(
    payload: ValuationPayload,
    user: Optional[dict] = Depends(get_optional_user),
) -> Response:
    # --- Gate PDF (Cap. 21 · task B2C-VAL-01) ---
    # Il PDF richiede SEMPRE tier UNI (payload con commercial_surfaces o merit).
    if not is_uni_payload(payload):
        raise HTTPException(status_code=402, detail={
            "code": "payment_required",
            "message": "Il report PDF richiede la valutazione UNI 10750 a €2,99.",
            "product_key": "b2c_valuator_uni_pdf",
            "price_eur": 2.99,
        })
    if not user:
        raise HTTPException(status_code=401, detail={
            "code": "login_required",
            "message": "Accedi per scaricare il report PDF.",
        })
    is_agent = bool(user.get("agency_id") or user.get("agency_ids"))
    if not is_agent:
        payload_hash = hash_valuation_payload(payload.model_dump(exclude_none=True))
        has_ent = await check_uni_entitlement(user["id"], payload_hash)
        if not has_ent:
            raise HTTPException(status_code=402, detail={
                "code": "payment_required",
                "message": "Report PDF: paga €2,99 per scaricare.",
                "product_key": "b2c_valuator_uni_pdf",
                "price_eur": 2.99,
                "payload_hash": payload_hash,
            })
    payload.email = None  # no lead double-capture from PDF generation
    payload.name = None
    result = await _estimate_value_core(payload)

    branding: Dict[str, Any] = {}
    if user:
        agency_id = user.get("agency_id") or (user.get("agency_ids") or [None])[0]
        if agency_id:
            db = Database.get()
            ag = await db.agencies.find_one({"id": agency_id}, {"_id": 0, "display_name": 1, "branding": 1, "contact": 1})
            if ag:
                br = ag.get("branding") or {}
                ct = ag.get("contact") or {}
                branding = {
                    "name": ag.get("display_name"),
                    "primary_color": br.get("primary_color"),
                    "accent_color": br.get("accent_color"),
                    "email": ct.get("email"),
                    "phone": ct.get("phone"),
                }

    pdf = _build_pdf(result, payload, branding)
    filename = f"valutazione-{(result.get('city_resolved') or payload.city).lower().replace(' ', '-')}-{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

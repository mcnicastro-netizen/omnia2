"""OMNIA Legal Kit — PDF generation (M2.5.4c, D-055).

Uses ReportLab platypus for a clean, editorial one-column layout.
Brand palette (from Brand Lab):
    Deep Navy   #0B1E3F   headings / accents
    Emerald     #1F6B5C   secondary accent
    Warm Gold   #C8A653   fine details
    Off-White   #F5F1E8   background if needed

The PDF has 3 zones:
1. Header — "OMNIA LEGAL KIT" wordmark + template name
2. Metadata block — sender / recipient / date / PEC channel
3. Body — sections rendered from `shared.legal_kit.templates`
"""
from __future__ import annotations
import io
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from jinja2 import Template
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY

from shared.legal_kit.templates import get_template

# Brand colors from Brand Lab reference
NAVY = HexColor("#0B1E3F")
EMERALD = HexColor("#1F6B5C")
GOLD = HexColor("#C8A653")
INK = HexColor("#1c1917")
MUTED = HexColor("#78716c")
BORDER = HexColor("#e7e5e4")


def _placeholder(value: Optional[str]) -> str:
    """Empty context values render as a visible [DA COMPILARE] tag."""
    v = (value or "").strip()
    return v if v else "[DA COMPILARE]"


def _build_context(ctx: Dict[str, Any]) -> Dict[str, str]:
    """Normalize user context: every field becomes a str with placeholder fallback."""
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    return {
        "signer_name":    _placeholder(ctx.get("signer_name")),
        "agency_name":    _placeholder(ctx.get("agency_name")),
        "agency_piva":    _placeholder(ctx.get("agency_piva")),
        "agency_address": _placeholder(ctx.get("agency_address")),
        "agency_pec":     _placeholder(ctx.get("agency_pec")),
        "vendor_name":    _placeholder(ctx.get("vendor_name")),
        "contract_ref":   _placeholder(ctx.get("contract_ref")),
        "domain":         _placeholder(ctx.get("domain")),
        "today":          today,
    }


# ---------- Page decoration ----------

def _draw_header_footer(canvas_obj: canvas.Canvas, doc) -> None:
    """Header (top strip) + footer (page number + disclaimer)."""
    canvas_obj.saveState()
    w, h = A4
    # Top strip
    canvas_obj.setFillColor(NAVY)
    canvas_obj.rect(0, h - 12 * mm, w, 12 * mm, fill=1, stroke=0)
    # Wordmark
    canvas_obj.setFillColor(GOLD)
    canvas_obj.setFont("Helvetica-Bold", 9)
    canvas_obj.drawString(20 * mm, h - 7.5 * mm, "OMNIA · LEGAL KIT")
    # Tagline right
    canvas_obj.setFillColor(HexColor("#F5F1E8"))
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.drawRightString(w - 20 * mm, h - 7.5 * mm,
                               "Domain Sovereignty Kit — gratuito e non brandizzato")
    # Footer
    canvas_obj.setFillColor(MUTED)
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.drawString(20 * mm, 12 * mm,
                          "Template non brandizzato · Compila i placeholder [tra parentesi quadre] con i tuoi dati.")
    canvas_obj.drawRightString(w - 20 * mm, 12 * mm,
                               f"Pagina {doc.page}")
    canvas_obj.restoreState()


# ---------- Styles ----------

def _make_styles():
    """Return a dict of ParagraphStyle instances."""
    return {
        "eyebrow": ParagraphStyle(
            "eyebrow", fontName="Helvetica", fontSize=7.5, textColor=EMERALD,
            leading=10, spaceAfter=4, alignment=TA_LEFT,
        ),
        "h1": ParagraphStyle(
            "h1", fontName="Helvetica-Bold", fontSize=18, textColor=NAVY,
            leading=22, spaceAfter=6, alignment=TA_LEFT,
        ),
        "meta": ParagraphStyle(
            "meta", fontName="Helvetica", fontSize=9, textColor=INK,
            leading=13, spaceAfter=2,
        ),
        "meta_label": ParagraphStyle(
            "meta_label", fontName="Helvetica-Bold", fontSize=7.5,
            textColor=MUTED, leading=10, spaceAfter=0,
        ),
        "h2": ParagraphStyle(
            "h2", fontName="Helvetica-Bold", fontSize=11, textColor=NAVY,
            leading=14, spaceBefore=10, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=10, textColor=INK,
            leading=14, alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "footer_disclaimer": ParagraphStyle(
            "footer_disclaimer", fontName="Helvetica-Oblique", fontSize=7.5,
            textColor=MUTED, leading=10, spaceBefore=8,
        ),
    }


# ---------- Rendering ----------

def render_pdf(slug: str, ctx: Dict[str, Any]) -> bytes:
    """Return raw PDF bytes for the requested template.

    Raises `KeyError` if the slug is unknown, `TypeError` if ctx is not a dict.
    """
    tpl = get_template(slug)  # raises KeyError if unknown
    filled = _build_context(ctx or {})
    styles = _make_styles()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=22 * mm, bottomMargin=20 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
        title=f"OMNIA Legal Kit — {tpl['name']}",
        author="OMNIA Real Estate Ecosystem",
        subject="Domain Sovereignty Kit",
    )

    story = []
    # Eyebrow + title
    story.append(Paragraph("MODELLO LEGALE · DA INVIARE VIA PEC", styles["eyebrow"]))
    story.append(Paragraph(tpl["name"], styles["h1"]))

    # Metadata block
    meta_rows = [
        ("Da",           filled["agency_name"]),
        ("P.IVA / CF",   filled["agency_piva"]),
        ("Sede",         filled["agency_address"]),
        ("PEC mittente", filled["agency_pec"]),
        ("A",            tpl["target"] + (f" — {filled['vendor_name']}"
                                          if filled["vendor_name"] != "[DA COMPILARE]" else "")),
        ("Data",         filled["today"]),
        ("Canale",       tpl["channel"]),
    ]
    for label, value in meta_rows:
        story.append(Paragraph(label.upper(), styles["meta_label"]))
        story.append(Paragraph(value, styles["meta"]))

    story.append(Spacer(1, 6 * mm))

    # Sections (each rendered from Jinja with context)
    for heading, body_tpl in tpl["sections"]:
        rendered = Template(body_tpl).render(**filled)
        # Escape < and > for reportlab XML paragraph, preserve line breaks
        safe = (rendered
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br/>"))
        story.append(KeepTogether([
            Paragraph(heading, styles["h2"]),
            Paragraph(safe, styles["body"]),
        ]))

    # Closing
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(
        "Cordiali saluti.<br/><br/>"
        f"<b>{filled['signer_name']}</b><br/>"
        f"Legale rappresentante — {filled['agency_name']}<br/>"
        f"PEC: {filled['agency_pec']}",
        styles["body"]))
    story.append(Paragraph(
        "Questo modello è fornito gratuitamente da OMNIA Real Estate Ecosystem "
        "come parte del \"Domain Sovereignty Kit\". Il modello NON costituisce "
        "parere legale: per situazioni specifiche consulta un avvocato di fiducia. "
        "Compila i placeholder [tra parentesi quadre] con i tuoi dati prima "
        "dell'invio via PEC.",
        styles["footer_disclaimer"]))

    doc.build(story, onFirstPage=_draw_header_footer,
              onLaterPages=_draw_header_footer)
    return buf.getvalue()


def render_kit_zip(ctx: Dict[str, Any]) -> bytes:
    """Bundle all 4 templates into a single ZIP archive."""
    import zipfile
    from shared.legal_kit.templates import TEMPLATES

    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as zf:
        for slug in TEMPLATES.keys():
            pdf = render_pdf(slug, ctx)
            zf.writestr(f"omnia_legal_{slug}.pdf", pdf)
        # Include a small README
        readme = (
            "OMNIA Legal Kit — Domain Sovereignty Kit\n"
            "=========================================\n\n"
            "Questo pacchetto contiene 4 modelli PDF per aiutarti a riprendere "
            "il controllo dei tuoi dati e del tuo dominio.\n\n"
            "1. omnia_legal_gdpr_20.pdf         — Richiesta portabilità dati (GDPR art. 20)\n"
            "2. omnia_legal_pec_titolarita_dominio.pdf — Titolarità dominio al registrar\n"
            "3. omnia_legal_disdetta_fornitore.pdf     — Disdetta contratto fornitore\n"
            "4. omnia_legal_reclamo_cnr_iit.pdf        — Reclamo/richiesta CNR-IIT\n\n"
            "Prima di inviare:\n"
            "  - Compila tutti i placeholder [DA COMPILARE] con i tuoi dati\n"
            "  - Verifica le clausole del contratto in essere (preavvisi, penali)\n"
            "  - Se hai dubbi, consulta un avvocato di tua fiducia\n\n"
            "Delivery: 100% digitale via PEC — nessun invio cartaceo necessario.\n\n"
            "OMNIA Real Estate Ecosystem — omniarealestateecosystem.it\n"
        )
        zf.writestr("LEGGIMI.txt", readme)
    return zbuf.getvalue()

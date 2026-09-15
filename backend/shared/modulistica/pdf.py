"""White-label PDF renderer for agency modulistica (M5.S7 / D-041).

Brand hierarchy:
  - Header / accents use agency primary + accent colors
  - Agency display name is the hero brand signal
  - OMNIA appears only as a subtle generator note for turnkey/hybrid;
    for plan_type=whitelabel the footer omits OMNIA entirely.
"""
from __future__ import annotations
import io
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from jinja2 import Template
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

from shared.modulistica.catalog import get_template


_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _placeholder(value: Optional[str]) -> str:
    v = (value or "").strip()
    return v if v else "[DA COMPILARE]"


def _color(hex_str: Optional[str], fallback: str) -> HexColor:
    h = (hex_str or "").strip()
    if not _HEX_RE.match(h):
        h = fallback
    return HexColor(h)


def _build_context(ctx: Dict[str, Any]) -> Dict[str, str]:
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    out: Dict[str, str] = {"today": today}
    for k, v in (ctx or {}).items():
        if k == "today":
            continue
        out[k] = _placeholder(str(v) if v is not None else "")
    # Ensure common keys exist even if missing
    for key in (
        "agency_name", "agency_piva", "agency_address", "agency_rea", "agency_pec",
        "agency_email", "agency_phone", "buyer_name", "seller_name", "client_name",
        "property_address", "property_city",
    ):
        out.setdefault(key, "[DA COMPILARE]")
    return out


def render_modulistica_pdf(
    slug: str,
    ctx: Dict[str, Any],
    *,
    branding: Optional[Dict[str, Any]] = None,
    plan_type: str = "hybrid",
) -> bytes:
    """Render a white-label branded PDF for the given template slug."""
    tpl = get_template(slug)
    if not tpl:
        raise KeyError(slug)

    branding = branding or {}
    primary = _color(branding.get("primary_color"), "#0B1E3F")
    accent = _color(branding.get("accent_color"), "#1F6B5C")
    agency_title = (ctx.get("agency_name") or branding.get("display_name") or "Agenzia").strip()
    tagline = (branding.get("tagline") or "").strip()
    filled = _build_context(ctx)
    if agency_title and filled.get("agency_name") == "[DA COMPILARE]":
        filled["agency_name"] = agency_title

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title=tpl["name"],
        author=agency_title,
    )

    styles = {
        "brand": ParagraphStyle(
            "brand", fontName="Helvetica-Bold", fontSize=16, textColor=primary,
            spaceAfter=2, leading=20,
        ),
        "tagline": ParagraphStyle(
            "tagline", fontName="Helvetica", fontSize=9, textColor=accent,
            spaceAfter=8, leading=12,
        ),
        "title": ParagraphStyle(
            "title", fontName="Helvetica-Bold", fontSize=13, textColor=black,
            spaceBefore=8, spaceAfter=10, leading=17,
        ),
        "h": ParagraphStyle(
            "h", fontName="Helvetica-Bold", fontSize=10, textColor=primary,
            spaceBefore=10, spaceAfter=4, leading=13,
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=9.5, textColor=black,
            alignment=TA_JUSTIFY, leading=13, spaceAfter=4,
        ),
        "meta": ParagraphStyle(
            "meta", fontName="Helvetica", fontSize=8, textColor=HexColor("#57534e"),
            leading=11, spaceAfter=2,
        ),
        "disc": ParagraphStyle(
            "disc", fontName="Helvetica-Oblique", fontSize=7.5,
            textColor=HexColor("#78716c"), alignment=TA_LEFT, leading=10,
        ),
        "footer": ParagraphStyle(
            "footer", fontName="Helvetica", fontSize=7,
            textColor=HexColor("#a8a29e"), alignment=TA_CENTER, leading=9,
        ),
    }

    story = []
    story.append(Paragraph(_esc(agency_title), styles["brand"]))
    if tagline:
        story.append(Paragraph(_esc(tagline), styles["tagline"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary, spaceAfter=6))
    story.append(Paragraph(_esc(tpl["name"]), styles["title"]))
    story.append(Paragraph(
        f"Categoria: {_esc(tpl['category'])} · Data: {_esc(filled['today'])}",
        styles["meta"],
    ))
    story.append(Spacer(1, 4))

    for heading, body_jinja in tpl["sections"]:
        rendered = Template(body_jinja).render(**filled)
        # Convert newlines to <br/>
        rendered_html = _esc(rendered).replace("\n", "<br/>")
        story.append(Paragraph(_esc(heading), styles["h"]))
        story.append(Paragraph(rendered_html, styles["body"]))

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#e7e5e4"), spaceBefore=4, spaceAfter=6))
    story.append(Paragraph(
        "Documento generato come bozza operativa del gestionale. Non costituisce parere legale. "
        "Verificare con un professionista abilitato prima dell'uso in produzione. "
        "Firma elettronica tramite provider esterno (Yousign/DocuSign) — nessuna firma qualificata proprietaria.",
        styles["disc"],
    ))
    if plan_type != "whitelabel":
        story.append(Spacer(1, 6))
        story.append(Paragraph("Generato digitalmente · zero carta (No Paper)", styles["footer"]))

    def _on_page(canvas, _doc):
        canvas.saveState()
        canvas.setStrokeColor(accent)
        canvas.setLineWidth(2)
        canvas.line(18 * mm, A4[1] - 10 * mm, A4[0] - 18 * mm, A4[1] - 10 * mm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()


def _esc(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

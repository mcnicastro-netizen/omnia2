"""OMNIA — Report PDF di valutazione (eleganza + chiarezza).

POST /api/cloud/valuator/report-pdf — riusa la pipeline di stima e genera un
report A4 professionale.

Branding:
  - B2C / senza agenzia → ImmobilCloud (OMNIA), accenti navy/bronzo
  - Agente → nome/colori/logo/tagline agenzia
  - plan_type=whitelabel → zero menzione OMNIA/ImmobilCloud nel documento
  - hybrid/turnkey → nota footer discreta «Generato con OMNIA ImmobilCloud»
"""
from __future__ import annotations

import io
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from xml.sax.saxutils import escape as xml_escape

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    Image,
    KeepTogether,
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

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

# ImmobilCloud defaults (OMNIA-branded report)
OMNIA_BRAND = {
    "name": "ImmobilCloud",
    "tagline": "Valutazione immobiliare · OMNIA",
    "primary_color": "#0B1E3F",
    "accent_color": "#A8895C",
    "plan_type": "omnia",
}

CONFIDENCE_LABELS = {"high": "Alta", "medium": "Media", "low": "Orientativa"}
ZONE_LABELS = {
    "center": "Centro", "semicenter": "Semicentro", "periphery": "Periferia",
    "centro": "Centro", "semicentro": "Semicentro", "periferia": "Periferia",
}
MERIT_LABELS = {
    "floor": "Piano", "floor_class": "Piano",
    "exposure": "Esposizione", "view": "Vista",
    "heating": "Riscaldamento", "elevator": "Ascensore", "age": "Vetustà",
    "year_built": "Anno di costruzione", "vincolo_storico": "Vincolo storico",
    "vincolo_paesag": "Vincolo paesaggistico", "locazione_libera_breve": "Locazione breve",
    "locazione_lunga": "Locazione lunga", "nuda_proprieta": "Nuda proprietà",
}

_FONTS_READY = False
FONT_SANS = "Helvetica"
FONT_SANS_BOLD = "Helvetica-Bold"
FONT_SERIF = "Times-Roman"
FONT_SERIF_BOLD = "Times-Bold"


def _register_fonts() -> None:
    global _FONTS_READY, FONT_SANS, FONT_SANS_BOLD, FONT_SERIF, FONT_SERIF_BOLD
    if _FONTS_READY:
        return
    candidates = [
        (
            "ValSans", "ValSans-Bold", "ValSerif", "ValSerif-Bold",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf",
        ),
        (
            "ValSans", "ValSans-Bold", "ValSerif", "ValSerif-Bold",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        ),
    ]
    for names in candidates:
        sans, sans_b, serif, serif_b, p_sans, p_sans_b, p_serif, p_serif_b = names
        paths = [Path(p) for p in (p_sans, p_sans_b, p_serif, p_serif_b)]
        if not all(p.exists() for p in paths):
            continue
        try:
            pdfmetrics.registerFont(TTFont(sans, str(paths[0])))
            pdfmetrics.registerFont(TTFont(sans_b, str(paths[1])))
            pdfmetrics.registerFont(TTFont(serif, str(paths[2])))
            pdfmetrics.registerFont(TTFont(serif_b, str(paths[3])))
            FONT_SANS, FONT_SANS_BOLD = sans, sans_b
            FONT_SERIF, FONT_SERIF_BOLD = serif, serif_b
            _FONTS_READY = True
            return
        except Exception as e:
            logger.warning("font registration failed: %s", e)
    _FONTS_READY = True  # stick with built-ins


def _color(hex_str: Optional[str], fallback: str) -> colors.Color:
    h = (hex_str or "").strip()
    if not _HEX_RE.match(h):
        h = fallback
    return colors.HexColor(h)


def _esc(text: Any) -> str:
    return xml_escape("" if text is None else str(text))


def _eur(v: Any) -> str:
    try:
        return f"€ {int(round(float(v))):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "—"


def _is_whitelabel(branding: Dict[str, Any]) -> bool:
    return (branding.get("plan_type") or "").lower() == "whitelabel"


def _sanitize_disclaimer(text: str, branding: Dict[str, Any]) -> str:
    """Neutralize OMNIA product mentions on white-label reports."""
    t = (text or "").strip()
    if not t:
        t = (
            "Stima orientativa basata su dati statistici di mercato e norme UNI 10750. "
            "Non costituisce perizia ufficiale né parere vincolante."
        )
    if _is_whitelabel(branding):
        t = re.sub(r"\bagente OMNIA certificato\b", "professionista abilitato", t, flags=re.I)
        t = re.sub(r"\bOMNIA\b", "un professionista", t, flags=re.I)
        t = re.sub(r"\bImmobilCloud\b", "", t, flags=re.I)
        t = re.sub(r"\s{2,}", " ", t).strip()
    return t


def _fetch_logo(url: Optional[str], max_h_mm: float = 14.0) -> Optional[Image]:
    if not url or not str(url).startswith(("http://", "https://", "/")):
        return None
    try:
        data: Optional[bytes] = None
        if str(url).startswith("/"):
            # local absolute path only (not web path)
            p = Path(url)
            if p.is_file():
                data = p.read_bytes()
        else:
            with httpx.Client(timeout=4.0, follow_redirects=True) as client:
                r = client.get(url)
                if r.status_code == 200 and r.content:
                    ctype = (r.headers.get("content-type") or "").lower()
                    if "image" in ctype or url.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                        data = r.content
        if not data or len(data) > 2_000_000:
            return None
        img = Image(io.BytesIO(data))
        # Cap height, preserve aspect
        max_h = max_h_mm * mm
        max_w = 48 * mm
        iw, ih = float(img.imageWidth), float(img.imageHeight)
        if ih <= 0 or iw <= 0:
            return None
        scale = min(max_h / ih, max_w / iw, 1.0)
        img.drawHeight = ih * scale
        img.drawWidth = iw * scale
        return img
    except Exception as e:
        logger.info("logo skip: %s", e)
        return None


# Soft palette (navy + bronze, no cream/purple)
_PAGE_WASH = colors.HexColor("#F5F8FC")
_CARD_BG = colors.HexColor("#EEF3F9")
_ROW_ALT = colors.HexColor("#F3F7FB")
_INK = colors.HexColor("#1A2740")
_MUTED = colors.HexColor("#5B6B82")


class AccentRule(Flowable):
    """Short bronze bar + optional hairline — used under section titles."""

    def __init__(self, color: colors.Color, thickness: float = 2.2, short: bool = True):
        super().__init__()
        self._color = color
        self._thickness = thickness
        self._short = short
        self.width = 0
        self.height = thickness + 3

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return self.width, self.height

    def draw(self):
        self.canv.setStrokeColor(self._color)
        self.canv.setFillColor(self._color)
        self.canv.setLineWidth(self._thickness)
        bar_w = min(28 * mm, self.width * 0.22) if self._short else self.width
        y = 1.5
        self.canv.roundRect(0, y - self._thickness / 2, bar_w, self._thickness, 0.6, stroke=0, fill=1)
        if self._short and self.width > bar_w + 4:
            self.canv.setStrokeColor(colors.HexColor("#D5DEEA"))
            self.canv.setLineWidth(0.5)
            self.canv.line(bar_w + 3 * mm, y, self.width, y)


class SectionTitle(Flowable):
    """Serif section title with bronze mark on the left."""

    def __init__(self, text: str, primary: colors.Color, accent: colors.Color):
        super().__init__()
        self._text = text
        self._primary = primary
        self._accent = accent
        self.width = 0
        self.height = 13

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(self._accent)
        c.roundRect(0, 2.5, 2.0 * mm, 8.5, 0.7, stroke=0, fill=1)
        c.setFillColor(self._primary)
        c.setFont(FONT_SERIF_BOLD, 10.5)
        c.drawString(4.5 * mm, 4.5, self._text)


def _styles(primary: colors.Color, accent: colors.Color, muted: colors.Color) -> Dict[str, ParagraphStyle]:
    return {
        "brand": ParagraphStyle(
            "v_brand", fontName=FONT_SERIF_BOLD, fontSize=22, leading=26,
            textColor=primary, spaceAfter=1, alignment=TA_LEFT,
        ),
        "tagline": ParagraphStyle(
            "v_tag", fontName=FONT_SANS, fontSize=8, leading=10,
            textColor=accent, spaceAfter=1, alignment=TA_LEFT,
        ),
        "doc_title": ParagraphStyle(
            "v_title", fontName=FONT_SERIF_BOLD, fontSize=12.5, leading=16,
            textColor=primary, spaceBefore=5, spaceAfter=1, alignment=TA_LEFT,
        ),
        "meta": ParagraphStyle(
            "v_meta", fontName=FONT_SANS, fontSize=7.5, leading=10,
            textColor=muted, spaceAfter=5,
        ),
        "section": ParagraphStyle(
            "v_sec", fontName=FONT_SERIF_BOLD, fontSize=10.5, leading=13,
            textColor=primary, spaceBefore=8, spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "v_body", fontName=FONT_SANS, fontSize=8.5, leading=12,
            textColor=_INK,
        ),
        "label": ParagraphStyle(
            "v_label", fontName=FONT_SANS, fontSize=6.5, leading=8,
            textColor=muted, alignment=TA_LEFT,
        ),
        "value": ParagraphStyle(
            "v_val", fontName=FONT_SANS_BOLD, fontSize=9.5, leading=12,
            textColor=_INK, alignment=TA_LEFT,
        ),
        "hero_label": ParagraphStyle(
            "v_hl", fontName=FONT_SANS, fontSize=8, leading=10,
            textColor=colors.HexColor("#D8E2F0"), alignment=TA_CENTER,
            spaceBefore=0, spaceAfter=0,
        ),
        "hero_num": ParagraphStyle(
            "v_hn", fontName=FONT_SERIF_BOLD, fontSize=27, leading=30,
            textColor=colors.white, alignment=TA_CENTER,
        ),
        "hero_range": ParagraphStyle(
            "v_hr", fontName=FONT_SANS, fontSize=9, leading=12,
            textColor=colors.HexColor("#E8D5B5"), alignment=TA_CENTER,
        ),
        "cell": ParagraphStyle(
            "v_cell", fontName=FONT_SANS, fontSize=8.2, leading=11,
            textColor=_INK,
        ),
        "cell_head": ParagraphStyle(
            "v_ch", fontName=FONT_SANS_BOLD, fontSize=7.5, leading=9,
            textColor=colors.white,
        ),
        "disc": ParagraphStyle(
            "v_disc", fontName=FONT_SANS, fontSize=7.2, leading=10,
            textColor=muted, spaceBefore=1,
        ),
        "footer": ParagraphStyle(
            "v_foot", fontName=FONT_SANS, fontSize=7, leading=9,
            textColor=_MUTED, alignment=TA_CENTER,
        ),
        "conf": ParagraphStyle(
            "v_conf", fontName=FONT_SANS_BOLD, fontSize=8.5, leading=11,
            textColor=primary, alignment=TA_CENTER,
        ),
        "stat_label": ParagraphStyle(
            "v_sl", fontName=FONT_SANS, fontSize=7, leading=9,
            textColor=muted, alignment=TA_CENTER,
        ),
        "stat_value": ParagraphStyle(
            "v_sv", fontName=FONT_SANS_BOLD, fontSize=9, leading=11,
            textColor=primary, alignment=TA_CENTER,
        ),
    }


def _kv_table(pairs: List[Tuple[str, str]], styles: Dict[str, ParagraphStyle], cols: int = 2) -> Table:
    """Soft card grid of label/value pairs."""
    cells: List[List[Any]] = []
    row: List[Any] = []
    for label, value in pairs:
        cell = [
            Paragraph(_esc(label).upper(), styles["label"]),
            Spacer(1, 1.5),
            Paragraph(_esc(value), styles["value"]),
        ]
        row.append(cell)
        if len(row) >= cols:
            cells.append(row)
            row = []
    if row:
        while len(row) < cols:
            row.append("")
        cells.append(row)

    widths = [87 * mm, 87 * mm] if cols == 2 else [174 * mm / cols] * cols
    t = Table(cells, colWidths=widths)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, -1), _CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D5DEEA")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDE5F0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]
    t.setStyle(TableStyle(style_cmds))
    return t


def _data_table(headers: List[str], rows: List[List[str]], styles: Dict[str, ParagraphStyle],
                widths: List[float], primary: colors.Color) -> Table:
    head = [Paragraph(_esc(h), styles["cell_head"]) for h in headers]
    body = [[Paragraph(_esc(c), styles["cell"]) for c in r] for r in rows]
    t = Table([head] + body, colWidths=widths, repeatRows=1)
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), primary),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D5DEEA")),
        ("LINEBELOW", (0, 1), (-1, -2), 0.35, colors.HexColor("#E2EAF3")),
    ]
    for i in range(1, len(body) + 1):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), _ROW_ALT))
    t.setStyle(TableStyle(cmds))
    return t


def _hero_block(est: Dict[str, Any], styles: Dict[str, ParagraphStyle],
                primary: colors.Color, accent: colors.Color) -> Table:
    """Market-value hero: navy panel + bronze top edge + warm range."""
    inner = Table(
        [
            [Paragraph("VALORE DI MERCATO STIMATO", styles["hero_label"])],
            [Paragraph(_esc(_eur(est.get("avg"))), styles["hero_num"])],
            [Paragraph(
                f"Range {_esc(_eur(est.get('min')))}  —  {_esc(_eur(est.get('max')))}",
                styles["hero_range"],
            )],
        ],
        colWidths=[174 * mm],
    )
    inner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), primary),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (0, 0), 1),
        ("TOPPADDING", (0, 1), (0, 1), 1),
        ("BOTTOMPADDING", (0, 1), (0, 1), 1),
        ("TOPPADDING", (0, 2), (0, 2), 1),
        ("BOTTOMPADDING", (0, 2), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 0, primary),
        ("LINEABOVE", (0, 0), (-1, 0), 3.0, accent),
    ]))
    return inner


def _stats_row(psm: Dict[str, Any], conf: str, score: Any,
               styles: Dict[str, ParagraphStyle], accent: colors.Color) -> Table:
    left = [
        Paragraph("PREZZO AL M² (COMMERCIALE)", styles["stat_label"]),
        Spacer(1, 2),
        Paragraph(
            f"{_esc(_eur(psm.get('min')))} — {_esc(_eur(psm.get('max')))}",
            styles["stat_value"],
        ),
        Paragraph(f"media {_esc(_eur(psm.get('avg')))}", styles["stat_label"]),
    ]
    right = [
        Paragraph("AFFIDABILITÀ", styles["stat_label"]),
        Spacer(1, 2),
        Paragraph(f"{_esc(conf)}", styles["stat_value"]),
        Paragraph(f"{_esc(score)}/110", styles["stat_label"]),
    ]
    t = Table([[left, right]], colWidths=[100 * mm, 74 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D5DEEA")),
        ("LINEBEFORE", (1, 0), (1, 0), 1.2, accent),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def build_valuation_pdf(
    result: Dict[str, Any],
    payload: ValuationPayload,
    branding: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Public builder used by the route and by tests / sample scripts."""
    _register_fonts()
    incoming = dict(branding or {})
    plan = (incoming.get("plan_type") or "").lower()
    if plan in ("whitelabel", "hybrid", "turnkey"):
        # Agency path: never inherit OMNIA name/tagline
        branding = {
            "name": (incoming.get("name") or "Agenzia").strip(),
            "tagline": (incoming.get("tagline") or "").strip(),
            "primary_color": incoming.get("primary_color") or OMNIA_BRAND["primary_color"],
            "accent_color": incoming.get("accent_color") or "#1F6B5C",
            "logo_url": incoming.get("logo_url"),
            "email": incoming.get("email"),
            "phone": incoming.get("phone"),
            "website": incoming.get("website"),
            "plan_type": plan,
        }
    else:
        branding = {**OMNIA_BRAND, **incoming}
        if not (branding.get("name") or "").strip():
            branding["name"] = OMNIA_BRAND["name"]

    primary = _color(branding.get("primary_color"), OMNIA_BRAND["primary_color"])
    accent = _color(branding.get("accent_color"), OMNIA_BRAND["accent_color"])
    muted = _MUTED
    styles = _styles(primary, accent, muted)
    whitelabel = _is_whitelabel(branding)
    agency_name = (branding.get("name") or OMNIA_BRAND["name"]).strip()
    tagline = (branding.get("tagline") or "").strip()
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=16 * mm, rightMargin=16 * mm,
        topMargin=14 * mm, bottomMargin=16 * mm,
        title="Rapporto di Valutazione Immobiliare",
        author=agency_name,
    )

    story: List[Any] = []

    # —— Header: brand first ——
    logo = _fetch_logo(branding.get("logo_url"))
    brand_block: List[Any] = []
    brand_block.append(Paragraph(_esc(agency_name), styles["brand"]))
    if tagline:
        brand_block.append(Paragraph(_esc(tagline), styles["tagline"]))
    else:
        brand_block.append(Spacer(1, 2))

    if logo:
        header = Table([[brand_block, logo]], colWidths=[126 * mm, 52 * mm])
        header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(header)
    else:
        story.extend(brand_block)

    story.append(Spacer(1, 3))
    story.append(AccentRule(accent, thickness=2.4, short=False))
    story.append(Paragraph("Rapporto di valutazione immobiliare", styles["doc_title"]))
    story.append(Paragraph(
        f"Emesso il {today} · Metodo UNI 10750:1998 / DPR 138/1998",
        styles["meta"],
    ))

    # —— Immobile ——
    surface = result.get("surface") or {}
    zone_txt = payload.zone or payload.address or "—"
    pairs = [
        ("Città", (result.get("city_resolved") or payload.city or "—").title()),
        ("Tipologia", (payload.property_type or "—").replace("_", " ").title()),
        ("Zona / indirizzo", str(zone_txt)[:56]),
        ("Fascia", ZONE_LABELS.get(result.get("zone_tier"), result.get("zone_tier") or "—")),
        ("Superficie calpestabile", f"{surface.get('calpestabile_mq', payload.surface_sqm)} m²"),
        ("Superficie commerciale", f"{surface.get('commercial_mq', '—')} m²"),
        ("Stato", (payload.condition or "—").replace("_", " ").title()),
        ("Classe energetica", payload.energy_class or "n.d."),
    ]
    story.append(KeepTogether([
        SectionTitle("Immobile", primary, accent),
        Spacer(1, 3),
        _kv_table(pairs, styles),
    ]))

    # —— Valore hero ——
    est = result.get("estimated_value") or {}
    psm = result.get("price_per_sqm") or {}
    conf = CONFIDENCE_LABELS.get(result.get("confidence"), "—")
    story.append(Spacer(1, 7))
    story.append(KeepTogether([
        _hero_block(est, styles, primary, accent),
        Spacer(1, 5),
        _stats_row(psm, conf, result.get("confidence_score", 0), styles, accent),
    ]))

    # —— Superfici UNI ——
    breakdown = surface.get("breakdown") or {}
    if len(breakdown) > 1:
        srows = []
        for k, v in breakdown.items():
            label = k.replace("_mq", "").replace("_", " ").title()
            if isinstance(v, dict):
                mq = v.get("mq", "")
                coeff = v.get("coeff", "")
                weighted = v.get("weighted", "")
                try:
                    coeff_txt = f"{float(coeff):.0%}".replace(".", ",")
                except (TypeError, ValueError):
                    coeff_txt = str(coeff)
                try:
                    mq_txt = f"{float(mq):.1f}".rstrip("0").rstrip(".")
                except (TypeError, ValueError):
                    mq_txt = str(mq)
                try:
                    w_txt = f"{float(weighted):.1f}".rstrip("0").rstrip(".")
                except (TypeError, ValueError):
                    w_txt = str(weighted)
                srows.append([label, mq_txt, coeff_txt, w_txt])
            else:
                srows.append([label, "—", "—", str(v)])
        story.append(Spacer(1, 6))
        story.append(KeepTogether([
            SectionTitle("Superficie commerciale ponderata", primary, accent),
            Spacer(1, 3),
            _data_table(
                ["Componente", "m² reali", "Coeff.", "m² ponderati"],
                srows, styles,
                [70 * mm, 34 * mm, 30 * mm, 40 * mm],
                primary,
            ),
        ]))

    # —— Merito ——
    merit = result.get("merit_breakdown") or {}
    if merit:
        mrows = []
        for k, v in merit.items():
            pct = v.get("pct") if isinstance(v, dict) else v
            try:
                pct_txt = f"{float(pct) * 100:+.1f}%"
            except (TypeError, ValueError):
                pct_txt = str(pct)
            # Skip neutral 0% lines to keep the report airy and on one page
            try:
                if abs(float(pct)) < 1e-9:
                    continue
            except (TypeError, ValueError):
                pass
            mrows.append([MERIT_LABELS.get(k, k.replace("_", " ").title()), pct_txt])
        if mrows:
            story.append(Spacer(1, 6))
            story.append(KeepTogether([
                SectionTitle("Coefficienti di merito", primary, accent),
                Spacer(1, 3),
                _data_table(
                    ["Fattore", "Impatto"],
                    mrows, styles,
                    [120 * mm, 54 * mm],
                    primary,
                ),
            ]))

    # —— Comparabili ——
    comps = result.get("comparables") or []
    if comps:
        crows = []
        for c in comps[:3]:
            crows.append([
                str(c.get("title", ""))[:40],
                str(c.get("zone") or c.get("city") or "")[:22],
                str(c.get("surface_sqm", "")),
                _eur(c.get("price")),
                _eur(c.get("price_per_sqm")),
            ])
        story.append(Spacer(1, 6))
        story.append(KeepTogether([
            SectionTitle("Immobili comparabili", primary, accent),
            Spacer(1, 3),
            _data_table(
                ["Immobile", "Zona", "m²", "Prezzo", "€/m²"],
                crows, styles,
                [62 * mm, 36 * mm, 16 * mm, 32 * mm, 28 * mm],
                primary,
            ),
        ]))

    # —— Metodologia + disclaimer (one compact band, stay on page 1) ——
    if whitelabel:
        meth_line = (
            "Metodo: prezzi OMI/Borsino rivalutati (FOI + trend), superficie UNI 10750, "
            "moltiplicatori tipologici e coefficienti di merito."
        )
    else:
        meth_line = (
            "Metodo OMNIA: prezzi OMI/Borsino rivalutati (FOI + trend regionale), "
            "superficie UNI 10750, moltiplicatori tipologici e coefficienti di merito."
        )
    fonte = result.get("data_source") or "—"
    if len(str(fonte)) > 110:
        fonte = str(fonte)[:107] + "…"
    contact_bits = [b for b in [branding.get("email"), branding.get("phone"), branding.get("website")] if b]
    if whitelabel:
        brand_line = f"Documento emesso da {agency_name}"
    elif branding.get("plan_type") == "omnia" or not branding.get("plan_type"):
        brand_line = "Report generato da ImmobilCloud · OMNIA"
    else:
        brand_line = f"Emesso da {agency_name} · Generato con OMNIA ImmobilCloud"
    if contact_bits:
        brand_line = f"{' · '.join(contact_bits)} · {brand_line}"

    foot_card = Table(
        [[
            [
                Paragraph(f"<b>Metodologia</b> — {_esc(meth_line)}", styles["disc"]),
                Spacer(1, 2),
                Paragraph(f"Fonte: {_esc(fonte)}", styles["disc"]),
                Spacer(1, 2),
                Paragraph(
                    f"<i>{_esc(_sanitize_disclaimer(result.get('disclaimer', ''), branding))}</i>",
                    styles["disc"],
                ),
                Spacer(1, 3),
                Paragraph(_esc(brand_line), styles["footer"]),
            ]
        ]],
        colWidths=[174 * mm],
    )
    foot_card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D5DEEA")),
        ("LINEBEFORE", (0, 0), (0, 0), 2.4, accent),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(Spacer(1, 7))
    story.append(foot_card)

    page_w, page_h = A4
    accent_for_page = accent
    primary_for_page = primary

    def _on_page(canvas, _doc):
        canvas.saveState()
        # Soft page wash
        canvas.setFillColor(_PAGE_WASH)
        canvas.rect(0, 0, page_w, page_h, stroke=0, fill=1)
        # Dual top bar: navy + bronze
        canvas.setFillColor(primary_for_page)
        canvas.rect(0, page_h - 4.5 * mm, page_w, 4.5 * mm, stroke=0, fill=1)
        canvas.setFillColor(accent_for_page)
        canvas.rect(0, page_h - 6.2 * mm, page_w, 1.7 * mm, stroke=0, fill=1)
        # Bottom footer band
        canvas.setFillColor(primary_for_page)
        canvas.rect(0, 0, page_w, 10 * mm, stroke=0, fill=1)
        canvas.setFillColor(accent_for_page)
        canvas.rect(0, 10 * mm, page_w, 0.9 * mm, stroke=0, fill=1)
        canvas.setFillColor(colors.HexColor("#D8E2F0"))
        canvas.setFont(FONT_SANS, 7.5)
        canvas.drawCentredString(page_w / 2, 4 * mm, f"{_doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()


# Back-compat alias for any external imports
_build_pdf = build_valuation_pdf


@router.post("/report-pdf")
async def valuation_report_pdf(
    payload: ValuationPayload,
    user: Optional[dict] = Depends(get_optional_user),
) -> Response:
    # --- Gate PDF (Cap. 21 · task B2C-VAL-01) ---
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
    payload.email = None
    payload.name = None
    result = await _estimate_value_core(payload)

    branding: Dict[str, Any] = dict(OMNIA_BRAND)
    if user:
        agency_id = user.get("agency_id") or (user.get("agency_ids") or [None])[0]
        if agency_id:
            db = Database.get()
            ag = await db.agencies.find_one(
                {"id": agency_id},
                {"_id": 0, "display_name": 1, "branding": 1, "contact": 1, "plan_type": 1},
            )
            if ag:
                br = ag.get("branding") or {}
                ct = ag.get("contact") or {}
                branding = {
                    "name": ag.get("display_name") or OMNIA_BRAND["name"],
                    "tagline": br.get("tagline") or "",
                    "primary_color": br.get("primary_color") or OMNIA_BRAND["primary_color"],
                    "accent_color": br.get("accent_color") or "#1F6B5C",
                    "logo_url": br.get("logo_url"),
                    "email": ct.get("email"),
                    "phone": ct.get("phone"),
                    "website": ct.get("website"),
                    "plan_type": ag.get("plan_type") or "hybrid",
                }

    pdf = build_valuation_pdf(result, payload, branding)
    city_slug = (result.get("city_resolved") or payload.city or "immobile").lower().replace(" ", "-")
    filename = f"valutazione-{city_slug}-{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

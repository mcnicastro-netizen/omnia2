"""Real content watermark for MLS document distribution (not a boolean flag).

Supported:
- image/* (JPEG/PNG/WEBP) via Pillow overlay
- application/pdf via reportlab overlay page stamp

Unsupported formats: refused for distribution (never claim watermarked).
Original bytes are never returned by distribution endpoints.
PDF watermark is fail-closed: any overlay/merge failure aborts distribution.
"""
from __future__ import annotations

import io
import logging
from typing import Tuple

from fastapi import HTTPException

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE = {"image/jpeg", "image/png", "image/webp"}
SUPPORTED_PDF = {"application/pdf"}
SUPPORTED = SUPPORTED_IMAGE | SUPPORTED_PDF


def assert_format_supported(content_type: str) -> None:
    ct = (content_type or "").split(";")[0].strip().lower()
    if ct not in SUPPORTED:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "watermark_format_unsupported",
                "content_type": ct,
                "supported": sorted(SUPPORTED),
            },
        )


def apply_watermark(
    original: bytes,
    *,
    content_type: str,
    label: str,
) -> Tuple[bytes, str]:
    """Return (watermarked_bytes, out_content_type). Never mutates caller's buffer."""
    ct = (content_type or "").split(";")[0].strip().lower()
    assert_format_supported(ct)
    text = (label or "OMNIA confidential")[:180]
    if ct in SUPPORTED_IMAGE:
        return _watermark_image(original, text), "image/jpeg"
    if ct in SUPPORTED_PDF:
        return _watermark_pdf(original, text), "application/pdf"
    raise HTTPException(status_code=400, detail="watermark_format_unsupported")


def _fail_closed(stage: str, exc: BaseException) -> None:
    """Abort distribution — never emit unwatermarked or partially watermarked bytes."""
    logger.error("watermark_apply_failed stage=%s err=%s", stage, type(exc).__name__)
    raise HTTPException(
        status_code=500,
        detail={"error": "watermark_apply_failed", "stage": stage},
    ) from exc


def _watermark_image(image_bytes: bytes, text: str) -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        font_size = max(16, img.size[0] // 36)
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size
            )
        except Exception:
            font = ImageFont.load_default()
        padding = font_size // 2
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x0 = max(0, img.size[0] - tw - padding * 3)
        y0 = max(0, img.size[1] - th - padding * 3)
        draw.rectangle(
            [x0, y0, img.size[0] - padding, img.size[1] - padding],
            fill=(0, 0, 0, 170),
        )
        draw.text(
            (x0 + padding, y0 + padding), text, font=font, fill=(255, 255, 255, 255)
        )
        out = Image.alpha_composite(img, overlay).convert("RGB")
        buf = io.BytesIO()
        out.save(buf, format="JPEG", quality=90)
        return buf.getvalue()
    except HTTPException:
        raise
    except Exception as exc:
        _fail_closed("image", exc)


def _watermark_pdf(pdf_bytes: bytes, text: str) -> bytes:
    """Fail-closed PDF watermark: every page must receive overlay or abort entirely."""
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception as exc:
        _fail_closed("pdf_read", exc)

    if not reader.pages:
        _fail_closed("pdf_empty", ValueError("pdf_has_no_pages"))

    writer = PdfWriter()
    for page_index, page in enumerate(reader.pages):
        try:
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
        except Exception:
            w, h = letter
        try:
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=(w, h))
            c.setFillColorRGB(0.75, 0.15, 0.15)
            c.setFont("Helvetica-Bold", 11)
            c.saveState()
            c.translate(48, 56)
            c.rotate(28)
            c.drawString(0, 0, text)
            c.restoreState()
            c.save()
            packet.seek(0)
            overlay = PdfReader(packet)
            if not overlay.pages:
                raise RuntimeError("overlay_empty")
            page.merge_page(overlay.pages[0])
        except HTTPException:
            raise
        except Exception as exc:
            _fail_closed(f"pdf_page_{page_index}", exc)
        writer.add_page(page)

    try:
        out = io.BytesIO()
        writer.write(out)
        result = out.getvalue()
        if not result:
            raise RuntimeError("pdf_writer_empty")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        _fail_closed("pdf_write", exc)
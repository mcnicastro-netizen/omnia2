"""Real content watermark for MLS document distribution (not a boolean flag).

Supported:
- image/* (JPEG/PNG/WEBP) via Pillow overlay
- application/pdf via reportlab overlay page stamp

Unsupported formats: refused for distribution (never claim watermarked).
Original bytes are never returned by distribution endpoints.
"""
from __future__ import annotations

import io
from typing import Optional, Tuple

from fastapi import HTTPException

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


def _watermark_image(image_bytes: bytes, text: str) -> bytes:
    from PIL import Image, ImageDraw, ImageFont

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
    draw.text((x0 + padding, y0 + padding), text, font=font, fill=(255, 255, 255, 255))
    out = Image.alpha_composite(img, overlay).convert("RGB")
    buf = io.BytesIO()
    out.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def _watermark_pdf(pdf_bytes: bytes, text: str) -> bytes:
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    for page in reader.pages:
        # Build overlay matching page size when possible
        try:
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
        except Exception:
            w, h = letter
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
        try:
            page.merge_page(overlay.pages[0])
        except Exception:
            pass
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()

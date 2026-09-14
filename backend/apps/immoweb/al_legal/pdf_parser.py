"""PDF text extraction for AL Legal document analysis.

Server-side only. Files are NOT persisted to disk; they are streamed
into memory, parsed with pypdf, and discarded.
"""
from __future__ import annotations

import io
import logging
from typing import Tuple

logger = logging.getLogger("omnia.legal.pdf")

MAX_PDF_BYTES = 5 * 1024 * 1024        # 5 MB hard cap
MAX_PAGES = 60                          # cap pages parsed
MAX_TEXT_CHARS = 40_000                 # cap text sent to LLM


def extract_text_from_pdf(pdf_bytes: bytes) -> Tuple[str, int]:
    """Return (text, page_count). Raises ValueError on invalid PDF or oversize."""
    if not pdf_bytes:
        raise ValueError("empty_file")
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise ValueError("file_too_large")

    try:
        from pypdf import PdfReader
    except ImportError as e:
        logger.error("pypdf not installed: %s", e)
        raise ValueError("pdf_library_missing")

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception as e:
        logger.warning("Invalid PDF: %s", e)
        raise ValueError("invalid_pdf")

    if reader.is_encrypted:
        # Try empty password (some PDFs ship with empty password protection)
        try:
            reader.decrypt("")
        except Exception:
            raise ValueError("encrypted_pdf")

    total_pages = len(reader.pages)
    pages_to_read = min(total_pages, MAX_PAGES)
    chunks = []
    for i in range(pages_to_read):
        try:
            txt = reader.pages[i].extract_text() or ""
        except Exception:
            txt = ""
        if txt.strip():
            chunks.append(f"--- Pagina {i + 1} ---\n{txt.strip()}")
        if sum(len(c) for c in chunks) >= MAX_TEXT_CHARS:
            break

    full_text = "\n\n".join(chunks)
    if not full_text.strip():
        raise ValueError("no_text_extracted")  # likely scanned PDF without OCR
    return full_text[:MAX_TEXT_CHARS], total_pages

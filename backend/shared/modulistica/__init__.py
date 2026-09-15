"""OMNIA Modulistica AI (M5.S7) + e-sign adapter (M5.S8).

Agency CRM document templates, white-label branded PDF generation,
and electronic signature via external providers (Yousign / DocuSign).

Anti-wedge (D-042): we do NOT build proprietary QES — we integrate
DocuSign/Yousign. Mock provider enables end-to-end demo without paid accounts.
"""
from shared.modulistica.catalog import TEMPLATES, list_templates, get_template
from shared.modulistica.pdf import render_modulistica_pdf
from shared.modulistica.esign import get_esign_provider, ESignResult

__all__ = [
    "TEMPLATES",
    "list_templates",
    "get_template",
    "render_modulistica_pdf",
    "get_esign_provider",
    "ESignResult",
]

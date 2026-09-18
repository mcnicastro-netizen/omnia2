#!/usr/bin/env python3
"""Generate sample valuation PDFs (OMNIA + white-label) for visual QA."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "/workspace/backend")

from apps.immocloud.valuation_pdf import OMNIA_BRAND, build_valuation_pdf
from apps.immocloud.valuator import ValuationPayload
from tests.test_valuation_pdf_branding import _payload, _sample_result

OUT = Path("/opt/cursor/artifacts/valuator-pdf")
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    payload = _payload()
    result = _sample_result()

    omnia = build_valuation_pdf(result, payload, branding=dict(OMNIA_BRAND))
    (OUT / "report-omnia-immobilcloud.pdf").write_bytes(omnia)

    wl = build_valuation_pdf(
        result,
        payload,
        branding={
            "name": "Nicastro Immobiliare",
            "tagline": "Acquisizione e consulenza sul territorio",
            "primary_color": "#1A3328",
            "accent_color": "#B08D57",
            "email": "info@nicastro.example",
            "phone": "+39 02 1234 5678",
            "website": "www.nicastro.example",
            "plan_type": "whitelabel",
        },
    )
    (OUT / "report-whitelabel-agenzia.pdf").write_bytes(wl)

    hybrid = build_valuation_pdf(
        result,
        payload,
        branding={
            "name": "Studio Lago",
            "tagline": "Immobili sul Lago di Como",
            "primary_color": "#0B1E3F",
            "accent_color": "#1F6B5C",
            "plan_type": "hybrid",
        },
    )
    (OUT / "report-hybrid-agenzia.pdf").write_bytes(hybrid)

    print("WROTE", OUT)
    for p in sorted(OUT.glob("*.pdf")):
        print(f"  {p.name}  {p.stat().st_size} bytes")


if __name__ == "__main__":
    main()

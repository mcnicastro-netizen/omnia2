"""Unit tests — Modulistica M5.S7 + e-sign adapter M5.S8."""
import asyncio
import os

import pytest


class TestModulisticaCatalog:
    def test_seven_templates(self):
        from shared.modulistica.catalog import TEMPLATES, list_templates
        assert len(TEMPLATES) >= 7
        slugs = {t["slug"] for t in list_templates()}
        assert "proposta_acquisto" in slugs
        assert "mandato_vendita" in slugs
        assert "mandato_locazione" in slugs
        assert "preliminare" in slugs
        assert "informativa_privacy" in slugs

    def test_list_has_no_section_bodies(self):
        from shared.modulistica.catalog import list_templates
        for t in list_templates():
            assert "sections" not in t
            assert "fields" in t


class TestModulisticaPDF:
    def test_render_pdf_magic(self):
        from shared.modulistica.pdf import render_modulistica_pdf
        pdf = render_modulistica_pdf(
            "proposta_acquisto",
            {"agency_name": "Nicastro Immobiliare", "buyer_name": "Mario Rossi"},
            branding={"primary_color": "#0B1E3F", "accent_color": "#1F6B5C", "display_name": "Nicastro Immobiliare"},
            plan_type="hybrid",
        )
        assert pdf.startswith(b"%PDF-")
        assert len(pdf) > 1500

    def test_all_slugs_render(self):
        from shared.modulistica.catalog import TEMPLATES
        from shared.modulistica.pdf import render_modulistica_pdf
        for slug in TEMPLATES:
            pdf = render_modulistica_pdf(slug, {"agency_name": "Test Agency SRL"})
            assert pdf.startswith(b"%PDF-"), slug

    def test_whitelabel_differs_from_hybrid_footer(self):
        from shared.modulistica.pdf import render_modulistica_pdf
        ctx = {"agency_name": "Brand Agency"}
        branding = {"primary_color": "#112233", "accent_color": "#445566", "display_name": "Brand Agency"}
        a = render_modulistica_pdf("informativa_privacy", ctx, branding=branding, plan_type="whitelabel")
        b = render_modulistica_pdf("informativa_privacy", ctx, branding=branding, plan_type="hybrid")
        # Different footers → different bytes
        assert a != b

    def test_missing_slug_raises(self):
        from shared.modulistica.pdf import render_modulistica_pdf
        with pytest.raises(KeyError):
            render_modulistica_pdf("no_such_template", {})


class TestESignAdapter:
    def test_default_is_mock(self, monkeypatch):
        monkeypatch.delenv("ESIGN_PROVIDER", raising=False)
        monkeypatch.delenv("YOUSIGN_API_KEY", raising=False)
        from shared.modulistica.esign import get_esign_provider
        assert get_esign_provider().name == "mock"

    def test_mock_send(self):
        from shared.modulistica.esign import MockESignProvider
        provider = MockESignProvider()
        result = asyncio.run(
            provider.create_signature_request(
                pdf_bytes=b"%PDF-1.4 mock",
                filename="test.pdf",
                document_name="Proposta",
                signers=[{"name": "Mario", "email": "mario@example.com"}],
            )
        )
        assert result.ok
        assert result.status == "sent"
        assert result.external_id.startswith("mock_")
        assert result.sign_url

    def test_yousign_falls_back_without_key(self, monkeypatch):
        monkeypatch.setenv("ESIGN_PROVIDER", "yousign")
        monkeypatch.delenv("YOUSIGN_API_KEY", raising=False)
        from shared.modulistica.esign import get_esign_provider
        assert get_esign_provider().name == "mock"

"""Electronic signature adapter (M5.S8) — D-042 anti-wedge.

Decision (PROGRAMMA + D-042): integrate DocuSign / Yousign.
Do NOT build proprietary FEA/FEQ. Namirial/Aruba remain backlog alternatives.

Providers:
  - mock     — local demo: marks document signed, stores audit (default)
  - yousign  — EU provider (preferred for IT) when YOUSIGN_API_KEY is set
  - docusign — when DOCUSIGN_* credentials are set

Env:
  ESIGN_PROVIDER=mock|yousign|docusign
  YOUSIGN_API_KEY=
  YOUSIGN_API_BASE=https://api-sandbox.yousign.app/v3
  DOCUSIGN_ACCESS_TOKEN=
  DOCUSIGN_ACCOUNT_ID=
  DOCUSIGN_BASE_URL=https://demo.docusign.net/restapi
"""
from __future__ import annotations
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger("omnia.esign")


@dataclass
class ESignResult:
    ok: bool
    provider: str
    external_id: str
    status: str  # draft | sent | signed | failed
    sign_url: Optional[str] = None
    message: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)


class BaseESignProvider:
    name = "base"

    async def create_signature_request(
        self,
        *,
        pdf_bytes: bytes,
        filename: str,
        document_name: str,
        signers: List[Dict[str, str]],
        callback_url: Optional[str] = None,
    ) -> ESignResult:
        raise NotImplementedError


class MockESignProvider(BaseESignProvider):
    """Demo provider — no external network. Marks flow as sent with a fake URL."""

    name = "mock"

    async def create_signature_request(
        self,
        *,
        pdf_bytes: bytes,
        filename: str,
        document_name: str,
        signers: List[Dict[str, str]],
        callback_url: Optional[str] = None,
    ) -> ESignResult:
        ext_id = f"mock_{uuid4().hex[:16]}"
        # First signer gets a fake signing URL for UI demos
        first = signers[0] if signers else {}
        email = first.get("email") or "firmatario@example.com"
        return ESignResult(
            ok=True,
            provider="mock",
            external_id=ext_id,
            status="sent",
            sign_url=f"https://sign.omnia.local/mock/{ext_id}?email={email}",
            message=(
                "Firma simulata (ESIGN_PROVIDER=mock). "
                "Collega YOUSIGN_API_KEY o DocuSign per firme reali."
            ),
            raw={
                "signers": signers,
                "filename": filename,
                "document_name": document_name,
                "pdf_size": len(pdf_bytes),
                "callback_url": callback_url,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def mark_signed(self, external_id: str) -> ESignResult:
        return ESignResult(
            ok=True,
            provider="mock",
            external_id=external_id,
            status="signed",
            message="Documento contrassegnato come firmato (mock).",
        )


class YousignProvider(BaseESignProvider):
    """Yousign API v3 — sandbox/production via YOUSIGN_API_BASE."""

    name = "yousign"

    def __init__(self) -> None:
        self.api_key = (os.environ.get("YOUSIGN_API_KEY") or "").strip()
        self.base = (os.environ.get("YOUSIGN_API_BASE") or "https://api-sandbox.yousign.app/v3").rstrip("/")
        if not self.api_key:
            raise RuntimeError("YOUSIGN_API_KEY missing")

    async def create_signature_request(
        self,
        *,
        pdf_bytes: bytes,
        filename: str,
        document_name: str,
        signers: List[Dict[str, str]],
        callback_url: Optional[str] = None,
    ) -> ESignResult:
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                # 1) Create signature request
                payload: Dict[str, Any] = {
                    "name": document_name[:255],
                    "delivery_mode": "email",
                    "timezone": "Europe/Rome",
                }
                if callback_url:
                    payload["custom_experience_id"] = None  # reserved
                r = await client.post(
                    f"{self.base}/signature_requests",
                    headers={**headers, "Content-Type": "application/json"},
                    json=payload,
                )
                if r.status_code >= 400:
                    return ESignResult(
                        ok=False, provider="yousign", external_id="",
                        status="failed",
                        message=f"Yousign create failed: {r.status_code} {r.text[:300]}",
                    )
                sr = r.json()
                sr_id = sr.get("id") or ""

                # 2) Upload document
                files = {"file": (filename, pdf_bytes, "application/pdf")}
                data = {"nature": "signable_document"}
                r2 = await client.post(
                    f"{self.base}/signature_requests/{sr_id}/documents",
                    headers=headers,
                    files=files,
                    data=data,
                )
                if r2.status_code >= 400:
                    return ESignResult(
                        ok=False, provider="yousign", external_id=sr_id,
                        status="failed",
                        message=f"Yousign upload failed: {r2.status_code} {r2.text[:300]}",
                    )
                doc = r2.json() if r2.content else {}
                doc_id = doc.get("id") or ""
                # Prefer last page for signature block (modulistica PDFs are usually 1 page)
                page_count = int(doc.get("total_pages") or doc.get("pages") or 1)

                # 3) Add signers + required signature field per signer
                for idx, s in enumerate(signers):
                    name = (s.get("name") or "").strip()
                    first = (s.get("first_name") or (name.split()[0] if name else "Firmatario"))[:50]
                    last = (s.get("last_name") or (" ".join(name.split()[1:]) if name and " " in name else "."))[:50]
                    signer_body = {
                        "info": {
                            "first_name": first,
                            "last_name": last or ".",
                            "email": s.get("email") or "",
                            "locale": "it",
                        },
                        "signature_level": "electronic_signature",
                        "signature_authentication_mode": "otp_email",
                        # Yousign v3: origin = top-left of page (A4 ≈ 595×842 pt).
                        # Place signature block near the bottom, not under the header.
                        "fields": [
                            {
                                "document_id": doc_id,
                                "type": "signature",
                                "page": max(1, page_count),
                                "x": 72,
                                "y": 720 + (idx * 56),
                                "width": 200,
                                "height": 50,
                            }
                        ],
                    }
                    r3 = await client.post(
                        f"{self.base}/signature_requests/{sr_id}/signers",
                        headers={**headers, "Content-Type": "application/json"},
                        json=signer_body,
                    )
                    if r3.status_code >= 400:
                        return ESignResult(
                            ok=False, provider="yousign", external_id=sr_id,
                            status="failed",
                            message=f"Yousign signer failed: {r3.status_code} {r3.text[:300]}",
                        )

                # 4) Activate
                r4 = await client.post(
                    f"{self.base}/signature_requests/{sr_id}/activate",
                    headers=headers,
                )
                if r4.status_code >= 400:
                    return ESignResult(
                        ok=False, provider="yousign", external_id=sr_id,
                        status="failed",
                        message=f"Yousign activate failed: {r4.status_code} {r4.text[:300]}",
                    )
                activated = r4.json() if r4.content else {}
                sign_url = None
                for signer in (activated.get("signers") or []):
                    if signer.get("signature_link"):
                        sign_url = signer["signature_link"]
                        break

                return ESignResult(
                    ok=True,
                    provider="yousign",
                    external_id=sr_id,
                    status="sent",
                    sign_url=sign_url,
                    message="Richiesta firma Yousign inviata.",
                    raw=activated or sr,
                )
        except Exception as e:
            logger.exception("Yousign request failed")
            return ESignResult(
                ok=False, provider="yousign", external_id="",
                status="failed", message=str(e)[:400],
            )


class DocuSignProvider(BaseESignProvider):
    """Minimal DocuSign REST envelope create (JWT/token must be pre-provisioned)."""

    name = "docusign"

    def __init__(self) -> None:
        self.token = (os.environ.get("DOCUSIGN_ACCESS_TOKEN") or "").strip()
        self.account_id = (os.environ.get("DOCUSIGN_ACCOUNT_ID") or "").strip()
        self.base = (os.environ.get("DOCUSIGN_BASE_URL") or "https://demo.docusign.net/restapi").rstrip("/")
        if not self.token or not self.account_id:
            raise RuntimeError("DOCUSIGN_ACCESS_TOKEN / DOCUSIGN_ACCOUNT_ID missing")

    async def create_signature_request(
        self,
        *,
        pdf_bytes: bytes,
        filename: str,
        document_name: str,
        signers: List[Dict[str, str]],
        callback_url: Optional[str] = None,
    ) -> ESignResult:
        import base64
        import httpx

        docs = [{
            "documentBase64": base64.b64encode(pdf_bytes).decode("ascii"),
            "name": filename,
            "fileExtension": "pdf",
            "documentId": "1",
        }]
        recipients = {"signers": []}
        for i, s in enumerate(signers, start=1):
            recipients["signers"].append({
                "email": s.get("email") or "",
                "name": s.get("name") or f"{s.get('first_name', '')} {s.get('last_name', '')}".strip() or "Firmatario",
                "recipientId": str(i),
                "routingOrder": str(i),
                "tabs": {
                    "signHereTabs": [{"documentId": "1", "pageNumber": "1", "xPosition": "100", "yPosition": "700"}]
                },
            })
        envelope = {
            "emailSubject": document_name[:100],
            "documents": docs,
            "recipients": recipients,
            "status": "sent",
        }
        if callback_url:
            envelope["eventNotification"] = {"url": callback_url, "loggingEnabled": "true"}

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                r = await client.post(
                    f"{self.base}/v2.1/accounts/{self.account_id}/envelopes",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json",
                    },
                    json=envelope,
                )
                if r.status_code >= 400:
                    return ESignResult(
                        ok=False, provider="docusign", external_id="",
                        status="failed",
                        message=f"DocuSign failed: {r.status_code} {r.text[:300]}",
                    )
                data = r.json()
                return ESignResult(
                    ok=True,
                    provider="docusign",
                    external_id=data.get("envelopeId") or "",
                    status="sent",
                    sign_url=None,
                    message="Busta DocuSign inviata ai firmatari via email.",
                    raw=data,
                )
        except Exception as e:
            logger.exception("DocuSign request failed")
            return ESignResult(
                ok=False, provider="docusign", external_id="",
                status="failed", message=str(e)[:400],
            )


def get_esign_provider() -> BaseESignProvider:
    """Resolve provider from ESIGN_PROVIDER env (default mock)."""
    name = (os.environ.get("ESIGN_PROVIDER") or "mock").strip().lower()
    if name == "yousign":
        try:
            return YousignProvider()
        except RuntimeError as e:
            logger.warning("Yousign unavailable (%s) — falling back to mock", e)
            return MockESignProvider()
    if name == "docusign":
        try:
            return DocuSignProvider()
        except RuntimeError as e:
            logger.warning("DocuSign unavailable (%s) — falling back to mock", e)
            return MockESignProvider()
    return MockESignProvider()

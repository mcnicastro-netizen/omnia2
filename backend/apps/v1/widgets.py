"""OMNIA — Track B Widget assets (M2.5.3 D-041/D-046/D-049).

Serves the embeddable widget HTML pages and the loader JS.
These are single-file static-ish assets rendered from Python (so they can
inject the backend URL at request time without needing a build step).

Endpoints:
    GET /api/widgets/v1/loader.js         → auto-embed script for clients
    GET /api/widgets/v1/{widget}.html     → the widget UI (iframe target)

Widgets available in this sprint (D-049 approvazione 1b):
    valuator, mortgages, staging (M2.5.3 gap #3, D-058b), legal (M2.5.3 gap #3, D-058b)
"""
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, Response

router = APIRouter(prefix="/widgets/v1", tags=["widgets"])

ASSETS_DIR = Path(__file__).parent / "assets"


def _backend_base(request: Request) -> str:
    """Return the base URL to reach the OMNIA backend as seen by the client.

    Priority: explicit `PUBLIC_BASE_URL` env → forwarded headers set by the
    ingress (host + proto) → request base URL (fallback for local dev).
    """
    explicit = os.environ.get("PUBLIC_BASE_URL")
    if explicit:
        return explicit.rstrip("/")
    fwd_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    fwd_proto = request.headers.get("x-forwarded-proto", "https")
    if fwd_host and "cluster-" not in fwd_host:
        return f"{fwd_proto}://{fwd_host}".rstrip("/")
    return str(request.base_url).rstrip("/")


@router.get("/loader.js", response_class=Response)
async def loader_js(request: Request) -> Response:
    """
    Client snippet installer. Usage in the customer's site:

        <script src="https://.../api/widgets/v1/loader.js"
                data-key="omk_live_..."
                data-widget="valuator"
                data-primary="#0b1e3f"
                data-lang="it"></script>
    """
    path = ASSETS_DIR / "loader.js"
    js = path.read_text(encoding="utf-8")
    js = js.replace("__BACKEND_BASE__", _backend_base(request))
    return Response(content=js, media_type="application/javascript; charset=utf-8",
                    headers={"Cache-Control": "public, max-age=300"})


@router.get("/{widget}.html", response_class=HTMLResponse)
async def widget_page(widget: str, request: Request,
                      key: Optional[str] = None,
                      primary: Optional[str] = None,
                      lang: str = "it") -> HTMLResponse:
    """Serve a single-file widget HTML. Query params: key, primary color, lang."""
    if widget not in {"valuator", "mortgages", "domain-check", "staging", "legal"}:
        raise HTTPException(status_code=404, detail="widget_not_found")

    path = ASSETS_DIR / f"{widget}.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="widget_asset_missing")

    html = path.read_text(encoding="utf-8")
    html = (
        html
        .replace("__BACKEND_BASE__", _backend_base(request))
        .replace("__PRIMARY_COLOR__", (primary or "#0b1e3f")[:7])
        .replace("__API_KEY__", (key or "")[:80])
        .replace("__LANG__", "it" if lang not in {"it", "en", "es"} else lang)
    )
    # Iframes MUST allow embedding — override any default X-Frame-Options
    return HTMLResponse(
        content=html,
        headers={
            "X-Frame-Options": "ALLOWALL",  # legacy — some browsers still read it
            "Content-Security-Policy": "frame-ancestors *",
            "Cache-Control": "public, max-age=60",
        },
    )

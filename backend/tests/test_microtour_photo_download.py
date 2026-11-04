"""Ken Burns photo download: Object Storage media paths must not rely on HTTP loopback."""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch

from apps.immoweb.micro_tour_video import _download_photo, _property_photo_urls


def test_download_media_path_uses_objstore():
    async def _run():
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "out.jpg"
            fake = b"JPEG" + b"x" * 800
            with patch("shared.storage.objstore.get_object", return_value=(fake, "image/jpeg")):
                ok = await _download_photo("/api/media/omnia/private/u/photos/a.jpg", dest)
            assert ok is True
            assert dest.read_bytes() == fake

    asyncio.run(_run())


def test_property_photo_urls_prefers_media_and_public_fallback():
    prop = {
        "id": "pid-1",
        "photos": [
            {"url": "/api/media/omnia/private/u/photos/a.jpg"},
            {"url": ""},
            {"url": "https://cdn.example/x.jpg"},
        ],
    }
    urls = _property_photo_urls(prop, "https://api.example.com")
    assert urls[0] == "/api/media/omnia/private/u/photos/a.jpg"
    assert urls[1] == "https://api.example.com/api/public/property/pid-1/photo/1"
    assert urls[2] == "https://cdn.example/x.jpg"

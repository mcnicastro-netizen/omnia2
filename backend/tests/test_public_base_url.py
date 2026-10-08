"""P-019 — public base URL prefers live tunnel over localhost env."""
from pathlib import Path

import shared.public_base as pb


def test_prefers_share_file_over_localhost(tmp_path, monkeypatch):
    share = tmp_path / "SHARE_URL.txt"
    share.write_text("https://demo-tunnel.trycloudflare.com\n")
    monkeypatch.setattr(pb, "_SHARE_CANDIDATES", (share,))
    monkeypatch.setenv("FRONTEND_BASE_URL", "http://127.0.0.1:43122")
    monkeypatch.setenv("FRONTEND_URL", "http://127.0.0.1:43122")
    monkeypatch.setenv("OMNIA_PUBLIC_URL", "http://127.0.0.1:43122")
    assert pb.get_public_base_url() == "https://demo-tunnel.trycloudflare.com"


def test_falls_back_to_non_local_env(monkeypatch):
    monkeypatch.setattr(pb, "_SHARE_CANDIDATES", (Path("/tmp/does-not-exist-omnia.txt"),))
    monkeypatch.setenv("FRONTEND_BASE_URL", "https://example.omnia.test")
    monkeypatch.delenv("FRONTEND_URL", raising=False)
    monkeypatch.delenv("OMNIA_PUBLIC_URL", raising=False)
    assert pb.get_public_base_url() == "https://example.omnia.test"

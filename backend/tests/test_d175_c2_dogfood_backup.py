"""D-175 C2 — unit tests for dogfood backup safety + scope helpers."""
from __future__ import annotations

from pathlib import Path

import pytest

from shared.dogfood.backup import (
    assert_dogfood_mongo_endpoint,
    assert_dogfood_mongo_port,
    assert_safe_db_name,
    authorized_dogfood_mongo_endpoints,
    backup_media,
    redact_mongo_uri,
    sha256_tree,
)


def test_c2_deny_restore_to_shared_omnia():
    with pytest.raises(RuntimeError) as ei:
        assert_safe_db_name("omnia", role="target_probe")
    assert "forbidden" in str(ei.value) or "probe" in str(ei.value)


def test_c2_deny_restore_to_permanent_prefix():
    with pytest.raises(RuntimeError) as ei:
        assert_safe_db_name("omnia_df_perm_main", role="target_probe")
    assert "permanent" in str(ei.value) or "probe" in str(ei.value)


def test_c2_probe_target_ok():
    assert assert_safe_db_name("omnia_df_probe_c2", role="target_probe") == "omnia_df_probe_c2"


def test_c2_source_must_be_dogfood_prefix():
    with pytest.raises(RuntimeError):
        assert_safe_db_name("omnia", role="source")
    assert assert_safe_db_name("omnia_df_c2_src", role="source")


def test_c2_redact_mongo_uri_strips_userinfo():
    red = redact_mongo_uri("mongodb://user:secret@127.0.0.1:27018/admin")
    assert "secret" not in red
    assert "user" not in red
    assert "127.0.0.1" in red


def test_c2_sha256_tree_empty(tmp_path):
    inv = sha256_tree(tmp_path)
    assert inv["file_count"] == 0
    assert len(inv["tree_sha256"]) == 64


def test_c2_endpoint_allows_authorized_loopback_27018(monkeypatch):
    monkeypatch.delenv("OMNIA_DOGFOOD_MONGO_ENDPOINTS", raising=False)
    monkeypatch.setenv("OMNIA_DF_MONGO_PORT", "27018")
    host, port = assert_dogfood_mongo_endpoint(
        "mongodb://omnia_df_admin:x@127.0.0.1:27018/?authSource=admin"
    )
    assert host == "127.0.0.1"
    assert port == 27018


def test_c2_endpoint_denies_shared_27017_even_without_db_path(monkeypatch):
    """Critical: host:port must be checked even when URI has no DB in path."""
    monkeypatch.delenv("OMNIA_DOGFOOD_MONGO_ENDPOINTS", raising=False)
    monkeypatch.setenv("OMNIA_DF_MONGO_PORT", "27018")
    with pytest.raises(RuntimeError) as ei:
        assert_dogfood_mongo_endpoint("mongodb://127.0.0.1:27017/")
    err = str(ei.value)
    assert "mongo_port_forbidden_shared" in err or "mongo_endpoint_not_allowed" in err


def test_c2_hard_deny_when_omnia_df_mongo_port_is_27017(monkeypatch):
    """Misconfig must NOT authorize shared Cloud mongod."""
    monkeypatch.delenv("OMNIA_DOGFOOD_MONGO_ENDPOINTS", raising=False)
    monkeypatch.setenv("OMNIA_DF_MONGO_PORT", "27017")
    with pytest.raises(RuntimeError) as ei:
        authorized_dogfood_mongo_endpoints()
    assert "mongo_port_forbidden_shared" in str(ei.value)
    with pytest.raises(RuntimeError) as ei2:
        assert_dogfood_mongo_endpoint("mongodb://127.0.0.1:27017/")
    assert "mongo_port_forbidden_shared" in str(ei2.value)


def test_c2_hard_deny_27017_in_explicit_endpoints_override(monkeypatch):
    monkeypatch.setenv("OMNIA_DOGFOOD_MONGO_ENDPOINTS", "127.0.0.1:27017")
    with pytest.raises(RuntimeError) as ei:
        authorized_dogfood_mongo_endpoints()
    assert "mongo_port_forbidden_shared" in str(ei.value)


def test_c2_hard_deny_non_loopback_in_endpoints_override(monkeypatch):
    monkeypatch.setenv("OMNIA_DOGFOOD_MONGO_ENDPOINTS", "mongo.example.com:27018")
    with pytest.raises(RuntimeError) as ei:
        authorized_dogfood_mongo_endpoints()
    assert "mongo_host_not_loopback" in str(ei.value)


def test_c2_assert_dogfood_mongo_port_rejects_27017():
    with pytest.raises(RuntimeError) as ei:
        assert_dogfood_mongo_port(27017)
    assert "mongo_port_forbidden_shared" in str(ei.value)
    assert assert_dogfood_mongo_port(27018) == 27018


def test_c2_endpoint_denies_remote_host_no_db_path(monkeypatch):
    monkeypatch.setenv("OMNIA_DF_MONGO_PORT", "27018")
    monkeypatch.delenv("OMNIA_DOGFOOD_MONGO_ENDPOINTS", raising=False)
    with pytest.raises(RuntimeError) as ei:
        assert_dogfood_mongo_endpoint("mongodb://mongo.example.com:27018/")
    err = str(ei.value)
    assert "mongo_host_not_loopback" in err or "mongo_endpoint_not_allowed" in err


def test_c2_endpoint_denies_wrong_port_on_loopback(monkeypatch):
    monkeypatch.setenv("OMNIA_DF_MONGO_PORT", "27018")
    monkeypatch.delenv("OMNIA_DOGFOOD_MONGO_ENDPOINTS", raising=False)
    with pytest.raises(RuntimeError) as ei:
        assert_dogfood_mongo_endpoint("mongodb://127.0.0.1:27019/?authSource=admin")
    assert "mongo_endpoint_not_allowed" in str(ei.value)


def test_c2_endpoint_explicit_allowlist(monkeypatch):
    monkeypatch.setenv("OMNIA_DOGFOOD_MONGO_ENDPOINTS", "127.0.0.1:27018")
    assert_dogfood_mongo_endpoint("mongodb://127.0.0.1:27018/")
    with pytest.raises(RuntimeError):
        assert_dogfood_mongo_endpoint("mongodb://localhost:27018/")


def test_c2_media_missing_is_blocking(tmp_path, monkeypatch):
    monkeypatch.delenv("OMNIA_DOGFOOD_ALLOW_MISSING_MEDIA", raising=False)
    src = tmp_path / "nope"
    dest = tmp_path / "bak"
    report = backup_media(src, dest)
    assert report["ok"] is False
    assert report["copied"] is False
    assert "media_src_missing" in report["anomalies"]


def test_c2_media_missing_allowed_only_with_explicit_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("OMNIA_DOGFOOD_ALLOW_MISSING_MEDIA", "1")
    src = tmp_path / "nope"
    dest = tmp_path / "bak"
    report = backup_media(src, dest)
    assert report["ok"] is True
    assert report["copied"] is False
    assert any("ALLOW_MISSING" in a for a in report["anomalies"])


def test_c2_media_present_copies(tmp_path, monkeypatch):
    monkeypatch.delenv("OMNIA_DOGFOOD_ALLOW_MISSING_MEDIA", raising=False)
    src = tmp_path / "media_src"
    src.mkdir()
    (src / "f.txt").write_text("x\n", encoding="utf-8")
    dest = tmp_path / "bak"
    report = backup_media(src, dest)
    assert report["ok"] is True
    assert report["copied"] is True
    assert (dest / "media" / "f.txt").is_file()

"""D-175 C3 — permanent base protection unit tests (T1–T13 gates)."""
from __future__ import annotations

import json

import pytest

from shared.dogfood.ordinary_ops import (
    ordinary_clone_allowed,
    ordinary_migrate_destructive_allowed,
    ordinary_restore_allowed,
    ordinary_wipe_allowed,
)
from shared.dogfood.permanent import (
    REQUIRED_AUTH_PHRASE,
    REQUIRED_CONFIRM_TOKEN,
    append_emergency_audit,
    build_identity_payload,
    check_emergency_unlock_gates,
    is_permanent_db_name,
    is_permanent_runtime_target,
    is_permanent_target,
)


@pytest.fixture()
def perm_env(monkeypatch, tmp_path):
    monkeypatch.setenv("DOGFOOD_ROOT", str(tmp_path))
    monkeypatch.setenv("OMNIA_DOGFOOD_PERMANENT_DB", "omnia_df_perm_main")
    monkeypatch.setenv(
        "OMNIA_DOGFOOD_PERMANENT_URI", "mongodb://127.0.0.1:27018/omnia_df_perm_main"
    )
    monkeypatch.setenv("OMNIA_DF_MONGO_PORT", "27018")
    (tmp_path / "permanent").mkdir(parents=True)
    return tmp_path


@pytest.fixture()
def dogfood_like(monkeypatch):
    monkeypatch.setenv("OMNIA_ENV", "dogfood")
    monkeypatch.setenv("OMNIA_DOGFOOD_ALLOWED_API_HOSTS", "127.0.0.1")
    monkeypatch.setenv("OMNIA_DOGFOOD_ALLOWED_FE_HOSTS", "127.0.0.1")
    monkeypatch.setenv("OMNIA_DF_MONGO_PORT", "27018")


def test_c3_permanent_db_name_detection():
    assert is_permanent_db_name("omnia_df_perm_main")
    assert is_permanent_db_name("omnia_df_permanent_x")
    assert not is_permanent_db_name("omnia_df_clean_a")
    assert not is_permanent_db_name("omnia_df_probe_c2")
    assert not is_permanent_db_name("omnia_df_c2_src")


def test_c3_t1_runtime_permanent_db_denied(dogfood_like, monkeypatch):
    from shared.dogfood import perimeter as p

    monkeypatch.setenv("DB_NAME", "omnia_df_perm_main")
    monkeypatch.setenv("MONGO_URL", "mongodb://127.0.0.1:27018/omnia_df_perm_main")
    monkeypatch.setenv(
        "OMNIA_DOGFOOD_PERMANENT_URI", "mongodb://127.0.0.1:27018/omnia_df_perm_main"
    )
    r = p.check_dogfood_db_isolation()
    assert r["ok"] is False
    assert "db_name_is_permanent" in r["errors"] or "mongo_url_is_permanent" in r["errors"]


def test_c3_t2_alternate_uri_same_permanent_denied(dogfood_like, monkeypatch):
    from shared.dogfood import perimeter as p

    alt = (
        "mongodb://omnia_df_runtime:x@127.0.0.1:27018/omnia_df_perm_main?authSource=admin"
    )
    monkeypatch.setenv("DB_NAME", "omnia_df_perm_main")
    monkeypatch.setenv("MONGO_URL", alt)
    monkeypatch.setenv(
        "OMNIA_DOGFOOD_PERMANENT_URI", "mongodb://127.0.0.1:27018/omnia_df_perm_main"
    )
    assert is_permanent_runtime_target(mongo_url=alt, db_name="omnia_df_perm_main")
    r = p.check_dogfood_db_isolation()
    assert r["ok"] is False


def test_c3_t3_clone_to_permanent_denied():
    r = ordinary_clone_allowed(
        source_uri="mongodb://127.0.0.1:27018/", target_db="omnia_df_perm_main"
    )
    assert r["ok"] is False
    assert "permanent" in r["error"]


def test_c3_t4_wipe_permanent_denied():
    r = ordinary_wipe_allowed(uri="mongodb://127.0.0.1:27018/", db_name="omnia_df_perm_main")
    assert r["ok"] is False


def test_c3_t5_restore_permanent_denied():
    r = ordinary_restore_allowed(
        uri="mongodb://127.0.0.1:27018/", target_db="omnia_df_perm_main"
    )
    assert r["ok"] is False


def test_c3_t6_migrate_permanent_denied():
    r = ordinary_migrate_destructive_allowed(
        uri="mongodb://127.0.0.1:27018/", db_name="omnia_df_perm_main"
    )
    assert r["ok"] is False


def test_c3_t9_emergency_without_unlock_denied():
    g = check_emergency_unlock_gates(
        unlock_token="", auth_phrase="", confirm1="", confirm2=""
    )
    assert g["ok"] is False
    assert "unlock_missing" in g["errors"]


def test_c3_t10_wrong_phrase_denied():
    g = check_emergency_unlock_gates(
        unlock_token="1",
        auth_phrase="WRONG PHRASE",
        confirm1=REQUIRED_CONFIRM_TOKEN,
        confirm2=REQUIRED_CONFIRM_TOKEN,
    )
    assert g["ok"] is False
    assert "auth_phrase_mismatch" in g["errors"]


def test_c3_t11_confirm_incomplete_denied():
    g = check_emergency_unlock_gates(
        unlock_token="1",
        auth_phrase=REQUIRED_AUTH_PHRASE,
        confirm1=REQUIRED_CONFIRM_TOKEN,
        confirm2="",
    )
    assert g["ok"] is False
    assert "confirm2_incomplete" in g["errors"]


def test_c3_t12_audit_append_only(perm_env):
    p1 = append_emergency_audit({"event": "test_a", "result": "DENY"})
    p2 = append_emergency_audit({"event": "test_b", "result": "PASS"})
    assert p1 == p2
    lines = p1.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 2
    assert json.loads(lines[0])["event"] == "test_a"
    assert json.loads(lines[1])["event"] == "test_b"


def test_c3_t13_ordinary_work_copy_allowed():
    r = ordinary_clone_allowed(
        source_uri="mongodb://127.0.0.1:27018/", target_db="omnia_df_clean_a"
    )
    assert r["ok"] is True
    r2 = ordinary_wipe_allowed(
        uri="mongodb://127.0.0.1:27018/", db_name="omnia_df_cont_a"
    )
    assert r2["ok"] is True


def test_c3_emergency_gates_all_ok():
    g = check_emergency_unlock_gates(
        unlock_token="1",
        auth_phrase=REQUIRED_AUTH_PHRASE,
        confirm1=REQUIRED_CONFIRM_TOKEN,
        confirm2=REQUIRED_CONFIRM_TOKEN,
    )
    assert g["ok"] is True


def test_c3_identity_builder_rejects_shared_port():
    with pytest.raises(RuntimeError):
        build_identity_payload(
            instance_id="x",
            db_name="omnia_df_perm_main",
            host="127.0.0.1",
            port=27017,
            git_sha="abc",
        )


def test_c3_is_permanent_target_by_uri(perm_env, monkeypatch):
    monkeypatch.setenv(
        "OMNIA_DOGFOOD_PERMANENT_URI", "mongodb://127.0.0.1:27018/omnia_df_perm_main"
    )
    assert is_permanent_target(uri="mongodb://127.0.0.1:27018/omnia_df_perm_main")
    assert not is_permanent_target(db_name="omnia_df_clean_a")


def test_c3_refuse_reinit_when_identity_exists(perm_env):
    from shared.dogfood.permanent import refuse_reinitialization_if_present, write_identity

    write_identity(
        build_identity_payload(
            instance_id="keep-me",
            db_name="omnia_df_perm_main",
            host="127.0.0.1",
            port=27018,
            git_sha="abc",
        )
    )
    with pytest.raises(RuntimeError) as ei:
        refuse_reinitialization_if_present()
    assert "permanent_already_initialized" in str(ei.value)


def test_c3_general_creds_must_not_contain_emergency():
    from shared.dogfood.permanent import assert_general_creds_have_no_emergency

    assert_general_creds_have_no_emergency({"admin": "x", "runtime": "y"})
    with pytest.raises(RuntimeError) as ei:
        assert_general_creds_have_no_emergency({"admin": "x", "emergency": "secret"})
    assert "emergency_password_must_not_live_in_general_creds" in str(ei.value)


def test_c3_require_identity_missing_fails(perm_env):
    from shared.dogfood.permanent import require_identity_or_raise

    with pytest.raises(RuntimeError) as ei:
        require_identity_or_raise()
    assert "permanent_identity_missing" in str(ei.value)


def test_c3_identity_fingerprint_stable():
    from shared.dogfood.permanent import identity_fingerprint

    ident = build_identity_payload(
        instance_id="id1",
        db_name="omnia_df_perm_main",
        host="127.0.0.1",
        port=27018,
        git_sha="sha",
    )
    fp1 = identity_fingerprint(ident)
    fp2 = identity_fingerprint(dict(ident))
    assert fp1 == fp2
    assert fp1["instance_id"] == "id1"

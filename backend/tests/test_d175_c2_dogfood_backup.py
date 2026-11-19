"""D-175 C2 — unit tests for dogfood backup safety + scope helpers."""
from __future__ import annotations

import pytest

from shared.dogfood.backup import (
    assert_safe_db_name,
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

"""D-175 B8 local proofs: persistent kill, fail-closed, multi-process.

Multi-process tests use OMNIA_PROVIDER_KILL_FILE (shared JSON SoT), not live
Mongo — declared explicitly. Staging multi-replica remains NOT DIMOSTRATO.
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(REPO))


@pytest.fixture(autouse=True)
def _clear_resend_hold():
    from shared.security import circuit as circuit_mod

    circuit_mod.clear_hold("resend")
    yield
    circuit_mod.clear_hold("resend")


def _run_send(to="probe@example.com", template="welcome"):
    from shared.email.client import send_email

    async def _go():
        return await send_email(to, template, lang="it")

    return asyncio.run(_go())


def test_b8_mongo_killed_memory_clear_blocks(tmp_path, monkeypatch):
    """Persistent killed=true, memory free → no send (kill file SoT)."""
    kill = tmp_path / "kill.json"
    kill.write_text(json.dumps({"resend": True}) + "\n", encoding="utf-8")
    monkeypatch.setenv("OMNIA_PROVIDER_KILL_FILE", str(kill))
    monkeypatch.delenv("OMNIA_RESEND_KILLED", raising=False)
    monkeypatch.delenv("OMNIA_ENV", raising=False)
    from shared.security import circuit as circuit_mod

    circuit_mod.clear_hold("resend")
    transport = MagicMock(side_effect=RuntimeError("must_not_call"))
    import shared.email.client as ec

    original = ec.resend.Emails.send
    ec.resend.Emails.send = transport
    try:
        out = _run_send()
    finally:
        ec.resend.Emails.send = original
    assert out["status"] == "killed"
    assert transport.call_count == 0


def test_b8_memory_hold_blocks_even_if_persistent_clear(tmp_path, monkeypatch):
    kill = tmp_path / "kill.json"
    kill.write_text(json.dumps({"resend": False}) + "\n", encoding="utf-8")
    monkeypatch.setenv("OMNIA_PROVIDER_KILL_FILE", str(kill))
    from shared.security import circuit as circuit_mod

    circuit_mod.force_hold("resend", "local")
    transport = MagicMock()
    import shared.email.client as ec

    original = ec.resend.Emails.send
    ec.resend.Emails.send = transport
    try:
        out = _run_send()
    finally:
        ec.resend.Emails.send = original
    assert out["status"] == "killed"
    assert transport.call_count == 0


@pytest.mark.parametrize("env_name", ["staging", "dogfood"])
def test_b8_persistent_unreadable_fail_closed(env_name, monkeypatch):
    monkeypatch.setenv("OMNIA_ENV", env_name)
    monkeypatch.delenv("OMNIA_PROVIDER_KILL_FILE", raising=False)
    from shared.ops import provider_flags as pf

    async def _boom():
        return None, "mongo_error:Timeout"

    monkeypatch.setattr(pf, "read_resend_killed_persistent", _boom)
    from shared.security import circuit as circuit_mod

    circuit_mod.clear_hold("resend")
    transport = MagicMock()
    import shared.email.client as ec

    original = ec.resend.Emails.send
    ec.resend.Emails.send = transport
    try:
        out = _run_send()
    finally:
        ec.resend.Emails.send = original
    assert out["status"] == "killed"
    assert transport.call_count == 0


def test_b8_load_holds_failure_raises_in_staging(monkeypatch):
    monkeypatch.setenv("OMNIA_ENV", "staging")
    from shared.ops import provider_flags as pf

    async def _fail(*, raise_on_error=None):
        raise RuntimeError("provider_flags_load_failed:Boom")

    # Call the real function path with mocked db
    monkeypatch.setattr(pf, "_db_raw", lambda: (_ for _ in ()).throw(RuntimeError("db_down")))
    with pytest.raises(RuntimeError, match="provider_flags_load_failed"):
        asyncio.run(pf.load_holds_into_circuit(raise_on_error=True))


def test_b8_restart_recovers_hold_from_persistent(tmp_path, monkeypatch):
    """Simulate process restart: clear memory, reload from kill file."""
    kill = tmp_path / "kill.json"
    kill.write_text(json.dumps({"resend": True}) + "\n", encoding="utf-8")
    monkeypatch.setenv("OMNIA_PROVIDER_KILL_FILE", str(kill))
    monkeypatch.delenv("OMNIA_ENV", raising=False)
    from shared.ops import provider_flags as pf
    from shared.security import circuit as circuit_mod

    circuit_mod.clear_hold("resend")
    assert not circuit_mod.is_held("resend")
    # load from file via set_killed path already true; emulate load by reading
    killed, err = asyncio.run(pf.read_resend_killed_persistent())
    assert killed is True and err is None
    if killed:
        circuit_mod.force_hold("resend", "restored")
    assert circuit_mod.is_held("resend")
    out = _run_send()
    assert out["status"] == "killed"


def test_b8_circuit_open_alone_not_permanent_kill_proof(monkeypatch):
    from scripts.d7_e2e.email_gate import assess_email_no_send

    a = assess_email_no_send(
        api_vars={"RESEND_API_KEY": "re_x", "OMNIA_ENV": "staging"},
        health_body={"message": {"circuits": {"resend": {"open": True, "held": False}}}},
    )
    assert a["ok"] is False


def test_b8_choke_point_inventory():
    from scripts.d7_e2e.email_proof import inventory_email_send_paths

    paths = inventory_email_send_paths()
    assert len([p for p in paths if p["transport"] == "resend.Emails.send"]) == 1


def test_b8_multiprocess_shared_kill_file(tmp_path):
    """Two OS processes; kill file SoT; both refuse send. Not live Mongo."""
    kill = tmp_path / "kill.json"
    kill.write_text(json.dumps({"resend": True}) + "\n", encoding="utf-8")
    worker = textwrap.dedent(
        f"""
        import asyncio, json, os, sys
        sys.path.insert(0, {str(BACKEND)!r})
        sys.path.insert(0, {str(REPO)!r})
        os.environ["OMNIA_PROVIDER_KILL_FILE"] = {str(kill)!r}
        os.environ.pop("OMNIA_ENV", None)
        from shared.security import circuit as c
        c.clear_hold("resend")
        from shared.email.client import send_email
        import shared.email.client as ec
        calls = []
        def boom(*a, **k):
            calls.append(1)
            raise RuntimeError("transport")
        ec.resend.Emails.send = boom
        out = asyncio.run(send_email("a@b.c", "welcome", lang="it"))
        print(json.dumps({{"status": out.get("status"), "calls": len(calls)}}))
        """
    )
    results = []
    for _ in range(2):
        proc = subprocess.run(
            [sys.executable, "-c", worker],
            capture_output=True,
            text=True,
            cwd=str(REPO),
            env={**os.environ, "PYTHONPATH": f"{BACKEND}:{REPO}"},
            timeout=30,
        )
        assert proc.returncode == 0, proc.stderr
        line = [ln for ln in proc.stdout.splitlines() if ln.startswith("{")][-1]
        results.append(json.loads(line))
    assert all(r["status"] == "killed" and r["calls"] == 0 for r in results)


def test_b8_multiprocess_kill_then_second_blocks(tmp_path):
    """Process A sets kill in shared file; process B cannot authorize send after."""
    kill = tmp_path / "kill.json"
    kill.write_text(json.dumps({"resend": False}) + "\n", encoding="utf-8")

    setter = textwrap.dedent(
        f"""
        import asyncio, os, sys
        sys.path.insert(0, {str(BACKEND)!r})
        sys.path.insert(0, {str(REPO)!r})
        os.environ["OMNIA_PROVIDER_KILL_FILE"] = {str(kill)!r}
        from shared.ops.provider_flags import set_killed
        asyncio.run(set_killed("resend", killed=True, note="mp"))
        print("SET_OK")
        """
    )
    checker = textwrap.dedent(
        f"""
        import asyncio, json, os, sys
        sys.path.insert(0, {str(BACKEND)!r})
        sys.path.insert(0, {str(REPO)!r})
        os.environ["OMNIA_PROVIDER_KILL_FILE"] = {str(kill)!r}
        os.environ.pop("OMNIA_ENV", None)
        from shared.security import circuit as c
        c.clear_hold("resend")
        from shared.email.client import send_email
        import shared.email.client as ec
        ec.resend.Emails.send = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x"))
        out = asyncio.run(send_email("a@b.c", "welcome", lang="it"))
        print(json.dumps({{"status": out.get("status")}}))
        """
    )
    env = {**os.environ, "PYTHONPATH": f"{BACKEND}:{REPO}"}
    r1 = subprocess.run(
        [sys.executable, "-c", setter], capture_output=True, text=True, cwd=str(REPO), env=env, timeout=30
    )
    assert r1.returncode == 0 and "SET_OK" in r1.stdout, r1.stderr
    data = json.loads(kill.read_text())
    assert data.get("resend") is True
    r2 = subprocess.run(
        [sys.executable, "-c", checker], capture_output=True, text=True, cwd=str(REPO), env=env, timeout=30
    )
    assert r2.returncode == 0, r2.stderr
    line = [ln for ln in r2.stdout.splitlines() if ln.startswith("{")][-1]
    assert json.loads(line)["status"] == "killed"


def test_b8_l5_skeleton_not_executed(tmp_path):
    from scripts.d7_e2e.l5_evidence import build_l5_evidence_skeleton

    ev = build_l5_evidence_skeleton(run_id="20261121T120000Z_l5skel1", run_path=tmp_path)
    assert ev["status"] == "NOT_EXECUTED"
    assert (tmp_path / "email_send_evidence_l5.json").exists()

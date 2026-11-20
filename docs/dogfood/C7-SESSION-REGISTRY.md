# D-175 · C7 — Registro sessioni Dogfood

**Baseline design:** `8b3723d` · **Implementazione:** autorizzata Founder  
**Esclusioni:** H4, sealed mint, Stripe LIVE, produzione, merge

## Decisioni recepite

D-C7-01…06 · P-C7-01 (off-host = futuro) · P-C7-02 (no M3; mirror off-host non blocca close/cert) · P-C7-04 (Ed25519 pure RFC 8032)

## Layout

```
dogfood/sessions/          # SoT (gitignored runtime)
  index.jsonl
  headers/<session_id>.json
  events/<session_id>.jsonl
  tips/<session_id>.tip.json
  unsigned_checkpoints/
  signed_checkpoints/
  mirrors/local/           # riscontro on-host best-effort
  evidence/<session_id>/<recovery_id>/
docs/dogfood/scenarios/catalog.yaml
docs/dogfood/c7_registry_verify.pub   # pubkey raw/hex (Founder)
```

## CLI

```bash
PY=backend/.venv/bin/python   # required (needs cryptography + backend deps)

# CLEAN: working tree MUST be clean (D-C7-05)
$PY scripts/dogfood_session.py open --kind CLEAN --workcopy omnia_df_clean_c7

$PY scripts/dogfood_session.py bind --session-id <id> --workcopy omnia_df_clean_c7
$PY scripts/dogfood_session.py verify --session-id <id>
$PY scripts/dogfood_session.py close --session-id <id> --status COMPLETED

# Founder firma offline il payload unsigned, poi:
export OMNIA_C7_PUBKEY_FINGERPRINT='sha256:...'
$PY scripts/dogfood_session.py attach-sig \
  --checkpoint-id <cid> \
  --signature /path/to/checkpoint.sig \
  --pubkey docs/dogfood/c7_registry_verify.pub

# Recovery coda parziale (seal-before-recover)
$PY scripts/dogfood_session.py recover-partial --session-id <id>
```

Override root: `OMNIA_DOGFOOD_SESSIONS_ROOT` o `DOGFOOD_ROOT`.

## Test

```bash
cd backend && .venv/bin/pytest tests/test_d175_c7_session_registry.py -q
```

## Note

- La chiave privata **non** è in Dogfood; solo verify/attach-sig.
- P-C7-01 off-host: non implementato in C7 (futuro).
- Certificazione non richiede mirror off-host (P-C7-02).

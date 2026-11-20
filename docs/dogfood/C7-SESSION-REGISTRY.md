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
docs/dogfood/c7_registry_verify.pub          # pubkey Founder (installata)
docs/dogfood/c7_registry_verify.fingerprint  # fingerprint atteso
```

## CLI

```bash
PY=backend/.venv/bin/python   # required (needs cryptography + backend deps)

# CLEAN: working tree MUST be clean (D-C7-05)
$PY scripts/dogfood_session.py open --kind CLEAN --workcopy omnia_df_clean_c7

$PY scripts/dogfood_session.py bind --session-id <id> --workcopy omnia_df_clean_c7
$PY scripts/dogfood_session.py verify --session-id <id>
$PY scripts/dogfood_session.py close --session-id <id> --status COMPLETED

# Firma offline (privata SOLO sul vault Founder — mai in repo):
$PY scripts/dogfood_c7_sign_offline.py \
  --private-key /secure/path/c7_founder.priv \
  --unsigned dogfood/sessions/unsigned_checkpoints/<cid>.json \
  --out /tmp/checkpoint.sig

# Attach (pubkey + fingerprint già in docs/dogfood/ — niente export manuale):
$PY scripts/dogfood_session.py attach-sig \
  --checkpoint-id <cid> \
  --signature /tmp/checkpoint.sig

# Recovery coda parziale (seal-before-recover)
$PY scripts/dogfood_session.py recover-partial --session-id <id>
```

Override:
- `DOGFOOD_ROOT` → usa `<DOGFOOD_ROOT>/sessions`
- `OMNIA_DOGFOOD_SESSIONS_ROOT` → path **diretto** al tree `sessions/` (nessun `/sessions` aggiuntivo)
- `OMNIA_C7_PUBKEY_FINGERPRINT` o `--fingerprint` → override del file `.fingerprint` (opzionale)

## Test

```bash
cd backend && .venv/bin/pytest tests/test_d175_c7_session_registry.py -q
```

## Note

- La chiave privata **non** è in Dogfood; solo verify/attach-sig.
- Pubkey + fingerprint Founder sono installati in `docs/dogfood/c7_registry_verify.*`.
- P-C7-01 off-host: non implementato in C7 (futuro).
- Certificazione non richiede mirror off-host (P-C7-02).

# D-175 · C2 — Backup / restore Dogfood

**Autorizzazione:** `OMNIA — AUTORIZZAZIONE ESPLICITA ALL'IMPLEMENTAZIONE` — ciclo **C2**  
**Fuori scope:** C3 permanente, C4–C8, Stripe/Resend, merge senza Founder.

## Procedura ripetibile

```bash
# 1) Bootstrap Mongo isolato :27018 + ruoli (auth)
python3 scripts/dogfood_mongo_bootstrap.py

# 2) Drill completo: seed → dump → media → manifest → restore probe → verify
python3 scripts/dogfood_c2_drill.py
```

## Destinazioni

| Ruolo | DB | Note |
|---|---|---|
| Source | `omnia_df_c2_src` | prefisso `omnia_df_` |
| Restore | `omnia_df_probe_c2` | solo `omnia_df_probe*` |
| Vietati | `omnia`, `omnia_df_perm*` | fail-closed |

## Ruoli Mongo

Vedi `dogfood/C2_MONGO_ROLE_MATRIX.json` (e artifact `D175-C2-MONGO-ROLE-MATRIX.json`).  
Credenziali solo in `dogfood/secrets/` (gitignored).

## Manifest

`MANIFEST.json` include backup_id, git_sha, collections, media inventory SHA, dump tree SHA.  
Mai password/URI con credenziali.

## Permanent

Nessuna operazione sulla base permanente (C3).

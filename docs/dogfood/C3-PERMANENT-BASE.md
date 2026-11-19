# D-175 · C3 — Base permanente Dogfood

**Autorizzazione:** `OMNIA — AUTORIZZAZIONE ESPLICITA ALL'IMPLEMENTAZIONE` — ciclo **C3**  
**Fuori scope:** C4 seed account, C5–C8, merge senza Founder, restore distruttivo reale.

## Identità

| Voce | Valore |
|---|---|
| DB | `omnia_df_perm_main` (`OMNIA_DOGFOOD_PERMANENT_DB`) |
| Endpoint | loopback `OMNIA_DF_MONGO_PORT` (default **27018**, hard-deny 27017) |
| Marker file | `dogfood/permanent/IDENTITY.json` |
| Marker collection | `_omnia_permanent_identity` |

La base permanente **non** è un DB di lavoro. Copie: `omnia_df_clean_*` (CLEAN), `omnia_df_cont_*` (CONTINUITY).

## Protezioni

1. Runtime (`OMNIA_ENV=dogfood`): refuse se `DB_NAME`/URI punta al permanente (anche con credenziali alternate).
2. Clone / wipe / restore / migrate ordinari → **DENY** se target permanente.
3. Mongo roles: `omnia_df_runtime` / `omnia_df_clone` **senza write** sul permanente; `omnia_df_emergency` sealed.
4. Fail-closed se IDENTITY non dimostrabile (emergenza).

## Init

```bash
python3 scripts/dogfood_mongo_bootstrap.py   # C2 auth instance
python3 scripts/dogfood_permanent_init.py    # IDENTITY + roles + backup skeleton
python3 scripts/dogfood_c3_verify.py         # T1–T13 live
```

Nessun account/org commerciale (C4).

## Emergenza (sealed)

```bash
# Solo prove gate — nessun restore distruttivo in C3
OMNIA_PERMANENT_UNLOCK=1 \
OMNIA_PERMANENT_AUTH_PHRASE='OMNIA FOUNDATION UNLOCK PERMANENT BASE' \
OMNIA_PERMANENT_CONFIRM_1=CONFIRM-PERMANENT-EMERGENCY \
OMNIA_PERMANENT_CONFIRM_2=CONFIRM-PERMANENT-EMERGENCY \
python3 scripts/dogfood_permanent_emergency_restore.py --prove-gates
```

Audit append-only: `dogfood/permanent/EMERGENCY_AUDIT.jsonl`.

## Dipendenza C1 (documentata)

`perimeter.check_dogfood_db_isolation` ora rifiuta anche `omnia_df_perm*` come runtime (prima il solo prefisso `omnia_df_` li avrebbe accettati). Modifica strettamente necessaria a C3.

# D-175 · C1 — Perimetro Dogfood (implementato)

**Autorizzazione:** `OMNIA — AUTORIZZAZIONE ESPLICITA ALL'IMPLEMENTAZIONE` — ciclo **C1**  
**Baseline tip:** `00a5506366cf58f4a9ab8ec41147733bb9784fc9`  
**Data:** 19 novembre 2026 (Europe/Rome)

## Precizioni operative integrate

| ID | Regola |
|---|---|
| **A** | `OMNIA_H4_PURCHASE_READY=true` **non** sblocca acquisti. Serve anche marker sealed `H4_PURCHASE_READY_V1=…` (prodotto solo dopo C5+C6). |
| **B** | Nessuna autorità commerciale implicita Super Admin per purchase. Acquisti = Main Admin nominato (C5). C1 blocca tutti. |
| **C** | Runtime Dogfood: `DB_NAME` deve iniziare con `omnia_df_` e non può essere `omnia` (DB condiviso). |

## Env Dogfood minimi

```bash
export OMNIA_ENV=dogfood
export DB_NAME=omnia_df_clean_<id>
export MONGO_URL=mongodb://127.0.0.1:27017
export OMNIA_DOGFOOD_ALLOWED_API_HOSTS=127.0.0.1,localhost
export OMNIA_DOGFOOD_ALLOWED_FE_HOSTS=127.0.0.1,localhost
export OMNIA_API_PUBLIC_URL=http://127.0.0.1:43121
export FRONTEND_URL=http://127.0.0.1:43123
# N1 vuota → Resend blocked
# N3 HOLD → applied at boot (resend/fal/llm/…)
```

## Verifica

```bash
bash scripts/e2e-dogfood-preflight.sh   # con env sopra
cd backend && .venv/bin/pytest tests/test_d175_c1_dogfood_perimeter.py -q
```

## Fuori scope C1

Base permanente, clone, seed, Stripe mutate, H4 Session.create, C2+.

# D-175 · C4 — Procedura Founder (account e organizzazioni Dogfood)

**Autorizzazione:** solo C4. C1–C3 chiusi. **Cursor non crea account**: li crei tu.

## Principio

| Chi | Cosa |
|---|---|
| **Founder** | Crea utenti (signup), sceglie email/password, conferma email, compila il manifest |
| **Cursor** | Predispone struttura CC/Org/wallet, gate anti-permanente, apply idempotente, verify |

## Schema target

```
CommercialCustomer (1 × P.IVA fittizia)
├── Organization / filiale A
├── Organization / filiale B
├── Organization / filiale …
├── cc_credit_wallets (1 wallet centrale)
└── main_admin_user_id → User (creato dal Founder)
```

- Main Admin **≠** accesso CRM automatico (serve Membership esplicita).
- Admin di filiale **≠** autorità wallet centrale.
- Stessa P.IVA → stesso CC (unicità).

## Passi

### 0) Ambiente Dogfood

```bash
# mongod isolato già da C2/C3
python3 scripts/dogfood_c3_verify.py   # read-only; IDENTITY stabile
```

### 1) Copia di lavoro CLEAN (mai sulla permanente)

```bash
python3 scripts/dogfood_c4_workcopy.py --kind clean --target omnia_df_clean_c4 --drop-target
# opzionale CONTINUITY:
python3 scripts/dogfood_c4_workcopy.py --kind continuity --target omnia_df_cont_c4 --drop-target
```

Runtime Dogfood: `DB_NAME=omnia_df_clean_c4` (non `omnia_df_perm_main`).

### 2) Manifest

Copia il template e **sostituisci** P.IVA fittizia, nomi org, email **dopo** che hai creato gli utenti:

```bash
cp docs/dogfood/c4-manifest.template.json dogfood/c4/manifest.json
# modifica dogfood/c4/manifest.json
python3 scripts/dogfood_c4_apply_manifest.py --manifest dogfood/c4/manifest.json --db omnia_df_clean_c4 --dry-run
```

### 3) Creazione account (tu)

Per ogni email nel manifest:

1. Registrati / invita nell’ambiente Dogfood (loopback).
2. Conferma email (`email_verified=true`).
3. Non usare email/P.IVA reali di Nicastro o produzione.

### 4) Apply struttura

```bash
python3 scripts/dogfood_c4_apply_manifest.py --manifest dogfood/c4/manifest.json --db omnia_df_clean_c4
```

- Se un utente manca → `pending_founder` (nessuna invenzione).
- CC + org + wallet vengono creati in modo idempotente.
- Main Admin nominato solo se l’utente esiste ed è idoneo.

### 5) Verify

```bash
python3 scripts/dogfood_c4_verify.py --db omnia_df_clean_c4
```

Esiti: `PASS` / `FAIL` / `NOT VERIFIED` (atteso finché non completi gli account).

## Matrice autorità (C4)

| Ruolo | Wallet CC | CRM filiale |
|---|---|---|
| Main Admin | sì (quando H4/C5) | **no** automatico |
| Admin Organization | no | sì (membership) |
| Collaboratore | no | sì (membership propria org) |

## Divieti

- Scrittura su base permanente C3  
- Account/dati reali / Nicastro / produzione  
- Email reali / Stripe LIVE  
- Merge senza Founder  
- C5+  

## Residui

`omnia_df_admin` resta superuser tecnico (come C3). Host-alias exact-match documentato in C3.

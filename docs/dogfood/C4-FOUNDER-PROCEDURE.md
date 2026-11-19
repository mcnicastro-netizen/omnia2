# D-175 · C4 — Procedura Founder (account e organizzazioni Dogfood)

**Stato:** ✅ **CHIUSO in main** (19-Nov-2026) · PR #234 · head `2ae1234` · merge `67b5e92` · **D-189**  
**Prossimo ciclo:** C5 solo con nuova autorizzazione Founder.  
**Nota procedura storica:** in C4 Founder o Cursor (con mandato sintetici) creano gli account; apply/verify restano tool Cursor.

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
- L’email del Main Admin **non** deve comparire anche in `organization_admins` / `collaborators` dello stesso manifest (l’apply rifiuta l’accoppiamento commerciale+CRM).

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

Prima collega il portale alla copia CLEAN (mai la permanente):

```bash
bash scripts/dogfood_c4_bind_runtime.sh
```

Per ogni email nel manifest:

1. Registrati sul portale Dogfood (link tunnel / login).
2. Conferma email: con provider inventati **non arriva posta**. Dopo la registrazione:
   `python3 scripts/dogfood_c4_print_verify_link.py --email TUA_EMAIL_INVENTATA`
   e apri il `verify_url` restituito.
3. Non usare email/P.IVA reali di Nicastro o produzione. Tutto inventato.

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

## Residui (registro rischi — non confondere con NOT VERIFIED C4)

| Residuo | Origine | Nota |
|---|---|---|
| `omnia_df_admin` superuser tecnico | C3 | Non è un NOT VERIFIED C4 |
| Host-alias exact-match | C3 | Non è un NOT VERIFIED C4 |
| T5 / T7 (storico NOT VERIFIED) | C4 | Chiusi con account sintetici (verify 13/13) |

## Review #234 — punti chiusi lato tecnico

1. Apply multi-run: CC/org/wallet idempotenti; membership `already_active` se invariata.
2. Workcopy/apply verso permanente: DENY (gate C3 + `assert_c4_seed_target`).
3. Manifest: no overlap MA↔membership; org_key sconosciuta → errore; membership vincolata al CC.
4. T5/T7 marcati `depends_on: founder_account`; T6/T9 verifiche strutturali (non solo matrice documentale).

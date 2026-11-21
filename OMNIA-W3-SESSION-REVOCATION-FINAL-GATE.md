# OMNIA — W3 FINAL SECURITY GATE: Immediate Session Invalidation & Staging Readiness

**Data (Europe/Rome):** 2026-11-21 20:56 CET  
**Branch:** `cursor/staging-e2e-d1d3-b894`  
**HEAD:** `ea89714dfee65ca592e413db551d1506b573049a` (**nessun commit in questo ciclo**)  
**Working tree:** modifiche W3 / D-175 / PRE-GTM **conservate** + gate sessioni  
**Vincoli:** solo locale · nessun reset/stash/clean · nessun commit/push/merge/deploy · nessun accesso Railway/Vercel/Mongo remoto/Stripe/Resend · nessuna email reale · solo dati sintetici

**Rapporti collegati:**  
`OMNIA-W3-STAGING-READINESS-REPORT.md` · `PRE-GTM-READINESS-MASTER.md` · `docs/pre-gtm/02-security-multitenant.md`

---

## 1. Causa radice

Prima di questo gate, la revoca operativa (logout-all, password change, `revoke_all_refresh`, cease CC, remove_member) **eliminava solo le row `refresh_tokens` (jti allowlist)**.

L’access token è un JWT HS256 (~15 minuti) validato in `get_current_user` con firma + expiry, **senza controllo server-side sullo stato sessione**. Risultato documentato nel report staging readiness:

> dopo `revoke_all_refresh`, l’access JWT poteva continuare ad autenticare fino alla propria scadenza (~15′).

Questo **contrasta** con B03/B14 (sessioni identificabili e revocabili; password change / membership revoke / logout devono invalidare le sessioni attive). La cancellazione dei refresh **non** equivale all’invalidazione della sessione attiva.

Percorsi che accettavano ancora il JWT precedente: **ogni** dependency autenticata (`get_current_user` / cookie `access_token` / Bearer), non solo `/auth/refresh`.

---

## 2. Architettura della correzione

**SoT condiviso:** MongoDB sul documento utente.

| Campo / claim | Ruolo |
|---------------|--------|
| `users.active_session_ids[]` | allowlist delle sessioni ancora valide |
| `users.session_epoch` (`sv` nel JWT) | epoch globale; bump su revoke-all → invalida anche sid stantii |
| Access JWT claims `sid` + `sv` (+ `jti`) | legano il token alla sessione Mongo |
| Refresh JWT claim `sid` + jti in `refresh_tokens` | refresh valido solo se jti presente **e** `sid` ancora in `active_session_ids` |

**Validazione per richiesta:** `assert_access_session(user, payload)` in `dependencies.get_current_user` **dopo** il load utente — nessun round-trip Mongo aggiuntivo; fail-closed se manca `sid`, se `sid` non è attivo, se `sv` ≠ epoch.

**Emissione:** `issue_auth_tokens` → `register_session` (push sid, slice ultime 20) → mint access+refresh → `store_refresh`.

**Revoche (ambiti):**

| Evento | Funzione | Effetto |
|--------|----------|---------|
| Logout sessione corrente | `revoke_refresh` → `revoke_session` | pull un `sid` + delete refresh di quel sid |
| Logout tutte / security revoke / password | `revoke_all_sessions` / `revoke_all_refresh` | clear sid + `$inc session_epoch` + delete tutti i refresh |
| Remove member / membership revoke | `revoke_all_sessions(..., membership_revoke)` | sessioni utente invalidate (identità/storia/CC restano) |
| Sospensione account | `is_active=False` + path auth (JWT ancora soggetto a session check) | blocco login/uso |
| Cease CommercialCustomer | `revoke_all_sessions(..., cc_cease)` per membri (MA incluso) | sessioni chiuse; accesso CC cessato |

**Non** usata memoria di processo come SoT. Nessuna cache locale che possa mantenere valida una sessione revocata su un’altra replica. Scadenza naturale JWT resta rispettata (token scaduto → 401 indipendentemente dalla sessione).

**Fail-closed:** errori Motor/Mongo su registration/validazione refresh → reject (`session_store_unavailable` / `is_refresh_valid=False`). Harness prova revoke via PyMongo sync condiviso con l’API.

**P.IVA (residuo precedente):** indice unique su CommercialCustomer + omissione campi sparse-null (`stripe_customer_id`) in insert → race concorrente chiusa; test `test_w3_piva_concurrent_create.py`.

---

## 3. File modificati (gate sessioni — principali)

**Produzione**
- `backend/shared/auth/session_store.py` — register / assert / issue / mint / revoke_session / revoke_all_sessions
- `backend/shared/auth/jwt_tokens.py` — claims `sid`/`sv` su access; `sid` su refresh
- `backend/shared/auth/dependencies.py` — `assert_access_session` su ogni richiesta autenticata
- `backend/apps/core/auth.py` — login/refresh/logout/logout-all via session store
- `backend/apps/core/google_auth.py`, `mfa_routes.py`, `immocloud/cloud_auth.py`, `immoweb/invites.py` — emissione session-bound
- `backend/apps/immoweb/agencies.py` — `remove_member` → `revoke_all_sessions`
- `backend/shared/billing/commercial_access.py` — cease → `revoke_all_sessions`
- `backend/shared/privacy/erasure.py` — revoca sessioni
- `backend/shared/auth/commercial_customer_service.py` — omit null sparse unique su insert
- `backend/shared/db/connection.py` — `Database.reset()` per test `asyncio.run`

**Test**
- `backend/tests/test_w3_session_revocation_final.py` (**nuovo**, HTTP Mongo)
- `backend/tests/test_w3_multiprocess_local.py` (riscritto: B14 cross-process)
- `backend/tests/test_w3_piva_concurrent_create.py` (**nuovo**)
- `backend/tests/test_slice1_b01_b03.py`, `test_mc042_r01_refresh_cease.py`, `test_w3_staging_readiness_authz.py`, dual-tenant seed `active_session_ids`

**Harness / docs**
- `scripts/w3_staging_harness/preflight.py` — `check_session_revocation_local` (access+refresh post-revoke Mongo)
- `scripts/w3_staging_harness/__main__.py` — EC-4 / EC-7
- questo rapporto + aggiornamenti PRE-GTM / staging readiness / `02-security-multitenant.md`

---

## 4. Test HTTP eseguiti (MongoDB reale + API `:43121`)

Suite: `tests/test_w3_session_revocation_final.py` — **8 passed**

| Test | Cosa dimostra |
|------|----------------|
| `test_http_valid_before_revoke` | Access JWT session-bound accettato pre-revoca (anche su path protetto) |
| `test_http_logout_rejects_old_access_immediately` | Logout corrente → access e refresh rifiutati subito |
| `test_http_revoke_all_sessions_rejects_access` | Revoke-all → access 401 immediato |
| `test_http_membership_revoke_clears_sessions` | Remove/membership revoke → sessioni invalidate; identità non cancellata |
| `test_http_account_suspension_blocks` | Account sospeso bloccato |
| `test_http_malformed_and_legacy_token_rejected` | Token malformato / legacy senza `sid` → 401 |
| `test_http_cc_cease_revokes_sessions` | Cease CC → sessioni membri revocate |
| `test_unit_assert_access_session_fail_closed` | Assert fail-closed (sid assente / revocato / epoch mismatch) |

Artefatto focused: `/opt/cursor/artifacts/w3_session_gate_v.txt` (16 passed con MP+PIVA).

---

## 5. Test multi-processo (HTTP reale tra processi distinti)

Suite: `tests/test_w3_multiprocess_local.py` — **5 passed**  
Processi: uvicorn A `:43121` + uvicorn B `:43122`, stesso Mongo.

| # | Sequenza | Esito |
|---|----------|-------|
| 1 | Health A e B | 200 entrambi |
| 2 | Auth via A; stesso access JWT su A e B **prima** della revoca | accettato su entrambi |
| 3 | Revoca sessioni via Mongo/A; **immediatamente** stessa access JWT su B | **401** |
| 4 | Refresh post-revoca | **401/403** |
| 5 | Membership revoke → access rifiutato cross-process | **401** |

Nessun processo mantiene una sessione valida in memoria locale dopo la revoca Mongo.

---

## 6. Risultati MongoDB reale / P.IVA concorrente

- Sessioni: `active_session_ids` / `session_epoch` aggiornati in Mongo; osservabili da entrambi i processi.
- Prefissi sintetici isolati (`w3sess-*`, `w3mp-*`, `w3piva-*`, harness `w3stg-*`); cleanup solo documenti taggati.
- `test_w3_piva_concurrent_create.py` (**3 passed**):
  - indice unique presente;
  - `get_or_create` concorrente → **un solo** CommercialCustomer;
  - insert grezzo duplicato → DuplicateKey;
  - fix insert: non scrivere `stripe_customer_id: null` (sparse unique).

---

## 7. Regressione

```text
cd backend && PYTHONPATH=. pytest \
  tests/test_w3_session_revocation_final.py \
  tests/test_w3_multiprocess_local.py \
  tests/test_w3_piva_concurrent_create.py \
  tests/test_w3_staging_readiness_authz.py \
  tests/test_w3_http_dual_tenant_mongo.py \
  tests/test_w3_residual_idor.py \
  tests/test_w3_secondary_paths.py \
  tests/test_w3_deals_mls_outsider_authz.py \
  tests/test_tenant_guard_adversarial.py \
  tests/test_tenant_guard_inject.py \
  tests/test_d175_* (deal/collab/pr240/c5) \
  tests/test_b04_* \
  tests/test_authz_storage_paths.py \
  tests/test_owner_delete_video_tour.py \
  tests/test_microtour_video_persist.py \
  tests/test_slice1_b01_b03.py \
  tests/test_mc042_r01_refresh_cease.py -q
→ 226 passed
```

Artefatto: `/opt/cursor/artifacts/w3_session_full_regression.txt`

---

## 8. Harness

```text
PYTHONPATH=backend:. python -m scripts.w3_staging_harness --mode local \
  --json-out /opt/cursor/artifacts/w3_staging_harness_session.json
→ verdict PASS
```

Preflight `session_revocation`: `pre_me=200`, `post_me=401`, `post_refresh=401` dopo clear Mongo `active_session_ids` + bump `session_epoch`.

Entry criteria: EC-1…EC-7 (incluso B14 multi-process locale).  
Staging mode resta **BLOCKED** senza `OMNIA_STAGING_VERIFY=1` (nessuna simulazione remota).

---

## 9. Residui (non bloccano l’ingresso alla verifica staging)

| Residuo | Nota |
|---------|------|
| Multi-replica Railway dietro LB | Da attestare in staging (stesso SoT Mongo; locale già cross-process) |
| B8 / L5 / T22 / Stripe webhook / cookie Vercel | Remote-only (invariati) |
| Certificazione GTM | **Non** dichiarata |

Residuo “access JWT ~15′ post-revoke” del report precedente: **chiuso localmente** da questo gate.

---

## 10. Branch · HEAD · working tree · operazioni remote

| Voce | Valore |
|------|--------|
| Branch | `cursor/staging-e2e-d1d3-b894` |
| HEAD | `ea89714dfee65ca592e413db551d1506b573049a` |
| Commit in questo ciclo | **nessuno** |
| Push / merge / deploy | **nessuno** |
| Accesso remoto prod/staging servizi | **nessuno** |
| Working tree | dirty (W3/D-175/PRE-GTM + gate sessioni) — **non** resettato |

---

## 11. Criteri di completamento (checklist)

| Criterio | Stato |
|----------|--------|
| Vecchio access JWT rifiutato subito dopo revoca | **implementato verificato** (HTTP + harness) |
| Vecchio refresh rifiutato | **implementato verificato** |
| Coerenza tra processi distinti | **implementato verificato** (A→revoke, B→401) |
| Logout / sospensione / membership ambiti distinti | **implementato verificato** |
| Fail-closed | **implementato verificato** (unit + refresh path) |
| Race P.IVA verificata e riparata | **implementato verificato** |
| Regressione pertinente verde | **226 passed** |
| Harness aggiornato PASS locale | **PASS** |
| Documentazione PRE-GTM aggiornata | **sì** |

---

## 12. VERDETTO

### **A. W3 PRONTO PER VERIFICA STAGING — SESSIONI VERIFICATE**

Invalidazione immediata delle sessioni dimostrata localmente anche tra processi API distinti sullo stesso MongoDB. Requisiti del gate completati; harness aggiornato e PASS.  

**Non** si dichiara certificazione staging né GTM: restano le verifiche sull’ambiente distribuito (repliche Railway, B8/L5/T22, cookie/CORS, Stripe test webhook).

---

## Rettifica cronologica (W4 · 2026-11-21 21:10 CET)

Ordine reale dei cicli locali:
1. **W3 Staging Readiness** (hardening globale + report iniziale) — ciclo precedente a questo gate.
2. **W3 Session Final Gate** (B14) — completato **2026-11-21 20:56 CET**; file scritto ~20:57 CET (mtime UTC 19:57).

Il report Staging Readiness aveva header «21:45 CET» (ciclo readiness) poi annotato «aggiornato post session gate» allo stesso orario del gate (~20:56–20:57 CET). La label «21:45» **non** indica un evento successivo al gate: è il timestamp documentale del ciclo readiness, cronologicamente **anteriore** al gate B14. I risultati dei due report non sono stati riscritti retroattivamente; solo questa nota chiarisce l’ordine.

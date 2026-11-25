# OMNIA — W4 Configuration Contract + B8 Restart Gate

**Data (Europe/Rome):** 2026-11-21 22:45 CET  
**Branch:** `cursor/w4-staging-e2e-b894`  
**Codice API staging di riferimento:** `3f34c5f`  
**Ambito:** solo staging (`omnia-api` + `omnia-api-w4b`)  
**Verdetto W4 complessivo:** resta **B** (nessun passaggio ad A in questo ciclo)

Nessun valore di segreto è stato letto nei report. Solo presenza/assenza.

---

## A. Contratto configurativo (dal codice deployato)

### A.1 Resend / email

| Variabile | Letta in | Obbligatoria? | Se assente | Servizi Railway |
|-----------|----------|---------------|------------|-----------------|
| `RESEND_API_KEY` | `backend/shared/email/client.py` `_configure_resend()` | **Sì** per invio reale | `_configure_resend()` → False; `send_email` logga `[EMAIL MOCK]` e ritorna `status=mock` (nessuna chiamata Resend) | **Entrambi** `omnia-api` e `omnia-api-w4b` (stesso valore) |
| `SENDER_EMAIL` | `backend/shared/email/client.py` L20 `SENDER = os.environ.get("SENDER_EMAIL") or _DEFAULT_SENDER` | Consigliata | Default hardcoded `OMNIA <info@omniarealestateecosystem.it>` | Entrambi (identico) |
| `FROM_EMAIL` | **non letta** dal codice email | No | — | Non configurare |
| `RESEND_FROM` | **non letta** | No | — | Non configurare |
| `OMNIA_RESEND_KILLED` | `shared/ops/provider_flags.py` `env_resend_killed()` | No (kill di emergenza) | Kill solo via Mongo `provider_flags` | Opzionale entrambi |
| `OMNIA_EMAIL_ALLOWLIST` | `shared/email/client.py` solo se `OMNIA_ENV=dogfood` | No su staging | Su staging (`OMNIA_ENV=staging`) l’allowlist **non** è applicata | Non richiesta per staging |
| `OMNIA_EMAIL_FORCE_ALLOWLIST_TEST` | solo ramo dogfood | No | — | Non richiesta |
| `OMNIA_ENV` | email client + provider flags | Già presente `staging` | — | Entrambi (già OK) |

**Mittente esatto:** `SENDER_EMAIL` (non `FROM_EMAIL`).  
**Dominio:** il default punta al dominio verificato documentato in `memory/RESEND_DOMAIN_GUIDE.md`. Se `SENDER_EMAIL` contiene `@resend.dev`, il client lo rifiuta e ripiega sul default.

**Path di invio:** unico ingresso applicativo `send_email()` in `shared/email/client.py` (template transazionali, invite, founders, ecc.). Kill B8: `resend_must_block_send()` + circuit hold — non bypassabile da allowlist.

### A.2 Stripe Test

| Variabile | Letta in | Obbligatoria? | Se assente | Servizi |
|-----------|----------|---------------|------------|---------|
| `STRIPE_ENABLED` | `apps/billing/routes.py` `_is_enabled()`; anche `visura_b2c`, `founder_*` | **Sì** (deve essere stringa `true`) | Billing 503 `stripe_not_configured` | Entrambi (già presente) |
| `STRIPE_SECRET_KEY` | `routes.py` `_refresh_stripe_api_key()`; `setup_stripe.py`; `commercial_access.py`; `founder_bridge`; `visura_b2c` | **Sì** per abilitare billing | `_is_enabled()` False → 503 | **Primario obbligatorio**; mirror su `w4b` per coerenza se il traffico lo colpisce |
| `STRIPE_PUBLISHABLE_KEY` | `routes.py` `GET /billing/plans` → `publishable_key` | **Sì** per FE checkout | FE riceve stringa vuota | Entrambi (identico) |
| `STRIPE_WEBHOOK_SECRET` | `routes.py` modulo + `stripe_webhook` | **Sì** per webhook | Se enabled ma secret assente → 503 `webhook_secret_missing` | **Primario** (endpoint pubblico tipico); mirror consigliato su w4b |
| `STRIPE_MODE` | `routes.py` L126 (solo risposta catalogo); `founder_ops.py` / `founder_bridge.py` (display) | **No per abilitare SDK** | Default codice `"test"` | Consigliata `test` su entrambi (chiarezza + UI) |
| `STRIPE_PUBLIC_KEY` | alias solo in dogfood perimeter / test | No | Fallback di `STRIPE_PUBLISHABLE_KEY` in dogfood check | Non usare su staging |
| `STRIPE_TEST_SECRET` / `STRIPE_TEST_PUBLISHABLE` | solo bootstrap Cloud Agent / test vault alias | No a runtime Railway | — | Non necessarie se si impostano i nomi canonici |

**`STRIPE_MODE` è letta?** Sì. **È necessaria per far funzionare checkout/webhook?** No: `_is_enabled()` richiede solo `STRIPE_ENABLED=true` **e** `STRIPE_SECRET_KEY` non vuota. `STRIPE_MODE` è informativa (default `test`). **Raccomandazione Founder:** impostarla comunque a `test` per evitare ambiguità nei pannelli.

**Gate Live:** il runtime billing **non** rifiuta automaticamente `sk_live_` su staging. Il controllo `check_dogfood_stripe_test_only()` (`shared/dogfood/perimeter.py`) è per modalità dogfood. Per W4: usare **solo** chiavi `sk_test_` / `pk_test_` / `whsec_` di Test. Non usare Live.

**Webhook:** `POST /api/billing/webhook` — firma via `stripe.Webhook.construct_event` con `STRIPE_WEBHOOK_SECRET`.

### A.3 Condivisione `omnia-api` vs `omnia-api-w4b`

| Classe | Identica? | Motivo |
|--------|-----------|--------|
| `JWT_SECRET`, `MONGO_URL`, `DB_NAME` | già condivise | sessioni cross-instance |
| Resend (`RESEND_API_KEY`, `SENDER_EMAIL`) | **sì, stessi valori** | B8/L5 multi-istanza; stesso provider |
| Stripe (`STRIPE_*` sopra) | **sì, stessi valori** | coerenza se una richiesta colpisce w4b; webhook destinazione = URL primario |
| `LOCAL_STORAGE_ROOT` | solo w4b | media ephemeral — non toccare |
| `RAILWAY_VOLUME_*` | solo primario | non replicare su w4b |

### A.4 Propagazione modifiche variabili Railway

- Aggiornare variabili su **entrambi** i servizi.
- Railway tipicamente riavvia il servizio al cambio variabili; se health non riflette la presenza entro 1–2 minuti, eseguire restart/redeploy del solo staging.
- Dopo config: verificare `GET /api/billing/plans` → `enabled=true` **senza** stampare `publishable_key` nei report (solo lunghezza/prefisso `pk_test` in artefatto privato se serve).
- Non loggare secret; i report devono restare presence-only.

### A.5 Presenza attuale Railway (verificata staging)

Fonte: `/opt/cursor/artifacts/w4r/config_presence_matrix.json` (2026-11-21 22:24 CET).

| Variabile | `omnia-api` | `omnia-api-w4b` |
|-----------|-------------|-----------------|
| `RESEND_API_KEY` | ASSENTE | ASSENTE |
| `SENDER_EMAIL` | ASSENTE | ASSENTE |
| `STRIPE_ENABLED` | presente | presente |
| `STRIPE_SECRET_KEY` | ASSENTE | ASSENTE |
| `STRIPE_PUBLISHABLE_KEY` | ASSENTE | ASSENTE |
| `STRIPE_WEBHOOK_SECRET` | ASSENTE | ASSENTE |
| `STRIPE_MODE` | ASSENTE | ASSENTE |
| `OMNIA_ENV` | presente | presente |
| Diff extra | volume vars solo primario | `LOCAL_STORAGE_ROOT`, `OMNIA_INSTANCE_LABEL` solo w4b |

Nessuna variabile obsolete Resend/Stripe incoerente rilevata (non esistono alias spurî).

---

## B. B8 restart gate (W4-18) — eseguito su staging

Artefatto: `/opt/cursor/artifacts/w4r/w4_18_b8_restart.json`  
Log startup: `w4r/api_logs_post_restart_probe.txt`, `w4r/w4b_logs_post_restart_probe.txt`

| Step | Esito | Note |
|------|-------|------|
| 1. `killed=false` su A e B | **PASS** | Mongo + health |
| 2. set kill → `killed=true` A e B | **PASS** | |
| 3. restart A e B | **PASS con caveat** | CLI `railway service restart` **timeout 120s**; tuttavia log Railway mostrano `Application startup complete` A **22:38:13 CET**, B **22:40:10 CET** |
| 4. post-restart `killed=true` | **PASS** | Persistenza Mongo SoT |
| 5. clear → `killed=false` | **PASS** | Stato finale pulito |
| `instance_id` change | non usabile | formato `hostname:pid` spesso pid=`2` → ID stabile anche dopo restart |

**Verdetto W4-18:** **PASS** (kill + propagazione + persistenza post-restart attestata da log startup + health).  
Nessuna email inviata.

Test locali B8: `pytest tests/test_d175_b8_provider_kill.py` → **11 passed**.

---

## C. Checklist test residui (NON eseguiti in questo ciclo)

### C.1 L5 Resend (dopo config Founder)

1. Confermare presence `RESEND_API_KEY` + `SENDER_EMAIL` su A e B (no valori in chat).  
2. Prefisso strutturale chiave solo in artefatto privato (`re_…`) — mai dump completo.  
3. B8 `killed=true` → tentativo send sintetico → `status=killed` su A e B.  
4. B8 `killed=false` → send **solo** a destinatario di test controllato (Resend test / sink), mai indirizzi reali.  
5. Evidenza: health kill, log `[EMAIL …]`, export Resend delivery count = 0 verso reali nella finestra.  
6. Zero PASS simulati.

### C.2 Stripe Test W4-21/22 (dopo config Founder)

Precondizione: `STRIPE_SECRET_KEY` inizia con `sk_test_`, publishable `pk_test_`, `STRIPE_ENABLED=true`, webhook secret presente. Se prefisso live → **STOP**.

1. `GET /api/billing/plans` → `enabled=true`.  
2. Checkout Test (sessione sintetica).  
3. Webhook firmato → 200; firma invalida → 400.  
4. Evento duplicato / fuori ordine → idempotenza.  
5. Aggiornamento subscription + wallet/crediti.  
6. Retry / errori.  
7. Non trattare 503 come PASS.

---

## D. Tabella Founder — cosa configurare ora

| # | Variabile | Servizio/i | Valore atteso (tipo, non il secret) | Verifica immediata post-config |
|---|-----------|------------|-------------------------------------|--------------------------------|
| 1 | `RESEND_API_KEY` | `omnia-api` **e** `omnia-api-w4b` | chiave API Resend (ambiente adatto a test) | presence; poi L5 |
| 2 | `SENDER_EMAIL` | entrambi | es. `OMNIA <info@…>` su dominio verificato Resend | presence; send from corretto |
| 3 | `STRIPE_SECRET_KEY` | entrambi (primario obbligatorio) | **solo** `sk_test_…` | plans `enabled=true` |
| 4 | `STRIPE_PUBLISHABLE_KEY` | entrambi | **solo** `pk_test_…` | plans espone chiave test |
| 5 | `STRIPE_WEBHOOK_SECRET` | primario (+ mirror w4b) | `whsec_…` Test per URL staging | webhook firma |
| 6 | `STRIPE_MODE` | entrambi | `test` (consigliata, non gate SDK) | plans `mode=test` |

**Non configurare:** `FROM_EMAIL`, `RESEND_FROM`, chiavi Live, `STRIPE_PUBLIC_KEY` al posto di publishable.

**Dopo l’inserimento (Passo 3):** Cursor esegue solo L5 + Stripe W4-21/22 + allineamento A/B + regressione + aggiornamento matrice; poi rivalutazione A/B.

---

## E. Classificazione stati

| Voce | Stato |
|------|-------|
| Contratto nomi variabili | **verificato localmente** (codice branch) |
| Presenza/assenza Railway | **verificato su staging** |
| B8 kill + restart persistenza | **verificato su staging** |
| L5 Resend | **PASS** 25-Nov (D-193) — kill/revive A+B |
| Stripe Test E2E | **PASS** 25-Nov (D-193) — plans+webhook+sdk; app checkout self_serve residuo |
| Verdetto W4 | **A con residui** (D-193) |

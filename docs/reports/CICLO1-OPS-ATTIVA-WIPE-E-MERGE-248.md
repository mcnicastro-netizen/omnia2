# CICLO 1 — Ops Attiva/wipe CRM + consolidamento PR #248 + kickoff RBAC/tools

**Data (Europe/Rome):** 2026-11-26 18:15–18:20 CET  
**Autore:** Cursor (Cloud Agent)  
**Autorizzazione:** `OMNIA — AUTORIZZAZIONE ESPLICITA ALL'IMPLEMENTAZIONE` — Programma prioritario GTM  
**Perimetro ciclo 1:** A–F (Ops wipe + merge #248 + smoke staging) · avvio G–H (RBAC/tools)  

---

## 1. Obiettivo

1. Eliminare il rischio che **Attiva** cancelli CRM (`wipe_crm` default pericoloso / seconda Attiva).  
2. Consolidare **PR #248** (B2C D01–D04 + residui + fix Ops) su `main`.  
3. Smoke staging sul codice previsto · **no** deploy commerciale.  
4. Avviare RBAC per-membership e audit tools (kickoff, non chiusura).

---

## 2. Baseline

| Voce | Valore |
|------|--------|
| Worktree | `/agent/repos/omnia2-integration-d193-cmj-a4` |
| Branch ciclo 1 post-merge | `cursor/ciclo1-gtm-ops-merge-b894` |
| Branch PR #248 | `cursor/b2c-public-hardening-b894` |
| `origin/main` pre-merge | `5fba9f5df0416e81b801d855da5bf79a202a6aaf` |
| HEAD Ops tip (pre-merge) | `c5495520d3737431adb9b6d7b07d7d2094abffc6` |
| PR #248 | **MERGED** 2026-11-26 18:06 CET |
| Merge commit / nuovo `main` | `c342fb057ddb31b3b490c5c99d59edd6e7ca8403` |
| CI `main` @ merge | **SUCCESS** (run `45864808220`, B04 unit) |

---

## 3. Diagnosi Ops Attiva / wipe

**Confermato nel codice pre-fix:**

- `ActivateAgencyBody.wipe_crm: bool = True` (default pericoloso).  
- `ops_activate_agency` chiamava wipe se `wipe_crm` True.  
- Nessun guard “già active” → seconda Attiva poteva wipe.  
- FE cabina inviava `wipe_crm: true`.  
- `POST /ops/wipe-agency-crm` riusava body Attiva senza confirm/reason.

**Percorsi wipe mappati:**

| Path | Ruolo post-fix |
|------|-----------------|
| `POST /app/ops/activate-agency` | Attiva — **non wipe**; rifiuta `wipe_crm=True` |
| `POST /app/ops/wipe-agency-crm` | Wipe dedicato: `confirm=WIPE_CRM` + reason + lock + audit |
| `POST /app/ops/bridge/tenants/{id}/offboard` | Offboard distinto (`confirm=CHIUDI_AGENZIA`) — non modificato oltre policy Attiva |

---

## 4. Soluzione Ops implementata

1. **Default** `wipe_crm=False`.  
2. **Attiva rifiuta** `wipe_crm=True` → `400 wipe_not_allowed_on_activate`.  
3. **Seconda Attiva** su già `active`: idempotente, nessun wipe, preserva `activated_at`.  
4. **Wipe dedicato** `WipeAgencyCrmBody`: `confirm=WIPE_CRM`, `reason` ≥10, opz. `confirm_agency_id`, lock atomico (409), audit `ops_security_events`.  
5. FE cabina: `wipe_crm: false`.  
6. Trail: `_record_ops_security_event` su activate e wipe.

**Criterio di chiusura Ops:** nessun percorso ordinario/ripetuto di Attiva cancella CRM. Wipe solo percorso esplicito. **Stato: implementato · testato localmente · verificato su staging (schema OpenAPI) · wipe mutativo Super Admin staging: non eseguito** (no credenziali super_admin staging in questo ciclo).

---

## 5. File modificati

### Ops + FE cabina (in PR #248 / `c549552`)

```
backend/apps/immoweb/founder_ops.py
backend/tests/test_ops_attiva_wipe_policy.py
backend/tests/test_d161_login_semplice.py
backend/tests/test_d156_onboarding_kyc.py
frontend/src/apps/immoweb/pages/FounderOpsPage.jsx
frontend/src/apps/immoweb/founder/pages/BridgeHomePage.jsx
frontend/src/apps/immoweb/founder/pages/BridgeTenantDetailPage.jsx
```

### B2C D01–D04 + residui (già in #248)

```
backend/apps/immocloud/portal_*.py, portal_common.py
backend/apps/immoweb/site.py, theme_*.py
backend/shared/db/public_visibility.py
backend/shared/utils/privacy_gate.py
frontend PropertyCard + cardReference.js
tests B2C / photo cache / contact
docs/reports B2C*
```

### RBAC kickoff (questo branch, post-merge)

```
backend/shared/auth/membership_service.py   # dual-write users.role
backend/shared/auth/dependencies.py         # prefer membership.operational_role
backend/tests/test_slice1_b01_b03.py        # regressione overlay ruolo
docs/reports/CICLO1-OPS-ATTIVA-WIPE-E-MERGE-248.md
```

---

## 6. Test locali

| Suite | Esito |
|-------|-------|
| Ops wipe + d161 + d156 + B2C hardening + photo cache (pre-merge) | **36 passed** |
| Ops wipe + RBAC kickoff (`test_slice1_b01_b03` nuovi + ops) | **13 passed** |

Log: `/opt/cursor/artifacts/ciclo1-ops-wipe-unit2.log`, `/opt/cursor/artifacts/ciclo1-rbac-kickoff-unit.log`

Casi Ops: default false · wipe=true rifiutato · Attiva ordinaria · già active · wipe senza confirm · wipe autorizzato · lock 409 · mismatch confirm_agency_id.  
Casi RBAC kickoff: dual-write `role` su membership · overlay membership su drift · super_admin non overlay.

---

## 7. Merge PR #248

| Voce | Valore |
|------|--------|
| Controlli pre-merge | tip Ops incluso; D01–D04 + residui; CI tip **SUCCESS**; MERGEABLE/CLEAN |
| File estranei | nessuno oltre B2C + Ops cabina + test/report correlati |
| Metodo | `gh pr merge 248 --merge` |
| Merge commit | `c342fb057ddb31b3b490c5c99d59edd6e7ca8403` |
| CI post-merge `main` | **SUCCESS** |
| Altre PR mergeate | **nessuna** |
| Deploy produzione commerciale | **non eseguito** |

---

## 8. Staging smoke (post-merge)

| Voce | Valore |
|------|--------|
| Progetto Railway | `omnia-api-staging` (env label `production` ≠ prod commerciale) |
| DB | `omnia_staging_e2e` |
| Deploy ID | `621c1b09-e44c-4a6c-a64d-2d499e73d703` **SUCCESS** |
| Instance | `21a0879bce09:2` |
| Codice sorgente upload | worktree @ `c342fb0` (merge #248) via `railway up` |
| FE | `https://omnia-frontend-staging.vercel.app` — home 200; **nessun redeploy FE** in questo ciclo (BE rifiuta già wipe su Attiva) |

### Evidenze HTTP / sintetico

| Check | Esito |
|-------|--------|
| `/api/health` ok + db ok | **PASS** |
| OpenAPI `wipe_crm` default `false` | **PASS** (pre-deploy era `true`) |
| OpenAPI `WipeAgencyCrmBody` presente | **PASS** |
| Search + D01 no `agency_id` | **PASS** (seed sintetico) |
| D04 `reference_code` su card search | **PASS** |
| Draft escluso da search | **PASS** |
| D02 foto `Cache-Control: private, no-store` | **PASS** |
| D02 revoke → 404 | **PASS** |
| D03 contact `{"ok": true}` senza CRM ids | **PASS** (`gdpr_consent=true`) |
| Cleanup seed `session_tag=ciclo1_smoke` | eseguito |

Artefatti: `/opt/cursor/artifacts/ciclo1-staging-smoke.json`, `ciclo1-staging-smoke-deep.json`, `ciclo1-contact-smoke.json`, `ciclo1-railway-up-api.log`.

**Distinzione:** schema Ops **verificato su staging**. Wipe mutativo Super Admin e Attiva end-to-end con cookie Founder staging = **non verificato** (login admin vault ≠ staging).

---

## 9. RBAC kickoff (avvio — non chiuso)

### Mappa (stato attuale)

| Superficie | Comportamento |
|------------|---------------|
| `users.role` | ancora usata da `require_roles` / JWT issue |
| `memberships.operational_role` | modello B01 già presente; una membership attiva |
| `activate_exclusive_membership` | **ora** dual-write anche `users.role` |
| `get_current_user` | **ora** preferisce `operational_role` se membership attiva; non override `super_admin`/`client` |
| Inviti | già scrivevano `users.role` post-accept |
| Cambio org / multi-role per org | ancora “exclusive membership” — migrazione multi-membership **non** forzata |
| B14 session SoT | preservato (`assert_access_session`) |

### Dipendenze / blocchi

- Molte route e test assumono `users.role` globale.  
- Wallet DES-08 usa `require_roles_exact` (da preservare).  
- Multi-org con ruoli diversi richiede membership multiple attive o switch esplicito — **decisione architetturale già approvata come obiettivo**, implementazione completa = fase successiva.

### Correzioni sicure già applicate in questo ciclo

1. Dual-write `role` in `activate_exclusive_membership`.  
2. Overlay request-scoped da membership in `get_current_user`.  
3. Test regressione.

**Non chiuso:** inviti scaduti/revocati matrix completa, sospensione, manipolazione ID cross-org, FE role display, audit eventi cambio ruolo dedicati.

---

## 10. Tools / servizi esterni (kickoff read-only)

| Servizio | Funzione | Stato ciclo 1 | Note |
|----------|----------|---------------|------|
| GitHub + Actions | SoT codice / CI | **attivo e verificato** | CI tip + CI main SUCCESS |
| Railway `omnia-api-staging` | API staging | **attivo e verificato** | deploy `621c1b09…`; health ok; Stripe Test |
| Vercel `omnia-frontend-staging` | FE staging | **attivo** (home 200) | redeploy FE non obbligatorio per Ops BE |
| Mongo `omnia_staging_e2e` | DB staging | **attivo e verificato** | ping + seed sintetico; accesso via TCP proxy |
| Stripe | billing | **Test only** presente | Live **escluso** |
| Resend | email | presente in vault | **nessuna email reale**; scope 403 residuo da cicli precedenti **non ri-verificato** qui |
| JWT_SECRET / auth | sessioni | presente | B14 invariato |
| fal / Gemini / Tavily / OpenAPI Visura | AI/integrazioni | presenti in vault | **non verificati funzionalmente** in ciclo 1 |
| YouSign | firma | key presente | **non attivato/verificato** |
| Cloudflare | DNS/CDN | WAIT in check-secrets | **non verificato** |
| Error tracking / APM / WAF / backup off-host | ops GTM | **non presenti / non verificati** | gate GTM successivi |
| MCP Cursor (github, cloud, subscriptions) | agent | **usati** | CI subscribe + merge + secrets presence |

**Staging non punta a Stripe Live** (class `sk_test` in agent env; Railway `STRIPE_ENABLED=true` con attesa Test).  
**Non** acquistati/attivati nuovi servizi.

---

## 11. Rischi residui / next (priorità)

| Priorità | Voce | Stato |
|----------|------|-------|
| P0 chiuso | Ops Attiva wipe default | **chiuso** codice+unit+schema staging |
| P0 chiuso | Merge #248 + CI main | **chiuso** |
| P1 | Redeploy FE staging (cabina `wipe_crm:false`) | residuo minore (BE già protegge) |
| P1 | RBAC per-org completo + test matrix mandato | **kickoff fatto**; continua |
| P1 | Isolamento multi-tenant deep (oltre B2C) | successivo |
| P1 | Documenti/chat/storage audit | successivo |
| P1 | Backup/restore dimostrato | gate GTM |
| P1/P2 | Privacy / rate limit load | successivo |
| P1/P2 | Wallet regressione mirata | successivo |
| Gate | Pentest indipendente prep | successivo |

---

## 12. SHA e verdetto ciclo 1

| Commit | Contenuto |
|--------|-----------|
| `c549552…` | fix Ops Attiva/wipe (incluso in #248) |
| `c342fb0…` | **merge #248 → main** (verificato) |
| tip branch `cursor/ciclo1-gtm-ops-merge-b894` | report + RBAC kickoff (questo documento / commit) |

### Risultato effettivo

1. Ops wipe policy **implementata e testata**.  
2. PR **#248 MERGED** su `main` @ `c342fb0`.  
3. Staging API redeploy + smoke B2C/Ops schema **PASS** (D03 contact con GDPR).  
4. RBAC kickoff **implementato** (dual-write + overlay) — **non** chiusura fase RBAC.  
5. Tools audit **avviato** (tabella §10).  
6. **NON GTM READY** (gate §17 programma: backup/restore, pentest, RBAC completo, ecc. aperti).

### Prossimo intervento tecnico immediatamente eseguibile

Continuare **RBAC per-organizzazione**: mappa completa scritture `users.role`, test matrix (invito/revoca/sospensione/cambio org/sessione pre-cambio), audit eventi ruolo; poi isolamento multi-tenant deep sugli aggregati CRM non ancora coperti dal B2C.

---

Fine report ciclo 1.

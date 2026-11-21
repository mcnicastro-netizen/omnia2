# OMNIA — PRE-GTM Readiness Master

**Avviato:** 2026-11-21 19:45:38 CET (Europe/Rome)  
**Aggiornato:** 2026-11-21 22:05 CET (Europe/Rome) — W4 remediation (verdetto B, blocchi infrastrutturali chiusi)  
**Branch W4:** `cursor/w4-staging-e2e-b894` @ tip docs remediation · API `3f34c5f` · FE Vercel `5a8adaf`  
**HEAD locale (branch W4):** tip docs + working tree D175 storici preservato  
**Metodo:** programma di avanzamento tecnico (non audit fine a sé stesso)  
**Vincoli:** nessun commit/push/deploy/remote write in questo ciclo; riparazioni e test locali autorizzati

---

## 1. Stato iniziale

| Voce | Valore |
|------|--------|
| Working tree | Sporco (PRE-C D-175 + post-forensic B8/DEF-01 + questo ciclo) — **preservato** |
| Stack locale | API `127.0.0.1:43121` UP; FE preview UP; Mongo locale UP (`DB_NAME=omnia`) |
| Seed locale | `demo-agency-001` presente; ~2 agencies, 3 users, 8 properties, 7 clients |
| Suite test backend | ~181 file in `backend/tests/` |
| Stress tooling esistente | `backend/scripts/stress_gestionale.py`, `stress_scale_ladder.py`, `stress_platform_full.py` |
| D-175 PRE-C | Codice locale post-forensic presente; staging/Package C **non** certificati |

### Attribuzione working tree (ricostruzione)

| Origine | Contenuti tipici |
|---------|------------------|
| D-175 PRE-C / post-forensic | `scripts/d7_e2e/*`, test remediation/B8, report D175-*, `provider_flags`/`send_email`/`server` health |
| Altri interventi preesistenti | Report OMNIA-S1-*, blueprint staging E2E, MD audit vari untracked |
| Questo ciclo PRE-GTM | `scripts/pre_gtm_local_capacity_probe.py`, docs `docs/pre-gtm/*`, master, cache health TTL, report JSON |

---

## 2. Architettura effettivamente rilevata

| Layer | Implementazione | Evidenza |
|-------|-----------------|----------|
| Backend | FastAPI monorepo, entry `backend/server.py` | Logical monorepo D-015 |
| Apps | `apps/core`, `immoweb`, `immocloud`, `billing`, `academy`, `marketing` | `backend/apps/` |
| Frontend | React (CRA/craco), `frontend/src/App.js` Routes | ImmowebApp, ImmobilCloud, auth pages |
| DB | MongoDB via Motor; `Database` + `TenantAwareDatabase` | `shared/db/connection.py`, `tenant_guard.py` |
| Multi-tenant | ContextVar `agency_id`; inject su `/api/app/*` | `tenant_middleware.py` |
| Auth | JWT cookie + roles | `apps/core/auth.py` |
| Email | `shared/email/client.send_email` → Resend unico | choke point verificato |
| Kill provider | Mongo `provider_flags` + circuit memory + pre-transport check | post-forensic B8 |
| Deploy | Railway API + Vercel FE (secrets presenti in vault locale) | `check-secrets-presence.sh` |

Documenti satellite: `docs/pre-gtm/01-functional-e2e.md`, `02-security-multitenant.md`, `03-database-infra.md`, `04-load-stress.md`, `05-resilience-recovery.md`, `06-observability.md`, `07-distributed-release.md`.

---

## 3. Perimetro funzionale (da decisioni approvate — non riaperto)

Gestionale immobiliare multi-tenant: auth, organizzazioni/filiali/CommercialCustomer, inviti/membership, immobili/incarichi/documenti, visite/Deal/MLS/chat/notifiche, billing/crediti/storage, B2C ImmobilCloud secondo roadmap.  
Fonte: `memory/DECISIONS.md`, PRD/roadmap esistenti. **Nessun nuovo requisito inventato.**

---

## 4. Workstream — stato

| WS | Nome | Stato ciclo | Note |
|----|------|-------------|------|
| W1 | Integrità repo / baseline | **AVANZATO** | Baseline documentata; no reset |
| W2 | Completezza funzionale | **PARZIALE** | Mappa flussi + tooling; E2E completo non rieseguito tutto |
| W3 | Multi-tenant / sicurezza | **CODICE IN STAGING (non cert. GTM)** | B14 deployato su `omnia-api-staging` (`3f34c5f`); report W3 locali + `OMNIA-W4-STAGING-E2E-REPORT.md` · `OMNIA-W4-REMEDIATION-REPORT.md` |
| W4 | Staging E2E distribuito | **B — NON SUPERATO** | Matrice W4-01…24: FAIL repliche (volume); BLOCKED L5/Stripe/fail-closed/cross-replica; invite fix OK — `OMNIA-W4-STAGING-E2E-REPORT.md` · `OMNIA-W4-REMEDIATION-REPORT.md` |
| W4 | DB / integrità | **PARZIALE** | Inventario locale; indici/query deep-dive aperto |
| W5 | Prestazioni / stress | **AVANZATO LOCALE** | Probe nuovo + script storici; ladder grande non rieseguita |
| W6 | Infra / capacità | **APERTO** | Staging/Railway capacity **non** misurata qui |
| W7 | Resilienza / recovery | **PARZIALE** | Circuit/email kill locale; restore remoto non eseguito |
| W8 | Osservabilità | **AVANZATO** | Health instance_id + resend_kill; fix cache TTL |
| W9 | PRE-C D-175 | **LOCALE OK / STAGING APERTO** | 72 PRE-C+B8 tests PASS |
| W10 | Release distribuita | **BLOCCATO** | Richiede commit/deploy autorizzati |

---

## 5. Problemi individuati (ciclo)

| ID | Severità | Area | Descrizione | Stato |
|----|----------|------|-------------|-------|
| PG-01 | ALTA | W5/W8 | `/health` con lettura Mongo kill su ogni hit → p95 ~327ms @40 worker | **RIPARATO** (cache 2s) → p95 ~193ms |
| PG-02 | ALTA | W5 | Health p95 ancora >100ms draft sotto fan-out (Mongo ping) | **APERTO** — soglia draft da ricalibrare / ottimizzare ping |
| PG-03 | ALTA | W5 | Match API O(active×searchers) — storico stress report | **CONOSCIUTO** — non riparato in questo ciclo |
| PG-04 | MEDIA | W3 | Suite authz B04 richiede cwd `backend/` — fragile da root | **DOCUMENTATO** |
| PG-05 | BLOCCANTE GTM | W9/W10 | B8 multi-replica staging, L5, T22 Mongo non eseguiti | **BLOCCATO** (auth remota) |
| PG-06 | ALTA | W2 | Seed locale minimo (8 props) ≠ dimostrazione gestionale completo | **APERTO** |
| PG-07 | ALTA | W3 | Tenant guard accettava `agency_id` client-supplied senza overwrite | **RIPARATO** + test `test_tenant_guard_inject.py` |
| PG-08 | MEDIA | W3 | `TENANT_COLLECTIONS` incompleto vs activities; deals/MLS restano out-of-guard (by design `$or`) | **PARZIALE** — activities+modulistica_documents+altri single-agency; deals/MLS documentati |
| PG-09 | ALTA | W3 | `TenantCollection.__getattr__` bypassava replace/distinct/bulk senza inject | **RIPARATO** |
| PG-10 | ALTA | W3 | Alias morto `modulistica_docs` ≠ collection reale `modulistica_documents` | **RIPARATO** |
| PG-11 | MEDIA | W3 | `Database.tenant_filter` poteva essere sovrascritto da `extra.agency_id` | **RIPARATO** |
| PG-12 | ALTA | W3 | Video public/status IDOR (ready-by-id / no agency) | **RIPARATO** |
| PG-13 | MEDIA | W3 | Guard senza context lasciava query non filtrate | **RIPARATO** (`TenantContextRequired`) |
| PG-14 | MEDIA | W3 | Deal/MLS update by id post-gate (TOCTOU) | **RIPARATO** (filtri actor) |
| PG-15 | ALTA | W3 | B2C/properties/billing mutazioni by-id; CC VAT join; checkout branch_admin; remove_member senza revoke | **RIPARATO** — `OMNIA-W3-STAGING-READINESS-REPORT.md` |
| PG-16 | MEDIA | W3 | Guard non scrubbava `$set.agency_id`; import_jobs fuori guard; MLS partner by-id | **RIPARATO** |
| PG-17 | ALTA | W3 | Access JWT restava valido ~15′ dopo revoke refresh (vs B14) | **RIPARATO** — `OMNIA-W3-SESSION-REVOCATION-FINAL-GATE.md` |
| PG-18 | MEDIA | W3 | Race create CC stessa P.IVA (sparse null `stripe_customer_id`) | **RIPARATO** + test concorrente |
| PG-19 | ALTA | W4 | Railway staging: replicas incompatibili con volume `/app/.media` | **APERTO** — blocca W4-02/06 |
| PG-20 | ALTA | W4 | Invite accept pubblico 500 sotto tenant guard | **RIPARATO** (`get_raw`, `3f34c5f`) |
| PG-21 | ALTA | W4 | Staging senza Resend/Stripe Test variables | **APERTO** — W4-19/21/22 BLOCKED |
| PG-22 | MEDIA | W4 | FE staging SHA `15b1978` ≠ BE `3f34c5f` | **APERTO** |

---

## 6. Riparazioni effettuate (questo ciclo)

1. **Health kill-flag cache TTL 2s** in `backend/server.py` — riduce contesa Mongo su probe concorrenti.  
2. **`scripts/pre_gtm_local_capacity_probe.py`** — probe riproducibile loopback-only.  
3. Documentazione master + satellite PRE-GTM.  
4. **Tenant guard force-`agency_id`** + `activities` in `TENANT_COLLECTIONS` + test inject (follow-up explore W3).  
5. **W3 adversarial hardening:** wrap replace/distinct; refuse bulk_write; denylist aggregate join; expand guarded collections; fix `tenant_filter`; orphan_gc raw; report `OMNIA-W3-TENANT-GUARD-E2E-VERIFICATION.md`.  
6. **W3 secondary paths:** video IDOR, fail-closed context, Deal/MLS actor filters, calendar/ledger/match_audit guard, HTTP dual-tenant Mongo — `OMNIA-W3-SECONDARY-ACCESS-PATHS-HARDENING.md`.  
7. **W3 residual IDOR:** document/chat/feedback actor filters; video job scope; social agency filters; HTTP suite → 12 scenari — `OMNIA-W3-RESIDUAL-IDOR-CLOSURE.md`.  
8. **W3 Staging Readiness:** B2C/CRM atomic owner filters; CC join gate; checkout/group/invite exact roles; remove_member membership+refresh; guard scrub; MLS partner filters; HTTP → 19 scenari; multi-processo locale; harness `scripts/w3_staging_harness` — `OMNIA-W3-STAGING-READINESS-REPORT.md`.  
9. **W3 Session Final Gate (B14):** `users.active_session_ids` + `session_epoch`; JWT `sid`/`sv`; assert su ogni richiesta autenticata; revoke logout/membership/cease cross-process; race P.IVA; harness session preflight — `OMNIA-W3-SESSION-REVOCATION-FINAL-GATE.md`.

(Riparazioni D-175 DEF-01/B8 appartengono al mandato post-forensic precedente; integrate in W9.)  
Inventario architettura arricchito da [Explore OMNIA architecture map](bc-b736ca10-e211-57c7-9e0f-26bff9904852) (~886 test fn, stress custom senza Locust/k6, split Railway/Vercel).

---

## 7–8. Test eseguiti e risultati

| Comando / suite | Risultato | Artefatto |
|-----------------|-----------|-----------|
| PRE-C harness+matrix+B8 | 72 passed | `/opt/cursor/artifacts/pre_gtm_w9_regression.txt` SHA `54364b88…` |
| Idem dopo health cache | 72 passed | `pre_gtm_w9_after_health_cache.txt` |
| Authz subset (backend cwd) | 30 passed | `pre_gtm_w3_authz_subset.txt` SHA `a5ed6efb…` |
| Capacity probe pre-cache | health p95 327ms, errors 0, unauth wall OK | `pre_gtm_capacity_probe_run.txt` |
| Capacity probe post-cache | health p95 193ms, errors 0, unauth wall OK | SHA `4184b6c0…` |
| Login smoke | eseguito nel probe (status in JSON) | `memory/reports/pre_gtm_local_capacity_probe.json` SHA `c3ed275b…` |

---

## 9. Metriche chiave (locale)

| Metrica | Pre-fix | Post-cache | Note |
|---------|----------|------------|------|
| `/api/health` p50 @40w/80req | 273ms | 163ms | Migliorato |
| `/api/health` p95 | 327ms | 193ms | Ancora sopra draft 100ms |
| Errori health | 0 | 0 | OK |
| Unauth `/app/properties` | 401/403 | 401/403 | Wall OK |

**Soglie proposte (non ratificate):** health p95 ≤200ms sotto 40 worker locali; error rate 0; ladder agenzie da DECISIONS (10→10k) resta obiettivo staging.

---

## 10. Attività bloccate

- Stress/spike/soak su Railway staging  
- Enumerazione repliche + L5 Resend  
- T22 Mongo staging  
- Commit/push/deploy SHA  
- Restore drill remoto  
- Ladder 5k/10k clienti (pesante; richiede conferma ambiente isolato anche se locale)

---

## 11. Dipendenze remote / autorizzazioni necessarie

1. Commit + push branch PRE-GTM/PRE-C.  
2. Deploy staging.  
3. Mandato staging: B8 attest + L5 + T22 (già specificato in report post-forensic).  
4. Mandato load: eseguire `stress_scale_ladder` / gestionale su staging isolato o dogfood.  
5. Ratifica soglie latenza/error rate Founder/tech.

---

## 12. Rischio residuo

| Rischio | Impatto GTM |
|---------|-------------|
| Capacità multi-agenzia non misurata su infra reale | Critico |
| Match O(n×m) sotto crescita | Alto |
| Health/DB ping sotto LB probe storm | Medio (mitigato cache kill) |
| Isolamento CC/filiale non ladder-completo in test | Alto |
| Working tree non pinabile su remote | Process |

---

## 13. Criteri di chiusura GTM (da direttiva §12) — scorecard

| # | Criterio | Stato |
|---|----------|-------|
| 1 | Flussi funzionali completi | NON VERIFICATO end-to-end completo |
| 2 | Isolamento multi-tenant | LOCALE PRONTO PER STAGING (19 HTTP Mongo + MP + B14 sessioni); staging non eseguito |
| 3 | Concorrenza / integrità | PARZIALE (P.IVA race chiusa; stress full non rieseguiti) |
| 4 | AuthZ affidabile | LOCALE AVANZATO (session revoke immediato verificato; staging non cert.) |
| 5 | Billing/crediti/storage | NON VERIFICATO in questo ciclo |
| 6 | Stabilità DB | LOCALE OK minimo |
| 7 | Capacità traffico misurata | LOCALE BASELINE ONLY |
| 8 | Stress controllato | TOOLING READY; full ladder non rieseguita |
| 9 | Recovery | PARZIALE |
| 10 | Backup/restore dimostrabile | NON ESEGUITO |
| 11 | Monitoraggio/alert | PARZIALE (health migliorato) |
| 12 | Codice verificato = distribuito | BLOCCATO (no deploy) |
| 13 | Criticità bloccanti risolte | NO (staging PRE-C aperti) |
| 14 | Evidenze per decisione GTM | INSUFFICIENTI per go |

---

## 14. Stato complessivo di readiness

**READINESS GTM: NON PRONTO.**

Avanzamento reale di questo ciclo:
- Metodo e scorecard istituzionalizzati.
- Baseline capacità locale misurata e riparazione performance health.
- W9 PRE-C locale ancora verde.
- Percorso chiaro alle autorizzazioni remote successive.

**Non** confondere 72/30 test verdi e un probe locale con capacità GTM.


## W4 remediation (2026-11-21 22:05 CET)

- Verdetto ancora **B** (L5/Stripe BLOCKED per variabili assenti su Railway staging).
- Chiusi: W4-02/06 multi-istanza (`omnia-api-w4b`), FE align, W4-08 fail-closed isolato, W4-13 visite/deal, B8 kill A/B.
- SoT dettagli: `OMNIA-W4-REMEDIATION-REPORT.md`.

# D175-PR240-DEFINITIVE-REMEDIATION-REPORT

## A. Identificazione
| Campo | Valore |
|-------|--------|
| Branch | `cursor/d175-deal-chat-dossier-h4-e393` |
| SHA iniziale | `fafab3d61d1b9b77b21947c02d0be6c22554b488` |
| SHA finale | `aacd664706eae530e57a0ac6c1ff5a71dd8b705a` |
| Commit remediation | `68b0fc6` (fix) + `aacd664` (docs pin) |
| PR | https://github.com/mcnicastro-netizen/omnia2/pull/240 |
| Ambiente | Dogfood `OMNIA_ENV=dogfood` · `DB_NAME=omnia_df_clean_c4` · Mongo `:27018` |
| Working tree pre-intervento | pulito |
| Merge | **NON eseguito** |

## B. Registro difetti FIX-01…06

### FIX-01 — Webhook `subscription.deleted`
- **Causa:** update per `agency_id` poteva cancellare sub attiva successiva.
- **Modifica:** chiave primaria `stripe_subscription_id`; fallback `agency_id` solo se id assente; check coerenza CC/agency; idempotenza se già canceled.
- **File:** `backend/apps/billing/routes.py`
- **Test:** `test_fix01_*` — PASS
- **Evidenza:** suite remediation

### FIX-02 — Isolamento thread chat
- **Causa:** `find_one` senza scope esatto riusava thread visita/deal.
- **Modifica:** `scope_key` canonico `collab|v:…|d:…` + query esatta.
- **File:** `shared/mls_collab/service.py`, `collaborations.py`
- **Test:** `test_fix02_*` + E2E scope — PASS

### FIX-03 — Revoca → documenti
- **Causa:** revoke non toccava `mls_document_requests`; access ignorava collab.
- **Modifica:** revoke massivo richieste; `assert_document_request_accessible`; download/access/chat attachment rispettano revoke.
- **File:** `collaborations.py`, `service.py`
- **Test:** `test_fix03_*` + E2E residual deny — PASS

### FIX-04 — Deal su collab non attiva
- **Causa:** `open_deal` senza check status.
- **Modifica:** `require_collaboration_active`; mutazioni Deal bloccate se collab revocata; Deal senza collab solo su property propria (regola esplicita).
- **File:** `deals.py`
- **Test:** `test_fix04_*` — PASS

### FIX-05 — Duplicazione da offerta
- **Causa:** `ensure_collaboration_from_offer` ignorava `pending`.
- **Modifica:** ritorna pending/active esistenti **senza** auto-attivare pending; nuova active solo se assente.
- **File:** `service.py`
- **Test:** `test_fix05_*` — PASS

### FIX-06 — Gate MLS
- **Causa:** solo owner ≠ self.
- **Modifica:** stessi gate di `create_offer` (`visibility`, `mls_shared`, `mls_enabled` owner/requester).
- **File:** `collaborations.py`, `service.assert_mls_listing_shareable`
- **Test:** `test_fix06_*` + E2E private gate — PASS

## C. Lacune funzionali

### Watermark
- **Completato:** watermark **reale** su PNG/JPEG (Pillow) e PDF (reportlab/pypdf); originale in `mls_document_artifacts`; copia tracciata in `mls_document_distributions`; endpoint `/download` con header `X-OMNIA-Watermark`; formati non supportati rifiutati.
- **Verificato:** download Dogfood 9643 byte JPEG valido, header watermark=1.
- **Limite:** formati non image/pdf non dichiarati protetti (HTTP 400).

### Rating / controversie
- **Completato:** dedupe feedback visit+agency; contest da agenzia valutata; resolve Super Admin con audit `mls_rating_dispute_audit`; aggregato pubblico senza storico individuale; contested esclusi fino a risoluzione.
- **Verificato:** unit test contest/dismiss/aggregate.
- **Limite:** UI Super Admin dedicata minimale (API completa); nessun canale CRM indiscriminato aggiunto.

### Deal authz / UI
- **Completato:** `allowed_transitions` + `role` in API; partner `partner-respond` (accepted/rejected/counter); FE mostra solo azioni consentite; deep-link da Collaborazioni.
- **Verificato:** E2E owner 403 su accept, partner accept OK.

### Persistenza / indici
- **Completato:** indici su collaborations, visits, feedback (unique visit+from), chat `scope_key`, document_requests, deals, subscriptions stripe id — in `ensure_indexes` (idempotenti, no delete dati).
- **Limite:** unique feedback può fallire se duplicati storici preesistenti (create_index catch/log).

### Frontend
- Deep-link MLS ↔ Collaborazioni ↔ Deal; download watermark; stati revoca; azioni Deal filtrate.
- Non è un redesign estetico.

## D. Test
| Suite | Risultato | Log |
|-------|-----------|-----|
| Unit remediation + collab/deal | **22 PASS** | `/opt/cursor/artifacts/d175-pr240-pytest.log` |
| C5 H4 purchase authz | **34 PASS** | `/opt/cursor/artifacts/d175-pr240-h4-regression.log` |
| E2E Dogfood remediation | **PASS** | `/opt/cursor/artifacts/d175-pr240-e2e-smoke.log` |
| Stripe checkout TEST reale | **BLOCKED H4** | `H4_ready False` |
| CI PR (SHA finale) | da verificare post-push | |

Flusso E2E: collab → visita → feedback(+dedupe) → chat scope → doc fulfill → **download watermarkato** → Deal + partner accept → foreign deny → revoke → deny residui → gate MLS private.

## E. Sicurezza
- Authz backend su collab/doc/chat/deal; revoke coerente; deny cross-org; nessun bypass H4; webhook deleted non muta CC operational; Super Admin dispute scoped + audit.

## F. Stripe
| Tipo | Stato |
|------|--------|
| Mock / gate H4 | PASS (C5) |
| Webhook deleted mapping | Corretto + test |
| Checkout / crediti / storage TEST live | **BLOCKED — AUTHORIZATION REQUIRED** (sealed) |
| LIVE | non usato |

## G. Residui
1. **Low** — UI Super Admin dispute: solo API (no pagina dedicata).
2. **Low** — Indice unique feedback: rischio skip se duplicati storici in DB non-dogfood.
3. **Info** — Stripe TEST checkout completo resta BLOCKED da H4 sealed (fuori autorizzazione).
4. **Info** — Watermark video/audio non supportato (rifiutato, non dichiarato protetto).

## H. Verdetto
**`PARTIALLY READY — EXPLICIT RESIDUAL GAPS`**

Pronto per review finale Founder sulla remediation dei 6 bug + watermark reale + rating/dispute + Deal roles. Non production-ready dichiarato. Residui espliciti sopra. **Nessun merge eseguito.**

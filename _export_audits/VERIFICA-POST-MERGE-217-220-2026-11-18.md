# OMNIA — Verifica post-merge #217–#220 + allineamento documentale (Opzione 3)

**Data verifica:** 18 novembre 2026 · ~13:00 Europe/Rome  
**Repo:** `mcnicastro-netizen/omnia2`  
**Branch verificato:** `origin/main`  
**HEAD verificato:** `6a1293238329f2095455fe8fde4639e9a249c7cf` (= commit dichiarato Founder `6a12932`)  
**Natura:** sola lettura codice + aggiornamento documentale successivo. **Nessun merge, nessun deploy, nessun commit** in questa consegna (attende autorizzazione Founder per push docs).

Fonti GitHub usate: `gh pr view`, `git fetch origin main`, Checks API.  
**Non** usati come prova: report chat precedenti.

---

## A. Stato Git

### Main

| Check | Esito |
|---|---|
| `origin/main` HEAD | `6a1293238329f2095455fe8fde4639e9a249c7cf` |
| Messaggio | `Merge pull request #220 from …/mc042-v2-suspend-deroga-e393` |
| Timestamp | 2026-11-18 11:38:07 UTC (= **12:38 Europe/Rome**) |
| `6a12932` è ancestor di `origin/main` | **Sì** (coincide con HEAD) |
| CI su tip `6a12932` | `Backend billing / B04 unit` → **success** |

### PR #217–#220 (stato GitHub effettivo)

| PR | Stato GitHub | mergedAt (UTC) | Merge commit | Head tip PR | Presente su main? | Contenuto effettivo su main | CI merge-commit | Conclusione |
|---|---|---|---|---|---|---|---|---|
| **#217** | **MERGED** | 11:15:44 | `684eb8a` | `2d6d91f` | **Sì** | Docs master / firme / MC-042 v2 / MC-054…059 decisioni | success | Discrepanza «Open» **smentita** — GitHub API = MERGED |
| **#218** | **MERGED** | 10:03:37 | `547f67f` | `413d2aa` | **Sì** | Wallet deny ceased + fail-open senza CC | success | Discrepanza «Open» **smentita** — MERGED |
| **#219** | **MERGED** | 11:19:17 | `4946390` | `047225c` | **Sì** | MC-040 Accetta · MC-041 job expiry · MC-043 nomina | success | Confermato |
| **#220** | **MERGED** | 11:38:08 | `6a12932` | `c3b5bd2` | **Sì** (= HEAD) | MC-042 v2 lockout · MC-054 B · MC-055…059 deroga | success (su tip PR `c3b5bd2` e merge) | Confermato |

**Sulla discrepanza «#217/#218 Open»:** verifica indipendente via `gh pr view` + merge-base → entrambe **MERGED**. Probabile causa: lista UI/ChatGPT stale, filtro «Open», o cache sidebar. **Non** risultano aperte. Le modifiche sono su `main` tramite i merge commit indicati (non tramite PR surrogate successive).

Catena tipica su `main` (nuovi → vecchi):  
`6a12932` (#220) → `4946390` (#219) → `684eb8a` (#217) → `547f67f` (#218) → …

---

## B. Verifica implementativa

Legenda: **CONFORME** / **PARZIALE** / **GAP** / **NON VERIFICATO E2E** / **MANCANTE**.

### B1. MC-042 v2 — cessazione (`ceased` / `closed_readonly`)

| Requisito Founder | Evidenza codice su `main` | Esito |
|---|---|---|
| Login disabilitato | `assert_user_login_allowed` in `apps/core/auth.py` login, `google_auth.py`, `mfa_routes.py` | **CONFORME** (gate; password hash **non** azzerato) |
| Sessioni / accesso autonomo bloccati | `enforce_commercial_access` in `get_current_user` (`shared/auth/dependencies.py`) | **CONFORME** sulle API che usano `get_current_user` |
| Refresh token | `POST /auth/refresh` **non** chiama `assert_user_login_allowed` né `enforce_commercial_access` — rinnova access cookie se refresh ancora valido | **GAP / PARZIALE** — non usa API gated, ma può rinnovare access; sessioni **non** revocate al momento del cease |
| Nessun read-only piattaforma | Gate 403 su ceased in `get_current_user` (salvo `super_admin`) | **CONFORME** (per route autenticate standard) |
| Nessun wallet | `cc_is_wallet_operable` nega `ceased` / `closed_readonly`; assert allocate/revoke/spend | **CONFORME** |
| Nessuna consultazione autonoma fatture/docs | Nessuna API self-serve post-cessazione; hint 403 email SA | **CONFORME di fatto** (assenza self-serve); canale email = processo manuale |
| Conservazione dati | Nessun delete su cease in path verificato; `set_commercial_status` setta `ceased_at` | **CONFORME (principio)** — **NON VERIFICATO E2E** wipe accidentale |
| Super Admin bypass | `role == super_admin` skip gate | **CONFORME** |

### B2. MC-054 — sospensione giorno 8 (opzione B)

| Requisito | Evidenza | Esito |
|---|---|---|
| Collaboratori bloccati | `enforce_commercial_access`: non-MA → 403 `commercial_customer_suspended` | **CONFORME** (unit `test_mc042_v2_suspend_deroga`) |
| MA autenticabile solo billing | Allowlist path in `is_billing_recovery_path` (subscription/plans/checkout/portal/status/main-admin/auth/me|logout|refresh/notifications) | **CONFORME** unit; **NON VERIFICATO E2E** FE |
| Wallet/crediti consultazione deny | `cc_is_wallet_operable` nega `suspended` e `billing_only` | **CONFORME** (superato stato tabella doc pre-#220) |
| Allocate/revoke/transfer deny | `assert_cc_wallet_operable` | **CONFORME** |
| Spend deny | `_spend_blocked` include suspended + operable false | **CONFORME** |
| Transizione giorno 8 | Job `apply_day8_suspensions` (past_due ≥8g via `payment_failed_at`/`updated_at`) + cron manuale | **CONFORME modello**; **NON VERIFICATO** timing reale Stripe |
| Deroga ≠ riattivazione | Deroga attiva bypassa gate senza forzare `commercial_status=active` finché non paid/ops | **CONFORME** |

Nota CI: workflow `.github/workflows/ci.yml` **non** esegue `tests/test_mc042_v2_suspend_deroga.py` (solo suite B04 elencata). Unit esistono sul repo; **non** sono nel job CI tip.

---

## C. Verifica Stripe — `invoice.paid` / MC-055…059

### Percorso

1. Webhook `POST /billing/webhook` → `etype == "invoice.paid"`.
2. Upsert invoice locale; grant crediti piano.
3. Risolve `commercial_customer_id` da metadata invoice **oppure** da agency collegata.
4. Chiama `reactivate_cc_on_full_payment(db, cc_id)`.

### `reactivate_cc_on_full_payment` (evidenza)

- Skip se CC assente / `ceased`.
- Se status ∈ `{suspended, grace, cancel_pending}` → set `commercial_status=active`, `operational_status=full`.
- Chiude deroghe `active` → `closed_paid`.
- Se già `active` → `skipped: already_active` (quasi-idempotente).

### Risposte obbligatorie (1–10)

| # | Domanda | Risposta verificata |
|---|---|---|
| 1 | Come si calcola il debito complessivo CC? | **Non calcolato** in questo path. Nessuna somma fatture open/`amount_remaining`/`amount_due` aggregate sul CC. |
| 2 | Tutte le fatture insoluti rilevanti? | **No** — non interrogate. |
| 3 | Fatture scadute / pagamenti parziali? | **Non valutati** prima della riattivazione. |
| 4 | `invoice.paid` può riattivare con altri insoluti? | **Sì, possibile** — basta un `invoice.paid` con CC risolvibile e status sospeso/grace/cancel_pending. |
| 5 | Riattivazione subordinata a saldo integrale? | **Decisione sì; codice no** — lag semantico. Nome funzione ≠ verifica saldo pieno. |
| 6 | Conferma Stripe idempotente? | Invoice upsert per `stripe_invoice_id`; riattivazione ripetuta su active è no-op soft. **Nessun** store `stripe_event.id` visto nel handler (dedup evento non dimostrato). |
| 7 | Eventi duplicati / fuori ordine? | Rischio basso su active già; rischio **riattivazione prematura** se unpaid paralleli. Fuori ordine non gestito esplicitamente. |
| 8 | Deroga → definitiva solo dopo saldo pieno? | Codice: qualsiasi `invoice.paid` chiude deroga come `closed_paid` + active — **stesso gap saldo**. |
| 9 | Scadenza deroga → sospensione? | **Sì** — `expire_due_deroghe` + job 15m; email best-effort. |
| 10 | Nuova deroga evita sospensione senza cancellare traccia? | Grant supersede precedenti a `superseded`; expire non cancella docs. **CONFORME traccia**. |

**Classificazione:** discrepanza **implementativa vs decisione Founder MC-055** — **non** bugfixato in questo incarico; **non** modificato codice.  
**Rischio:** commerciale (cliente riattivato con debito residuo reale).  
**Test proposto (futuro incarico):** fixture CC suspended + 2 invoice open; paga solo 1 → assert **non** active; paga entrambe / saldo zero Stripe → active.  
**Mandato codice:** solo con `OMNIA — AUTORIZZAZIONE ESPLICITA ALL'IMPLEMENTAZIONE` + scope MC-055 saldo.

### MC-056…059 (sintesi)

| Item | Esito |
|---|---|
| Grant deroga Ops (`/ops/.../reactivation-deroga`) | **PRESENTE** |
| Durata/scadenza obbligatorie | **PRESENTE** |
| Email cliente on grant | **PRESENTE** best-effort |
| Reminder SA 48h | **PRESENTE** (`remind_deroghe_expiring_soon`) |
| Expire → suspended + email | **PRESENTE** |
| Indipendenza per CC | **PRESENTE** (collection keyed by `commercial_customer_id`) |
| Template email dedicati | **PARZIALE** — riusa `agency_pending` |

---

## D. Discrepanze (sintesi)

| ID | Tra | Descrizione | Gravità |
|---|---|---|---|
| D-GIT-01 | Handoff vs GitHub stale | «#217/#218 Open» vs API **MERGED** | Risolta — stale view |
| D-DOC-01 | `NEXT_SESSION.md` vs main | Baseline `547f67f`, 040/041/043 e 042/054 come non impl | Docs stale (allineato in Fase E) |
| D-DOC-02 | Piano Master datato 17/11 / baseline `c3baebc` | Superato da `6a12932` | Docs stale (allineato) |
| D-DOC-03 | Tabella tecnica MC-054 @ `547f67f` | Dice NON CONFORME wallet `billing_only` | Superata da #220 (allineata) |
| D-CODE-01 | MC-055 saldo pieno | `invoice.paid` senza check debito residuo | **CHIUSA** 18/11 — Founder «fix» · `list_outstanding_invoices_for_cc` (branch `cursor/mc055-saldo-pieno-e393`) |
| D-CODE-02 | MC-042 refresh | `/auth/refresh` senza gate ceased/suspended | **Aperta — minore**; API successive gated |
| D-CODE-03 | Revoca sessioni al cease | Nessun `revoke_all_refresh` al set ceased | **Aperta — minore/medio** |
| D-CI-01 | Test deroga | `test_mc042_v2_suspend_deroga.py` non in CI job | Igiene CI (non prodotto) |

---

## E. Documenti

### Aggiornati in working tree (attende commit Founder)

- `_export_audits/VERIFICA-POST-MERGE-217-220-2026-11-18.md` (questo report)
- `memory/NEXT_SESSION.md`
- `_export_audits/MASTER-CHIUSURA-POST-AUDIT-PIANO.md` (baseline + stati MC rilevanti)
- `_export_audits/MASTER-STRATO-B-REPORT-FINALE-BOZZA.md`
- `_export_audits/MC-054-059-SOSPENSIONE-RIATTIVAZIONE-DEROGA.md` (tabella tecnica)
- Nota stato in `_export_audits/MC-042-DECISIONE-FOUNDER.md` già aggiornata in #220; lasciata coerente / ritocco se serve

### Non toccati (motivazione)

- `B04-DES-REGISTRO.md` / `B04-OPEN-FOLLOWUPS.md` — design/OPEN-01 non cambiati da #217–220
- `B04-H2-*-CONFORMITY/REPORT` — H2 già chiuso; no regressione doc richiesta
- Handoff 14 nov — resta STALE; non riattivato
- Codice / test / CI workflow — **vietati** da incarico

---

## F. Strato B

| Voce | Stato |
|---|---|
| Dichiarazione Founder `MASTER STRATO B CHIUSO` | **Confermata** (D-182b / MC-026b) |
| Riserve MC-042 v2 / MC-054 / MC-055…059 | **Affrontate in codice** su main via #218+#220 |
| Evidenze unit | Presenti; CI tip verde su suite B04 **senza** file deroga dedicato |
| Punti non verificati E2E | FE billing recovery; Stripe live events; multi-invoice debt |
| Gap aperti da classificare (non riaprono B) | D-CODE-01 (saldo), D-CODE-02/03 (refresh/session) |

**Chiusura Master A+B ≠ readiness produzione (Strato C).**

---

## G. Strato C — matrice e raccomandazione

| Pacchetto | Dipendenze | Impatto funzionale | Rischio sicurezza | Rischio dati | Rischio commerciale | Test | Prereq / decisioni |
|---|---|---|---|---|---|---|---|
| **MC-055 fix saldo** (gap D-CODE-01) | #220 | Alto — allinea decisione | Medio | Basso | **Alto** | Multi-invoice unpaid | Founder: conferma regola «qualsiasi invoice.paid» vs «zero open balance» |
| MC-042 refresh/session revoke | #220 | Medio | Medio | Basso | Basso | Cease + refresh | Opzionale hardening |
| MC-045 H3 allocate org-CC | H1/H2 | Medio isolamento | Medio | Basso | Medio | Cross-org allocate | Nessuna decisione nuova |
| MC-046 H4 Stripe Customer CC | DES-01 | Medio billing | Basso | Medio | Medio | Checkout top-up | — |
| MC-030 B04-III allowance | DES | Alto cicli | Basso | Medio | Alto | Allowance cycle | Slice design ready |
| MC-031…034 B04-IV…VII | MC-030 | Alto | Medio | Medio | Alto | Stati/entitlements | Sequenza |
| MC-035…037 B01–B03 impl | Design chiusi | Alto piattaforma | Alto | Alto | Medio | Ampio | Mandato ampio |
| MC-047/048 legacy/B07 | Modello | Alto migrazione | Medio | **Alto** | Alto | Reconcile | Umano |
| MC-049 Stripe live/prod | Tutto C | Critico | Critico | Critico | Critico | Runbook | **Mandato dedicato** |
| MC-038/039 B05/B06 | — | — | — | — | — | — | FUORI_MASTER |
| B04-OPEN-01 repricing | DES-03 | Commerciale | Basso | Basso | Alto | — | Sessione Founder |

**Raccomandazione Cursor (non decisione):**  
1) Prima chiudere **D-CODE-01 MC-055 saldo** (piccolo, alto rischio commerciale) **oppure** accettare esplicitamente «proxy invoice.paid = saldo» come deroga documentata.  
2) Poi igiene CI includendo test deroga.  
3) Poi primo slice C classico: **MC-045 H3** (sicurezza isolamento) prima di B04-III.  
**Founder sceglie.** Stripe live resta fuori.

---

## H. Decisioni Founder aperte (solo queste)

1. **MC-055:** confermi che la riattivazione debba richiedere **zero insoluti** sul CC (fix codice) **oppure** accetti l’attuale proxy «un `invoice.paid` ⇒ active» come regola operativa?
2. **Hardening sessione ceased:** vuoi revoca refresh + gate su `/auth/refresh` in un mini-incarico?
3. **Primo slice Strato C** dopo igiene docs: H3 (MC-045) · fix MC-055 · B04-III · altro?
4. **Autorizzazione commit/push** di questo allineamento documentale (nessun codice)?

---

## I. Integrità intervento

| Vincolo | Stato |
|---|---|
| Nessun file Python/JS/TS/config prodotto modificato in questa fase | **Da confermare a fine edit docs-only** |
| Nessun test applicativo modificato | Sì |
| Nessun DB / Stripe / webhook touch | Sì |
| Nessun commit / push | **Sì — attende tuo OK** |
| Nessun merge / deploy | Sì |

---

## Nota sulla domanda «perché continua a trovare lavori non ultimati?»

Perché tre piani diversi vengono spesso confusi:

1. **Master chiusura A+B** — oggi sostanzialmente chiuso in codice autorizzato.  
2. **Conformità perfetta decisione↔codice** — restano gap reali (es. MC-055 saldo).  
3. **Strato C / prodotto produzione** — volutamente infinito finché non si sceglie uno slice.

ChatGPT/verifiche elencano (2)+(3) come «non ultimato» anche quando (1) è fatto. La cura: etichettare ogni residuale come `RISERVA_CHIUSA` · `GAP_APERTO_DECISIONE` · `STRATO_C` · `FUORI_MASTER`, e non mischiarli.

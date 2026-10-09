# Cap. 00 · Architettura tenancy → jobs (audit SaaS)

**Ambito**: founder / super_admin.  
**Prompt master**: `memory/AUDIT_PROMPT_MASTER.md` (§1–§27).  
**Numerazione sessione**: continuum in `AUDIT_ARCHITETTURA_NOTE.md`.

---

## Metodo

Un blocco alla volta · niente fix senza «vai» · no P0–P3 prematuri · **listino fermo** finché Backup+Restore non sono disegnati.

---

## Decisioni di dominio (codice ⏳)

| ID | Sintesi |
|----|---------|
| **D-094** | Trash ≠ status · filtro uniforme dominio (pre-GTM) · default non-trashed |
| **D-095** | Media pubblici vs privati · cleanup blob |
| **D-096** | Bak+Restore insieme · restore agency-first |
| **D-097** | Elimina per sempre ≠ irrecuperabile assoluto · trash in bak OK |
| **D-098** | Orphan → path a delete (WHEN col bak) · agency close V1 controllata |
| **D-099** | Founders GDPR assistito · fascicolo AuthZ **prima** del bak |
| **D-100** | Invite: utente esistente → link agency; **mai** overwrite password (**fix-needed** · **trasversale**) |
| **D-101** | Job automatici: **single-instance** ora (non lock multi-pod); worker poi |
| **D-102** | Purge + orphan cleanup: **automatizzare ora** nel ciclo APScheduler |
| **D-103** | No worker dedicato ora; eventuale anti-dup minimo stesso-giorno |
| **D-104** | **GTM-01 ACQUISITO** · in coda · **vincolo hard** pre-~5000 email |
| **D-105** | Bak health minimo Founder Ops (OK/PARTIAL/FAILED + alert + last_run) |
| **D-106** | `active_agency_id` = SoT; no fallback `agency_ids[0]`; missing = errore |
| **D-107** | Errori API: `code` stabile BE + i18n FE; feedback se altera significato azione |
| **D-108** | Scheduling: un solo owner di esecuzione (cron = trigger/fallback) |
| **D-109** | Pricing SoT = `GET /billing/plans`; landing allineata o nascosta; legacy esplicito |
| **D-110** | Demo mode esplicito; `localStorage` ≠ entitlement authority |
| **D-111** | Cestino = stato non operativo (freeze); storico preservato |
| **D-112** | Seed demo idempotente e deterministico |
| **D-113** | Restore manuale testabile pre-GTM (non piattaforma DR) |
| **D-114** | Sostenibilità bak/media = priorità pre-attivazione; O0 = numeri+design vincolante |
| **D-115** | Programma O0…O6 approvato · **no self-serve finché O6 ≠ PASS** |
| **D-118** | **Audit Portale ImmobilCloud** · onde **A–J GREEN** (analisi **9-Ott-2026**) · fascicolo `docs/audit/OMNIA_PORTALE_AUDIT_FASCICOLO.md` · finding `P-###` · fix solo con «vai» |
| **D-116** | OpenAPI Catasto sandbox: **una sola API key** (`OPENAPI_API_KEY` + fallback `ADMIN_EMAIL`) |

**SoT continuità:** `docs/audit/OMNIA_AUDIT_STATE.md` · `memory/NEXT_SESSION.md` · fascicolo D-118  
**Sequenza priorità (D-099):** fascicolo → orphan → Bak+Restore → retention → costi.  
**Niente codice** senza «vai».

### Cloud Agent — ID `bld-…` (7-Ott-2026)

Nella UI chat può comparire un ID tipo `bld-20261007-…`: è lo **snapshot Environment Build** (install già fatto), **non** un secret.  
Cursor lo tiene in Dashboard → Environments → Builds. **Non serve** salvarlo nel password manager; annotalo solo se vuoi pin/debug di quello snapshot. I secret restano nel vault (`CLOUD_SECRETS_INVENTORY.md`). HAL: `api.cloud-environment-builds`.

### D-118 — stato (aggiornato 9-Ott-2026)

**Analisi chiusa**: onde **A–J GREEN** · fascicolo Founder pronto.  
**Fix codice già fatti** (con «vai»): Ops P-025…P-030 · G P-035/P-036 · H GDPR P-037…P-044 (P-045 WONTFIX).  
**Coda aperta**: P-046…P-058 (+ P-033 dopo) — priorità **P-051 / P-049 / P-046**.  
SoT: `OMNIA_PORTALE_AUDIT_PROGRAM.md` · `OMNIA_PORTALE_AUDIT_FASCICOLO.md` · `portale-finding.md`.  
Post-test: **A-038** fattura Stripe + dati fiscali (solo con «vai»).  
HAL: `api.portale-audit-program` · `api.founder-ops-portale` · `api.visura-openapi-catasto`.

---

## Cluster aperti

| Cluster | Finding |
|---------|---------|
| Media / fascicolo AuthZ | P3.1 + M-01 + **G-02** → D-095/D-099 |
| Orphan / retention | RET-* · D-098 · **D-102** |
| Disaster recovery | B-* · R-* · D-096 |
| GDPR | G-* · D-099 (Founders assistito) |
| Race | **RC-*** · invite → **D-100** |
| Jobs | **J-*** · **JA-*** · **D-101**…**D-103** |
| Osservabilità | **O-*** · **D-105** |
| API / Frontend | **AF-*** |
| Coerenza prodotto | **CT-*** · **D-109** · **D-110** · P21 CHIUSO |
| Casi limite | **EC-*** · **D-111** · **D-112** · P22 CHIUSO |
| Debito architetturale | **AD-*** · **D-113** · P23 CHIUSO |
| Non lista infinita | **NI-*** · P24 CHIUSO · SoT ripago §25bis |
| Report finale | P25 A–K · ⏳ |
| GTM / Demo | **GTM-01 ACQUISITO** · **D-104** · in coda · pre-~5000 email |
| Portale B2C audit | **D-118** · A–J GREEN · fascicolo · coda «vai» `P-###` |
| Costo / listino | C-* · B-01 · fermo |

---

## Progresso

| Sessione | Master | Stato |
|----------|--------|--------|
| P1–P24 | §1–§24 | chiusi · D-094…D-114 · classificazione + D-114 bak/media |
| P25 Report finale | §25 | Consegnato · A–K · ⏳ analisi |
| D-118 Portale | A–J | ✅ GREEN analisi · fascicolo · coda «vai» P-046…P-058 |
| — | §23 Priorità | ⬜ CLOSED fino al «vai» |
| GTM-01 | post-audit | 🟠 **ACQUISITO** · in coda · smoke ~20 |

Dettaglio: `docs/audit/OMNIA_AUDIT_STATE.md` · `AUDIT_ARCHITETTURA_NOTE.md` · A-035 · A-036.
# 📘 PROGRAMMA OPERATIVO — Progetto OMNIA
## Dal MVP all'ecosistema completo · 6 Milestone · ~30 sessioni · 3-6 mesi

**Versione**: 3.1
**Data creazione**: Gennaio 2026
**Ultimo aggiornamento**: 24 Febbraio 2026 (audit onesto M1→M5 vs realtà, chiusura Sprint 1 M2.5/M2.6 3/3)
**Founder / Product Owner**: mcnicastro-netizen
**Lead Developer**: E1 (Emergent Agent)
**Stato**: M1 ✅ · M2 ✅ · M2.5 ✅ (5/5) · M2.6 ✅ (4/4) · M3 ✅ (7/7 core, 2 backlog) · M5.S1/S3/S4.1/S5 ✅ · **NEXT → Sprint 2: M5.S2 HAL Knowledge (RAG)** · M6/M4 in coda post-M5 · Sprint 3 (M3 backlog + M5.S4.2-4) · Sprint 4 (perf hardening)

---

## 🎯 ORDINE DI ESECUZIONE v3.1 (vincolante — audit 24-Feb-2026)

```
✅ DONE  M2.5.0 — GO_TO_MARKET.md + PRICING_OMNIA.md v2                (13-Lug-2026)
✅ DONE  M2.5.1 — Multi-branch / Franchising Layer                     (13-Lug-2026)
✅ DONE  M2.5.2 — API Gateway + API Keys Track B                       (13-Lug-2026)
✅ DONE  M2.5.3 — Widget Embeddabili Brandizzati                       (14-Lug-2026)
✅ DONE  M2.5.4a — Universal XML Importer                              (15-Lug-2026, D-050)
✅ DONE  M2.5.4b — Domain Ownership Checker                            (05-Feb-2026, D-054)
✅ DONE  M2.5.4c — Legal Templates Pack (4 PDF)                        (23-Feb-2026, D-055)
✅ DONE  M2.5.5 — Domain Vault                                          (23-Feb-2026, D-056)
✅ DONE  M2.6a — Publishing Center Foundation                          (Feb-2026, D-052)
✅ DONE  M2.6b — Sync Engine + Compliance Validator                    (05-Feb-2026, D-053)
✅ DONE  M2.6c — Social Publisher (FB Page + IG Business + Telegram)   (24-Feb-2026, D-058)
✅ DONE  M2.6d — Universal Portal Wizard                                (23-Feb-2026, D-057)

🟡 NEXT  Sprint 2 · M5.S2 HAL Knowledge (RAG su PRD/ROADMAP/DECISIONS + Manuale)
         → prerequisito: completare M5.S2-pre Manuale Operativo (cap 1 fatto, 11 capitoli restanti)
🟢 P2    Sprint 3 · M3 backlog (ricerca avanzata + privacy audit 4 livelli) + M5.S4.2/S4.3/S4.4
🔵 P3    Sprint 4 · Perf hardening (async geocoding, list projection) + Deploy readiness
🟠 P4    M6 Omnia Academy (post-Sprint 4, D-035)
🔴 P5    M4 MLS + Stripe + Crediti (post-società)
⏳ POST  M5.S7/S8 — Modulistica, Firma elettronica, Visure (post-società)
🛑        Pre-launch commerciale (CONGELATO — D-035, riapre dopo M6)
```

**Razionale ordine v3.1 (post-audit 24-Feb-2026)**: Sprint 1 chiuso 3/3 al 100% (M2.5.5 + M2.6c + M2.6d). Il pilastro Publishing Center + Doppio Binario Track B è completo. Prossimo focus: Sprint 2 HAL Knowledge — mission critical perché diventa il "how-to" della piattaforma e sblocca l'onboarding self-service delle agenzie strutturate.

---

## 🔥 Cambiamenti strategici v3.1 (rispetto a v3.0) — AUDIT M1→M5 (24-Feb-2026)

Sessione 24 Febbraio: chiuso Sprint 1 M2.5/M2.6 al 3/3 (M2.5.5 Domain Vault + M2.6c Social Publisher + M2.6d Universal Portal Wizard). Fatto audit onesto del programma vs realtà del codice per allineare la roadmap allo stato effettivo.

### 📊 Tabella riassuntiva stato (24-Feb-2026)

| Milestone | Status | DoD coverage | Test coverage | Note |
|---|:-:|:-:|:-:|---|
| **M1 Foundation** | ✅ | 4/4 (100%) | Auth JWT + multi-tenant testati | Deploy preview stabile |
| **M2 ImmoWeb MVP** | ✅ | 8/8 (100%) | 30+ pytest core + stress 5 agenti | Custom domain funzionante |
| **M2.5 White Label / Doppio Binario** | ✅ | 8/8 (100%) | 132 pytest cumulativi | Multi-branch, API Gateway, Widget, Universal Importer, Domain Ownership Checker, Legal Kit, Domain Vault |
| **M2.6 Publishing Center** | ✅ | 4/4 (100%) | 42 pytest cumulativi (16 M2.6a + 13 sync/compliance + 16 social + 13 wizard) | Feed multi-portale, sync scheduler, social auto-post, custom portal wizard |
| **M3 ImmobilCloud B2C** | ✅ | 7/9 (78%) | 60+ pytest (public, map, contact, private listings, valuator 50 pytest, saved searches) | ⚠️ Backlog: M3.S8 ricerca avanzata multi-zona/disegno mappa, M3.S9 privacy audit 4 livelli |
| **M5.S1 AL for Agents** | ✅ | 100% | 27 pytest (8 sync + 6 stream + 13 improve) | Streaming SSE + inline "Migliora con AL" |
| **M5.S2-pre Manuale Operativo** | 🟡 | 1/12 capitoli | — | Solo `01-introduzione-primo-accesso.md`; 11 capitoli residui prerequisiti di M5.S2 |
| **M5.S2 HAL Knowledge** | 🔴 | 0% | — | **Prossimo Sprint 2** (RAG su PRD/ROADMAP/DECISIONS + capitoli manuale disponibili) |
| **M5.S3 AL Legal** | ✅ | 100% | 16 pytest | Tavily + 5 sub-agenti + anti-hallucination + PDF upload |
| **M5.S4.1 Virtual Staging base** | ✅ | 100% | 5 pytest live | Pipeline 3-stage SAM 2 + Flux + Real-ESRGAN |
| **M5.S4.2 Reverse Staging + 4 varianti + prompt CRM-aware** | 🔴 | 0% | — | Sprint 3 |
| **M5.S4.3 Micro-tour video 5s** | 🔴 | 0% | — | Sprint 3 |
| **M5.S4.4 A/B testing portale** | 🔴 | 0% | — | Sprint 3 |
| **M5.S5 Comparatore Mutui** | ✅ | 100% | 12 pytest | Motore in-house + 14 offerte curate + 3 superfici (B2C/CRM/inline listing) |
| **M5.S6 APE** | ❌ | Rimosso (D-039) | — | Solo binario partner esterno (D-038, ⏳ risposta APEFACILE/EnUp) |
| **M5.S7 Modulistica AI** | 🛑 | — | — | Post-società |
| **M5.S8 Firma elettronica + Visure** | 🛑 | — | — | Post-società |
| **M6 Omnia Academy** | 🛑 | 0% | — | Prossimo grande blocco dopo Sprint 4 |
| **M4 MLS + Stripe + Crediti** | 🛑 | 0% | — | Post-società, post-M6 (D-035) |

**Test suite totale**: **180/180 pytest verdi** (backend). Frontend E2E validato da testing_agent_v3_fork su tutte le feature UI critiche.

### 🎯 Cosa cambia in v3.1

| Cosa cambia | v3.0 (Lug-2026) | v3.1 (Feb-2026 post-audit) |
|---|---|---|
| **M2.5 Doppio Binario** | 5 item pianificati, 4 fatti (mancava M2.5.4b/c e M2.5.5) | **8/8 completi** (M2.5.1→M2.5.5 tutti chiusi) |
| **M2.6 Publishing Center** | Nuova sotto-milestone (M2.6a→d) | **4/4 completi** (Foundation + Sync + Social + Wizard) |
| **Sprint model** | Ordine P0→P4 milestone-based | **Sprint 1/2/3/4** granulari, ognuno con DoD + regressione totale |
| **Prossima priorità** | M2.5 White Label | **Sprint 2 · M5.S2 HAL Knowledge** (M2.5 chiuso, blocca solo il Manuale prerequisito) |
| **Perf hardening** | Menzionato in backlog | **Sprint 4 dedicato** (async geocoding <500ms, list projection p95 <200ms) |
| **Sprint 3 residui** | Mescolati in M3/M5 | Estratti in Sprint 3 dedicato: M3.S8 ricerca avanzata + M3.S9 privacy audit + M5.S4.2/S4.3/S4.4 |

### 🧭 Punti di attenzione emersi dall'audit

1. **Manuale Operativo bloccante**: M5.S2 (HAL Knowledge) usa il manuale come corpus RAG primario. Serve completare almeno i capitoli chiave (Immobili, Clienti, Publishing, Portali, Virtual Staging, HAL Legal, Valuator) prima di lanciare S2 in produzione. Alternativa provvisoria (approvata): usare PRD.md + ROADMAP.md + DECISIONS.md come corpus di **cold start** e arricchire progressivamente con i capitoli man mano che vengono scritti.
2. **Sprint 3 M3 backlog** (ricerca avanzata + privacy 4 livelli): esplicitato come tale nella `DoD M3`, non ancora consegnato — resta P2 dopo Sprint 2.
3. **APE post-partnership** (D-038): rimane in attesa risposta APEFACILE + EnUp; non blocca sviluppo — quando arriva la risposta, integrazione via link-out (nessun calcolo lato OMNIA, D-039).
4. **Meta Instagram Business Account non collegato** alla Facebook Page "Omnia real estate lab": M2.6c IG è pronto ma serve un click in Meta Business Manager dal Founder per abilitarlo end-to-end.
5. **Consumo crediti Emergent LLM Key**: monitorare in Sprint 2 (embeddings + RAG). Se il budget si avvicina alla soglia, valutare cache aggressiva.

---

## 🔥 Cambiamenti strategici v3.0 (rispetto a v2.4) — PIVOT "DOPPIO BINARIO" 🏛️

Sessione 06 Luglio: il Founder ha formalizzato il pivot strategico più importante dalla nascita del progetto (D-041/D-042/D-043). OMNIA non è più solo turnkey per agenzie nuove: diventa un ecosistema a **doppio binario** che serve anche le agenzie strutturate/franchising che mantengono il proprio gestionale e sito.

| Cosa cambia | v2.4 | v3.0 |
|---|---|---|
| **Target primario revenue** | Agenzie piccole/nuove turnkey (Track A) | **Agenzie strutturate/franchising (Track B)**: consumano feature OMNIA via API+crediti, widget brandizzati, feed XML bidirezionale (D-041) |
| **Definition of Done feature** | UI dentro OMNIA | **3 modalità simultanee**: (a) UI OMNIA, (b) API+crediti, (c) widget embeddabile — deroghe da giustificare nello sprint plan |
| **Posizionamento (wedge)** | "Anti-Agestanet AI" generico | **B+D formalizzato (D-042)**: AI-first (prodotti hero: HAL, Valuator, Virtual Staging) + Zero-friction migration |
| **Strategia migrazione** | Parser dedicati per gestionale | **Universal Smart Importer (D-043)**: 1 mapper HAL-powered per qualsiasi export; connettore nativo solo a 5+ paganti dallo stesso gestionale |
| **Nuova milestone** | — | **M2.5 White Label/Doppio Binario** (multi-branch, API Gateway, widget, feed bidir., importer 2.0) — entra PRIMA di M4 |
| **Sequenza finale** | M5.S2-pre → M5.S2 → M6 → M4 | **P0 docs → M2.5 → M5.S2-pre/S2 → M6 → M4** |
| **M5.S6 APE** | Calcolatore orientativo in-house | ❌ **Rimosso** (D-039) — resta solo binario partner esterno (D-038, bottone "Ordina APE ufficiale") |
| **Modello dati** | `agency` flat | `agency_group` + `branch` + ruoli `group_admin`/`branch_admin`/`branch_agent` + `plan_type: turnkey\|whitelabel\|hybrid` |
| **HAL entry point** | Da decidere | **3 bottoni fisici** (Agents / Knowledge / Legal), no router LLM (D-040) |

---

## 🔥 Cambiamenti strategici v2.4 (rispetto a v2.3)

Sessione 23-24 Giugno: introdotta la prima ondata della **AI Suite** (M5), che ribalta il posizionamento competitivo OMNIA contro Idealista/Immobiliare.it/Agestanet (questi ultimi hanno ZERO AI).

| Cosa cambia | v2.3 | v2.4 |
|---|---|---|
| **AI Suite** | Roadmap astratta | **3 deliverable in produzione**: AL Chatbot CRM + AL Inline Copywriter + AL Legal |
| **Modello AI base** | Da decidere (stima Claude Sonnet) | **Gemini 3 Flash** via Emergent LLM Key — costi ~×10 inferiori al previsto, free-tier B2C sostenibile |
| **Architettura AL** | Singolo chatbot tuttofare | **3 chatbot specializzati**: Agents (CRM tool-use) / Knowledge (RAG manuale, blocked) / Legal (web-search + anti-hallucination) |
| **Web search legale** | Non in scope | **Tavily AI** integrato (1000 query/mese free) su 7 fonti normative ufficiali italiane |
| **Anti-hallucination** | Non previsto | Validator a secondo LLM con confidence ≥0.85 + CTA notaio sotto soglia |
| **PDF analysis** | Roadmap | ✅ Upload proposte/preliminari/locazioni con analisi strutturata (max 5MB / 60 pp / 40k char) |
| **Posizionamento competitivo** | "Killer feature copy" | "Killer feature **anti-Agestanet**" — loro non hanno AI |
| **Brand AI** | "Al" (nome proprio) | "**AL**" (maiuscolo, acronimo) coerente in UI |

---

## 🔥 Cambiamenti strategici v2.3 (rispetto a v2.2)

Dopo le sessioni del 19-22 Giugno è stato completato l'intero ciclo M3.S1→S6, chiudendo end-to-end il funnel B2C ImmobilCloud:

| Cosa cambia | v2.2 | v2.3 |
|---|---|---|
| **Stato M3** | M3.S1 ✅ DONE | **M3.S1→S6 ✅ DONE** (6 sprint completati in 4 giorni reali) |
| **Funnel B2C** | Solo home + ricerca pubblica | **End-to-end**: home → registrazione segmentata → ricerca → mappa interattiva → dettaglio → form contatto con email notification → pubblicazione privati con moderazione → **valutatore GIS** |
| **Lead generation** | Form contatto basic | 3 canali: contact form (agenzie), private listing (B2C UGC), **valuation_leads** (lead-magnet alta intenzione) |
| **Valutatore** | "Da progettare con OMI 27k zone" | ✅ **Dataset curato 124 città × 3 zone tier**, 50 pytest di congruenza, output verificati su scala Italia (Portofino €20k/m² → Crotone €575/m²) |
| **Email engine** | Magic-link + invite | + **lead_notification** template Resend live (notifica agente quando arriva un lead) |
| **Moderazione UGC** | "Da progettare" | ✅ Workflow admin completo (queue / approve / reject con notes) |

### Razionale v2.3

L'obiettivo dichiarato era: "il valutatore è una NOSTRA SKILL". Il delivery va oltre il "valutatore basico":
- Dataset auditabile e versionato (`italy_real_estate_prices_2025.py`) — fonti documentate
- Algoritmo deterministico con audit trail (multipliers_applied visibili)
- 50 pytest che assicurano congruenza prezzi su Italia intera
- Funziona come **lead-magnet attivo**: chi cerca stima ha intenzione di vendere → lead caldissimo per agenti

## 🔥 Cambiamenti strategici v2.2 (rispetto a v2.1)

Dopo M2.S6 (custom domains) + D-FUTURE-07 (AI Smart Import) completati con successo, M2 chiuso 100%:

| Cosa cambia | v2.1 | v2.2 |
|---|---|---|
| **Stato M2** | "S1→S5 ✅, S6 ⏳" | **M2 ✅ DONE** (tutti i 6 sprint completati) |
| **Custom Domain** | "Sottodominio agenzia" | **Custom CNAME + Host-based routing middleware** (`agenzia-rossi.it` → tema headless) |
| **AI Smart Import** | "Backend in design" | ✅ **End-to-end con Gemini 3 Flash** — parsifica Excel disordinati/vCard/Outlook in schema OMNIA |
| **Next focus** | M3.S1 (B2C portal) | M3 al completo (S1→S7) come milestone unica |

## 🔥 Cambiamenti strategici v2.1 (rispetto a v2.0)

Dopo il completamento di M2.S5 (tutti i Layer A→D) e la sessione del 18 Giugno è emersa una nuova decisione vincolante (D-FUTURE-07):

Dopo il completamento di M2.S5 (tutti i Layer A→D) e la sessione del 18 Giugno è emersa una nuova decisione vincolante (D-FUTURE-07):

| Cosa cambia | v2.0 | v2.1 |
|---|---|---|
| **CSV Import Clienti** | "Backend pronto, polish UI in backlog" | ✅ **UI completata** + 🔴 **nuova priorità AI Smart Import** (D-FUTURE-07) |
| **Pattern import dati** | XML Agestanet (immobili) + CSV (clienti) | Esteso: **AI-Assisted Import** per qualsiasi file disordinato (Excel non standard, vCard, contatti Gmail/Outlook, anche PDF/screenshot) |
| **Stato M2** | "S1+S2+S3 ✅ · S3.5+S4+S5+S6 ⏳" | "**S1→S5 ✅ DONE**" — manca solo S6 (custom domain) |
| **Killer feature commerciale** | Clone-from-URL siti | Clone-from-URL **+** AI Smart Import Clienti (zero-friction migration) |

### Razionale D-FUTURE-07 (AI Smart Import Clienti)

Compilare manualmente il template CSV di 18 colonne per 100 clienti = **5-13 ore di lavoro**. Nessun agente lo farà → senza dati la Smart Clients List (con AI Lead Scoring di M2.S4) vale zero. Lo stesso pattern di `brand_extractor` (Gemini parsa input non strutturato → schema OMNIA) applicato ai clienti riduce il tempo da ore a minuti, sbloccando l'adoption reale dell'ecosistema.

## 🔥 Cambiamenti strategici v2.0 (rispetto a v1.1)

Dopo l'analisi competitiva di Idealista, Immobiliare.it (=Getrix), Casa.it e gestionali italiani/spagnoli (vedi `COMPETITIVE_ANALYSIS_IDEALISTA.md`) sono state introdotte le decisioni D-022→D-026 e le seguenti modifiche al programma:

| Cosa cambia | Vecchio | Nuovo |
|---|---|---|
| **Architettura siti agenzia** | "5-10 template tema" | **Headless OMNIA, 1000+ siti unici** (D-022) |
| **M2 sprint count** | 6 sprint | **7 sprint** (aggiunto M2.S3.5 mini-sprint per `Property.seller_client_id`) |
| **M2.S4 scope** | Matching engine soltanto | Matching **+ Lead Scoring AI** (D-025) — risolve la lamentela #1 del mercato |
| **M2.S5 scope** | Solo XML multiposting verso portali | Multiposting **+ Clone-from-URL** del sito agenzia (D-023 — idea del Founder) |
| **M2.S6 scope** | "White label base + sottodominio" | **Theme registry headless** + custom domain per agenzia (D-018+D-022) |
| **Pricing** | €29 / €49 / €149 | **Lancio: GRATIS / €29 / €79** (D-024), target post-traction tabella vecchia |
| **AI Suite (M5)** | Tutto rinviato a M5 | Lead Scoring AI già in M2.S4 (anticipato); AI Copywriter resta in M5.S1 |
| **Tot sessioni** | 29 | **30** (M2.S3.5 + altre micro-aggiunte) |

---

> ## ⚠️ SEI UN AGENTE AI CHE SUBENTRA?
>
> **STOP.** Prima di leggere oltre, vai a `/app/memory/AGENT_BOOTSTRAP.md` e segui il protocollo obbligatorio.
> Le decisioni in `DECISIONS.md` sono **vincolanti** — non rimetterle in discussione.

---

## 🧭 PARTE I — Le regole del gioco

### 1.1 Come funzionano le nostre sessioni

Ogni sessione segue sempre lo stesso protocollo:

```
┌─────────────────────────────────────────────────┐
│  1. APERTURA   → "Dove eravamo rimasti?"         │
│  2. OBIETTIVO  → Cosa facciamo OGGI (1 cosa sola)│
│  3. DECISIONI  → Domande che ti pongo (se serve) │
│  4. ESECUZIONE → Io costruisco                   │
│  5. VALIDAZIONE→ Tu testi e approvi              │
│  6. CHIUSURA   → Aggiorno PRD.md + roadmap       │
└─────────────────────────────────────────────────┘
```

**Regola d'oro**: una sessione = un obiettivo chiuso. Mai "andiamo avanti finché c'è tempo".

### 1.2 I 3 file di navigazione

| File | Cosa contiene | Quando lo leggi |
|---|---|---|
| `/app/memory/PRD.md` | Cosa è stato fatto, quando, da chi | Inizio di ogni sessione |
| `/app/memory/ROADMAP.md` | Cosa rimane, in che ordine, P0/P1/P2 | Per pianificare la sessione |
| `/app/memory/DECISIONS.md` | Tutte le decisioni di business prese | Per non rifare le stesse domande |

### 1.3 Convenzioni di nomenclatura

- **Milestone** (M1–M6) = blocchi grandi (settimane)
- **Sprint** = gruppo di sessioni legate
- **Sessione** = singolo intervento (1-3 ore di lavoro)
- **Task** = pezzo atomico dentro una sessione

### 1.4 Stato di avanzamento

A fine di ogni sessione ti consegno questo formato:

```
✅ M2.S3 — CRM clienti + matching: COMPLETATO
🟡 M2.S4 — Multiposting XML: IN CORSO (50%)
⏸️  M2.S5 — White label minimo: BLOCCATO (manca dominio)
```

---

## 🗺️ PARTE II — La mappa completa delle 6 Milestone

```
SEQUENZA v3.0 (post pivot Doppio Binario):

M1 ✅ ─→ M2 ✅ ─→ M3 ✅ ─→ M5(S1/S3/S4/S5) ✅ ─→ M2.5 🟠 ─→ M5.S2 🟡 ─→ M6 🟢 ─→ M4 🔵
Fond.    ImmoWeb  ImmoCloud  AI Suite core        Doppio     Manuale+     Academy   MLS+Stripe
                                                  Binario    HAL Knowl.             (post-società)

Dopo M2.5 → Track B vendibile (API+crediti, widget, franchising)
Dopo M4   → monetizzazione completa end-to-end (subscription + crediti)
Dopo M6   → ecosistema completo OMNIA come da schema PDF
```

---

# 🏗️ MILESTONE 1 — FOUNDATION & ARCHITETTURA ✅ DONE
**Durata**: 1-2 settimane · **Sessioni**: 4 · **Stato**: completata 12 Giu 2026

### M1.S1 ✅ — Decisioni architetturali (NO codice)
- Decisione 1: Monorepo (Turborepo) vs 3 repo separati → raccomando monorepo
- Decisione 2: Nome dominio principale (es. omnia.realestate)
- Decisione 3: Schema URL sottodomini
- Decisione 4: Database singolo MongoDB con tenant-id o cluster separati
- **Output**: ARCHITECTURE.md firmato
- **Tuo compito**: rispondere alle 4 domande

### M1.S2 ✅ — Setup monorepo + struttura base
- Setup Turborepo: apps/immocloud, apps/immoweb, apps/academy, packages/shared
- Modelli dati canonici condivisi
- Backend FastAPI con multi-tenant pattern
- Frontend React shell per le 3 app
- **Output**: 3 app vuote che girano + endpoint /api/health
- **Tuo compito**: vedere le 3 home pages caricarsi

### M1.S3 ✅ — Auth JWT + Ruoli + Multi-tenant
- Sistema auth condiviso (login/register/reset password)
- Ruoli: super_admin, agency_admin, agent, client, student
- Multi-tenant: ogni utente appartiene a agency_id
- Email transazionali (Resend) operative
- **Output**: account, login, ruolo funzionanti
- **Tuo compito**: API key Resend ottenuta

### M1.S4 ✅ — Deploy preview + dominio
- Deploy le 3 app su Emergent platform
- Configurazione sottodomini DNS (cloud./app./learn.omniarealestateecosystem.it)
- HTTPS automatico
- Pagina "Coming Soon" pubblica
- **Output**: 3 URL pubblici raggiungibili ✅
- **Tuo compito**: dominio omniarealestateecosystem.it acquistato

### ✅ Definition of Done M1 — TUTTO COMPLETATO
- [x] 3 app deployabili e raggiungibili online
- [x] Login/logout funzionante con ruoli
- [x] Tenant isolation testato
- [x] PRD.md e ROADMAP.md aggiornati

---

# 🏢 MILESTONE 2 — IMMOWEB MVP (Gestionale Agenzia) ✅ DONE
**Durata**: 4-5 settimane · **Sessioni**: 7 · **Stato**: ✅ COMPLETATA (S1→S6 + D-FUTURE-07)

### M2.S1 ✅ — Dashboard agenzia + onboarding
- Wizard setup agenzia (logo, dati fiscali, indirizzo, contatti)
- Dashboard con KPI base
- Gestione collaboratori (invito agente via magic-link Resend)
- **Completato**: 11 Giu 2026
- **Test**: 100% backend, 100% frontend

### M2.S2 ✅ — CRUD Immobili completo + Import
- Form pubblicazione immobile (16 tipologie, 25 features)
- Upload foto multiple (base64 + canvas resize client-side, da migrare a S3 in M3)
- Campi: dati base, energetici, features, owner, privacy, stati workflow
- Stati: draft / active / reserved / sold / rented / withdrawn
- Bulk CSV Import + Custom Agestanet XML Parser (testato su 65 immobili reali)
- **Completato**: 12 Giu 2026

### M2.S3 ✅ — CRM clienti + Preferenze di ricerca (idealista-style)
- Anagrafica clienti (5 tipologie: buyer/seller/tenant/landlord/investor)
- Preferenze ricerca COMPLETE (replica filtri idealista, D-021)
- CSV Import backend
- Filtri lista + tabella con chips colorati
- **Completato**: 16 Giu 2026
- **Test**: 15/15 pytest backend + 7/7 flussi UI

### M2.S3.5 ✅ — Link Property↔Seller Client (D-026)
- `Property.seller_client_id` + cascade delete safety (409 se cliente ha immobili)
- UI dropdown autocomplete venditore + scheda venditore con immobili in carico
- **Completato**: 17 Giu 2026

### M2.S4 ✅ — Matching Engine + AI Lead Scoring (D-025)
- Layer 1 deterministico (city/zone/type/op/price/surface/rooms/beds + features)
- Layer 2 Gemini-3-flash classificazione (freddo/tiepido/caldo/rovente + action_hint)
- 24h cache per ottimizzare costi LLM
- Inline match preview in PropertyFormPage
- **Completato**: 17 Giu 2026

### M2.S5 ✅ DONE — Multiposting + Clone-from-URL + Theme Registry
**Tutti e 4 i Layer + 2 enhancement completati il 18 Giu 2026.**

- ✅ **Layer A — Portal Manager**: backend CRUD `/api/app/portals` con Fernet AES-256 encryption, 7 portali catalogati (Idealista, Immobiliare.it, Casa.it, Wikicasa, Subito.it, Facebook Catalog, LinkedIn). UI tabella + modale subscribe.
- ✅ **Layer B — XML/JSON OSF Feed Generator**: endpoint pubblici `/api/feed/{slug}.xml|.json`, namespace OMNIA AI-extended.
- ✅ **Layer C — Site-as-Feed (HTML SEO)**: 4 endpoint pubblici (`/api/p/{slug}/`, `/{pid}`, sitemap.xml, photo binary). Schema.org RealEstateListing JSON-LD + OG tags + crawler-friendly.
- ✅ **Layer D Phase 1 — Brand Extractor**: BeautifulSoup + Gemini-3-flash crawla URL agenzia → JSON brand profile (palette/typography/voice/structure/logo). Endpoint `POST /api/app/website/extract-from-url`.
- ✅ **Layer D Phase 2 — Theme Registry & Site Generation**: 4 temi headless (minimal/classic/bold/luxury) consumano il brand_profile e renderizzano il sito agenzia con identità visiva. Endpoint `/api/app/website/{themes,theme,theme/apply,theme/auto-configure,preview/{id}}`. Frontend Brand Studio `/it/app/website` (extractor + theme picker + live preview iframe).
- ✅ **Enhancement Social Share**: 4 pulsanti (WhatsApp · Facebook · Email · Copy Link) iniettati in ogni property pubblica `/api/p/{slug}/{pid}`. Absolute URLs per OG/share. JS inline copy-to-clipboard.
- ✅ **D-FUTURE-04 — Smart Clients List**: editorial-sober variant. Endpoint `GET /api/app/clients/smart` (enriched + bucket filters + sort) e `POST /smart/refresh` (batch AI parallel). Frontend con ScoreBox Fraunces serif, TempPill monocroma, MatchesPill, filter pills stone.
- ✅ **Inline Click-to-Call/WhatsApp**: bottoni 📞/💬 su ogni row clienti con `tel:` href + `wa.me` deep-link con messaggio precompilato basato sull'action_hint AI.
- ✅ **UI CSV Client Import**: nuova pagina `/it/app/clients/import` con dropzone, preview e gestione errori.
- ⏳ **Layer A++**: cron worker push portali push_api (rinviato a M4.S3+ insieme allo Stripe)

**Test totale**: 30/30 backend pytest passati + 100% frontend flows.

### 🔴 D-FUTURE-07 ✅ DONE (19 Giu 2026) — AI Smart Import Clienti v1
**Risolto il blocco adoption**: CSV template richiedeva 5-13h per 100 clienti → ora trascini qualsiasi file (CSV/Excel/vCard/TXT) e Gemini-3-flash mappa al schema OMNIA in 5-15 secondi con confidence score per riga.

**Implementato**:
- Backend `apps/immoweb/clients_ai_import.py` (4 endpoint: upload+parse, get draft, patch row, commit) + pre-parser per `.csv .xlsx .vcf .txt` con format auto-detection + Gemini con system prompt domain-specific (interpreta "trilocale"→3 stanze, "venditore"→seller, ecc.) + draft TTL 1h via Mongo index.
- Frontend `ClientImportPage.jsx` dual-tab (AI default + Template CSV legacy) editorial-sober con confidence badge ★/⚠/!.
- 12/12 backend pytest + frontend full flow validato.

**v2 prevista — D-FUTURE-09**: PDF + screenshot via Gemini Vision (in backlog, memorizzato).

### M2.S6 ✅ DONE (18 Giu 2026) — Custom domain + DNS verification (D-022)
- ✅ Custom CNAME + host-based routing middleware operativi (`agenzia-rossi.it` → tema headless). Guida in `DNS_SETUP_GUIDE.md`.
- Scope originale:
  - Custom domain (CNAME) per agenzie del piano Agency+
  - DNS verification con check TXT record (anti-takeover)
  - Wildcard SSL (Let's Encrypt o provider managed)
  - Routing ingress: `agenzia.it` → serve `/api/p/{slug}/` con host stripping
- **Tuo compito**: scegliere provider DNS (Cloudflare?) + decidere se subdomain proxy o full CNAME apex

### ✅ Definition of Done M2
- [x] Agenzia registra, onboarding, gestisce immobili (16 tipologie) e clienti (5 tipologie)
- [x] **Property↔Seller link operativo** (M2.S3.5)
- [x] **Matching engine + Lead Scoring AI live** (M2.S4)
- [x] **Multiposting OSF + Site-as-Feed + Clone-from-URL operativi** (M2.S5)
- [x] **Theme registry headless live + 4 temi applicabili** (M2.S5 Layer D Phase 2)
- [x] **Social share + Smart Clients List + Click-to-call/WA + CSV Client Import**
- [x] **AI Smart Import Clienti** (D-FUTURE-07) — sblocca adoption
- [x] **Custom domain CNAME funzionante** (M2.S6)
- [ ] 5 agenti in parallelo nella stessa agenzia (testabile ora)

---

# 🔗 MILESTONE 2.5 — WHITE LABEL / DOPPIO BINARIO (D-041) ✅ DONE 100% (5/5)
**Durata effettiva**: Lug-2026 → Feb-2026 · **Sessioni**: 7 · **Stato**: ✅ tutti gli item chiusi (M2.5.0→M2.5.5). Rollup in M2.6 anch'essa 100%.

> **Cornice architetturale (D-041)**: da qui in avanti ogni feature deve essere consumabile in **3 modalità**: (a) UI diretta OMNIA, (b) API+crediti, (c) widget embeddabile brandizzato. M2.5 costruisce le fondazioni per la modalità (b) e (c) + il layer multi-filiale che sblocca il target franchising.
>
> **Wedge di posizionamento (D-042)**: AI-first + Zero-friction migration. M2.5 materializza la seconda gamba.
>
> **Ordine interno v3.0**: M2.5.0 (docs) → M2.5.1 (Multi-branch) → M2.5.2 (API Gateway) → M2.5.3 (Widget) → M2.5.4 (Feed bidir.) → M2.5.5 (Importer 2.0)

### M2.5.0 — 🔴 P0 — Documenti strategici GTM + Pricing v2 (NO codice) 🟡 CONSEGNATO 06-Lug — in revisione Founder
- ✅ `GO_TO_MARKET.md` v1.0 creato: posizionamento wedge B+D, ICP Track A/B (affiliate, casa madre, web agency), sezione obbligatoria "Il nodo della domanda" (D-045), motion bottom-up in 4 fasi, messaging kit con claims verificati (Fronte 8), metriche di validazione, vincolo D-035 (strategia sì, esecuzione solo post-M6)
- ✅ `PRICING_OMNIA.md` aggiornato a v2.0 (bozza): listino Track B (widget €19-119/mese, bundle €119, API a crediti unificati, feed inbound €49/mese, free tier dev), staging 1→3 crediti (€0,90), nuovi servizi a crediti (UNI 10750, HAL Legal, micro-tour), benchmark documentale (-85% vs stack reale €7.786/anno)
- **Prerequisito ✅ DONE (06 Lug)**: `COMPETITIVE_ANALYSIS_TRACK_B.md` — ricerca su 7 fronti con benchmark prezzi reali (valutatori white-label, staging SaaS, stack franchising, pricing API, MLS, chatbot, mutui). White space Track B confermato: nessuna suite headless integrata esiste in Italia.
- **`GO_TO_MARKET.md`**: segmentazione Track A/B, ICP (franchising: Tecnocasa, RE/MAX, Gabetti, Toscano, Frimm, Grimaldi + agenzie multi-sede), messaging wedge B+D, canali di acquisizione, funnel e metriche di validazione
- **`PRICING_OMNIA.md` v2**: unit economics Track A vs Track B, cap free tier, logica crediti API (contabilità group vs branch), revenue share ADV ImmoCloud + lead per Track B, welcome credits
- **Perché prima del codice**: cap free tier e contabilità crediti group/branch determinano lo schema dati di M2.5.1 e M2.5.2
- **Tuo compito (Founder)**: revisione e approvazione dei 2 documenti prima di scrivere codice

### M2.5.1 — 🏢 Multi-branch / Franchising Layer ⭐ primo sprint di codice
- **Nuove entità dati**: `agency_group` (holding/franchising sopra) + `branch` (filiale sotto). Backward-compatible: le agenzie attuali diventano automaticamente "gruppo mono-filiale"
- **Nuovi ruoli**: `group_admin` (visione consolidata), `branch_admin` (perimetro filiale), `branch_agent` (perimetro individuale)
- **Campo `plan_type`** su agency: `turnkey | whitelabel | hybrid` (D-041)
- **Reporting consolidato**: KPI per filiale + rollup per gruppo (immobili, clienti, lead, fatturato prospect)
- **Contabilità crediti**: livello group vs branch (holding paga o filiale paga — sceglibile per gruppo, regole definite in M2.5.0)
- **Prerequisito per**: M4 (tier Enterprise/franchising)
- **Tuo compito**: validare il modello permessi con 1 agenzia franchising di riferimento prima del rilascio

### M2.5.2 — 🔑 API Gateway + API Keys per Track B
- Emissione **API key per agenzia white-label** con budget crediti collegato
- **`partner_id` su API key/snippet widget** (D-046): attribution automatica per il Programma Partner Web Agency (rev-share 20% a vita) + dashboard partner (clienti attivi, MRR, commissioni). Stima +0,5-1 sessione
- Endpoint pubblici versionati (`/api/v1/*`) per: Valuator, Mutui, Virtual Staging, HAL Legal pubblico, Import Feed Immobili, Export Lead
- Rate limit + audit + revocation dashboard
- SDK reference (Node.js + Python) documentato in `/app/memory/API_DOCS_TRACK_B.md`

### M2.5.3 — 🧩 Widget Embeddabili Brandizzati
- Iframe leggeri (~50-100 KB) con customer colors/logo per: **Valuator**, **Comparatore Mutui**, **Virtual Staging demo**, **HAL Legal pubblico**
- Snippet 1-line `<script src="https://widgets.omniarealestateecosystem.it/valuator.js" data-key="ak_..."></script>`
- Lead capture on-widget → forward al CRM cliente via webhook
- Dashboard analytics widget (impression, engagement, lead generati)

### M2.5.4 — 🔒 Domain Sovereignty Kit (D-051, riformulato 15-Lug-2026) ✅ **DONE**
> Nato dalla scoperta "Domain Lock-in" nel settore gestionali immobiliari italiani. Strategia **Extraction-first**: aiuta prima chi è già in trappola, poi previeni per i nuovi. Regola: **zero brand mentions** in materiale pubblico.
- **M2.5.4a ✅ DONE (15-Lug-2026, D-050)** — Universal XML Importer: parser schema-agnostic per feed di qualsiasi gestionale italiano, preview→commit two-phase, UI `/it/app/import`
- **M2.5.4b ✅ DONE (05-Feb-2026, D-054)** — Domain Ownership Checker: landing pubblica `/it/verifica-dominio` con query RDAP live + lead capture + IP rate-limit
- **M2.5.4c ✅ DONE (23-Feb-2026, D-055)** — Legal Templates Pack: 4 PDF con placeholder `[FORNITORE]` (PEC transfer dominio · GDPR art. 20 export dati · disdetta contratto · ricorso CNR-IIT registrazione fiduciaria)

### M2.5.5 — 🛡️ Domain Vault (Prevention layer per nuovi OMNIA) ✅ **DONE (23-Feb-2026, D-056)**
- ✅ Onboarding OMNIA con badge emerald 🛡️ "Il tuo dominio resta tuo" nel signup (visibile solo per ruoli agenzia)
- ✅ Campo opzionale dominio esistente con link a `/verifica-dominio` (integrazione con M2.5.4b)
- ✅ Checkbox obbligatoria "Ho letto e accetto la Domain Sovereignty Policy" con blocco submit
- ✅ Pagina pubblica `/it/domain-sovereignty-policy` (Mediterranean Future 2035) con 6 sezioni contrattuali
- ✅ Audit trail append-only `domain_vault_events` (agency_id, user_id, confirmed, existing_domain, ts)
- ✅ Endpoint `/api/app/agencies/me/domain-sovereignty` (GET + POST idempotent) + 11/11 pytest
- Slogan pubblico: *"OMNIA non tocca il tuo dominio. È tuo. Lo era, lo resta."*

### M2.6 — 📡 Publishing Center (Multi-portal Outbound, NUOVO 15-Lug-2026) ✅ **DONE 4/4**
> Match funzionale con l'area "Portali" dei gestionali legacy: OMNIA deve pubblicare gli annunci su tutti i portali gratuiti/paganti italiani con setup one-click e sync automatica. Senza questo layer OMNIA non è sostituibile all'esistente.
- **M2.6a ✅ DONE (Feb-2026, D-052)** — Foundation: modelli `PortalCatalog` (8 portali di sistema) + `AgencyPortalConnection` con credenziali AES-256-GCM + feed generator multi-dialetto (`osf_federata`, `generic_rss`) + UI dashboard `/it/app/publishing` a tab attivi/disponibili
- **M2.6b ✅ DONE (05-Feb-2026, D-053)** — Sync engine + Compliance: APScheduler daily job 06:00 UTC + trigger manuale, `PortalSyncLog` audit, compliance validator HARD (classe energetica L. Boschi obbligatoria, min-foto ≥3, prezzo, superficie, indirizzo) + dashboard compliance per-portale
- **M2.6c ✅ DONE (24-Feb-2026, D-058)** — Social Publisher: Facebook Page + Instagram Business + Telegram broadcast via API ufficiali (Graph v20 + Bot API), credenziali cifrate, audit trail `social_posts`, caption builder italiano automatico, UI `/it/app/publishing/social` + 16/16 pytest
- **M2.6d ✅ DONE (23-Feb-2026, D-057)** — Universal Portal Wizard self-service: agenzia aggiunge portali non nel catalogo curato con setup guidato 4-step + tenant isolation via slug namespacing + 13/13 pytest
- **Coverage MVP Fase 1**: 8 portali di sistema (Subito, Bakeca, Kijiji, Wikicasa, Facebook Marketplace, Google Business Profile, Attico, Case24) + self-service illimitato via Wizard + 3 canali social — copre >70% traffico lead gratuito italiano

### ✅ Definition of Done M2.5 + M2.6 (chiusa 100% al 24-Feb-2026)
- [x] GO_TO_MARKET.md + PRICING_OMNIA.md v2 approvati dal Founder (M2.5.0) — 13-Lug-2026
- [x] Multi-branch operativo (M2.5.1) — 13-Lug-2026
- [x] API Gateway con 5+ endpoint Track B live (M2.5.2) — 13-Lug-2026
- [x] 2+ widget embeddabili in produzione (M2.5.3) — 14-Lug-2026
- [x] Universal XML Importer (M2.5.4a) — 15-Lug-2026 (D-050)
- [x] Domain Ownership Checker (M2.5.4b) — 05-Feb-2026 (D-054)
- [x] Legal Templates Pack 4 PDF (M2.5.4c) — 23-Feb-2026 (D-055)
- [x] Domain Vault onboarding (M2.5.5) — 23-Feb-2026 (D-056)
- [x] Publishing Center — Foundation (M2.6a) — Feb-2026 (D-052)
- [x] Publishing Center — Sync engine + Compliance (M2.6b) — 05-Feb-2026 (D-053)
- [x] Publishing Center — Social Publisher FB/IG/Telegram (M2.6c) — 24-Feb-2026 (D-058)
- [x] Publishing Center — Universal Wizard (M2.6d) — 23-Feb-2026 (D-057)

---



# 🌐 MILESTONE 3 — IMMOBILCLOUD (Portale B2C) ✅ DONE (S1→S7)
**Durata reale**: 19-23 Giugno 2026 · **Sessioni**: 7 completate

### M3.S1 — Home pubblica + Registrazione segmentata B2C ✅ DONE (19 Giu)
- CloudTopNav (logo ImmobilCloud™, link cerca/vendi/valuta gratis/area riservata)
- Hero split-layout + 3 card azione (Cerca/Vendi/Affitta)
- `POST /api/cloud/auth/register` con segmentazione intents (sell/rent_out/get_alerts) + notification_channels
- Test: iter_8/9 100% PASS

### M3.S2 — Publishing Center lato agente ✅ DONE (19 Giu)
- Toggle `is_listed_on_immobilcloud` per ogni immobile dell'agente
- Pulsanti share WhatsApp / Facebook / Email / Copy Link → URL pubblico `/api/p/{slug}/{pid}`
- Test: iter_10 (4 backend + 14 frontend) 100% PASS

### M3.S3 — Mappa interattiva Leaflet + Filtri avanzati ✅ DONE (22 Giu)
- Mappa OSM con marker cluster (FitBounds automatico, popup con prezzo + link dettaglio)
- Toggle Lista/Mappa nella SearchPage
- Filtri avanzati: `bedrooms_min`, `bathrooms_min`, `energy_class` (A4..G) + bbox sul `/api/cloud/map`
- Geocoding automatico Nominatim/OSM (fire-and-forget) ad ogni POST/PATCH property
- Test: iter_11 (14 backend + 18 frontend) 100% PASS

### M3.S4 — Pagina dettaglio pubblica + Form contatto ✅ DONE (22 Giu)
- `/it/cloud/property/:pid` con gallery foto, info grid (8 celle), descrizione, features, mini-mappa Leaflet, card agenzia
- Form contatto `POST /api/cloud/property/{pid}/contact` → find-or-create client + lead con `source='ImmobilCloud'` nel CRM dell'agenzia
- Schema.org JSON-LD `RealEstateListing` per SEO + share rich previews
- Test: iter_12 (10 backend + frontend) 100% PASS

### M3.S4.1 — Email lead notification via Resend ✅ DONE (22 Giu)
- Helper `_schedule_lead_email()` fire-and-forget chiamato in coda al contact endpoint
- Smart destinatario: `listing_agent_id.email` fallback su `agency.email`
- Template `lead_notification.{it,en,es}.html` con CTA deep-link CRM
- Verifica live: `[EMAIL OK] template=lead_notification id=...` < 1s
- Test: smoke E2E PASS

### M3.S5 v2 — Pubblicazione annunci da privati B2C + Moderazione admin ✅ DONE (22 Giu)
- Backend: 2 nuovi router
  - `/api/cloud/me/properties` (B2C auth) POST/GET/PATCH/DELETE/submit, free-tier 1 listing attivo, sentinel `agency_id="_private_listings"`
  - `/api/app/moderation` (admin only) queue/approve/reject con notes ≥3 char
- Frontend:
  - `/it/cloud/account/sell` (B2C) — form lista/crea/edita/sottometti, badge status, motivo rifiuto visibile
  - `/it/app/moderation` (admin) — tabs pending/approved/rejected, approve one-click + reject con textarea
- Bug fix HIGH: `_public()` ora restituisce `account_type`, `intents`, `notification_channels`, `phone` (era causa di redirect loop SellPage)
- Test: iter_13 (19 backend) + iter_14 (100% retest dopo fix) PASS

### M3.S6 — Valutatore GIS pubblico ✅ DONE (22 Giu) — **NOSTRA SKILL CORE**
- **Dataset curato 124 città italiane × 3 zone tier** (centro/semicentro/periferia) — €/m² 2025 da Borsino Immobiliare/OMI/Tecnocasa/Idealista
- Algoritmo deterministico auditabile:
  1. Normalize city → resolve canonical key (gestisce sinonimi EN)
  2. Infer zone_tier da keywords address (Trastevere/Vomero/Chiaia/Navigli…)
  3. Apply multipliers: property_type × condition × energy_class × floor
  4. Comparables query db.properties stessa città + tipo
- `POST /api/cloud/valuator` (pubblico): risposta con price_per_sqm{min,avg,max}, estimated_value{min,avg,max}, multipliers_applied (audit trail), confidence (high/medium/low), methodology, data_source, comparables, disclaimer
- `GET /api/cloud/valuator/coverage` (meta): 124 città, 20 regioni
- ⬆️ **UPGRADE M3.S6-pro (25 Giu, D-034)**: copertura estesa al **100% del territorio nazionale** (~7.900 comuni) — 124 città curate + 107 province + fallback regionale via Nominatim, superficie commerciale UNI 10750/DPR 138, coefficienti di merito, liquidità regionale. **"124 città" NON è la copertura: è solo il layer 1 di 3.**
- Frontend `/it/cloud/valutatore` con hero dark gradient + form 3-sezioni + correttori auditabili + comparables clickabili + collapsible methodology
- **Lead capture**: `db.valuation_leads` (high-intent — chi cerca stima ha decisione di vendere)
- **Verifica congruenza prezzi su Italia intera**:
  - Milano centro nuovo A → €13.682/m² ✓
  - Cortina villa ottimo → €15k/m² ✓
  - Portofino centro → €20k/m² ✓
  - Crotone periferia → €575/m² ✓
- Test: iter_15 (50 pytest + 12 backend + 4 frontend) 100% PASS

### M3.S7 ✅ DONE (23 Giu) — Account B2C completo: ricerche salvate + alert email
- Backend: `POST /api/cloud/me/saved-searches`, `GET /api/cloud/me/saved-searches`, `DELETE .../{id}`
- Schema: `{user_id, name, filters: SearchFilters, frequency: daily|weekly|instant, created_at, last_run_at}`
- Cron job (APScheduler o cron Mongo) che ogni ora controlla matching tra ricerche salvate e proprietà nuove
- Email template `alert_match.{it,en,es}.html` con preview 3 immobili matching + link search
- Frontend: `/it/cloud/account` (Dashboard B2C) con tab "Ricerche salvate" + bottone "Salva questa ricerca" in SearchPage

### ✅ Definition of Done M3 (aggiornato 22 Giu)
- [x] Portale pubblico online con SEO Schema.org
- [x] Funnel acquisizione lead chiuso (form contatto + email notification real-time)
- [x] Mappa interattiva + filtri avanzati
- [x] Pagina dettaglio pubblica
- [x] Privato pubblica annuncio in autonomia (B2C UGC)
- [x] Moderazione admin queue funzionante
- [x] Valutatore GIS pubblico — **copertura nazionale 100%** (~7.900 comuni: 124 città curate + 107 province + fallback regionale, UNI 10750 — M3.S6-pro)
- [x] Lead arrivano in ImmoWeb (3 fonti: contact form, private listing, valutatore)
- [x] Saved searches + alert email B2C (M3.S7) ✅ 23 Giu — 12 pytest + 11 Playwright PASS

### 🔮 Backlog M3 (post-S7)
- **Upgrade valutatore**: caricare OMI 27k zone come override DB (granularità sub-quartiere)
- **Auto-assignment lead**: lead valutatore → agente OMNIA più attivo nella zona (lead score + round-robin)
- Cluster marker mappa con `react-leaflet-cluster` (>100 marker)
- Cerca vicino a te / tempo percorrenza
- Disegna su mappa / multi-zone selection
- Immobili Segreti off-market premium
- [ ] Privacy 4 livelli rispettata
- [ ] Multi-zone selection + Disegna su mappa + Cerca vicino a te + Confronta prezzi

---

# 💎 MILESTONE 4 — MLS + STRIPE + KILLER FEATURES 🔵 P4 — POST-M6, POST-SOCIETÀ
**Durata**: 3-4 settimane · **Sessioni**: 5 · **Stato**: ⏸️ BLOCCATA — richiede costituzione società (Stripe/IBAN) e viene DOPO M6 Academy (ordine v3.0). **Prerequisito tecnico: M2.5.1 Multi-branch** (contabilità crediti group/branch per il tier Enterprise/franchising).

### M4.S1 — MLS Network multi-agenzia
- Sistema invito agenzie a MLS
- Acceptance workflow inter-agenzia
- Vista MLS con privacy MLS_MEMBER
- **Tuo compito**: definire regole MLS (commissioni, esclusiva)

### M4.S2 — Workflow collaborazione 5 giorni
- Richiesta visita inter-agenzia → countdown 5gg
- Stati: requested / accepted / rejected / expired
- Upgrade privacy ACCEPTED
- Audit log completo

### M4.S3 — Stripe abbonamenti (pricing aggressivo lancio D-024)
- **Fase lancio** (primi 12 mesi):
  - Starter (1 agente, 20 immobili): GRATIS primi 3 mesi → €19/mese
  - Pro (3 agenti, 100 immobili): **€29/mese**
  - Agency (illimitato + MLS + AI): **€79/mese**
  - Enterprise (network/franchising): da €299/mese
- **Fase post-traction** (dopo 100 agenzie paganti):
  - Starter €19, Pro €49, Agency €149, Enterprise €299-499
- Trial 14 giorni gratuito su tutti i piani a pagamento
- **Zero setup fee. Zero formazione a pagamento. Zero vincoli contrattuali** (anti-Getrix)
- Migrazione dati gratuita inclusa
- Listino PUBBLICO in homepage (anti-opacità Idealista/Immobiliare)
- Customer Portal Stripe
- **Tuo compito**: account Stripe attivo + IBAN (rinviato a M4.S3 come da D-010)

### M4.S4 — Sistema crediti pay-as-you-go
- Wallet crediti per agenzia
- Acquisto pacchetti (50/200/1000 crediti)
- Consumo crediti (visure, valutazioni, Top, SMS)
- **Tuo compito**: tabella prezzi crediti-vs-servizi

### M4.S5 — Punti visibilità (gap vs idealista)
- Promozione immobile: Top / Premium / In Evidenza
- Costo in crediti
- Dashboard ROI
- **Tuo compito**: prezzi visibilità

### ✅ Definition of Done M4 — 🎉 PRODOTTO VENDIBILE
- [ ] Agenzia paga €29-149/mese end-to-end
- [ ] MLS attivo con 2 agenzie test
- [ ] Sistema crediti operativo
- [ ] Pronti per **prime 2 agenzie pilota reali**

---

# 🤖 MILESTONE 5 — AI SUITE (Vantaggio competitivo) 🟢 CORE DONE (4/8) — Sprint 2/3 residui
**Durata**: 2-3 settimane · **Sessioni**: 8 · **Stato**: S1 ✅ · S2-pre 🟡 1/12 · S2 🔴 (Sprint 2 NEXT) · S3 ✅ · S4.1 ✅ · S4.2/S4.3/S4.4 🔴 (Sprint 3) · S5 ✅ · S6 ❌ rimosso (D-039) · S7/S8 post-società

> **Decisione architetturale chiave (D-028)**: Il chatbot "Al" del santo graal è stato **split in 3 chatbot specializzati sequenziali** invece di un unico tuttofare. Stack: Gemini 3 Flash via Emergent LLM Key, web-search API gratuita in fase lancio, anti-hallucination layer, audit log 5 anni.

### M5.S1 — 🤖 AL for Agents (chatbot CRM ImmoWeb) ✅ **DONE — 24 Giu 2026**
- ✅ Assistente conversazionale dentro l'app ImmoWeb con **manual JSON tool-use** (emergentintegrations non supporta `tools=` nativi di Gemini)
- ✅ 5 tool whitelistati: `query_properties`, `query_clients`, `query_leads`, `monthly_performance`, `write_description`
- ✅ Sicurezza multi-tenant: `agency_id` iniettato dal JWT server-side, **mai** dall'AI
- ✅ **Streaming SSE token-by-token** (`POST /api/app/al/chat/stream`) per UX ChatGPT-style con cursore lampeggiante + Stop button
- ✅ **Inline ✨ "Migliora con AL"** su titolo+descrizione di PropertyForm (agenti) e SellPage (privati B2C) — multilingua IT/EN/ES, modal con preview Originale | Suggerito
- ✅ Persistenza sessioni (`al_sessions`) + audit (`al_audit`), rate limit 60/h chat + 60/h improve indipendenti
- ✅ Tests: iteration_17.json (8/8 sync), iteration_18.json (6/6 streaming), iteration_19.json (13/13 improve) — **100%**

### M5.S2-pre — 📖 MANUALE OPERATIVO OMNIA 🟡 P2 (riprende dopo M2.5)
- **Cos'è**: il manuale utente completo della piattaforma, scritto da E1 — capitolo per modulo (Dashboard, Immobili, Clienti, Match, Portali, Sito web, Virtual Staging, HAL Legal, Fascicolo, Valuator, Collaboratori, Impostazioni)
- **Formato**: Markdown strutturato in `/app/memory/manuale/` (un file per capitolo) — sarà la knowledge base RAG di M5.S2
- **Contenuti per capitolo**: a cosa serve, flusso passo-passo con i nomi esatti dei bottoni/campi, FAQ, errori comuni, screenshot descritti testualmente
- **Quando**: 🟡 P2 — dopo M2.5 (ordine v3.0). Capitolo 1 già scritto (`/app/memory/manuale/01-introduzione-primo-accesso.md`), poi task messo in pausa dal Founder per il pivot Doppio Binario. Alla ripresa, ogni capitolo documenta anche le modalità di consumo Track B (API/widget) dove applicabile. Comunque PRIMA di M5.S2.
- **Tuo compito (Founder)**: revisione del manuale prima che diventi la base del chatbot

### M5.S2 — 📚 HAL Knowledge (chatbot how-to piattaforma) 🟡 P2
- **Entry point**: 3 bottoni fisici HAL (Agents / Knowledge / Legal), no router LLM (D-040)
- **Prerequisito**: ⬆️ M5.S2-pre Manuale Operativo completato e revisionato dal Founder
- RAG su manuale curato + FAQ + (opzionale) database immobili pubblico
- Vector DB: Mongo Atlas vector search, embeddings Google text-embedding-004
- Lead capture conversazionale quando rilevante, handoff agente reale possibile
- **Tuo compito**: revisione del manuale prima del lancio

### M5.S3 — ⚖️ AL Legal (chatbot giuridico-notarile con web search) ✅ **DONE — 24 Giu 2026**
- ✅ Architettura **multi-agente**: 5 sub-agenti specializzati (General, Proposta, Locazioni, Catasto, Urbanistica) + analizzatore PDF, routing automatico via keyword matching
- ✅ **Web search live** via **Tavily AI** (1000 query/mese gratis) su 7 fonti normative: `normattiva.it`, `gazzettaufficiale.it`, `agenziaentrate.gov.it`, `notariato.it`, `cassazione.it`, `altalex.com`, `brocardi.it`
- ✅ **Citazioni inline obbligatorie** `[1]`, `[2]`, ... con pannello fonti laterale cliccabile
- ✅ **Anti-hallucination layer**: secondo LLM (Gemini 3 Flash, sessione separata) valuta `confidence ∈ [0,1]` + lista `unsupported_claims` + `fabricated_refs`, soglia 0.85
- ✅ Sotto soglia → CTA `notariato.it/trova-notaio` automatica + disclaimer rafforzato
- ✅ **Chain of Thought interno** + temperature 0.2 (D-029)
- ✅ **Upload PDF** (max 5MB / 60 pp / 40k char) con sub-agente `pdf_analysis`: analisi strutturata clausole, criticità, verifiche pre-firma
- ✅ **Disclaimer L.247/2012** + checkbox obbligatorio first-visit, persistito in localStorage
- ✅ Audit log `al_legal_audit` completo (user, sub_agent, citation_count, confidence, unsupported_claims, validator_rationale)
- ✅ Pagina dedicata `/it/legal` accessibile a **tutti gli utenti autenticati** (agenti + B2C, no agency_id required)
- ✅ Tests: iteration_20.json — **16/16 backend + 100% frontend**
- 🟡 **Tuo compito**: termini d'uso da revisionare con avvocato di fiducia (€200 una tantum) prima della commercializzazione

### M5.S4 — 🎨 Virtual Staging foto immobili ✅ **DONE — 03 Lug 2026 (pipeline premium 3-stage, D-033)**
- ✅ Pipeline 3 stadi via fal.ai: SAM 2 (segmentazione) → Flux.1 [dev] Inpainting + Depth ControlNet → Real-ESRGAN 4x + watermark "Render virtuale OMNIA" (conformità AGCM)
- ✅ Costo ~€0,056/render vs competitor €15-29/img
- ✅ Frontend Staging Studio con dropzone + A/B "prima vs dopo"
- ❌ "Descrizione coordinata" rimossa (D-037 parte 1) — NON riproporre
- 🔮 Backlog S4.2-S4.4: Reverse Staging avanzato, micro-tour video 5s, A/B testing sul portale B2C — anche come API/widget Track B (M2.5)

### M5.S5 — 💰 Comparatore mutui ✅ **DONE — 06 Lug 2026 (motore in-house, D-037)**
- ✅ Motore in-house: ammortamento francese, TAN = benchmark + spread (Eurirs per fisso per durata, Euribor 3M per variabile con floor 0), TAEG via IRR con spese (istruttoria, perizia, imposta sostitutiva 0,25%/2%, incasso rata), controllo soglia usura TEGM Banca d'Italia
- ✅ 14 offerte curate di 8 banche (Intesa, UniCredit, BPER, Crédit Agricole, BNL, MPS, ING, Webank) in `data/mortgage_data.py` — NO scraping (fragile/grigio), NO pannello admin (scelta Founder): aggiornamento manuale del file dati (~5 min/trimestre)
- ✅ Vincoli reali: LTV max 80% (95% under-36 prima casa via Consap, solo banche aderenti), sostenibilità rata ≤ 35% reddito
- ✅ Piano di ammortamento completo per offerta (aggregato per anno + primi 12 mesi)
- ✅ **Tre superfici**: portale B2C `/cloud/mutui` (con lead capture → `mortgage_leads`), CRM agenti `/app/mutui` (senza lead form), box "Rata stimata da €X/mese" sulle pagine pubbliche degli annunci → comparatore precompilato
- ✅ i18n completa IT/EN/ES (~35 chiavi), disclaimer art. 128-sexies TUB (no mediazione creditizia)
- ✅ Tests: 12/12 pytest backend + testing agent frontend 100% (iteration_24.json)
- **Contesto**: MutuiOnline & co. hanno rifiutato partnership senza volumi di traffico → soluzione interna (decisione Founder 06-Lug)
- **Tuo compito (quando ci saranno volumi)**: riaprire il discorso affiliazione per il link-out

### M5.S6 — 🌡️ Certificazione APE — ❌ **RIMOSSO (D-039, 06-Lug-2026)**
- **Decisione Founder**: eliminato il calcolatore APE orientativo in-house dalla roadmap. Rischio disclaimer + valore percepito basso + confusione con l'APE ufficiale (solo tecnico abilitato ENEA).
- **Rimane attivo il binario partner esterno** (D-038): in attesa di risposta da APEFACILE e Certificato-Energetico.it/EnUp. Se un partner risponde positivamente, si integrerà **solo** un bottone "Ordina APE ufficiale" nel Fascicolo Immobile + scheda CRM — nessun calcolo lato OMNIA.
- **Effetto sulla sequenza**: M5.S5 ✅ → **M5.S2-pre Manuale Operativo** (prossimo step) → M5.S2 HAL Knowledge → M5.S7/S8 (post-società).

### M5.S7 — 📑 Modulistica AI (post-società)
- Template contratti italiani (proposta acquisto, mandato vendita/locazione, preliminare, lettera ai condòmini, disdetta)
- Auto-compilazione con dati CRM (cliente, immobile, prezzo)
- Generazione PDF brandizzati
- Storage documenti per agenzia
- **Tuo compito**: 5 template legali iniziali (può aiutare un legale)

### M5.S8 — ✍️ Firma elettronica + Visure (post-società)
- Integrazione DocuSign / Yousign per firma a distanza (richiede account paid)
- VisureItalia API per visure catastali/ipotecarie (richiede account paid)
- Storage documenti firmati nel cloud
- **Tuo compito**: account DocuSign + VisureItalia (a carico nuova società)

### ✅ Definition of Done M5
- [ ] Al for Agents risponde correttamente a 90%+ query CRM
- [ ] Al Knowledge copre 30+ how-to della piattaforma
- [ ] Al Legal: 95%+ risposte con citazione normativa, 0 false positive ad alta confidence
- [ ] Virtual Staging produce render vendibili
- [ ] Comparatore mutui genera primi lead reali
- [ ] Modulistica + Firma + Visure tutto integrato (post-società)

---

# 🎓 MILESTONE 6 — OMNIA ACADEMY 🟢 P3 — PRIMA DI M4 (ordine v3.0, D-035)
**Durata**: 2-3 settimane · **Sessioni**: 5

### M6.S1 — Struttura LMS base
- Catalogo corsi
- Iscrizione + tracking progresso
- Player video (Mux/Cloudflare Stream)
- Risorse scaricabili
- **Tuo compito**: scegliere 1 corso pilota

### M6.S2 — Quiz + Certificazioni
- Editor quiz
- Soglie superamento
- Esame finale
- Certificato PDF brandizzato
- **Tuo compito**: contenuti quiz primo corso

### M6.S3 — Chatbot tutor "Al Academy"
- Tutor AI per ogni corso (Gemini + RAG)
- Spiegazione concetti, esempi, esercizi
- Tracking domande frequenti
- **Tuo compito**: materiale corso pilota

### M6.S4 — Marketplace agenti certificati
- Profilo pubblico agente con certificazioni
- Badge verificati su ImmobilCloud
- Ricerca per zona + specializzazione
- **Tuo compito**: criteri certificazione

### M6.S5 — Crediti formativi + FIAIP/FIMAA
- Tracciamento ore formative
- Export certificati ordine professionale
- Calendario eventi/webinar live
- **Tuo compito**: contattare FIAIP per accreditamento

### ✅ Definition of Done M6 — 🏆 ECOSISTEMA OMNIA COMPLETO
- [ ] 3 pilastri operativi
- [ ] White label totale
- [ ] Almeno 1 corso con certificazione
- [ ] **Pronti per scale-up commerciale**

---

## 📊 PARTE III — Quadro riassuntivo

| Priorità | M | Nome | Sessioni | Stato | Output chiave |
|---|---|---|---|---|---|
| — | **M1** | Foundation | 4 | ✅ DONE | Auth + multi-tenant + DNS |
| — | **M2** | ImmoWeb | 7 | ✅ DONE | CRM + Matching + Lead Scoring AI + Multiposting OSF + Theme Registry + Custom Domain + AI Smart Import |
| — | **M3** | ImmobilCloud | 7 | ✅ DONE | Portale B2C + **valutatore GIS nazionale 100%** (~7.900 comuni, UNI 10750) + UGC privati + saved searches |
| — | **M5** core | AI Suite | 8 | 🟢 4/6 | HAL Agents ✅ · HAL Legal ✅ · Virtual Staging ✅ · Mutui ✅ (S6 ❌ D-039) |
| 🔴 P0 | **M2.5.0** | GTM + Pricing v2 | 1 | ⏳ **NEXT** | `GO_TO_MARKET.md` + `PRICING_OMNIA.md` v2 (unit economics Track A/B) |
| 🟠 P1 | **M2.5** | Doppio Binario | 5-6 | 🟠 pianificata | Multi-branch + API Gateway + Widget + Feed bidir. + Importer 2.0 |
| 🟡 P2 | **M5.S2-pre + S2** | Manuale + HAL Knowledge | 2-3 | ⏸️ in pausa | 13 capitoli manuale + RAG chatbot (cap.1 ✅) |
| 🟢 P3 | **M6** | Academy | 5 | ⏸️ in coda | LMS + certificazioni + marketplace agenti |
| 🔵 P4 | **M4** | MLS + Stripe + Crediti | 5 | ⏸️ post-società | 🎉 Monetizzazione end-to-end |
| POST | **M5.S7/S8** | Modulistica + Firma + Visure | 2 | ⏸️ post-società | Contratti AI + DocuSign/Yousign + VisureItalia |

### 🎯 Argomenti commerciali chiave dopo M4 (ricavati dall'analisi competitiva)
1. **Risparmia il 95%** vs stack tradizionale (€10.000-12.000/anno → €348-948/anno)
2. **Listino trasparente** (vs "Contattaci" di tutti i competitor)
3. **Zero setup fee, zero vincoli, mese per mese**
4. **Migrazione gratuita** da Getrix/Agestanet/Gestim in 1 click
5. **Lead Scoring AI**: smetti di rincorrere lead morti
6. **Clone del tuo sito attuale in 60 secondi** (Demo killer)
7. **Sito su dominio tuo, non sottodominio nostro** (D-018)
8. **Academy inclusa** (no upsell separato)

---

## 📝 PARTE IV — Checklist per il Founder

### Necessario adesso (✅ già fatto)
- [x] Dominio principale: omniarealestateecosystem.it
- [x] Account Emergent attivo con Universal LLM Key (~100 crediti residui da monitorare)
- [x] Account GitHub: repo mcnicastro-netizen/OMNIA

### Necessario M2 (ancora in corso)
- [x] API Key Resend (operativa, magic-link funzionanti)
- [ ] **Dominio Resend verificato** per inviare a email esterne (oggi sandbox)
- [ ] 3-5 **URL siti agenzie reali** per testare Clone-from-URL (M2.S5)
- [ ] Credenziali XML portali Idealista/Immobiliare.it/Casa.it (M2.S5)
- [ ] Logo OMNIA finale + paletta colori brand (M2.S6)

### Necessario M3
- [ ] Decisione prezzi annunci over-limit privati
- [ ] Validazione tono di voce
- [ ] Criteri **Agency Recommender** (algoritmo: quali 4 agenzie suggerire al privato venditore)
- [ ] Criteri "Immobili Segreti" (chi può accedere, costo accesso)

### Necessario M4
- [ ] Account Stripe + IBAN
- [ ] Tabella prezzi crediti + visibilità
- [ ] 1 agenzia pilota test
- [ ] Credenziali XML portali

### Necessario M5
- [ ] 30-50 FAQ chatbot
- [ ] 5 template contratti
- [ ] Account VisureItalia
- [ ] Partner mutui

### Necessario M6
- [ ] 1 corso pilota completo (script + slide + video)
- [ ] Eventuale accreditamento FIAIP/FIMAA

### Post-M6
- [ ] Namirial/Aruba (firma elettronica)
- [ ] WhatsApp Business
- [ ] Avvocato GDPR + contratti
- [ ] 2-3 agenzie pilota stabili

---

## 🚦 PARTE V — Sistema di emergenza (parole magiche)

| Parola magica | Cosa faccio io |
|---|---|
| **"Dove siamo"** | Stato attuale: M, sessione, %, prossimo step |
| **"Riassumi"** | Sunto di tutto fatto finora |
| **"Cambia piano"** | Rivediamo roadmap senza demolire |

---

## ⚠️ PARTE VI — Rischi e mitigazioni

| Rischio | Probabilità | Mitigazione |
|---|---|---|
| Scope creep | 🔴 Alta | Backlog Futuro, non in milestone in corso |
| Bloccato in attesa credenziali | 🟡 Media | Mock/sandbox e switch al live dopo |
| Burnout founder | 🟡 Media | Pause dopo M2 e M4 |
| Drift tecnico | 🟢 Bassa | INTERFACE_CONTRACT.md + monorepo |
| Competitor copia | 🟡 Media | M5 (AI) accelerato se serve |
| Costi infra | 🟢 Bassa | Monitoring + soft cap AI |

---

## 🎯 PARTE VII — Prossimo passo IMMEDIATO

**Stato al 24 Febbraio 2026**: M1 ✅ · M2 ✅ · M2.5 ✅ (5/5) · M2.6 ✅ (4/4) · M3 ✅ (7/9 DoD, 2 backlog Sprint 3) · M5.S1/S3/S4.1/S5 ✅ · Sprint 1 Publishing Center + Doppio Binario CHIUSO 3/3 · 180/180 pytest verdi.

Quando rientri prossima sessione:

1. 🟡 **P1 — Sprint 2 · M5.S2 HAL Knowledge (RAG)**: 3° bottone fisico HAL (D-040) su corpus PRD + ROADMAP + DECISIONS (cold start) + capitoli manuale disponibili. Emergent LLM Key già in `.env`, zero credenziali esterne. Prerequisito: chiamare `integration_playbook_expert_v2` prima di scrivere codice RAG.
2. 🟡 **P1b — M5.S2-pre Manuale Operativo**: completare i restanti 11 capitoli (Immobili, Clienti, Match, Publishing, Portali, Sito web, Virtual Staging, HAL Legal, Fascicolo, Valuator, Impostazioni). Può procedere in parallelo con S2 (arricchisce il corpus RAG progressivamente).
3. 🟢 **P2 — Sprint 3 · Chiusura backlog M3 + M5.S4.2/3/4**: ricerca avanzata multi-zona/disegno mappa (M3.S8), privacy audit 4 livelli (M3.S9), Reverse Staging + 4 varianti + prompt CRM-aware (M5.S4.2), micro-tour video 5s (M5.S4.3), A/B testing portale (M5.S4.4).
4. 🔵 **P3 — Sprint 4 · Perf hardening + Deploy readiness**: async geocoding via Motor background task (POST /properties da 3.6s → <500ms), projection esplicito su list properties (p95 da 2.6s → <200ms), stress test finale, deployment_agent pre-produzione.
5. 🟠 **P4 — M6 Omnia Academy**: LMS base + Quiz + Chatbot tutor + Marketplace agenti (post-Sprint 4).
6. 🔴 **P5 — M4 MLS + Stripe** (post-società, D-035).

Parole magiche per ripartire:
- *"Sprint 2"* / *"Partiamo con HAL Knowledge"* → M5.S2 RAG
- *"Riprendiamo il manuale"* → M5.S2-pre (capitolo 2 e successivi)
- *"Sprint 3"* → M3 backlog + M5.S4.2/3/4
- *"Sprint 4"* → Perf hardening
- *"Dove siamo"* → riassunto stato completo
- *"Audit"* → riassunto tabella stato M1→M5 in Cambiamenti strategici v3.1

---

*Documento approvato v2.1: 18 Giugno 2026*
*Documento approvato v3.0: 06 Luglio 2026 (ordine P0→P4 confermato dal Founder — pivot Doppio Binario)*
*Documento aggiornato v3.1: 24 Febbraio 2026 (audit M1→M5 vs realtà, chiusura Sprint 1 M2.5/M2.6 3/3)*
*Prossima revisione: alla chiusura di Sprint 2 (M5.S2 HAL Knowledge)*

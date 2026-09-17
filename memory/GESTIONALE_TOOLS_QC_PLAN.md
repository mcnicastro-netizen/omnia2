# Piano QC tools ImmoWeb — sessione domani

**Aggiornato**: 17 Settembre 2026  
**Contesto**: review esterna QC sulle 5 schermate — giudizio positivo su architettura prodotto; rischio principale = **gerarchia**, non mancanza feature.  
**Obiettivo domani**: provare **tutti i tool** del gestionale in ordine operativo (loop «mattina dell’agente»), senza burn vendor (Resend/Stripe/fal/portali live/Nominatim).  
**Gate**: solo dopo «vai» si implementano redesign sidebar / cockpit dashboard / score explainability.

---

## Complimenti (tenere a mente)

- Non è un CRUD: idea di prodotto chiara (immobili ↔ clienti ↔ match ↔ portali ↔ HAL).
- Clienti + Smart Sorting = differenziante («su chi lavorare»).
- HAL come guida operativa = onboarding/supporto; evoluzione naturale: Knowledge → contestuale → operativo con conferma.
- UI sobria B2B: tenere.
- Posizionamento target: **sistema operativo agenzia**, non «gestionale + AI».

**Non fare domani** (salvo «vai»): riscrivere sidebar, cockpit «Oggi», tooltip score 83, vista tabella immobili. Prima: **prova tool → report gap → poi priorità prodotto** (`ASPETTI` **A-028**).

---

## Setup (15 min)

1. `bash scripts/omnia-stack.sh ensure`
2. Spegnere bypass QC se ancora on: `CRM_PUBLIC_PREVIEW=0` + `restart-preview` (sessione review esterna chiusa).
3. Login founder / agency demo (credenziali solo da `memory/test_credentials.env`, non in chat).
4. Seed già OK da stress `7e1d21fd` (2k clients / 2k props; match su 40 active). Se DB vuoto: `python scripts/stress_gestionale.py --clients 2000` (no externals).
5. Output: `memory/GESTIONALE_TOOLS_QC_REPORT.md` + checklist PASS/FAIL per tool.

**Policy soft**: mock/skip Resend, Stripe checkout, fal staging live, publish portali, geocode hammer.

---

## Ordine di prova (allineato al feedback IA sidebar)

### A — OPERATIVO (priorità assoluta)

| # | Tool | Route | Cosa provare | Pass |
|---|------|-------|--------------|------|
| A1 | Dashboard | `/app/dashboard` | KPI caricano; quick actions aprono destinazioni corrette | 200 + navigazione OK |
| A2 | Immobili lista | `/app/properties` | cerca, filtri stato/operazione, apri card, importa CTA | lista + dettaglio |
| A3 | Immobile scheda | `/app/properties/:id` | salva campo, Fascicolo AI entry, Migliora HAL (no burn se mock) | persistenza + UI |
| A4 | Nuovo immobile | `/app/properties/new` | create minimo → compare in lista | create OK |
| A5 | Clienti smart | `/app/clients` | smart sort, tab caldo/acquirente, apri scheda, match count visibile | lista smart OK |
| A6 | Cliente scheda | `/app/clients/:id` | edit, match disponibili, tel/WA link | dettaglio OK |
| A7 | Nuovo cliente | `/app/clients/new` | create buyer minimo | create OK |
| A8 | Match | `/app/matches` | run match su cliente caldo; lista score; **non** fan-out 2k×2k | risultati limitati OK |
| A9 | Attività / follow-up | (se UI assente → **GAP**) | dove vive «da fare oggi»? | documentare assenza |

### B — PUBBLICAZIONE

| # | Tool | Route | Cosa provare | Pass |
|---|------|-------|--------------|------|
| B1 | Portali | `/app/publishing` | lista connessioni, compliance UI, **no sync live** | smoke UI/API |
| B2 | Wizard portale | `/app/publishing/wizard` | apri step 1–2, esci senza salvare credenziali live | UI OK |
| B3 | Social publisher | `/app/publishing/social` | pagina carica; no post live | UI OK |
| B4 | MLS | `/app/mls` | browse / join UI; no side-effect esterno | UI OK |
| B5 | Sito web | `/app/website` | tema/preview; no DNS | UI OK |
| B6 | Import XML | `/app/import` | UI + validazione file sample se presente | no crash |

### C — STRUMENTI

| # | Tool | Route | Cosa provare | Pass |
|---|------|-------|--------------|------|
| C1 | Virtual Staging | `/app/staging` | UI; **skip fal spend** (soft) | UI + soft skip |
| C2 | Mutui | `/app/mutui` | calcolo demo / form | output coerente |
| C3 | Modulistica | `/app/modulistica` | lista template, render PDF mock | PDF/mock OK |
| C4 | Moderazione | `/app/moderation` | coda se dati; altrimenti empty state | no 500 |

### D — INTELLIGENZA

| # | Tool | Route | Cosa provare | Pass |
|---|------|-------|--------------|------|
| D1 | Guida HAL | `/app/hal-knowledge` | 3 domande guida (MLS, publish, clienti) | risposta non vuota |
| D2 | HAL Assist (FAB) | global | domanda da scheda immobile se possibile | UI + risposta |
| D3 | HAL Legal | `/legal` o nav | query legale mock/fonte; no inventare | UI OK |
| D4 | Analytics A/B | `/app/analytics` | overview 30g | KPI/empty OK |

### E — AMMINISTRAZIONE

| # | Tool | Route | Cosa provare | Pass |
|---|------|-------|--------------|------|
| E1 | Gruppo | `/app/group` | solo se ruolo group/super | 200 o skip ruolo |
| E2 | Collaboratori | `/app/members` | lista + invito UI (no email live) | lista OK |
| E3 | API Keys | `/app/api-keys` | lista; create+revoke in sandbox se sicuro | CRUD controllato |
| E4 | Impostazioni | `/app/settings` | patch anagrafica agenzia | save OK |
| E5 | Billing | `/app/settings/billing` | plans UI; **no Stripe checkout** | UI OK |
| E6 | Brand Lab | `/app/brand-lab` | super_admin only | 200 o 403 atteso |
| E7 | Ops costi | `/app/ops` | super_admin | 200 |

---

## Loop «mattina dell’agente» (smoke end-to-end, 30–40 min)

Sequenza unica da filmare/annotare:

1. Apri Dashboard → annota se dice «cosa fare oggi» o solo KPI (**gap noto**).
2. Clienti → apri primo **CALDO** → Match → invita/annotare score.
3. Immobili → apri uno incompleto → prova HAL migliora / fascicolo.
4. Publishing → verifica readiness **senza** publish.
5. HAL Knowledge → «Come pubblico un immobile?».
6. Torna Dashboard → cosa è cambiato? (spesso poco → gap cockpit).

---

## Criteri di chiusura report

Per ogni tool: `PASS | FAIL | SKIP(soft) | GAP(prodotto)`.

Sezioni finali obbligatorie:
1. **Blocchi tecnici** (500, route morte, permessi sbagliati)
2. **Gap prodotto vs review QC** (sidebar flat, dashboard non operativa, score unexplained, no Attività)
3. **Top 5 fix** ordinati per impatto sul loop mattina (proposta — implementare solo con «vai»)
4. **Burn check**: zero chiamate a Resend/Stripe/fal/portali/Nominatim

---

## Fuori scope domani

- Redesign information architecture sidebar
- Cockpit «Oggi» + activity feed
- Vista tabella immobili + filtri intelligenti
- Tooltip Match Score breakdown
- HAL «esegui con conferma»
- Burn vendor / go-live

Queste voci finiscono in backlog prioritizzato **dopo** il report tools.

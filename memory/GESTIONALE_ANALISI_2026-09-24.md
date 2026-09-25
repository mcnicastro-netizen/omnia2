# Analisi gestionale ImmoWeb — 25 Settembre 2026

**Autore**: Cloud Agent (refresh post A-028a…i)  
**Fonte**: codice live (`AgencyShell`, `DashboardPage`, `PropertiesPage`, `MatchesPage`, `ActivitiesPage`, `matches.py`, coach/confirm-apply) + QC report 18-Set (**stale** su A9/A-028a)  
**Scopo**: verdetto aggiornato sul CRM agenzia dopo chiusura A-028. Solo proposte vincolate a «vai».  
**Demo commerciale (A-025)**: **in pausa** (Founder 25-Set) — non in coda operativa.

---

## 1. Verdetto in una frase

Il gestionale **ha il loop mattina dimostrabile** (Oggi → Attività → Immobili coach/filtri → Match spiegato → HAL conferma → Portali); il rischio non è più “mancano i pezzi P0 del review”, è **profondità operativa e rumore residuo** (Attività minimale, filtri smart incompleti, Analytics in nav, QC/docs stale, match ancora capped).

---

## 2. Mappa nav attuale (a cluster — A-028c ✅)

Da `AgencyShell.jsx` — voci raggruppate, route invariate:

| Cluster | Voci tipiche (admin) |
|---------|----------------------|
| **Operativo** | Dashboard · Immobili · Clienti · Richieste · **Attività** · Match |
| **Pubblicazione** | Importa · Pubblicità su portali · MLS · Sito web |
| **Strumenti** | **Analytics A/B** · Virtual Staging · Mutui · Modulistica |
| **Intelligenza** | HAL Legal · Guida HAL |
| **Amministrazione** | Gruppo · Cestino · Membri · Piano & Crediti · Impostazioni · (+ Brand Lab / Ops Founder) |

API Keys fuori nav primaria (D-092 ✅).  
**Residuo soft**: Analytics A/B resta in nav primaria del cluster Strumenti — rumore per l’agente medio rispetto al loop quotidiano.

---

## 3. Stato A-028 (chiuso 24-Set — verificato in codice 25-Set)

| ID | Tema | Stato | Evidenza live |
|----|------|:-----:|---------------|
| **A-028a** | Cockpit «Oggi» | ✅ | `GET /app/dashboard/today` + `TodayCockpit` sopra KPI |
| **A-028b** | Explain Match Score | ✅ | `MatchBreakdownBars` su card Match; popover fasce su `ScoreBox` Clienti |
| **A-028c** | Sidebar a cluster | ✅ | `NAV_CLUSTERS` + `data-testid="agency-nav-clusters"` |
| **A-028d** | HAL contestuale scheda | ✅ | `GET .../coach` + `PropertyCoachPanel` + improve su gap |
| **A-028e** | Vista tabella immobili | ✅ | toggle Card/Tabella + sort (no colonna agente v1) |
| **A-028f** | Filtri intelligenti | ✅ | `smart=no_photos\|incomplete\|weak_copy` (+ deep-link da Oggi) |
| **A-028g** | HAL esegui+conferma | ✅ | `proposal_id` + `POST /app/al/confirm-apply` + UI |
| **A-028h** | Modulo Attività | ✅ | CRUD `/app/activities` + pagina + coda Oggi |
| **A-028i** | Claim «OS agenzia» | ✅ | copy soft landing (nord OS, gestionale AI oggi) |

**Post D-092**: destinazioni dashboard, Import hub, Richieste vs Clienti, Portali onesti, Gruppo wizard — **ok**.

---

## 4. Loop mattina agente (9:00) — post A-028

| Passo | Oggi (25-Set) | Gap residuo |
|-------|---------------|-------------|
| Apri Dashboard | «Cosa fare oggi» + KPI + link Attività | Non è un calendario visite (lista due_at, no slot/agenda) |
| Follow-up / chiamate | Pagina Attività + coda Oggi | CRUD minimale: no link forte a cliente/immobile in create, no reminder push |
| Chiama / WhatsApp caldi | Clienti smart + score spiegato | OK per demo; smart path ancora il più lento a 2k (stress) |
| Guarda match | Cards + breakdown on click | Agency-wide **capped 400×400** (`scan_capped`); non è full inventory |
| Completa immobili | Tabella + filtri smart + coach | Manca filtro «senza match» e price-delta (fuori v1 A-028f) |
| Pubblica | Publishing 3 tab (D-092) | Ok |
| Chiedi a HAL | Guida + improve + conferma apply | Chat HAL ancora dipende da chiave LLM env; conferma-apply cablata |

**Conclusione loop**: dimostrabile end-to-end. Non serve altro P0 A-028.

---

## 5. Residui A-034 — **shippati 25-Set** (erano R1–R8)

| # | Tema | Stato |
|---|------|:-----:|
| R1 | Smart `no_match` | ✅ |
| R2 | Smart / flag `price_drop` | ✅ |
| R3 | Attività agenda settimana + link client/property | ✅ |
| R4 | Analytics fuori nav → Impostazioni | ✅ |
| R5 | UI Match `scan_capped` | ✅ |
| R6 | QC report STALE banner | ✅ (docs) |
| R7 | clients/smart cache scoped | ✅ |
| R8 | Colonna agente tabella | ✅ |

**Nuovi gap** (se emergono dall’analisi completa moduli oltre Clienti) → solo con «vai».

---

## 6. Cosa NON toccare

- **D-091** no MyAgency / area riservata cliente  
- Multiposting Idealista/Immobiliare (accordi commerciali)  
- Claim «OS agenzia» pieno (D-051 / A-028i soft già shippato)  
- A-031…033 B2C senza «vai»  
- **A-025 demo commerciale** — esplicitamente in pausa  
- Riaprire A-028 / A-034 chiusi come se fossero ❌

---

## 7. Documentazione stale da non credere

| Doc | Problema | Azione |
|-----|----------|--------|
| `GESTIONALE_TOOLS_QC_REPORT.md` (18-Set) | A9 = GAP Attività; LOOP dice dashboard KPI-only | Banner STALE; rieseguire solo con «vai» |
| Analisi 24-Set (prima bozza A-028 ❌) | Superata | Rev. 25-Set + A-034 |
| Stress report 17-Set | Match OK con 40 active; non riflette harden 400×400 | Utile per latency storica |

---

## 8. Ordine di attacco consigliato (prossimo «vai»)

Dopo A-034 e §10: solo gap **G1–G6** sotto (o B2C A-031…). Nessun P0 aperto sul loop mattina.

---

## 9. Decisione operativa (25-Set)

Founder: rifinire residuali, poi analizzare tutto il resto del gestionale.  
→ A-034 R1–R8 shippati.  
→ Demo A-025 resta in pausa.  
→ Tunnel CRM: cloudflared **http2** (anti-530 QUIC).  
→ §10 = mappa moduli oltre Clienti.

---

## 10. Analisi resto moduli (25-Set) — oltre Dashboard / Immobili / Match / Attività

### Operativo

| Modulo | Stato | Nota da codice |
|--------|:-----:|----------------|
| **Clienti** | ✅ solido | `ClientsPage` smart: segmenti searchers/sellers, bucket temperatura, score explain, refresh AI. Path lento mitigato A-034 R7. |
| **Richieste** | ✅ solido | `RequestsPage` + form: tipi interest/search_brief, stati, match portfolio/MLS, vista rete. Allineato D-089/D-090. |
| **Match** | ✅ + onesto | Banner campione (R5). Scoped client/property restano il path «completo». |

**Gap soft Clienti/Attività**  
- **G1** — Attività: link cliente/immobile via UUID testuale (no autocomplete). Funziona, UX grezza.  
- **G2** — Clienti smart: bucket temperatura su scan capped (già documentato in API `counts_scope`).

### Pubblicazione

| Modulo | Stato | Nota |
|--------|:-----:|------|
| **Importa** | ✅ | Hub 3 card (`ImportHubPage`) → XML / clienti / legacy. D-092. |
| **Pubblicità portali** | ✅ onesto | Tab attivi / attivabili / in arrivo + sync/compliance. Multiposting Idealista/Immobiliare = fuori (accordi). |
| **Social** | ✅ v1 | On-demand, no scheduler (Cap.15 onesto). |
| **MLS** | ✅ seed | Dashboard + inventory scope + partners/offers. Rete commerciale post-società. |
| **Sito web** | ✅ | Brand Studio + domain. |

**Gap soft Pubblicazione**  
- **G3** — Social: niente calendario editoriale (già backlog Cap.15, non riaprire senza «vai»).

### Strumenti

| Modulo | Stato | Nota |
|--------|:-----:|------|
| **Analytics A/B** | ✅ fuori nav | Overview + confronto 2–6 listing. Ora da Impostazioni (R4). |
| **Virtual Staging** | ✅ | Crediti + fal (skip burn in QC). |
| **Mutui** | ✅ | Comparatore operativo. |
| **Modulistica** | ✅ | Template + docs; e-sign status soft. |

### Intelligenza

| Modulo | Stato | Nota |
|--------|:-----:|------|
| **Guida HAL** | ✅ | Knowledge + ask (dipende LLM key env). |
| **HAL Legal** | ✅ | Chat + disclaimer. |
| **HAL in scheda** | ✅ | Coach + improve + conferma (A-028d/g). |

### Amministrazione

| Modulo | Stato | Nota |
|--------|:-----:|------|
| **Membri** | ✅ | Inviti / ruoli. |
| **Piano & Crediti** | ✅ | Billing Founders; checkout Stripe soft in QC. |
| **Impostazioni** | ✅ | Identità + API Keys + Analytics + notifiche. |
| **Gruppo** | ✅ | Wizard multi-filiale (group_admin). |
| **Cestino** | ✅ | Soft-delete restore. |
| **Brand Lab / Ops** | ✅ Founder | Solo `super_admin`. |
| **Moderazione B2C** | ✅ route | Coda annunci privati — **non in nav CRM** (ok: non è loop agente). |

### Verdetto §10

Il gestionale **non ha buchi grossi di prodotto** fuori dal loop già chiuso. I residui utili sono **G1** (autocomplete Attività) e, solo se serve go-to-market portali, gli accordi Idealista/Immobiliare (non codice). Il resto è profondità (scheduler social, MLS commerciale) già esplicitamente fuori o post-società.

### Backlog candidato (solo «vai»)

| ID | Tema | Effort |
|----|------|:------:|
| G1 | Autocomplete cliente/immobile in Attività | S |
| G2 | Copy UI su `counts_scope` Clienti smart | XS |
| G3 | Social scheduling | L (Cap.15) |
| — | B2C A-031…033 | binario D-093 |
| — | Demo A-025 | ⏸ pausa |

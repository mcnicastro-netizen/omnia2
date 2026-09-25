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

*Audit codice cross-check: [Audit moduli CRM](bc-37f6b433-b800-5ba0-8f71-5e2d50a2f2ee).*

### Operativo

| Modulo | Stato | Nota da codice |
|--------|:-----:|----------------|
| **Clienti** | ✅ solido | `ClientsPage` smart: Acquirenti/Venditori, bucket temperatura, call/WA, score explain, refresh AI. Scheda: preferenze, immobili in carico, richieste. Path lento mitigato A-034 R7. |
| **Richieste** | ✅ solido | `RequestsPage` + form: tipi interest/search_brief, stati, match portfolio/MLS, share rete. D-089/D-090. |
| **Match** | ✅ + onesto | Banner campione (R5). Scoped client/property = path «completo». |

**Gap soft Operativo**  
- **G1** — Attività: link cliente/immobile via UUID (no autocomplete).  
- **G2** — Clienti smart: copy su `counts_scope` / scan capped.  
- **G5** — Lista Venditori: niente conteggio «immobili in carico» in riga (solo in scheda).

### Pubblicazione

| Modulo | Stato | Nota |
|--------|:-----:|------|
| **Importa** | ✅ | Hub 3 card (`ImportHubPage`) → XML / immobili / clienti. D-092. |
| **Pubblicità portali** | ✅ onesto | Tab attivi / attivabili / in arrivo + sync/compliance. Push Idealista/Immobiliare = fuori (accordi). |
| **Social** | ✅ v1 | On-demand FB/IG/Telegram/… — no scheduler (Cap.15). |
| **MLS** | ✅ seed | Join, scope mine/locale/Italia, partner, offerte. |
| **Sito web** | ✅ | Brand extract, temi, custom domain. |

**Gap soft Pubblicazione**  
- **G3** — Social scheduling (Cap.15, L).

### Strumenti

| Modulo | Stato | Nota |
|--------|:-----:|------|
| **Analytics A/B** | ✅ fuori nav | Overview + A/B 2–6 listing → Impostazioni (R4). |
| **Virtual Staging** | ✅ | Studio + crediti + 402 se insufficienti. |
| **Mutui** | ✅ | Wrapper su comparatore in-house. |
| **Modulistica** | ✅ caveat | PDF white-label; e-sign **mock** in locale (Yousign/DocuSign solo con credenziali). |

### Intelligenza

| Modulo | Stato | Nota |
|--------|:-----:|------|
| **Guida HAL** | ✅ | Ask/history; widget chat nascosto su quella pagina. |
| **HAL Legal** | ✅ frizione | Chat + PDF + disclaimer; route `/{lang}/legal` **fuori** `AgencyShell` (shell CRM sparisce). |
| **HAL in scheda** | ✅ | Coach + improve + conferma (A-028d/g). |

**Gap soft**  
- **G6** — HAL Legal: restare in shell CRM o CTA «torna al gestionale» più evidente.

### Amministrazione

| Modulo | Stato | Nota |
|--------|:-----:|------|
| **Membri** | ✅ | Inviti / revoke (admin). |
| **Piano & Crediti** | ✅ soft-gate | Billing + storage; gate demo D-080 via `localStorage` (bypassabile — ok MVP). |
| **Impostazioni** | ✅ | Anagrafica + API Keys + Analytics + notifiche/security. |
| **Gruppo** | ✅ | Wizard multi-filiale (`group_admin` / `super_admin`). |
| **Cestino** | ✅ | Soft-delete property/client, 30g. |
| **Brand Lab / Ops** | ✅ Founder | Statico + costi; solo `super_admin`. |
| **Moderazione B2C** | ⚠ gap nav | Coda approve/reject **funziona** (`ModerationPage` + `moderation.py`, solo `super_admin`) ma **assente da nav** → URL da conoscere. |

### Verdetto §10

Niente buchi P0 sul loop agenzia. Unico gap **reale e piccolo**: discoverability Moderazione Founder (**G4**). Soft: G1, G5, G6, e-sign reale, demo-gate server-side. Multiposting portali / MLS commerciale / demo A-025 = fuori o in pausa.

### Backlog candidato (solo «vai»)

| ID | Tema | Effort |
|----|------|:------:|
| **G4** | Nav Moderazione B2C per `super_admin` (o link da Ops) | S |
| G1 | Autocomplete cliente/immobile in Attività | S |
| G2 | Copy UI `counts_scope` Clienti smart | XS |
| G5 | Conteggio immobili in lista Venditori | S |
| G6 | HAL Legal in shell / CTA ritorno CRM | S |
| G3 | Social scheduling | L (Cap.15) |
| — | E-sign provider reale | M (credenziali) |
| — | Demo-gate billing server-side | M |
| — | B2C A-031…033 | binario D-093 |
| — | Demo A-025 | ⏸ pausa |

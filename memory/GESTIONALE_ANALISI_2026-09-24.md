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

## 5. Residui concreti (nuovo backlog — solo con «vai»)

Ordinati per impatto sul loop / fiducia / demo stress (non ship senza ok Founder):

| # | Tema | Perché | Effort | Note |
|---|------|--------|:------:|------|
| R1 | **Filtro smart `no_match`** (immobili attivi senza cliente/richiesta sopra soglia) | Completa A-028f come da review esterna | M | Richiede scan match capped o materiale notturno |
| R2 | **Filtro / flag price-delta** (ribasso recente) | Coda commerciale «da ripubblicare / avvisare» | M | Dati prezzo storico se già presenti |
| R3 | **Attività → calendario leggero** (settimana + link client/property obbligatori) | Oggi è todo-list, non agenda visite | M–L | Cap.2 già onesto: «non calendario completo» |
| R4 | **Analytics A/B fuori nav primaria** (sotto Impostazioni o Founder-only) | Riduce rumore sidebar | S | Solo IA nav, zero backend |
| R5 | **Match: paginate / require filter / cap UI onesto** | Cap 400×400 mitiga A8 ma UI non spiega `scan_capped` | S | Badge «campione» + link scoped client/property |
| R6 | **QC Tools report refresh** | Report 18-Set dice A9 GAP + dashboard KPI-only → confonde riprese | S | Docs/automation; non prodotto |
| R7 | **clients/smart p95** a seed 2k | Stress: path più lento (~436 ms p95) | M | Ottimizzazione, non feature |
| R8 | **Colonna agente** in tabella immobili | Lasciato fuori A-028e v1 | S | Se multi-agente in demo |

**Non in questa lista**: A-031…033 B2C (altro binario D-093); A-025 demo (pausa); multiposting Idealista/Immobiliare (accordi); redesign visuale / dark mode.

---

## 6. Cosa NON toccare

- **D-091** no MyAgency / area riservata cliente  
- Multiposting Idealista/Immobiliare (accordi commerciali)  
- Claim «OS agenzia» pieno (D-051 / A-028i soft già shippato)  
- A-031…033 B2C senza «vai»  
- **A-025 demo commerciale** — esplicitamente in pausa  
- Riaprire A-028 chiuso come se fosse ❌ (il file analisi precedente era stale)

---

## 7. Documentazione stale da non credere

| Doc | Problema | Azione |
|-----|----------|--------|
| `GESTIONALE_TOOLS_QC_REPORT.md` (18-Set) | A9 = GAP Attività; LOOP dice dashboard KPI-only | Segnato stale in coda report; rieseguire solo con «vai» |
| Analisi 24-Set (prima revisione in questo file) | A-028b…f ancora ❌ | **Sostituita** da questa revisione 25-Set |
| Stress report 17-Set | Match OK con 40 active; non riflette harden 400×400 | Ancora utile per clients/smart latency |

---

## 8. Ordine di attacco consigliato (prossimo «vai»)

| Priorità | Item | Perché |
|:--------:|------|--------|
| 1 | **R4** Analytics fuori nav | Quick win IA, zero rischio |
| 2 | **R5** UI onesta su match capped | Fiducia + anti-confusione demo |
| 3 | **R6** Refresh QC report | Allinea SoT docs |
| 4 | **R1** smart `no_match` | Chiude gap review esterna su Immobili |
| 5 | **R3** Attività → agenda leggera | Profondità loop visite |
| 6 | R2 / R7 / R8 | Dopo i precedenti |

**B2C P1** (A-031…033) resta binario separato — non mischiare con harden gestionale salvo priorità Founder.

---

## 9. Decisione operativa di questa sessione (25-Set)

Founder: «tralascia la demo… ultimiamo lavoro in programma e continuiamo con analisi del gestionale».

→ A-028 già chiuso in codice + HAL sync (sera 24-Set) — **nessun ship codice aggiuntivo senza nuovo «vai»**.  
→ Demo A-025 **in pausa**.  
→ Questo documento = SoT analisi gestionale aggiornata + backlog residuale R1–R8.  
→ Prossimo passo prodotto: solo con «vai» su una riga della §8 (o B2C A-031…).

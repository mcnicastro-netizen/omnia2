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

Dopo A-034: **analisi completa restanti moduli** (Richieste, Pubblicazione, Strumenti, Admin) → nuovo backlog solo se gap reali.  
Binario B2C: A-031…033 separato.

---

## 9. Decisione operativa (25-Set)

Founder: rifinire residuali, poi analizzare tutto il resto del gestionale (eravamo ai Clienti).  
→ A-034 R1–R8 shippati.  
→ Demo A-025 resta in pausa.  
→ Tunnel CRM condivisibile (cloudflared http2).  
→ Sezione analisi moduli restanti: append sotto (§10) quando audit completo.

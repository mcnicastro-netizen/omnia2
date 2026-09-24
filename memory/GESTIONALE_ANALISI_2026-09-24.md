# Analisi gestionale ImmoWeb — 24 Settembre 2026

**Autore**: Cloud Agent (post D-092 / D-093)  
**Fonte**: codice live + `GESTIONALE_TOOLS_QC_REPORT` (18-Set, parzialmente stale) + A-028  
**Scopo**: verdetto onesto sul CRM agenzia e ordine di ship. Solo proposte vincolate a «vai» sulle sotto-voci.

---

## 1. Verdetto in una frase

Il gestionale **ha già il loop prodotto** (immobili ↔ clienti ↔ richieste ↔ match ↔ portali ↔ HAL); il rischio non è “mancano 30 feature”, è **gerarchia e fiducia sul numero** (sidebar piatta, score non spiegato in lista, scala immobili a card-only).

---

## 2. Mappa nav attuale (flat)

Da `AgencyShell.jsx` (ordine reale, admin tipico):

| Voce | Ruolo |
|------|--------|
| Dashboard | Operativo |
| Importa | Pubblicazione / migrazione |
| Pubblicità su portali | Pubblicazione |
| Immobili | Operativo |
| Clienti | Operativo |
| Richieste | Operativo (D-089) |
| Cestino | Admin |
| Match | Operativo |
| Analytics A/B | Strumenti |
| MLS | Pubblicazione / rete |
| Sito web | Pubblicazione |
| Virtual Staging | Strumenti / AI |
| Mutui | Strumenti |
| Modulistica | Strumenti |
| HAL Legal | Intelligenza |
| Guida HAL | Intelligenza |
| Membri | Amministrazione |
| Piano & Crediti | Amministrazione |
| Impostazioni | Amministrazione |
| (+ Brand Lab / Ops) | Founder |

**Problema**: ~15–18 voci allo stesso livello → l’agente “mattina” non ha una gerarchia mentale. API Keys già fuori nav (D-092 ✅).

---

## 3. Stato A-028 (aggiornato 24-Set)

| ID | Tema | Stato | Evidenza |
|----|------|:-----:|----------|
| **A-028a** | Cockpit «Oggi» | ✅ | `GET /app/dashboard/today` + `DashboardPage` TodayCockpit (QC report ancora dice KPI-only → **stale**) |
| **A-028b** | Explain Match Score | ❌ lista | API match già manda `breakdown`+`missing`; UI lista mostra solo chips “Mancano”. Breakdown pieno solo su Lead Score page |
| **A-028c** | Sidebar a cluster | ❌ | `navItems` flat |
| **A-028d** | HAL contestuale scheda | 🟡 | «Migliora» titolo/descrizione + Fascicolo; manca pannello «cosa manca / genera da dati» |
| **A-028e** | Vista tabella immobili | ❌ | solo grid card (`PropertiesPage`) |
| **A-028f** | Filtri intelligenti | ❌ | status/operation base; no «senza foto / incompleti» |
| **A-028g** | HAL esegui+conferma | ✅ | `proposal_id` + `/al/confirm-apply` + UI Conferma e applica |
| **A-028h** | Modulo Attività | ✅ | CRUD + pagina + coda Oggi |
| **A-028i** | Claim «OS agenzia» | ✅ | copy soft landing (nord OS, gestionale AI oggi) |

**Post D-092**: destinazioni dashboard, Import hub, Richieste vs Clienti, Portali onesti, Gruppo wizard — **ok**. Residuo soft: Analytics A/B ancora in nav primaria (rumore per agente medio).

---

## 4. Loop mattina agente (9:00)

| Passo | Oggi | Gap |
|-------|------|-----|
| Apri Dashboard | «Cosa fare oggi» + KPI | Code ok; non sostituisce calendario visite/attività |
| Chiama / WhatsApp caldi | Clienti smart + score | **83 senza spiegazione** in riga |
| Guarda match | Cards + missing chips | Breakdown nascosto; `/app/matches` agency-wide **FAIL perf** sotto stress (2M pair) |
| Completa immobili | Card grid | A 2k+ serve **tabella** + filtri incompleti |
| Pubblica | Publishing 3 tab (D-092) | Ok |
| Chiedi a HAL | Guida + improve | Contestuale scheda ancora debole |

---

## 5. Top problemi concreti

1. **Sidebar piatta** — `AgencyShell.jsx` · A-028c  
2. **Score opaco in lista** — Clients/Matches · A-028b (dati già in API)  
3. **Match agency-wide perf bomb** — QC A8 FAIL · rischio demo stress  
4. **Immobili solo card** — `PropertiesPage.jsx` · A-028e  
5. **Niente filtri «incompleti / senza foto»** — A-028f  
6. **Nessun modulo Attività** — GAP A9 · A-028h (P2; cockpit the workaround)  
7. **Analytics A/B in nav primaria** — rumore vs loop quotidiano  
8. **QC report stale su A-028a** — confonde riprese future

---

## 6. Cosa NON toccare

- **D-091** no MyAgency / area riservata cliente  
- Multiposting Idealista/Immobiliare (accordi commerciali)  
- Redesign visuale completo / dark mode / “OS” claim prima del loop dimostrabile  
- A-031…033 B2C (già backlog D-093, altro binario)

---

## 7. Ordine di attacco consigliato

| Priorità | ID | Perché | Effort |
|:--------:|----|--------|:------:|
| 1 | **A-028b** | Fiducia immediata; breakdown già in API | S |
| 2 | **A-028c** | Solo IA nav; zero backend | S |
| 3 | **Match list harden** | Evita kill API in demo (cap/paginate/require filter) | M |
| 4 | **A-028d** | Copilota in scheda | M |
| 5 | **A-028e+f** | Scala 2k+ | M |
| 6 | A-028h / i | Dopo loop stabile | L / copy |

**Quick wins**: b + c. **Invasivi**: e/f tabella, h attività, g esegui-con-conferma.

---

## 8. Decisione operativa di questa sessione

Founder: «vai» sulla ripresa **analisi gestionale**.  
→ Documento pubblicato qui.  
→ Ship immediato dei quick win **A-028b + A-028c** (già in cima all’ordine A-028 approvato).  
→ Match harden + A-028d restano per successivo «vai» esplicito.

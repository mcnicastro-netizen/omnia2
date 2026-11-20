# ⛔ HANDOFF PRE-GTM — ORDINI INDIFFERIBILI AL PROSSIMO AGENTE

**Data:** 21 novembre 2026 ~00:00 Europe/Rome  
**Founder:** Marco Nicastro  
**Lingua:** italiano obbligatorio  
**Repo SoT:** `github.com/mcnicastro-netizen/omnia2` (mai Origin-tmp / New Project)

> Se leggi solo un file in questa sessione, leggi **questo**.  
> Poi: `NEXT_SESSION.md` · `DECISIONS.md` (D-191) · programma in `_export_audits/`.

---

## 1. Il punto (non fraintendere)

1. **Il gestionale non è “morto” perché ci sono 49 card senza SUPERATO.**  
   La riconciliazione dimostra: criteri più severi + copertura più ampia + DB CONTINUITY.  
   Fonte: `_export_audits/RICONCILIAZIONE-PRIMO-E2E-VS-E2E-20-NOVEMBRE.md`.

2. **Non ripartire da zero e non rifare un audit generale** senza mandato.  
   Gli audit/E2E/riconciliazione/programma esistono già.

3. **Non contare le PARZIALI come percentuale di malfunzionamento.**

4. **Non correggere nulla finché il Founder non emette un mandato di implementazione esplicito.**  
   Il programma attuale è pianificazione. `D-191` = READ-ONLY chiuso / implementazione **non** autorizzata.

5. **LLM/HAL non è un optional.**  
   OMNIA non può presentarsi come gestionale evoluto se HAL/AI sono instabili o incontrollabili nei costi.  
   Non risolvere `llm_busy` “cambiando modello” senza diagnosi di causa (provider vs orchestrazione vs app vs hold).

6. **PR #240 è già in `main`.**  
   Non ripartire dal task “patch 3 finding e merge #240” come se fosse ancora aperto (era D-190 fine pomeriggio; superseduto dal merge + lavoro sera).

---

## 2. Ordini indifferibili (vietato violare)

| # | Ordine |
|---|--------|
| O1 | **Niente codice prodotto** finché non c’è autorizzazione Founder distinta (S1+ del programma). |
| O2 | **Niente H4 sealed / Stripe LIVE / sealed mint / checkout** senza mandato dedicato. |
| O3 | **Niente seed/reset/migrazioni/account** su Dogfood senza mandato. |
| O4 | **Niente nuovo E2E mutativo generale** “per sicurezza”. |
| O5 | **Non riaprire decisioni `APPROVATO`** in `DECISIONS.md` senza gap tecnico documentato. |
| O6 | **Non dichiarare GTM-ready** né “SUPERATO” inventati. |
| O7 | **Non inventare percentuali** di funzionamento. |
| O8 | **Sequenza obbligatoria se/quando autorizzato:** fondazioni (A-007) → LLM/HAL → org/security → ciclo+MLS → documenti → billing → UI/GTM. |
| O9 | **AI = piano di accettazione autonomo** (stabilità, concorrenza, degrado, qualità, costi, osservabilità). |
| O10 | **Sync docs:** ogni ship futura aggiorna MD + YAML HAL nello stesso giro (`MANUAL_SYNC.md` / D-084). |
| O11 | Workspace = `/workspace` o checkout `omnia2` GitHub — **anti New Project**. |
| O12 | Segreti: non stampare; non committare `.env`. |

---

## 3. Cosa è già fatto (non rifare)

| Deliverable | Path |
|-------------|------|
| Primo E2E gestionale dogfood | Artifacts `D175-E2E-DEEP-*` · SHA `9aec192` · CLEAN |
| E2E INTEGRALE PRE-GTM | Artifacts `E2E-INTEGRALE-*` + dossier Founder · SHA `759d628` · CONTINUITY |
| Riconciliazione DEEP vs INTEGRALE | `_export_audits/RICONCILIAZIONE-PRIMO-E2E-VS-E2E-20-NOVEMBRE.md` |
| Programma 8 aree pre-GTM | `_export_audits/OMNIA-PROGRAMMA-STABILIZZAZIONE-PRE-GTM.md` |
| Anomalie A-001…A-008 | `E2E-INTEGRALE-ANOMALIE.md` / dossier |
| PR #240 Deal/chat/docs | **MERGED** `f0d4b26` → tip docs `759d628` |

---

## 4. Prossimo passo legittimo (solo dopo “vai” Founder)

Aprire **un solo** mandato tra:

- **S1** — Diagnosi tecnica approfondita A-007 (+ eventuale A-006) READ-ONLY → bozza patch **senza merge** finché non autorizzato S2.  
- **S3** — Diagnosi LLM/HAL (cause `llm_busy` classificate, metriche, piano accettazione) **senza** introdurre secondo provider.  

**Default se il Founder non sceglie:** chiedere quale tra S1 e S3; **non** inventare un terzo cantiere.

---

## 5. Letture obbligatorie (ordine)

1. Questo file  
2. `memory/NEXT_SESSION.md`  
3. `memory/DECISIONS.md` → **D-191** (e D-075/D-040/D-135 per AI; B01/B02/D-185 per org)  
4. `_export_audits/OMNIA-PROGRAMMA-STABILIZZAZIONE-PRE-GTM.md`  
5. `_export_audits/RICONCILIAZIONE-PRIMO-E2E-VS-E2E-20-NOVEMBRE.md`  
6. `memory/manuale/hal/IMPORT_HAL.md` (voci `api.pre-gtm-programma`, `api.llm-busy`, `api.d175-pr240`)

---

## 6. Anomalie — priorità (non fixare ora)

1. **A-007** lista immobili `created_at` (HIGH)  
2. **A-006** API key `agency_inactive` (HIGH)  
3. **A-002** billing/H4 (HIGH, gate)  
4. **AI `llm_busy`** (critico reputazionale; non è A-00x ma VERIFICATO)  
5. **A-003** fixture MA/agent  
6. A-001, A-004, A-005, A-008

---

## 7. Frasi tipiche da non dire al Founder

- «Rifacciamo tutto l’E2E da zero.»  
- «Con 35 PARZIALI il prodotto è al 30%.»  
- «Basta cambiare modello Gemini.»  
- «Apro H4 per verificare.»  
- «Mergio su main senza OK.»  
- «#240 non è ancora mergiata» (è in main).

---

**Fine ordini.** Attendi istruzioni Founder. Zero implementazione spontanea.

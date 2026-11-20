# OMNIA — Programma strategico di stabilizzazione, completamento e preparazione GTM

**Mandato:** pianificazione e verifica **READ-ONLY**  
**Data:** 20 novembre 2026 (Europe/Rome)  
**Autorizzazione implementazione:** **NON CONCESSA**  
**Baseline storica:** riconciliazione `RICONCILIAZIONE-PRIMO-E2E-VS-E2E-20-NOVEMBRE.md` · DEEP `9aec192` · INTEGRALE `759d628`

**Etichette usate:** `APPROVATO` · `IMPLEMENTATO` · `VERIFICATO` · `PARZIALE` · `PROPOSTA` · `APERTO` · `NON VERIFICABILE`

---

## 1. Executive summary

OMNIA non parte da zero. Il nucleo gestionale (CRM + MLS multi-filiale) risulta **operativo a Livello 1** sul percorso Dogfood DEEP e riconfermato in larga parte dall’INTEGRALE; il dossier con **0 SUPERATO** misura soprattutto **criteri più ampi e lacune di copertura**, non un crollo generale del prodotto. Fonte: riconciliazione §1 e §11.

Il percorso verso un gestionale **affidabile e commercialmente credibile** richiede un programma ordinato in **8 aree**, con tre priorità critiche trasversali:

1. **Fondamenta dati/errori** (A-007 e integrità legacy) — senza lista immobili stabile ogni demo e ogni E2E successivi sono contaminati.  
2. **LLM / HAL / AI** — componente trasversale; oggi `llm_busy` / 503 / 502 sono **VERIFICATI** in collaudo e **IMPLEMENTATI** come mapping a overload Gemini + circuit breaker, ma mancano concorrenza globale, token reali e piano di accettazione autonomo.  
3. **Organizzazione / Main Admin / permessi** — decisioni Founder già `APPROVATO`; fixture e operabilità CC restano `PARZIALE` / `APERTO` (A-002, A-003).

**Regola di esecuzione raccomandata (PROPOSTA, non autorizzazione):** non aprire otto cantieri insieme. Sequenza: fondazioni → LLM/HAL → org/security → ciclo gestionale+MLS → documenti/strumenti → billing (con gate) → UI/GTM.

Questo documento è una **roadmap eseguibile**. Non modifica il prodotto. Non riapre decisioni `APPROVATO` senza motivo tecnico documentato.

---

## 2. Stato attuale ricostruito dalle evidenze

### 2.1 Contesto storico (VERIFICATO)

| Evento | SHA / contesto | Fonte |
|--------|----------------|-------|
| Primo E2E gestionale dogfood `D175-E2E-DEEP` | `9aec192` · CLEAN `omnia_df_clean_c4` | `D175-E2E-DEEP-FINAL-REPORT.md` |
| Merge PR#240 Deal/chat/docs | `f0d4b26` → tip docs `759d628` | `E2E-INTEGRALE-PREVIOUS-RECOVERY.json` |
| E2E INTEGRALE PRE-GTM | `759d628` · CONTINUITY stesso DB name | `E2E-INTEGRALE-00-PREFLIGHT.md` |
| Riconciliazione | nessuna regressione CRM/MLS confermata; A-007 latente | `RICONCILIAZIONE-…md` |

### 2.2 Livelli di maturità (sintesi)

| Livello | Stato | Fonte |
|---------|-------|-------|
| L1 Nucleo API CRM/MLS | **PARZIALE** ma usable post-fixture; lista fragile (A-007) | DEEP + INTEGRALE + riconciliazione |
| L2 Flussi E2E coerenti | **PARZIALE** — Deal/docs entrati via #240; visite/billing incompleti | PREVIOUS-RECOVERY + card DEA/DOC/MLS |
| L3 Prontezza GTM | **NON** dichiarabile | `E2E-GTM-VERIFICA.md` |

### 2.3 Cosa non fare

- Contare le card PARZIALI come “% rotto”.  
- Confondere CONTINUITY sporca con regressione tip.  
- Dichiarare integrazione completa perché esiste un endpoint.  
- “Sistemare” `llm_busy` cambiando modello senza diagnosi di causa.

---

## 3. Otto aree di lavoro

Mappatura Founder → codice documento:

| # Founder | Area documento | Priorità |
|-----------|----------------|----------|
| 1 | **A** Fondamenta tecniche e affidabilità | Critica |
| 2 | **B** CommercialCustomer, org, sicurezza | Critica |
| 3 | **C** LLM, HAL, infrastruttura AI | Critica (+ piano accettazione autonomo) |
| 4 | **D** Ciclo gestionale immobiliare | Alta |
| 5 | **E** MLS, ImmobilCloud, collaborazione | Alta |
| 6 | **F** Documenti e strumenti professionali | Media-Alta |
| 7 | **G** Billing, crediti, storage, provider | Alta (gate) |
| 8 | **H** UI, UX, GTM | Alta (dopo stabilizzazione L1–L2) |

Dettaglio per area: sezioni 4–11 e appendici sotto.

---

## 4. Anomalie e criticità documentate (A-001…A-008)

Fonte canonica: `E2E-INTEGRALE-ANOMALIE.md` + lettura riconciliazione §5.

| ID | Gravità | Classificazione storica | Impatto sul programma | Area primaria |
|----|---------|-------------------------|----------------------|---------------|
| A-007 | HIGH | Problema latente + copertura insufficiente nel DEEP (**non** regressione tip confermata) | Blocca affidabilità lista immobili / demo | **A** |
| A-006 | HIGH | Fuori perimetro DEEP; difetto gateway `is_active` | Blocca narrativa developer API | **A** + developer in **G/F** |
| A-002 | HIGH | Già presente (H4 chiuso / CC non operable) | Blocca GTM economico | **G** + **B** |
| A-003 | MEDIUM | Seed/fixture già fragili nel DEEP; drift CONTINUITY | Contamina collaudi MA/agent | **B** |
| A-001 | MEDIUM | Emergente post-#240 (Deal non esisteva nel DEEP) | Qualità errori Deal post-revoca | **D** / **E** |
| A-004 | INFO (impatto GTM alto) | Limite piattaforma collaudo UI | Blocca certificazione schermo | **H** |
| A-005 | INFO | Qualità watermark residua | Qualità documenti | **F** |
| A-008 | INFO | Side-effect collaudo gruppo | Fixture meno pulite | **B** |

**Criticità AI non numerate A-00x ma VERIFICATE in dossier:** TOOL-08 / PROV-03 **PARZIALE** — `llm_busy` 502/503. Fonte: card INTEGRALE + `shared/llm`.

---

## 5. Problemi non ancora verificati (o NON VERIFICABILE)

Elenco non esaustivo, da trattare come `APERTO` / `NON VERIFICABILE` finché non autorizzato un piano di prova:

- A-007 sullo stesso tip `9aec192` con stessi legacy (per chiudere “già presente vs introdotto”).  
- Stripe TEST checkout+webhook con H4 sealed.  
- Lifecycle past_due / deroga / cease E2E su CC reale operable.  
- Multiposting sync verso portale sandbox.  
- fal.ai generate staging (costo; NON ESEGUITO).  
- Resend send reale.  
- Computer-use UI full (A-004).  
- Matrice permessi UI vs API bit-a-bit.  
- Token usage reale Gemini (oggi COGS stimato).  
- Fallback OpenAI (flag inventariato, client assente) — `IMPLEMENTATO`: no; `PROPOSTA` solo dopo privacy/autorizzazione.

---

## 6. Analisi dedicata LLM / HAL (Area C — progetto autonomo)

### 6.1 Architettura osservata (IMPLEMENTATO nel repository)

Catena reale oggi:

```
Utente OMNIA (3 entry point fisici — D-040 APPROVATO)
  → HAL Agents (/api/app/al/*)  |  HAL Knowledge (/api/app/hal/knowledge/*)  |  HAL Legal (/api/app/legal/*)
  → Orchestrazione locale (tool CRM / RAG TF-IDF / Tavily+validator)
  → shared.llm.generate_text*  (Gemini via GEMINI_API_KEY | GOOGLE_API_KEY | EMERGENT_LLM_KEY)
  → Eventuale model fallback interno (flash → lite)
  → Risposta + audit (al_audit / al_legal_audit / hal_knowledge_sessions)
```

**Fonti codice:**  
`backend/shared/llm/__init__.py`, `backend/shared/llm/chat.py`,  
`backend/apps/immoweb/al_agent.py`, `hal_knowledge.py`, `al_legal/`,  
`backend/shared/security/circuit.py`, `backend/shared/ops/provider_flags.py`.

**Staging/video = percorso distinto fal.ai** (`FAL_KEY`) — non confondere con LLM testo. Critic/analisi staging possono però **consumare Gemini** e contendersi la stessa chiave.

**Decisioni APPROVATO rilevanti:** D-028/D-029 (3 HAL), D-040 (no router LLM unificato), D-061 (Knowledge RAG), D-075 (AI in-app inclusa, zero crediti agenzia), D-076/D-077 (ops costi stimati), D-119 (Legal CRM incluso), D-135 (improve stabile / timeout/fallback), D-128/D-136 (staging fal).

### 6.2 Diagnosi `llm_busy` (cause distinguibili — non “cambia modello”)

| Causa tipologica | Evidenza codice / collaudo | Note |
|------------------|----------------------------|------|
| **Provider** overload/quota Google (429/503/resource_exhausted) | `LlmBusy` in `shared/llm` | Dopo esaurimento catena modelli |
| **Orchestrazione** timeout per tentativo | `GEMINI_ATTEMPT_TIMEOUT_SEC` default 25s × N modelli | Può sommare latenza |
| **Applicativo** circuit breaker `llm` | soglia 5 fail, recovery 90s | Hold anche da kill-switch / dogfood |
| **Config** kill-switch / dogfood HOLD gemini/llm | `provider_flags`, perimeter dogfood | Può apparire come busy anche senza Google down |
| **Carico condiviso** stessa API key | HAL + Legal (2× Gemini: risposta+validator) + staging critic + safety + KYC + Scout | Contesa non misurata con semaforo globale |
| **Incoerenza mapping HTTP** | Agents/Legal → 503 `llm_busy`; Knowledge → 502 `generation_error` | Stessa classe di guasto, UX diversa |

**VERIFICATO in E2E:** risposte `llm_busy` / 502/503 su percorsi HAL.  
**NON VERIFICABILE qui:** quota esatta Google account, burst contemporanei in produzione, costi token reali.

### 6.3 Cosa manca (gap tecnici — PROPOSTA di diagnosi, non fix)

1. Semaforo / coda concorrenza globale LLM (priorità user-facing vs background critic).  
2. Retry policy esplicita e budget di retry (oggi fallback modelli + pause fissa).  
3. Normalizzazione errori Knowledge → stesso contratto `llm_busy`.  
4. Metriche token/latency/provider reali (non solo COGS stimato per evento).  
5. Suite eval ripetibile (golden questions HAL Agents/Knowledge/Legal).  
6. Degrado controllato UX quando AI down (D-075 già orienta “HAL non risponde” — da verificare a UI).  
7. Fallback cross-provider: **non** introdurre senza decisione privacy/costi (`APERTO`).  
8. Distinzione netta in log: `provider_error` | `model_error` | `orchestration_error` | `app_error`.

### 6.4 Funzioni AI essenziali vs accessorie (PROPOSTA di classificazione)

| Classe | Funzioni | Motivo |
|--------|----------|--------|
| **Essenziali** (affidabilità obbligatoria pre-GTM “gestionale evoluto”) | HAL Agents (assistenza operativa), HAL Knowledge (procedure), HAL Legal (con disclaimer e fonti) | Promessa prodotto + D-075 incluso |
| **Importanti** | HAL improve descrizioni, safety gate listing | Qualità listing / compliance |
| **Accessorie / a consumo** | Virtual staging fal, micro-video, Track B `/api/v1/legal/ask` a crediti | Possono degradare senza abbattere il gestionale core |

### 6.5 Proposta di architettura AI affidabile (PROPOSTA — non APPROVATO)

| Elemento | Proposta | Dipende da |
|----------|----------|------------|
| Provider primario | Gemini (già IMPLEMENTATO) | Conferma Founder su account/quota |
| Fallback | Solo modelli Gemini già in catena **finché** non c’è decisione privacy su secondo provider | `APERTO` |
| Timeout | Allineare default Agents/Knowledge/Legal; documentare budget totale utente | Diagnosi latenze |
| Retry | Max N, jitter, no retry su 400/policy | — |
| Concorrenza | Limite globale + code per classe (interactive vs batch) | — |
| Limiti cliente | Soft RL già 60/h Agents, 30/h Legal (IMPLEMENTATO); valutare limiti CC | D-075 |
| Budget token | Metering reale + alert Ops (estende D-076/D-077) | — |
| Degrado | Risposta deterministica “servizio AI temporaneamente non disponibile” + ticket ops | UI |
| Eval | Suite golden + gate di regressione qualità | — |
| Sicurezza | Isolamento tenant già vincolo prodotti; test prompt-injection / leakage | Area B |

### 6.6 Criteri di accettazione AI (autonomi — PROPOSTA)

Una funzione AI essenziale è accettabile solo se:

1. **Stabilità:** tasso di successo definito su N richieste golden in finestra T; `llm_busy` sotto soglia con cause classificate.  
2. **Concorrenza:** comportamento documentato a K richieste parallele (no storm di retry).  
3. **Indisponibilità provider:** degrado controllato senza 500 opachi e senza costi duplicati.  
4. **Qualità:** score minimo su eval (Legal: fonti/citazioni; Knowledge: insufficient_context quando corpus assente; Agents: no azioni CRM non autorizzate).  
5. **Sicurezza:** nessun leak cross-tenant in prompt/context.  
6. **Costi:** consumo tracciato per funzione; anomalie alertabili.  
7. **Osservabilità:** log con provider/model/latency/outcome **senza** payload sensibili in chiaro.

**Non** basta una demo “una volta ha risposto”.

---

## 7. Dipendenze tecniche e funzionali

```
A Fondamenta (A-007, errori, legacy)
    └─► H UI lista/demo affidabile
    └─► D/E collaudi non contaminati da 500 lista

B Org / CC / MA / permessi / fixture (A-003, A-008)
    ├─► D ciclo multi-filiale credibile
    ├─► E MLS collaborazioni
    └─► G wallet/allocate (anche con H4)

C LLM/HAL stabile
    ├─► F tool che usano Gemini (improve, safety, critic staging)
    └─► H percorsi “gestionale evoluto” in demo

D Ciclo gestionale (incl. Deal #240)
    └─► E visite/feedback/opportunità

F Documenti (watermark A-005, esign mock)
    └─► D/E chiusura trattativa documentale

G Billing (A-002) — gate H4 / sealed
    └─► GTM economico; non blocca L1 CRM se H4 resta chiuso

H UI/GTM
    └─► dipende da A+B+C+D stabili; A-004 da sbloccare con collaudo reale
```

**Non avviare in parallelo:** fix billing sealed + redesign AI fallback cross-provider + refactor permessi — richiedono decisioni Founder distinte.

---

## 8. Roadmap ordinata per priorità

Ordine raccomandato (allinea la tabella Founder; **PROPOSTA**):

| Ordine | Obiettivo | Perché | Output di fase (ancora READ-ONLY finché non autorizzato altro) |
|--------|-----------|--------|----------------------------------------------------------------|
| **1** | Diagnosi fondazioni e dati (Area A, focus A-007/A-006) | Evitare contaminazione test successivi | Specifica causa A-007 + piano fix + criteri accettazione lista |
| **2** | Diagnosi LLM/HAL (Area C) | Trasversale; reputazione “gestionale evoluto” | Report cause `llm_busy` classificate + architettura proposta + suite eval |
| **3** | Organizzazione e sicurezza (Area B) | Multi-agenzia e MA dipendono da qui | Gap decisioni APPROVATO vs implementazione; piano fixture C4 |
| **4** | Ciclo gestionale + MLS/Cloud (Aree D+E) | Cuore prodotto | Mappa stati/relazioni; gap vs decisioni visita/feedback/docs |
| **5** | Documenti e strumenti (Area F) | Servizi professionali | Matrice mock vs reale vs non testato |
| **6** | Billing e provider (Area G) | Credibilità commerciale | Mappa discrepanze; **nessun** checkout finché non autorizzato |
| **7** | UI e GTM (Area H) | Dimostrazione | Piano collaudo UI reale; script demo su flussi verdi |

All’interno di ogni ordine: prima **diagnosi READ-ONLY / design**, poi (solo con mandato separato) **implementazione**, poi **verifica**.

---

## 9. Milestone e criteri di completamento

### Milestone M0 — Programma (questa consegna)
- Deliverable: questo documento.  
- Criterio: Founder valuta e autorizza la **prossima** fase.

### Milestone M1 — Fondamenta affidabili (post-autorizzazione implementativa futura)
- A-007: lista immobili non 500 su legacy tipici; test page_size/sort.  
- Errori 500 ridotti sui percorsi CRM elenco; logging utile.  
- Criterio: E2E lista su dataset con record incompleti = 200 + item degradati o esclusi in modo documentato (dettaglio fix = mandato futuro).

### Milestone M2 — AI accettabile (piano accettazione autonomo)
- Cause `llm_busy` classificate con prove.  
- Contratto errore unificato; degrado UX.  
- Eval golden Agents/Knowledge/Legal sotto soglia.  
- Concorrenza documentata.  
- Criterio: vedi §6.6.

### Milestone M3 — Identità commerciale e permessi
- Fixture MA/agent coerenti (chiude A-003 in collaudo).  
- Gap D-185 / B01-B02 vs codice elenco chiuso o esplicitamente `APERTO` con decisione.  
- Isolamento tenant riconfermato.

### Milestone M4 — Ciclo immobiliare dimostrabile L2
- Percorso cliente→immobile→match→visita→Deal→docs senza buchi di stato.  
- A-001: deny esplicito post-revoca.

### Milestone M5 — Collaborazione e portale
- Regole APPROVATO su collab/visite/feedback rispettate e verificabili.  
- Ponte ImmobilCloud→CRM (già PARZIALE VERIFICATO) portato a dimostrazione UI.

### Milestone M6 — Tool professionali onesti
- Matrice mock/reale; esign non venduto come provider reale se mock.

### Milestone M7 — Billing TEST autorizzato
- Solo con mandato H4/sealed; ledger/CC post-acquisto.

### Milestone M8 — GTM credibile
- UI click sui percorsi M1–M5; script demo; no promesse su A-002/A-006/A-007 aperti.

**Regola trasversale di completamento (mandaato §6):** ogni attività futura deve portare: problema, evidenza, causa, impatto, soluzione proposta, moduli, dipendenze, rischio, test, accettazione, rollback. **200 ≠ fatto.**

---

## 10. Piano di verifica futuro (non eseguito ora)

| Fase | Tipo verifica | Mutativo? | Richiede autorizzazione |
|------|---------------|-----------|-------------------------|
| V0 | Review codice A-007 serializer + sample legacy READ | No scrittura prodotto | Già coperto da analisi; approfondimento ok in READ-ONLY |
| V1 | Suite unit/integration lista immobili con fixture incomplete | Sì (test env) | Mandato test |
| V2 | Diagnosi LLM: metriche, classificazione errori, load controllato | Possibile carico provider | Mandato AI + budget |
| V3 | Eval golden HAL (qualità/fonti) | Sì (chiamate Gemini) | Mandato AI |
| V4 | Fixture C4 repair design | No finché solo design | Poi mandato seed |
| V5 | Journey L2 ciclo+MLS+Deal su CLEAN fresco | Sì | Mandato E2E |
| V6 | H4 Stripe TEST | Sì | Mandato H4 esplicito |
| V7 | UI computer-use / manuale | Sì | Sblocco piattaforma / mandato UI |

**Vietato in questo mandato:** V1–V7 esecutivi mutativi.

---

## 11. Rischi residui

| Rischio | Area | Mitigazione di programma |
|---------|------|--------------------------|
| Lista immobili 500 in demo | A | M1 prima di demos commerciali |
| AI instabile percepita come prodotto immaturo | C | M2 con accettazione autonoma |
| Fixture sporche → falsi FAIL/PASS | B | Riparare seed prima di E2E larghi |
| H4 chiuso → narrativa GTM economica falsa | G | Non promettere; autorizzare TEST separato |
| Fallback AI non autorizzato → privacy/costi | C | Nessun secondo provider senza decisione |
| UI 0 click → overconfidence codice | H | Non certificare GTM su inventory |
| Parallelizzare troppi fix | tutte | Sequenza §8 |
| Riaprire decisioni APPROVATO | B/D/E/G | Solo con gap implementazione documentato |

---

## 12. Decisioni ancora necessarie al Founder (`APERTO`)

1. **Autorizzare M1 implementativo** su A-007 (e eventuale A-006) dopo lettura di una specifica tecnica dedicata?  
2. **Autorizzare programma AI M2** (diagnosi load + eventuale implementazione resilience) con budget Gemini dedicato e limiti di costo?  
3. **Secondo provider LLM** (privacy, contratti, fallback): sì/no/più tardi?  
4. **H4 sealed Stripe TEST**: quando e con quale perimetro (storage only vs crediti)?  
5. **Riparazione seed C4** (email/role/activation/MA) come mandato Dogfood separato?  
6. **Priorità staging fal generate** vs defer post-GTM core?  
7. **Soglie accettazione AI** quantitative (es. % successo, p95 latency) — conferma o modifica della proposta §6.6?  
8. **Firma checkpoint DEEP** `ffd1deb2-…` (ancora PENDING) — rilevante per catena Dogfood, non per GTM diretto.

---

## 13. Proposta di sequenza delle successive autorizzazioni

| Step | Mandato da emettere | Contenuto | Non include |
|------|---------------------|-----------|-------------|
| S0 | *(questo)* Pianificazione READ-ONLY | Programma | Fix |
| **S1** | Diagnosi tecnica A-007/A-006 READ-ONLY approfondita + bozza patch | Specifica + test plan | Merge senza review |
| **S2** | Implementazione fondamenta (A) | Fix lista/legacy/gateway se approvato | H4, AI redesign |
| **S3** | Diagnosi AI/HAL + piano accettazione (misure, no cambio provider) | Report cause + design | Secondo provider |
| **S4** | Implementazione resilience AI (se S3 ok) | Concorrenza, errori, metriche, eval | Fallback cross-vendor senza decisione |
| **S5** | Fixture/org/security (B) | Seed + gap permessi | Billing sealed |
| **S6** | E2E L2 ciclo+MLS+Deal su CLEAN | Verifica | LIVE payments |
| **S7** | Documenti/tool honesty pass (F) | Matrice + fix mirati | — |
| **S8** | H4 TEST (G) se deciso | Checkout+ledger | LIVE |
| **S9** | UI/GTM demo pack (H) | Click paths | Overclaim |

Ogni step richiede **testo di autorizzazione esplicito** del Founder. Nessuno di questi step è avviato da questo documento.

---

## Appendice A — Dettaglio Area A (Fondamenta)

**Analizzare (già in parte VERIFICATO):** A-007 KeyError `created_at` in list serializer; 500 vs page_size; legacy incompleti CONTINUITY; A-006 projection `is_active`; coerenza errori 404 Deal (A-001).  
**Risultato richiesto alla prossima autorizzazione:** elenco problemi reali con file/endpoint, impatto, priorità, patch proposal.  
**Non fare ora:** patch.

## Appendice B — Area B (CC / org / sicurezza)

**APPROVATO (esempi):** B01 modello CC/Org; B02 MA ≠ CRM filiali automatico; D-185 nomina MA obbligatoria; regole grace/cease.  
**PARZIALE / APERTO:** CC `pre_activation` blocca wallet (DEEP+INTEGRALE); A-003 fixture; A-008 drift role.  
**PROPOSTA:** gap matrix decisione↔codice prima di ogni E2E multi-ruolo.

## Appendice C — Area D (Ciclo gestionale)

Percorso target: acquisizione → incarico → immobile → docs → richieste → matching → visita → trattativa → Deal → conclusione.  
**VERIFICATO parziale:** create/match/Deal base post-#240.  
**Gap:** coerenza stati end-to-end, visite dedicate, A-001, UI.  
Obiettivo: gestionale immobiliare, non CRM generico.

## Appendice D — Area E (MLS / Cloud)

Rispettare regole APPROVATO su collaborazione, mandato, visite, feedback, docs (no auto-doc).  
**VERIFICATO:** nucleo MLS DEEP; collab/deal/docs INTEGRALE PARZIALE.  
ImmobilCloud ponte lead: PARZIALE VERIFICATO API.

## Appendice E — Area F (Documenti / tool)

| Tool | Stato etichetta | Nota |
|------|-----------------|------|
| Chat contestuale | PARZIALE VERIFICATO | Post-#240 |
| Watermark | PARZIALE; A-005 | Fail-closed OK |
| Fascicolo | PARZIALE | Analyze OK |
| Modulistica generate | PARZIALE | |
| E-sign | Mock IMPLEMENTATO | Non vendere come provider reale |
| Valutatore / mutui | PARZIALE API | |
| APE/OpenAPI.it | Ping OK; E2E no | |
| Staging fal | NON ESEGUITO generate | Distinto da LLM |

## Appendice F — Area G (Billing)

Gate: H4 sealed **ASSENTE** (DEEP+INTEGRALE) — `VERIFICATO`.  
Nessun checkout in questo programma finché non autorizzato.  
Mappa discrepanze: CC status, MA context, plans read vs subscribe, wallet allocate.

## Appendice G — Area H (UI / GTM)

1411 inventariati · 0 click (A-004).  
GTM = flussi dimostrabili (M1–M5), non conteggio pagine.  
Fonte: `E2E-GTM-VERIFICA.md`, `E2E-INTEGRALE-UI-COLLAUDO.md`.

---

## Fonti primarie (indice)

- `/opt/cursor/artifacts/RICONCILIAZIONE-PRIMO-E2E-VS-E2E-20-NOVEMBRE.md`  
- `/opt/cursor/artifacts/D175-E2E-DEEP-FINAL-REPORT.md`  
- `/opt/cursor/artifacts/E2E-INTEGRALE-ANOMALIE.md`  
- `/opt/cursor/artifacts/E2E-INTEGRALE-00-PREFLIGHT.md`  
- `/opt/cursor/artifacts/E2E-INTEGRALE-PREVIOUS-RECOVERY.json`  
- `/opt/cursor/artifacts/E2E-GTM-VERIFICA.md`  
- `/opt/cursor/artifacts/E2E-FOUNDER-GUIDA-COMPLETA.md` / `E2E-CONTROLLO-TECNICO-COMPLETO.md`  
- `memory/DECISIONS.md` (D-028…D-040, D-075…, D-135, D-185, B01/B02, D-190 PR#240)  
- Codice AI: `backend/shared/llm/`, `al_agent.py`, `hal_knowledge.py`, `al_legal/`, `circuit.py`

---

**STOP.**  
Nessuna modifica prodotto, nessun E2E nuovo, nessun H4, nessun commit/PR da questo mandato.  
Consegna al Founder per valutazione.  
**Questo documento NON autorizza l’implementazione.**

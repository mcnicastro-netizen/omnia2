# Capitolo 12 · HAL Knowledge — il RAG che risponde sul manuale OMNIA

> **Cosa trovi in questo capitolo**
> **HAL Knowledge** è il terzo assistente HAL di OMNIA (dopo HAL Agent CRM del Cap. 10 e HAL Legal in arrivo). È un motore di **RAG — Retrieval-Augmented Generation** che risponde a domande in linguaggio naturale sul funzionamento di OMNIA usando come base la documentazione ufficiale interna (PRD, ROADMAP, DECISIONS, Business Model) **e il Manuale Operativo Cap. 1-11** ora indicizzato come 129 voci atomiche. Ogni risposta cita le fonti utilizzate — se HAL non ha abbastanza contesto, te lo dice invece di inventare. Il capitolo copre: come porre una domanda, come leggere il badge di confidence, come funziona il motore (TF-IDF + Gemini 3 Flash Preview), il corpus indicizzato, lo storico, il reindex manuale (super_admin), i limiti onesti v1.

**Cosa NON è (D-051 onestà — regola cardine)**
- Non è **HAL Agent CRM**: non ha i 5 tool CRM (query_properties, query_clients, ecc.). Non legge il tuo database immobili/clienti — legge **solo la documentazione**.
- Non è **HAL Legal**: non risponde a domande giuridiche vincolanti. HAL Legal è un'altra applicazione ancora in arrivo (Cap. futuro).
- Non è **una chat multi-turno**: ogni domanda è **one-shot** (non ricorda le domande precedenti dentro la stessa sessione ai fini della risposta). Lo storico è solo per te, per ripescare rapidamente vecchie interrogazioni.
- Non fa **web search** né **scraping di siti esterni**. Il corpus è statico e curato.
- Non **traduce**: risponde nella stessa lingua della domanda (attualmente ottimizzato per italiano; funziona anche in inglese con qualità inferiore).
- Non **genera codice**, non **modifica dati**, non **esegue azioni** dentro il CRM. È in **sola lettura** sulla documentazione.

---

## 12.1 · Cos'è HAL Knowledge e dove lo trovi

**In una frase**
Un motore di Q&A sul manuale e sui documenti fondamentali di OMNIA (PRD, ROADMAP, DECISIONS, ecc.). Se non sai come funziona una parte del prodotto, chiedi a HAL Knowledge invece di leggere 300 pagine di manuale.

**Dove lo trovi**
Nella barra a sinistra di ImmoWeb, voce **HAL** → sotto-voce **Knowledge Base** (rotta `/it/app/hal/knowledge`). L'accesso è per tutti i ruoli utente autenticati: `titolare`, `agente`, `segreteria`, `branch_admin`, `group_admin`, `super_admin`.

**Chi può usarlo**
Tutti gli utenti agenzia autenticati. Non è accessibile lato B2C `/cloud` (non è un servizio per privati).

**Cosa vedi in pagina**
- Titolo *"Chiedi ad HAL"* con sottotitolo esplicativo.
- Badge di stato in alto a destra: numero chunk indicizzati, numero termini nel vocabolario TF-IDF, nome del modello LLM di generation.
- Un campo di testo per la tua domanda (max 1000 caratteri).
- 5 domande di esempio cliccabili per orientarti.
- La risposta (quando arriva) con badge di **confidence** e blocco **Fonti citate**.
- Storico delle tue ultime domande (max 15 righe, cliccabili per ripescare la risposta).

[SCREEN: cap12-halk-panoramica]

---

## 12.2 · Come porre una domanda

**A cosa serve capirlo**
Domande più mirate = risposte più precise. Il motore TF-IDF premia le parole-chiave che compaiono nel corpus del manuale.

**Passi operativi**
1. Apri la pagina *HAL → Knowledge Base*.
2. Scrivi la domanda nel campo di testo (max 1000 caratteri).
3. Preferisci frasi **naturali** (*"Come attivo Subito.it?"*) invece di keyword secche (*"attivazione subito"*).
4. Premi **Chiedi ad HAL** (o Enter senza Shift).
5. In pochi secondi (~2-5 sec) arriva la risposta con il badge di confidence e le fonti citate.

**Suggerimenti dalla forma della domanda**
- Domande sui **capitoli del manuale**: funzionano benissimo — le voci HAL sono ottimizzate per query naturali.
- Domande su **PRD/ROADMAP/DECISIONS**: funzionano se la domanda contiene keyword tecniche presenti nei documenti (es. *"Cosa è il D-051?"* → hit su DECISIONS).
- Domande **super generiche** (*"come funziona OMNIA"*): rispondono ma citando chunk generalisti da PRD/BUSINESS_MODEL.
- Domande **fuori scope** (meteo, ricette, notizie): HAL restituisce *insufficient_context* — non inventa.

**5 domande di esempio in pagina** (cliccabili per provare subito)
- *"Come pubblico un immobile su tutti i portali?"*
- *"Cos'è il Domain Vault e come funziona?"*
- *"Come faccio a configurare un canale social?"*
- *"Cosa può fare HAL Legal? Quali fonti usa?"*
- *"Cosa cambia tra Track A e Track B (Doppio Binario)?"*

**Limite lunghezza domanda**: **1000 caratteri** (`max_length=1000` nel Pydantic `KnowledgeAskRequest`). Sopra il limite l'invio viene rifiutato dal backend con `422 unprocessable_entity`.

**Limite minimo domanda**: **3 caratteri** (`min_length=3`). Sotto → `422`.

---

## 12.3 · Come leggere la risposta (badge di confidence + fonti citate)

**A cosa serve capirlo**
Il badge di confidence in alto a destra sulla risposta ti dice **quanto HAL si fida** della sua risposta. Non è una percentuale di accuratezza semantica — è la **similarità coseno TF-IDF** tra la tua domanda e i chunk più rilevanti nel corpus.

**I 3 stati del badge**

| Stato | Range similarity | Cosa significa | Colore |
|-------|------------------|----------------|:------:|
| **Alta confidence** | ≥ **0,20** (20%) | HAL ha trovato uno o più chunk molto pertinenti alla tua domanda. La risposta è affidabile. | 🟢 verde smeraldo |
| **Media confidence** | ≥ 0,08 e < 0,20 (8-20%) | HAL ha trovato chunk parzialmente pertinenti. La risposta può essere corretta ma la corrispondenza è debole — verifica le fonti. | 🟡 ambra |
| **Insufficiente** | < **0,08** (8%) | HAL rifiuta di rispondere. Ti restituisce il messaggio *"Non ho abbastanza contesto nel corpus OMNIA per rispondere"*. | 🔴 rosso |

**Perché queste soglie**
- `CONFIDENCE_MIN = 0.08` (`hal_knowledge.py:77`) è la soglia sotto cui HAL preferisce **rifiutare** invece di dare una risposta debole (D-051 · onestà).
- `CONFIDENCE_HIGH = 0.20` (`hal_knowledge.py:78`) segna il passaggio da *medium* a *high*.
- Valori TF-IDF italiani su documenti tecnici stanno tipicamente in range 0,10-0,45. Sopra 0,50 è raro.

**Il blocco "Fonti citate"**
Sotto la risposta trovi la lista delle fonti recuperate (max 5, `TOP_K=5` in `hal_knowledge.py:76`):
- **Nome file**: es. `07-fascicolo-immobile.yaml`, `PRD.md`, `ROADMAP.md`.
- **Sezione**: il modulo (per YAML) o il titolo della sezione H1/H2 (per MD).
- **Similarity %**: quanto il chunk è vicino alla tua domanda.

Nella prosa della risposta HAL cita le fonti con marker `[FONTE N]` alla fine delle frasi.

[SCREEN: cap12-halk-risposta-fonti]

**Cosa fare se la confidence è media**
1. Leggi le fonti citate: se sono coerenti con la domanda, la risposta è probabilmente buona.
2. Riformula la domanda con parole-chiave più specifiche (es. da *"pubblicazione"* a *"come attivo Subito.it"*).
3. Se il tema è nuovo o non ancora coperto nel manuale, HAL lo ammette.

---

## 12.4 · Cosa c'è nel corpus indicizzato

**A cosa serve capirlo**
Se sai cosa HAL può leggere, capisci **su cosa aspettarti risposte precise** e su cosa no.

**Documenti fondamentali OMNIA (interni, in `/app/memory/`)**
Elenco definito in `hal_knowledge.py:CORPUS_FILES` (linee 59-70):
- `PRD.md` — Product Requirements Document (prodotto in senso ampio).
- `ROADMAP.md` — Roadmap moduli e sprint (M1-M6).
- `DECISIONS.md` — Registro decisioni architetturali e di prodotto (D-001, D-037, D-051, D-061, ecc.).
- `AUDIT_M2.md` — Audit tecnico M2 (privacy, portali, moduli avanzati).
- `PROGRAMMA_OMNIA.md` — Programma esecutivo e milestone.
- `ASPETTI_DA_APPROFONDIRE.md` — Log dei temi ancora aperti (A-001, A-002, ..., A-005).
- `BUSINESS_MODEL.md` — Modello di business, pricing, target.

**Manuale Operativo — Cap. 1-11 (in `/app/memory/manuale/`)**
- I **file .md** di ogni capitolo (prosa lunga) sono chunkati per sezione con finestra di 500 parole e 50 di overlap.
- I **file .yaml** (`/app/memory/manuale/hal/*.yaml`) sono chunkati **1 voce = 1 chunk atomico**, con serializzazione strutturata `[TITOLO] [MODULO] [DOMANDA] [A COSA SERVE] [QUANDO SI USA] [PASSI] [ERRORI COMUNI] [PERMESSI] [TAGS]` (`hal_knowledge.py:_render_voce_hal` linee 168-203).
- **129 voci HAL** a Feb 2026 (Cap. 1-11).

**Cosa NON è nel corpus (D-051 esplicito)**
- ❌ **`CHANGELOG.md`** — escluso a Feb 2026 nel TASK B-ter (`hal_knowledge.py:67-70`). Motivo: il changelog cita query test come esempi, che creavano un **feedback loop TF-IDF** (il top-1 finiva sempre sul CHANGELOG anziché sulla voce del manuale). Commento inline nel codice conferma la scelta.
- ❌ Il tuo **database CRM** (immobili, clienti, lead): quello è HAL Agent CRM (Cap. 10), non HAL Knowledge.
- ❌ **Siti web esterni**, **Wikipedia**, **notizie**, **normativa aggiornata in tempo reale**: fuori scope.
- ❌ **Comunicazioni email/chat** interne, ticket di supporto, note operative: non indicizzati.

**Fingerprint di invalidazione**
Ogni file ha un MD5 salvato in `hal_knowledge_chunks.md5_source`. Al reindex idempotente (`force=False`), i file con MD5 invariato vengono **saltati**. Solo con `force=true` viene fatto un reingest completo.

---

## 12.5 · Come funziona il motore sotto il cofano (TF-IDF + Gemini)

**A cosa serve capirlo**
Se una risposta ti sembra strana, sapere **come è stata costruita** aiuta a interpretarla.

**Approccio D-061 · retrieval semplice + generation LLM**
1. **Chunking**: la documentazione viene spezzettata in "chunk" (pezzi di ~500 parole ciascuno per gli .md, oppure 1 voce YAML = 1 chunk per il manuale HAL). Ogni chunk ha un file, una sezione e un id univoco.
2. **Indicizzazione TF-IDF**: viene calcolata la matrice TF-IDF (term frequency × inverse document frequency) sul corpus, con:
   - **N-gram range**: unigrammi + bigrammi (`ngram_range=(1, 2)` in `_rebuild_tfidf_index`).
   - **Stopword italiane**: elenco compatto di ~90 parole comuni ("il", "la", "di", "con", ecc.) — `_ITALIAN_STOPS` a linea 340.
   - **`strip_accents="unicode"`** per matchare "città" e "citta".
   - Vocabolario: 3000-6000 termini circa (dipende da quanto è cresciuto il manuale).
3. **Retrieval (per ogni domanda)**:
   - La domanda viene vettorializzata con lo stesso vocabolario TF-IDF.
   - Si calcola la **cosine similarity** con ogni chunk del corpus.
   - Si tengono i **top-5** (`TOP_K=5`) più simili.
   - Se il migliore ha similarity **< 0,08** → `insufficient_context`.
4. **Generation (LLM)**: se ci sono chunk sufficienti, HAL costruisce un prompt strutturato con le fonti e chiede a **Gemini 3 Flash Preview** (`gemini-3-flash-preview` via Emergent LLM Key) di rispondere.
   - System prompt (`hal_knowledge.py:_build_prompt` linee 468-486): *"Rispondi ESCLUSIVAMENTE sulle fonti qui sotto. Se le fonti non contengono la risposta, di' onestamente 'Non ho abbastanza contesto'. NON inventare. Usa il formato [FONTE N] alla fine delle frasi. Risposta max 300 parole, italiano, tono professionale conciso."*
5. **Risposta**: la prosa generata viene mostrata all'utente insieme al badge di confidence e alla lista delle 5 fonti recuperate.

**Perché TF-IDF invece di embeddings neurali?**
Scelta D-061 (`hal_knowledge.py:11-14`):
- Corpus **piccolo** (~130 voci + 7 documenti fondamentali).
- Domande **italiane** su documenti **tecnici**.
- TF-IDF batte gli embeddings in **latenza** (nessuna chiamata API sulla query, tutto in-memory) senza degradare la qualità in questo dominio.
- **Zero costi ricorrenti** per la parte di retrieval (paghi solo la generation Gemini, ~30 token in + 300 token out ≈ frazione di centesimo per domanda).

**Persistenza indice**
La matrice TF-IDF è **serializzata in JSON** (D-051 H9 · no pickle per motivi di sicurezza — un DB compromesso non deve poter portare a RCE) e salvata in Mongo su `hal_knowledge_meta` (singleton). Alla prima query del processo viene caricata in una cache in-memory (`_CACHE` in `hal_knowledge.py:402`) e riusata finché non arriva un nuovo reindex.

---

## 12.6 · Storico delle domande e ricerca rapida

**A cosa serve**
Ripescare rapidamente una risposta che ti era già arrivata la settimana scorsa senza rifare la stessa domanda.

**Come funziona**
- Sotto il form di domanda, se hai già usato HAL Knowledge, trovi la sezione *"Domande recenti"*.
- Vengono mostrate le tue **ultime 8 domande** (la lista completa è fino a 15, `limit=15` nel fetch — `GET /api/app/hal/knowledge/history?limit=15`).
- Ogni riga mostra: domanda, badge di confidence piccolo, data/ora, numero di fonti citate.
- Clic su una riga → la domanda viene riportata nel campo di testo e la risposta viene riproposta (dallo storage locale, senza rigenerarla — nessun costo LLM aggiuntivo).

**Privacy dello storico**
- Ogni utente vede **solo le proprie domande** (filtro server-side `user_id: user.id`).
- **Eccezione**: il ruolo `super_admin` vede lo storico di **tutti gli utenti** (`hal_knowledge.py:614`). Motivo: audit e debug corpus/qualità.
- Nessuna cancellazione utente-side in v1 (non c'è bottone Elimina lato pagina). Non è ancora previsto un TTL automatico sulle sessioni salvate.

**Cosa viene salvato per ogni domanda** (collezione `hal_knowledge_sessions`)
- `id` (uuid), `session_id`, `user_id`, `agency_id`, `question`, `answer`, `sources`, `confidence`, `status`, `created_at`.
- Anche le richieste `insufficient_context` vengono loggate (con `answer=null`) — utile a te per ricordare che avevi già chiesto quella cosa, e utile al team OMNIA per capire quali aree del corpus vanno arricchite.

---

## 12.7 · Reindex del corpus (solo super_admin)

**A cosa serve**
Quando viene aggiunto un capitolo del manuale, o modificato un documento fondamentale, il super_admin deve **rigenerare l'indice TF-IDF** perché le nuove voci compaiano nelle risposte.

**Chi può fare reindex**
Solo il ruolo `super_admin` (`hal_knowledge.py:530-536` · `Depends(require_roles("super_admin"))`). Un `titolare` o `agente` che tenta la chiamata riceve `403 Forbidden`.

**Endpoint**
```
POST /api/app/hal/knowledge/reindex?force=false
POST /api/app/hal/knowledge/reindex?force=true
```

- **`force=false`** (default): reindex **idempotente**. I file con MD5 invariato vengono saltati (`skipped`). Solo i file cambiati o nuovi vengono riprocessati.
- **`force=true`**: forza il **reingest completo** di tutti i file. Utile quando cambia lo schema del chunker, la stopword list, o vuoi resettare la matrice.

**Cosa restituisce**
Un report JSON con:
- `scanned`: numero totale di file scannerizzati.
- `reingested`: lista `[{file, chunks}]` dei file re-indicizzati.
- `skipped`: lista dei file saltati perché invariati.
- `total_chunks`: chunk aggiunti/aggiornati in questo run.

**Costo del reindex**
- **Zero** (nessuna chiamata LLM). La matrice TF-IDF si rigenera **in-process** in pochi secondi (< 5 sec per il corpus attuale).
- Solo la **generation** (Q&A live) consuma Gemini via Emergent LLM Key.

**Endpoint di status per verificare l'esito**
```
GET /api/app/hal/knowledge/status
```
Restituisce:
- `chunks_indexed`: numero totale di chunk nell'indice.
- `manual_hal_indexed`: solo i chunk provenienti da file `.yaml` del manuale (proxy per capire se il manuale è indicizzato).
- `index.vocab_size`: dimensione del vocabolario TF-IDF.
- `model.name`: es. `gemini-3-flash-preview`.
- `corpus_files`: lista file fondamentali (`CORPUS_FILES`) — non include i .md del manuale (calcolati dinamicamente).

Sul badge in alto a destra della pagina UI vedi in sintesi *"📚 129 chunk · 4200 termini | 🤖 gemini-3-flash-preview"* (i numeri variano nel tempo).

[SCREEN: cap12-halk-status-badge]

---

## 12.8 · Insufficient context — quando HAL rifiuta di rispondere

**A cosa serve capirlo**
Se HAL ti risponde *"Non ho abbastanza contesto"*, **non è un bug**: è il comportamento voluto (D-051 onestà · zero invenzioni).

**Quando succede**
- La domanda è **fuori scope** (meteo, gossip, ricette). Il TF-IDF non trova chunk pertinenti.
- La domanda usa **keyword troppo generiche** (*"OMNIA"*, *"che roba è"*) o troppo specifiche mai comparse nel corpus.
- Il tema **non è ancora nel manuale** (esempio: capitoli 12-26 in scrittura, feature ancora in roadmap).
- Refusi ortografici gravi rendono la vettorializzazione TF-IDF inefficace (le stopword italiane sono limitate, nessun spell-check).

**Cosa vedi in pagina**
- Riquadro ambra con *"⚠️ Contesto insufficiente"* e il messaggio *"Non ho abbastanza contesto nel corpus OMNIA per rispondere a questa domanda. Puoi riformularla o contattare il team OMNIA."*
- Nessuna fonte citata.
- Similarity mostrata sotto (es. *"Similarity: 3,2% — sotto la soglia minima del 8%"*).

**Cosa fare**
1. Riformula usando parole-chiave che tipicamente compaiono nel manuale (es. *"Fascicolo"*, *"Match"*, *"Compliance HARD"*, *"Consap under-36"*, *"Watermark"*).
2. Se il tema è veramente coperto ma HAL non ti trova → segnala al team OMNIA (probabile miglioramento voce YAML o tag da aggiungere).
3. Se il tema è nuovo → aspetta il capitolo del manuale che lo copre, oppure chiedi a HAL Agent CRM (Cap. 10) se il tema è di natura CRM.

---

## 12.9 · Distinzione tra i tre HAL (Knowledge, Agent CRM, Legal)

**A cosa serve capirlo**
I tre HAL sono **3 endpoint AI distinti**, non un unico bot che smista. Sapere quale usare quando ti fa risparmiare tempo.

| HAL | Scope | Endpoint | Dati letti | Cap. manuale |
|-----|-------|----------|------------|:------------:|
| **HAL Agent CRM** | Consulenza operativa sul tuo CRM | `/api/app/al/chat` (streaming SSE) | Il TUO database (immobili, clienti, lead — solo tua agenzia) | Cap. 10 |
| **HAL Knowledge** | Q&A sul manuale e documenti OMNIA | `/api/app/hal/knowledge/ask` (one-shot) | Documentazione OMNIA (statica, curata) | Cap. 12 (questo) |
| **HAL Legal** | Domande giuridiche su compravendite (in arrivo) | *(non attivo v1)* | Corpus legale curato (in arrivo) | Cap. futuro |

**Regola pratica**
- *"Quali immobili ho attivi sotto 200k a Milano?"* → **HAL Agent CRM**.
- *"Come funziona la Compliance HARD sui portali?"* → **HAL Knowledge**.
- *"L'usucapione ventennale si applica a questo caso?"* → **HAL Legal** (non attivo v1, oggi ti consiglia il notaio).

**D-040 · 3 bottoni fisici, no router LLM**
La distinzione è **esplicita** in UI: 3 pagine separate nella sidebar, non un unico prompt che smista automaticamente. Motivo: chiarezza di responsabilità, no confusione utente.

---

## 12.10 · Limiti onesti v1

**Cosa HAL Knowledge NON fa (D-051)**
- ❌ Non risponde in **lingue diverse dall'italiano** con qualità comparabile (il corpus è quasi tutto in italiano, tranne alcuni titoli tecnici in inglese).
- ❌ Non usa un **modello di embedding neurale** (SBERT, OpenAI ada, ecc.) — usa TF-IDF classico. Va benissimo per il corpus attuale, potrebbe essere migliorato in futuro con embeddings quando il corpus supererà le 500 voci.
- ❌ Non ha **memoria** fra domande consecutive. Ogni domanda è isolata, non fa follow-up multi-turno. Se vuoi "affinare" una risposta, devi riformulare la domanda intera.
- ❌ Non ha un **feedback loop utente** ("questa risposta è utile? 👍 👎"). In v1 non c'è modo di segnalare inline che una risposta era sbagliata. Il super_admin vede lo storico e può correlare `insufficient_context` per capire dove il corpus va arricchito.
- ❌ Non è **multitenant a corpus**: tutti gli utenti agenzia hanno accesso allo stesso corpus documentale OMNIA (i tuoi dati agenzia non vengono indicizzati e non vengono mostrati ad altre agenzie — quello sarebbe **HAL Agent CRM** con isolamento by `agency_id`, cfr. Cap. 10).
- ❌ Non ha **rate limit dedicato** in v1 (a differenza di HAL Agent CRM che ha 60/h chat + 60/h improve). Le domande sono economiche (~2 sec + frazione di centesimo/domanda) e non sono state osservate abusi. Se in futuro serve, il pattern è già disponibile nel codice HAL Agent (`al_agent.py:_check_rate_limit`).

**Cosa può cambiare in futuro**
- Aggiunta di capitoli 12-26 al manuale → più voci nel corpus → risposte più precise su tutti i moduli.
- Passaggio da TF-IDF a embeddings neurali se il corpus supera le 500 voci (D-061 rivalutabile).
- Feedback loop utente (👍👎) per far emergere gap del corpus in modo strutturato.
- Multilingua (EN/ES) → richiede voci HAL YAML tradotte, non solo prompt in altra lingua.

---

## 12.11 · Errori comuni

| Problema | Cosa succede | Soluzione |
|----------|--------------|-----------|
| *"La risposta cita `07-fascicolo-immobile.yaml` ma non `07-fascicolo-immobile.md`"* | HAL a Feb 2026 preferisce chunk atomici YAML (1 voce = 1 chunk) rispetto ai chunk larghi .md. Non è un bug. | Le voci YAML sono la fonte più aggiornata e mirata. Se hai bisogno di più prosa, apri il file `.md` corrispondente da GitHub. |
| *"Ho fatto reindex ma il conteggio chunk non è cambiato"* | Reindex idempotente: se il MD5 del file è invariato, viene saltato. | Usa `force=true` per forzare il reingest completo. |
| *"Il badge dice 'Media confidence' su una domanda che credo copra il manuale"* | Similarity 0,08-0,20 → il chunk migliore non è super preciso ma HAL ha comunque provato. | Guarda le fonti: se sono coerenti, la risposta è probabilmente buona. Altrimenti riformula con keyword del capitolo (es. *"Compliance HARD"* invece di *"regole pubblicazione"*). |
| *"Chiedo qualcosa sui MIEI immobili e HAL non risponde"* | HAL Knowledge non legge il tuo DB CRM. | Usa **HAL Agent CRM** (Cap. 10, chat widget flottante in ImmoWeb). |
| *"Ricevo 429 o `agency_not_active`"* | Il tuo utente non ha ruolo agency e il token è scaduto. | Fai login → l'endpoint richiede ruolo `agent`, `titolare`, `segreteria`, `branch_admin`, `group_admin` o `super_admin`. |
| *"HAL mi cita `PRD.md` invece del capitolo di manuale"* | Il PRD contiene spesso definizioni sintetiche che vengono premiate dal TF-IDF quando la domanda è generica. | Riformula usando terminologia dal manuale (es. *"come attivo Subito.it?"* invece di *"pubblicazione"*). |

---

## 12.12 · Cosa fare adesso

**Se sei un titolare di agenzia**
1. Fai una prova su HAL Knowledge con **3 domande sul tuo flusso preferito** (es. Match, Fascicolo, Virtual Staging).
2. Verifica che citi le fonti coerenti con il capitolo del manuale.
3. Se una domanda ti torna `insufficient_context` e tu sai che il tema è coperto → segnala al team OMNIA con la stringa esatta della domanda.

**Se sei un super_admin**
1. Dopo ogni push del manuale, esegui `POST /api/app/hal/knowledge/reindex?force=true`.
2. Verifica `GET /status` che `chunks_indexed` sia cresciuto correttamente.
3. Rilancia le **smoke query** documentate per il capitolo appena inserito (vedi `IMPORT_HAL.md` sezione "Smoke Cap. N").

---

**Progressione manuale**: 12/26 capitoli (46%).
**Voci HAL totali**: **142** (Cap. 1-12, +13 nuove voci Cap. 12).
**Versione capitolo**: v1.0 (Feb 2026 · TASK I).

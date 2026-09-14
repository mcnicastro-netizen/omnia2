# Capitolo 7 · Fascicolo Immobile

> **Cosa trovi in questo capitolo**
> Il Fascicolo è la **vista unica** di un immobile in vendita: dati sintetici, **stima AI** con range, **checklist documentale rogito** con upload/download, **analisi HAL** dei documenti mancanti e i **render Virtual Staging** già prodotti. È il capitolo che chiude il cerchio di [Cap. 3 · Immobili](./03-immobili.md) — dove creavi la scheda — e prepara il passaggio al rogito.

**Cap. 3 vs Cap. 7 · dove sta il confine**

| Cap. 3 · Immobili | Cap. 7 · Fascicolo (questo capitolo) |
|---|---|
| Creare/importare l'immobile, gestire foto, privacy, stato annuncio | Portare l'immobile al rogito: documenti, valutazione, prontezza legale |
| §3.6 accennava alla checklist | Approfondisce checklist + analisi HAL + valutazione AI + download docs + regole condominio |

---

## 7.1 · Cos'è il Fascicolo Immobile

**In una frase**
Il Fascicolo è il "raccoglitore digitale" di ogni immobile: un solo posto dove hai **cosa vale**, **cosa hai**, **cosa manca** e **cosa dice HAL**.

**Cosa mostra la pagina Fascicolo**
1. **Hero immobile** — titolo, città/zona, tipologia, superficie, cover.
2. **Prezzo annuncio** — valore da scheda immobile.
3. **Stima AI (UNI 10750)** — valore medio + range min/max, quando disponibile.
4. **Badge di posizionamento** — *Sotto la stima*, *In linea con la stima*, *Sopra la stima* (verde/celeste/ambra).
5. **Checklist documentale rogito** — 10 tipologie documento (5 obbligatori + 5 facoltativi/condominio), con contatore progressione.
6. **Analisi HAL — prontezza al rogito** — report generato on-demand.
7. **Render Virtual Staging** — miniature degli ultimi render `done` (max 12), se presenti.

[SCREEN: cap7-fascicolo-panoramica]

**Come arrivi qui**
- Da **Immobili** → apri un immobile → link *Fascicolo* (in alto sulla scheda).
- URL diretto: `/it/app/properties/{id}/fascicolo`.

**Chi può aprirlo**
- **Titolare**: sempre.
- **Agente**: sempre (con visibilità coerente al livello privacy dell'immobile — vedi Cap. 3.4).
- **Segreteria**: come agente (utenti non hanno permessi di eliminazione).
- **Utente esterno / pubblico**: mai. Il Fascicolo è area interna.

---

## 7.2 · Stima AI (UNI 10750) e confronto col prezzo annuncio

**A cosa serve**
Capire in un colpo d'occhio se il **prezzo pubblicato** è coerente col mercato locale. La stima è calcolata dal motore valutatore ImmobilCloud (backend `apps/immocloud/valuator.py`) usando città, tipologia, superficie, condizione, classe energetica e piano.

**Cosa vedi**
- **Prezzo annuncio** — cifra secca (o "—" se non impostato).
- **Stima AI** — valore medio + banda `min — max` (banda ~±10-15% intorno alla media).
- **Badge**:
  - 🟢 *Sotto la stima AI* → prezzo annuncio inferiore al min della banda.
  - 🔵 *In linea con la stima AI* → prezzo annuncio dentro min-max.
  - 🟠 *Sopra la stima AI* → prezzo annuncio superiore al max della banda.

**Quando la stima non compare**
- Manca la **città** nella scheda immobile.
- Manca la **superficie in m²**.
- Il valutatore ha risposto con un errore transitorio (retry al prossimo refresh della pagina).

**Attenzione (D-051 onestà)**
- La stima è **indicativa**, basata su comparabili di zona (dataset UNI 10750 su ~124 città con fallback provinciale).
- Non sostituisce una **perizia estimativa** firmata da un tecnico o una **valutazione bancaria**.
- Per range di prezzo particolari (ville di pregio, cortina/portofino/lago, immobili da ristrutturare pesantemente) la banda può essere ampia: usala come benchmark, non come oracolo.

[SCREEN: cap7-fascicolo-stima-badge]

**Correlato**
- Confronto puntuale con immobili simili in vendita: dalla stima ImmobilCloud pubblica trovi il CTA *Confronta con immobili simili* (Cap. 3 §3.6).

---

## 7.3 · Checklist documentale rogito

**A cosa serve**
Avere sempre sott'occhio **cosa serve per andare a rogito** e **cosa hai già** caricato. La checklist si costruisce automaticamente dai `documents` collegati all'immobile.

**Le 10 righe della checklist**

| # | Documento | Obbligatorio | Condizione |
|:-:|-----------|:-:|-----------|
| 1 | APE — Attestato di Prestazione Energetica | ⚠ Sì | Sempre |
| 2 | Planimetria catastale | ⚠ Sì | Sempre |
| 3 | Visura catastale | ⚠ Sì | Sempre |
| 4 | Atto di provenienza (rogito / successione / donazione) | ⚠ Sì | Sempre |
| 5 | Documento d'identità del venditore | ⚠ Sì | Sempre |
| 6 | Conformità urbanistica / titoli edilizi | ⭘ Consigliato | Sempre |
| 7 | Certificato di agibilità | ⭘ Consigliato | Sempre |
| 8 | Visura ipotecaria | ⭘ Consigliato | Sempre |
| 9 | Regolamento di condominio | ⭘ Consigliato | Solo condominio |
| 10 | Attestazione spese condominiali | ⭘ Consigliato | Solo condominio |
| — | Altro documento (libero) | ⭘ | Sempre disponibile |

Le righe **9 e 10** compaiono solo se la **tipologia** dell'immobile è: `appartamento`, `attico`, `loft`, `monolocale` (verificato nel backend con `CONDO_TYPES` in `fascicolo.py`). Per villa/villetta/rustico/terreno la sezione condominio non appare.

**Stati riga**
- ✅ Verde — documento presente
- 🔴 Rosso — documento obbligatorio mancante
- ⚪ Grigio — documento facoltativo non caricato

**Contatore progressione**
In alto trovi una barra `N / M obbligatori` che diventa **verde** quando arrivi a 5/5 (o al totale di riferimento) e **ambra** finché è incompleta.

**Nota APE speciale**
Se nell'annuncio hai **dichiarato la classe energetica** (A4 → G) ma non hai ancora caricato il PDF, la riga APE mostra la nota:
> *Classe energetica X dichiarata nell'annuncio ma APE non caricato*

Per pubblicare in regola sui portali serve almeno la classe dichiarata; per il **rogito** serve il documento firmato dal tecnico (vedi §7.7 sotto).

[SCREEN: cap7-checklist-vista]

---

## 7.4 · Caricare, scaricare, eliminare un documento

**Formati e limiti**
- **Peso max**: 8 MB per file (`MAX_DOC_MB=8` nel backend).
- **Formati consigliati**: PDF (preferito), JPEG, PNG.
- **Storage**: i documenti finiscono su Object Storage cifrato (via `put_object`, path `omnia/fascicolo/{property_id}/{doc_id}`). Non vengono più salvati in base64 nel database.

**Caricare (passi)**
1. Sulla riga del documento, clicca il bottone **⬆ Carica**.
2. Scegli il file dal filesystem.
3. Attendi il caricamento (indicatore *"..."*).
4. La riga passa a ✅ e il documento compare col nome sotto.

**Scaricare (passi)**
1. Clicca sul nome del documento sotto la riga della checklist (`📎 nome.pdf`).
2. Il file viene scaricato nel browser col nome originale.

**Eliminare (passi)**
1. Clicca la ✕ rossa accanto al nome documento.
2. Il documento viene rimosso dal Fascicolo (l'operazione è **immediata**, senza cestino).

**Errori comuni**

| Messaggio | Perché succede | Cosa fare |
|-----------|----------------|-----------|
| *Max 8 MB* | File più pesante del limite | Riduci il PDF (scansione a 200 dpi invece che 600, o comprimi con iLovePDF/Smallpdf) |
| *Tipo documento non valido* | Chiave `doc_type` non prevista | Non capita da UI (il bottone imposta la chiave giusta). Se accade contatta HAL / assistenza |
| *storage_upload_failed* | Object Storage transitoriamente non disponibile | Riprova dopo qualche secondo. Se persiste, segnala |
| *Documento non trovato* (in download) | Il file è stato eliminato o l'ID URL è vecchio | Ricarica la pagina Fascicolo |
| *Documento non più disponibile* (410) | Il documento esiste a livello di riferimento ma il blob su storage è stato purgato | Ricarica il documento |

**Regola operativa**
Rinomina i file **prima** di caricarli con nomi parlanti: `APE-2025-firmato.pdf`, `visura-catastale-2025-06.pdf`, `atto-rogito-2018.pdf`. Il nome che carichi è quello che il tuo cliente/notaio vedrà al download.

[SCREEN: cap7-upload-flow]

---

## 7.5 · Analisi HAL — "prontezza al rogito"

**A cosa serve**
Ottenere in 5-10 secondi un **report scritto** che riassume:
1. Stato di prontezza al rogito.
2. Documenti obbligatori mancanti in ordine di priorità **con indicazione di dove/come ottenerli** (es. *"visura → Agenzia delle Entrate / SISTER"*, *"APE → tecnico certificatore"*).
3. Rischi da segnalare al cliente/notaio.

**Come lanciarla**
1. In fondo alla pagina Fascicolo, sezione *Analisi HAL — prontezza al rogito*, clicca **🤖 Analizza con HAL**.
2. Il bottone diventa *"HAL sta analizzando..."* per qualche secondo.
3. Al termine appare il report (max ~180 parole) con timestamp e sorgente.

**Come funziona sotto il cofano**
- Prima genera una **base rule-based** (elenca obbligatori mancanti e consigliati mancanti a partire dalla checklist).
- Se la chiave `EMERGENT_LLM_KEY` è configurata → chiama **Gemini 3 Flash** con il contesto immobile + checklist e produce un report in italiano naturale con emoji e bullet.
- Se il LLM fallisce (rete, budget, timeout) → si torna al **fallback rule-based** senza rompere il flusso.
- La sorgente è indicata in fondo al report: *"Analisi HAL (Gemini)"* oppure *"Analisi automatica"*.

**Cosa HAL NON fa**
- ❌ Non dà **consulenza legale vincolante** — per casi complessi (successioni con dubbi, servitù, contenziosi) rimanda a **notaio/avvocato**.
- ❌ Non inventa documenti presenti — se un obbligatorio manca, viene marcato mancante e messo in cima alle priorità.
- ❌ Non modifica il fascicolo — è **sola lettura**: riporta lo stato attuale.

**Quando conviene ri-lanciarla**
- Dopo ogni **caricamento** di documento obbligatorio (per aggiornare il quadro).
- Alla vigilia di un **appuntamento notarile** (come check-list finale).
- Su richiesta del **cliente venditore** che chiede un punto della situazione.

**Ultima analisi salvata**
Il backend salva l'ultima analisi sul documento immobile (`fascicolo_analysis`) — se torni sulla pagina dopo la vedi già lì con timestamp. Rilanciando *"Analizza con HAL"* sovrascrivi la precedente.

[SCREEN: cap7-analisi-hal]

---

## 7.6 · Valutazione AI integrata

**A cosa serve**
La stima commentata in §7.2 è **sempre attiva** in cima al Fascicolo, senza che tu debba lanciarla: viene calcolata al caricamento della pagina.

**Cosa passa al valutatore**
Il Fascicolo prende dalla scheda immobile:
- `city` (obbligatorio)
- `zone` (facoltativo, migliora accuratezza)
- `address` (facoltativo)
- `property_type` (default: `appartamento`)
- `surface_sqm` (obbligatorio)
- `condition` — mapping automatico: *ottime → ottimo*, *buone → buono*, ecc.
- `energy_class` — presa da `energy.energy_class` o dal top-level della scheda
- `floor` — piano, come intero

**Cosa restituisce**
- `estimated_value` — oggetto con `min`, `avg`, `max` (euro).
- `price_per_sqm` — €/m² medio della fascia.
- `confidence` — livello (alto/medio/basso) in base a quanti dati sono presenti e alla densità del dataset locale.
- `zone_tier` — fascia della zona (es. *centro storico*, *periferia*, *residenziale semi-centrale*).

**Cosa succede se il valutatore fallisce**
- Log warning lato server (`Fascicolo valuation failed for {property_id}: {errore}`).
- In UI vedi la card della stima con *"Servono città e superficie"* o vuota.
- La pagina resta comunque funzionante (checklist e HAL analysis vanno lo stesso).

**Approfondimento**
- Il motore completo con **Modalità Pro** (11 tipi di superficie UNI 10750, 6 select merit come piano/esposizione/affaccio/riscaldamento/ascensore/anno) è disponibile su **`/cloud/valutatore`** (B2C).
- Nel Fascicolo B2B usiamo la modalità **base**, sufficiente per il badge di coerenza prezzo.

---

## 7.7 · APE — cosa fa e non fa il Fascicolo

**Fatti onesti (D-051)**
- **OMNIA non calcola l'APE ufficiale**. L'attestato di prestazione energetica è per legge un documento **firmato da un tecnico abilitato ENEA** (geometra, architetto, ingegnere certificatore).
- **Non c'è un bottone "Ordina APE ufficiale" attivo** nel Fascicolo oggi. L'integrazione con un partner certificatore è **in valutazione** (fase 2).
- Quello che il Fascicolo fa oggi:
  1. Ospita il PDF firmato quando lo carichi come **APE**.
  2. Mostra la classe energetica dichiarata nell'annuncio se APE non ancora caricato (nota inline sulla riga).
  3. La classe energetica passa alla stima AI e alla Compliance HARD per la pubblicazione portali (Cap. 6).

**Cosa fare in pratica**
- Se il proprietario **ce l'ha già** → chiedi il PDF, verifica che sia in corso di validità (10 anni salvo interventi), caricalo come *APE*.
- Se il proprietario **non ce l'ha ancora** → indicagli un tecnico certificatore di fiducia o dell'agenzia (o consulta l'albo ENEA / gli ordini professionali locali). Costo di mercato tipico: €130-180 per un appartamento standard.
- **Nell'attesa**, dichiara comunque la classe energetica (anche stimata) nei dati dell'immobile: alcuni portali rifiutano annunci senza classe. Il documento firmato serve al **rogito**.

**Errori comuni**
- *"Ho caricato l'APE ma la Compliance dei portali continua a bloccare l'immobile"* → verifica che la classe energetica dichiarata nella scheda immobile **coincida** con quella scritta sull'APE. La Compliance controlla il campo `energy_class` della scheda, non legge il PDF.
- *"Il PDF dell'APE che ho ricevuto è enorme"* → è normale se il tecnico l'ha esportato ad alta risoluzione. Comprimi (iLovePDF/Smallpdf) o chiedigli il PDF ottimizzato.

---

## 7.8 · Documenti condominio (regolamento + spese)

**Quando compaiono**
Le due righe *Regolamento di condominio* e *Attestazione spese condominiali* appaiono nella checklist **solo** se la tipologia dell'immobile è:
- `appartamento`
- `attico`
- `loft`
- `monolocale`

(Verificato in `fascicolo.py:CONDO_TYPES`.)

**Come recuperarli**
- **Regolamento di condominio** — chiedilo all'**amministratore condominiale**. In alcuni condomini è depositato presso il notaio del rogito originario. Serve al notaio del rogito successivo per verificare eventuali destinazioni d'uso o divieti (uso ufficio, animali, B&B).
- **Attestazione spese condominiali** — l'amministratore prepara una **liberatoria** sui pagamenti degli ultimi 2 anni + un'indicazione degli **importi correnti**. È un tassello per il compratore che vuole capire il **peso mensile**.

**Perché sono "consigliati" e non "obbligatori"**
- Per il **rogito** puro la legge non li richiede sempre. Ma il notaio a rogito **li verifica** e la loro assenza può bloccare o rinviare la firma.
- La logica del Fascicolo è: **obbligatori** = quelli senza cui il notaio non firma (APE, planimetria, visura, atto, ID). **Consigliati** = quelli che eviti di rincorrere il giorno prima.

**Regole pratiche**
- Quando prendi il mandato, chiedi subito all'agenzia/proprietario il **contatto dell'amministratore**: fai partire la richiesta.
- **Attestazione spese**: alcuni amministratori la producono in 24h, altri in 2-3 settimane. Non aspettare l'ultimo momento.
- Se il condominio è **minimo** (2-4 unità senza amministratore) → puoi documentare la mancanza con dichiarazione sostitutiva e allegare gli ultimi ripartizioni firmati.

**Chi carica cosa**
- Titolare / agente responsabile: caricano tutto.
- Segreteria: può caricare/scaricare, ma non elimina (per policy operativa; l'endpoint DELETE lato backend non discrimina il ruolo — il vincolo è UI/procedurale).

---

## 7.9 · Render Virtual Staging visibili nel Fascicolo

**Cosa vedi**
Quando su questo immobile hai già lanciato render Virtual Staging (Cap. 13, quando sarà scritto — modulo `apps/immoweb/virtual_staging.py`), le miniature degli ultimi **12** render con `status: done` compaiono nella sezione *Render Virtual Staging* in fondo alla pagina.

Per ogni miniatura vedi:
- Immagine anteprima (`variant_url`).
- Stile + tipo stanza (es. *modern · living*).
- Simbolo 🔄 se è una render *reverse* (stanza prima svuotata e ri-arredata).

**A cosa serve nel Fascicolo**
- Rendersi conto se hai già arredato virtualmente le stanze principali prima del rogito / dell'open-house.
- Recuperare rapidamente i visuals da allegare a una **proposta di acquisto** o mail al cliente interessato.

**Cosa NON fa il Fascicolo su Staging**
- Non lancia nuovi render (usa la sezione **Virtual Staging** dalla barra a sinistra).
- Non permette di scaricare direttamente dal Fascicolo — clicca sulla miniatura e vai alla pagina Staging per il download watermarkato.

---

## 7.10 · Errori comuni (raccolta)

| Problema | Dove | Cosa fare |
|----------|------|-----------|
| La pagina Fascicolo dice *"Immobile non trovato"* | 404 | L'immobile è di un'altra agenzia o è stato eliminato. Torna a Immobili. |
| La checklist non mostra Regolamento condominio anche se dovrebbe | Riga condominio | Verifica la **tipologia** dell'immobile: solo appartamento/attico/loft/monolocale attivano quelle righe. Se è "villa" ma è in condominio → cambia tipologia in "appartamento" o usa "Altro documento". |
| Il pulsante **⬆ Carica** non risponde | Upload | Ricarica la pagina. Se persiste, verifica che il file sia < 8 MB e il browser non blocchi il picker file. |
| L'analisi HAL restituisce sempre la stessa risposta generica | Analizza | Probabilmente il LLM non è configurato in questo ambiente (fallback rule-based). Verifica con l'amministratore piattaforma. |
| Il badge stima è *"Sopra la stima AI"* ma il prezzo è concordato col cliente | Stima | Il badge è **indicativo**, non blocca nulla. Salva pure. Serve solo a te per farti una domanda in più. |
| Ho caricato un doc ma non lo vedo | Upload | Il documento è stato salvato: refresh della pagina. Se persiste, controlla la scheda documenti direttamente sull'immobile. |
| Vedo *"Documento non più disponibile"* al download | Download | Il blob è stato purgato dallo storage. Elimina il riferimento (✕) e ricarica il PDF. |

---

## Voci correlate (fuori capitolo)

- **Cap. 3 · Immobili** — creazione dell'immobile, foto, privacy, stato annuncio (il Fascicolo consuma questi dati)
- **Cap. 4 · Clienti** — collegamento cliente **venditore** (dati anagrafici, GDPR) — l'ID del venditore è quello che finisce nell'*Atto di provenienza*
- **Cap. 5 · Match** — quando l'immobile è nel Fascicolo con documenti a posto, la campagna Match verso i lead è pronta
- **Cap. 6 · Portali** — la Compliance HARD legge la stessa **classe energetica** che dichiari qui e i dati che pubblichi
- **Cap. 12 · HAL Knowledge** (quando scritto) — HAL Knowledge risponde su "come funziona il Fascicolo" col corpus manuale indicizzato

---

**Versione**: v1.0 · Feb 2026 (TASK D · Cap. 7 Fascicolo Immobile)

# Capitolo 5 · Match

**Versione manuale**: v1.0 · **Ultima revisione**: Feb 2026
**Chi lo legge**: titolari, agenti, segreteria
**Prerequisiti**: aver caricato almeno alcuni immobili (Cap. 3) e clienti con preferenze (Cap. 4)

Il modulo **Match** è il motore che risponde alla domanda "*a chi propongo questa casa?*" e "*quale casa consiglio a questo cliente?*" — automaticamente, a partire dagli immobili in portafoglio e dalle preferenze di ricerca dei clienti. Ci arrivi cliccando **Match** dalla barra a sinistra.

---

## 5.1 · Come funziona il matching (in 60 secondi)

**A cosa serve**
Confrontare ogni immobile del portafoglio con ogni cliente Acquirente/Affittuario/Investitore e generare un **punteggio 0-100** che dice quanto sono compatibili. Il punteggio alimenta:
- La lista **Match** con ranking automatico.
- Le **temperature** (Rovente / Caldo / Tiepido / Freddo) che vedi accanto ai clienti.
- Le priorità del bucket *"Da chiamare oggi"* (Cap. 4).

**Cosa NON è il matching**
- Non è una previsione: dice *compatibilità*, non *"comprerà"*.
- Non tiene conto (ancora) del comportamento sul sito, delle risposte email o dei clic sugli annunci.
- Non promette una vendita: fornisce **il miglior ordine di chiamata**, tu poi lavori il cliente.

**Come parte il calcolo**
- Automaticamente, in continuo: ogni volta che aggiungi/modifichi un immobile o un cliente, i match vengono ricalcolati.
- Se un cliente è **Venditore/Proprietario** (senza preferenze) → **non genera match automatici**. Il matching riguarda solo chi cerca.

[SCREEN: cap5-matches-lista]

**Chi vede la pagina Match**
- **Titolare · Agente · Segreteria** (come agente): tutti vedono la lista globale dei match dell'agenzia. Non c'è filtro per agente assegnato (vedi Cap. 4.6).

---

## 5.2 · La scala delle temperature (ROVENTE / CALDO / TIEPIDO / FREDDO)

Il punteggio 0-100 viene tradotto in **quattro fasce di temperatura**, ognuna con un'azione tipica.

| Temperatura | Range punti | Colore | Cosa fare |
|-------------|:-:|:-:|-----------|
| 🔥 **ROVENTE** | **85-100** | 🟥 rosso | **Chiama entro 24 ore**. Il cliente e l'immobile hanno un altissimo grado di compatibilità: prezzo dentro range, zona giusta, tipologia giusta, superficie compatibile. Se non risponde, tenta WhatsApp entro il giorno. |
| 🌶️ **CALDO** | **65-84** | 🟧 arancione | **Chiama questa settimana**. Buona compatibilità con qualche disallineamento leggero (es. prezzo poco sopra il budget, o zona limitrofa a quella preferita). Vale la telefonata. |
| ☀️ **TIEPIDO** | **40-64** | 🟨 ambra | **Menziona quando ne hai occasione**. Compatibilità parziale: potrebbe interessare ma richiede una vendita più consulenziale. Utile durante altre conversazioni. |
| ❄️ **FREDDO** | **< 40** | ⚪ grigio | **Salta, se non hai idee migliori**. La compatibilità è troppo bassa per giustificare una proposta specifica. Non è mai visualizzato di default (il filtro parte da 50+). |

[SCREEN: cap5-temperature-legenda]

**Perché queste soglie?**
Sono ricavate da un motore di scoring deterministico a 14 criteri (vedi 5.3). 85+ significa "quasi tutti i criteri principali sono soddisfatti"; sotto 40 significa "manca almeno uno dei tre criteri più pesanti (prezzo, operazione, città/tipologia)".

**Regola d'oro**: se un match è ROVENTE ma non converte in 30 giorni, aggiorna lo **Stato CRM** del cliente (Cap. 4). Un lead che non risponde non è realmente rovente.

---

## 5.3 · I 14 criteri di scoring (pesi)

Il punteggio totale è la somma di 14 sotto-punteggi, ognuno con un peso diverso. **Il totale fa esattamente 100**.

| Criterio | Peso | Cosa valuta |
|----------|:-:|-------------|
| **Prezzo** | 17 | Prezzo/canone dell'immobile rispetto al budget min-max del cliente. Bonus se è sotto max, penalità lineare se sopra |
| **Operazione** | 14 | Vendita vs Affitto vs Riscatto vs Asta. **Se non combacia → score complessivo cade a 0** (incompatibilità hard) |
| **Città** | 12 | Città dell'immobile deve essere in una delle città cercate |
| **Tipologia** | 11 | Appartamento, Villa, Attico, ecc. Se il cliente ha scelto una lista, l'immobile deve appartenere a una di quelle |
| **Superficie** | 7 | m² dell'immobile dentro il range preferito |
| **Caratteristiche imprescindibili** | 6 | Es. ascensore, giardino, balcone, box — voci compilate come "must have" nelle preferenze |
| **Zona / Quartiere** | 5 | Zona esatta o limitrofa alle preferenze |
| **Locali (vani)** | 5 | Numero vani totali dentro il range |
| **Camere da letto** | 4 | Camere ≥ minimo richiesto |
| **Bagni** | 4 | Bagni ≥ minimo richiesto |
| **Condizione** | 4 | Nuovo / Ottime / Buone / Ristrutturato ecc. — l'immobile deve essere nella lista accettata |
| **Classe energetica** | 4 | Classe ≥ soglia minima (A4 > A3 > A2 > A1 > A > B > … > G) |
| **Multimedia** | 4 | Foto presenti; virtual tour se richiesto |
| **Piano preferito** | 3 | Piano terra / intermedio / ultimo piano |
| **TOTALE** | **100** | |

[SCREEN: cap5-scoring-breakdown]

**Punti operativi**
- Se un criterio non è compilato nelle preferenze → conta come *indifferente* (piena assegnazione dei punti su quel criterio).
- **Prezzo (17)** e **Operazione (14)** insieme fanno il 31%: incompatibilità qui abbassano subito il punteggio.
- **Operazione errata** (compra una casa in vendita ma cliente cerca affitto) → score 0 secco. Non è mostrato.

---

## 5.4 · La pagina Match

**Cosa vedi entrando**
1. Titolo *"Match"* + sottotitolo.
2. In alto a destra un **selettore Score minimo** con 4 valori: `40+ tiepidi · 50+ buoni · 65+ caldi · 85+ roventi`. Il default è **50+**.
3. La lista dei match ordinata per **score decrescente** (i più forti in cima).
4. Ogni riga mostra: nome cliente, indirizzo/titolo immobile, prezzo, **badge temperatura** colorato, punteggio numerico.

**Uso quotidiano**

- Al mattino: apri Match, lascia il filtro **65+ caldi** o **85+ roventi** e chiama in ordine.
- Se pochi match: abbassa a **50+**.
- Se non c'è nulla: apri **Clienti** (Cap. 4) e completa le preferenze mancanti.

[SCREEN: cap5-lista-filtri]

**Cosa succede cliccando una riga**
Si apre il **Dettaglio Match** con:
- Anagrafica cliente e link alla scheda completa.
- Scheda immobile e link.
- **Breakdown**: come è composto il punteggio (quanti punti su ciascuno dei 14 criteri).
- **Cosa manca**: elenco leggibile dei mismatch (es. *"Prezzo sopra budget di €25.000"*, *"Zona non tra le preferite"*).

---

## 5.5 · Match visti da un immobile

**A cosa serve**
Rispondere alla domanda *"a chi propongo questo immobile?"*.

**Passi**
1. Vai in **Immobili** e apri l'immobile.
2. Trova la sezione **Match** (o clicca il pulsante *"Chi vuole questo immobile"*).
3. Vedi la lista dei clienti compatibili, ordinati per score.
4. Ogni cliente ha un badge temperatura e — se calcolato — un **Lead Score AI** (vedi 5.7).

**Regola operativa**
Con un nuovo mandato, la prima cosa da fare è aprire Match dell'immobile e chiamare **i primi 3-5 ROVENTI** che escono. Spesso l'annuncio non ha bisogno neanche di uscire sui portali.

---

## 5.6 · Match visti da un cliente

**A cosa serve**
Rispondere alla domanda *"quale casa consiglio a questo cliente?"*.

**Passi**
1. Vai in **Clienti** e apri il cliente Acquirente/Affittuario/Investitore.
2. Trova la sezione **Match / Immobili suggeriti**.
3. Vedi la lista degli immobili compatibili in ordine di score.
4. Clicca su un immobile per aprire la scheda.

**Nota**
Se il cliente ha zero match:
- Le sue preferenze sono troppo strette (Cap. 4.2 — allarga range).
- Il portafoglio è troppo piccolo o troppo specializzato per il suo profilo.
- Il cliente è di tipo **Venditore/Proprietario** — non genera match, è normale.

---

## 5.7 · Lead Scoring AI (approfondimento)

Il punteggio 0-100 dei 14 criteri è **deterministico**: puro calcolo, sempre uguale a parità di dati. Il **Lead Scoring AI** aggiunge un secondo strato di lettura, valutando:
- Coerenza fra preferenze e biografia del cliente.
- Qualità della compilazione (un cliente con preferenze dettagliate è più "serio").
- Storia dei contatti (stato CRM, numero di interazioni).

**Cosa produce**
Un punteggio AI e una temperatura (Rovente / Caldo / Tiepido / Freddo) **sulla scheda cliente**, non sul singolo match. Ecco perché in **Clienti** vedi *"Rovente"* accanto a un cliente anche prima di aprire un match specifico.

**Quando si aggiorna**
- Automaticamente ogni 24 ore per i clienti con match esistenti.
- Manualmente col bottone **"⚡ Aggiorna AI (N)"** in alto alla lista Clienti (Cap. 4.6). Utile dopo aver aggiunto molti immobili nuovi o dopo aver corretto le preferenze di un cliente.

**Costo**
Il ricalcolo AI consuma crediti Emergent LLM (Gemini). Un ricalcolo di ~50 clienti costa qualche centesimo. Nel dubbio, aggiorna solo quando ne vale la pena (nuovo portafoglio, nuove preferenze).

[SCREEN: cap5-lead-scoring-ai]

**Errori comuni**
- *"Ho aggiornato AI ma la temperatura non cambia"* → il ricalcolo è coerente: se la deterministic score è bassa, l'AI non la alza artificialmente.
- *"Un cliente Rovente non compra"* → aggiorna lo stato CRM. Il Lead Scoring AI legge lo stato: un cliente che dice ripetutamente "no" scende gradualmente.

---

## 5.8 · Filtri e ricerca sui match

**Filtro principale**: il selettore **Score minimo** in alto a destra della pagina Match.
- **40+ tiepidi** → mostra tutto il visibile
- **50+ buoni** → default consigliato
- **65+ caldi** → per giornate produttive
- **85+ roventi** → per il *power hour* del mattino

**Filtri combinabili** (dalle pagine collegate)
- Da **Immobili**: apri un immobile → vedi i match solo per lui.
- Da **Clienti**: apri un cliente → vedi i match solo per lui.
- Da **Clienti (bucket)**: filtro "Roventi" → poi apri il cliente → vedi i suoi match ordinati.

**Ordinamento**
La pagina Match è sempre ordinata per **score decrescente**. Non c'è ordinamento personalizzato al momento — il ranking automatico è la logica primaria.

---

## 5.9 · Workflow operativo consigliato (giornata tipo)

Un giorno lavorativo di 2 ore ben investite sul modulo Match:

| Momento | Attività | Cosa apri |
|---------|----------|-----------|
| **08:30-09:00** | Bevi caffè, guarda Dashboard | Dashboard |
| **09:00-09:30** | **Power hour ROVENTI**: apri Match con filtro **85+**, chiama i primi 5. Per ognuno: aggiorna Stato CRM subito (Contattato/Qualificato/…). | Match + Clienti |
| **09:30-10:15** | **Sessione CALDI (65+)**: 6-8 telefonate/WhatsApp. | Match + Clienti |
| **10:15-10:30** | Rispondi ai lead nuovi dai portali (bucket "Nuovi" in Clienti). | Clienti |
| **10:30-11:00** | **Nuovo mandato?** Apri immobile → tab Match → chiama i primi 3 clienti che escono. | Immobili → Match |

**Regola dell'80/20**
- 80% del tuo tempo produttivo va sui ROVENTI e CALDI.
- 20% sull'igiene del CRM: preferenze mancanti, stati vecchi, dati fiscali dimenticati.
- I FREDDI non li chiami quasi mai.

---

## 5.10 · Zero match — cosa fare

Situazione classica per agenzie nuove o piccole: apri Match e vedi *"Nessun match al momento"*.

**Checklist**
1. **Hai immobili in stato Pubblicato?** Se sono tutti in Bozza, non entrano nel matching. Cap. 3.5.
2. **Hai clienti con preferenze compilate?** Un cliente senza almeno *operazione + città + budget* non genera match. Cap. 4.2.
3. **Il filtro non è troppo alto?** Prova a scendere da 85+ a 40+.
4. **I clienti sono tutti Venditori?** I Venditori/Proprietari non generano match automatici. Servono Acquirenti/Affittuari/Investitori.
5. **Il portafoglio è coerente con la domanda?** Se hai solo ville da €500k e i clienti cercano bilocali a €150k, il match non arriva a 40.

**Suggerimenti dal sistema**
Nella pagina *"Nessun match"* trovi collegamenti diretti a **Immobili** e **Clienti** per completare quello che manca.

---

## 5.11 · Errori comuni (raccolta)

| Problema | Cosa fare |
|----------|-----------|
| Punteggio 0 secco | Operazione incompatibile (cliente cerca affitto, immobile in vendita). Controlla il campo Operazione. |
| Il cliente è ROVENTE ma non risponde | Aggiorna Stato CRM a *Contattato* dopo 3 tentativi falliti. Un lead che non risponde non è rovente. |
| Vedo lo stesso cliente su decine di immobili | Ha preferenze troppo larghe. Vale la pena affinare (budget più stretto, tipologia specifica) — vedi Cap. 4.2. |
| Un immobile ha zero match | Le preferenze dei clienti non collimano. Non è un bug: aggiungi clienti con quel profilo, oppure spingi l'annuncio sui portali. |
| Il match non aggiorna dopo aver cambiato prezzo | Il ricalcolo è immediato, ma la pagina Match cache l'ultima chiamata. Ricarica la pagina o naviga fuori e rientra. |
| Voglio disattivare temporaneamente il matching per un cliente | Metti il suo Stato CRM in *Archiviato*: continua a esistere ma non produce badge nei bucket. |
| I punti su un criterio sembrano bassi ma il cliente ci vive | Controlla il **Breakdown**: se la zona/quartiere è compilata male sull'immobile, la geo-matcha in modo penalizzato. Correggi *Zona* dall'immobile. |

---

## Voci correlate (fuori capitolo)

- **Cap. 2 · Dashboard** — contatore *Nuovi match (7gg)*
- **Cap. 3 · Immobili** — modifica dati che influenzano il match (prezzo, zona, condizione)
- **Cap. 4 · Clienti** — preferenze di ricerca + bucket Smart Sorting
- **Cap. 10 · HAL Agents** — chiedere a HAL *"chi devo chiamare per l'immobile X?"*

---

## Note per HAL

> Le voci di questo capitolo sono esportate come YAML operativo in
> `/app/memory/manuale/hal/05-match.yaml`.

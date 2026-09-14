# Capitolo 4 · Clienti

**Versione manuale**: v1.0 · **Ultima revisione**: Feb 2026
**Chi lo legge**: titolari, agenti, segreteria
**Prerequisiti**: aver fatto login (Cap. 1), avere almeno un immobile in portafoglio (Cap. 3) — non obbligatorio, ma consigliato per capire i Match

Il modulo **Clienti** raccoglie tutte le persone con cui la tua agenzia parla: chi vuole comprare, chi vuole vendere, chi vuole affittare e chi affitta. Ci arrivi cliccando **Clienti** dalla barra a sinistra.

---

## 4.1 · Creare un nuovo cliente (anagrafica)

**A cosa serve**
Registrare in ImmoWeb una persona: dati di contatto, tipo (acquirente / venditore / affittuario / proprietario / investitore), stato nel funnel commerciale, note interne.

**Quando si usa**
- Ogni nuovo lead che arriva (dal telefono, walk-in, email, portale, widget).
- Ogni proprietario che ti affida un mandato di vendita/locazione.
- Ogni investitore con cui costruisci una relazione lunga.

### 4.1.1 Passi per crearne uno

1. Dalla barra a sinistra clicca **Clienti**.
2. In alto a destra clicca **+ Nuovo cliente**.
3. Sezione **Anagrafica** — compila:
   - **Nome · Cognome** (obbligatori)
   - **Email** (fortemente consigliata — molte azioni automatiche partono da qui)
   - **Telefono · WhatsApp** (spesso è lo stesso numero, ma non sempre)
   - **Codice fiscale** (utile per contratti e proposte)
   - **Tipo cliente**: vedi 4.1.2
   - **Stato CRM**: vedi 4.1.3
   - **Origine** (es. *"Idealista"*, *"Passaparola"*, *"Walk-in"*, *"Sito agenzia"*)
4. Attiva la spunta **"Il cliente ha rilasciato consenso GDPR"** (obbligatorio prima di ricontattarlo commercialmente).
5. Sezione **Note interne** — aggiungi promemoria (es. *"preferisce essere chiamato dopo le 18"*).
6. Clicca **Salva cliente**.

[SCREEN: cap4-client-form-nuovo]

**Chi può farlo**
- **Titolare · Agente · Segreteria** (come agente): tutti possono creare clienti.
- Il cliente creato risulta assegnato all'utente che l'ha inserito.

### 4.1.2 I 5 tipi di cliente

| Tipo | Descrizione | Quando usarlo |
|------|-------------|---------------|
| **Acquirente** | Vuole comprare casa (prima casa, investimento, upgrade) | Il più comune. Compila anche le Preferenze di ricerca (4.2) |
| **Venditore** | Ha una casa da vendere e vuole affidarla a te | Compila **Anagrafica**. Poi collegalo a un immobile del portafoglio (4.5) |
| **Affittuario** | Cerca casa in affitto | Come Acquirente ma con operazione = *Affitto* nelle preferenze |
| **Proprietario (affitta)** | Ha un immobile da mettere in affitto | Come Venditore, ma per contratti di locazione |
| **Investitore** | Cerca opportunità (valore, rendita, riqualificazione) | Preferenze più ampie e flessibili — spesso segue mercato lungo periodo |

Il tipo si può **cambiare** in qualsiasi momento (es. un venditore che dopo l'incasso diventa acquirente per una nuova casa).

### 4.1.3 Gli stati del funnel CRM

Ogni cliente ha uno **stato** che riflette a che punto sei con lui:

| Stato | Cosa vuol dire |
|-------|---------------|
| **Nuovo** | Appena arrivato, non ancora chiamato |
| **Contattato** | Lo hai sentito almeno una volta, ma nessuna azione concreta |
| **Qualificato** | Ha budget reale, esigenze chiare, tempi definiti |
| **Trattativa** | C'è una proposta scritta / visita concordata / due diligence |
| **Chiuso (vinto)** | Rogito o contratto firmato con te |
| **Chiuso (perso)** | Ha comprato/affittato altrove o si è ritirato |
| **Archiviato** | Contatto vecchio, non attivo — resta nello storico |

Aggiorna sempre lo stato dopo ogni telefonata o mail. È la base della Dashboard e del filtro *"Lead aperti"*.

---

## 4.2 · Preferenze di ricerca

**A cosa serve**
Dire al sistema **cosa cerca** il cliente, così ImmoWeb potrà proporgli automaticamente gli immobili adatti (**Match**, Cap. 5).

**Quando si usa**
Subito, al primo colloquio, per i clienti **Acquirenti · Affittuari · Investitori**. Un cliente senza preferenze compilate non produce match automatici — è il singolo motivo più frequente per cui "il matching non funziona".

**I campi principali (in ordine di importanza)**

1. **Operazione cercata**: Vendita · Affitto · Affitto con riscatto · Asta · *Indifferente*.
2. **Tipologie d'immobile** (scelta multipla — es. *Appartamento + Attico*).
3. **Città** (una o più, separate da virgola).
4. **Zone / Quartieri** (una o più, es. *"Centro Storico, Trastevere"*).
5. **Prezzo min / max** (€) — il budget realistico. *Suggerimento*: metti un range, non un numero secco.
6. **Superficie min / max** (m²).
7. **Locali min / max** (vani totali).
8. **Camere min · Bagni min**.
9. **Stato dell'immobile** (Nuovo, Ottime, Buone, Da ristrutturare, Ristrutturato — scelta multipla).
10. **Piano preferito**: Piano terra · Piani intermedi · Ultimo piano.
11. **Classe energetica minima** (A4→G).
12. **Solo con foto · Solo con virtual tour** (checkbox).
13. **Caratteristiche imprescindibili** (es. *"ascensore obbligatorio se al 3° piano"*).
14. **Note di ricerca** (testo libero — orientamento, vincoli particolari).

[SCREEN: cap4-preferences-form]

**Chi può farlo**
- **Titolare · Agente · Segreteria** (come agente).

**Regola operativa**
Non riempire "a tutti i costi": campi vuoti = *indifferente*. Meglio 3 criteri chiari che 10 mediamente vaghi.

---

## 4.3 · Importare clienti da CSV (template)

**A cosa serve**
Caricare in blocco molti clienti da un file (Excel, Google Sheets) — utile alla prima migrazione dal vecchio gestionale o quando hai una lista di lead da una campagna.

**Passi**

1. Dalla lista Clienti, in alto a destra, clicca **⬆ Importa CSV**.
2. Assicurati di essere sulla scheda **📋 Template CSV**.
3. Clicca **⬇ Scarica template CSV**.
4. Apri il file con Excel o Google Sheets. Trovi tutte le colonne supportate: anagrafica + preferenze di ricerca + una riga di esempio.
5. Compila una riga per cliente (**il separatore è `;` punto e virgola** — compatibile con Excel/Numbers in italiano).
6. Salva come CSV.
7. Torna in ImmoWeb: **trascina** il file nel riquadro tratteggiato oppure cliccalo per sceglierlo.
8. Verifica la **preview delle prime 5 righe** e il conteggio totale.
9. Clicca **Importa N clienti**.
10. Al termine vedi *"N clienti su M importati con successo"* e, se ci sono errori, un accordion con **riga e causa**.

[SCREEN: cap4-import-csv-flow]

**Errori comuni**
- *"File CSV non valido"* → il file non è UTF-8 o hai usato virgola dove serve punto e virgola. Riesporta da Excel scegliendo *"CSV UTF-8"* con separatore `;`.
- *"Riga scartata"* → mancano campi obbligatori (nome, cognome). Apri il dettaglio.
- *"Email duplicata"* → il cliente esiste già. Aggiorna la scheda esistente invece di crearne una nuova.

**Chi può farlo**
- **Titolare · Agente · Segreteria** (come agente).

---

## 4.4 · Smart Import AI (qualsiasi file)

**A cosa serve**
Caricare un file "brutto" (Excel del vecchio CRM con colonne strane, export contatti Gmail/Outlook in vCard, file di testo con note libere) e lasciare che l'IA estragga i clienti al posto tuo. Non devi mappare le colonne: **HAL legge il file, capisce cosa c'è dentro e ti mostra un'anteprima da correggere**.

**Formati supportati**
- **.csv** (qualsiasi formato, anche con colonne non standard)
- **.xlsx** (Excel)
- **.vcf** (vCard — export contatti da Gmail, Outlook, iPhone)
- **.txt** (testo libero — note, elenchi)

**Limiti**
- Dimensione massima: **5 MB per file**
- Massimo **500 righe** per import
- Tempo tipico: 5-15 secondi (dipende dal numero di righe)

**Passi**

1. Dalla lista Clienti clicca **⬆ Importa CSV**.
2. Vai sulla scheda **⚡ Import AI**.
3. Trascina il file nel riquadro (o clicca per sceglierlo).
4. HAL legge il file (vedi *"L'IA sta leggendo: {nome file}"*).
5. Vedi l'anteprima dei clienti estratti con **confidenza** per riga.
6. **Rivedi e correggi**: puoi modificare i campi direttamente, o rimuovere righe sotto soglia.
7. Clicca **Importa**.
8. Al termine: *"N clienti su M importati · X righe saltate"*.

[SCREEN: cap4-smart-import-ai-preview]

**Quando usarlo (vs CSV template)**
- **File pulito e strutturato** → usa Template CSV (4.3), è più veloce.
- **File "brutto", export legacy, contatti Gmail/vCard, note libere** → usa Smart Import AI.

**Errori comuni**
- *"File troppo grande"* → dividilo in più file da 500 righe.
- *"Righe sotto soglia confidenza"* → l'IA non ha trovato dati abbastanza chiari. Puoi correggerle manualmente prima di confermare, oppure saltarle e reinserirle a mano.

**Chi può farlo**
- **Titolare · Agente · Segreteria** (come agente).

---

## 4.5 · Collegare un cliente venditore a un immobile

**A cosa serve**
Sapere sempre **chi è il proprietario** di un immobile in portafoglio. Il collegamento *property-seller* attiva:
- Nome e telefono del proprietario visibili al team (privacy L4, Cap. 3.4).
- Scheda cliente arricchita con **tutti gli immobili collegati** (utile per proprietari con più asset).
- Coerenza fra CRM e portale: se il venditore compila un form B2C, ritrovi tutto sotto il suo profilo.

**Quando si usa**
Ogni volta che acquisisci un mandato di vendita/locazione, subito dopo aver caricato l'immobile.

### 4.5.1 Collegare dal form immobile

1. Vai in **Immobili** e apri l'immobile (o crealo nuovo).
2. Trova il campo **Cliente venditore / proprietario (collega anagrafica)**.
3. Scrivi il nome nel riquadro *"Cerca un cliente venditore o proprietario…"*.
4. Se il cliente esiste, cliccalo e sarà collegato.
5. Se **non esiste ancora**: vedi il messaggio *"Nessun cliente venditore/proprietario trovato. Crealo prima nella sezione Clienti."* → apri Clienti in un'altra scheda, crealo di tipo **Venditore** (o Proprietario), torna qui e ripeti la ricerca.
6. Salva l'immobile.

### 4.5.2 Vedere immobili collegati a un cliente

1. Vai in **Clienti** e apri la scheda del cliente venditore.
2. Trovi una sezione **Immobili collegati** con l'elenco.
3. Clicca *"Apri scheda ↗"* per andare all'immobile.

### 4.5.3 Cambiare o rimuovere il collegamento

Nel form immobile, accanto al cliente collegato:
- **Cambia** → cerca un altro cliente venditore.
- **Rimuovi** → il collegamento viene disfatto (l'immobile resta in portafoglio, ma senza proprietario collegato).

[SCREEN: cap4-property-seller-link]

**Chi può farlo**
- **Titolare · Agente · Segreteria** (come agente).

---

## 4.6 · Smart Sorting e Lead Scoring (intro)

Dopo aver popolato Clienti e Immobili, ImmoWeb inizia a proporti chi chiamare **prima** grazie al **Lead Scoring AI** (dettaglio completo nel Cap. 5).

**Cosa vedi in Clienti**

- Sopra la lista trovi una banda con i **bucket** (filtri rapidi):

| Bucket | Cosa contiene |
|--------|---------------|
| **Tutti** | Tutti i clienti attivi |
| **Da chiamare oggi** | Clienti che oggi hanno la priorità (score alto + non contattati di recente) |
| **Roventi 🔥** | Massima priorità — chiamali subito |
| **Caldi 🌶️** | Alta priorità — questa settimana |
| **Tiepidi ☀️** | Media — quando puoi |
| **Freddi ❄️** | Bassa — nel dubbio salta |
| **Acquirenti** | Solo clienti di tipo *Acquirente/Investitore/Affittuario* con preferenze |
| **Venditori** | Solo clienti di tipo *Venditore/Proprietario/Investitore* — utile per gestire proprietari e chi affida mandati (indipendentemente da eventuali immobili collegati) |

- Ogni riga cliente mostra un **badge temperatura** (Rovente / Caldo / Tiepido / Freddo) e — se calcolato — il **numero di match** con immobili in portafoglio.

**Aggiornare il punteggio AI**

Il badge *"⚡ Aggiorna AI (N)"* in alto indica quanti clienti sono ancora senza punteggio. Cliccalo e HAL ricalcola tutti (5-15 secondi per pochi decine di clienti).

**Azioni rapide**

Passando il mouse su una riga cliente vedi due bottoni:
- **📞 Chiama** → apre l'app telefono (o Skype/WhatsApp desktop) con il numero precompilato.
- **💬 WhatsApp** → apre WhatsApp Web con un messaggio precompilato personalizzabile.

Se il cliente non ha numero, il bottone è disabilitato.

[SCREEN: cap4-smart-sorting-buckets]

**Continuano nel Capitolo 5**
- Come funziona **matematicamente** il matching (cosa fa "ROVENTE"?)
- Come leggere il badge Lead Score
- Cosa fare quando un match è rosso ma non si converte
- Configurazione ranking (per agenzie che vogliono più controllo)

**Chi vede cosa**
- **Titolare · Agente · Segreteria** (come agente): tutti vedono l'**intera anagrafica clienti dell'agenzia** — non c'è separazione per proprietario del contatto. Ogni collaboratore può cercare, aprire e modificare qualsiasi cliente.
- Il campo *"agente assegnato"* di ciascun cliente serve per statistiche interne, non per limitare la visibilità.
- Se in futuro serve una separazione "ogni agente vede solo i suoi clienti", va introdotta una nuova funzione — al momento non esiste.

---

## 4.7 · Modificare, archiviare, eliminare un cliente

### Modificare
1. Apri il cliente dalla lista.
2. Modifica i campi.
3. Clicca **Salva cliente**.

### Archiviare (consigliato)
Per non perdere lo storico:
1. Apri il cliente.
2. Cambia **Stato CRM** in *Archiviato*.
3. Salva.

Il cliente scompare dai bucket ma resta nello storico e nelle statistiche.

### Eliminare definitivamente
⚠️ Perdi anche le note e la storia dei contatti.

**Prima di eliminare**: se il cliente ha immobili collegati (proprietario/venditore) il sistema **blocca l'eliminazione** con un messaggio del tipo *"Impossibile eliminare: questo cliente ha N immobile/i in carico. Riassegna o elimina prima quegli immobili."*

Per procedere devi prima:
- **Riassegnare** ogni immobile a un altro cliente venditore/proprietario (Cap. 3.5), oppure
- **Rimuovere il collegamento** dall'immobile (in questo caso l'immobile resta senza proprietario collegato).

1. Apri il cliente.
2. In fondo alla scheda clicca **Elimina**.
3. Conferma.

**Chi può eliminare**
- **Solo titolare** (l'agente non può eliminare, per evitare cancellazioni accidentali).
- Segreteria (come agente): **non può eliminare**.

---

## Errori comuni (raccolta)

| Problema | Cosa fare |
|----------|-----------|
| Ho creato clienti ma la Dashboard mostra "Lead aperti" = 0 | I clienti risultano *Nuovo* o *Contattato* per contare. Controlla gli stati. |
| Il matching non produce nulla | Verifica che i clienti Acquirenti abbiano le **Preferenze di ricerca** compilate (almeno operazione, città, budget). |
| Non riesco a collegare un venditore all'immobile | Il cliente deve esistere e essere di tipo **Venditore** o **Proprietario (affitta)**. Se è un Acquirente, cambia prima il tipo. |
| Ho importato 200 clienti ma ne vedo 180 | 20 righe sono state scartate: apri l'accordion errori nell'import per capire perché (email duplicate, campi obbligatori mancanti). |
| Voglio contattare tutti i "Roventi" via WhatsApp | Passa da un cliente all'altro con il pulsante **💬 WhatsApp** — non c'è ancora invio massivo (in arrivo). |
| Ho perso il consenso GDPR | Senza spunta GDPR non puoi ricontattare commercialmente. Serve un nuovo consenso esplicito (email o modulo cartaceo firmato). |

---

## Voci correlate (fuori capitolo)

- **Cap. 2 · Dashboard** — contatore *"Lead aperti"*
- **Cap. 3 · Immobili** — collegare cliente venditore all'immobile
- **Cap. 5 · Match** — Lead Scoring dettagliato + azioni sui match
- **Cap. 10 · HAL Agents** — chiedere a HAL *"chi devo chiamare oggi?"*

---

## Note per HAL

> Le voci di questo capitolo sono esportate come YAML operativo in
> `/app/memory/manuale/hal/04-clienti.yaml`.

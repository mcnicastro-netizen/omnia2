# Capitolo 3 · Immobili

**Versione manuale**: v1.0 · **Ultima revisione**: Feb 2026
**Chi lo legge**: titolari, agenti, segreteria
**Prerequisiti**: aver fatto login (Cap. 1), essere assegnati a un'agenzia attiva

Il modulo **Immobili** è il cuore operativo di ImmoWeb: qui vive il tuo portafoglio.
Ci arrivi cliccando **Immobili** dalla barra a sinistra oppure da un contatore della Dashboard.

---

## 3.1 · Creare un immobile a mano

**A cosa serve**
Aggiungere in ImmoWeb un immobile che vuoi vendere o affittare — poi lo pubblicherai sul sito, sui portali e lo proporrai ai clienti compatibili tramite il modulo **Match**.

**Quando si usa**
Ogni volta che acquisisci un nuovo mandato o inserisci un immobile appena affidato. Se hai già molti immobili in un altro gestionale, salta al paragrafo 3.2 (Import).

**Passi**

1. Dalla barra a sinistra clicca **Immobili**.
2. In alto a destra clicca **+ Nuovo immobile**.
3. Compila i campi principali (obbligatori):
   - **Titolo annuncio** (es. *"Trilocale luminoso zona centro"*)
   - **Tipologia** (Appartamento, Villa, Villetta a schiera, Loft, Attico, Monolocale, Rustico, Ufficio, Negozio, Magazzino, Capannone, Garage/Box, Terreno agricolo, Terreno edificabile, Palazzo, Altro)
   - **Operazione**: Vendita · Affitto · Affitto con riscatto · Asta
   - **Indirizzo · Città · Provincia · CAP**
   - **Prezzo (€)** oppure **Canone mensile (€)** a seconda dell'operazione
   - **Superficie (m²)**
4. Compila i campi opzionali quando li conosci:
   - **Descrizione** (puoi migliorarla con HAL — vedi *Migliora con HAL* nel Cap. 10)
   - **Codice di riferimento** (utile per non duplicare)
   - **Zona / Quartiere** (compare in mappa e cerca)
   - **Vani · Camere · Bagni · Piano · Piani totali · Anno**
   - **Condizione**: Nuovo · Ottime · Buone · Da ristrutturare · Ristrutturato
   - **Classe energetica** (A4→G) + **consumo** kWh/m²·anno
   - **Spese condominiali · Arredamento · Riscaldamento**
   - **Cliente venditore** (collega l'anagrafica del proprietario dal modulo Clienti)
5. Aggiungi almeno 3 fotografie (vedi 3.3).
6. Scegli il **livello di privacy** (vedi 3.4). Di default è **L2** (visibile agli utenti loggati del portale).
7. Clicca **Salva immobile**.

[SCREEN: cap3-property-form-nuovo]

**Chi può farlo**
- **Titolare**: sempre.
- **Agente**: sempre (l'immobile risulta assegnato a lui come *listing agent*).
- **Segreteria**: si logga come agente. Può creare se il titolare non gli ha rimosso il permesso.

---

## 3.2 · Importare immobili da file (CSV o XML)

Sono disponibili **due percorsi**:

- **Import CSV/XML "veloce"** dalla pagina Immobili → utile per caricare batch piccoli/medi con template guidato.
- **Import XML "universale"** dedicato → utile quando arrivi da un altro gestionale e vuoi analizzare il file prima di importare.

### 3.2.1 Import veloce CSV

**Passi**

1. Clicca **Immobili → ↓ Importa** (in alto a destra).
2. Nella scheda **📋 Template CSV** clicca **Scarica template** e apri il file con Excel o Google Sheets.
3. Compila una riga per ogni immobile (le colonne obbligatorie sono già evidenziate).
4. Salva il file in formato **CSV** (UTF-8).
5. Torna in ImmoWeb: **trascina** il file nel riquadro tratteggiato oppure cliccalo per scegliere dal disco.
6. Verifica la **preview delle prime 5 righe** e il numero totale che stai per importare.
7. Clicca **Importa**.
8. A fine importazione vedi *"Importati X immobili"* e — se ci sono errori — un elenco a discesa con la riga e la causa.

[SCREEN: cap3-import-csv-flow]

**Errori comuni CSV**
- *"File CSV non valido"* → il file non è UTF-8 o ha caratteri strani. Riesporta da Excel scegliendo *"CSV UTF-8 (separatore virgola)"*.
- *"Prezzo vuoto"* → almeno uno tra prezzo (per Vendita) e canone (per Affitto) è obbligatorio.
- *"Riga scartata"* → mancano colonne obbligatorie. Guarda il dettaglio nell'accordion *"⚠ N errori"*.

### 3.2.2 Import XML veloce (dalla stessa pagina)

Adatto se hai già un feed XML del vecchio gestionale o vuoi incollare un XML esportato.

**Passi**
1. Clicca **Immobili → ↓ Importa** e vai sulla scheda **XML**.
2. Scegli la modalità:
   - **Da URL**: incolla l'indirizzo di un feed pubblico.
   - **Incolla contenuto**: incolla direttamente il testo XML.
3. Clicca **Importa**.
4. Confermi e vedi il risultato.

### 3.2.3 Import XML "universale" (menu Importa)

Un percorso dedicato per grosse migrazioni, con **due fasi** (analisi + conferma).

**Passi**
1. Dalla barra a sinistra clicca **Importa** (visibile solo al titolare).
2. Trascina il file `.xml` (max 50 MB) o cliccalo per sceglierlo.
3. Clicca **Analizza contenuto**.
4. Rivedi il report di analisi:
   - Numero totale di immobili trovati
   - Ripartizione **per tipologia · per contratto · per città**
   - Divergenze rilevate (es. campi non standard)
   - Warning: *"immobili senza foto"*, *"immobili senza prezzo"*
   - Anteprima primi 5 immobili
5. Attiva **Salta immobili già presenti** (consigliato: usa il codice di riferimento per non duplicare).
6. Opzionale: **Simulazione** — vedi cosa succederebbe senza scrivere nulla.
7. Clicca **Importa in OMNIA**.

[SCREEN: cap3-xml-import-preview]

**Errori comuni XML**
- *"Il file deve avere estensione .xml"* → sbagli formato. Rinomina o riesporta.
- *"File troppo grande (max 50 MB)"* → dividi il feed. Molti gestionali permettono export per zona/agente.
- *"Divergenze rilevate"* nel report → alcuni campi non sono standard. Non è bloccante: vedi cosa manca e completerai dopo, oppure chiedi al fornitore XML uno schema standard (OSF).

**Chi può farlo**
- **Import CSV/XML veloce**: titolare + agente + segreteria (come agente).
- **Import XML universale** (`/app/import`): **solo titolare**.

---

## 3.3 · Fotografie e ordinamento

**A cosa serve**
Le foto sono il primo motivo per cui un cliente clicca (o scarta) un annuncio. La **prima foto** compare come copertina in tutti i portali e sul portale ImmobilCloud.

**Formati e limiti**
- Formati accettati: **JPEG · PNG · WEBP**.
- Peso massimo per foto: **8 MB**.
- Non c'è un numero massimo, ma i portali richiedono in genere **minimo 5-8 foto**.

**Passi (nuova foto)**
1. Apri l'immobile (Immobili → clicca sulla riga).
2. Scorri fino alla sezione **Fotografie**.
3. **Trascina** le foto nel riquadro o clicca per scegliere dal disco.
4. Aspetta il caricamento (barra di avanzamento).
5. Le foto appaiono in ordine di caricamento.

**Impostare la foto di copertina**
1. Passa il mouse sulla foto scelta.
2. Clicca **⭐ Copertina** (o simile).
3. Dalla lista degli immobili quella foto compare per prima.

**Ordinamento**
Trascina le miniature per riordinarle. Il nuovo ordine viene salvato subito.

**Eliminare una foto**
Passa il mouse e clicca l'icona ✕ (cestino). L'operazione è **immediata**: assicurati di non aver bisogno del file altrove.

[SCREEN: cap3-photos-dropzone-cover]

**Errori comuni**
- *"Formato non supportato"* → converti in JPEG/PNG/WEBP. Se hai HEIC (foto da iPhone) apri con l'app Foto ed **esporta** come JPEG.
- *"File troppo grande"* → riduci con Foto (Mac/Windows) o con un servizio come TinyPNG.
- *"Caricamento lento"* → foto pesanti e connessione lenta. Preferisci JPEG intorno a 1-2 MB per foto (qualità ottima, peso contenuto).

**Chi può farlo**
- **Titolare · Agente · Segreteria** (come agente): tutti possono caricare, ordinare, eliminare foto degli immobili a cui hanno accesso.

---

## 3.4 · Privacy 4 livelli (chi vede cosa)

Ogni immobile ha un **livello di privacy** (L1 → L4) che decide **cosa mostra** al mondo esterno.
Non decide solo se è pubblico: decide **quali campi** sono visibili a chi.

### La matrice (spiegata semplice)

|  | **L1 · Anonimo** | **L2 · Registrato** | **L3 · Lead qualificato** | **L4 · Agenzia** |
|---|:-:|:-:|:-:|:-:|
| Chi è | Chiunque visiti il portale senza login | Chi ha creato un account su ImmobilCloud | Chi ha lasciato un lead + confermato email (GDPR ok) | Solo tu e il tuo team di agenzia |
| Titolo + descrizione | ✅ | ✅ | ✅ | ✅ |
| Foto | ✅ (ridotte) | ✅ | ✅ | ✅ |
| Città + quartiere | ✅ | ✅ | ✅ | ✅ |
| Prezzo | ✅ arrotondato | ✅ esatto | ✅ esatto | ✅ esatto |
| Superficie, vani | ✅ | ✅ | ✅ | ✅ |
| Indirizzo esatto (via + civico) | ❌ | ❌ | ✅ | ✅ |
| Coordinate mappa | ❌ approssimative | ❌ approssimative | ✅ esatte | ✅ esatte |
| CAP + piano | ❌ | ✅ CAP | ✅ | ✅ |
| Planimetria | ❌ | ❌ | ✅ | ✅ |
| Nome + telefono proprietario | ❌ | ❌ | ❌ | ✅ |
| Note interne, commissioni | ❌ | ❌ | ❌ | ✅ |
| Classe energetica | ✅ (solo lettera) | ✅ (solo lettera) | ✅ dettagli | ✅ dettagli |

### Il "livello immobile" ristringe ancora di più

Il livello che imposti sull'immobile è una **soglia minima**: dice *"per essere visibile serve almeno questa qualifica"*.

- **Immobile L1** → visibile a tutti (anche anonimi). L'ideale per l'85% degli annunci pubblici.
- **Immobile L2** → visibile solo a utenti registrati sul portale. Piccolo filtro anti-curiosi.
- **Immobile L3** → visibile solo a chi ha lasciato un lead qualificato con email verificata. Perfetto per esclusive semi-riservate.
- **Immobile L4** → visibile **solo dentro l'agenzia** (tu e il tuo team). Non compare sui portali, né sul sito, né su ImmobilCloud.

### Scegliere il livello giusto

**Passi**
1. Apri l'immobile.
2. Scorri fino a **Privacy** (all'inizio o in fondo alla scheda a seconda della vista).
3. Scegli **L1 · Pubblico**, **L2 · Registrati**, **L3 · Lead qualificati** o **L4 · Solo agenzia**.
4. Aggiungi facoltativamente una **motivazione** (utile per il registro modifiche).
5. Clicca **Salva**.

**Casi tipici**
- Vendita standard → **L1**.
- Esclusiva con richiesta di riservatezza → **L2** o **L3**.
- Immobile riservato (villa di persona nota, azienda in vendita) → **L4** (viene visto solo dagli agenti dell'agenzia).

### Nascondere solo l'indirizzo (senza toccare la privacy)

Anche a livello L1 puoi decidere di **non mostrare l'indirizzo esatto**:
1. Apri l'immobile.
2. Attiva **Nascondi indirizzo esatto pubblicamente**.
3. Salva.

Sul portale comparirà solo *"Zona / Quartiere"* invece della via.

[SCREEN: cap3-privacy-selector]

**Chi può farlo**
- **Titolare · Agente**: possono cambiare la privacy degli immobili a cui hanno accesso.
- **Segreteria** (come agente): può cambiare privacy se il titolare non ha ristretto il permesso.
- Ogni modifica lascia un **registro** (chi, quando, motivo se fornito) — utile per gli audit.

---

## 3.5 · Modificare stato, mettere in bozza, archiviare

Ogni immobile ha uno **stato del ciclo di vita**:

| Stato | Cosa significa | Compare nei portali? |
|-------|----------------|:-:|
| **Bozza** | Ancora in preparazione | ❌ |
| **Pubblicato** | Live sui portali e sul portale ImmobilCloud | ✅ |
| **Prenotato** | Proposta accettata, in attesa di rogito | ✅ (marcato) |
| **Venduto** | Rogito fatto | ❌ (archiviato) |
| **Affittato** | Contratto firmato | ❌ (archiviato) |
| **Ritirato** | Mandato revocato / immobile tolto dal mercato | ❌ |

### Passare da bozza a pubblicato

1. Apri l'immobile.
2. Verifica che i campi obbligatori (titolo, tipologia, indirizzo, prezzo, foto) siano compilati.
3. Cambia **Stato** da *Bozza* a *Pubblicato*.
4. Salva.

Se il flag **"Pubblica su ImmobilCloud"** è attivo (default), l'immobile compare anche sul portale nazionale. Puoi disattivarlo se è una trattativa che vuoi tenere solo sul tuo sito agenzia.

### Cambiare stato durante il ciclo

- Proposta accettata → *Prenotato*.
- Rogito firmato → *Venduto* (o *Affittato*).
- Mandato revocato → *Ritirato*.

L'immobile non viene mai eliminato: resta nello storico. Se serve **eliminarlo definitivamente**, vedi sotto.

### Eliminare un immobile (definitivo)

**Passi**
1. Apri l'immobile.
2. In fondo clicca **Elimina**.
3. Conferma la richiesta *"Sei sicuro? L'operazione è definitiva."*

⚠️ **L'operazione non è reversibile.** Perdi anche foto, documenti e storia contatti collegati.

[SCREEN: cap3-state-select]

**Chi può farlo**
- **Cambio di stato**: titolare, agente, segreteria (come agente).
- **Eliminazione**: **solo titolare** (l'agente non può eliminare, per evitare cancellazioni accidentali).

---

## 3.6 · Fascicolo immobile (documenti + APE)

**A cosa serve**
Raccogliere in un unico posto tutti i documenti necessari al rogito o al contratto di locazione. Il Fascicolo ti dice **cosa hai** e **cosa manca**.

### La checklist automatica

Il Fascicolo mostra una checklist di 10 documenti tipici, di cui alcuni **obbligatori** (⚠) e altri facoltativi:

**Obbligatori**
- APE — Attestato di Prestazione Energetica
- Planimetria catastale
- Visura catastale
- Atto di provenienza (rogito / successione / donazione)
- Documento d'identità del venditore

**Facoltativi (utili al rogito)**
- Conformità urbanistica / titoli edilizi
- Certificato di agibilità
- Visura ipotecaria
- *Solo per condomini* (Appartamento, Attico, Loft, Monolocale):
  - Regolamento di condominio
  - Attestazione spese condominiali
- Altro documento (libero)

### Aprire il Fascicolo

1. Vai in **Immobili** e apri l'immobile.
2. Clicca **Fascicolo** (in alto).
3. Vedi la checklist: ogni riga è ✅ se il documento c'è, ⚠️ se manca ma è obbligatorio, ⬜ se è facoltativo.

[SCREEN: cap3-fascicolo-checklist]

### Caricare un documento

**Passi**
1. Trova il documento nella checklist (o scegli *Altro documento*).
2. Clicca **Carica**.
3. Scegli il file (max **8 MB**, formati PDF · JPEG · PNG).
4. Il documento viene caricato e la riga passa a ✅.

**Errori comuni**
- *"File troppo grande"* → riduci le pagine (spesso il PDF è scansione a 600 dpi; 200 dpi bastano). Programmi utili: **Anteprima** su Mac, **Adobe Acrobat Reader** su Windows, servizi come **iLovePDF** o **Smallpdf**.
- *"Formato non supportato"* → converti in PDF. La maggior parte dei visori PDF permette **Salva come PDF**.

### APE — Attestato di Prestazione Energetica

L'APE non è calcolabile da OMNIA: deve essere **prodotto da un tecnico abilitato** (geometra, architetto, ingegnere con certificazione).

- Se ce l'hai già → caricalo come *APE*.
- Se non ce l'hai ancora → **l'ordine APE via partner integrato è in valutazione** (nessun bottone in UI oggi). Nell'attesa, chiedi il documento al tuo tecnico abilitato di fiducia (geometra/architetto/ingegnere certificatore) e caricalo appena disponibile.
- Nell'attesa, puoi comunque **dichiarare la classe energetica** (A4 → G) nei dati dell'immobile: il portale la mostrerà, ma per il rogito serve il documento firmato dal tecnico.

**Chi vede il Fascicolo**
- **Titolare · Agente responsabile**: sempre.
- **Altri agenti dell'agenzia**: dipende dal livello di privacy dell'immobile (L4 solo interno = tutti).
- **Segreteria**: come agente.
- **Nessun utente esterno** vede mai il Fascicolo: è un'area interna.

---

## 3.7 · Errori comuni (raccolta)

Riassumo i problemi più frequenti su questo modulo. Le soluzioni dettagliate sono nei paragrafi precedenti.

| Problema | Dove | Cosa fare |
|----------|------|-----------|
| Ho aggiunto un immobile ma non compare in "Immobili attivi" | Dashboard | È in Bozza. Aprilo → Stato: Pubblicato → Salva. |
| L'indirizzo non è riconosciuto sulla mappa | Nuovo immobile | Metti *"via + civico"* completo, o aggiungi *"(sigla provincia)"* dopo il comune. |
| Le foto compaiono in ordine sbagliato | Foto | Trascina le miniature. La prima foto della lista è la copertina. |
| Il proprietario si lamenta della visibilità del prezzo | Privacy | Alza a **L2** (esatto solo per registrati) o **L3** (esclusive). |
| Ho pubblicato ma l'immobile non compare sui portali | Portali | Il sync automatico gira ogni notte alle 06:00 UTC; puoi anche forzare *Sync subito* dalla scheda del portale. Se dopo la finestra di sync non appare, apri la modale **Compliance** per vedere se è stato bloccato. Vedi Cap. 6. |
| Voglio nascondere solo l'indirizzo, non tutto | Privacy | Attiva *"Nascondi indirizzo esatto pubblicamente"*. |
| Import CSV: molte righe scartate | Importa CSV | Apri l'accordion errori: mancano campi obbligatori (prezzo, tipologia, città). |
| Import XML: file troppo grande | Import universale | Chiedi al vecchio gestionale di esportare per zona/agente. Massimo 50 MB per file. |

---

## Voci correlate (fuori capitolo)

- **Cap. 2 · Dashboard** — contatore *Immobili attivi*
- **Cap. 4 · Clienti** — collegare *Cliente venditore* al proprietario
- **Cap. 5 · Match** — abbinamenti automatici cliente↔immobile
- **Cap. 6 · Portali** — Publishing Center (catalogo v1 di 8 portali generalisti; Immobiliare.it/Casa.it/Idealista non in v1)
- **Cap. 7 · Fascicolo Immobile** — checklist rogito, analisi HAL e valutazione AI (approfondimento del §3.6)
- **Cap. 10 · HAL Agents** — pulsante *"Migliora con HAL"* su titolo/descrizione

---

## Note per HAL

> Le voci di questo capitolo sono esportate come YAML operativo in
> `/app/memory/manuale/hal/03-immobili.yaml`.

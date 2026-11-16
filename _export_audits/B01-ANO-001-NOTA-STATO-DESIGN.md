# OMNIA — B01 / ANO-001
## Nota di stato e chiusura del design

**Data:** 16 novembre 2026  
**Design:** `B01-ANO-001-DESIGN-MODELLO-DATI-TARGET.md`  
**Commit dichiarato:** `cfbd69a`

### 1. Stato

Design B01 acquisito e salvato nel repository.

La progettazione del modello dati target è considerata acquisita come base architetturale, ma la chiusura definitiva resta subordinata alla definizione dei tre punti indicati sotto.

### 2. Dipendenze corrette

La sequenza corretta del backlog è:

- B02 — autorizzazioni e audit
- B03 — sessioni, registrazione e inviti
- B04 — billing
- B05 — MLS
- B06 — documenti
- B07 — migrazione

La precedente inversione B04/B05 è da considerarsi corretta nell'export.

### 3. Punti ancora aperti

**B01-OPEN-01 — Person vs User legacy**

La separazione tra Person e User è acquisita. Resta da definire la regola per gli account legacy, inclusa la possibilità di mantenere un User senza Person finché non siano disponibili dati anagrafici sufficienti.

**B01-OPEN-02 — Owner ≠ Main Admin**

È confermato che proprietà/titolarità dell'organizzazione e amministrazione commerciale sono concetti distinti. Restano da definire le regole operative e le relazioni necessarie per rappresentarli.

**B01-OPEN-03 — Membership ≠ Representation**

La distinzione è acquisita e non deve essere riaperta. Restano da precisare le regole operative e i dati necessari a rappresentanza, validità e ambito dei poteri.

### 4. Confini

- Nessun codice autorizzato.
- Nessuna migrazione autorizzata.
- Nessuna PR autorizzata.
- Nessuna modifica al repository da parte di ChatGPT.
- B02 non aperto.
- Nessuna decisione implicita sui tre punti aperti.

### 5. Stato finale

**B01: design acquisito; tre punti aperti; chiusura definitiva in attesa delle decisioni Founder.**

Il prossimo passaggio, quando autorizzato, sarà definire esclusivamente i tre punti aperti. Solo dopo potrà essere valutata la chiusura definitiva di B01.

Nessuna attività ulteriore avviata.

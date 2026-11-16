# OMNIA — REGISTRO AGGIORNAMENTO
## Chiusura definitiva B01 — ANO-001

**Data:** 16 novembre 2026  
**Stato:** DESIGN DEFINITIVAMENTE CHIUSO  
**Implementazione:** NON AUTORIZZATA

Riferimenti: `B01-ANO-001-DESIGN-MODELLO-DATI-TARGET.md`, `B01-ANO-001-NOTA-STATO-DESIGN.md`.

### B01-DEC-01 — Person vs User

Decisione Founder:

- Un User può esistere senza Person.
- Person viene creata soltanto quando sono disponibili dati anagrafici sufficienti.
- Non si creano Person fittizie o inventate per completare relazioni tecniche.
- L'assenza di Person non invalida l'esistenza dell'account User.

**Stato:** APPROVATA E CHIUSA.

### B01-DEC-02 — Owner, Main Admin e Branch Admin

Decisione Founder:

- Owner, Main Admin e Branch Admin sono tre concetti distinti.
- Non sono sinonimi e non devono essere accorpati nel modello dati.
- Nel caso di libero professionista con P.IVA propria, titolare e zero collaboratori, la stessa persona può ricoprire tutti e tre i ruoli.
- La coincidenza della persona non elimina la distinzione concettuale e funzionale dei ruoli.

**Stato:** APPROVATA E CHIUSA.

### B01-DEC-03 — Membership e Representation

Decisione Founder:

- Membership e Representation sono entità/relazioni distinte.
- È consentita una sola Membership operativa attiva per volta.
- Representation non crea Membership.
- La rappresentanza non conferisce automaticamente appartenenza operativa.

**Stato:** APPROVATA E CHIUSA.

### Chiusura B01

- Modello dati target: acquisito.
- Mapping dello stato attuale: acquisito come progetto.
- Rischi e criteri di accettazione: acquisiti.
- Dipendenze: corrette secondo backlog (B02…B07).
- B01-OPEN-01 / 02 / 03: chiusi tramite B01-DEC-01 / 02 / 03.

**B01 — ANO-001: DESIGN DEFINITIVAMENTE CHIUSO.**

### Confini di autorizzazione

- Nessun codice autorizzato.
- Nessuna migrazione autorizzata.
- Nessuna PR di prodotto autorizzata.
- B02 NON APERTO.

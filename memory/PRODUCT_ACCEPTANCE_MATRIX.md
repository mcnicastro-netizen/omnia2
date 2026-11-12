# OMNIA Product Acceptance Matrix

**SoT collaudo flussi gestionale** · aggiornato 12-Nov-2026 (~18:15 CET · Europe/Rome)  
**Principio (audit 2)**: ogni operazione ha un *prima*, un’*azione* e un *passo successivo evidente*.  
**Ordine programma**: (1) flussi · (2) design system navy/oro · (3) esperienza quotidiana · (4) QA journey.  
**Non-done**: «il pulsante funziona» ≠ flusso concluso.

## Gate obbligatori (5)

| # | Gate | Domanda |
|---|------|---------|
| S | Salvataggio | Il dato viene registrato? |
| C | Continuità | Dove mi porta dopo il salvataggio? |
| R | Relazione | Cliente, immobile e richiesta sono collegati (se serve)? |
| A | Azione | Posso proseguire senza tornare alla sidebar? |
| F | Feedback | Capisco cosa è completato e cosa manca? |

**Done** = S∧C∧R∧A∧F tutti ✅.

---

## Stato programma (post merge)

| Fase | Cosa | PR su main | Stato |
|------|------|------------|-------|
| 1 Flussi P0–P2 | Desk flows, Cliente→Richiesta, Visibility, Oggi, Portali, Import | #192 · #195 · #196 · #197 · #198 | ✅ codice |
| 2 Design system | Token `crm-*`, Immobili, Attività, MLS, Clienti | #199 · #200 · #201 · #202 | ✅ codice |
| 3 Quotidiano | Oggi, Match, Richieste, Lucide shell | #203 · #204 · #205 | ✅ codice |
| 4 QA journey | Collaudo gate su **produzione** | questo doc | ⬜ dogfood Founder |

---

## Matrice 9 journey (stato su `main`)

### J1 — Avvio

| Gate | Esito | Note |
|------|-------|------|
| S | ✅ | `setup_journey` persistito |
| C | ✅ | Un passo in focus + Continuare / rail |
| R | n/a | — |
| A | ✅ | Link a sito / import / MLS / publishing |
| F | ✅ | Segna fatto + embed D-170 |

**Done?** ✅ codice · ⬜ dogfood Nicastro su prod

---

### J2 — Immobile → foto → visibilità

| Gate | Esito | Note |
|------|-------|------|
| S | ✅ | POST/PATCH property |
| C | ✅ | Post-create → `/{id}?created=1` (focus foto) |
| R | ✅ | Seller client / owner fields |
| A | ✅ | Select visibility public / mls_only / private |
| F | ✅ | Banner created + coach |

**Done?** ✅ codice · ⬜ dogfood

---

### J3 — Attività → Cliente → Immobile

| Gate | Esito | Note |
|------|-------|------|
| S | ✅ | POST activities |
| C | ✅ | Lista / settimana |
| R | ✅ | EntitySearch typeahead (no UUID) |
| A | ✅ | Link Cliente / Immobile in riga |
| F | ✅ | Filtri Aperte/Oggi/Settimana |

**Done?** ✅ codice · ⬜ dogfood

---

### J4 — Cliente → Richiesta → Match

| Gate | Esito | Note |
|------|-------|------|
| S | ✅ | Create client |
| C | ✅ | Searcher → `/requests/new?client_id=&created=1` |
| R | ✅ | Brief legato al client |
| A | ✅ | CTA Match da scheda cliente |
| F | ✅ | Banner next su request form |

**Done?** ✅ codice · ⬜ dogfood

---

### J5 — MLS adesione → condivisione

| Gate | Esito | Note |
|------|-------|------|
| S | ✅ | Join/leave MLS |
| C | ✅ | Banner «Vai agli immobili» post-join |
| R | ✅ | Inventory card → scheda CRM o cloud |
| A | ✅ | Visibility su immobile |
| F | ✅ | Embed kit se sito external (D-170) |

**Done?** ✅ codice · ⬜ dogfood Nicastro (incolla box su sito proprio)

---

### J6 — Oggi → scheda

| Gate | Esito | Note |
|------|-------|------|
| S | n/a | — |
| C | ✅ | `recent[].href` cliccabili |
| R | ✅ | Link a client/property/activity/match |
| A | ✅ | Empty → Apri Clienti |
| F | ✅ | Cockpit gruppi + KPI |

**Done?** ✅ codice · ⬜ dogfood

---

### J7 — Match

| Gate | Esito | Note |
|------|-------|------|
| S | ✅ | Motore match |
| C | ✅ | Empty guidato (nuovo immobile / acquirente) |
| R | ✅ | CTA da scheda cliente |
| A | ✅ | Lead score + breakdown |
| F | ✅ | Min score filter |

**Done?** ✅ codice · ⬜ dogfood

---

### J8 — Portali

| Gate | Esito | Note |
|------|-------|------|
| S | n/a | — |
| C | ✅ | Percorso reale: sito → feed → social |
| R | n/a | — |
| A | ✅ | Tab «Attivabili ora» default se vuoto |
| F | ✅ | Idealista/Immobiliare «In arrivo» onesto |

**Done?** ✅ codice · ⬜ dogfood

---

### J9 — Import Avvio

| Gate | Esito | Note |
|------|-------|------|
| S | ✅ | Import clienti/immobili |
| C | ✅ | CTA brief + Continua Avvio |
| R | ✅ | Hint: crea richieste per acquirenti |
| A | ✅ | Avvio step Clienti con link richiesta |
| F | ✅ | Done UI post-commit |

**Done?** ✅ codice · ⬜ dogfood

---

## Checklist dogfood Founder (fase 4)

Eseguire su **produzione** (non solo Cloud preview), account Nicastro o demo:

1. **J1** — Completa / ripercorre un passo Avvio; verifica Continuare e (se external) snippet MLS.
2. **J2** — Nuovo immobile → resti in scheda → carica foto → imposta visibility.
3. **J3** — Nuova attività con typeahead cliente + immobile → apri i link.
4. **J4** — Nuovo acquirente → landi su nuova richiesta → salva brief → Apri Match.
5. **J5** — MLS join → Vai agli immobili → apri card inventory → (sito) box embed.
6. **J6** — Oggi: click su una riga recente; empty state se vuoto.
7. **J7** — Match empty o lista; da cliente CTA Match.
8. **J8** — Portali: vedi sito/feed/social prima di Idealista.
9. **J9** — Import clienti (anche 1 riga) → vedi CTA brief / Continua Avvio.
10. **Superficie** — Immobili/Attività/MLS/Clienti/Oggi/Match/Richieste + sidebar Lucide oro su attivo.

Segnare qui sotto dopo il giro:

| Journey | Dogfood prod | Note Founder |
|---------|--------------|--------------|
| J1–J9 | ⬜ | |
| Superficie D-171 | ⬜ | |

---

## Riferimenti

- D-171 identità · D-172 flussi · D-170 embed MLS
- PR flusso: #192–#198 · PR design: #199–#205

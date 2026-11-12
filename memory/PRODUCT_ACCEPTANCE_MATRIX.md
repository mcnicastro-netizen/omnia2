# OMNIA Product Acceptance Matrix

**SoT collaudo flussi gestionale** · aggiornato 12-Nov-2026 (Europe/Rome)  
**Principio (audit 2)**: ogni operazione ha un *prima*, un’*azione* e un *passo successivo evidente*.  
**Ordine programma**: (1) chiudere flussi · (2) design system navy/oro · (3) esperienza quotidiana · (4) QA journey end-to-end.  
**Non-done**: «il pulsante funziona» ≠ flusso concluso.

## Gate obbligatori (5)

| # | Gate | Domanda |
|---|------|---------|
| S | Salvataggio | Il dato viene registrato? |
| C | Continuità | Dove mi porta dopo il salvataggio? |
| R | Relazione | Cliente, immobile e richiesta sono collegati (se serve)? |
| A | Azione | Posso proseguire senza tornare alla sidebar? |
| F | Feedback | Capisco cosa è completato e cosa manca? |

**Done** = S∧C∧R∧A∧F tutti ✅. Un solo ❌ = flusso non concluso.

---

## Stato PR #192 (blocco operativo)

| Voce | Stato verificato |
|------|------------------|
| Branch | `cursor/feat-crm-desk-flows-1433` |
| Contro `main` | **CONFLICTING / DIRTY** (post merge #193 D-170) |
| File in conflitto | `AvvioSetupPage.jsx`, `MlsPage.jsx` (testo/embed D-170 vs hint MLS #192) |
| Auto-merge ok | `ActivitiesPage.jsx`, `PropertyFormPage.jsx`, `AgencyShell.jsx` |
| Scope reale PR | Avvio un passo + rail Continuare · Crea immobile → scheda `?created=1` · Attività EntitySearch · hint post-join MLS |
| **Non** in PR | Cliente→Richiesta · Visibility MLS · Match da scheda · Oggi cliccabile · Portali · Import Avvio |

### Checklist merge #192 (obbligatoria)

1. Rebase/merge `main` → risolvere conflitti Avvio/MLS **preservando D-170 embed kit**.
2. Test manuale: Avvio passo corrente · Crea immobile → scheda/foto · Attività typeahead.
3. CI verde sul branch aggiornato.
4. Merge solo dopo 1–3.
5. Dogfood produzione: verificare che i 3 percorsi esistano live (non «perché esiste la PR»).

---

## Matrice 9 journey

Legenda stato: `main` = codice su main oggi · `PR` = presente in #192 (non ancora prod) · Gate = esito su main (e su PR se diverso).

### J1 — Avvio (setup agenzia)

| Passo atteso | main | #192 |
|--------------|------|------|
| Un solo passo in focus | Checklist + «segna fatto» | Un passo + Continuare |
| Rail «Continua Avvio» nel desk | No | Sì |
| Sito proprio → embed box (D-170) | Sì (#193) | Conflitto da fondere |

| S | C | R | A | F | Done? |
|---|---|---|---|---|-------|
| ✅ | ❌ main / ✅ PR* | n/a | ❌ main / ✅ PR* | ⚠️ | No finché #192 non è in prod senza rompere D-170 |

\*dopo risoluzione conflitti.

**Criterio done**: dopo Attiva, l’agente vede solo il passo corrente, sa «e poi», e D-170 resta intatto.

---

### J2 — Immobile → Fotografie → Visibilità → Lavoro commerciale

| Passo atteso | main | #192 |
|--------------|------|------|
| 1. Crea dati principali | Sì | Sì |
| 2. Salva (registrato) | Sì | Sì |
| 3. Apre scheda + focus foto | No → lista | Sì → `/{id}?created=1` |
| 4. Scelta visibility public / mls_only / private | No (default BE) | No |
| 5. Match / clienti / attività | Solo da menu | Solo da menu |

| S | C | R | A | F | Done? |
|---|---|---|---|---|-------|
| ✅ | ❌ main / ⚠️ PR (scheda sì, visibility no) | ⚠️ | ❌ | ❌ | No |

**Criterio done**: post-save → scheda con foto in primo piano → select visibilità → CTA match/attività senza sidebar. Visibility in UI (campo BE già esiste).

---

### J3 — Attività → Cliente → Immobile

| Passo atteso | main | #192 |
|--------------|------|------|
| Crea attività | Sì | Sì |
| Seleziona cliente/immobile per nome | UUID a mano | EntitySearch |
| Apri scheda da attività | Parziale | Parziale |

| S | C | R | A | F | Done? |
|---|---|---|---|---|-------|
| ✅ | ⚠️ | ❌ main / ✅ PR | ⚠️ | ⚠️ | No finché #192 in prod |

**Criterio done**: zero campi «codice»; pick typeahead; dopo salva si capisce il collegamento.

---

### J4 — Cliente → Richiesta → Match

| Passo atteso | main | #192 |
|--------------|------|------|
| Crea acquirente/tenant/investor | Sì | — |
| Post-save → brief/richiesta | No → lista clienti | — |
| «+ richiesta» | Solo in edit | — |
| Match dalla scheda cliente | No | — |

| S | C | R | A | F | Done? |
|---|---|---|---|---|-------|
| ✅ | ❌ | ❌ | ❌ | ❌ | No — **non in #192** |

**Criterio done**: se searcher, dopo Salva → `/requests/new?client_id=` (o scheda con CTA forte «Crea brief») · poi Match senza limbo preferenze.

---

### J5 — MLS adesione → Condivisione consapevole

| Passo atteso | main | #192 |
|--------------|------|------|
| Entra nel network | Sì | Sì |
| Passo successivo post-join | Debole | Hint migliorato* |
| Inventory apre scheda immobile | No (card morte) | No |
| Visibility per immobile | No in form | No |
| Embed sito proprio | Sì (D-170) | Conflitto copy |

| S | C | R | A | F | Done? |
|---|---|---|---|---|-------|
| ✅ | ⚠️ | ⚠️ | ❌ | ❌ | No |

**Criterio done**: join → «condividi immobile» o inventory cliccabile · visibility esplicita · D-170 ok.

---

### J6 — Oggi → Attività → Scheda

| Passo atteso | main | #192 |
|--------------|------|------|
| Strip «Ultime attività» | Testo senza link | — |
| Click → scheda | No | — |
| Empty → lavoro utile | Debole | — |

| S | C | R | A | F | Done? |
|---|---|---|---|---|-------|
| n/a | ❌ | ❌ | ❌ | ⚠️ | No — **non in #192** |

**Criterio done**: ogni riga recente è Link a immobile/cliente/attività.

---

### J7 — Match (lavoro commerciale)

| Passo atteso | main | #192 |
|--------------|------|------|
| Motore match | Sì | — |
| CTA da scheda cliente / immobile | Debole / assente | — |
| Empty state guidato | Debole | — |

| S | C | R | A | F | Done? |
|---|---|---|---|---|-------|
| ✅ | ❌ | ⚠️ | ❌ | ❌ | No — **non in #192** |

**Criterio done**: da cliente con brief → Match in un click; empty state dice cosa manca.

---

### J8 — Portali

| Passo atteso | main | #192 |
|--------------|------|------|
| Idealista toggle | «In arrivo» (onesto) | — |
| Percorso reale (sito/feed/social) | Sparso | — |

| S | C | R | A | F | Done? |
|---|---|---|---|---|-------|
| n/a | ❌ | n/a | ❌ | ✅ (onesto) | No path chiaro |

**Criterio done**: Avvio/Publishing mostra prima ciò che pubblica oggi; Idealista fuori dal critico finché non è vero.

---

### J9 — Import Avvio

| Passo atteso | main | #192 |
|--------------|------|------|
| Segna fatto senza import | Possibile | — |
| Post-import → «crea richieste» / torna Avvio | Lista | — |

| S | C | R | A | F | Done? |
|---|---|---|---|---|-------|
| ✅ | ❌ | ❌ | ❌ | ❌ | No — P2 |

**Criterio done**: dopo import clienti/immobili, passo successivo esplicito (richieste o Continuare Avvio).

---

## Priorità approvate (audit 2)

| P | Intervento | Journey | Dipende |
|---|------------|---------|---------|
| P0 | Merge #192 (dopo checklist) | J1, J2†, J3 | Conflitti D-170 |
| P0 | Cliente → Richiesta | J4 | — |
| P0 | Visibility MLS | J2 passo 4, J5 | Campo BE già pronto |
| P1 | Match + Oggi | J6, J7 | — |
| P1 | Portali percorso onesto | J8 | — |
| P2 | Import Avvio guidato | J9 | — |

†J2 completo solo dopo Visibility (non tutta in #192).

## Design system (D-171)

Navy + oro, Inter, Lucide: **scelta chiusa**, ma **dopo** i flussi P0 (non bloccare merge #192 per restyling).  
Superficie Immobili/Attività/MLS = passo 3 del programma, non scusa per lasciare i journey spezzati.

## Riferimenti

- Audit 1 (superficie): canvas *Flussi gestionale · dove si spezza*
- Audit 2 (conclusione lavoro): questa matrice + D-172
- Identità: D-171
- Embed sito proprio: D-170

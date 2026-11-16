# OMNIA — HANDOFF PER CHATGPT (fonte primaria di ripresa)
**Data:** 14 novembre 2026 · Europe/Rome  
**Autore del pacchetto:** Cursor (ricostruzione da export chat Founder + audit Cursor)  
**Destinatario:** nuovo agente ChatGPT nel progetto `controllo omnia`

---

## 0. ISTRUZIONI OPERATIVE (LEGGI PRIMA DI TUTTO)

Stai riprendendo un lavoro **già avanzato**. Non ricominciare da zero.

1. Tratta **questo documento** come fonte primaria di continuità.
2. Se ti allegano anche `TUTTI-GLI-AUDIT.md` / parti audit Cursor, usali come fonte tecnica degli audit repo.
3. **Non** riproporre decisioni già approvate (elenco §3).
4. **Non** confondere: *decisione approvata* ≠ *implementata nel codice*.
5. **Non** implementare né chiedere a Cursor di scrivere codice senza la frase esatta:
   `OMNIA — AUTORIZZAZIONE ESPLICITA ALL'IMPLEMENTAZIONE`
6. Procedi **una sola decisione aperta alla volta**.
7. Ogni nuova decisione: assegna ID stabile (es. `B16-…`, `G…`) e aggiorna il registro.
8. Se ti manca contesto: dillo e chiedi il pezzo mancante — **non inventare**.

### Anti-casino (obbligatorio d’ora in poi)

| Problema già successo | Regola nuova |
|---|---|
| Finestra contesto piena / nuovo agente che riparte | All’inizio di ogni sessione: rileggi questo handoff + ultime 20 righe del registro decisioni |
| Domande già risposte rifatte | Prima di chiedere: cerca nel §3; se c’è, **non chiedere** |
| Chat spezzate (Accesso 0–18, Passaggio 1–3) | **Una sola chat lunga “MASTER CONTINUITÀ”**; le chat nuove solo per topic isolati, con link/incolla a questo file |
| Export HTML incompleti | Preferisci **esportare testo / .md** o salvare l’handoff aggiornato dopo ogni decisione |
| Confusione Cursor vs ChatGPT | ChatGPT = decisioni funzionali + programma; Cursor = verifica codice / implementazione solo con autorizzazione |
| Sommari che “dimenticano” | Dopo ogni decisione: aggiorna §3 e §5 in un messaggio dedicato «REGISTRO AGGIORNATO» |

---

## 1. DOVE SIAMO (stato al 14 nov 2026)

### Binario A — Area B / Billing (B16)
- Percorso B16 (billing, cliente commerciale, wallet, P.IVA, cessazione, disdetta) **avanzato**.
- **Ultima decisione chiusa:** `B16-CA-01` Disdetta volontaria  
  - registrata subito  
  - servizio fino a fine periodo pagato  
  - poi cessazione CE-01  
  - no rimborso automatico crediti  
  - **approvata funzionalmente, NON implementata**
- **Punto di ripresa B16:** verificare cosa resta davvero aperto **dopo** B16-CA-01 (ciclo vita Stripe / past_due tecnico / modello cliente commerciale / migrazione legacy / ledger crediti / fatturazione B2B) — **senza** riaprire Founder period, wallet centrale, P.IVA, disdetta.

### Binario B — Gestionale / MLS / UX
- Audit Cursor Master Business Architecture + serie Area B (B1, B11, B12, B14, B15, B16) **consegnati** (sola lettura).
- MLS: distinta Collaboration (B2B) vs Deal (cliente); molte regole G…; alcune aperte (rating cambio agenzia A/B/C).
- UX: priorità Founder = **chiudere i flussi**, poi Onde Design 1–4 (non nuove feature “per bellezza”).
- **Nessuna implementazione gestionale/MLS autorizzata** in queste chat.

### Binario C — Continuità / Master Program
- Esisteva già un **PROMPT MASTER DI PASSAGGIO** (14 nov) in `Presa in carico OMNIA (1)`.
- Poi ChatGPT ha chiesto gli export delle chat 0–18 perché perdeva contesto.
- Ora gli export sono stati consegnati a Cursor e **questo handoff** ricostruisce il filo.

---

## 2. PROGRAMMA MASTER DA COMPLETARE (ordine)

Completa **in sequenza**. Non saltare. Non riaprire i chiusi.

### Fase M0 — Continuity lock (questa sessione)
- [ ] Conferma di aver letto questo handoff.
- [ ] Conferma punto ripresa: **dopo B16-CA-01**.
- [ ] Crea/aggiorna un messaggio «REGISTRO DECISIONI VIVENTE» (copia §3 + §4).

### Fase M1 — Chiudere B16 (funzionale → checklist tecnica)
Una domanda alla volta, solo se serve decisione Founder:
1. Cosa resta aperto sul **ciclo vita Stripe** (past_due → sospensione: tempi già decisi? se sì non richiedere; se manca solo il “quando sospendere dopo past_due”, chiedi **solo quello**).
2. Design funzionale **cliente commerciale** (entità, link org, wallet, plafond) — senza migrazione.
3. Regole residue crediti/ledger solo se non già chiuse (FIFO, no scadenza crediti, no rimborso a cessazione = già dette).
4. Fatturazione B2B Admin: cosa deve vedere (funzionale).
5. Produce tabella: `ID | Decisione | Stato: approvato-non-implementato | Impatto codice atteso`.

### Fase M2 — Consolidare dossier MLS (senza implementare)
1. Elenco G già chiuse vs aperte (vedi §3–§4).
2. Chiudi **una** aperta prioritaria: rating agente al cambio agenzia (**A/B/C** — ancora senza risposta Founder negli export).
3. Non approvare in automatico: identità MLS≠User, snapshot, Visit riusata, `mls_shared=false`, doppia search — chiedi solo se serve al passo corrente.

### Fase M3 — Area B residua (sicurezza account)
- B5 verifica email (titolare vs invito) era “da decidere” in un handover intermedio: verifica se ancora aperta; se sì, **una** proposta.
- Non riaprire B12/B13 decisioni token/sessioni (chiuse funzionalmente; non implementate).

### Fase M4 — Disegno gestionale (Deal/Mandate/Visit/Offer)
- Usa gli audit Cursor come base.
- Output: gap list prioritizzata (P0–P3) **senza** codice.
- Allinea a G1–G6 e decisioni MLS≠Deal.

### Fase M5 — Deliverable unico
Produci (in chat, testo):

`OMNIA_MASTER_STATO_PROGETTO_E_CONTINUITA`

Sezioni obbligatorie:
1. Visione e vincoli  
2. Decisioni chiuse (ID)  
3. Aperte (ID + prossima domanda)  
4. Audit Cursor già fatti (lista)  
5. Cosa NON implementare ancora  
6. Prossimo passo unico  
7. Prompt Cursor **solo lettura** (se serve verifica codice)  
8. Prompt Cursor **implementazione** (solo bozza; non inviare a Cursor finché non c’è autorizzazione)

### Fase M6 — Prompt per Cursor (solo quando Founder dice sì)
- Prima: prompt di verifica read-only mirati.
- Poi: piano implementazione a slice.
- Mai codice senza: `OMNIA — AUTORIZZAZIONE ESPLICITA ALL'IMPLEMENTAZIONE` + scope.

---

## 3. DECISIONI GIÀ APPROVATE (NON RICHIEDERE DI NUOVO)

> Stato tipico: **approvato funzionalmente / non implementato**, salvo diversa verifica codice.

### Organizzazione / commerciale
- P.IVA = cliente commerciale; stessa P.IVA → un cliente, una subscription, un wallet.
- P.IVA diversa → nuovo cliente.
- Filiale stessa P.IVA = stesso cliente/plafond; P.IVA diversa = nuovo cliente.
- Filiale **autonoma** = autonoma anche in MLS.
- 1 Admin per organizzazione; accessi cross-org solo con autorizzazione esplicita tracciata.
- Stessa persona fisica può rappresentare più org se P.IVA diverse; no unicità forzata `owner_id`.
- Limiti utenti/immobili aggregati per P.IVA; filiali **non** moltiplicano i limiti.
- Attenzione a non alterare i pacchetti Starter/Pro/Agency (catalogo `PRICING_OMNIA.md` v3.3).

### Founder period
- 12 mesi dal **primo** abbonamento pagato/attivato.
- Upgrade Starter→Pro **non** riavvia i 12 mesi.
- Unico per cliente commerciale / P.IVA.

### Billing B16 (tra cui)
- Serie B16-PD / B16-CE già definite nel Prompt Master (tolleranze, wallet, FIFO, crediti senza scadenza, upgrade/downgrade, cessazione, uscita filiale, cambio P.IVA).
- **B16-CA-01** disdetta volontaria (vedi §1).
- Precisazione crediti su cambio P.IVA (CE-05) confermata Founder.

### Sessioni / sicurezza (funzionale)
- B13: collaboratore gestisce **solo le proprie** sessioni; Admin non vede quelle altrui; Super Admin strumenti tecnici tracciati.
- B12 log: decisioni precedenti chiuse sul piano decisionale.
- Implementazione ancora da fare.

### MLS / collaborazione (funzionale, selezione)
- MLS ≠ Deal; Collaboration come funzione autonoma (concetto condiviso).
- Property ≠ Listing ≠ Mandate (G5).
- Condizioni collaborazione: campo dedicato in scheda + ripetute in accordo.
- Visite MLS: ≥3 slot; alternative; telefono OK nella pratica.
- Chat OMNIA **fuori** dalle chat interne intra-agenzia; chat solo inter-agenzia MLS.
- Fascicolo originale **non** condiviso.
- Mini-dossier post-visita: due feedback indipendenti; Super Admin su segnalazioni; no confronto obbligatorio diretto.
- G23 contestazioni → admin rete; G24 Super Admin piattaforma.

### Metodo
- Evolvere codice esistente, non rebuild totale.
- Audit Cursor in sola lettura finché non c’è autorizzazione.
- Formula unica di implementazione (sopra).

---

## 4. ANCORA APERTE (lavorare da qui)

Priorità suggerita:

1. **B16 residuale tecnico/funzionale** dopo CA-01 (soprattutto: sospendere dopo past_due — se non già fissato nel master; ciclo eventi Stripe; design cliente commerciale).
2. **Rating MLS al cambio agenzia** — domanda A/B/C **senza risposta Founder** negli export (chat Accesso dashboard 4).
3. **B5** verifica email (se ancora aperta).
4. Premature (non chiudere a fascio): identità MLS separata da User; snapshot immutabile; Visit riusata MLS/Deal; default `mls_shared=false`; doppia search pubblica/autenticata.
5. G25 formula rating; G51 nuova chat stessa collaborazione; G53 notifiche; dettagli calendario MLS; G40 versioni documenti.
6. Doppia creazione cliente stessa P.IVA (prevenzione).
7. UX Onde 1–4: solo dopo chiusura flussi prioritari.

---

## 5. AUDIT CURSOR GIÀ CONSEGNATI (non rifare da zero)

Serie commissionata / estratta (13–14 nov 2026), tra cui:
- Master Business Architecture & Gap Analysis (+ follow-up scenario 1 immobile / 3 clienti)
- Decisione soggetti + specifica MLS + verifica coerenza MLS
- B1 Account/auth · B11 permessi · B12 log · B14 login · B15 registrazione/attivazione
- Agent dedicati: RBAC backend · UI permessi · inventario collection audit Mongo · register/invite/KYC · B15 verifica · **B16 billing**

Se serve dettaglio: allegare `TUTTI-GLI-AUDIT.md` (o le 4 parti `.txt`).

---

## 6. COSA DIRE SUBITO AL FOUNDER (primo messaggio utile)

Usa questo schema:

1. «Ho letto l’handoff del 14 nov. Riparto **dopo B16-CA-01**. Non riapro P.IVA/wallet/Founder period/disdetta.»
2. «Prossima unica domanda: …» (scegline **una** da §4, preferibilmente residuale B16 o rating A/B/C).
3. «Alla fine di questa sessione aggiorno il REGISTRO.»

---

## 7. NOTA SULLA QUALITÀ DEGLI EXPORT

Gli HTML “Salva pagina” di ChatGPT sono **parziali** (UI + pezzi di testo). Cursor ha ricostruito da:
- HTML Accesso 1–18 (+ paste della 4)
- Presa in carico / Passaggio consegne
- Prompt Master interno a Presa in carico (1)
- Audit Cursor

Se trovi contraddizione tra un pezzo HTML troncatо e il Prompt Master B16, **prevale il Prompt Master + decisioni Founder esplicite**.

---

## 8. CHECKLIST ANTI-CASINO PER IL FOUNDER (Marco)

1. Lavora in **una** chat MASTER CONTINUITÀ + allega sempre questo file.
2. Dopo ogni decisione: «Annota come IDxxx».
3. Prima di nuova chat: esporta handoff aggiornato.
4. Non chiedere “riparti da capo”.
5. Per Cursor: solo prompt mirati; implementazione solo con frase autorizzazione + scope.
6. Non affidarti alla sola memoria della chat lunga.

---

**Fine handoff.**  
Prossimo passo atteso da ChatGPT: conferma lettura + **una** domanda aperta (M1 o rating A/B/C).

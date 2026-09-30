# OMNIA — Programma attuativo pre-attivazione commerciale

**Stato:** ✅ **APPROVATO Founder** (30-Set-2026) · K-PA-01…03 risolte · **D-115**  
**SoT continuità:** `docs/audit/OMNIA_AUDIT_STATE.md` (§25bis · D-094…D-115)  
**Vincoli:** listino fermo · nessun P0–P3 nuovo in audit · **nessun codice** finché Founder non dà «vai» su onde/implementazione  
**Regola commerciale:** **nessun pagamento self-serve finché O6 non è PASS.**  
**Obiettivo:** prima OMNIA attivabile senza sorprese, poi rubinetto commerciale — non corsa outreach ~5k email.

### Priorità Founder (ordine di senso)

1. Sicurezza dei dati  
2. Storage / sostenibilità bak+media  
3. Sistemi anticrash (integrità operativa)  
4. Recupero dati  

GTM-01 resta in coda come **checkpoint** quando si sceglierà l’outreach; non guida questa sequenza.

---

## Principi attuativi

1. **Attivazione ≠ demo.** Debito dichiarato può stare in una demo assistita; non in “paga e entri” se sicurezza/recupero/economia bak sono aperti.
2. **Invarianti sui percorsi**, non mega-rewrite (baseline P22/P23).
3. **Una source of truth** per stato semantico (agency, entitlement, pricing, errori).
4. **Bak + restore + retention + costi** = catena unica (**D-096** · **D-114**); listino fermo finché ci sono numeri.
5. **FS locale** può restare backend fisico; il full-copy × retention **non** resta modello economico silenzioso.
6. Implementazione solo al «vai»; §23 Priorità audit resta CLOSED — questo documento è la sequenza operativa.
7. **Nessun pagamento self-serve finché O6 ≠ PASS** (**D-115**). Durante le onde: solo **provisioning assistito dichiarato** (tempi interni da definire; non scappatoia permanente).

---

## Onde di lavoro

| Onda | Nome | Focus Founder | Esito |
|------|------|---------------|--------|
| **O0** | Design & numeri bak/media | Storage / economia | **Numeri + design vincolante** (no refactoring obbligatorio in O0) |
| **O1** | Confini di sicurezza | Sicurezza dati | Fascicolo + invite + SoT agency |
| **O2** | Integrità di dominio | Anticrash | Trash uniforme + freeze |
| **O3** | Catena di recupero | Recupero + anticrash ops | Bak health + restore manuale testato |
| **O4** | Contratto commerciale onesto | Fiducia / pagamento | Pricing SoT + demo≠entitlement |
| **O5** | Percorso anti-fallimento | Affidabilità primo uso | Upload/empty/pagination/errori/scheduling/seed |
| **O6** | Gate attivazione | Go / no-go | Checklist pass/fail prima di accettare soldi self-serve |

Le onde **O0∥O1** possono partire in parallelo (design economia vs fix AuthZ).  
**O3** dipende da avere chiaro almeno il perimetro restore di **O0/D-096**.  
**O6** è il cancello: senza O1–O3 + O0 (numeri/design) + O4 se c’è pagamento → **no attivazione self-serve**.

---

## Dettaglio voci (motivo · evidenza · done)

### O0 — Sostenibilità bak/media · **D-114** · **K-PA-01**

| Campo | Contenuto |
|-------|-----------|
| **Cosa** | **Calcolo reale dei costi** + **modello target deciso e scritto**. Deliverable minimi: retention target · cosa entra/esce dal bak · full vs incrementale · restore agency-first · costo stimato · frase vincolante: *“questo è il modello che implementeremo”* |
| **Motivo** | Full-copy × ~30g ≈ ~32×: margine cieco. Corregge R1: non Excel morto, non mega-refactor in O0 |
| **Evidenza** | AD-02 · B-01 · C-04 · SC-03 · Master §5 · review auditer R1 |
| **Done quando** | Documento costi + design **vincolante** approvato Founder; listino ancora fermo finché non si decide revisione |
| **Non include** | Refactoring/implementazione del nuovo bak **dentro O0** — quella è fase successiva post-design |

### O1a — Fascicolo AuthZ · **D-095** · NI-01

| Campo | Contenuto |
|-------|-----------|
| **Cosa** | Separare endpoint/AuthZ fascicolo da `/api/media` pubblico; listing photos possono restare pubbliche |
| **Motivo** | Sicurezza dati: path noto ≠ autorizzazione |
| **Evidenza** | AD-05 · M-01 · EC-10 · G-02 |
| **Done quando** | Fascicolo/modulistica richiedono auth + agency; test negativi su URL diretto |

### O1b — Invite senza overwrite · **D-100** · NI-02

| Campo | Contenuto |
|-------|-----------|
| **Cosa** | Contratto invite unico: utente esistente → link agency; mai `$set` password; FE stati espliciti |
| **Motivo** | Integrità identità / anti account-takeover in onboarding reale |
| **Evidenza** | AF-01 · AD-09 · EC-05/06 · CT-09 |
| **Done quando** | Accept su utente esistente non muta `password_hash`; verify espone `user_exists` |

### O1c — SoT `active_agency_id` · **D-106** · NI-03

| Campo | Contenuto |
|-------|-----------|
| **Cosa** | Nessun fallback semantico a `agency_ids[0]`; missing/invalid = errore |
| **Motivo** | Isolamento tenant: operare sull’agency sbagliata è leak/corruzione |
| **Evidenza** | AF-03 · AD-08 · EC-01 |
| **Done quando** | `/agencies/me*`, invites, billing, CRM usano agency attiva |

### O2 — Trash uniforme + freeze · **D-094** · **D-111** · NI-04

| Campo | Contenuto |
|-------|-----------|
| **Cosa** | Filtro non-trashed nel dominio (match/sync/smart/job); client TRASHED → freeze nuove ops; richieste `active→frozen`; storico preservato |
| **Motivo** | Anticrash di dominio: dati “eliminati” che rientrano da job = corruzione operativa |
| **Evidenza** | EC-02/03/04 · AD-10 · E-* |
| **Done quando** | Test: property/client trashed assenti da match/sync; freeze blocca nuove richieste/side effect |

### O3a — Bak health · **D-105** · NI-07

| Campo | Contenuto |
|-------|-----------|
| **Cosa** | Founder Ops: ultimo bak OK/PARTIAL/FAILED + timestamp + alert |
| **Motivo** | Senza osservabilità non sai se il recupero è anche solo possibile |
| **Evidenza** | AD-12 · O-01/02/05 · CT-11 |
| **Done quando** | Fallimento bak visibile in Ops entro il ciclo successivo |

### O3b — Restore manuale testabile · **D-113**

| Campo | Contenuto |
|-------|-----------|
| **Cosa** | Procedura documentata, ripetuta su non-prod, esito verificabile per **una agency** |
| **Motivo** | Recupero dati: bak ≠ restore testato. Non piattaforma DR |
| **Evidenza** | AD-03 · R-* · CT-03 · D-096 |
| **Done quando** | Almeno una run firmata (immobili/clienti/richieste/attività/media coerenti); limiti interni scritti (anche se non “garantito” in marketing) |

### O4a — Pricing SoT · **D-109** · NI-05

| Campo | Contenuto |
|-------|-----------|
| **Cosa** | Landing allineata a `GET /billing/plans` **oppure** nascosta; legacy esplicito |
| **Motivo** | Contratto commerciale divergente = litigio/attivazione su premesse false |
| **Evidenza** | CT-01 · AD-14 |
| **Done quando** | Una sola fonte prezzi correnti in superficie pubblica |

### O4b — Demo ≠ entitlement · **D-110** · NI-05

| Campo | Contenuto |
|-------|-----------|
| **Cosa** | `localStorage` non simula piano pagato; entitlement solo server-side |
| **Motivo** | Pagamento/attivazione non possono poggiare su storage client |
| **Evidenza** | CT-06 · EC-07 · AD-13 |
| **Done quando** | Stripe off / no entitlement → UI non mostra “piano attivo” |

### O5 — Percorso anti-fallimento · **D-104** (+ D-107 · D-108 · D-112) · NI-06

| Campo | Contenuto |
|-------|-----------|
| **Cosa** | Upload `pending→success/error`+retry; empty≠error; pagination FE properties; error `code` stabile; un owner scheduling; seed demo deterministico |
| **Motivo** | Primo uso reale non deve produrre stati silenziosi o falsi-positivi; job doppi rompono bak/purge |
| **Evidenza** | AF-04/05 · EH-03/04 · SC-08 · SC-10 · EC-13 · EC-15 |
| **Done quando** | Percorso tipico agenzia green; smoke media~20 come confidence (trigger AD-01 se fallisce) |

### O6 — Gate attivazione account

| Campo | Contenuto |
|-------|-----------|
| **Cosa** | Checklist go/no-go prima di self-serve a pagamento (o provisioning assistito esplicito) |
| **Motivo** | Evitare “compra → aspetta perché c’è debito”. O si chiude il perimetro, o si vende onboarding assistito dichiarato |
| **Done quando** | O0 (numeri+design) · O1 · O2 · O3 · O4 (se pagamento) · O5 minimi = **PASS**; altrimenti no self-serve |

---

## Fuori programma pre-attivazione (esplicito)

| Voce | Perché fuori |
|------|----------------|
| Object storage/CDN generico | Solo se smoke **o** D-114 lo impone |
| Worker dedicato / multi-replica | D-101/D-103 — 1 replica deliberata |
| OTel / Prometheus | Dopo D-105 |
| DR piattaforma / restore self-service | Oltre D-113 |
| Orphan WHEN definitivo | Path D-098/D-102; timing col design bak (O0) |
| GDPR package completo | D-099 Founders assistito *se eseguibile* |
| Hard `max_properties`/`max_agents` | Solo se entitlement GTM reali |
| Revisione listino € | Solo dopo numeri D-114 |

---

## Criterio “cliente ha pagato → operativo” · **K-PA-02** · **D-115**

> **Nessun pagamento self-serve finché O6 non è PASS.**

| Fase | Modello |
|------|---------|
| **Durante O0–O5** | Solo **provisioning assistito dichiarato** (tempi interni da definire; non “paga ora, poi vediamo”) |
| **Dopo O6 PASS** | Self-serve a pagamento ammissibile |
| **Assistito** | Non scappatoia permanente — da chiudere quando O6 è PASS |

Non si stima calendario qui. Fisso resta il **cancello O6**.

---

## Revisione auditer (critica sul programma)

### Verdetto auditer

Il programma è **coerente** con Master State §25bis, D-094…D-114 e con le priorità Founder (sicurezza · storage · anticrash · recupero). Sposta correttamente il framing da “corsa GTM” a **pre-attivazione**. La presenza di **O0/D-114 in testa (parallela a O1)** è la correzione giusta rispetto al report P25 che lasciava il bak full come vincolo accettato.

### Punti di accordo

1. **O1 prima di scaling infra** — corretto: AuthZ/invite/SoT non aspettano S3.  
2. **O2 come anticrash di dominio** — corretto: trash bypass è corruzione, non nice-to-have.  
3. **O3 = health + restore testabile** — corretto e distinto da DR commerciale.  
4. **O4 obbligatorio se c’è pagamento** — corretto.  
5. **O6 come cancello** — risponde alla domanda Founder sul biglietto da visita post-acquisto.

### Rischi / correzioni consigliate

| # | Rischio | Correzione auditer |
|---|---------|-------------------|
| R1 | O0 “solo documento” senza impegno a **cambiare** il bak → numeri che non cambiano la realtà | O0 deve produrre **decisione di design vincolante** (anche se listino fermo): es. target retention/incrementale/scope — non solo spreadsheet |
| R2 | O3b restore su bak ancora full-copy “tossico” → si testa un modello che si vuole abbandonare | Accettabile: si testa **recuperabilità attuale**; O0 definisce il modello **successivo**. Non bloccare O3b in attesa del bak perfetto |
| R3 | O5 troppo largo (i18n, seed, pagination…) diluisce O1–O3 | Tenere O5 come **minimo percorso**; non espandere a tutta EH/SC |
| R4 | Parallelismo O0∥O1 senza owner unico → O0 slitta di nuovo nel “dopo” | Owner esplicito Founder su O0; O6 non passa senza O0 DONE |
| R5 | “Assistito” diventa scappatoia infinita | SLA interno massimo di provisioning assistito da dichiarare quando si sceglie quel modello — non lasciarlo vago |

### Domande auditer — **RISOLTE** Founder (30-Set)

| K-PA | Decisione |
|------|-----------|
| **K-PA-01** | O0 = **numeri + design vincolante**; **non** refactoring obbligatorio del bak in O0. Poi implementazione = fase successiva |
| **K-PA-02** | Durante le onde: **provisioning assistito dichiarato**. Self-serve a pagamento: **solo dopo O6 PASS**. Assistito ≠ scappatoia permanente |
| **K-PA-03** | Sequenza **O0 ∥ O1 → O2 → O3 → O4 → O5 → O6**. O3 non prima di O2: prima regole dato eliminato/frozen, poi test recupero |

**Motivo K-PA-03 (Founder):** O2 protegge il comportamento del sistema; O3 verifica che possiamo recuperarlo. O0 e O1 in parallelo = binari distinti (economia bak vs confini AuthZ).

### Regola commerciale aggiuntiva

> **Nessun pagamento self-serve finché O6 non è PASS.** (**D-115**)

Prima rendiamo OMNIA attivabile senza sorprese, poi apriamo il rubinetto commerciale.

### Raccomandazione auditer — **ACQUISITA**

Programma approvato come SoT attuativo con vincoli Founder sopra. R1 chiuso da K-PA-01 (design vincolante senza mega-refactor in O0). R5 mitigato da K-PA-02 (assistito dichiarato, non permanente).

---

## Stato approvazione

| Ruolo | Stato |
|-------|--------|
| Founder | ✅ **APPROVATO** · K-PA-01…03 · regola self-serve |
| Auditer | ✅ review acquisita · programma coerente Master State |
| «vai» implementazione onde | ⏳ **non ancora dato** |

*Prossimo:* Founder dà «vai» su O0 e/o O1 (paralleli), oppure su sottoinsieme esplicito.

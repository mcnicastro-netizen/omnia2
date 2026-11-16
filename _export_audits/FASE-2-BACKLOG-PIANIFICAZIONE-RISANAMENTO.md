# FASE 2 — BACKLOG DI PIANIFICAZIONE DEL RISANAMENTO OMNIA

**Pianificazione autorizzata · Nessuna esecuzione**

**Riferimento:** `main` @ `2fea64a`  
**Perimetro:** ANO-001…ANO-009  
**Obiettivo:** definire ordine, gravità, dipendenze e criteri di completamento del futuro risanamento.  
**Data:** 16 novembre 2026  
**Natura:** programma di lavoro da sottoporre al controllo Founder prima di qualsiasi esecuzione.

Una distinzione fondamentale: il backlog non è un'autorizzazione a intervenire.

Restano vietati finché non autorizzati esplicitamente:

- modifiche al codice o ai test;
- migrazioni e scritture su database;
- patch, commit, PR e deploy;
- verifiche live su Railway o Stripe;
- riapertura o ripetizione degli audit già acquisiti.

Le decisioni Founder approvate restano vincolanti; i rilievi tecnici non diventano automaticamente nuove decisioni.

Riferimento di chiusura FASE 1: `CHIUSURA-VERIFICA-STATICA-BLOCCHI-0-7.md`.

---

## 1. Criterio di classificazione

| Priorità            | Significato                                                                                  |
| ------------------- | -------------------------------------------------------------------------------------------- |
| **P0 — Bloccante**  | Fondamenta mancanti che compromettono sicurezza, modello commerciale o correttezza dei dati. |
| **P1 — Critica**    | Funzioni essenziali del gestionale non conformi al modello approvato.                        |
| **P2 — Alta**       | Funzioni incomplete che compromettono operatività, controllo e tracciabilità.                |
| **P3 — Successiva** | Consolidamento, verifiche estese e aspetti non bloccanti per le fondamenta.                  |

Le priorità indicano la gravità funzionale e architetturale, non una stima di tempi o costi.

---

## 2. Backlog ordinato per gravità

### P0 — Fondamenta bloccanti

#### B01 — ANO-001: identità e cliente commerciale

Problema centrale: OMNIA identifica oggi l'agency, non il cliente commerciale P.IVA.

Ambito da pianificare:

- separazione persona, organizzazione e cliente commerciale;
- entità cliente commerciale identificata dalla P.IVA;
- collegamento di più organizzazioni allo stesso cliente;
- gerarchia organizzativa annidata;
- appartenenza del collaboratore a una sola organizzazione;
- Main Admin commerciale e Admin delle singole organizzazioni;
- limiti aggregati per cliente commerciale.

**Criterio di completamento:** ogni organizzazione deve essere ricondotta senza ambiguità al cliente commerciale corretto, mantenendo distinta la persona che la rappresenta.

#### B02 — ANO-002 + ANO-004: autorizzazioni e audit

Problema centrale: il ruolo globale e i controlli attuali non rappresentano completamente i poteri effettivi delle persone nelle organizzazioni.

Ambito da pianificare:

- modello di autorizzazioni per appartenenza;
- distinzione Main Admin / Branch Admin / collaboratore;
- deleghe selettive, revocabili e tracciate;
- protezione backend indipendente dalla UI;
- separazione tra Super Admin tecnico e operatore MLS;
- audit applicativo centralizzato e consultabile;
- tracciamento delle operazioni sensibili e dei rifiuti.

**Criterio di completamento:** ogni operazione deve avere un'autorizzazione verificabile e un livello di tracciabilità coerente con il suo rischio.

#### B03 — ANO-003 + ANO-005: sessioni, registrazione e inviti

Problema centrale: l'identità e le appartenenze non sono ancora gestite con tutti i vincoli richiesti.

Ambito da pianificare:

- invalidazione delle sessioni dopo reset password;
- revoca effettiva delle sessioni;
- controllo dello stato utente su ogni richiesta protetta;
- gestione coerente dei dispositivi;
- inviti e accettazione atomica;
- appartenenza unica del collaboratore;
- conteggio corretto dei posti disponibili;
- gestione degli utenti sospesi;
- coerenza tra autenticazione, inviti e sessioni.

**Criterio di completamento:** nessun accesso deve sopravvivere a una revoca prevista e nessun invito deve creare appartenenze incompatibili con le regole Founder.

### P1 — Funzioni essenziali

#### B04 — ANO-008: billing e risorse commerciali

Problema centrale: il sistema economico è attualmente riferito all'agency anziché al cliente P.IVA.

Ambito da pianificare:

- subscription unica per cliente commerciale;
- rapporto coerente con Stripe Customer;
- wallet centrale;
- assegnazioni e revoche dei crediti alle filiali;
- consumi e FIFO tracciabili;
- upgrade e downgrade;
- limiti utenti e immobili aggregati;
- enforcement del limite immobili;
- grace period di sette giorni;
- notifiche giorni 1, 4 e 7;
- sospensione dal giorno 8 e riattivazione al recupero;
- disdetta volontaria distinta dall'insoluto;
- area «Amministrazione e fatturazione» B16-CC-07.

**Criterio di completamento:** subscription, crediti, fatture e limiti devono seguire il cliente commerciale, non la singola agency.

#### B05 — ANO-006: MLS e collaborazione

Problema centrale: manca il flusso collaborativo previsto dal modello Founder.

Ambito da pianificare:

- separazione Property / Listing / Mandate / Collaboration;
- condivisione sotto mandato;
- referenti e autorizzazioni;
- richiesta visita con almeno tre proposte;
- accordo e registrazione appuntamento;
- calendario;
- chat contestuale;
- mini-dossier dopo 24 ore;
- valutazione a livello di agenzia;
- gestione delle controversie;
- esclusione del Super Admin dalla normale operatività MLS.

**Criterio di completamento:** una collaborazione deve seguire il percorso autorizzato dal mandato fino alla visita e alla relativa documentazione.

#### B06 — ANO-007: documenti e fascicoli

Problema centrale: il fascicolo interno è isolato, ma manca il ciclo documentale collaborativo.

Ambito da pianificare:

- separazione originale/copia condivisa;
- autorizzazione all'invio;
- watermark destinatario/data;
- versionamento;
- audit dei download;
- allegati chat;
- archivio consultabile;
- revoca degli accessi futuri;
- conservazione delle copie già scaricate.

**Criterio di completamento:** ogni copia condivisa deve avere provenienza, destinatario, versione, autorizzazione e storia di accesso verificabili.

### P2 — Integrità e transizione

#### B07 — ANO-009: migrazione e integrità dati

Problema centrale: la migrazione verso il modello commerciale P.IVA non è certificabile con i dati locali disponibili.

Ambito da pianificare:

- inventario e riconciliazione delle organizzazioni;
- attribuzione documentata delle P.IVA;
- riconciliazione Stripe;
- riconciliazione subscription e wallet;
- ricostruzione crediti solo sulla base di movimenti dimostrabili;
- conservazione documenti e storico;
- gestione delle appartenenze storiche mancanti;
- trattamento esplicito dei casi ambigui;
- criteri di integrità pre e post eventuale migrazione.

**Criterio di completamento della pianificazione:** nessuna relazione commerciale o finanziaria deve essere ricostruita per supposizione. Ogni caso ambiguo deve avere un percorso di riconciliazione umana.

**Nota:** nessuna migrazione è compresa in questa autorizzazione di pianificazione.

---

## 3. Dipendenze e ordine logico

L'ordine non deve essere deciso soltanto dalla gravità: alcune aree non possono essere consolidate correttamente prima che le fondamenta siano definite.

### Sequenza di dipendenza

1. **B01 — Identità e cliente commerciale** — fondamento per organizzazioni, P.IVA e appartenenze.
2. **B02 — Autorizzazioni e audit** — definisce chi può agire e come si dimostra.
3. **B03 — Sessioni e inviti** — applica identità e autorizzazioni all'accesso effettivo.
4. **B04 — Billing** — dipende dal cliente commerciale e dai ruoli amministrativi.
5. **B05 + B06 — MLS e documenti** — dipendono da identità, appartenenze, autorizzazioni e audit.
6. **B07 — Migrazione** — dipende dal modello definitivo e dalla riconciliazione commerciale e finanziaria.
7. **Collaudo integrato successivo** — dovrà verificare i flussi risanati, senza confonderlo con la fotografia statica già chiusa.

La sequenza è una proposta di dipendenza tecnica, non una nuova decisione Founder. B05 e B06 possono essere progettati in modo coordinato, ma non vanno considerati indipendenti dalle autorizzazioni.

---

## 4. Rischi trasversali da non perdere

| Rischio                     | Aree coinvolte         | Conseguenza                                                  |
| --------------------------- | ---------------------- | ------------------------------------------------------------ |
| Identità commerciale errata | ANO-001, 008, 009      | Subscription, crediti e dati attribuiti al cliente sbagliato |
| Autorizzazioni incoerenti   | ANO-002, 003, 004, 005 | Accessi non autorizzati o non revocabili                     |
| Storico incompleto          | ANO-004, 005, 007, 009 | Impossibilità di ricostruire operazioni e responsabilità     |
| Disallineamento tra sistemi | ANO-006, 007, 008, 009 | Gestionale, MLS, documenti e billing non coerenti            |

**Precisazione su ANO-009:** la migrazione è collocata per ultima nella sequenza, ma non è un problema di gravità secondaria. È un rischio elevato che non può essere affrontato seriamente prima di avere definito e consolidato il modello di destinazione.

---

## 5. Condizioni obbligatorie prima di considerare chiuso un blocco

Ogni futura attività di risanamento dovrà avere:

1. Perimetro funzionale esplicito.
2. Decisioni Founder applicabili già individuate.
3. Evidenze del comportamento precedente.
4. Criteri di accettazione verificabili.
5. Test previsti e risultati documentati.
6. Controllo delle regressioni sulle aree dipendenti.
7. Conferma che i dati storici siano preservati.
8. Verifica read-only finale del repository.
9. Distinzione tra completato, parziale e non verificabile.

Non sarà sufficiente che Cursor dichiari di aver completato una modifica: dovrà dimostrare il comportamento richiesto.

---

## 6. Cosa rimane fuori da questa autorizzazione

- Codice e test modificati.
- Migrazioni MongoDB.
- Modifiche a Stripe.
- Patch e PR.
- Deploy e produzione.
- Riconciliazione effettiva di dati finanziari.
- Esecuzione di nuovi audit già acquisiti.
- Collaudo mutativo.

La pianificazione non autorizza automaticamente nessuna di queste attività.

---

## 7. Stato della FASE 2

| Elemento                 | Stato                 |
| ------------------------ | --------------------- |
| ANO-001…009              | Ricondotti al backlog |
| Gravità                  | Classificata          |
| Dipendenze               | Definite              |
| Criteri di completamento | Proposti              |
| Implementazione          | Non autorizzata       |
| Migrazione               | Non autorizzata       |
| PR                       | Non autorizzate       |

**Raccomandazione:** non partire da MLS o da interventi isolati sul billing. La prima fondamentale area da affrontare, quando sarà autorizzata l'esecuzione, sarà il modello persona–organizzazione–cliente commerciale.

Non nasce alcuna nuova decisione Founder e non viene aggiornato alcun registro.

**Backlog di pianificazione elaborato. Nessuna esecuzione avviata.**

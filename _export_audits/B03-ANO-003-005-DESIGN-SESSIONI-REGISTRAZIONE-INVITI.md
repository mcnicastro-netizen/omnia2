# B03 — ANO-003 (+ ANO-005): Design sessioni, registrazione e inviti

**Design B03 elaborato · Solo progettazione — nessun codice**

**Data:** 17 novembre 2026  
**Perimetro:** sessioni, registrazione, verifica email e inviti.  
**Vincoli:** B01 e B02 acquisiti integralmente. Nessuna loro riapertura. B04–B07 esclusi.  
**Baseline storica verifica:** `main` @ `2fea64a` (FASE 1).  

Riferimenti: `B01-ANO-001-CHIUSURA-DEFINITIVA-DESIGN.md`, `B02-ANO-002-004-CHIUSURA-DEFINITIVA-DESIGN.md`, `FASE-2-BACKLOG-PIANIFICAZIONE-RISANAMENTO.md`, D-173.

---

## 1. Identità e registrazione

- `User` rappresenta l'account di autenticazione.
- `Person` rappresenta la persona anagrafica: viene creata solo quando sono disponibili dati sufficienti, mai inventata.
- La registrazione crea un `User`, senza creare automaticamente una `Person` incompleta.
- La verifica dell'indirizzo email è necessaria prima di attivare le funzionalità operative che richiedono un'identità verificata.
- La registrazione non attribuisce automaticamente ruoli, Membership o accessi a organizzazioni.

**Principio:** avere un account non significa appartenere automaticamente a un'organizzazione.

---

## 2. Sessioni

Ogni sessione deve essere identificabile e revocabile individualmente.

Modello proposto:

- Access token di durata limitata.
- Refresh token gestito e conservato lato server, con rotazione a ogni rinnovo.
- Identificativo univoco della sessione.
- Tracciabilità di creazione, rinnovo, scadenza e revoca.
- Possibilità di revocare una singola sessione o tutte le sessioni dell'account.

Invalidazione obbligatoria:

- Logout: revoca della sessione interessata.
- Cambio password o reset password: invalidazione di tutte le sessioni.
- Sospensione dell'account: blocco delle sessioni operative.
- Revoca di sicurezza: invalidazione delle sessioni coinvolte.
- Revoca o perdita della Membership: rivalutazione immediata dell'autorizzazione; nessuna sessione può mantenere privilegi non più validi.

La sessione non costituisce mai una fonte autonoma di autorizzazione: a ogni richiesta il backend deve applicare le regole B02.

---

## 3. Inviti

L'invito è una procedura di ingresso in un'organizzazione, non una registrazione alternativa e non una concessione permanente di privilegi.

Flusso proposto:

1. Un soggetto autorizzato crea l'invito, indicando destinatario, organizzazione, ruolo previsto e scope consentito.
2. Il sistema genera un token casuale, non prevedibile, con scadenza e utilizzo singolo.
3. L'invito viene inviato all'indirizzo email del destinatario.
4. Il destinatario verifica l'email e accetta l'invito.
5. Il backend verifica nuovamente validità, scadenza, revoca, destinatario e poteri dell'invitante.
6. In un'unica operazione atomica vengono completati accettazione dell'invito e creazione/attivazione della Membership.
7. Viene registrato l'esito nell'audit B02.

Se il destinatario non possiede ancora un account, la registrazione deve precedere il completamento dell'accettazione, mantenendo il collegamento all'invito originario.

---

## 4. Regole inderogabili

- Un invito non può attribuire privilegi superiori a quelli posseduti dall'invitante.
- Il ruolo e lo scope sono espliciti: niente privilegi impliciti.
- Inviti scaduti, revocati o già utilizzati non sono accettabili.
- L'accettazione deve essere atomica e idempotente: doppie richieste o richieste concorrenti non devono creare Membership duplicate.
- Il destinatario deve corrispondere all'identità email verificata prevista dall'invito.
- Un collaboratore può avere una sola Membership operativa attiva alla volta, secondo B01.
- L'invito non crea automaticamente una Representation.
- La revoca di un invito non equivale alla revoca di una Membership già attiva.
- Gli eventi rilevanti, compresi i tentativi negati, sono registrati secondo B02.

---

## 5. Audit e tracciabilità

Eventi minimi da registrare:

| Area          | Eventi                                                                                      |
| ------------- | ------------------------------------------------------------------------------------------- |
| Registrazione | account creato, verifica email richiesta e completata, tentativi falliti                    |
| Sessioni      | login, rinnovo, logout, revoca, scadenza, reset password                                    |
| Inviti        | creato, inviato, reinviato, accettato, rifiutato, scaduto, revocato                         |
| Sicurezza     | token non valido, destinatario non corrispondente, accettazione negata, tentativi duplicati |

L'audit deve rispettare B02: eventi append-only, attore, timestamp, risorsa, esito e motivo; mai password, token o segreti in chiaro.

---

## 6. Allineamento alle lacune già rilevate (Blocco 3 — non nuova verifica)

Il design B03 copre, a livello progettuale, gli scostamenti già acquisiti in ANO-003 / ANO-005:

| Lacuna già nota | Copertura design B03 |
| --- | --- |
| Access token non revocabile fino a scadenza | Sessione identificabile + rivalutazione B02; invalidazione sessioni su eventi critici |
| Reset/cambio password senza revoca refresh | Invalidazione di tutte le sessioni |
| `is_active` non controllato su ogni richiesta | Sospensione → blocco sessioni operative + B02 |
| Accept invite senza `store_refresh` / race seat | Accettazione atomica + re-check poteri/limiti |
| Multi-membership via `agency_ids` | Una sola Membership operativa attiva |
| Email verify assente / non gate | Verifica email prima di funzionalità operative |

---

## 7. Esito del design

**B03 — Perimetro progettuale completato (proposta).**

Il design individua:

- identità e registrazione separate dall'appartenenza organizzativa;
- sessioni revocabili e invalidabili;
- inviti con destinatario verificato, scadenza e utilizzo singolo;
- accettazione atomica;
- autorizzazioni sempre subordinate a B02;
- audit coerente con B02.

**Classificazione dello stato:**

- B01 e B02: decisioni Founder già approvate, non riaperte.
- B03: design proposto ed elaborato in questa fase.
- Nuove decisioni Founder B03: nessuna formalmente approvata (fino a chiusura Founder).
- Verifica tecnica sul repository: non ripetuta in questa fase (baseline già acquisita).
- Implementazione: non autorizzata e non eseguita.

**B04–B07 restano chiusi.**

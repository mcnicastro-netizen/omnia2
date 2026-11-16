# OMNIA — B02
## DESIGN AUTORIZZAZIONI E AUDIT

**Versione:** 1.0 — Design  
**Data:** 16 novembre 2026  
**Baseline tecnica di riferimento:** `main` @ `2fea64a`  
**Dipendenze:** B01 — ANO-001, design definitivamente chiuso  
**Perimetro:** ANO-002 — Autorizzazioni e ruoli; ANO-004 — Audit e tracciabilità.  
**Stato:** progettazione. Nessuna implementazione autorizzata.

Riferimenti: `B01-ANO-001-DESIGN-MODELLO-DATI-TARGET.md`, `B01-ANO-001-CHIUSURA-DEFINITIVA-DESIGN.md`, `FASE-2-BACKLOG-PIANIFICAZIONE-RISANAMENTO.md`.

---

# 1. Obiettivo

B02 deve definire un sistema coerente di autorizzazioni e tracciabilità per OMNIA.

Il sistema deve rispondere in modo verificabile a cinque domande:

1. Chi sta eseguendo l'operazione?
2. Per conto di quale organizzazione o cliente commerciale?
3. Quale potere gli consente di eseguirla?
4. Su quali dati e risorse può operare?
5. Chi può ricostruire successivamente cosa è successo?

L'obiettivo non è aggiungere semplicemente altri ruoli al sistema attuale.

È necessario separare:

- identità dell'account;
- appartenenza operativa;
- ruolo;
- capability;
- ambito di applicazione;
- delega;
- autorizzazione cross-organizzazione;
- tracciabilità delle operazioni.

Il sistema deve impedire che un ruolo globale, un'appartenenza a un gruppo o la visibilità di una schermata siano interpretati come autorizzazione sufficiente.

---

# 2. Vincoli Founder e dipendenze da B01

Questi requisiti sono vincolanti e non vengono rimessi in discussione.

| ID      | Vincolo                                                                          |
| ------- | -------------------------------------------------------------------------------- |
| B02-C01 | Person e User restano distinti                                                   |
| B02-C02 | Un User può esistere senza Person                                                |
| B02-C03 | Owner, Main Admin e Branch Admin sono concetti distinti                          |
| B02-C04 | La stessa persona può ricoprire più ruoli, senza fonderli                        |
| B02-C05 | Membership e Representation sono distinte                                        |
| B02-C06 | Una sola Membership operativa attiva                                             |
| B02-C07 | Representation non crea Membership                                               |
| B02-C08 | Ogni organizzazione ha un proprio Admin                                          |
| B02-C09 | La gerarchia organizzativa è annidata e non limitata a un solo livello           |
| B02-C10 | Il cliente commerciale è identificato dalla P.IVA                                |
| B02-C11 | Un gruppo/franchising non equivale a un cliente commerciale                      |
| B02-C12 | Accessi tra organizzazioni soltanto espliciti, selettivi, revocabili e tracciati |
| B02-C13 | Nessuna delega può attribuire poteri superiori a quelli del delegante            |

Una persona che sia contemporaneamente Owner, Main Admin e Branch Admin mantiene tre relazioni funzionali distinte. Il sistema deve verificare il potere utilizzato in base all'operazione e al relativo ambito.

---

# 3. Diagnosi dello stato attuale

Dalle evidenze già acquisite per ANO-002 e ANO-004 (baseline Blocchi 1–7, non nuova verifica):

- i ruoli sono prevalentemente contenuti in `users.role`;
- sono presenti ruoli come `super_admin`, `agency_admin`, `agent`, `client`, `student`, `group_admin`, `branch_admin`, `branch_agent`;
- `require_roles` costituisce il principale meccanismo di controllo;
- esistono alias e sovrapposizioni tra ruoli;
- `active_agency_id` definisce il contesto operativo corrente;
- il controllo tenant è presente in diverse aree, ma non costituisce una garanzia universale;
- il frontend replica alcune condizioni di accesso, ma la visibilità frontend non è sicurezza;
- esistono autorizzazioni cross-agency specifiche per MLS;
- non esiste una matrice generale di capability;
- non esiste un sistema uniforme di delega e prevenzione dell'escalation;
- Super Admin è ammesso in numerosi endpoint MLS;
- non esiste un audit log applicativo unificato;
- le registrazioni degli eventi sono distribuite in più collezioni;
- attori, timestamp, esiti, motivazioni e correlazioni non sono uniformi;
- alcuni eventi di accesso negato non vengono registrati;
- la consultazione degli eventi da parte di Admin e Super Admin è frammentaria.

---

# 4. Modello autorizzativo target

## 4.1 Principio fondamentale

L'autorizzazione non deve dipendere da un singolo campo `role`.

Ogni richiesta deve essere valutata attraverso una combinazione di:

- identità autenticata;
- stato dell'account;
- contesto operativo;
- Membership attiva, quando richiesta;
- ruolo nel contesto;
- capability necessaria;
- ambito della risorsa;
- eventuale delega;
- eventuale autorizzazione cross-organizzazione;
- stato operativo dell'organizzazione e del cliente commerciale.

Regola generale: **Accesso consentito solo se tutti i controlli obbligatori per quella specifica operazione sono superati.**

## 4.2 Entità e concetti autorizzativi

### A. Role

Definisce una funzione organizzativa. Esempi: Owner; Main Admin; Admin dell'organizzazione / Branch Admin; collaboratore; ruoli operativi specialistici.

Il ruolo identifica una funzione, non un'autorizzazione universale.

**Nota di allineamento B01:** «Admin dell'organizzazione» e «Branch Admin» sono lo stesso concetto operativo a livello organizzazione (Admin della singola org/filiale). Non introdurre un quarto ruolo admin generico distinto senza decisione Founder.

### B. Capability

Definisce una singola capacità operativa (es. `organization.manage`, `membership.invite`, `billing.manage`, `property.read`, `document.share`, `audit.read`, `mls.collaboration.manage`).

L'elenco iniziale non è la matrice definitiva.

### C. RoleCapability

Associa un ruolo alle capability consentite, con `scope_type`, `policy_version`, `status`. Matrice centralizzata e versionata.

### D. AuthorizationContext

Contesto backend della richiesta: `user_id`, `organization_id`, `commercial_customer_id`, `membership_id`, `effective_role`, `requested_capability`, `resource_type`, `resource_id`, `authorization_source`.

### E. Delegation

Concessione esplicita e limitata di poteri. Vincoli: esplicita; capability; scope; stato; revoca; traccia; non supera i poteri del delegante; non agira isolamento org; non crea Membership; non ri-delega oltre i poteri ricevuti.

### F. CrossOrganizationGrant

Autorizzazione esplicita tra organizzazioni. Distinta dai grant MLS di dominio. Nessuna apertura automatica dell'intero CRM.

---

# 5. Regole per i ruoli principali

## 5.1 Owner

Titolare giuridico/commerciale dell'organizzazione. Non acquisisce automaticamente Main Admin, Branch Admin, Super Admin, né accesso a ogni org del gruppo.

## 5.2 Main Admin

Riferimento amministrativo del **cliente commerciale** (P.IVA): subscription, wallet, assegnazioni, dati commerciali aggregati.

**Non** acquisisce automaticamente accesso ai contenuti CRM di tutte le organizzazioni.

## 5.3 / 5.4 Admin organizzazione = Branch Admin

Admin della singola organizzazione. Non diventa Main Admin. Non estende poteri alle altre org solo perché condividono P.IVA.

## 5.5 Collaboratore

Opera sulla Membership attiva. Representation non conferisce accesso operativo automatico.

## 5.6 Super Admin

Ruolo tecnico di piattaforma. Non operatore ordinario MLS/org. Accesso straordinario motivato, limitato, tracciato. Nessun accesso a password/segreti in chiaro.

---

# 6. Motore di autorizzazione

Flusso: autenticare → stato account → contesto → Membership se richiesta → ruolo/capability → ambito risorsa → delega → CrossOrganizationGrant → controlli dominio → allow/deny → audit.

**Deny by default.** Backend autorità definitiva. Gerarchia senza ereditarietà automatica CRM. Stessa P.IVA ≠ scorciatoia isolamento.

---

# 7. Modello audit target

Fonte centrale proposta: `audit_events` (append-only applicativo).

Campi chiave: event_id, occurred_at, actor_*, organization_id, commercial_customer_id, action, resource_*, capability, authorization_source, outcome (success|denied|failed), reason_code, request_id, correlation_id, snapshot selettive, metadata non sensibili.

Niente password, token, segreti.

Eventi obbligatori: identità/appartenenza, autorizzazioni (incluse deny), operazioni amministrative, accessi dati rilevanti (download, share, export, cross-org, Super Admin).

---

# 8. Consultazione audit

- Admin org: eventi della propria organizzazione.
- Main Admin: eventi commerciali del proprio cliente; non CRM generalizzato.
- Super Admin: vista piattaforma giustificata e tracciata.
- UI: filtri tempo/attore/org/azione/esito; export controllato.
- Retention: per categoria, non periodo unico arbitrario in questo design.

---

# 9. Audit centrale vs log di dominio

Logger tecnico ≠ audit applicativo ≠ storico dominio ≠ ledger. Fonti esistenti (`consent_events`, `mls_events`, `al_audit`, ledgers, ecc.) restano collegabili, non sostituite senza criterio.

---

# 10. Rischi progettuali

B02-RSK-01…12: ruolo globale universale; cross-tenant; escalation delega; confusione Main/Branch; Super Admin come MLS; frontend-as-security; deny non loggati; audit modificabile; segreti nei log; correlazione; oversharing audit; confusione log/audit.

---

# 11. Criteri di accettazione

B02-AC01…AC16 (autorizzazioni) e B02-AC17…AC30 (audit). Il design non prova l'implementazione.

---

# 12. Dipendenze e confini

B02 usa B01 senza modificarlo. B03–B07 dipendono da B02 ma non sono aperti.

---

# 13. Questioni tecniche pre-implementazione (non decisioni Founder)

1. Matrice completa Role → Capability → Scope.
2. Capability assegnabili solo via ruolo vs dirette.
3. Precedenza Membership / delega / grant.
4. Delega se il delegante perde poteri.
5. Versioning storico matrice.
6. Dettaglio snapshot.
7. Retention e protezione infrastrutturale audit.
8. Accesso straordinario Super Admin.
9. Correlazione audit ↔ storici dominio.
10. Eventi automatici/integrazioni.

---

# 14. Confini

Comprende modello, regole, audit, criteri. Non comprende codice, migrazioni, PR, middleware, API, frontend, test mutativi, deploy, design B03–B07.

---

# 15. Stato

**B02 — DESIGN PRODOTTO.** B01 non riaperto. Codice non scritto. B03–B07 non aperti.

## Punti critici da validare Founder

1. Main Admin commerciale ≠ accesso automatico CRM filiali.
2. Delega: capability + scope + periodo + anti-escalation.
3. Audit: anche `denied` e operazioni Super Admin.

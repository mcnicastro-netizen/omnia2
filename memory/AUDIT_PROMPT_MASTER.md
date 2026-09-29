# AUDIT LOGICO, ARCHITETTURALE E FUNZIONALE DI OMNIA

> **Prompt master** (Founder · 28-Set-2026).  
> Documento **vincolante** per ogni sessione di audit.  
> **Non perdere** · **non riprendere l’esecuzione** finché il Founder non dice «vai».  
> Progresso sessione: `memory/AUDIT_ARCHITETTURA_NOTE.md` · backlog `A-035`.

---

## Ruolo

Agisci come **Senior Software Architect + Product Architect + Security Reviewer + SaaS/Cloud Systems Engineer**.

Devi analizzare il progetto **OMNIA**, un gestionale cloud SaaS per agenzie immobiliari.

L'obiettivo principale **NON è fare una code review tradizionale** e non è giudicare lo stile del codice.

Voglio capire se:

* la logica applicativa costruita finora è corretta;
* il modello concettuale è coerente;
* le decisioni architetturali prese finora hanno senso;
* esistono casi limite non gestiti;
* mancano componenti fondamentali;
* alcune funzionalità sono state progettate in modo che potrebbero creare problemi più avanti;
* il comportamento tecnico del sistema è coerente con ciò che il prodotto promette commercialmente;
* il sistema può crescere senza generare costi, problemi di sicurezza o complessità ingestibili.

In altre parole:

> **non voglio sapere soltanto se il codice funziona. Voglio sapere se stiamo costruendo il prodotto nel modo giusto.**

---

## Regola pratica (Founder)

* **Non** dare tutto il progetto e chiedere subito il verdetto finale.
* Analizzare **progressivamente**, un blocco alla volta, aggiornando un **“OMNIA Architecture Audit”** (`AUDIT_ARCHITETTURA_NOTE.md`) a ogni blocco.
* Verificare che le conclusioni sulle diverse parti **non si contraddicano**.
* **Niente fix codice** finché non richiesto esplicitamente («vai» di implementazione, distinto dal «vai» sul prossimo blocco).
* **Nessuna classificazione P0–P3 definitiva** finché non si è visto abbastanza del sistema (punto 23 del prompt — tipicamente a fine percorso o quando il Founder lo chiede).
* Se qualcosa non è chiaro: **non inventare** → `"Informazione non determinabile dal codice analizzato."`
* SoT codice: GitHub `mcnicastro-netizen/omnia2` (D-087).

---

## Indice punti (1–27)

| # | Titolo |
|---|--------|
| 1 | Prima fase: comprendi il sistema |
| 2 | Modello concettuale |
| 3 | Multi-tenancy |
| 4 | Autenticazione e autorizzazione |
| 5 | Lifecycle delle entità |
| 6 | Cestino |
| 7 | Media e file |
| 8 | Storage e costi |
| 9 | Backup |
| 10 | Restore |
| 11 | Backup vs cestino |
| 12 | Retention e cancellazione |
| 13 | GDPR e privacy |
| 14 | Concorrenza e race conditions |
| 15 | Job asincroni e automazioni |
| 16 | Osservabilità |
| 17 | API e frontend |
| 18 | Error handling |
| 19 | Scalabilità |
| 20 | Coerenza tra prodotto e tecnologia |
| 21 | Analisi dei casi limite |
| 22 | Debito architetturale |
| 23 | Priorità (P0–P3) |
| 24 | Non una lista infinita di problemi |
| 25 | Formato della risposta (report A–K) |
| 26 | Regola fondamentale (SaaS commerciale reale) |
| 27 | Non modificare subito il codice |

---

## Mappa sessione già svolta ↔ questo indice

| Sessione | Punto master | Note |
|----------|--------------|------|
| P1 Architettura | **§1** | Acquisito |
| P2 Modello | **§2** | Approvato |
| P3 Multi-tenancy | **§3** | Acquisito · finding aperti |
| P4 AuthN/AuthZ | **§4** | Acquisito · finding aperti |
| P5 Lifecycle + D-094 | **§5** (+ pezzi §6) | Acquisito · D-094 |
| P6 Proiezioni / D-094 | **fuori indice** | **ACQUISITO** · E-* |
| P7 Media | **§7** | **ACQUISITO** · D-095 · M-* |
| P8 Jobs | **§15** (anticipato) | **ACQUISITO** · J-* · decisioni purge/trusted aperte |
| P9 Storage e costi | **§8** | **ACQUISITO** · C-* · listino fermo |
| P10 Backup | **§9** | **ACQUISITO** · B-* · pesante/incompleto · €0,04 non confermare |
| P11 Restore | **§10** | **ACQUISITO** · **D-096** · agency-first · Bak+Restore insieme |
| P12 Backup vs Cestino | **§11** | Consegnato · BC-* / T-* (feedback) |
| — | **§6 Cestino** | Parziale P5 + coperto in P12 |
| — | **§12 Retention** | **Prossimo naturale** tipico dopo feedback P12 |
| — | **§13–§14, §16–§27** | Non avviati |

**Regola numerazione**: mantenere il continuum di sessione; documentare la corrispondenza qui / in `AUDIT_ARCHITETTURA_NOTE.md` — non riallineare artificialmente i numeri.

Decisioni di dominio già registrate (codice ⏳): **D-094**, **D-095**, **D-096**.

---

## 1. PRIMA FASE: COMPRENDI IL SISTEMA

Prima di proporre modifiche, ricostruisci mentalmente e poi descrivi:

* struttura generale dell'applicazione;
* architettura;
* componenti principali;
* database;
* entità principali;
* relazioni;
* autenticazione;
* autorizzazioni;
* gestione dei file;
* servizi esterni;
* job asincroni;
* queue;
* cron;
* storage;
* eventuali CDN;
* API;
* meccanismi di logging;
* gestione degli errori.

Non dare per scontato che l'architettura sia corretta.  
Ricostruisci prima **come funziona realmente** sulla base del progetto.  
Se qualcosa non è chiaro, non inventare. Segnalalo esplicitamente come:

> "Informazione non determinabile dal codice analizzato."

---

## 2. MODELLO CONCETTUALE

Analizza se il modello dati rappresenta correttamente il dominio.

In particolare analizza:

* Agenzia · Utente · Ruolo · Permessi · Immobile · Cliente/contatto · Documento · Foto · Video · File · Cestino · Backup · Versione/storico · eventuali altre entità.

Per ogni entità verifica: responsabilità; ownership; relazioni; lifecycle; identificazione; cancellazione; ripristino; dipendenze; duplicazioni; concetti accorpati impropriamente.

Domanda:

> "Il modello dati rappresenta realmente il concetto di business che OMNIA sta cercando di implementare?"

---

## 3. MULTI-TENANCY

Verifica che i dati di un'agenzia siano sempre isolati da quelli delle altre.

Analizza: query; repository; API; servizi; accesso ai file; URL; ID pubblici; job asincroni; cron; backup; restore; operazioni amministrative; ricerca; filtri; export; endpoint speciali.

Non limitarti a verificare che normalmente venga usato `agency_id`.  
Cerca scenari in cui un parametro, un ID o un job possa bypassare l'isolamento.

> "Esiste anche un solo percorso realistico attraverso cui un utente dell'Agenzia A potrebbe accedere, modificare, cancellare o ripristinare dati dell'Agenzia B?"

Se sì → problema critico.

---

## 4. AUTENTICAZIONE E AUTORIZZAZIONE

### Authentication — Chi è l'utente?  
### Authorization — Cosa può fare?

Verifica: ruoli; permessi; admin; utenti normali; super-admin; accesso risorse; operazioni distruttive; ripristino; file; dati sensibili; escalation.

Cerca autorizzazioni implicite o controlli **solo frontend**.

> **Il frontend non deve mai essere considerato un confine di sicurezza.**

---

## 5. LIFECYCLE DELLE ENTITÀ

Ricostruisci il ciclo di vita delle principali entità.  
Analizza se gli stati sono completi, coerenti, mutuamente compatibili, reversibili/irreversibili quando devono esserlo.  
Cerca stati impossibili (es. eliminato ma media attivi; DB senza file; file senza ref).

---

## 6. CESTINO

Verifica: cosa viene eliminato/mantenuto/ripristinato; 30 giorni; eliminazione automatica; relazioni; media; documenti; clienti; cascades; concorrenza; race.

> "Il ripristino ricrea realmente lo stato precedente oppure soltanto il record principale?"

---

## 7. MEDIA E FILE

Analizza separatamente: fotografie; PDF; documenti; video; altri file.  
Per ciascuno: upload; storage; naming; metadata; dimensione; MIME; validazione; accesso; download; preview; thumbnail; cancellazione; ripristino; duplicazione; versioning; processing asincrono.  
Casi: upload a metà; DB vs file inconsistenti; video enormi; molti file; storage down.

---

## 8. STORAGE E COSTI

Non solo correttezza tecnica: **sostenibilità economica**.

Piani di riferimento:

* Starter €49 — max 30 immobili  
* Pro €99 — max 200 immobili  
* Agency €299 — immobili illimitati  

Focus media/video.  
> "Il costo infrastrutturale per cliente è prevedibile?"  
Segnala componenti che trasformano un cliente €299/mese in un costo di centinaia di euro/mese per OMNIA.

---

## 9. BACKUP

Sistema indipendente. Cosa viene salvato (DB, file, foto, video, documenti, config, metadata, oggetti esterni).  
Frequenza; retention; versioning; incremental/full; storage; isolamento; cifratura; accesso; monitoring; failure; retry; integrità; restore.

> "Se perdiamo completamente DB e/o storage principale, possiamo realmente ricostruire l'agenzia?"

Non accettare solo: "Abbiamo il backup."

---

## 10. RESTORE

Funzionalità distinta dal backup.  
Completo / parziale / singolo immobile / singoli file / agenzia; consistenza; conflitti; ID; relazioni.  
Scenari A–F (DB perso / file persi / entrambi / restore a metà / backup corrotto / backup incompleto).

---

## 11. BACKUP VS CESTINO

Cestino = errore utente. Backup = problema grave / disaster.  
Niente sovrapposizioni o assunzioni errate tra i due.

---

## 12. RETENTION E CANCELLAZIONE

Cancellazione applicativa; cestino 30g; backup 30g; definitiva; orphan; copie in backup; chiusura account/abbonamento/agenzia.

> "Quando un cliente chiede che i suoi dati vengano eliminati, quali copie continuano a esistere e per quanto tempo?"

---

## 13. GDPR E PRIVACY

Non consulenza legale definitiva.  
Segna: "Questo è un punto tecnico." oppure "Questo richiede validazione legale/DPO."  
Non inventare obblighi giuridici.

---

## 14. CONCORRENZA E RACE CONDITIONS

Operazioni simultanee; idempotenza; locking; transazioni; consistency; duplicate jobs; retry.

---

## 15. JOB ASINCRONI E AUTOMAZIONI

Per ogni job: idempotenza; retry; timeout; failure; dead-letter; monitoring; duplicazione; ordine; dipendenze.  
> "Se eseguito due volte?" · "Se zero volte, come ce ne accorgiamo?"

---

## 16. OSSERVABILITÀ

Log; errori; audit trail; metriche; alert; stato backup/upload/job/storage/restore.

---

## 17. API E FRONTEND

Coerenza FE ↔ API ↔ BE ↔ DB.  
Controlli solo FE; endpoint chiamabili bypassando UI.

---

## 18. ERROR HANDLING

Cosa è completato / fallito / ritentabile / azione utente — non solo "Errore."

---

## 19. SCALABILITÀ

10 → 100 → 1.000 → 10.000 agenzie.  
Niente benchmark inventati. Colli di bottiglia potenziali.

---

## 20. COERENZA TRA PRODOTTO E TECNOLOGIA

Marketing/commerciale vs capacità architetturale (es. "immobili illimitati" ≠ storage illimitato).

---

## 21. ANALISI DEI CASI LIMITE

Lista edge case (felici e non). Aggiungere casi rilevanti oltre agli esempi del prompt.

---

## 22. DEBITO ARCHITETTURALE

Classificare: **OK** · **Monitorare** · **Migliorare** · **Critico**.  
Non proporre riscritture automatiche.

---

## 23. PRIORITÀ

P0 Bloccante · P1 Critico · P2 Importante · P3 Miglioramento.  
Solo impatto prodotto, non stile codice.

---

## 24. NON UNA LISTA INFINITA

Distinguere: problema reale · rischio potenziale · miglioramento opzionale · preferenza architetturale.  
Se qualcosa è corretto, dirlo.

---

## 25. FORMATO DELLA RISPOSTA (report finale)

A. Executive summary (10–15 punti)  
B. Mappa architettura attuale  
C. Modello di dominio  
D. Flussi principali  
E. Problemi (tabella ID | Area | Problema | Impatto | Priorità | Evidenza | Soluzione)  
F. Cose che funzionano bene  
G. Cose mancanti  
H. Rischi futuri  
I. Piano di intervento (pre-prod · 100 · 1.000 · dopo)  
J. Architettura consigliata (evolutiva, non rewrite se evitabile)  
K. Decisioni da prendere  

---

## 26. REGOLA FONDAMENTALE

Ragionare come SaaS commerciale reale: correttezza · sicurezza · affidabilità · costi · scalabilità · UX · manutenzione · operatività · coerenza commerciale.  
Non ottimizzare una dimensione ignorando le altre.

---

## 27. NON MODIFICARE SUBITO IL CODICE

1. analizza · 2. ricostruisci · 3. individua · 4. spiega perché · 5. alternative · 6. priorità.  
Solo dopo, se richiesto → codice.

Per ogni problema:

> **cosa succede oggi → perché è un problema → in quale scenario emerge → comportamento corretto → alternative → quale consigli e perché.**

---

## OBIETTIVO FINALE

Rispondere con sicurezza a:

> **"Se continuo a costruire OMNIA seguendo l'architettura attuale, sto costruendo una base solida oppure sto accumulando problemi che esploderanno più avanti?"**

E:

> **"Quali sono le 5-10 cose che dovrei sistemare ADESSO prima di continuare a sviluppare?"**

Non impressionare con complessità.  
**Proteggere il progetto** da errori architetturali, logici, economici e di sicurezza costosi da scoprire dopo.

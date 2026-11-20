# OMNIA — Documentazione completa audit E2E (pacchetto revisione Founder)

Questo file unisce integralmente i sei documenti originali dell'audit E2E, nell'ordine di consegna.
Baseline dichiarata nei documenti: `main` @ `759d628` · Ambiente: Dogfood CONTINUITY `omnia_df_clean_c4`.
Nessuna riscrittura dei contenuti originali: solo concatenazione con separatori.


================================================================================
## DOCUMENTO ORIGINALE: `E2E-INDICE-FOUNDER.md`
================================================================================

# Indice Founder — Audit E2E OMNIA

**Data:** 20 novembre 2026 (Europe/Rome)  
**Baseline:** main @ 759d628  
**Ambiente:** Dogfood CONTINUITY omnia_df_clean_c4

## Le due copie
1. **`E2E-FOUNDER-GUIDA-COMPLETA.md`** — linguaggio semplice.
2. **`E2E-CONTROLLO-TECNICO-COMPLETO.md`** — stesse funzioni, stessi codici, prove.

## Altri documenti
- `E2E-REGISTRO-ANOMALIE.md`
- `E2E-COPERTURA-MATRIX.md`
- `E2E-GTM-VERIFICA.md`
- Grezzi: `E2E-INTEGRALE-*`

## Legenda stati
| Stato | Significato |
|-------|-------------|
| SUPERATO | Provato e conforme |
| PARZIALE | Solo una parte |
| FALLITO | Provato e non conforme |
| BLOCCATO | Impedimento concreto |
| NON ESEGUITO | Non fatto |
| NON VERIFICATO | Prove insufficienti |

## Ordine di lettura
1. Verità commerciale (inizio Guida Founder)
2. `CRM-04`, `BILL-02`, `DEV-02`, `DEV-03`, `UI-01`
3. Anomalie A-007, A-006, A-002, A-004
4. Resto area per area, confrontando ogni codice con la copia tecnica

## Conteggio
- Schede: **49**
- Stati: `{'PARZIALE': 35, 'NON_ESEGUITO': 5, 'BLOCCATO': 5, 'FALLITO': 2, 'NON_VERIFICATO': 2}`
- UI inventariata non cliccata: **1411**

## Fuori perimetro
Academy e Customer Support: non aperti.


================================================================================
## DOCUMENTO ORIGINALE: `E2E-FOUNDER-GUIDA-COMPLETA.md`
================================================================================

# OMNIA — Guida completa audit E2E (COPIA FOUNDER)

**A chi è destinata:** al proprietario di OMNIA, senza bisogno di linguaggio da sviluppatore.  
**Baseline:** main @ 759d628  
**Ambiente di prova:** Dogfood CONTINUITY omnia_df_clean_c4  
**Data sintesi:** 20 novembre 2026 (Europe/Rome)  
**Copia gemella tecnica:** `E2E-CONTROLLO-TECNICO-COMPLETO.md` (stessi codici funzione).  
**Regola:** nessuna correzione prodotto in questo lavoro; solo verità sulle prove.

## Come leggere questa guida
- Ogni funzione ha un **codice** (es. `CRM-04`) uguale nella copia tecnica.
- Stati possibili: **SUPERATO**, **PARZIALE**, **FALLITO**, **BLOCCATO**, **NON ESEGUITO**, **NON VERIFICATO**.
- Aver trovato una funzione nel prodotto non significa che sia collaudata.
- Aver collaudato il collegamento tecnico (API) non significa aver collaudato i pulsanti a schermo.
- L'interfaccia grafica **non** è stata cliccata in automatico in questa campagna (limite della piattaforma di collaudo). Quindi i pulsanti restano in gran parte **NON ESEGUITI** a schermo.

## Verità commerciale in una frase
OMNIA mostra pezzi di ecosistema che si parlano (gestionale ↔ portale ↔ collaborazioni), ma **non** è dimostrabile come prodotto completo pronto da vendere a un'agenzia pagante: elenco immobili rotto sui dati storici, pagamenti non collaudati, API per sviluppatori bloccate, interfaccia non certificata.

## Quadro stati (funzioni schedate qui)
- **BLOCCATO:** 5
- **FALLITO:** 2
- **NON ESEGUITO:** 5
- **NON VERIFICATO:** 2
- **PARZIALE:** 35

Totale schede funzione: **49** (più inventario UI di 1411 elementi non cliccati).

---

# A. Accesso e utenti

### ACC-01 — Login agenzia
**Area:** A. Accesso e utenti  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Permette a un utente dell'agenzia di entrare nel gestionale con email e password.
2. **A cosa serve:** Senza accesso nessuno può lavorare su clienti e immobili.
3. **Esempio concreto:** Luca, titolare della sede, al mattino entra con email e password e arriva alla sua area di lavoro.
4. **Che cosa abbiamo provato:** Accesso con account di prova della sede e della filiale Nord; poi uscita.
5. **Che cosa è successo:** Accesso riuscito. Dopo l'uscita i dati riservati non erano più leggibili senza nuovo accesso.
6. **Che cosa manca:** Prova del login cliccando nella schermata del browser.
7. **Conseguenza commerciale:** Si entra e si lavora sugli account collaudati; manca la prova a schermo.
8. **Giudizio finale:** Parzialmente pronta: ingresso ok in prova tecnica, interfaccia non certificata.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### ACC-02 — Logout
**Area:** A. Accesso e utenti  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Chiude la sessione così nessuno usa l'account lasciato aperto.
2. **A cosa serve:** Sicurezza in ufficio e su postazioni condivise.
3. **Esempio concreto:** Sara esce dall'account prima di lasciare la postazione.
4. **Che cosa abbiamo provato:** Uscita e tentativo di rileggere i dati personali.
5. **Che cosa è successo:** Dopo l'uscita i dati riservati non erano accessibili.
6. **Che cosa manca:** Prova del pulsante Esci nell'interfaccia.
7. **Conseguenza commerciale:** Meccanismo ok; manca prova del pulsante.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### ACC-03 — Registrazione utente privato (ImmobilCloud)
**Area:** A. Accesso e utenti  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Un privato crea un account per cercare case o pubblicare il proprio immobile.
2. **A cosa serve:** Alimenta il portale e porta contatti alle agenzie.
3. **Esempio concreto:** Un proprietario crea l'account, accetta privacy e indica che vuole vendere.
4. **Che cosa abbiamo provato:** Registrazione con dati finti, consenso, conferma età e intenti.
5. **Che cosa è successo:** Account creato; senza consenso o senza intenti il sistema rifiuta correttamente.
6. **Che cosa manca:** Verifica email completa e prova del modulo a schermo.
7. **Conseguenza commerciale:** Iscrizione base ok in prova; verifica email non chiusa.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### ACC-04 — Recupero password
**Area:** A. Accesso e utenti  
**Stato:** NON ESEGUITO

1. **Che cosa dovrebbe fare:** Reset della password se dimenticata.
2. **A cosa serve:** Altrimenti l'utente resta fuori.
3. **Esempio concreto:** Un collaboratore usa Password dimenticata.
4. **Che cosa abbiamo provato:** Solo presenza pagina/API in inventario; ciclo email non completato.
5. **Che cosa è successo:** Non collaudato dall'inizio alla fine.
6. **Che cosa manca:** Invio email di prova e conferma reset.
7. **Conseguenza commerciale:** Non promettere recupero password come collaudato.
8. **Giudizio finale:** Non eseguita.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Non abbiamo prove sufficienti per dirlo.

### ACC-05 — Inviti collaboratori
**Area:** A. Accesso e utenti  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Il titolare invita un collega con un link controllato.
2. **A cosa serve:** Onboarding agenti senza accessi fuori controllo.
3. **Esempio concreto:** Luca invita un collaboratore nella sede.
4. **Che cosa abbiamo provato:** Verifica invito fasullo; ciclo completo non chiuso (account collaboratore di prova non accessibile).
5. **Che cosa è successo:** Invito fasullo rifiutato. Login collaboratore di prova fallito.
6. **Che cosa manca:** Invito valido → accettazione → primo accesso.
7. **Conseguenza commerciale:** Onboarding collaboratori non dimostrato.
8. **Giudizio finale:** Parziale / bloccato da dati di prova.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### ACC-06 — Ruoli e permessi
**Area:** A. Accesso e utenti  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Decide chi vede e fa cosa tra sede, filiale, collaboratore e amministrazione pagamenti.
2. **A cosa serve:** Evitare accessi tra uffici o a impostazioni delicate.
3. **Esempio concreto:** La filiale Nord non apre gli immobili privati della Sede come propri.
4. **Che cosa abbiamo provato:** Accessi incrociati sede/Nord; tentativi area Founder; account Main Admin di prova.
5. **Che cosa è successo:** Immobili/documenti altrui negati; Founder negato ai non autorizzati; Main Admin di prova non è davvero Main Admin.
6. **Che cosa manca:** Matrice completa a schermo; account Main Admin di prova corretto.
7. **Conseguenza commerciale:** Separazione base ok; Main Admin non dimostrabile con i dati attuali.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.


# B. Struttura commerciale

### Piccolo dizionario
- **Cliente commerciale:** chi ha la Partita IVA e paga OMNIA (contratto/fattura).
- **Organizzazione / agenzia:** l'ufficio che lavora ogni giorno (clienti e immobili).
- **Filiale:** un altro ufficio dello stesso gruppo.
- **Main Admin:** chi amministra soldi/crediti del cliente commerciale, non necessariamente l'agente che fa le visite.

### ORG-01 — Cliente commerciale vs agenzia vs filiale
**Area:** B. Struttura commerciale  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Il cliente commerciale è chi paga (Partita IVA). L'agenzia è l'ufficio operativo. La filiale è un altro ufficio dello stesso gruppo.
2. **A cosa serve:** Fatture e crediti sul cliente commerciale; lavoro quotidiano sull'agenzia/filiale.
3. **Esempio concreto:** Bianchi Srl paga OMNIA; ha Sede Milano e Filiale Monza.
4. **Che cosa abbiamo provato:** Lettura contesto acquisto/storage; creazione gruppo e collegamento sede.
5. **Che cosa è successo:** Modello presente; wallet spesso non operativo; acquisti bloccati da H4.
6. **Che cosa manca:** Ciclo fatturazione/crediti su cliente commerciale operativo.
7. **Conseguenza commerciale:** Modello chiaro; ciclo soldi non dimostrabile.
8. **Giudizio finale:** Presente ma non vendibile come ciclo amministrativo completo.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### ORG-02 — Gruppo e filiali
**Area:** B. Struttura commerciale  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Collega più sedi sotto lo stesso gruppo.
2. **A cosa serve:** Network multi-ufficio con amministrazione di gruppo.
3. **Esempio concreto:** Creo il gruppo e aggancio la Sede come filiale.
4. **Che cosa abbiamo provato:** Creazione gruppo e attacco branch.
5. **Che cosa è successo:** Riuscito; effetto collaterale: ruolo utente sede diventato admin di gruppo nei dati di prova.
6. **Che cosa manca:** Creazione agenzia con dati fiscali completi; UI gruppo; Main Admin di gruppo.
7. **Conseguenza commerciale:** Base multi-sede esiste; onboarding completo no.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### ORG-03 — Main Admin
**Area:** B. Struttura commerciale  
**Stato:** BLOCCATO

1. **Che cosa dovrebbe fare:** Chi amministra soldi/crediti del cliente commerciale.
2. **A cosa serve:** Controllo economico separato dal lavoro agente.
3. **Esempio concreto:** Giulia come Main Admin vede il wallet centrale.
4. **Che cosa abbiamo provato:** Login account Main Admin di prova e chiamate wallet.
5. **Che cosa è successo:** Account di prova non è Main Admin reale; operazioni incomplete.
6. **Che cosa manca:** Fixture corretta o nomina reale collaudata.
7. **Conseguenza commerciale:** Percorso Main Admin non dimostrabile.
8. **Giudizio finale:** Non pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ No.


# C. Gestionale ImmoWeb

### CRM-01 — Dashboard
**Area:** C. Gestionale ImmoWeb  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Schermata iniziale con sintesi attività.
2. **A cosa serve:** Priorità della giornata.
3. **Esempio concreto:** Luca vede gli indicatori della sua organizzazione.
4. **Che cosa abbiamo provato:** Lettura indicatori autenticata.
5. **Che cosa è successo:** Risposta corretta e veloce.
6. **Che cosa manca:** Verifica visuale widget/pulsanti.
7. **Conseguenza commerciale:** Dati ok; schermo non certificato.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### CRM-02 — Anagrafica clienti
**Area:** C. Gestionale ImmoWeb  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Rubrica acquirenti/venditori con note e attività.
2. **A cosa serve:** Cuore del lavoro agente.
3. **Esempio concreto:** Creo un acquirente e gli collego una richiesta.
4. **Che cosa abbiamo provato:** Creazione/lettura/modifica/lista; contatto portale → cliente.
5. **Che cosa è successo:** Operazioni ok; contatto portale visibile in rubrica.
6. **Che cosa manca:** Import e UI completa.
7. **Conseguenza commerciale:** Nucleo clienti utilizzabile in prova tecnica.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### CRM-03 — Immobili — creazione e modifica
**Area:** C. Gestionale ImmoWeb  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Scheda immobile (prezzo, mq, città, stato).
2. **A cosa serve:** Base di mandato e pubblicazione.
3. **Esempio concreto:** Inserisco un trilocale e lo attivo.
4. **Che cosa abbiamo provato:** Creazione, modifica, attivazione.
5. **Che cosa è successo:** Ok; attivo compare in ricerca portale.
6. **Che cosa manca:** Upload foto collaudato; UI form.
7. **Conseguenza commerciale:** Creare/attivare funziona in prova tecnica.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### CRM-04 — Elenco immobili
**Area:** C. Gestionale ImmoWeb  
**Stato:** FALLITO

1. **Che cosa dovrebbe fare:** Tabella di tutti gli immobili dell'agenzia.
2. **A cosa serve:** Schermata quotidiana del portafoglio.
3. **Esempio concreto:** Apro Immobili e scorro tutto il portafoglio.
4. **Che cosa abbiamo provato:** Liste con varie dimensioni pagina, anche con schede vecchie incomplete.
5. **Che cosa è successo:** Con poche righe ok; con schede storiche incomplete la lista va in errore server.
6. **Che cosa manca:** Correzione prodotto e ricollaudo (fuori da questo audit).
7. **Conseguenza commerciale:** Rischio concreto di non aprire l'elenco: problema grave.
8. **Giudizio finale:** Non pronta finché A-007 è aperto.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ No.

### CRM-05 — Richieste e matching
**Area:** C. Gestionale ImmoWeb  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** La richiesta descrive cosa cerca il cliente; il matching propone immobili.
2. **A cosa serve:** Riduce tempo tra esigenza e proposta.
3. **Esempio concreto:** Bilocale Milano fino a 400.000 € → elenco punteggi.
4. **Che cosa abbiamo provato:** Creazione richiesta; match per richiesta/cliente/immobile; lead-score.
5. **Che cosa è successo:** Percorsi tecnici ok; matching globale evitata (troppo pesante in passato).
6. **Che cosa manca:** UI; prova su grandi volumi in modo sicuro.
7. **Conseguenza commerciale:** Nucleo matching ok; non stress-testato.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### CRM-06 — Attività / agenda
**Area:** C. Gestionale ImmoWeb  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Note, chiamate, scadenze sui clienti.
2. **A cosa serve:** Follow-up commerciale.
3. **Esempio concreto:** Promemoria richiamare Rossi.
4. **Che cosa abbiamo provato:** Creazione e lista; osservazione doppio invio.
5. **Che cosa è successo:** Creazione ok; doppio invio può duplicare.
6. **Che cosa manca:** UI calendario; protezione doppio click.
7. **Conseguenza commerciale:** Base utile; rischio duplicati.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### CRM-07 — Pubblicazione / multiposting / wizard
**Area:** C. Gestionale ImmoWeb  
**Stato:** NON VERIFICATO

1. **Che cosa dovrebbe fare:** Collegare OMNIA ai portali o al sito agenzia per pubblicare.
2. **A cosa serve:** Portare gli annunci dove cercano i clienti.
3. **Esempio concreto:** Collegare un portale e sincronizzare.
4. **Che cosa abbiamo provato:** Lettura cataloghi; nessuna sync reale.
5. **Che cosa è successo:** Cataloghi rispondono; connessioni di prova assenti; sync non eseguita.
6. **Che cosa manca:** Connessione sandbox + sync + UI wizard.
7. **Conseguenza commerciale:** Multiposting non collaudato verso portali.
8. **Giudizio finale:** Non verificata operativamente.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Non abbiamo prove sufficienti per dirlo.


# D. ImmobilCloud B2C

### CLD-01 — Ricerca e scheda immobile
**Area:** D. ImmobilCloud B2C  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Il privato cerca case e apre la scheda.
2. **A cosa serve:** Vetrina pubblica.
3. **Esempio concreto:** Filtro Milano e apro un annuncio.
4. **Che cosa abbiamo provato:** Ricerca, filtri, facets, dettaglio.
5. **Che cosa è successo:** Funziona; catalogo di prova magro ma coerente.
6. **Che cosa manca:** UI browser; dataset ampio.
7. **Conseguenza commerciale:** Ricerca base ok; esperienza vetrina non certificata a schermo.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### CLD-02 — Preferiti e ricerche salvate
**Area:** D. ImmobilCloud B2C  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Salvare annunci e ricerche.
2. **A cosa serve:** Far tornare l'acquirente.
3. **Esempio concreto:** Salvo filtro Milano e un preferito.
4. **Che cosa abbiamo provato:** Creazione preferito e ricerca salvata; liste.
5. **Che cosa è successo:** Ok.
6. **Che cosa manca:** Notifiche complete; UI.
7. **Conseguenza commerciale:** Funzioni base presenti.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### CLD-03 — Contatto annuncio → lead in agenzia
**Area:** D. ImmobilCloud B2C  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Il privato scrive sull'annuncio; l'agenzia riceve il contatto.
2. **A cosa serve:** Ponte portale → lavoro agente.
3. **Esempio concreto:** Messaggio di interesse → compare in rubrica.
4. **Che cosa abbiamo provato:** Messaggio valido e controllo clienti.
5. **Che cosa è successo:** Lead creato e cliente visibile.
6. **Che cosa manca:** UI form; email agente.
7. **Conseguenza commerciale:** Ponte dimostrato in prova tecnica.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### CLD-04 — Annuncio del proprietario privato
**Area:** D. ImmobilCloud B2C  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Il privato pubblica e gestisce il proprio immobile.
2. **A cosa serve:** Acquisizione mandati e traffico.
3. **Esempio concreto:** Creo annuncio, aggiorno prezzo, vedo statistiche.
4. **Che cosa abbiamo provato:** Create/patch/list/stats; scout/mandati.
5. **Che cosa è successo:** Gestione ok; collegamento agenzia/mandato debole.
6. **Che cosa manca:** Ciclo privato → agenzia → mandato.
7. **Conseguenza commerciale:** Pubblicare sì; chiudere mandato no dimostrato.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### CLD-05 — Visibilità gestionale → portale
**Area:** D. ImmobilCloud B2C  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Immobile attivo in gestionale può comparire in ricerca pubblica.
2. **A cosa serve:** Un inserimento, due canali.
3. **Esempio concreto:** Attivo in gestionale → trovato in cloud search.
4. **Che cosa abbiamo provato:** Creazione active + ricerca.
5. **Che cosa è successo:** Trovato.
6. **Che cosa manca:** Matrice privacy completa; toggle UI.
7. **Conseguenza commerciale:** Collegamento base esiste.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.


# E. MLS e collaborazioni

### MLS-01 — Ciclo collaborazione
**Area:** E. MLS e collaborazioni  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Due agenzie collaborano su un immobile con autorizzazioni.
2. **A cosa serve:** Far girare mandati tra reti senza perdere controllo.
3. **Esempio concreto:** Sede propone, Nord accetta, poi si può revocare.
4. **Che cosa abbiamo provato:** Ciclo API journey 7–10.
5. **Che cosa è successo:** Create/accept senza documenti automatici; revoke con effetti su chat/download.
6. **Che cosa manca:** UI Collaborazioni.
7. **Conseguenza commerciale:** Nucleo collaborazione dimostrato in prova tecnica.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### MLS-02 — Visite e feedback post-visita
**Area:** E. MLS e collaborazioni  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Dopo la visita ufficiale si raccoglie feedback di valutazione. Non è richiesta documenti.
2. **A cosa serve:** Qualità rete e tracciabilità visite.
3. **Esempio concreto:** Visita completata → feedback; documenti solo con azione esplicita dopo.
4. **Che cosa abbiamo provato:** Visita completed; feedback; document request separata.
5. **Che cosa è successo:** Allineato alle decisioni approvate.
6. **Che cosa manca:** UI e calendari.
7. **Conseguenza commerciale:** Regole rispettate in prova tecnica.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.


# F. Deal

### DEA-01 — Percorso Deal
**Area:** F. Deal  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Filo della trattativa: interesse, proposta, risposte, esito.
2. **A cosa serve:** Non perdere lo storico commerciale.
3. **Esempio concreto:** Dopo visita si apre Deal e si invia proposta.
4. **Che cosa abbiamo provato:** Open→proposal→accept; tentativi post-revoca.
5. **Che cosa è successo:** Ciclo base ok; post-revoca alcuni errori poco chiari (A-001).
6. **Che cosa manca:** Messaggi chiari; UI Deal.
7. **Conseguenza commerciale:** Deal lavorabile; errori post-revoca opachi.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.


# G. Chat e documenti

### DOC-01 — Chat contestuale
**Area:** G. Chat e documenti  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Messaggi legati a collaborazione/visita.
2. **A cosa serve:** Contesto e prove sul mandato condiviso.
3. **Esempio concreto:** Chat visita solo tra partecipanti.
4. **Che cosa abbiamo provato:** Scope chat; deny dopo revoca.
5. **Che cosa è successo:** Scope ok; dopo revoca accesso non attivo.
6. **Che cosa manca:** UI chat.
7. **Conseguenza commerciale:** Regole accesso dimostrate in prova tecnica.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### DOC-02 — Documenti richiesti + watermark
**Area:** G. Chat e documenti  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Richiesta esplicita documenti; download con marchio.
2. **A cosa serve:** Condividere atti con tracciabilità.
3. **Esempio concreto:** Dopo interesse si chiedono documenti; partner scarica PDF marchiato.
4. **Che cosa abbiamo provato:** Request, fulfill, download, deny post-revoke.
5. **Che cosa è successo:** Flusso ok; watermark fail-closed; qualità visiva su PDF strani limitata (A-005).
6. **Che cosa manca:** UI; batteria PDF reali.
7. **Conseguenza commerciale:** Condivisione collaborativa dimostrata in prova tecnica.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.


# H. Strumenti

### TOOL-01 — Valutatore immobiliare
**Area:** H. Strumenti  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Stima orientativa (città, mq, tipologia).
2. **A cosa serve:** Primo colloquio con proprietario/acquirente.
3. **Esempio concreto:** Quanto vale un bilocale a Milano?
4. **Che cosa abbiamo provato:** Chiamata autenticata.
5. **Che cosa è successo:** Risposta ok.
6. **Che cosa manca:** UI; eventuale PDF a pagamento.
7. **Conseguenza commerciale:** Stima base funzionante in prova.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### TOOL-02 — Mutui (confronto)
**Area:** H. Strumenti  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Simula/confronta scenari di mutuo.
2. **A cosa serve:** Supporto in trattativa.
3. **Esempio concreto:** 350k, anticipo 70k, 25 anni.
4. **Che cosa abbiamo provato:** Compare con parametri corretti.
5. **Che cosa è successo:** Risposta coerente.
6. **Che cosa manca:** UI; lead mutuo.
7. **Conseguenza commerciale:** Motore ok.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### TOOL-03 — Modulistica
**Area:** H. Strumenti  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Genera documenti da modelli (es. proposta d'acquisto).
2. **A cosa serve:** Standardizzare la carta in agenzia.
3. **Esempio concreto:** Genero proposta irrevocabile su un immobile.
4. **Che cosa abbiamo provato:** Lista modelli e generazione.
5. **Che cosa è successo:** Generazione riuscita.
6. **Che cosa manca:** Firma reale; UI completa.
7. **Conseguenza commerciale:** Generazione base ok.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### TOOL-04 — Firma elettronica
**Area:** H. Strumenti  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Far firmare documenti a distanza.
2. **A cosa serve:** Chiudere proposte senza carta fisica.
3. **Esempio concreto:** Invio proposta in firma al cliente.
4. **Che cosa abbiamo provato:** Stato servizio firma.
5. **Che cosa è successo:** Solo simulazione locale, non provider reale.
6. **Che cosa manca:** Provider reale/sandbox e ciclo completo.
7. **Conseguenza commerciale:** Non vendibile come firma vera.
8. **Giudizio finale:** Non pronta (simulazione).

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### TOOL-05 — Fascicolo / paperless
**Area:** H. Strumenti  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Raccoglie documenti immobile e segnala mancanze.
2. **A cosa serve:** Checklist verso rogito.
3. **Esempio concreto:** Analyze: mancano APE e altri atti.
4. **Che cosa abbiamo provato:** Apertura fascicolo e analyze.
5. **Che cosa è successo:** Elenco mancanze restituito.
6. **Che cosa manca:** Upload UI; APE search completo.
7. **Conseguenza commerciale:** Utile come checklist; non fascicolo completo collaudato.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### TOOL-06 — APE / visure (OpenAPI.it)
**Area:** H. Strumenti  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Documenti catastali/APE da servizio esterno.
2. **A cosa serve:** Due diligence più veloce.
3. **Esempio concreto:** Ping ambiente di test fornitore.
4. **Che cosa abbiamo provato:** Status docs + ping; ricerca APE.
5. **Che cosa è successo:** Ping sandbox ok; ricerca APE non abilitata/end-to-end.
6. **Che cosa manca:** Flusso APE completo.
7. **Conseguenza commerciale:** Collegamento test sì; prodotto APE no dimostrato.
8. **Giudizio finale:** Parziale / non pronta come servizio completo.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### TOOL-07 — Virtual staging
**Area:** H. Strumenti  
**Stato:** NON ESEGUITO

1. **Che cosa dovrebbe fare:** Arreda virtualmente foto di immobili vuoti.
2. **A cosa serve:** Annunci più attraenti.
3. **Esempio concreto:** Foto salotto vuoto → variante arredata.
4. **Che cosa abbiamo provato:** Stili/storico/crediti; nessuna generate (costo).
5. **Che cosa è successo:** Stili ok; crediti bloccati; generate non eseguita.
6. **Che cosa manca:** Generate in sandbox autorizzata.
7. **Conseguenza commerciale:** Risultato staging non dimostrabile.
8. **Giudizio finale:** Non eseguita sul risultato finale.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Non abbiamo prove sufficienti per dirlo.

### TOOL-08 — HAL / assistente AI e legale
**Area:** H. Strumenti  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Assistente domande procedure/agenzia/legale.
2. **A cosa serve:** Supporto rapido all'agente.
3. **Esempio concreto:** Cosa deve contenere un contratto di mediazione?
4. **Che cosa abbiamo provato:** Status knowledge; ask; chat AL/legal.
5. **Che cosa è successo:** Status ok; molte risposte AI occupato; legal health ok.
6. **Che cosa manca:** Stabilità sotto carico; UI.
7. **Conseguenza commerciale:** Non affidabile come sempre disponibile.
8. **Giudizio finale:** Parziale / instabile.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.


# I. Piattaforma sviluppatori

### DEV-01 — Gestione chiavi API
**Area:** I. Piattaforma sviluppatori  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Creare, mostrare una volta, mascherare, ruotare e revocare chiavi per software esterni.
2. **A cosa serve:** Collegare il sito agenzia a OMNIA.
3. **Esempio concreto:** Lo sviluppatore crea la chiave, la copia, poi la revoca se serve.
4. **Che cosa abbiamo provato:** Ciclo gestione chiavi (senza pubblicare segreti).
5. **Che cosa è successo:** Creazione, maschera, usage, rotazione, revoca ok.
6. **Che cosa manca:** Portale sviluppatori e onboarding guidato; UI.
7. **Conseguenza commerciale:** Attrezzi chiave ok; non bastano a vendere una piattaforma API.
8. **Giudizio finale:** Gestione chiavi parziale; piattaforma no.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### DEV-02 — API pubbliche /api/v1
**Area:** I. Piattaforma sviluppatori  
**Stato:** BLOCCATO

1. **Che cosa dovrebbe fare:** Porte per software esterni (salute, profilo chiave, servizi a consumo).
2. **A cosa serve:** Integrare OMNIA senza usare l'interfaccia agenzia.
3. **Esempio concreto:** Il sito agenzia chiama OMNIA con la chiave.
4. **Che cosa abbiamo provato:** Senza chiave, chiave sbagliata, valida, revocata.
5. **Che cosa è successo:** Blocchi corretti su assente/sbagliata/revocata. Chiave valida bloccata da A-006 (agenzia inattiva incoerente).
6. **Che cosa manca:** Fix A-006 e ricollaudo servizi; documentazione dedicata.
7. **Conseguenza commerciale:** Non promettere API esterne funzionanti oggi.
8. **Giudizio finale:** Non pronta commercialmente.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ No.

### DEV-03 — Sandbox sviluppatori
**Area:** I. Piattaforma sviluppatori  
**Stato:** FALLITO

1. **Che cosa dovrebbe fare:** Ambiente di prova separato da dati e chiavi reali.
2. **A cosa serve:** Standard di mercato per vendere API.
3. **Esempio concreto:** Chiave di test distinta; dati finti; reset.
4. **Che cosa abbiamo provato:** Ricerca sandbox/prefissi test/tenant dedicati.
5. **Che cosa è successo:** Assente; chiavi solo con prefisso da ambiente reale.
6. **Che cosa manca:** Progettazione sandbox (fuori audit).
7. **Conseguenza commerciale:** Offerta developer non matura.
8. **Giudizio finale:** Non pronta / assente.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ No.


# J. Provider esterni

### PROV-01 — Stripe
**Area:** J. Provider esterni  
**Stato:** BLOCCATO

1. **Che cosa dovrebbe fare:** Incassa abbonamenti e acquisti con carta.
2. **A cosa serve:** Senza pagamenti non c'è SaaS vendibile.
3. **Esempio concreto:** Compra storage extra con carta di test.
4. **Che cosa abbiamo provato:** Presenza chiave test; tentativi acquisto; niente LIVE; H4 chiuso.
5. **Che cosa è successo:** Chiavi test presenti; acquisto completo non eseguibile.
6. **Che cosa manca:** H4 autorizzato + acquisto TEST con ledger.
7. **Conseguenza commerciale:** Pagamenti non dichiarabili funzionanti.
8. **Giudizio finale:** Bloccato / non pronto.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ No.

### PROV-02 — Resend (email)
**Area:** J. Provider esterni  
**Stato:** NON ESEGUITO

1. **Che cosa dovrebbe fare:** Invio email automatiche.
2. **A cosa serve:** Inviti, reset, lead.
3. **Esempio concreto:** Email invito collaboratore.
4. **Che cosa abbiamo provato:** Solo presenza chiave; nessun invio deliberato.
5. **Che cosa è successo:** Configurata; non collaudata.
6. **Che cosa manca:** Invio sandbox.
7. **Conseguenza commerciale:** Non certificata.
8. **Giudizio finale:** Non eseguita.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Non abbiamo prove sufficienti per dirlo.

### PROV-03 — Gemini (AI)
**Area:** J. Provider esterni  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Motore AI per assistenti.
2. **A cosa serve:** HAL/legal/agent.
3. **Esempio concreto:** Domanda legale all'assistente.
4. **Che cosa abbiamo provato:** Chat che usano il modello.
5. **Che cosa è successo:** Spesso occupato; health legale ok.
6. **Che cosa manca:** Stabilità.
7. **Conseguenza commerciale:** AI non affidabile sotto carico osservato.
8. **Giudizio finale:** Parziale / instabile.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### PROV-04 — fal.ai
**Area:** J. Provider esterni  
**Stato:** NON ESEGUITO

1. **Che cosa dovrebbe fare:** Genera immagini/video AI.
2. **A cosa serve:** Staging e video.
3. **Esempio concreto:** Render staging a crediti.
4. **Che cosa abbiamo provato:** Nessuna generate (costo).
5. **Che cosa è successo:** Non eseguita.
6. **Che cosa manca:** Sandbox autorizzata.
7. **Conseguenza commerciale:** Non dimostrabile.
8. **Giudizio finale:** Non eseguita.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Non abbiamo prove sufficienti per dirlo.

### PROV-05 — OpenAPI.it
**Area:** J. Provider esterni  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Documenti catastali da fornitore esterno.
2. **A cosa serve:** Visure/planimetrie.
3. **Esempio concreto:** Ping ambiente test.
4. **Che cosa abbiamo provato:** Ping oauth test.
5. **Che cosa è successo:** Ok su host di test.
6. **Che cosa manca:** Ordine documento + download.
7. **Conseguenza commerciale:** Collegamento test ok; E2E documento no.
8. **Giudizio finale:** Parziale.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### PROV-06 — Tavily / firma refs / portali
**Area:** J. Provider esterni  
**Stato:** NON VERIFICATO

1. **Che cosa dovrebbe fare:** Ricerca web AI; riferimenti firma; portali annunci.
2. **A cosa serve:** Completare tool e multiposting.
3. **Esempio concreto:** Credenziali portale per sync.
4. **Che cosa abbiamo provato:** Inventario + cataloghi; esign mock.
5. **Che cosa è successo:** Presenti a catalogo/codice; non collaudati come integrazioni complete.
6. **Che cosa manca:** Test dedicati.
7. **Conseguenza commerciale:** Non promettibili chiavi in mano.
8. **Giudizio finale:** Non verificato operativamente.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Non abbiamo prove sufficienti per dirlo.


# K. Abbonamenti e crediti

### BILL-01 — Piani e stato abbonamento (lettura)
**Area:** K. Abbonamenti e crediti  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Vedere listino e se c'è abbonamento attivo.
2. **A cosa serve:** Trasparenza commerciale.
3. **Esempio concreto:** Consulta piani Starter/Pro.
4. **Che cosa abbiamo provato:** Lettura plans/subscription/demo-status.
5. **Che cosa è successo:** Listino ok; nessun abbonamento attivo sul tenant di prova.
6. **Che cosa manca:** Attivazione abbonamento di test.
7. **Conseguenza commerciale:** Si vede il listino; non il ciclo di vita.
8. **Giudizio finale:** Parziale.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### BILL-02 — Acquisto crediti / storage (H4)
**Area:** K. Abbonamenti e crediti  
**Stato:** BLOCCATO

1. **Che cosa dovrebbe fare:** Pagare crediti o spazio extra.
2. **A cosa serve:** Monetizzazione consumi.
3. **Esempio concreto:** Compra spazio extra con carta di test.
4. **Che cosa abbiamo provato:** Tentativi purchase/checkout senza aprire H4 e senza LIVE.
5. **Che cosa è successo:** Bloccato. Nessun acquisto completo dimostrato. Scorciatoie Dogfood non valgono come acquisto reale.
6. **Che cosa manca:** H4 autorizzato + Stripe TEST E2E.
7. **Conseguenza commerciale:** Non vendibile come acquisto collaudato.
8. **Giudizio finale:** Bloccato — H4 non operativo ai fini GTM.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ No.

### BILL-03 — Wallet, assegnazioni, ledger, fatture
**Area:** K. Abbonamenti e crediti  
**Stato:** BLOCCATO

1. **Che cosa dovrebbe fare:** Saldo centrale, assegna crediti alle sedi, storico e fatture.
2. **A cosa serve:** Controllo economico del network.
3. **Esempio concreto:** Main Admin assegna crediti alla filiale.
4. **Che cosa abbiamo provato:** Lettura wallet; ciclo assegnazione/fatture non eseguibile.
5. **Che cosa è successo:** Wallet non operativo; MA di prova senza contesto; lifecycle bloccato.
6. **Che cosa manca:** CC operativo + MA reale + H4.
7. **Conseguenza commerciale:** Amministrazione crediti non dimostrabile.
8. **Giudizio finale:** Non pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ No.


# L. Pulsanti e azioni UI

### UI-01 — Inventario e collaudo interfaccia
**Area:** L. Pulsanti e azioni UI  
**Stato:** NON ESEGUITO

1. **Che cosa dovrebbe fare:** Tutti i pulsanti, menu e form che l'utente clicca.
2. **A cosa serve:** Si vende l'esperienza a schermo.
3. **Esempio concreto:** Clicco Salva immobile e vedo conferma.
4. **Che cosa abbiamo provato:** Inventario automatico dal codice; aperture pagina; computer-use fallito per limite piattaforma.
5. **Che cosa è successo:** 1411 elementi censiti; 0 click reali.
6. **Che cosa manca:** Collaudo browser autorizzato senza limiti.
7. **Conseguenza commerciale:** Nessuna certificazione UI.
8. **Giudizio finale:** Non eseguita a schermo.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Non abbiamo prove sufficienti per dirlo.


# M. Sicurezza

### SEC-01 — Separazione dati tra agenzie/filiali
**Area:** M. Sicurezza  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Una sede non legge i privati di un'altra come propri.
2. **A cosa serve:** Privacy e fiducia.
3. **Esempio concreto:** Nord non apre scheda esclusiva della Sede.
4. **Che cosa abbiamo provato:** GET cross-tenant; ops Founder.
5. **Che cosa è successo:** Accessi negati nei casi provati.
6. **Che cosa manca:** Matrice UI; utente sospeso; agent fixture.
7. **Conseguenza commerciale:** Isolamento base dimostrato in prova tecnica.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.

### SEC-02 — Revoche collaborazione e API key
**Area:** M. Sicurezza  
**Stato:** PARZIALE

1. **Che cosa dovrebbe fare:** Togliendo un permesso, i vecchi accessi smettono di funzionare.
2. **A cosa serve:** Fine collaborazione o chiave compromessa.
3. **Esempio concreto:** Revoco collab → niente download/chat; revoco chiave → niente API.
4. **Che cosa abbiamo provato:** Revoca collab e API key.
5. **Che cosa è successo:** Revoche efficaci; messaggi Deal post-revoca a tratti opachi (A-001).
6. **Che cosa manca:** Uniformare messaggi errore.
7. **Conseguenza commerciale:** Sicurezza sostanziale ok; chiarezza messaggi da migliorare.
8. **Giudizio finale:** Parzialmente pronta.

**Se un'agenzia pagasse domani per questa funzione, riuscirebbe a usarla senza problemi?**  
→ Solo in parte: funzionano i percorsi collaudati; restano buchi elencati nella scheda.


---
# Anomalie aperte (parole semplici)

| Codice | In pratica | Gravità | Chiusa? |
|--------|------------|---------|---------|
| A-001 | Dopo aver tolto una collaborazione, alcuni messaggi sul Deal sono poco chiari | Media | No |
| A-002 | Non riusciamo a dimostrare un acquisto completo (crediti/spazio): cancello pagamenti di prova chiuso | Alta | No |
| A-003 | Gli account di prova “Main Admin” / collaboratore non sono impostati bene | Media | No |
| A-004 | Non abbiamo potuto cliccare l'interfaccia in automatico | Info (impatto alto sul lancio) | No |
| A-005 | Il marchio sui PDF di collaborazione tiene; su file strani la resa visiva può essere limitata | Info | No |
| A-006 | Le chiavi per sviluppatori si fermano per un controllo “agenzia attiva” incoerente | Alta | No |
| A-007 | L'elenco immobili si rompe con schede vecchie incomplete | Alta | No |
| A-008 | Nei dati di prova il ruolo della sede è cambiato dopo un test sul gruppo | Info | No |

---
# Dieci problemi più importanti per un lancio
1. Elenco immobili in errore (A-007).
2. Pagamenti/crediti non dimostrati (A-002).
3. Interfaccia non collaudata (A-004 / UI-01).
4. API sviluppatori non usabili (A-006) e assenza ambiente di prova dedicato (DEV-03).
5. Firma elettronica solo simulata (TOOL-04).
6. Pubblicazione su grandi portali non collaudata (CRM-07).
7. Staging AI non dimostrato (TOOL-07).
8. Assistenti AI instabili (TOOL-08).
9. Main Admin / wallet non dimostrabili (ORG-03, BILL-03).
10. Onboarding collaboratori non chiuso (ACC-05, A-003).

---
# Cosa è più affidabile *sulle prove di oggi* (con limiti)
- Accesso sede/filiale (prova tecnica, non prova a schermo).
- Clienti, richieste e abbinamenti di base (prova tecnica).
- Creare/attivare un immobile e vederlo in ricerca sul portale (prova tecnica).
- Contatto dal portale che diventa cliente in gestionale (prova tecnica).
- Collaborazioni tra agenzie, visite, feedback e documenti con le regole già decise (prova tecnica).
- Valutatore e mutui di base; generazione modulistica di base (prova tecnica).
- Creazione e revoca chiavi per sviluppatori (prova tecnica) — non i servizi dietro la chiave.

Nessuna di queste è automaticamente “pronta da vendere” senza collaudo interfaccia e senza chiudere le anomalie alte.

---
# Cosa non dichiarare a un cliente oggi
- “Le API per sviluppatori sono pronte”.
- “Puoi comprare crediti o spazio extra senza problemi”.
- “Tutti i pulsanti sono collaudati”.
- “La firma elettronica è quella dei provider reali”.
- “Il multiposting sui grandi portali è collaudato dall'inizio alla fine”.
- “L'elenco immobili è affidabile su qualsiasi portafoglio storico”.


================================================================================
## DOCUMENTO ORIGINALE: `E2E-CONTROLLO-TECNICO-COMPLETO.md`
================================================================================

# OMNIA — Controllo tecnico completo (COPIA B)

**Baseline:** `759d628` · **DB:** `omnia_df_clean_c4` · **Env:** dogfood CONTINUITY  
**Data:** 20 novembre 2026 (Europe/Rome)  
**Copia Founder:** `E2E-FOUNDER-GUIDA-COMPLETA.md`  
**Vincoli:** no code/DB/config changes; no PR/commit; no H4 open; no LIVE payments; no secrets in clear.

## Metodo
- Evidenze da `/opt/cursor/artifacts/E2E-INTEGRALE-*`.
- Stati allineati 1:1 con la copia Founder.
- API verification ≠ UI verification.
- Inventory ≠ verified.

## Indice codici
- `ACC-01` Login agenzia — **PARZIALE**
- `ACC-02` Logout — **PARZIALE**
- `ACC-03` Registrazione utente privato (ImmobilCloud) — **PARZIALE**
- `ACC-04` Recupero password — **NON ESEGUITO**
- `ACC-05` Inviti collaboratori — **PARZIALE**
- `ACC-06` Ruoli e permessi — **PARZIALE**
- `ORG-01` Cliente commerciale vs agenzia vs filiale — **PARZIALE**
- `ORG-02` Gruppo e filiali — **PARZIALE**
- `ORG-03` Main Admin — **BLOCCATO**
- `CRM-01` Dashboard — **PARZIALE**
- `CRM-02` Anagrafica clienti — **PARZIALE**
- `CRM-03` Immobili — creazione e modifica — **PARZIALE**
- `CRM-04` Elenco immobili — **FALLITO**
- `CRM-05` Richieste e matching — **PARZIALE**
- `CRM-06` Attività / agenda — **PARZIALE**
- `CRM-07` Pubblicazione / multiposting / wizard — **NON VERIFICATO**
- `CLD-01` Ricerca e scheda immobile — **PARZIALE**
- `CLD-02` Preferiti e ricerche salvate — **PARZIALE**
- `CLD-03` Contatto annuncio → lead in agenzia — **PARZIALE**
- `CLD-04` Annuncio del proprietario privato — **PARZIALE**
- `CLD-05` Visibilità gestionale → portale — **PARZIALE**
- `MLS-01` Ciclo collaborazione — **PARZIALE**
- `MLS-02` Visite e feedback post-visita — **PARZIALE**
- `DEA-01` Percorso Deal — **PARZIALE**
- `DOC-01` Chat contestuale — **PARZIALE**
- `DOC-02` Documenti richiesti + watermark — **PARZIALE**
- `TOOL-01` Valutatore immobiliare — **PARZIALE**
- `TOOL-02` Mutui (confronto) — **PARZIALE**
- `TOOL-03` Modulistica — **PARZIALE**
- `TOOL-04` Firma elettronica — **PARZIALE**
- `TOOL-05` Fascicolo / paperless — **PARZIALE**
- `TOOL-06` APE / visure (OpenAPI.it) — **PARZIALE**
- `TOOL-07` Virtual staging — **NON ESEGUITO**
- `TOOL-08` HAL / assistente AI e legale — **PARZIALE**
- `DEV-01` Gestione chiavi API — **PARZIALE**
- `DEV-02` API pubbliche /api/v1 — **BLOCCATO**
- `DEV-03` Sandbox sviluppatori — **FALLITO**
- `PROV-01` Stripe — **BLOCCATO**
- `PROV-02` Resend (email) — **NON ESEGUITO**
- `PROV-03` Gemini (AI) — **PARZIALE**
- `PROV-04` fal.ai — **NON ESEGUITO**
- `PROV-05` OpenAPI.it — **PARZIALE**
- `PROV-06` Tavily / firma refs / portali — **NON VERIFICATO**
- `BILL-01` Piani e stato abbonamento (lettura) — **PARZIALE**
- `BILL-02` Acquisto crediti / storage (H4) — **BLOCCATO**
- `BILL-03` Wallet, assegnazioni, ledger, fatture — **BLOCCATO**
- `UI-01` Inventario e collaudo interfaccia — **NON ESEGUITO**
- `SEC-01` Separazione dati tra agenzie/filiali — **PARZIALE**
- `SEC-02` Revoche collaborazione e API key — **PARZIALE**

---

# A. Accesso e utenti

### ACC-01 — Login agenzia
**Area:** A. Accesso e utenti  
**Stato test:** PARZIALE

1. **Codice:** `ACC-01`
2. **Modulo/componente:** auth
3. **Percorso/API/UI:** `POST /api/auth/login|logout; GET /api/auth/me; UI /it/login`
4. **Comportamento atteso:** 200 + session; logout → 401 /me
5. **Test eseguito:** J1 smoke; J11-13 AUTH; PERF logout
6. **Risultato osservato:** sede/nord 200; logout 401; MA password deep; agent login FAIL
7. **Evidenze:** J1-SMOKE, J11-13 AUTH
8. **Evidenze mancanti:** UI click; MFA; email verify UX
9. **Anomalie:** A-003, A-004
10. **Gravità/impatto:** MED/INFO
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** UI click; MFA; email verify UX (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### ACC-02 — Logout
**Area:** A. Accesso e utenti  
**Stato test:** PARZIALE

1. **Codice:** `ACC-02`
2. **Modulo/componente:** auth
3. **Percorso/API/UI:** `POST /api/auth/logout`
4. **Comportamento atteso:** session invalidated
5. **Test eseguito:** PERF P-01
6. **Risultato osservato:** me 401 dopo logout
7. **Evidenze:** J11-13 P-01
8. **Evidenze mancanti:** UI
9. **Anomalie:** A-004
10. **Gravità/impatto:** INFO
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** UI (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### ACC-03 — Registrazione utente privato (ImmobilCloud)
**Area:** A. Accesso e utenti  
**Stato test:** PARZIALE

1. **Codice:** `ACC-03`
2. **Modulo/componente:** immocloud cloud-auth
3. **Percorso/API/UI:** `POST /api/cloud/auth/register`
4. **Comportamento atteso:** 200/201 con gdpr+age+intents
5. **Test eseguito:** J6 / J6X
6. **Risultato osservato:** 200; 400 senza gdpr/intents
7. **Evidenze:** J6-COMPLETE, J6X-reg
8. **Evidenze mancanti:** email verification; UI
9. **Anomalie:** A-004
10. **Gravità/impatto:** MED
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** email verification; UI (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### ACC-04 — Recupero password
**Area:** A. Accesso e utenti  
**Stato test:** NON ESEGUITO

1. **Codice:** `ACC-04`
2. **Modulo/componente:** auth
3. **Percorso/API/UI:** `forgot-password / reset-password; UI /it/forgot-password`
4. **Comportamento atteso:** email token flow
5. **Test eseguito:** NONE e2e
6. **Risultato osservato:** INVENTORIED
7. **Evidenze:** OpenAPI + FE routes
8. **Evidenze mancanti:** full flow
9. **Anomalie:** —
10. **Gravità/impatto:** MED
11. **Stato:** NON ESEGUITO
12. **Verifica per chiudere:** full flow (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### ACC-05 — Inviti collaboratori
**Area:** A. Accesso e utenti  
**Stato test:** PARZIALE

1. **Codice:** `ACC-05`
2. **Modulo/componente:** invites
3. **Percorso/API/UI:** `/api/app/agencies/me/invites; invites/verify|accept`
4. **Comportamento atteso:** invalid → 404
5. **Test eseguito:** J13-10
6. **Risultato osservato:** invite_invalid; agent 401
7. **Evidenze:** J13-10, A-003
8. **Evidenze mancanti:** happy path
9. **Anomalie:** A-003
10. **Gravità/impatto:** MED
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** happy path (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### ACC-06 — Ruoli e permessi
**Area:** A. Accesso e utenti  
**Stato test:** PARZIALE

1. **Codice:** `ACC-06`
2. **Modulo/componente:** authz
3. **Percorso/API/UI:** `ProtectedRoute + agency scope`
4. **Comportamento atteso:** 403/404 cross-tenant
5. **Test eseguito:** J13 SEC
6. **Risultato osservato:** foreign 404; ops 403; MA role=agent
7. **Evidenze:** J13 ACCOUNTS-META
8. **Evidenze mancanti:** UI role matrix
9. **Anomalie:** A-003,A-008
10. **Gravità/impatto:** HIGH MA fixture
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** UI role matrix (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)


# B. Struttura commerciale

### ORG-01 — Cliente commerciale vs agenzia vs filiale
**Area:** B. Struttura commerciale  
**Stato test:** PARZIALE

1. **Codice:** `ORG-01`
2. **Modulo/componente:** billing/commercial
3. **Percorso/API/UI:** `purchase-context; storage/usage; groups`
4. **Comportamento atteso:** CC context + wallet
5. **Test eseguito:** J2 J12
6. **Risultato osservato:** CC[]; cc_not_operable; storage ha CC id
7. **Evidenze:** J12
8. **Evidenze mancanti:** operable CC + H4
9. **Anomalie:** A-002
10. **Gravità/impatto:** HIGH
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** operable CC + H4 (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### ORG-02 — Gruppo e filiali
**Area:** B. Struttura commerciale  
**Stato test:** PARZIALE

1. **Codice:** `ORG-02`
2. **Modulo/componente:** groups
3. **Percorso/API/UI:** `POST /api/app/groups; .../branches`
4. **Comportamento atteso:** 201
5. **Test eseguito:** J2-06/07
6. **Risultato osservato:** 201; role drift A-008
7. **Evidenze:** J2
8. **Evidenze mancanti:** fiscal agency create UI
9. **Anomalie:** A-008
10. **Gravità/impatto:** INFO
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** fiscal agency create UI (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### ORG-03 — Main Admin
**Area:** B. Struttura commerciale  
**Stato test:** BLOCCATO

1. **Codice:** `ORG-03`
2. **Modulo/componente:** billing main-admin
3. **Percorso/API/UI:** `/api/billing/commercial/main-admin*`
4. **Comportamento atteso:** MA context
5. **Test eseguito:** J12-07/08
6. **Risultato osservato:** commercial_customer_context_required
7. **Evidenze:** A-003 J12
8. **Evidenze mancanti:** MA fixture + transfer E2E
9. **Anomalie:** A-003,A-002
10. **Gravità/impatto:** HIGH
11. **Stato:** BLOCCATO
12. **Verifica per chiudere:** MA fixture + transfer E2E (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)


# C. Gestionale ImmoWeb

### CRM-01 — Dashboard
**Area:** C. Gestionale ImmoWeb  
**Stato test:** PARZIALE

1. **Codice:** `CRM-01`
2. **Modulo/componente:** dashboard
3. **Percorso/API/UI:** `GET /api/app/dashboard/kpis; UI /app/dashboard`
4. **Comportamento atteso:** 200
5. **Test eseguito:** PERF
6. **Risultato osservato:** 200 ~55ms
7. **Evidenze:** J11-13
8. **Evidenze mancanti:** UI
9. **Anomalie:** A-004
10. **Gravità/impatto:** LOW
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** UI (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### CRM-02 — Anagrafica clienti
**Area:** C. Gestionale ImmoWeb  
**Stato test:** PARZIALE

1. **Codice:** `CRM-02`
2. **Modulo/componente:** clients
3. **Percorso/API/UI:** `/api/app/clients*`
4. **Comportamento atteso:** 201/200
5. **Test eseguito:** J4 X-03/04
6. **Risultato osservato:** PASS; contact hit
7. **Evidenze:** J4 XMOD
8. **Evidenze mancanti:** UI CSV
9. **Anomalie:** A-004
10. **Gravità/impatto:** LOW
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** UI CSV (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### CRM-03 — Immobili — creazione e modifica
**Area:** C. Gestionale ImmoWeb  
**Stato test:** PARZIALE

1. **Codice:** `CRM-03`
2. **Modulo/componente:** properties
3. **Percorso/API/UI:** `POST/PATCH/GET /api/app/properties`
4. **Comportamento atteso:** 201/200
5. **Test eseguito:** J3 X-01
6. **Risultato osservato:** PASS
7. **Evidenze:** J3 XMOD
8. **Evidenze mancanti:** photo UI
9. **Anomalie:** A-004
10. **Gravità/impatto:** MED
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** photo UI (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### CRM-04 — Elenco immobili
**Area:** C. Gestionale ImmoWeb  
**Stato test:** FALLITO

1. **Codice:** `CRM-04`
2. **Modulo/componente:** properties list
3. **Percorso/API/UI:** `GET /api/app/properties?page_size=`
4. **Comportamento atteso:** 200
5. **Test eseguito:** A007-ps*
6. **Risultato osservato:** ps<=2 OK; >=3 500 created_at
7. **Evidenze:** api.log properties.py:120
8. **Evidenze mancanti:** fix after fix
9. **Anomalie:** A-007
10. **Gravità/impatto:** HIGH
11. **Stato:** FALLITO
12. **Verifica per chiudere:** fix after fix (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### CRM-05 — Richieste e matching
**Area:** C. Gestionale ImmoWeb  
**Stato test:** PARZIALE

1. **Codice:** `CRM-05`
2. **Modulo/componente:** requests/matches
3. **Percorso/API/UI:** `/api/app/requests*; /matches*`
4. **Comportamento atteso:** 200
5. **Test eseguito:** J4 J5
6. **Risultato osservato:** PASS core
7. **Evidenze:** J4/J5
8. **Evidenze mancanti:** UI large-data
9. **Anomalie:** —
10. **Gravità/impatto:** MED
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** UI large-data (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### CRM-06 — Attività / agenda
**Area:** C. Gestionale ImmoWeb  
**Stato test:** PARZIALE

1. **Codice:** `CRM-06`
2. **Modulo/componente:** activities
3. **Percorso/API/UI:** `/api/app/activities`
4. **Comportamento atteso:** 201
5. **Test eseguito:** J4-06 J13-12
6. **Risultato osservato:** 201; double informational
7. **Evidenze:** J4/J13
8. **Evidenze mancanti:** UI idempotency
9. **Anomalie:** A-004
10. **Gravità/impatto:** LOW
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** UI idempotency (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### CRM-07 — Pubblicazione / multiposting / wizard
**Area:** C. Gestionale ImmoWeb  
**Stato test:** NON VERIFICATO

1. **Codice:** `CRM-07`
2. **Modulo/componente:** publishing/website
3. **Percorso/API/UI:** `/api/app/publishing/*; website/themes`
4. **Comportamento atteso:** catalog+sync
5. **Test eseguito:** J11-PUB*
6. **Risultato osservato:** catalog PASS; connections empty
7. **Evidenze:** J11
8. **Evidenze mancanti:** connection+sync
9. **Anomalie:** —
10. **Gravità/impatto:** HIGH commercial
11. **Stato:** NON VERIFICATO
12. **Verifica per chiudere:** connection+sync (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)


# D. ImmobilCloud B2C

### CLD-01 — Ricerca e scheda immobile
**Area:** D. ImmobilCloud B2C  
**Stato test:** PARZIALE

1. **Codice:** `CLD-01`
2. **Modulo/componente:** cloud search
3. **Percorso/API/UI:** `/api/cloud/search; /property/{id}; /facets`
4. **Comportamento atteso:** 200
5. **Test eseguito:** J6/J6X
6. **Risultato osservato:** PASS
7. **Evidenze:** J6X
8. **Evidenze mancanti:** UI
9. **Anomalie:** A-004
10. **Gravità/impatto:** MED
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** UI (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### CLD-02 — Preferiti e ricerche salvate
**Area:** D. ImmobilCloud B2C  
**Stato test:** PARZIALE

1. **Codice:** `CLD-02`
2. **Modulo/componente:** favorites/saved-searches
3. **Percorso/API/UI:** `/api/cloud/me/favorites*; saved-searches*`
4. **Comportamento atteso:** 201/200
5. **Test eseguito:** J6/J6X
6. **Risultato osservato:** PASS
7. **Evidenze:** J6
8. **Evidenze mancanti:** UI notify
9. **Anomalie:** A-004
10. **Gravità/impatto:** LOW
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** UI notify (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### CLD-03 — Contatto annuncio → lead in agenzia
**Area:** D. ImmobilCloud B2C  
**Stato test:** PARZIALE

1. **Codice:** `CLD-03`
2. **Modulo/componente:** cloud contact
3. **Percorso/API/UI:** `POST /api/cloud/property/{id}/contact`
4. **Comportamento atteso:** 200 lead/client
5. **Test eseguito:** X-03 X-04
6. **Risultato osservato:** PASS hit=True
7. **Evidenze:** XMOD
8. **Evidenze mancanti:** notify UI
9. **Anomalie:** A-004
10. **Gravità/impatto:** LOW
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** notify UI (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### CLD-04 — Annuncio del proprietario privato
**Area:** D. ImmobilCloud B2C  
**Stato test:** PARZIALE

1. **Codice:** `CLD-04`
2. **Modulo/componente:** private listings
3. **Percorso/API/UI:** `/api/cloud/me/properties*; scout; mandate-opportunities`
4. **Comportamento atteso:** 201 + agency link
5. **Test eseguito:** J6X
6. **Risultato osservato:** CRUD PASS; scout 404; mandates 0
7. **Evidenze:** IMMOBILCLOUD-DEEP
8. **Evidenze mancanti:** mandate path
9. **Anomalie:** —
10. **Gravità/impatto:** MED
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** mandate path (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### CLD-05 — Visibilità gestionale → portale
**Area:** D. ImmobilCloud B2C  
**Stato test:** PARZIALE

1. **Codice:** `CLD-05`
2. **Modulo/componente:** visibility
3. **Percorso/API/UI:** `is_listed_on_immobilcloud / cloud search`
4. **Comportamento atteso:** active in search
5. **Test eseguito:** X-02
6. **Risultato osservato:** found=True
7. **Evidenze:** XMOD
8. **Evidenze mancanti:** privacy UI
9. **Anomalie:** —
10. **Gravità/impatto:** LOW
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** privacy UI (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)


# E. MLS e collaborazioni

### MLS-01 — Ciclo collaborazione
**Area:** E. MLS e collaborazioni  
**Stato test:** PARZIALE

1. **Codice:** `MLS-01`
2. **Modulo/componente:** collaborations
3. **Percorso/API/UI:** `/api/app/collaborations*`
4. **Comportamento atteso:** no auto doc; revoke denies
5. **Test eseguito:** J7-10
6. **Risultato osservato:** PASS core
7. **Evidenze:** J7-10
8. **Evidenze mancanti:** UI
9. **Anomalie:** A-004
10. **Gravità/impatto:** MED
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** UI (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### MLS-02 — Visite e feedback post-visita
**Area:** E. MLS e collaborazioni  
**Stato test:** PARZIALE

1. **Codice:** `MLS-02`
2. **Modulo/componente:** visits/feedback
3. **Percorso/API/UI:** `/visits*; /visit-feedback; document-requests`
4. **Comportamento atteso:** feedback ≠ docs
5. **Test eseguito:** J8
6. **Risultato osservato:** PASS
7. **Evidenze:** J7-10
8. **Evidenze mancanti:** UI calendar
9. **Anomalie:** A-004
10. **Gravità/impatto:** LOW
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** UI calendar (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)


# F. Deal

### DEA-01 — Percorso Deal
**Area:** F. Deal  
**Stato test:** PARZIALE

1. **Codice:** `DEA-01`
2. **Modulo/componente:** deals
3. **Percorso/API/UI:** `/api/app/deals*`
4. **Comportamento atteso:** deny esplicito post-revoke
5. **Test eseguito:** J9 J13-11
6. **Risultato osservato:** cycle PASS; J9-07 404 A-001
7. **Evidenze:** J9-07
8. **Evidenze mancanti:** error taxonomy
9. **Anomalie:** A-001
10. **Gravità/impatto:** MED
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** error taxonomy (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)


# G. Chat e documenti

### DOC-01 — Chat contestuale
**Area:** G. Chat e documenti  
**Stato test:** PARZIALE

1. **Codice:** `DOC-01`
2. **Modulo/componente:** collab-chat
3. **Percorso/API/UI:** `/api/app/collab-chat/threads*`
4. **Comportamento atteso:** scope+revoke deny
5. **Test eseguito:** J10 J13-17
6. **Risultato osservato:** PASS/PARTIAL
7. **Evidenze:** J7-10
8. **Evidenze mancanti:** UI
9. **Anomalie:** A-004
10. **Gravità/impatto:** LOW
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** UI (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### DOC-02 — Documenti richiesti + watermark
**Area:** G. Chat e documenti  
**Stato test:** PARZIALE

1. **Codice:** `DOC-02`
2. **Modulo/componente:** document-requests/watermark
3. **Percorso/API/UI:** `document-requests download`
4. **Comportamento atteso:** watermarked
5. **Test eseguito:** J8
6. **Risultato osservato:** PASS fail-closed
7. **Evidenze:** J8-06 A-005
8. **Evidenze mancanti:** UI visual QA
9. **Anomalie:** A-005
10. **Gravità/impatto:** LOW
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** UI visual QA (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)


# H. Strumenti

### TOOL-01 — Valutatore immobiliare
**Area:** H. Strumenti  
**Stato test:** PARZIALE

1. **Codice:** `TOOL-01`
2. **Modulo/componente:** valuator
3. **Percorso/API/UI:** `POST /api/cloud/valuator`
4. **Comportamento atteso:** 200
5. **Test eseguito:** J11-VAL
6. **Risultato osservato:** 200
7. **Evidenze:** J11
8. **Evidenze mancanti:** UI PDF
9. **Anomalie:** —
10. **Gravità/impatto:** LOW
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** UI PDF (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### TOOL-02 — Mutui (confronto)
**Area:** H. Strumenti  
**Stato test:** PARZIALE

1. **Codice:** `TOOL-02`
2. **Modulo/componente:** mutui
3. **Percorso/API/UI:** `POST /api/cloud/mutui/compare`
4. **Comportamento atteso:** 200
5. **Test eseguito:** J11-MUT
6. **Risultato osservato:** 200
7. **Evidenze:** J11
8. **Evidenze mancanti:** UI
9. **Anomalie:** —
10. **Gravità/impatto:** LOW
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** UI (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### TOOL-03 — Modulistica
**Area:** H. Strumenti  
**Stato test:** PARZIALE

1. **Codice:** `TOOL-03`
2. **Modulo/componente:** modulistica
3. **Percorso/API/UI:** `templates + documents/generate`
4. **Comportamento atteso:** 201
5. **Test eseguito:** J11-MOD-G2
6. **Risultato osservato:** 201 slug
7. **Evidenze:** J11
8. **Evidenze mancanti:** UI esign real
9. **Anomalie:** —
10. **Gravità/impatto:** LOW
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** UI esign real (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### TOOL-04 — Firma elettronica
**Area:** H. Strumenti  
**Stato test:** PARZIALE

1. **Codice:** `TOOL-04`
2. **Modulo/componente:** esign
3. **Percorso/API/UI:** `modulistica/esign/status`
4. **Comportamento atteso:** provider ready
5. **Test eseguito:** J11-ESIGN
6. **Risultato osservato:** provider=mock
7. **Evidenze:** J11
8. **Evidenze mancanti:** real provider
9. **Anomalie:** —
10. **Gravità/impatto:** HIGH commercial
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** real provider (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### TOOL-05 — Fascicolo / paperless
**Area:** H. Strumenti  
**Stato test:** PARZIALE

1. **Codice:** `TOOL-05`
2. **Modulo/componente:** fascicolo
3. **Percorso/API/UI:** `/api/app/fascicolo/{id}*`
4. **Comportamento atteso:** 200 analysis
5. **Test eseguito:** J11-PAP*
6. **Risultato osservato:** 200 warnings
7. **Evidenze:** J11
8. **Evidenze mancanti:** uploads UI
9. **Anomalie:** —
10. **Gravità/impatto:** MED
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** uploads UI (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### TOOL-06 — APE / visure (OpenAPI.it)
**Area:** H. Strumenti  
**Stato test:** PARZIALE

1. **Codice:** `TOOL-06`
2. **Modulo/componente:** docs/openapi
3. **Percorso/API/UI:** `/api/docs/*; openapi/ping`
4. **Comportamento atteso:** enabled flows
5. **Test eseguito:** J11-APE/OAPI
6. **Risultato osservato:** ape_search_enabled false; ping PASS
7. **Evidenze:** J11 K
8. **Evidenze mancanti:** APE E2E
9. **Anomalie:** —
10. **Gravità/impatto:** MED
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** APE E2E (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### TOOL-07 — Virtual staging
**Area:** H. Strumenti  
**Stato test:** NON ESEGUITO

1. **Codice:** `TOOL-07`
2. **Modulo/componente:** staging
3. **Percorso/API/UI:** `/api/app/staging/*`
4. **Comportamento atteso:** generate job
5. **Test eseguito:** J11-STG*
6. **Risultato osservato:** styles PASS; generate NOT_EXECUTED
7. **Evidenze:** J11
8. **Evidenze mancanti:** generate
9. **Anomalie:** A-002 related
10. **Gravità/impatto:** MED
11. **Stato:** NON ESEGUITO
12. **Verifica per chiudere:** generate (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### TOOL-08 — HAL / assistente AI e legale
**Area:** H. Strumenti  
**Stato test:** PARZIALE

1. **Codice:** `TOOL-08`
2. **Modulo/componente:** hal/al/legal
3. **Percorso/API/UI:** `/hal/knowledge/*; /al/chat; /legal/*`
4. **Comportamento atteso:** 200 answers
5. **Test eseguito:** J11
6. **Risultato osservato:** llm_busy 502/503
7. **Evidenze:** J11
8. **Evidenze mancanti:** stable LLM
9. **Anomalie:** —
10. **Gravità/impatto:** MED
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** stable LLM (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)


# I. Piattaforma sviluppatori

### DEV-01 — Gestione chiavi API
**Area:** I. Piattaforma sviluppatori  
**Stato test:** PARZIALE

1. **Codice:** `DEV-01`
2. **Modulo/componente:** api-keys
3. **Percorso/API/UI:** `/api/app/api-keys*`
4. **Comportamento atteso:** plaintext once; mask; revoke
5. **Test eseguito:** DEV lifecycle
6. **Risultato osservato:** PASS create/list/mask/usage/rotate/revoke
7. **Evidenze:** J-DEVELOPER
8. **Evidenze mancanti:** UI
9. **Anomalie:** A-004
10. **Gravità/impatto:** LOW
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** UI (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### DEV-02 — API pubbliche /api/v1
**Area:** I. Piattaforma sviluppatori  
**Stato test:** BLOCCATO

1. **Codice:** `DEV-02`
2. **Modulo/componente:** v1 gateway
3. **Percorso/API/UI:** `/api/v1/* Bearer omk_live_*`
4. **Comportamento atteso:** valid key → 200
5. **Test eseguito:** V1-* A006-R
6. **Risultato osservato:** 401/403 revoked; 403 agency_inactive
7. **Evidenze:** api_key.py A-006
8. **Evidenze mancanti:** functional v1 after fix
9. **Anomalie:** A-006
10. **Gravità/impatto:** HIGH
11. **Stato:** BLOCCATO
12. **Verifica per chiudere:** functional v1 after fix (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### DEV-03 — Sandbox sviluppatori
**Area:** I. Piattaforma sviluppatori  
**Stato test:** FALLITO

1. **Codice:** `DEV-03`
2. **Modulo/componente:** developer sandbox
3. **Percorso/API/UI:** `KEY_PREFIX omk_live_ only`
4. **Comportamento atteso:** omk_test/sandbox tenant
5. **Test eseguito:** DEV-10/11
6. **Risultato osservato:** NOT FOUND
7. **Evidenze:** J-DEVELOPER
8. **Evidenze mancanti:** sandbox product
9. **Anomalie:** —
10. **Gravità/impatto:** HIGH
11. **Stato:** FALLITO
12. **Verifica per chiudere:** sandbox product (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)


# J. Provider esterni

### PROV-01 — Stripe
**Area:** J. Provider esterni  
**Stato test:** BLOCCATO

1. **Codice:** `PROV-01`
2. **Modulo/componente:** stripe
3. **Percorso/API/UI:** `STRIPE_* sk_test; /billing/*`
4. **Comportamento atteso:** TEST checkout
5. **Test eseguito:** J12 A-002
6. **Risultato osservato:** H4/CC block
7. **Evidenze:** A-002 K
8. **Evidenze mancanti:** H4+fulfill
9. **Anomalie:** A-002
10. **Gravità/impatto:** HIGH
11. **Stato:** BLOCCATO
12. **Verifica per chiudere:** H4+fulfill (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### PROV-02 — Resend (email)
**Area:** J. Provider esterni  
**Stato test:** NON ESEGUITO

1. **Codice:** `PROV-02`
2. **Modulo/componente:** resend
3. **Percorso/API/UI:** `RESEND_API_KEY`
4. **Comportamento atteso:** send
5. **Test eseguito:** NOT_EXECUTED
6. **Risultato osservato:** key present
7. **Evidenze:** K
8. **Evidenze mancanti:** send test
9. **Anomalie:** —
10. **Gravità/impatto:** MED
11. **Stato:** NON ESEGUITO
12. **Verifica per chiudere:** send test (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### PROV-03 — Gemini (AI)
**Area:** J. Provider esterni  
**Stato test:** PARZIALE

1. **Codice:** `PROV-03`
2. **Modulo/componente:** gemini
3. **Percorso/API/UI:** `GEMINI_API_KEY`
4. **Comportamento atteso:** 200
5. **Test eseguito:** J11
6. **Risultato osservato:** llm_busy
7. **Evidenze:** J11
8. **Evidenze mancanti:** stable
9. **Anomalie:** —
10. **Gravità/impatto:** MED
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** stable (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### PROV-04 — fal.ai
**Area:** J. Provider esterni  
**Stato test:** NON ESEGUITO

1. **Codice:** `PROV-04`
2. **Modulo/componente:** fal
3. **Percorso/API/UI:** `FAL_KEY`
4. **Comportamento atteso:** job
5. **Test eseguito:** NOT_EXECUTED_COST
6. **Risultato osservato:** key present
7. **Evidenze:** K
8. **Evidenze mancanti:** generate
9. **Anomalie:** —
10. **Gravità/impatto:** MED
11. **Stato:** NON ESEGUITO
12. **Verifica per chiudere:** generate (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### PROV-05 — OpenAPI.it
**Area:** J. Provider esterni  
**Stato test:** PARZIALE

1. **Codice:** `PROV-05`
2. **Modulo/componente:** openapi.it
3. **Percorso/API/UI:** `docs/openapi/ping`
4. **Comportamento atteso:** sandbox
5. **Test eseguito:** J11-OAPI
6. **Risultato osservato:** PASS test.catasto
7. **Evidenze:** K
8. **Evidenze mancanti:** full order
9. **Anomalie:** —
10. **Gravità/impatto:** MED
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** full order (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### PROV-06 — Tavily / firma refs / portali
**Area:** J. Provider esterni  
**Stato test:** NON VERIFICATO

1. **Codice:** `PROV-06`
2. **Modulo/componente:** tavily/esign/portals
3. **Percorso/API/UI:** `TAVILY; publishing; esign mock`
4. **Comportamento atteso:** varies
5. **Test eseguito:** inventory
6. **Risultato osservato:** key/catalog/mock
7. **Evidenze:** K
8. **Evidenze mancanti:** each E2E
9. **Anomalie:** —
10. **Gravità/impatto:** MED
11. **Stato:** NON VERIFICATO
12. **Verifica per chiudere:** each E2E (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)


# K. Abbonamenti e crediti

### BILL-01 — Piani e stato abbonamento (lettura)
**Area:** K. Abbonamenti e crediti  
**Stato test:** PARZIALE

1. **Codice:** `BILL-01`
2. **Modulo/componente:** billing plans
3. **Percorso/API/UI:** `/api/billing/plans|subscription|demo-status`
4. **Comportamento atteso:** 200
5. **Test eseguito:** J12
6. **Risultato osservato:** plans 200; subscription null
7. **Evidenze:** J12
8. **Evidenze mancanti:** subscribe E2E
9. **Anomalie:** A-002
10. **Gravità/impatto:** HIGH
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** subscribe E2E (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### BILL-02 — Acquisto crediti / storage (H4)
**Area:** K. Abbonamenti e crediti  
**Stato test:** BLOCCATO

1. **Codice:** `BILL-02`
2. **Modulo/componente:** billing purchase
3. **Percorso/API/UI:** `/billing/storage/purchase; /checkout`
4. **Comportamento atteso:** checkout TEST
5. **Test eseguito:** J12-09/10
6. **Risultato osservato:** blocked; no completed purchase
7. **Evidenze:** A-002
8. **Evidenze mancanti:** H4+fulfill
9. **Anomalie:** A-002
10. **Gravità/impatto:** HIGH
11. **Stato:** BLOCCATO
12. **Verifica per chiudere:** H4+fulfill (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### BILL-03 — Wallet, assegnazioni, ledger, fatture
**Area:** K. Abbonamenti e crediti  
**Stato test:** BLOCCATO

1. **Codice:** `BILL-03`
2. **Modulo/componente:** wallet
3. **Percorso/API/UI:** `/api/billing/wallet*`
4. **Comportamento atteso:** balances+transfers
5. **Test eseguito:** J12
6. **Risultato osservato:** cc_not_operable; lifecycle BLOCKED
7. **Evidenze:** J12
8. **Evidenze mancanti:** full wallet E2E
9. **Anomalie:** A-002 A-003
10. **Gravità/impatto:** HIGH
11. **Stato:** BLOCCATO
12. **Verifica per chiudere:** full wallet E2E (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)


# L. Pulsanti e azioni UI

### UI-01 — Inventario e collaudo interfaccia
**Area:** L. Pulsanti e azioni UI  
**Stato test:** NON ESEGUITO

1. **Codice:** `UI-01`
2. **Modulo/componente:** frontend
3. **Percorso/API/UI:** `frontend/src/** ; :43123`
4. **Comportamento atteso:** button outcomes
5. **Test eseguito:** static inventory + HTTP shell
6. **Risultato osservato:** 1411 INVENTORIED; 0 EXECUTED
7. **Evidenze:** B-UI-INVENTORY UI-COLLAUDO A-004
8. **Evidenze mancanti:** real UI E2E
9. **Anomalie:** A-004
10. **Gravità/impatto:** HIGH GTM
11. **Stato:** NON ESEGUITO
12. **Verifica per chiudere:** real UI E2E (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)


# M. Sicurezza

### SEC-01 — Separazione dati tra agenzie/filiali
**Area:** M. Sicurezza  
**Stato test:** PARZIALE

1. **Codice:** `SEC-01`
2. **Modulo/componente:** authz
3. **Percorso/API/UI:** `properties/fascicolo/ops`
4. **Comportamento atteso:** 403/404
5. **Test eseguito:** J13
6. **Risultato osservato:** PASS
7. **Evidenze:** J13 L-security
8. **Evidenze mancanti:** suspended user
9. **Anomalie:** A-003
10. **Gravità/impatto:** MED
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** suspended user (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)

### SEC-02 — Revoche collaborazione e API key
**Area:** M. Sicurezza  
**Stato test:** PARZIALE

1. **Codice:** `SEC-02`
2. **Modulo/componente:** revoke
3. **Percorso/API/UI:** `collaborations revoke; api-keys revoke; deals`
4. **Comportamento atteso:** deny after revoke
5. **Test eseguito:** J7-10 J13-09
6. **Risultato osservato:** key 403; A-001 opacity
7. **Evidenze:** A-001 J13
8. **Evidenze mancanti:** error taxonomy
9. **Anomalie:** A-001
10. **Gravità/impatto:** MED
11. **Stato:** PARZIALE
12. **Verifica per chiudere:** error taxonomy (+ risoluzione evidenziata delle anomalie collegate, poi ricollaudo)


---
# H4 — ricostruzione precisa (billing / A-002)

1. **Verifiche gestionale senza H4:** CRUD clienti/immobili/richieste/match; MLS/deal/docs; cloud search/contact; tools non-checkout; API key management.
2. **Percorsi alternativi Dogfood:** CONTINUITY DB + account sintetici — **non** equivalgono a checkout Stripe.
3. **Simulazioni:** esign `provider=mock`; letture billing parziali.
4. **Stripe TEST:** `sk_test` presente; **nessun** checkout+fulfillment completato evidenziato in questo audit.
5. **Acquisto crediti completo:** NON eseguito / NON evidenziato come riuscito.
6. **Acquisto storage completo:** tentato → bloccato; NON completato.
7. **Pagamento → CommercialCustomer:** NON dimostrato.
8. **Wallet/saldo post-acquisto:** NON dimostrato.
9. **Transazione registrata:** NON dimostrata per purchase reale.
10. **Cosa impedisce H4 operativo ai fini GTM:** sealed gate non autorizzato + CC non operable + fixture MA (A-003).

**Non confondere workaround Dogfood con acquisto funzionante.**


================================================================================
## DOCUMENTO ORIGINALE: `E2E-REGISTRO-ANOMALIE.md`
================================================================================

# Registro anomalie E2E (canonico)

**Campagna:** E2E INTEGRALE PRE-GTM · SHA `759d628` · 20 novembre 2026 (Europe/Rome)  
**Regola:** nessuna chiusura senza prova specifica. Nessuna correzione in questo lavoro.

## Storico attivo

### A-001 — Deal post-revoca: errore opaco
- **Founder:** Dopo aver tolto una collaborazione, alcune azioni sul Deal non spiegano bene il rifiuto.
- **Tecnico:** `POST /deals/{id}/proposals` → 404 vs deny esplicito atteso; altri path possono dare `collaboration_not_active`.
- **Impatto:** confusione utente/supporto. **Gravità:** MEDIUM. **Stato:** OPEN.
- **Evidenza:** J9-07 in `E2E-INTEGRALE-J7-10-RESULTS.json`.
- **Chiusura:** rieseguire post-revoke proposal → deny esplicito stabile + prova UI.

### A-002 — Acquisti bloccati (H4 / CC)
- **Founder:** Non dimostriamo che un'agenzia riesca a pagare crediti o spazio extra.
- **Tecnico:** purchase/checkout → H4/CC/validazione; no completed TEST purchase evidence.
- **Impatto:** monetizzazione GTM. **Gravità:** HIGH. **Stato:** OPEN.
- **Evidenza:** J12-09/10. **Chiusura:** H4 autorizzato + Stripe TEST E2E + ledger/CC.

### A-003 — Fixture Main Admin / Agent
- **Founder:** Account di prova “amministratore pagamenti” / collaboratore non sistemati.
- **Tecnico:** `giulia…` role=agent `agency_id=null`; `paolo…` login 401 vs smoke; MA wallet senza contesto CC.
- **Gravità:** MEDIUM. **Stato:** OPEN. **Evidenza:** ACCOUNTS-META, J12.
- **Chiusura:** fixture corrette + rivalidazione (senza chiudere prima).

### A-004 — UI computer-use indisponibile
- **Founder:** Non abbiamo cliccato l'interfaccia in automatico.
- **Tecnico:** computerUse spend limit; 1411 UI NOT_EXECUTED.
- **Gravità:** INFORMATIONAL (impatto GTM alto). **Stato:** OPEN.
- **Evidenza:** `E2E-INTEGRALE-UI-COLLAUDO.md`. **Chiusura:** computer-use o collaudo manuale con screenshot.

### A-005 — Watermark qualità residua
- **Founder:** Protezione download ok; resa visiva su PDF anomali limitata.
- **Tecnico:** fail-closed verificato. **Gravità:** INFORMATIONAL. **Stato:** OPEN.
- **Evidenza:** J8-06. **Chiusura:** batteria PDF reali + review visiva.

### A-006 — API key / agency_inactive
- **Founder:** Chiave valida ma servizi sviluppatori bloccati da “agenzia non attiva”, mentre il gestionale lavora.
- **Tecnico:** projection `is_active` → `{}` falsy; `activation_status=active` senza campo `is_active`; commento legacy non rispettato (`shared/auth/api_key.py`).
- **Gravità:** HIGH. **Stato:** OPEN (riconfermato). **Evidenza:** A006-R.
- **Chiusura:** fix + ricollaudo `/api/v1/me` e feed.

### A-007 — Lista immobili `created_at`
- **Founder:** Elenco immobili in errore con schede storiche incomplete.
- **Tecnico:** KeyError in `_to_list_item`; page_size≤2 OK, ≥3 500.
- **Gravità:** HIGH. **Stato:** OPEN. **Evidenza:** api.log `properties.py:120`.
- **Chiusura:** fix + test legacy page sizes/sorts.

### A-008 — Drift ruolo sede `group_admin`
- **Founder:** Dopo test gruppo, utente sede risulta admin di gruppo nei dati di prova.
- **Tecnico:** side-effect J2; auth via `active_agency_id`.
- **Gravità:** INFORMATIONAL. **Stato:** OPEN. **Evidenza:** A-ROLE.
- **Chiusura:** reset fixture o consapevolezza nei run successivi.

## Nessuna anomalia chiusa in questo pass documentale.


================================================================================
## DOCUMENTO ORIGINALE: `E2E-COPERTURA-MATRIX.md`
================================================================================

# Matrice di copertura E2E

**SHA:** `759d628` · 20 novembre 2026 (Europe/Rome)

## Funzioni schedate (Founder ↔ Tecnico)

| Codice | Funzione | Stato | UI a schermo | Anomalie |
|--------|----------|-------|--------------|----------|
| ACC-01 | Login agenzia | PARZIALE | NON ESEGUITO (A-004) | A-003, A-004 |
| ACC-02 | Logout | PARZIALE | NON ESEGUITO (A-004) | A-004 |
| ACC-03 | Registrazione utente privato (ImmobilCloud) | PARZIALE | NON ESEGUITO (A-004) | A-004 |
| ACC-04 | Recupero password | NON ESEGUITO | NON ESEGUITO (A-004) | — |
| ACC-05 | Inviti collaboratori | PARZIALE | NON ESEGUITO (A-004) | A-003 |
| ACC-06 | Ruoli e permessi | PARZIALE | NON ESEGUITO (A-004) | A-003,A-008 |
| ORG-01 | Cliente commerciale vs agenzia vs filiale | PARZIALE | NON ESEGUITO (A-004) | A-002 |
| ORG-02 | Gruppo e filiali | PARZIALE | NON ESEGUITO (A-004) | A-008 |
| ORG-03 | Main Admin | BLOCCATO | NON ESEGUITO (A-004) | A-003,A-002 |
| CRM-01 | Dashboard | PARZIALE | NON ESEGUITO (A-004) | A-004 |
| CRM-02 | Anagrafica clienti | PARZIALE | NON ESEGUITO (A-004) | A-004 |
| CRM-03 | Immobili — creazione e modifica | PARZIALE | NON ESEGUITO (A-004) | A-004 |
| CRM-04 | Elenco immobili | FALLITO | NON ESEGUITO (A-004) | A-007 |
| CRM-05 | Richieste e matching | PARZIALE | NON ESEGUITO (A-004) | — |
| CRM-06 | Attività / agenda | PARZIALE | NON ESEGUITO (A-004) | A-004 |
| CRM-07 | Pubblicazione / multiposting / wizard | NON VERIFICATO | NON ESEGUITO (A-004) | — |
| CLD-01 | Ricerca e scheda immobile | PARZIALE | NON ESEGUITO (A-004) | A-004 |
| CLD-02 | Preferiti e ricerche salvate | PARZIALE | NON ESEGUITO (A-004) | A-004 |
| CLD-03 | Contatto annuncio → lead in agenzia | PARZIALE | NON ESEGUITO (A-004) | A-004 |
| CLD-04 | Annuncio del proprietario privato | PARZIALE | NON ESEGUITO (A-004) | — |
| CLD-05 | Visibilità gestionale → portale | PARZIALE | NON ESEGUITO (A-004) | — |
| MLS-01 | Ciclo collaborazione | PARZIALE | NON ESEGUITO (A-004) | A-004 |
| MLS-02 | Visite e feedback post-visita | PARZIALE | NON ESEGUITO (A-004) | A-004 |
| DEA-01 | Percorso Deal | PARZIALE | NON ESEGUITO (A-004) | A-001 |
| DOC-01 | Chat contestuale | PARZIALE | NON ESEGUITO (A-004) | A-004 |
| DOC-02 | Documenti richiesti + watermark | PARZIALE | NON ESEGUITO (A-004) | A-005 |
| TOOL-01 | Valutatore immobiliare | PARZIALE | NON ESEGUITO (A-004) | — |
| TOOL-02 | Mutui (confronto) | PARZIALE | NON ESEGUITO (A-004) | — |
| TOOL-03 | Modulistica | PARZIALE | NON ESEGUITO (A-004) | — |
| TOOL-04 | Firma elettronica | PARZIALE | NON ESEGUITO (A-004) | — |
| TOOL-05 | Fascicolo / paperless | PARZIALE | NON ESEGUITO (A-004) | — |
| TOOL-06 | APE / visure (OpenAPI.it) | PARZIALE | NON ESEGUITO (A-004) | — |
| TOOL-07 | Virtual staging | NON ESEGUITO | NON ESEGUITO (A-004) | A-002 related |
| TOOL-08 | HAL / assistente AI e legale | PARZIALE | NON ESEGUITO (A-004) | — |
| DEV-01 | Gestione chiavi API | PARZIALE | NON ESEGUITO (A-004) | A-004 |
| DEV-02 | API pubbliche /api/v1 | BLOCCATO | NON ESEGUITO (A-004) | A-006 |
| DEV-03 | Sandbox sviluppatori | FALLITO | NON ESEGUITO (A-004) | — |
| PROV-01 | Stripe | BLOCCATO | NON ESEGUITO (A-004) | A-002 |
| PROV-02 | Resend (email) | NON ESEGUITO | NON ESEGUITO (A-004) | — |
| PROV-03 | Gemini (AI) | PARZIALE | NON ESEGUITO (A-004) | — |
| PROV-04 | fal.ai | NON ESEGUITO | NON ESEGUITO (A-004) | — |
| PROV-05 | OpenAPI.it | PARZIALE | NON ESEGUITO (A-004) | — |
| PROV-06 | Tavily / firma refs / portali | NON VERIFICATO | NON ESEGUITO (A-004) | — |
| BILL-01 | Piani e stato abbonamento (lettura) | PARZIALE | NON ESEGUITO (A-004) | A-002 |
| BILL-02 | Acquisto crediti / storage (H4) | BLOCCATO | NON ESEGUITO (A-004) | A-002 |
| BILL-03 | Wallet, assegnazioni, ledger, fatture | BLOCCATO | NON ESEGUITO (A-004) | A-002 A-003 |
| UI-01 | Inventario e collaudo interfaccia | NON ESEGUITO | NON ESEGUITO (A-004) | A-004 |
| SEC-01 | Separazione dati tra agenzie/filiali | PARZIALE | NON ESEGUITO (A-004) | A-003 |
| SEC-02 | Revoche collaborazione e API key | PARZIALE | NON ESEGUITO (A-004) | A-001 |

## Riepilogo schede
- BLOCCATO: 5
- FALLITO: 2
- NON ESEGUITO: 5
- NON VERIFICATO: 2
- PARZIALE: 35
- Totale schede: 49

## UI
- Inventariati: **1411** · Route: **89** · Click reali: **0** · Copertura UI eseguita: **0%**

## OpenAPI
- ~458 operazioni inventariate ≠ % prodotto collaudato.

## Journey (sintesi)
| Journey | Stato |
|---------|-------|
| J1 Auth | PARZIALE (API) |
| J2 Org | PARZIALE |
| J3 Immobili | FALLITO lista (A-007) / PARZIALE CRUD |
| J4–5 Clienti/Match | PARZIALE |
| J6 Cloud | PARZIALE |
| J7–10 MLS/Deal | PARZIALE (A-001) |
| J11 Tools | PARZIALE |
| J12 Billing | BLOCCATO acquisti |
| J13 Security | PARZIALE |


================================================================================
## DOCUMENTO ORIGINALE: `E2E-GTM-VERIFICA.md`
================================================================================

# Verifica preparazione GTM

**Domanda:** se un'agenzia pagasse domani, userebbe OMNIA senza problemi ingiustificati?  
**Risposta complessiva:** **NO** come piattaforma completa.

## Cosa si può raccontare con onestà (non come garanzia commerciale)
- Nuclei gestionale (clienti/richieste/match/create immobile) *con caveat* A-007 e UI non collaudata.
- Ponte portale → lead.
- Collaborazioni MLS di base (prove tecniche).

## Cosa non promettere
- Elenco immobili affidabile su storici (A-007).
- Acquisto crediti/storage/abbonamento (A-002).
- API developer + sandbox (A-006, DEV-03).
- UI collaudata (A-004).
- Firma elettronica provider reale; multiposting E2E; staging AI dimostrato; AI sempre disponibile.

## Valutazione per area
| Area | Vendibile oggi? |
|------|-----------------|
| Gestionale | NO finché A-007; nuclei sì con caveat |
| Portale | PARZIALE tecnica; UI no |
| Strumenti | PARZIALE stretta |
| API sviluppatori | NO |
| Pagamenti/provider | NO |
| MLS/Deal/docs | PARZIALE tecnica |
| Sicurezza isolamento | PARZIALE positiva |

## Priorità pre-lancio
1. A-007 lista immobili  
2. A-002 / H4 TEST autorizzato  
3. A-004 UI reale  
4. A-006 + sandbox developer  
5. A-003 fixture MA/agent  
6. Firma reale o trasparenza mock  
7. Un portale multiposting sandbox  
8. Staging generate sandbox  
9. Stabilizzare LLM  
10. A-001 errori Deal post-revoca  

## Conclusione
**Non dichiarare OMNIA pronta al lancio GTM** su questo audit.


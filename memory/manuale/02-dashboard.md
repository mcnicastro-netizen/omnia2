# Capitolo 2 · Dashboard

**Versione manuale**: v1.0 · **Ultima revisione**: Feb 2026
**Chi lo legge**: titolari, agenti, segreteria
**Prerequisiti**: aver fatto login (vedi Cap. 1)

---

## 2.1 · Cosa mi dice il pannello iniziale

**A cosa serve**
Sapere in un colpo d'occhio come sta andando la tua agenzia oggi: quanti immobili in vetrina, quanti lead da chiamare, quanti match nuovi, quali visite sono in agenda, chi lavora con te.

**Cosa vedi entrando**
Appena fai login su ImmoWeb, dopo qualche secondo di caricamento vedi:

1. **Un saluto in alto**: *"Bentornato, {tuo nome}"*.
2. **Sei riquadri (KPI)**: sei numeri chiave in una griglia da 2×3 (su desktop) o uno sotto l'altro (su cellulare).
3. **Una nota in fondo** che ricorda cosa rappresentano.

[SCREEN: cap2-dashboard-panoramica]

**Cosa NON c'è (ancora)**
La dashboard è volutamente essenziale: non ha grafici, non ha timeline, non ha notifiche cliccabili. È un **cruscotto di stato**, non un feed. Se cerchi il dettaglio di un cliente o di un immobile, apri la voce dedicata dalla barra a sinistra.

---

## 2.2 · I sei contatori (cosa significano)

I sei numeri della dashboard si aggiornano automaticamente ogni volta che apri la pagina. Sono calcolati sull'**agenzia attiva** (se sei in più agenzie, ricorda di controllare quale hai selezionato in alto a sinistra).

| # | Contatore | Cosa conta | Da dove viene |
|---|-----------|-----------|---------------|
| 1 | **Immobili attivi** | Numero di immobili in stato *Pubblicato* | Modulo Immobili |
| 2 | **Lead aperti** | Contatti in stato *Nuovo* o *Contattato* (non ancora chiusi) | Modulo Clienti + form contatto portale + widget |
| 3 | **Nuovi match (7gg)** | Match generati negli ultimi 7 giorni | Modulo Match (motore di abbinamento) |
| 4 | **Visite (7gg)** | Appuntamenti di visita nei prossimi 7 giorni | Calendario (da un modulo che verrà collegato prossimamente) |
| 5 | **Collaboratori** | Membri dell'agenzia con account attivo | Modulo Collaboratori |
| 6 | **Inviti pendenti** | Inviti spediti ma non ancora accettati | Modulo Collaboratori |

[SCREEN: cap2-dashboard-kpi-6cards]

**Nota per la segreteria**
Se il titolare ti ha ristretto i permessi, alcuni numeri possono apparire diversi da quelli che vede lui: dipende da cosa hai accesso a vedere.

---

## 2.3 · Come leggere i numeri in pratica

Non tutti i numeri servono allo stesso modo. Ecco come usarli ogni mattina:

### Immobili attivi
- **Sale**: hai acquisito nuovi mandati o riattivato annunci → controlla che tutti i portali stiano aggiornando (Cap. 8 · Portali).
- **Scende**: qualcuno si è venduto/affittato o è stato archiviato → verifica dal modulo Immobili.

### Lead aperti
- **Sale rapido**: campagna in corso, o si è messo online un annuncio molto interessante.
- **Fermo/alto per giorni**: c'è un accumulo di contatti non gestiti — vai in **Clienti** e filtra per stato *Nuovo*.

### Nuovi match (7gg)
- **Bassi**: potresti non avere abbastanza clienti registrati o le loro preferenze sono troppo strette. Vedi Cap. 4 · Clienti (paragrafo Preferenze di ricerca).
- **Alti**: motore che sta lavorando bene. Apri **Match** per vedere quali chiamare per primi (i "ROVENTI" in rosso).

### Visite (7gg)
- **Zero visite**: attenzione, la settimana rischia di essere improduttiva.
- **Molte visite**: verifica che siano assegnate al collaboratore giusto (se non tutti gli agenti hanno accesso al calendario).

### Collaboratori
Se il numero non corrisponde a chi lavora davvero con te, apri **Collaboratori** e disattiva chi è uscito.

### Inviti pendenti
Numero > 0 = c'è qualcuno che non ha ancora aperto la mail di invito. Da **Collaboratori** puoi re-inviare l'invito.

---

## 2.4 · Dopo la dashboard, dove vado

Dalla dashboard non parte quasi mai un'azione diretta: è un **punto di partenza** per capire dove intervenire. Ecco la scelta più frequente:

| Se vedi… | Vai a… |
|----------|--------|
| Lead aperti in aumento | **Clienti** → filtra *Nuovo* → chiama in ordine di temperatura |
| Nuovi match alti | **Match** → apri prima i ROVENTI (rosso) |
| Immobili attivi calati | **Immobili** → verifica quali sono in bozza da riattivare |
| Visite (7gg) = 0 | **Clienti** → richiama i CALDI di questa settimana |
| Inviti pendenti > 0 | **Collaboratori** → re-invita chi non ha risposto |
| Nessun match, agenzia nuova | **Immobili** + **Clienti** → assicurati di avere almeno 10 immobili e 20 clienti con preferenze compilate |

---

## 2.5 · Errori comuni

- **"La dashboard è vuota, tutti i numeri sono 0"**
  Se l'agenzia è nuova è normale. I contatori si popolano man mano che aggiungi immobili, clienti, inviti collaboratori. Se hai già dati e vedi tutto 0, verifica in alto a sinistra di aver **selezionato l'agenzia giusta**.

- **"Vedo un numero diverso dal mio collega"**
  Se la segreteria ha permessi ridotti, alcuni conteggi possono differire dal titolare. Non è un bug: è la privacy dei ruoli.

- **"I contatori non si aggiornano mentre lavoro"**
  I numeri si ricalcolano ad ogni caricamento della pagina Dashboard. Per forzare l'aggiornamento clicca su un'altra voce del menu e poi torna su **Dashboard**.

- **"Ho aggiunto un immobile ma 'Immobili attivi' non è aumentato"**
  L'immobile va in stato *Pubblicato*, non *Bozza*. Se lo hai salvato in bozza non conta. Aprilo e clicca **Pubblica**.

---

## Voci correlate (fuori capitolo)

- **Cap. 3 · Immobili** — creare, modificare, pubblicare
- **Cap. 4 · Clienti** — anagrafica + preferenze di ricerca
- **Cap. 5 · Match** — leggere il Lead Scoring e agire
- **Cap. 20 · Collaboratori** — gestire team e inviti

---

## Note per HAL

> Le voci di questo capitolo sono esportate come YAML operativo in
> `/app/memory/manuale/hal/02-dashboard.yaml`.

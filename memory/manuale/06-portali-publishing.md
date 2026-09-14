# Capitolo 6 · Portali / Publishing

**Versione manuale**: v1.0 · **Ultima revisione**: Feb 2026
**Chi lo legge**: titolari, agenti (segreteria in sola lettura)
**Prerequisiti**: aver caricato almeno 1 immobile (Cap. 3) con foto, prezzo, indirizzo, superficie e classe APE compilati

Il modulo **Portali** (Publishing Center) è il ponte tra ImmoWeb e i portali immobiliari esterni. Serve a rispondere alla domanda "*dove finiscono i miei annunci?*" e "*perché quell'annuncio non viene pubblicato?*". Ci arrivi cliccando **Portali** dalla barra a sinistra.

Al posto di caricare gli annunci a mano su ogni portale, OMNIA genera un **feed XML** aggiornato in tempo reale e i portali attivi lo scaricano automaticamente ogni notte. Un **validatore Compliance** controlla che ogni annuncio rispetti le regole di legge (D.Lgs 192/2005 sull'APE, AGCM sul prezzo) e le regole tecniche dei portali (minimo 3 foto). Un **sync automatico giornaliero** alle 06:00 UTC (~07:00 in inverno / 08:00 in estate ora italiana) gira su tutti i portali attivi.

---

## 6.1 · A cosa serve il Publishing Center (in 60 secondi)

**Il problema che risolve**
Prima: aprivi Idealista, aprivi Immobiliare.it, aprivi Casa.it, aprivi Subito, caricavi le stesse foto e lo stesso testo su ognuno, e ogni volta che cambiavi prezzo dovevi rifare il giro.

**Con OMNIA**
- Compili l'immobile una sola volta (Cap. 3).
- Attivi i portali su cui vuoi essere presente (una-tantum).
- OMNIA genera un feed XML sempre aggiornato per la tua agenzia.
- I portali attivi lo leggono ogni notte e aggiornano gli annunci automaticamente.
- Un validatore controlla la compliance prima della pubblicazione: se manca prezzo, APE, indirizzo o 3+ foto → l'annuncio viene **escluso** (non pubblicato). Non è una punizione: è la regola HARD imposta dalla normativa italiana.

**Cosa NON fa (ancora) il Publishing Center**
- Non pubblica *automaticamente* su Idealista / Immobiliare.it / Casa.it (i tre portali dominanti). Servono accordi commerciali diretti tra agenzia e portale; OMNIA non ha ancora integrazione ufficiale. Continuerai a usarli come oggi finché non lo dichiareremo esplicitamente.
- Per i portali "push" (Facebook Marketplace, Google Business Profile) il sync per ora è **simulato**: il pulsante Sync gira, il log si aggiorna, ma la pubblicazione reale via API arriverà con lo Sprint successivo. È comunque visibile in dashboard per non "perdere il ricordo" del portale.

**Chi vede la pagina Portali**
- **Titolare**: pieno controllo (attivare, disattivare, forzare sync, vedere compliance).
- **Agente**: pieno controllo (stesso perimetro del titolare).
- **Segreteria** (concetto operativo, non ruolo): può vedere ma il consiglio è demandare al titolare le attivazioni con credenziali.

[SCREEN: cap6-portali-panoramica]

---

## 6.2 · I portali del catalogo (chi c'è, chi manca)

Al primo accesso al modulo trovi **8 portali** nella scheda **Disponibili**, ordinati per "traffico stimato" (stellette da 1 a 5). Sono i portali che abbiamo integrato per lo Sprint 1 del Publishing Center.

| Portale | Categoria | Modalità | Traffico | Cosa richiede |
|---------|-----------|:-:|:-:|---------------|
| **Subito.it** | freemium | feed_pull | ★★★★★ | Username + (opzionale) chiave partner |
| **Wikicasa.it** | freemium | feed_pull | ★★★★☆ | API Key (fornita dopo iscrizione) |
| **Facebook Marketplace** | gratuito | api_push ⚠️ *simulato* | ★★★★☆ | Page ID + Access Token Meta |
| **Google Business Profile** | gratuito | api_push ⚠️ *simulato* | ★★★★☆ | Google Business Account ID |
| **Bakeca.it** | gratuito | feed_pull | ★★★☆☆ | Email account |
| **Kijiji.it** | gratuito | feed_pull | ★★☆☆☆ | Email account |
| **Attico.it** | freemium | feed_pull | ★★☆☆☆ | Email account (free tier limitato) |
| **Case24.it** | freemium | feed_pull | ★★☆☆☆ | Email account |

**Cosa vuol dire "modalità"**
- **feed_pull** = il portale scarica da solo il tuo feed XML pubblico (`.../publishing/feed/<agenzia>.xml`) ogni notte. Non serve che OMNIA "spinga" nulla. Devi solo comunicare al portale l'URL del feed (spesso durante l'iscrizione).
- **api_push** = OMNIA dovrebbe chiamare le API del portale per pubblicare. Al momento è **simulato**: il pulsante "Sync" gira, il log dice "simulated_push", ma non c'è ancora una chiamata reale. Le integrazioni Meta e Google arriveranno in uno sprint dedicato.

**Non trovi il portale che ti serve?**
Se il tuo portale (regionale, di franchising, di nicchia) non è nel catalogo puoi aggiungerlo tu con il **Universal Portal Wizard** — vedi 6.7. Il portale personalizzato è visibile solo alla tua agenzia.

**Idealista, Immobiliare.it, Casa.it — dove sono?**
Volutamente non nel catalogo v1: sono a pagamento con integrazione commerciale diretta portale ↔ agenzia. Continua a usarli come oggi. Quando saranno integrati te lo diremo esplicitamente.

[SCREEN: cap6-catalog-disponibili]

---

## 6.3 · Attivare un portale (procedura standard)

**Prima di attivare, verifica**
- L'immobile che vuoi mandare deve essere in stato **Pubblicato** (non Bozza — vedi Cap. 3.8).
- Almeno un immobile deve superare la Compliance HARD (vedi 6.5), altrimenti il feed sarà vuoto.

**Passi**
1. Vai su **Portali** (barra a sinistra) → scheda **Disponibili**.
2. Trova il portale che ti interessa nella tabella.
3. Clicca **Attiva** in fondo alla riga.
4. Si apre una **finestra di attivazione**: contiene una breve descrizione del portale e i campi credenziali richiesti (variano da portale a portale — email, username, API key, ecc.).
5. Compila i campi. Le credenziali vengono **cifrate localmente** con AES-256-GCM prima di essere salvate: OMNIA non le legge mai in chiaro dopo il salvataggio.
6. Clicca **Attiva portale** (bottone verde). Se il portale non richiede credenziali → attivazione immediata.
7. Il portale sparisce dalla scheda "Disponibili" e appare nella scheda **Attivi** con badge di stato **active** (verde).

[SCREEN: cap6-modale-attivazione]

**Cosa succede subito dopo l'attivazione**
- OMNIA aggiunge il portale alla lista dei syncs schedulati.
- Il **primo sync reale** parte alla prossima esecuzione del job automatico giornaliero (06:00 UTC). Se vuoi vedere subito il risultato → forza il sync manuale (6.4).
- Se il portale è **feed_pull**: dovrai comunicare al portale l'URL del feed OMNIA della tua agenzia. Lo trovi nel Wizard Custom (6.7) o chiedilo al supporto del portale.

**Errori comuni**

| Problema | Cosa fare |
|----------|-----------|
| "already_connected" al clic su Attiva | Il portale è già attivo per la tua agenzia. Vai nella scheda "Attivi". |
| "portal_not_in_catalog" | Il portale è stato disattivato lato OMNIA (raro). Attendi o crea un Custom Portal (6.7). |
| Attivazione OK ma feed vuoto | Nessun immobile supera la Compliance. Vai su Compliance (6.5) e correggi. |

---

## 6.4 · Sync automatico + Sync manuale

**Il ciclo automatico**
OMNIA fa girare un job schedulato ogni notte alle **06:00 UTC** (07:00 in inverno, 08:00 in estate ora italiana). Il job:
1. Elenca tutte le connessioni attive di tutte le agenzie.
2. Per ognuna carica gli immobili in stato *active*.
3. Applica il validatore Compliance (6.5).
4. Per i portali feed_pull → aggiorna il timestamp e ricalcola quanti immobili sono pubblicabili.
5. Per i portali api_push → simulazione (integrazione reale in sprint successivo).
6. Scrive una riga di log per ogni sync in `publishing_sync_logs` (visibile in dashboard).
7. Se un sync fallisce → riprova fino a **3 volte** con attese progressive (1 min, 5 min, 30 min).

**Il sync manuale**
Serve quando: hai appena aggiunto un immobile importante, hai corretto un errore di compliance, vuoi vedere subito lo stato senza aspettare la notte.

1. Vai su **Portali** → scheda **Attivi**.
2. Trova il portale nella tabella.
3. Clicca il pulsante **Sync** (nero, piccolo, a destra della riga).
4. Nella riga compare "…" per qualche secondo.
5. Sopra la tabella compare un banner colorato con l'esito:
   - **Verde** = sync OK, N immobili pubblicabili, M bloccati.
   - **Ambra** = sync completato ma con warning (es. blocchi compliance) — pubblicazione parziale.
   - **Rosso** = sync fallito (vedi errore in log).
6. La colonna **Ultimo sync** sotto il nome del portale si aggiorna in tempo reale.

[SCREEN: cap6-sync-manuale-esito]

**Il banner risultato manuale (leggerlo bene)**
- `N immobili pubblicabili, M bloccati dal validatore compliance`.
- Se il portale è api_push il banner aggiunge una nota chiara: *"ℹ️ Portale push: integrazione reale in arrivo — per ora simulata."*
- Il banner si chiude col ✕ in alto a destra.

**Errori comuni**

| Problema | Cosa fare |
|----------|-----------|
| "connection_disabled" | Hai disattivato il portale prima. Riattivalo o rimuovilo definitivamente. |
| Sync gira ma "0 pubblicabili" | Nessun immobile passa la Compliance HARD. Apri Compliance (6.5) per capire i motivi. |
| Sync fallito per portale api_push | Normale in v1: l'integrazione live non è ancora attiva. Il log dirà "simulated_push". |

---

## 6.5 · Compliance HARD — perché un annuncio viene escluso

> 📖 **Deep-dive normativo → Cap. 16 · Compliance Portali**
> Questo paragrafo elenca le regole a livello operativo. Per il **contesto normativo** (D.Lgs 192/2005 APE, AGCM trasparenza prezzi), il **mapping campo-per-campo** su come correggere, la **logica esatta prezzo sale/rent/auction**, le **14 classi APE ammesse** e la **ghost label `missing_rent`** documentata onestamente → vedi **Cap. 16 · Compliance Portali**.

Prima di pubblicare un immobile su qualsiasi portale, OMNIA esegue un controllo. Le regole si dividono in due gruppi:

### 6.5.1 · Regole HARD (bloccano la pubblicazione)

L'annuncio **viene escluso** dal feed se manca anche uno solo di questi requisiti. Sono obbligatori per legge o per policy dei portali.

| Regola | Motivazione |
|--------|-------------|
| **Prezzo o canone** presente e > 0 | Obbligo di trasparenza AGCM. Sale → serve `price`. Affitto → serve `rent_monthly`. È ammesso il flag "Prezzo su richiesta" (`price_on_request`). |
| **Superficie (mq)** presente e > 0 | Obbligo normativo + regola di ogni portale. |
| **Classe energetica APE** valida | D.Lgs 192/2005. Classi ammesse: A4, A3, A2, A1, A, B, C, D, E, F, G, EXEMPT_IN_PROGRESS, EXEMPT_NOT_APPLICABLE. Se la classe è vuota o fuori lista → blocco. |
| **Almeno 3 foto** con URL valido | Standard portali (Immobiliare.it, Idealista, tutti). Meno di 3 → blocco. |
| **Indirizzo** (città + provincia) compilato | Serve al portale per la geo-ricerca. Manca la provincia → blocco. |

### 6.5.2 · Regole SOFT (warning, non bloccano)

L'annuncio **viene pubblicato lo stesso**, ma appare un avviso in dashboard.

| Warning | Perché è utile |
|---------|----------------|
| Titolo < 10 caratteri | I portali penalizzano annunci con titoli poveri. |
| Descrizione < 50 caratteri | Meno visibilità nelle liste. |
| Locali non indicati | Il portale non lo mostrerà nei filtri "N locali". |
| IPE (indice prestazione energetica in kWh/m²) mancante | Non è obbligatorio come la classe, ma alcuni portali lo pretendono. |

### 6.5.3 · Aprire la Compliance di un portale

1. Vai su **Portali** → scheda **Attivi**.
2. Clicca **Compliance** (bottone bianco a destra della riga).
3. Si apre una **finestra** con 4 riquadri contatore:
   - **Totale** — immobili attivi dell'agenzia.
   - **Pubblicabili** — immobili che passano l'HARD.
   - **Bloccati** — immobili che falliscono almeno una regola HARD.
   - **Con warning** — immobili pubblicabili ma con almeno un SOFT.
4. Sotto ai contatori: **"Motivi blocco più frequenti"** (top 5 con quanti immobili colpisce ciascuno).
5. Ancora sotto: **"Immobili bloccati (primi 20)"** con il titolo e il link **"Correggi →"** che ti porta direttamente alla scheda dell'immobile.

[SCREEN: cap6-modale-compliance]

**Tabella di traduzione dei motivi (le etichette che vedi)**

| Codice interno | Etichetta italiana in UI |
|----------------|--------------------------|
| `missing_price` | Prezzo mancante |
| `missing_rent` | Canone mensile mancante |
| `missing_surface` | Superficie (mq) mancante |
| `missing_energy_class` | Classe energetica APE mancante |
| `invalid_energy_class` | Classe energetica non valida |
| `less_than_3_photos` | Meno di 3 foto |
| `no_valid_photo_url` | Foto senza URL valido |
| `missing_address` | Indirizzo incompleto (città/provincia) |
| `title_too_short` | Titolo troppo corto (<10 caratteri) |
| `description_too_short` | Descrizione troppo corta (<50 caratteri) |
| `rooms_not_specified` | Numero locali non indicato |
| `ipe_missing` | IPE (indice prestazione) non indicato |

**Errori comuni**

| Problema | Cosa fare |
|----------|-----------|
| "10 immobili bloccati per less_than_3_photos" | Vai su Immobili, filtra per "foto < 3", carica almeno 3 foto per ognuno (Cap. 3.5). |
| "5 immobili bloccati per missing_energy_class" | Vai sull'immobile → sezione Energia → seleziona la classe APE o "In corso" / "Non applicabile" (Cap. 3.6). |
| Il totale di "Pubblicabili" è uguale a "Totale" | Complimenti, agenzia perfetta. Il banner verde te lo conferma con ✅. |

---

## 6.6 · Log di sync (audit trail)

Ogni sync (automatico o manuale) lascia una **riga di log** salvata in permanenza. Serve per capire "*perché ieri notte non è successo niente*" o "*quanti annunci ho pubblicato la settimana scorsa*".

**Cosa contiene un log**

| Campo | Cosa dice |
|-------|-----------|
| **Trigger** | `scheduled` (job automatico), `manual` (bottone Sync), `admin_manual` (bypass admin) |
| **Stato** | `success`, `partial` (con blocchi compliance), `failed`, `simulated_push` |
| **Items OK** | Numero immobili pubblicati / pubblicabili |
| **Items Failed** | Numero immobili bloccati dalla compliance |
| **Retry count** | Se è un retry: 0, 1, 2, 3 (max) |
| **Error message** | Testo tecnico (es. `blocked_by_compliance:5`) |
| **Started/Ended** | Timestamp UTC |

**In v1 i log sono accessibili via endpoint API** (per admin/debug), mentre in dashboard vedi solo:
- L'**ultimo sync** (data + ora) sotto il nome del portale.
- Il **contatore** "N pubblicati · M bloccati" a destra.
- Il **badge errore rosso** se l'ultimo sync ha fallito (con tooltip sul messaggio d'errore).

Un pannello di visualizzazione log-per-riga in UI è pianificato per uno sprint successivo. Se hai bisogno di storico completo prima di allora, contatta il titolare o super_admin.

---

## 6.7 · Universal Portal Wizard (aggiungere un portale tuo)

Il catalogo v1 copre 8 portali generalisti. Se lavori con un portale regionale, di franchising o di nicchia (es. il portale della tua rete provinciale, un aggregatore ligure, un club di ville storiche) puoi **aggiungerlo tu** senza aspettare OMNIA. Il portale personalizzato è **visibile solo alla tua agenzia**.

**Prerequisito**
Il portale deve accettare feed XML in uno di questi due formati:
- **osf_federata** — formato OMNIA "federato", ricco (immobile completo con tutte le feature).
- **generic_rss** — RSS 2.0 semplice (titolo + prezzo + link), compatibile con la maggior parte degli aggregatori.

Non supportiamo (ancora) push via API o webhook per i custom portal — arriveranno in uno sprint successivo.

**Passi (wizard a 4 step)**

1. **Apri il Wizard**: dalla pagina Portali clicca **"+ Aggiungi portale personalizzato"** (bottone blu scuro in alto a destra).
2. **Step 1 · Identità**: dai un nome (es. *"Portale AgenziaLiguria"*), lo slug si compila da solo dal nome; opzionalmente inserisci il sito ufficiale del portale (informativo), scegli categoria (gratuito / freemium / premium) e scope geografico (locale / regionale / nazionale).
3. **Step 2 · Formato**: scegli il dialetto XML (**osf_federata** consigliato se non sai, oppure **generic_rss** per aggregatori). L'integrazione è fissa a **feed_pull** (il portale scarica il tuo feed).
4. **Step 3 · Endpoint**: incolla (opzionale) l'URL dove il portale scaricherà il feed OMNIA. È solo informativo: OMNIA non chiama quell'URL, serve al pilota del portale se glielo devi passare via email.
5. **Step 4 · Conferma**: appare **l'URL del feed OMNIA della tua agenzia** (`.../publishing/feed/<slug-agenzia>.xml?dialect=osf_federata`). Cliccando **"Copia"** lo copi negli appunti. Questo URL è quello che devi passare al portale.
6. Clicca **Conferma** → il portale viene creato + la connessione viene attivata subito (feed_pull non richiede credenziali → status **active**).
7. Torni alla pagina Portali con il tuo nuovo portale già nella scheda **Attivi**.

[SCREEN: cap6-wizard-step4-conferma]

**Note sui portali custom**
- Lo slug interno diventa `x-<8char-agency>-<tuo-slug>` per evitare collisioni con altre agenzie che usano lo stesso nome.
- Un portale custom con lo stesso slug viene rifiutato con errore `slug_already_used` → cambia leggermente il nome.
- Puoi cancellare un portale custom in qualsiasi momento (cascata sulla sua connessione). I log restano per audit.

**Errori comuni**

| Problema | Cosa fare |
|----------|-----------|
| "unsupported_dialect" | Hai scelto un dialetto non implementato (in v1: solo osf_federata e generic_rss). |
| "unsupported_integration_type" | Hai provato api_push o push_url. In v1 solo feed_pull. |
| "slug_already_used" | Nome troppo simile a un altro tuo portale custom. Rinomina. |
| Il portale scarica il feed ma vede 0 immobili | La Compliance HARD sta bloccando tutto. Apri Compliance sull'attivazione e correggi (6.5). |

---

## 6.8 · Il feed XML pubblico (per curiosi)

OMNIA espone un URL pubblico per ogni agenzia:

```
.../api/publishing/feed/<slug-agenzia>.xml?dialect=osf_federata
```

- È **pubblico** (nessuna autenticazione) — è pensato per essere scaricato da bot.
- Contiene **solo immobili in stato "active" che superano la Compliance HARD**. Le bozze non ci finiscono mai.
- Cache 30 minuti: il portale può leggerlo continuamente senza sovraccarico.
- Due dialetti disponibili: `osf_federata` (default, ricco) e `generic_rss` (basico).

Se un immobile scompare dal feed dopo essere stato lì: 3 possibilità.
1. È passato a stato *Prenotato* / *Venduto* / *Ritirato* → uscita voluta.
2. Hai eliminato una foto e ora ne ha meno di 3 → violazione HARD.
3. Hai modificato prezzo o APE lasciandolo vuoto → violazione HARD.

Apri la Compliance (6.5) per capire il motivo esatto.

---

## 6.9 · Errori comuni (raccolta)

| Problema | Cosa fare |
|----------|-----------|
| "Il portale non riceve gli annunci" | 1. Verifica che il portale sia nella scheda **Attivi**. 2. Verifica che almeno un immobile passi la Compliance. 3. Forza un sync manuale (6.4). 4. Se il portale è feed_pull, verifica che al portale hai comunicato l'URL corretto del feed (6.8). |
| "Vedo 'simulated_push' nel log" | È normale per Facebook Marketplace e Google Business Profile: l'integrazione live arriverà. Il portale non riceverà annunci reali finché non lo abilitiamo. |
| "Ultimo sync ieri, ma sono le 15:00" | Il sync gira alle 06:00 UTC. Se vuoi aggiornamento immediato → Sync manuale. |
| "Compliance dice 5 bloccati ma non vedo quali" | Nella modale Compliance scorri sotto ai contatori: c'è la lista "Immobili bloccati (primi 20)" con link Correggi. |
| "Ho attivato Idealista/Immobiliare.it e non li vedo" | Non sono nel catalogo v1. Continua a usarli col loro pannello agenzia. Se ti servono come Custom Portal, aggiungili col Wizard (6.7) usando dialetto `generic_rss` o `osf_federata`. |
| "Ho cambiato prezzo, non lo vedo sul portale" | Il portale scarica il feed la notte successiva. Forza un Sync manuale se vuoi verificare il feed OMNIA subito; il portale però ha comunque i suoi tempi di refresh. |
| "Voglio spegnere un portale temporaneamente" | Clicca **Disattiva** sulla riga → status passa a `disabled`, non viene syncato ma non perdi le credenziali. Riattivi quando vuoi. |

---

## Voci correlate (fuori capitolo)

- **Cap. 3 · Immobili** — foto, prezzo, APE, indirizzo (i 4 requisiti hard più frequenti)
- **Cap. 3.4 · Privacy** — un immobile L3/L4 NON entra nel feed pubblico (non vengono pubblicati)
- **Cap. 2 · Dashboard** — non c'è ancora un KPI "immobili pubblicati": lo consulti dalla Compliance
- **Cap. 24 · Impostazioni** — Domain Vault per Custom Portal + slug agenzia (usato nell'URL del feed)

---

## Note per HAL

> Le voci di questo capitolo sono esportate come YAML operativo in
> `/app/memory/manuale/hal/06-portali-publishing.yaml`.

# Capitolo 1 · Primo accesso

**Versione manuale**: v1.0 · **Ultima revisione**: Feb 2026
**Chi lo legge**: titolari, agenti, segreteria (chiunque debba iniziare a usare ImmoWeb)
**Prerequisiti**: aver ricevuto le credenziali (email + password) o un invito da un collega

---

## 1.1 · Cos'è OMNIA in 3 minuti

**A cosa serve**
OMNIA è un ecosistema per la tua agenzia immobiliare. Ti dà tre cose:

1. **ImmoWeb** — il tuo gestionale in-app (immobili, clienti, portali, sito).
2. **HAL** — l'assistente intelligente che ti aiuta a scrivere annunci, dare risposte legali e trovare informazioni dentro il gestionale.
3. **ImmobilCloud** — il portale nazionale dove finiscono in vetrina gli annunci della tua agenzia.

**In pratica**
Quando entri in OMNIA:
- La schermata iniziale è **ImmoWeb**, il tuo posto di lavoro quotidiano.
- Nella barra a sinistra trovi tutti i moduli (Dashboard, Immobili, Clienti, Match, Portali, Sito web, Impostazioni…).
- In alto trovi il pulsante per aprire **HAL**, che può risponderti in qualsiasi momento.
- Dall'esterno, chiunque cerchi casa può visitare **ImmobilCloud**: lì vede anche i tuoi annunci.

[SCREEN: cap1-orientamento-generale]

**Cosa NON serve sapere ora**
Non è necessario capire tutto subito. Il manuale ti guida modulo per modulo. Il capitolo di oggi copre solo l'ingresso.

---

## 1.2 · Login e cambio password

### 1.2.1 Entrare la prima volta

Il tuo titolare (o il servizio OMNIA se ti sei registrato tu stesso) ti ha inviato **due cose per email**:
- Un indirizzo del tipo `https://tua-agenzia.omniarealestateecosystem.it` (o simile).
- La tua email e una **password provvisoria**.

> **Sei stato invitato da un titolare?** Usa direttamente il link nell'email di invito: entri in un'agenzia già configurata, salti il wizard di onboarding e cominci a lavorare. L'onboarding descritto al paragrafo 1.3 riguarda **solo il titolare** che apre l'agenzia per la prima volta.

**Passi**
1. Apri il link ricevuto per email.
2. Clicca **Accedi** (in alto a destra).
3. Scrivi la tua email.
4. Scrivi la password provvisoria.
5. Clicca **Entra**.
6. Se è il tuo primo accesso, ti viene chiesto di **cambiare la password**.

[SCREEN: cap1-login-form]

**Errori comuni**
- *"Email o password sbagliata"*: controlla di avere copiato la password senza spazi iniziali/finali. Se hai fatto copia-incolla dalla mail, spesso viene copiato uno spazio in più.
- *"Il link scade dopo 7 giorni"*: se hai ricevuto un invito e non l'hai aperto in tempo, chiedi al titolare di re-inviarlo dalla sezione **Collaboratori** (Cap. 13).

### 1.2.2 Ho dimenticato la password

**Passi**
1. Dalla schermata di accesso clicca **Password dimenticata**.
2. Scrivi la tua email.
3. Clicca **Invia link di recupero**.
4. Apri la mail (arriva in genere entro 2 minuti; controlla anche lo spam).
5. Clicca il link nella mail.
6. Imposta una **nuova password** (almeno 8 caratteri, con una maiuscola e un numero).
7. Torna alla schermata di accesso ed entra con la nuova password.

[SCREEN: cap1-forgot-password]

**Errori comuni**
- *"Non arriva la mail"*: controlla la cartella Spam/Promozioni. Se non c'è dopo 5 minuti, la tua email potrebbe non essere quella collegata all'account: chiedi al titolare di verificare dalle **Collaboratori**.

### 1.2.3 Cambiare la password in un secondo momento

**Passi**
1. Clicca sul tuo nome in alto a destra.
2. Scegli **Profilo**.
3. Scorri fino a *Sicurezza*.
4. Clicca **Cambia password**.
5. Inserisci la password attuale e la nuova.
6. Clicca **Salva**.

---

## 1.3 · Onboarding agenzia (wizard 4 passi)

> Questo paragrafo serve solo al **titolare** che apre l'agenzia per la prima volta. Agenti e segreteria non lo vedono: entrano già in un'agenzia esistente e possono saltare direttamente al 1.4.

**A cosa serve**
Configurare i dati di base della tua agenzia una volta sola: nome pubblico, dati fiscali per le fatture, logo e colori del sito.

**Quando si usa**
Al primo login del titolare, se non è stata configurata prima. Puoi comunque modificare tutto in seguito dalle **Impostazioni**.

**I 4 passi**

### Passo 1 · Identità

Compili il **nome commerciale** dell'agenzia (quello che compare sui portali e sui volantini).
Esempio: *"Immobiliare Rossi"*.

### Passo 2 · Dati fiscali

Compili i dati che finiranno sulle fatture e sui contratti:
- **Ragione sociale** (es. *"Immobiliare Rossi S.r.l."*)
- **Partita IVA**
- **Codice fiscale**
- **Numero REA** (facoltativo, ma consigliato)
- **Codice FIAIP** (facoltativo)
- Indirizzo completo (via, CAP, città, provincia)
- Email pubblica, telefono, sito (se ne hai già uno)

### Passo 3 · Branding

Personalizzi l'aspetto del sito che OMNIA ti darà:
- **URL del logo** (o carichi il file)
- **Colore primario** (quello dominante)
- **Colore d'accento** (per pulsanti e dettagli)
- **Tagline** (una frase corta, es. *"Casa tua, dal 1985."*)

### Passo 4 · Conferma

Vedi un'anteprima dei colori scelti. Clicca **Crea agenzia** e sei dentro.

[SCREEN: cap1-onboarding-step4-conferma]

**Errori comuni**
- *"Partita IVA non valida"*: verifica di aver messo 11 cifre senza spazi.
- *"Il colore non si vede bene sul mio logo"*: puoi cambiarlo in qualsiasi momento dalle **Impostazioni → Branding**.
- *"Ho sbagliato la ragione sociale"*: correggibile da **Impostazioni → Dati fiscali**.

**Chi può farlo**
Solo il titolare (ruolo *agency_admin*). Se un agente prova ad accedere prima che l'agenzia sia configurata, vede un messaggio *"L'agenzia non è ancora attiva"*.

---

## 1.4 · Tour della barra a sinistra

**A cosa serve**
Sapere dove trovi ogni cosa. La barra a sinistra è il tuo indice: da qui apri i moduli.

**Cosa vedi (in ordine di apparizione)**

| Voce | Cosa apre | Chi la vede |
|------|-----------|-------------|
| **Dashboard** | Pannello iniziale con 6 numeri chiave (immobili attivi, lead, match, visite, collaboratori, inviti pendenti) | Tutti |
| **Gruppo** | Gestione filiali (solo tier **Agency** — reti multi-sede) | Titolare + capogruppo |
| **API Keys** | Chiavi per widget e integrazioni esterne | Solo titolare |
| **Importa** | Import massivo di immobili da file XML | Solo titolare |
| **Portali** | Publishing Center: catalogo v1 di 8 portali generalisti (Subito, Bakeca, Kijiji, Wikicasa, Facebook Marketplace, Google Business, Attico, Case24). Immobiliare.it/Casa.it/Idealista non sono in v1 — vedi Cap. 6. | Solo titolare (in questa versione) |
| **Immobili** | Elenco e schede degli immobili | Tutti |
| **Clienti** | Anagrafica clienti + preferenze di ricerca | Tutti |
| **Match** | Abbinamenti automatici cliente↔immobile con Lead Scoring | Tutti |
| **Sito web** | Personalizzazione sito pubblico agenzia | Solo titolare |
| **Virtual Staging** | Studio per arredare stanze vuote con l'AI | Tutti |
| **Mutui** | Comparatore mutui | Tutti |
| **HAL Legal** | Chatbot giuridico con citazioni normative | Tutti gli utenti loggati |
| **HAL Knowledge** | Chatbot che spiega come funziona la piattaforma. Corpus manuale indicizzato — pronto all'uso. | Tutti |
| **Collaboratori** | Inviti e gestione membri agenzia | Tutti (solo titolare può invitare) |
| **Piano & Crediti** | Il tuo piano attuale, crediti residui, ricariche | Solo titolare |
| **Impostazioni** | Dati agenzia, branding, dominio, notifiche | Solo titolare |

[SCREEN: cap1-sidebar-completa]

**Note utili**
- La barra si **restringe automaticamente** su schermi piccoli. Su cellulare compare come menu ☰ in alto.
- L'ordine è stabile: non cambia in base al ruolo. Le voci non accessibili semplicemente **non compaiono**.
- Se vuoi tornare rapidamente alla home clicca in alto a sinistra su **OMNIA**.

**Chi vede cosa (riepilogo per ruolo)**

- **Titolare (agency_admin)**: vede tutto.
- **Agente**: vede Dashboard, Immobili, Clienti, Match, Virtual Staging, Mutui, HAL Legal, HAL Knowledge, Collaboratori.
- **Segreteria** (concetto operativo, si logga come *agente* con ruolo backend `agent` — cfr. Cap. 13): stesso menu dell'agente. Nota D-051: in v1 non esiste UI per nascondere singole voci del menu per membro; permessi granulari per collaboratore non sono disponibili (cfr. Cap. 13 §13.12 limiti v1).

---

## 1.5 · Cambio lingua e profilo utente

### 1.5.1 Cambiare lingua interfaccia

**A cosa serve**
OMNIA parla italiano, inglese e spagnolo. Cambi lingua quando accogli un cliente straniero o se un collaboratore preferisce un'altra lingua.

**Passi**
1. In alto a destra clicca la sigla della lingua attuale (**IT**, **EN** o **ES**).
2. Scegli la lingua nel menu a tendina.
3. La pagina si ricarica nella nuova lingua.

[SCREEN: cap1-language-switcher]

**Nota**
Il cambio lingua è **personale**: cambia solo per te. Il tuo collega continua a vedere OMNIA nella sua lingua. Anche i clienti finali del portale ImmobilCloud possono scegliere la loro lingua indipendentemente.

### 1.5.2 Il tuo profilo

**A cosa serve**
Aggiornare il tuo nome, la tua foto e la password. Vedere l'agenzia in cui sei attivo.

**Passi**
1. Clicca sul tuo nome in alto a destra.
2. Scegli **Profilo**.
3. Modifica: nome, cognome, foto, telefono.
4. Clicca **Salva**.

**Se sei attivo in più agenzie**
Il selettore compare **solo se sei membro di due o più agenzie** (es. rete franchising, doppio incarico su più sedi). Se sei in una sola agenzia non lo vedi affatto: è normale.

Quando c'è, lo trovi in alto a sinistra sotto il logo OMNIA. Clicca e scegli l'agenzia su cui vuoi lavorare: da quel momento immobili, clienti, match e ogni dato mostrato si riferiscono **solo** all'agenzia attiva. Cambiare agenzia non ti fa uscire dall'account.

### 1.5.3 Uscire

**Passi**
1. Clicca sul tuo nome in alto a destra.
2. Scegli **Esci**.

Sarai riportato alla schermata di accesso.

---

## Voci correlate (fuori capitolo)

- **Cap. 2 · Dashboard** — cosa fare appena entrato
- **Cap. 13 · Team & Ruoli (Collaboratori)** — come il titolare invita agenti/segreteria (magic-link 7gg, ruoli `agency_admin`/`agent`, limiti v1)
- **Cap. 24 · Impostazioni** — dove modificare dati agenzia e branding

---

## Note per HAL

> Le voci di questo capitolo sono esportate come YAML operativo in
> `/app/memory/manuale/hal/01-primo-accesso.yaml`.
> HAL Knowledge le usa per rispondere a domande dell'utente sul primo accesso.

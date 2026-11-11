# Capitolo 1 · Primo accesso

**Versione manuale**: v1.7 · **Ultima revisione**: 10-Nov-2026 (D-157/D-158 registrazione gestionale)
**Chi lo legge**: titolari, agenti, segreteria (chiunque debba iniziare a usare ImmoWeb); privatamente anche utenti ImmobilCloud
**Prerequisiti**: aver scelto un pacchetto e completato la registrazione agenzia, oppure aver ricevuto un invito / chiave API

---

## 1.1 · Cos'è OMNIA in 3 minuti

**A cosa serve**
OMNIA è un ecosistema per la tua agenzia immobiliare. Ti dà tre cose:

1. **ImmoWeb** — il tuo gestionale in-app (immobili, clienti, portali, sito).
2. **HAL** — l'assistente intelligente che ti aiuta a scrivere annunci, dare risposte legali e trovare informazioni dentro il gestionale.
3. **ImmobilCloud** — il portale nazionale dove finiscono in vetrina gli annunci della tua agenzia.

**Sito istituzionale (www · D-146)**  
`https://omniarealestateecosystem.it/it` è la **vetrina Lab + Ecosystem** (Chi siamo, tre anime, Perché OMNIA, prezzi Founders). Non confonderla con ImmobilCloud: sulla nav www **non** c’è «Cerca casa» — per cercare casa si entra da ImmobilCloud (`/it/cloud`). I box «Le tre anime» portano a cloud / registrazione agenzia / Academy.

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

### 1.2.0 Registrazione nuova agenzia (D-157…D-160)

Flusso gestionale B2B:

1. Scegli il **pacchetto** (3 box Starter / Pro / Agency) su `/it/register` → si apre il form.
2. Compila nome + email + **password temporanea** (min 8; D-159). Ti serve per rientrare durante onboarding / sala d’attesa.
3. Completa l’onboarding (identità, fiscale, branding) → sala d’attesa.  
   Email «richiesta ricevuta» (`agency_pending`) parte **solo a fine onboarding** (D-160: niente mail a metà register).
4. In sala d’attesa: carica **visura** + **documento identità** (PDF/PNG/JPG/WebP; anteprima dopo upload), poi paga con Stripe.
5. Il Super Admin in Cabina fa la checklist a **3 passi** (documenti → pagamento → Attiva). Ricevi email con **chiave API = password iniziale** (e Ops può **Copia chiave** show-once).
6. Collaboratori invitati: stessa logica API key = password iniziale; tetti posti a sedere (Starter 3 · Pro 10 · Agency ∞).

**Logo (D-158)**  
Con **sito web / dominio** già indicato, il file logo è **facoltativo**. Altrimenti PNG/JPG/WebP/SVG (max 2 MB) con anteprima locale.

**Se chiudi il browser a metà**  
Hai già la password temporanea del register: entra da `/it/login?from=app`. Se l’hai dimenticata → **Password dimenticata?**.

### 1.2.1 Entrare dopo l’attivazione (o con invito)

Dopo Attiva Ops (o invito) hai ricevuto per email:
- Link di accesso al gestionale.
- La **chiave API / password iniziale** (seleziona il riquadro → Ctrl+C / tieni premuto → Copia).

> **Sei stato invitato da un titolare?** Usa il link nell’email di invito: entri in un’agenzia già attiva.

**Passi**
1. Apri il link (o `/it/login?from=app`).
2. Email + chiave API / password iniziale.
3. **Entra**.
4. Al **primo ingresso** compare una schermata obbligatoria: incolli la chiave come password attuale e scegli la **tua** password (`POST /auth/me/change-password`, D-160). La chiave resta in Impostazioni → API keys per integrazioni.

[SCREEN: cap1-login-form]

**Errori comuni**
- *"Email o password sbagliata"* in onboarding: usa la **password temporanea** del register, non la chiave API (ancora non esiste).
- *"Email o password sbagliata"* dopo Attiva: controlla spazi in copia-incolla della chiave.
- *"Il link scade dopo 7 giorni"* (invito): chiedi re-invio da **Collaboratori** (Cap. 13).
- *Login ok ma resti fuori su URL pubblico*: hard refresh. Cookie Secure su HTTPS.

### 1.2.1b Area riservata ImmobilCloud (B2C · D-131 / D-135)

Sul portale, **Area riservata** apre l'hub `/cloud/area` con due scelte chiare:
- **Accedi** → login esistente
- **Crea account** → registrazione privato

Se l'email è già registrata (B2C o B2B), la registrazione risponde **409** con messaggio e link ad Accedi — niente account doppi.

**D-135 — sessione agenzia / Founder**: il bottone nav mostra **«Il mio account» solo se sei B2C**. Se sei loggato nel gestionale (agenzia/Founder) vedi **Area riservata** e, su `/cloud/area`, un banner che spiega di usare un account Privato (finestra anonima OK). Non usare la sessione CRM per pubblicare da privato.

**Pubblicare annuncio (Privato)**:  
`/it/cloud/register?intent=sell` → `/it/cloud/account/sell` → salva → **Invia per la revisione** → stato **IN REVISIONE** (`moderation_status=pending`).

**Registrazione — telefono / WhatsApp (D-138)**: campi **opzionali** in `/cloud/register`. Restano editabili in Account → Sicurezza & privacy. Servono come default per i canali pubblici in **Vendi** (opt-in `show_phone` / `show_whatsapp`).

**Esci (logout B2C)**: se sei loggato come Privato, in nav ImmobilCloud e in `/cloud/account` c’è **Esci** → `POST /auth/logout` → Area riservata / home cloud. Sessione cookie JWT (access ~15 min, refresh ~7 giorni): senza Esci resti autenticato — è normale, non un bug.

**Messaggi e visite (D-138 Idealista+)**: da Account o Vendi → `/cloud/account/messages`. Inbox delle `listing_inquiries` (filtri, nota privata, Accetta/Rifiuta/Fatta visita, reply email/tel/WhatsApp). Dettaglio Cap. 18 §18.7b.

### 1.2.1b2 Home ImmobilCloud — 4 riquadri + Cerca casa / mappa / app (D-139…D-143)

**Home** (`/it/cloud`): sotto l’hero con form ricerca, griglia **4 riquadri** (`cloud-tools`):

| Tile | Destinazione | Nota |
|------|----------------|------|
| **Scout** | `/cloud/search` | Fiore all’occhiello: completezza, prezzo, domande (D-142) |
| **Cerca su mappa** | `/cloud/search?view=map` | Flusso mappa stile Idealista (D-141) |
| **Scarica app** | `/{lang}/cloud/app` | Guida + QR (D-143) |
| **News** | ticker RSS | Casa24 · mutui · arredo; `GET /api/cloud/news` (D-139) |

**Visura** e **HAL Legal** restano in **nav** (non nei tile home).

**Scarica app / QR (D-143)**  
1. Tile home → `/cloud/app` (QR grande + istruzioni Android/iOS).  
2. Il **QR** apre `/{lang}/cloud/area?from=pwa` → **Accedi** | **Crea account**.  
3. Su Area con `from=pwa`: striscia **Installa** (Android dialog nativo; iOS link alla guida).  
4. Nav sticky **opaca** (cream pieno): niente testo hero in trasparenza sulla barra.

**Cerca / Vendi**: banner Scout in evidenza (copy «fiore all’occhiello»).

**Cerca casa — lista**: sotto i filtri laterali c’è il box **«Cerca su mappa»** (`search-map-box`) → stessa ricerca in `view=map`.

**Cerca casa — mappa** (`?view=map`):
1. Split a viewport pieno: lista sticky a sinistra + mappa Leaflet a destra.
2. Pin con **pillola prezzo**.
3. Dopo pan/zoom compare **«Cerca in questa zona»** → aggiorna URL con `bbox=south,west,north,east` e richiama search/map filtrati.
4. API: `GET /api/cloud/search` e `GET /api/cloud/map` accettano `bbox`.

### 1.2.1c Continua con Google (D-134)

Su login/registrazione compare **Continua con Google** se l’API ha `GOOGLE_CLIENT_ID` valido (Client ID Web Console Google).  
Ops: Railway Variables + vault Cursor · vedi `memory/GOOGLE_AUTH.md`.  
Errore tipico `401: invalid_client` = Client ID placeholder o assente — non un bug del form password.

### 1.2.2 Ho dimenticato la password

Vale per **tutti i ruoli** (privato, agente, admin, Founder): stesso endpoint `POST /api/auth/forgot-password`.

**Passi**
1. Dalla schermata di accesso clicca **Password dimenticata**.
2. Scrivi la tua email.
3. Clicca **Invia link di recupero**.
4. Apri la mail (mittente `OMNIA <info@omniarealestateecosystem.it>` · D-132; entro ~2 minuti; controlla anche lo spam).
5. Clicca il link nella mail.
6. Imposta una **nuova password** (almeno 8 caratteri, con una maiuscola e un numero).
7. Torna alla schermata di accesso ed entra con la nuova password.

[SCREEN: cap1-forgot-password]

**Errori comuni**
- *"Non arriva la mail"*: controlla Spam/Promozioni. Se non arriva dopo 5 minuti, verifica l'email in **Collaboratori** (B2B) o riprova. Founder/ops: `SENDER_EMAIL` non deve essere sandbox Resend (D-132 · Cap. 18).

### 1.2.3 Cambiare la password in un secondo momento

**Passi**
1. Clicca sul tuo nome in alto a destra.
2. Scegli **Profilo**.
3. Scorri fino a *Sicurezza*.
4. Clicca **Cambia password**.
5. Inserisci la password attuale e la nuova.
6. Clicca **Salva**.

---

## 1.3 · Onboarding agenzia + sala d’attesa (D-157 / D-158)

> Solo il **titolare** che apre l’agenzia. Collaboratori invitati saltano questo passo.

**A cosa serve**  
Anagrafica agenzia + identificazione clientela (visura/CI) + pagamento pacchetto. Il CRM resta bloccato finché Ops non attiva.

### Wizard (dopo register)

1. **Identità** — nome commerciale.
2. **Dati fiscali / contatti** — ragione sociale, P.IVA, CF, REA (facoltativo), indirizzo, email, telefono, **PEC**, **sito web**. (Niente codice FIAIP in UI.)
3. **Branding** — logo file (opzionale se hai già il sito), colori, tagline.
4. **Invio** — crea agenzia in stato `pending` → redirect sala d’attesa.

### Sala d’attesa (`/it/app/waiting-activation`)

1. Carica **visura camerale** e **documento identità** (PDF/PNG/JPG/WebP, max 8 MB).
2. Paga il pacchetto (Stripe).
3. Attendi Super Admin → email con **chiave API = password iniziale**.

«Controlla di nuovo» aggiorna lo stato senza riportarti al register.

[SCREEN: cap1-onboarding-step4-conferma]

**Errori comuni**
- *"Partita IVA non valida"*: 11 cifre senza spazi.
- *Upload logo/documenti che «non va»*: usa PNG/JPG/WebP/PDF (niente HEIC/GIF); se la preview non si vede ma compare «Logo caricato» / «Documento caricato», l’upload è ok.
- *Non riesco a fare login a metà procedura*: vedi §1.2.0 (Password dimenticata / link resume).

**Chi può farlo**  
Titolare in registrazione → diventa `agency_admin` a fine wizard. CRM operativo solo dopo Attiva Ops.

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
| **Portali** | Publishing Center: catalogo di sistema **15 portali** (attivabili solo se integrazione pronta; Idealista/Immobiliare/Casa/Meta/Google in catalogo come Non ancora attivo). Vedi Cap. 6. | Solo titolare (in questa versione) |
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

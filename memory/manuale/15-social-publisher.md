# Capitolo 15 · Social Publisher — Pubblicazione su Facebook, Instagram, Telegram, WhatsApp e Google Business

> **Cosa trovi in questo capitolo**
> Il modulo **Social Publisher** ti permette di pubblicare un immobile su **Facebook Page**, **Instagram Business**, **Telegram**, **WhatsApp**, **WhatsApp Business** e **Google Business** direttamente dai canali social **della tua agenzia** — non da OMNIA. Ogni post appare come postato dalla tua Pagina/Bot/Profilo, con la tua identità visiva. Il capitolo copre: dove trovarlo, il **white label** (D-041), la configurazione dei 6 canali (con credenziali cifrate AES-GCM), la validazione, il flusso di pubblicazione on-demand, la caption automatica generata dai dati immobile, l'audit log dei post e i limiti onesti v1.

**Cosa NON è (D-051 onestà — regola cardine)**
- Non è uno **scheduler** con calendario e code di pubblicazione. È **on-demand**: apri l'immobile → clic *"Pubblica"* → il post parte adesso. Nessun cron, nessuna coda, nessuna programmazione futura.
- Non è un **editor di post creativi** (caroselli, video, reels, stories, GIF, collage). In v1 c'è **una sola immagine** per post + una caption testuale.
- Non è un **modulo analytics**. Non conta like, commenti, share, reach o impressioni. Sa solo se il post è stato **pubblicato con successo** oppure fallito.
- Non pubblica sotto un profilo **OMNIA condiviso**. Ogni post parte con **la tua Pagina Facebook**, **il tuo account Instagram Business**, **il tuo bot Telegram**, **il tuo WhatsApp / WABA**, **il tuo profilo Google Business**. OMNIA è invisibile per il pubblico finale.
- Non gestisce **X/Twitter, LinkedIn, TikTok, YouTube, Threads** in v1.
- Non fa **bulk publish** su 100 immobili alla volta. Un immobile per operazione (ma su più canali contemporaneamente).
- Non **auto-rinnova** i Page Access Token di lunga durata: quando scadono, li rinnovi manualmente dalle credenziali del canale.

---

## 15.1 · Cos'è Social Publisher e a chi serve

**In una frase**
Uno strumento a **push on-demand** che invia un annuncio immobiliare (foto + didascalia + link) sulla tua Pagina Facebook, sul tuo account Instagram Business, sul tuo canale Telegram, via WhatsApp / WhatsApp Business o sul tuo profilo Google Business — sotto **la tua identità di brand**.

**A chi serve**
- **Titolari di agenzia** che gestiscono social propri (Pagina FB, IG Business, canale Telegram, WhatsApp, Google Business) e vogliono ridurre il tempo di "prendere una foto, scrivere una caption, incollare" a un click.
- **Agenzie con marketing interno** che pubblicano regolarmente il portafoglio e vogliono standardizzare la caption (evitare refusi, dimenticanze di prezzo o città).
- **Reti / franchising** che devono garantire un tono coerente attraverso più filiali (la caption di default parte dai dati canonici della scheda immobile).

**White label (D-041 · regola cardine)**
OMNIA **non ha mai un profilo social pubblico su cui pubblicare per conto tuo**. Ogni canale opera **sotto la tua Meta App / il tuo Bot Telegram / il tuo WABA / il tuo account Google** — sono le tue credenziali, il tuo audit log, la tua responsabilità editoriale. Il pubblico che vede il post **non vede mai il nome OMNIA**.

[SCREEN: cap15-social-panoramica]

---

## 15.2 · Dove trovare Social Publisher

**Rotta**: `/it/app/social` (o `/en/app/social`, `/es/app/social`).

**Come arrivarci**
1. Fai login a ImmoWeb come **titolare** (`agency_admin`), `super_admin` o ruoli di rete (`branch_admin`, `group_admin`).
2. Nella barra a sinistra, sezione **Publishing** o **Marketing**, clicca **"Social Publisher"**.
3. Si apre la pagina con **6 card canali** (FB / IG / Telegram / WhatsApp / WhatsApp Business / Google Business) e l'elenco dei **post recenti** (max 20).

**Chi può accedere**
Ruoli `agency_admin`, `super_admin`, `branch_admin`, `group_admin`. Un `agent` semplice **non ha accesso** al modulo (né vede la voce menu, né può chiamare gli endpoint — riceve `403 Forbidden`). Motivo: la configurazione dei canali social è un'operazione di brand che spetta al titolare o al manager della filiale/gruppo.

---

## 15.3 · I 6 canali supportati (v1)

**Panoramica**

| Canale | Kind API | Colore brand | Credenziali richieste |
|--------|:-:|:-:|-----------------------|
| **Facebook Page** | Meta Graph v20 | #1877F2 blu | `page_id` + `access_token` |
| **Instagram Business** | Meta Graph v20 | #E4405F rosa | `ig_user_id` + `access_token` |
| **Telegram Channel** | Bot API | #26A5E4 azzurro | `bot_token` + `chat_id` |
| **WhatsApp** | wa.me deep-link | #25D366 verde | `phone` (E.164) |
| **WhatsApp Business** | Cloud API (Meta Graph) | #128C7E verde scuro | `phone_number_id` + `access_token` + `recipient_phone` |
| **Google Business** | GBP Local Posts v4 | #4285F4 blu Google | `location_name` + `access_token` |

### Facebook Page
- **API**: Facebook Graph v20.0 (`https://graph.facebook.com/v20.0`).
- **Cosa fa**: pubblica sulla tua **Pagina Facebook** aziendale (non profilo personale). Se c'è una foto → post con foto. Se non c'è foto ma c'è un link → post testo + link.
- **Serve**: `page_id` (ID numerico della Pagina) + `access_token` con permesso `pages_manage_posts` (idealmente **long-lived**, non-scadente o rinnovato periodicamente).

### Instagram Business
- **API**: Meta Graph v20.0 (Instagram Content Publishing API).
- **Cosa fa**: pubblica sul tuo **account IG Business** (non personale). L'immagine deve essere una **URL HTTPS pubblica** — è un vincolo di Meta, non nostro.
- **Serve**: `ig_user_id` (ID del profilo IG Business) + `access_token` del **Page Access Token** della Pagina Facebook collegata (IG Business → sempre collegato a una Pagina FB).
- **Flusso 2-step**: `POST /media` per creare un container → `POST /media_publish` per pubblicarlo.

### Telegram Channel
- **API**: Telegram Bot API (`https://api.telegram.org`).
- **Cosa fa**: manda un messaggio nel tuo **canale Telegram** attraverso il tuo **bot**. Se c'è foto → `sendPhoto`. Altrimenti `sendMessage`.
- **Serve**: `bot_token` (dal @BotFather di Telegram) + `chat_id` (formato `@nomecanale` oppure ID numerico negativo tipo `-1001234567890`).
- **Vincolo**: il bot **deve essere admin** del canale, altrimenti Telegram rifiuta la pubblicazione.

### WhatsApp
- **API**: nessuna Cloud API — genera un **link wa.me** con caption precompilata verso il tuo numero.
- **Cosa fa**: al publish salva in audit l'`external_id` = URL `https://wa.me/{phone}?text=…`. L'invio al contatto resta un tap sul link (WhatsApp consumer non espone un endpoint di push).
- **Serve**: `phone` in formato internazionale senza `+` (es. `393331234567`).

### WhatsApp Business
- **API**: WhatsApp Cloud API via Meta Graph v20.0 (`POST /{phone_number_id}/messages`).
- **Cosa fa**: invia un messaggio di testo (caption + eventuale listing_url) al **numero destinatario** configurato.
- **Serve**: `phone_number_id` (dal Meta Developer Dashboard / WABA) + `access_token` Cloud API + `recipient_phone` (E.164 del destinatario).
- **Vincolo onesto**: non pubblica su Status/wall; è un messaggio 1:1 verso il numero configurato. Fuori dalla finestra 24h Meta può richiedere un template approvato.

### Google Business
- **API**: Google Business Profile Local Posts (`https://mybusiness.googleapis.com/v4`).
- **Cosa fa**: crea un **Local Post** STANDARD sul tuo profilo attività (summary + media foto opzionale + CTA LEARN_MORE se c'è listing_url).
- **Serve**: `location_name` nel formato `accounts/{accountId}/locations/{locationId}` + OAuth `access_token` con scope `https://www.googleapis.com/auth/business.manage`.

**Limiti di lunghezza caption per canale**
| Canale | Limite piattaforma | Budget OMNIA v1 |
|--------|:-:|:-:|
| Facebook Page | 5.000 char | 4.900 char (troncatura sicura) |
| Instagram Business | 2.200 char | 2.100 char (troncatura sicura) |
| Telegram (con foto) | 1.024 char | 1.024 char (troncatura hard) |
| Telegram (solo testo) | 4.096 char | 4.096 char |
| WhatsApp / WhatsApp Business | 4.096 char | 4.096 char |
| Google Business (summary) | 1.500 char | 1.500 char |

Se una caption supera il limite del canale, viene **troncata automaticamente** con `…` a fine testo. Nessuna eccezione bloccante.

---

## 15.4 · Configurare un canale (self-service, 3 step)

**A cosa serve**
Salvare le tue credenziali API su OMNIA in modo che il modulo possa pubblicare a tuo nome. Le credenziali vengono **cifrate AES-GCM** lato backend e **non tornano mai in chiaro** alla UI.

**Passi operativi (identici per ogni canale)**
1. Vai in **Social Publisher**.
2. Nella sezione *"Canali disponibili"* individua quello che vuoi collegare (FB / IG / Telegram / WhatsApp / WABA / Google Business).
3. Clicca **"Configura"**. Si apre una modale con i campi credenziale.
4. Compila i campi (vedi §15.5 per come reperirli).
5. Clicca **"Salva credenziali"**.
6. Il backend cifra le credenziali e salva il canale come `active` (subito operativo, ma non ancora verificato con una chiamata reale alle API esterne).
7. Nella card del canale ora attivo clicca **"Valida connessione"** → OMNIA chiama l'endpoint Meta/Telegram/WhatsApp/GBP, verifica che le credenziali funzionino, e mostra il nome della Pagina/username IG/username del bot/numero/titolo location.

**Endpoint API dietro le quinte**
- `POST /api/app/publishing/social/channels` → salva credenziali + status="active"
- `POST /api/app/publishing/social/channels/{id}/validate` → chiama Meta/Telegram, aggiorna `display_name`, `status`, `last_error`

**Sicurezza (D-051)**
- Le credenziali vengono **cifrate AES-256-GCM** via `encrypt_dict()` prima di essere salvate su MongoDB (`credentials_encrypted` è una stringa opaca).
- Le API di lettura (`GET /channels`) escludono sempre il campo `credentials_encrypted` dalla risposta. **Non c'è modo di rileggere in chiaro** una credenziale dopo averla salvata (nemmeno il super_admin può via UI).
- Se devi cambiarne una, usi `PATCH /channels/{id}` con le nuove credenziali — le vecchie vengono **sovrascritte**.
- Il logging del backend **non stampa mai** i valori delle credenziali (solo il canale + agency_id).

**Un canale per agenzia per tipo (v1)**
Non puoi avere **due Pagine Facebook** collegate contemporaneamente alla stessa agenzia. Al secondo tentativo ricevi `409 channel_already_configured`. Se vuoi cambiare Pagina → prima disconnetti la vecchia (`DELETE`), poi configura la nuova.

[SCREEN: cap15-config-modal]

---

## 15.5 · Dove trovare le credenziali di ogni canale

### Facebook Page
1. Vai su **Meta Business Suite** → seleziona la tua Pagina.
2. **`page_id`**: nella barra URL della tua Pagina, oppure in *Impostazioni Pagina → Informazioni sulla Pagina → ID Pagina*.
3. **`access_token`**: da **developers.facebook.com** → Graph API Explorer → seleziona la tua App e la tua Pagina → richiedi permesso `pages_manage_posts` e `pages_read_engagement` → *"Genera Access Token"*.
4. Per ottenere un token **long-lived** (60 giorni invece di 1-2 ore), scambialo via `debug_token` — vedi la [guida Meta ufficiale](https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived).

### Instagram Business
1. Il tuo account IG deve essere **Business** (non personale) e **collegato a una Pagina Facebook**.
2. **`ig_user_id`**: chiamando `GET /me/accounts?fields=instagram_business_account` dal Graph API Explorer con il Page Access Token della Pagina collegata. Il campo `instagram_business_account.id` è il tuo `ig_user_id`.
3. **`access_token`**: **lo stesso Page Access Token** della Pagina Facebook collegata. Non è un token separato di IG.

### Telegram
1. Chatta con **@BotFather** su Telegram → `/newbot` → segui i passi → ricevi il **bot_token** (stringa del tipo `123456789:ABCdef...`).
2. Crea un canale Telegram (o usa uno esistente).
3. **Aggiungi il bot come admin** del canale (Impostazioni canale → Amministratori → Aggiungi Admin → cerca il tuo bot).
4. **`chat_id`**: se il canale è pubblico → `@nomecanale`. Se privato → l'ID numerico negativo (lo puoi trovare inoltrando un messaggio del canale a `@userinfobot`).

### WhatsApp
1. Usa il numero WhatsApp dell'agenzia in formato internazionale **senza `+` né spazi** (es. `393331234567`).
2. In OMNIA: Social Publisher → card WhatsApp → Configura → incolla `phone` → Salva.
3. Al publish viene generato un link `wa.me` con la caption: non c'è invio automatico (WhatsApp consumer non ha Cloud API).

### WhatsApp Business
1. Crea / apri un'app su **developers.facebook.com** con prodotto **WhatsApp** (Cloud API) e un WABA attivo.
2. **`phone_number_id`**: in Meta Developer Dashboard → WhatsApp → API Setup → *Phone number ID*.
3. **`access_token`**: token permanente o long-lived con permessi `whatsapp_business_messaging`.
4. **`recipient_phone`**: numero E.164 (senza `+`) a cui inviare gli annunci (es. numero interno di marketing).
5. In OMNIA: Social Publisher → card WhatsApp Business → Configura → compila i 3 campi → Salva → Valida.

### Google Business
1. Abilita **Google Business Profile API** sul tuo progetto Google Cloud e ottieni un OAuth token con scope `https://www.googleapis.com/auth/business.manage`.
2. **`location_name`**: formato `accounts/{accountId}/locations/{locationId}` (da Business Profile Manager / API `accounts.locations.list`).
3. **`access_token`**: OAuth Bearer token valido.
4. In OMNIA: Social Publisher → card Google Business → Configura → Salva → Valida (legge titolo location via Business Information API).

---

## 15.6 · Validare un canale (test di connessione)

**A cosa serve**
Verificare che le credenziali salvate funzionano davvero **prima di provare a pubblicare un immobile**. Ti evita di scoprire il token scaduto solo al primo post.

**Come si fa**
1. Nella card del canale attivo clicca **"Valida connessione"**.
2. Il backend chiama:
   - FB Page: `GET /me?fields=id,name` con il tuo `access_token` — poi confronta l'`id` restituito con il tuo `page_id` (se non matchano → `422 page_id_mismatch`).
   - IG Business: `GET /{ig_user_id}?fields=id,username`.
   - Telegram: `POST /getMe` sul bot token.
   - WhatsApp: normalizza e valida il formato E.164 del `phone` (8–15 cifre).
   - WhatsApp Business: `GET /{phone_number_id}?fields=id,display_phone_number,verified_name` + check `recipient_phone`.
   - Google Business: `GET /{location_name}` su Business Information API (`readMask=name,title,…`).
3. Se OK → status del canale diventa `active`, il campo `display_name` viene aggiornato (es. *"Nicastro Immobiliare"* per FB, *"@nicastro_immo"* per IG, *"nicastro_bot"* per TG, numero per WA, titolo location per GBP).
4. Se KO → status diventa `error`, `last_error` contiene la stringa Meta/Telegram/GBP, la card mostra un badge rosso con l'errore.

**Cosa NON verifica**
- Se il tuo bot Telegram è effettivamente **admin del canale** (Telegram non lo espone via getMe). Lo scopri solo al primo `sendPhoto/sendMessage` fallito.
- Se la tua Pagina FB ha effettivamente il permesso `pages_manage_posts` (non verificabile senza fare un post di prova).
- Se le immagini dei tuoi immobili sono **HTTPS pubbliche** (fondamentale per IG — se sono behind auth, IG rifiuta con `instagram_container_missing_id`).
- Se il destinatario WhatsApp Business è dentro la finestra 24h / ha un template approvato (Meta lo rifiuta solo al publish).
---

## 15.7 · Pubblicare un immobile — il flusso

**A cosa serve**
Mandare un annuncio immobile sui canali attivi con un click.

**Passi operativi**
1. Vai su **Immobili** (Cap. 3) e apri l'immobile che vuoi pubblicare.
2. Clic su **"Pubblica sui social"** (bottone presente nella toolbar della scheda immobile).
3. Scegli su quali canali pubblicare (multiselezione fra quelli che hai attivo).
4. **Opzionale**: rivedi la caption default (generata automaticamente dai dati immobile) e modificala se vuoi.
5. Clic **"Pubblica adesso"**.
6. Il backend chiama `POST /api/app/publishing/social/publish` con:
   ```json
   {
     "property_id": "<id>",
     "channels": ["facebook_page", "instagram_business", "telegram"],
     "caption": "<testo>",
     "image_url": "<url>",
     "listing_url": "<url>"
   }
   ```
7. Il backend itera su ciascun canale in **serie** e produce un risultato per canale.

**Il payload di risposta**
```json
{
  "property_id": "prop-abc",
  "results": {
    "facebook_page":     {"ok": true, "external_id": "12345_67890"},
    "instagram_business":{"ok": true, "external_id": "18023456789"},
    "telegram":          {"ok": false, "error": "telegram_error:chat not found"}
  },
  "ok": false
}
```

Il flag `ok` (top-level) è `true` **solo se tutti i canali sono andati a segno**. Se anche uno solo fallisce → `ok: false`, ma i canali che sono riusciti sono comunque pubblicati (non c'è rollback multi-canale).

**Cosa succede se un canale non è configurato**
Il canale ritorna `{"ok": false, "error": "channel_not_configured"}` **senza tentare alcuna chiamata esterna**. Viene comunque registrato un record in `social_posts` con `status: "failed"` (per audit).

[SCREEN: cap15-publish-multichannel]

---

## 15.8 · La caption automatica (default)

**A cosa serve**
Se non scrivi una caption custom, OMNIA ne compone una a partire dai dati canonici della scheda immobile.

**Formula (5 righe, in italiano)**
```
Trilocale via Roma
📍 Milano, MI
💶 250.000 €
📐 85 mq · 3 locali

<descrizione dell'immobile, primi 800 caratteri>
```

**Righe generate solo se il dato esiste** (D-051 · niente placeholder):
- **Riga 1** — Titolo (se presente).
- **Riga 2** — Città + Provincia (se almeno uno).
- **Riga 3** — Prezzo formattato con separatore migliaia italiano (`.`) + suffisso `€` (vendita) o `€/mese` (affitto — se c'è `rent_monthly` ma non `price`).
- **Riga 4** — Superficie MQ + Locali (se almeno uno).
- **Righe 5+** — Descrizione (primi 800 caratteri, il resto viene omesso).

**Nessuna riga con dato mancante viene stampata** — no `"Prezzo: N/D"`, no `"Città: - "`.

**Il tuo listing URL**
Se lo passi come parametro `listing_url`, viene aggiunto come **link nativo** al post Facebook (parametro `link` del feed). IG non lo usa (IG non accetta link in caption pubblici cliccabili). Telegram lo puoi mettere in caption a mano se vuoi.

---

## 15.9 · Audit log dei post (collezione `social_posts`)

**A cosa serve**
Sapere cosa hai pubblicato, quando, su quale canale, con quale risultato. Utile in caso di dispute (*"Questo immobile è stato pubblicato prima o dopo la data X?"*).

**Cosa viene salvato per ogni tentativo (success O failed)**
- `id` (uuid), `agency_id`, `channel` (fb / ig / tg / wa / waba / gbp), `property_id`, `caption` (troncata a 2000 char), `image_url`, `listing_url`.
- `status` (`success` | `failed`), `external_id` (l'ID Meta/Telegram/WABA/GBP o il link wa.me, se success), `error` (stringa errore, se failed).
- `created_at` / `updated_at` (ISO 8601 UTC).

**Anche i fallimenti vengono loggati** — così sai quando hai avuto problemi di deliverability e puoi indagare.

**Come consultare**
`GET /api/app/publishing/social/posts?limit=50&channel=facebook_page` (opzionale). In UI, la pagina Social Publisher mostra i **20 post più recenti** (tutti i canali insieme).

**Counter live sul canale**
Ogni canale ha due contatori `posts_ok` e `posts_failed` che vengono incrementati automaticamente ad ogni tentativo. Compaiono come badge accanto al nome del canale.

---

## 15.10 · Errori comuni e come risolverli

| Errore | HTTP | Cosa significa | Soluzione |
|--------|:-:|----------------|-----------|
| `channels_required` | 422 | Non hai selezionato nessun canale al publish. | Seleziona almeno un canale. |
| `unsupported_channel` | 422 | Canale non fra i 6 supportati (`facebook_page`, `instagram_business`, `telegram`, `whatsapp`, `whatsapp_business`, `google_business`). | Bug UI o richiesta manuale con canale sbagliato. |
| `missing_credentials:page_id,access_token` | 422 | Nella configurazione manca uno o più campi obbligatori. | Compila tutti i campi della modale. |
| `channel_already_configured` | 409 | Hai già configurato quel tipo di canale per la tua agenzia. | Aggiorna (`PATCH`) o disconnetti prima. |
| `channel_not_found` | 404 | Stai cercando un canale non tuo o cancellato. | Refresh pagina, verifica di non aver cancellato. |
| `page_id_mismatch` | 422 (validate FB) | Il token appartiene a una Pagina diversa da quella dichiarata. | Verifica il `page_id` — probabilmente sbagliato. |
| `invalid_phone` | 422 | Numero WhatsApp non in formato E.164 valido (8–15 cifre). | Usa solo cifre internazionali senza `+` (es. `393331234567`). |
| `invalid_location_name` | 422 | `location_name` non nel formato `accounts/…/locations/…`. | Copia il name completo dalla GBP API. |
| `instagram_requires_image` | 422 (publish IG) | Stai provando a pubblicare su IG senza immagine. | IG non accetta post testuali. Aggiungi almeno una foto pubblica HTTPS. |
| `meta_error:190:...` | 502 | Il token FB/WABA è scaduto o revocato. | Rigenera Access Token da developers.facebook.com. |
| `meta_error:100:...` | 502 | Parametro mancante o non valido (spesso `page_id` errato). | Verifica page_id + permessi token. |
| `instagram_container_missing_id` | 502 | Il container creato non ha ID. Spesso image_url non è accessibile pubblicamente HTTPS. | Verifica che la foto principale dell'immobile sia HTTPS e senza restrizioni access. |
| `telegram_error:chat not found` | 502 | Il `chat_id` è sbagliato o il bot non è admin del canale. | Aggiungi il bot come admin del canale. Se privato usa ID numerico negativo (es. `-1001234567890`). |
| `telegram_error:bot was blocked...` | 502 | Il bot è stato bloccato dal canale o dall'admin. | Rimuovi il bot e riaggiungilo come admin. |
| `gbp_error:…` | 502 | Google Business Profile ha rifiutato validate/publish (token, scope o location). | Rigenera OAuth con scope `business.manage` e verifica `location_name`. |
| `channel_not_configured` (in publish results) | — | Non hai attivo quel canale in configurazione. | Vai a Social Publisher → Configura il canale. |
| `property_not_found` | 404 | Il `property_id` non esiste nella tua agenzia. | L'immobile è stato cancellato o cambia agency_id. |

---

## 15.11 · Limiti onesti v1 (D-051)

**Cosa Social Publisher NON fa oggi**

- ❌ **Nessuno scheduling**: solo on-demand. Non puoi dire *"pubblica questo domani alle 10:00"*. Nessun calendario editoriale.
- ❌ **6 canali, non di più**: Facebook Page, Instagram Business, Telegram, WhatsApp, WhatsApp Business, Google Business. No **X/Twitter, LinkedIn, TikTok, YouTube Shorts, Threads** in v1.
- ❌ **WhatsApp consumer** genera solo un link `wa.me` (nessun invio automatico). **WhatsApp Business** invia un messaggio 1:1 al destinatario configurato — non Status/wall.
- ❌ **Solo 1 immagine per post** (Meta e Telegram supportano caroselli, ma non li usiamo v1).
- ❌ **No video / reels / stories**. Solo foto + testo.
- ❌ **No editor caption** con anteprima live per canale. Vedi la caption default o la scrivi tu al volo.
- ❌ **No template caption personalizzati per agenzia**. La caption default è la stessa per tutti (righe standard con emoji fisse: 📍 💶 📐).
- ❌ **No analytics engagement**. Non sappiamo dirti *"quanti like ha preso"* o *"reach del post"*. Sappiamo solo *"pubblicato con successo"* + `external_id` (con cui puoi cercare il post sul canale nativo).
- ❌ **No auto-refresh dei token FB long-lived**. Quando il tuo Page Access Token scade (60 giorni per i long-lived), lo devi rinnovare a mano dalle Impostazioni.
- ❌ **No bulk publish**: un immobile alla volta. Se vuoi pubblicare 50 immobili, li apri 50 volte.
- ❌ **No rollback multi-canale**: se pubblichi su FB+IG+TG e IG fallisce, i post su FB e TG restano pubblicati. Non c'è "annulla tutto".
- ❌ **No preview finale del post** prima di pubblicare (nessuna mock preview che simula come apparirà su FB/IG/TG).
- ❌ **No moderazione pre-pubblicazione**: qualsiasi utente con ruolo abilitato può pubblicare direttamente senza approvazione di un manager.

**Cosa può cambiare in futuro**
Se il campo esprime la necessità, in versioni successive: scheduling con calendario, caroselli/reels/stories, editor visuale caption, template per agenzia, analytics engagement, altri canali (X, LinkedIn, TikTok), bulk publish, preview visiva.

---

## 15.12 · Cross-ref con altri capitoli

- **Cap. 3 · Immobili**: il bottone *"Pubblica sui social"* parte dalla scheda immobile. La foto usata è quella marcata come principale (`photos[0]`).
- **Cap. 6 · Portali & Publishing**: **Sync engine portali** (`sync_engine.py`) è un flusso separato dedicato ai portali immobiliari (Subito, Bakeca, ecc.) — usa **feed pull**, non push social. Il social publisher è **push esplicito on-demand**. Sono due mondi distinti.
- **Cap. 8 · Sito web agenzia**: il `listing_url` che passi al social publisher è l'URL dell'immobile sul tuo sito. Cap. 8 spiega come è costruito.
- **Cap. 12 · HAL Knowledge**: puoi chiedere a HAL *"Come pubblico su Instagram?"* → risposta con fonti da `15-social-publisher.yaml`.
- **Cap. 13 · Team & Ruoli**: ruoli abilitati al modulo sono `agency_admin`, `super_admin`, `branch_admin`, `group_admin`. L'`agent` semplice non ha accesso.

---

**Progressione manuale**: 15/26 capitoli (58%).
**Voci HAL totali**: **182** (Cap. 1-15, +14 nuove voci Cap. 15).
**Versione capitolo**: v1.0 (Feb 2026 · TASK L).

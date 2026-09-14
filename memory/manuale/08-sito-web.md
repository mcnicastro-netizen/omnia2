# Capitolo 8 · Sito web agenzia

> **Cosa trovi in questo capitolo**
> Il modulo **Sito web** ti dà un sito pubblico dell'agenzia — con vetrina immobili, SEO, share sociale — collegato al tuo portafoglio ImmoWeb e brandato coi tuoi colori/logo. Il capitolo copre: come funziona il sito pubblico, l'estrattore brand da URL, i 4 temi disponibili, l'auto-configurazione, la live preview e il custom domain (il tuo `www.tuoagenzia.it`).

**Cosa NON è (D-051 onestà)**
- Non è un **CMS pagine libere**: le pagine sono generate da OMNIA a partire dai tuoi immobili + brand config. Non scrivi HTML.
- Non è un **editor visuale**: scegli 1 dei 4 temi predefiniti e applichi eventuali override su palette/typography/logo/tagline.
- Non abilita **automaticamente l'SSL sul tuo dominio custom**: c'è uno step manuale del super_admin su pannello di hosting (vedi §8.8).
- **Custom CSS non supportato in v1**: la personalizzazione è entro il framework dei 4 temi + override.

---

## 8.1 · Cos'è il modulo Sito web

**In una frase**
OMNIA pubblica per ogni agenzia un sito pubblico **autonomo, indicizzabile da Google**, con vetrina immobili + schede dettaglio + condivisione sociale, brandato coi tuoi colori/logo.

**Cosa vedi dalla pagina Sito web (in CRM)**
1. **Brand Extractor** — inserisci l'URL del tuo sito attuale, HAL estrae palette, tipografia, tono e logo.
2. **Theme Picker** — 4 card con anteprima dei temi (Minimal, Classic, Bold, Luxury).
3. **Live Preview** — iframe con l'anteprima del sito con le tue impostazioni correnti.
4. **Custom Domain** — sezione per collegare il tuo dominio (es. `www.tuoagenzia.it`).

**Il sito pubblico** è servito da OMNIA su:
- URL di default: `https://omniarealestateecosystem.it/api/p/{slug-agenzia}/`
- URL personalizzato: `https://www.tuoagenzia.it/` (dopo verifica DNS e attivazione SSL).

**Cosa contiene il sito pubblico**
- **Home / vetrina** con la griglia dei tuoi annunci attivi (`status: active`), ordinati per data di aggiornamento decrescente. Fino a 200 in una pagina.
- **Scheda singolo immobile** con foto, prezzo, caratteristiche in griglia, descrizione, features, share block sociale, contatto agenzia.
- **`sitemap.xml`** automatica su `/api/p/{slug}/sitemap.xml` (per Google/Bing).
- **JSON-LD schema.org** (`RealEstateAgent` sulla home, `Product`/`RealEstateListing` sulla scheda) per rich snippets nei motori.
- **Meta OG** (Open Graph) per anteprima nei link condivisi (WhatsApp, Facebook, LinkedIn).

[SCREEN: cap8-website-panoramica]

**Chi può gestire il sito**
- **Titolare** (`agency_admin`): estrae, sceglie tema, applica, gestisce dominio custom.
- **Super_admin**: idem + può vedere l'elenco richieste dominio pendenti (`/admin/domains`).
- **Agente / segreteria**: non vedono la voce Sito web in sidebar (visibile solo al titolare).

**Ciclo di vita immobile → sito pubblico**
Un immobile compare nel sito pubblico **solo se** `status = active` (vedi Cap. 3.5 stato annuncio). Bozze, prenotati, venduti/affittati e ritirati non appaiono.

---

## 8.2 · Brand Extractor — estrai il brand dal tuo sito attuale

**A cosa serve**
Se hai già un sito, HAL lo analizza e capisce che colori usi, che tipografia, il tono editoriale, il logo. Poi ti propone il tema OMNIA più coerente con la tua identità.

**Come funziona sotto il cofano**
1. HAL scarica l'HTML della home del sito (User-Agent `OMNIA-BrandBot/1.0`, timeout 20 s, max 200 KB HTML).
2. Estrae: titolo pagina, meta description, primo logo trovato (`<img>` con "logo" in classe/alt/src), voci di navigazione, primo `<h1>`, snippet stili inline, prime 3 link stylesheet.
3. Invia il riepilogo a **Gemini 3 Flash** (via EMERGENT_LLM_KEY) con uno schema strutturato.
4. Riceve un JSON con: `palette` (primary, accent, neutral_dark, neutral_light in hex), `typography` (heading/body family + scale), `structure` (header_style, hero_type, navigation, card_style), `voice` (tone: professionale/familiare/lusso/tecnico/amichevole + tagline_guess), `logo_hint` (URL assoluto + alt), `confidence` (0-100).

**Passi operativi**
1. Vai in **Sito web** dalla barra a sinistra.
2. Nella sezione **Brand Extractor**, incolla l'URL del tuo sito attuale (es. `https://www.tuoagenzia.it`).
3. Clicca **Estrai brand**.
4. Dopo qualche secondo vedi un pannello con: confidence, colori estratti (4 chip), voce/header/card style, logo trovato ✓.
5. Se il risultato ti convince → clicca **⚡ Applica automaticamente**.

[SCREEN: cap8-brand-extractor]

**Cosa aspettarsi come confidence**
- **≥ 70/100** (verde) → estrazione affidabile, il logo è chiaro, i colori sono nell'HTML/CSS senza ambiguità.
- **40-69** (ambra) → estrazione parziale. Rivedi il tema proposto prima di applicare.
- **< 40** (rossa) → il sito è complesso o è renderizzato solo lato client. Considera di scegliere il tema manualmente.

**Errori comuni**

| Messaggio | Perché succede | Cosa fare |
|-----------|----------------|-----------|
| *`emergent_llm_key_missing`* (503) | Il credito LLM Emergent è finito o la chiave non è configurata | Controlla Piano & Crediti; ricarica se serve |
| *`ai_response_invalid`* (502) | Gemini ha risposto con un JSON non parseabile | Rilancia. Se persiste, scegli il tema manualmente |
| *`extraction_failed`* (502) | Timeout HTTP o errore di download | Verifica che il sito risponda; alcuni siti bloccano bot HTTP con Cloudflare/WAF |
| *`fetch_failed`* | URL non raggiungibile o schema non http(s) | Assicurati che sia una URL pubblica con `https://` |
| *`invalid_url_scheme`* (400) | URL con schema diverso da http/https | Correggi la URL |

**Costo credito**
Ogni estrazione consuma **1 chiamata Gemini 3 Flash** (EMERGENT_LLM_KEY). Nessun sub-conto crediti separato in v1.

**Il brand estratto viene salvato**
Il risultato completo va in `agency.website.extracted_profile` (JSON con `brand_profile`, `extracted_from`, `extracted_at`, `title`, `logo_hint`). Puoi rilanciare l'estrazione più volte — l'ultimo risultato sovrascrive il precedente.

---

## 8.3 · I 4 temi disponibili

**Filosofia**
Ogni tema è una coppia di layout `render_index` (vetrina) + `render_property` (scheda dettaglio) generati server-side in HTML pulito. Nessun framework JS lato pubblico — solo un piccolo script per il pulsante "Copia link" nello share block.

**Il catalogo**

### 1) Minimal
- **Per chi**: agenzie boutique, tono familiare o professionale.
- **Palette default**: primario `#1c1917` (nero pece) · accent `#1f6b5c` (verde bosco) · neutro chiaro `#fafaf9`.
- **Tipografia**: heading `Fraunces` serif · body `system-ui` sans.
- **Layout**: molto spazio bianco, header trasparente con logo piccolo, card con bordo sottile, hero tipografico.
- **Ideale se**: hai poche immagini di alta qualità e vuoi far parlare il testo.

### 2) Classic
- **Per chi**: agenzie generaliste con portafoglio ampio, clientela mainstream.
- **Palette default**: primario `#0B1E3F` (blu notte) · accent `#C19A6B` (ottone/champagne) · neutro chiaro `#f5f3ee`.
- **Tipografia**: heading `Playfair Display` serif · body `Georgia` serif.
- **Layout**: header colorato con logo invertito, cards con ombra, titoli sottolineati dall'accent, prezzo in Playfair.
- **Ideale se**: vuoi un'immagine "istituzionale" tradizionale ma non polverosa.

### 3) Bold
- **Per chi**: agenzie moderne, ad alto volume, tono tecnico o professionale.
- **Palette default**: primario `#FF5A1F` (arancio brand) · accent `#111111` (nero) · neutro chiaro `#ffffff`.
- **Tipografia**: heading + body `Inter` sans, pesi 700-800.
- **Layout**: hero con typo maiuscolo enorme, card a piena immagine con body scuro, poca ombra, tanto contrasto.
- **Ideale se**: hai molte foto professionali e vuoi comunicare energia.

### 4) Luxury
- **Per chi**: agenzie di pregio, immobili di lusso.
- **Palette default**: primario `#0a0a0a` (nero puro) · accent `#B89D5E` (oro rosato) · neutro chiaro `#fafafa`.
- **Tipografia**: heading `Playfair Display` serif · body `Inter` sans, pesi leggeri.
- **Layout**: header centrato con tagline in maiuscoletto spaziato, foto molto grandi (fino a 380px alte), card senza bordo, descrizione centrata max 720px, features come pill outline.
- **Ideale se**: il tuo portafoglio ha immobili sopra €500k medio e vuoi trasmettere esclusività.

[SCREEN: cap8-theme-picker]

**Personalizzazione oltre il tema**
Ogni tema accetta 4 override salvabili in `agency.website.theme_config`:
- **Palette**: puoi sovrascrivere `primary`, `accent`, `neutral_dark`, `neutral_light` (hex `#RRGGBB` obbligatorio).
- **Typography**: puoi sovrascrivere `headings` e `body` (stringa CSS `font-family`).
- **Logo URL**: URL assoluto del tuo logo (max 500 caratteri).
- **Tagline**: sottotitolo mostrato in header (visibile principalmente in Luxury; max 200 caratteri).

**Applicare un tema**
1. Nella sezione **Tema**, clicca sulla card del tema desiderato.
2. Il tema viene applicato immediatamente (POST `/website/theme/apply`) con la palette di default del tema.
3. Vedi il badge *"✓ Attivo"* comparire sulla card.
4. La **Live Preview** iframe si aggiorna automaticamente.

**Cambiare tema più volte**
È un'operazione **idempotente e reversibile**: cambia quante volte vuoi, il pubblico vede sempre l'ultima versione salvata. Ogni cambio aggiorna `applied_at` con timestamp.

---

## 8.4 · Auto-configurazione dal brand estratto

**A cosa serve**
Un unico click che combina brand estratto + scelta tema + palette dedotta.

**Come funziona (heuristic mapping)**
| Voice/tone estratto | Struttura | Tema scelto |
|---|---|---|
| `lusso` | qualunque | **Luxury** |
| — | `header_style: bold` **o** `card_style: image_dominant` | **Bold** |
| `familiare` **o** `amichevole` | — | **Classic** |
| `tecnico` | — | **Bold** |
| altrimenti | — | **Minimal** |

La **palette** proposta = quella estratta dal brand (solo hex validi passano il filtro `^#[0-9A-Fa-f]{6}$`). Se un colore estratto è invalido, si usa il default del tema.

Il **logo** proposto = quello estratto (o il logo salvato in `agency.branding.logo_url` come fallback).
La **tagline** proposta = quella estratta come `tagline_guess` (o quella salvata in `agency.branding.tagline`).

**Passi operativi**
1. Estrai il brand (§8.2).
2. Nel pannello risultato clicca **⚡ Applica automaticamente**.
3. OMNIA salva: `theme_id` scelto + palette + typography + logo + tagline + `source: "auto_from_extracted"`.
4. La Live Preview si aggiorna.

**Errori comuni**

| Messaggio | Perché succede | Cosa fare |
|-----------|----------------|-----------|
| *`no_extracted_profile`* (400) | Non hai ancora estratto un brand | Vai in §8.2 e lancia l'estrazione |

**Cosa NON fa l'auto-config**
- ❌ Non richiede il dominio custom.
- ❌ Non modifica gli annunci.
- ❌ Non blocca override manuali successivi: puoi comunque cambiare tema/colori dopo aver auto-configurato.

---

## 8.5 · Live Preview

**A cosa serve**
Vedere il sito **prima di condividerlo**, senza aprire una tab nuova. L'iframe carica direttamente il sito pubblico corrente.

**Come funziona**
- L'iframe punta a `{REACT_APP_BACKEND_URL}/api/p/{tuo-slug}/?t={timestamp}` — il timestamp forza refresh evitando cache.
- L'iframe è **sandboxed** (`allow-same-origin allow-scripts`) — nessun rischio di script esterni.
- Il bottone **↻ Aggiorna** ricarica l'iframe (utile dopo aver cambiato tema).
- Il bottone **Apri sito pubblico ↗** apre lo stesso URL in una nuova tab.

**Anteprima transient di un tema NON salvato**
Endpoint dedicato `GET /website/preview/{theme_id}` (usato internamente): applica un tema temporaneo alla vetrina senza persisterlo. Header risposta: `X-Robots-Tag: noindex` per evitare indicizzazione delle anteprime.

**Errori comuni**

| Sintomo | Perché succede | Cosa fare |
|---------|----------------|-----------|
| Iframe vuoto o "Impossibile connettersi" | Il tuo slug agenzia non è attivo o il backend è down | Verifica in **Impostazioni** che la tua agenzia sia `is_active: true` (contatta assistenza se dubbi) |
| Anteprima mostra "Nessun immobile pubblicato" | Nessun immobile in `status: active` | Vai in **Immobili**, verifica gli stati (vedi Cap. 3.5) |
| Foto rotte / non caricano | Le foto sono state eliminate ma referenziate | Ricarica le foto degli immobili (Cap. 3.3) |

---

## 8.6 · Vetrina pubblica (`/p/{slug}/`)

**Cosa vedono gli utenti sulla home**
- **Header** con logo + nome agenzia (tagline solo in Luxury).
- **H1** col nome dell'agenzia + counter *"N immobili attivi"*.
- **Griglia listings** con card per ogni immobile:
  - Cover photo (dalla prima foto `is_cover=true`, o dalla prima foto se nessuna è cover).
  - Titolo, città, tipologia, superficie m², numero locali.
  - Prezzo (o `€X/mese` per affitti).
- Se non ci sono annunci attivi, appare: *"Nessun immobile pubblicato al momento."*

**Meta SEO generati automaticamente**
- `<title>`: *"{Nome Agenzia} — Immobili in vendita e affitto"*
- `<meta description>`: *"Portafoglio immobili pubblicato da {Nome Agenzia}. {N} annunci attivi su OMNIA."*
- `<link rel="canonical">`: URL assoluto della home.
- `<meta property="og:title|description|url">` e `og:type: website`.
- JSON-LD `RealEstateAgent` con `name` e `url`.

**Ordinamento**
Gli immobili sono ordinati per `updated_at` decrescente — le modifiche recenti vanno in cima. Max 200 immobili in home. Per portafogli più grandi, la sitemap.xml elenca comunque tutti (fino a 5.000).

**Sitemap.xml**
- URL: `/api/p/{slug}/sitemap.xml`
- Contiene la home (priorità 1.0, changefreq `hourly`) + tutte le schede immobili attivi (priorità 0.8, changefreq `daily`, `lastmod` = data ultimo aggiornamento).
- **Consiglio**: dopo aver attivato il dominio custom, invia la sitemap a Google Search Console per accelerare l'indicizzazione.

---

## 8.7 · Scheda pubblica immobile (`/p/{slug}/{property_id}`)

**Cosa vede il visitatore**
1. **Header agenzia** (uguale alla home).
2. **Breadcrumb informale** — città + zona + riferimento (RIF).
3. **Prezzo** in evidenza (usa tipografia del tema).
4. **Griglia foto** con tutte le foto dell'immobile (nessun limite, `loading="lazy"` per performance).
5. **Griglia caratteristiche principali** — tipologia, operazione, città, zona, superficie, locali, camere, bagni, piano, classe energetica, anno, riferimento.
6. **Descrizione** — testo intero della scheda (preserva a-capo).
7. **Caratteristiche** — chip per ogni feature attiva (auto snake_case → spazi).
8. **Share block** — 4 bottoni (WhatsApp, Facebook, Email, Copia link) con SVG inline; nessun script terze parti.
9. **CTA contatto agenzia** — box "Contatta [Nome Agenzia]" (non c'è form nativo B2B → il lead form appartiene al portale B2C `/cloud`).

**Meta SEO scheda**
- `<title>`: *"{Titolo immobile} — {Nome Agenzia}"*
- `<meta description>`: *"{Tipologia} in {operazione} a {Città} · {m²} m² · {locali} locali · {prezzo}"*
- `<link rel="canonical">`: URL assoluto della scheda.
- `<meta property="og:image">`: URL assoluto della cover photo (chiave per anteprima link su WhatsApp/Facebook).
- JSON-LD schema.org `Product` (con `additionalType: RealEstateListing`), `offers.price` con currency EUR, `seller: RealEstateAgent`, `areaServed` = città.

**Come funzionano le foto**
Ogni immagine è servita da `/api/public/property/{pid}/photo/{idx}`. Il backend supporta 3 formati storage:
- **Object Storage cifrato** (H10 — path `/api/media/...` nel campo `url`): download binario diretto.
- **URL esterna** (`http(s)://...`): redirect 302 all'origine.
- **Base64 legacy** (`data:image/...`): decode e stream binario.
Header cache: `public, max-age=86400` (24 ore).

**Share sociale — cosa succede al click**
- **WhatsApp**: apre `wa.me` con testo pre-compilato *"{Titolo} — {Agenzia} · {Prezzo} {URL}"*.
- **Facebook**: apre il dialog nativo `sharer.php` di FB con l'URL della scheda.
- **Email**: apre client mail default con subject + body pre-riempiti.
- **Copia link**: usa `navigator.clipboard` (fallback textarea in browser vecchi) — feedback *"✓ Copiato"* per 1.8s.

[SCREEN: cap8-scheda-pubblica]

---

## 8.8 · Custom Domain (`www.tuoagenzia.it`)

**A cosa serve**
Far vedere il tuo sito OMNIA sul tuo dominio commerciale invece che sull'URL `/api/p/{slug}/` di OMNIA. Migliora branding, SEO, memorabilità.

**Come funziona in 4 step (D-051 onestà: c'è UNO step manuale del super_admin)**

**Step 1 — Richiesta (tu)**
1. Vai in **Sito web** → sezione **Dominio personalizzato**.
2. Inserisci il dominio (es. `www.tuoagenzia.it`) — solo minuscole, no `https://`, no percorsi.
3. Clicca **Richiedi dominio**.
4. OMNIA genera un **token di verifica** casuale e ti mostra 2 record DNS da configurare.

**Step 2 — DNS (tu, sul pannello del tuo registrar)**
Aggiungi al tuo dominio i **2 record**:

| Tipo | Host | Valore |
|:-:|------|--------|
| **TXT** | `_omnia-challenge.tuoagenzia.it` | `omnia-verify={token generato}` |
| **CNAME** | `www.tuoagenzia.it` (o quello che hai richiesto) | `agencies.omniarealestateecosystem.it` |

**Apex (dominio senza `www`)**: alcuni registrar non permettono CNAME sull'apex. Usa **ALIAS/ANAME** dove supportato (es. Cloudflare, DNSimple), altrimenti configura il sito sul sottodominio `www` e imposta un redirect apex→www.

I DNS pubblici propagano di solito in **5-60 minuti** ma possono impiegare fino a **24-48 ore** in casi lenti (TTL alto pre-esistente).

**Step 3 — Verifica (tu)**
1. Torna in **Sito web** → **Dominio personalizzato**.
2. Clicca **Verifica DNS**.
3. OMNIA risolve TXT e CNAME contro i DNS pubblici (1.1.1.1 e 8.8.8.8) e confronta:
   - TXT deve contenere esattamente `omnia-verify={token}`.
   - CNAME deve puntare a `agencies.omniarealestateecosystem.it` (o a un IP che corrisponde al target risolto).
4. Se OK → il dominio passa a **`verified`** con badge verde.
5. Se KO → badge rosso *"error"* con dettaglio (`txt_record_not_found_or_mismatch`, `cname_record_not_pointing_to_target`, ecc.). Correggi e rilancia.

**Step 4 — Attivazione SSL (super_admin OMNIA, manuale)**
- Dopo la verifica, il super_admin riceve un'email con la richiesta.
- Il super_admin aggiunge il dominio sul **pannello di hosting** (Emergent) per attivare l'**SSL Let's Encrypt** automatico.
- Solo dopo questo step il dominio è raggiungibile in HTTPS.
- **Tempo tipico**: 24-48 ore lavorative dopo la verifica DNS.

[SCREEN: cap8-custom-domain-flow]

**Stati possibili**
- **`pending`** (ambra) → richiesta creata, aspetto la tua verifica DNS.
- **`error`** (rosso) → l'ultima verifica DNS ha fallito. Correggi e rilancia.
- **`verified`** (verde) → DNS OK, aspetta l'attivazione SSL dell'admin.

**Domini vietati (`RESERVED_SUFFIXES`)**
Non puoi richiedere domini che finiscono con:
- `omniarealestateecosystem.it` (nostro dominio principale)
- `emergent.host`, `emergentagent.com` (piattaforma di hosting)

**Errori comuni**

| Messaggio | Perché succede | Cosa fare |
|-----------|----------------|-----------|
| *`invalid_domain`* (400) | Formato dominio non valido (spazi, maiuscole, protocolli, path) | Inserisci solo `www.dominio.it` in minuscolo |
| *`reserved_domain`* (400) | Il dominio finisce con un suffisso vietato | Usa il tuo dominio commerciale, non uno OMNIA |
| *`domain_too_long`* (400) | > 120 caratteri | Impossibile in DNS reale, verifica di non aver incollato roba strana |
| *`domain_already_claimed`* (409) | Un'altra agenzia ha già reclamato lo stesso dominio | Impossibile in ambienti sani; contatta assistenza |
| *`txt_record_not_found_or_mismatch`* | Il TXT non è nei DNS pubblici o ha valore sbagliato | Verifica sul registrar; attendi propagazione DNS |
| *`cname_record_not_pointing_to_target`* | Il CNAME non risolve a `agencies.omniarealestateecosystem.it` | Correggi il valore sul registrar |

**Eliminare il dominio**
Puoi rimuovere il custom domain in qualsiasi momento con **Elimina dominio**. Attenzione: il sito continuerà a essere raggiungibile sul dominio custom finché il super_admin non lo rimuove anche dal pannello Emergent.

---

## 8.9 · Sitemap e SEO

**Sitemap.xml**
- Auto-generata su `/api/p/{slug}/sitemap.xml`.
- Formato XML standard `<urlset>` con `<loc>`, `<lastmod>`, `<changefreq>`, `<priority>`.
- Home: `changefreq=hourly, priority=1.0`.
- Schede immobili: `changefreq=daily, priority=0.8`, `lastmod` = data ultimo aggiornamento.

**Search Console — cosa fare dopo il dominio custom**
1. Aggiungi il dominio (verified via Google Search Console + record DNS).
2. Sottometti sitemap: `https://www.tuoagenzia.it/api/p/{slug}/sitemap.xml`.
3. Verifica in *Coverage*: le prime schede compaiono in 24-72 ore di solito.

**Cosa fa già bene OMNIA lato SEO**
- **Canonical tags** su ogni pagina.
- **Meta description** univoca per home + per ogni scheda.
- **Open Graph tags** con og:image (cover photo) per anteprima link social.
- **Schema.org JSON-LD** per rich snippets (rating, prezzo, area — dove i dati esistono).
- **URL stabili** (non contengono parametri di sessione).
- **Immagini con `alt` text** dedotti dal titolo immobile + `loading="lazy"` per performance.

**Cosa NON fa OMNIA (per essere onesti)**
- ❌ Non genera un blog integrato o pagine editoriali.
- ❌ Non ha una pagina "Chi siamo" / "Contatti" separata: la vetrina + le schede sono l'unico contenuto pubblico.
- ❌ Non inserisce hreflang multi-lingua sul sito pubblico (il pubblico è solo italiano in v1).
- ❌ Non integra Google Analytics o simili (nessun tracking pubblico by default — privacy by design).

---

## 8.10 · Errori comuni (raccolta)

| Problema | Dove | Cosa fare |
|----------|------|-----------|
| Il Brand Extractor mi restituisce confidence bassa (< 40) | Estrattore | Il tuo sito attuale ha molto JavaScript o è servito da un CMS che nasconde CSS/tipografia agli scraper. Scegli il tema manualmente. |
| Ho applicato un tema ma l'iframe non si aggiorna | Live Preview | Clicca **↻ Aggiorna**. Se persiste, apri il sito pubblico in una nuova tab (bottone **Apri sito pubblico ↗**). |
| Ho cambiato tema 3 volte ma il pubblico vede ancora quello vecchio | Cache CDN | Il tema viene applicato **immediatamente** lato server. Se un utente ha il sito in cache browser, deve fare hard-refresh (Ctrl+F5). |
| Il custom domain è `verified` da 2 giorni ma non risponde in HTTPS | SSL | L'attivazione SSL richiede lo step manuale del super_admin (~24-48h lavorative). Se sono passate più di 48h, contatta assistenza. |
| Le mie foto non compaiono sul sito pubblico | Foto | Le foto legacy in base64 pesano tanto; per performance consigliato spostare a Object Storage. Vedi Cap. 3.3. |
| Il logo che ho estratto è sbagliato | Extractor | Sovrascrivi con URL logo corretto nell'override (vedi §8.3). |
| Nel sito pubblico non c'è la mia agenzia | Sito pubblico | La tua agenzia deve avere `is_active: true` + almeno uno slug. Contatta assistenza se il pannello dice attiva ma il sito dà 404. |
| Voglio nascondere l'indirizzo esatto degli immobili dal sito pubblico | Privacy | Alza il livello privacy dell'immobile a L2 (vedi Cap. 3.4). |

---

## Voci correlate (fuori capitolo)

- **Cap. 3 · Immobili** — solo gli immobili `status: active` sono pubblicati. La cover photo definisce l'anteprima home + og:image.
- **Cap. 3.4 · Privacy L1-L4** — il sito pubblico rispetta il livello privacy: L3/L4 non appaiono in vetrina agli anonimi.
- **Cap. 6 · Portali** — il sito pubblico OMNIA è **complementare** ai portali, non li sostituisce. Il feed XML degli 8 portali generalisti convive con questo sito.
- **Cap. 7 · Fascicolo Immobile** — mai visibile al pubblico. Nessun documento del Fascicolo passa nel sito.

---

**Versione**: v1.0 · Feb 2026 (TASK E · Cap. 8 Sito web agenzia)

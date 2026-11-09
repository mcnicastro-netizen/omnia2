# Capitolo 8 · Sito web agenzia

> **Cosa trovi in questo capitolo**
> Il modulo **Sito web** ti dà un sito pubblico dell'agenzia — con vetrina immobili, SEO, share sociale — collegato al tuo portafoglio ImmoWeb e brandato coi tuoi colori/logo. Il capitolo copre: brand extractor, **gallery 8 temi** (D-150/D-151), MLS on/off sul sito (D-149), clone capture → preview 3 pagine, live preview e custom domain.

**Cosa NON è (D-051 onestà)**
- Non è un **CMS pagine libere**: le pagine sono generate da OMNIA a partire dai tuoi immobili + brand config. Non scrivi HTML.
- Non è un **editor visuale**: scegli 1 degli **8 temi** live e applichi eventuali override su palette/typography/logo/tagline.
- Non abilita **automaticamente l'SSL sul tuo dominio custom**: c'è uno step manuale del super_admin su pannello di hosting (vedi §8.8).
- **Custom CSS non supportato in v1**: la personalizzazione è entro il framework degli 8 temi + override.
- **Restyling caso 3** e **Stripe checkout template** (D-151 entitlement): restyling €199 in listino · checkout Stripe ancora ⏳.

---

## 8.1 · Cos'è il modulo Sito web

**In una frase**
OMNIA pubblica per ogni agenzia un sito pubblico **autonomo, indicizzabile da Google**, con vetrina immobili + schede dettaglio + condivisione sociale, brandato coi tuoi colori/logo.

**Cosa vedi dalla pagina Sito web (in CRM)**
1. **Brand Extractor** — inserisci l'URL del tuo sito attuale, HAL estrae palette, tipografia, tono e logo.
2. **Theme Picker / Brand Studio** — gallery **8 temi live**: Minimal, Classic, Bold, Luxury, Atelier, Cinematic, Editorial, Mediterranean (ogni tema QA MLS on|off).
3. **Live Preview** — iframe con l'anteprima del sito con le tue impostazioni correnti.
4. **Custom Domain** — sezione per collegare il tuo dominio (es. `www.tuoagenzia.it`).
5. **Cattura sito / clone** (D-149) — URL → palette → build preview home+lista+scheda (`clone_ready`).

**Il sito pubblico** è servito da OMNIA su:
- URL di default: `https://omniarealestateecosystem.it/api/p/{slug-agenzia}/`
- URL personalizzato: `https://www.tuoagenzia.it/` (dopo verifica DNS e attivazione SSL).

**Cosa contiene il sito pubblico**
- **Home / vetrina** con la griglia dei tuoi annunci attivi (`status: active`), ordinati per data di aggiornamento decrescente. Fino a 200 in una pagina.
- **Scheda singolo immobile** con foto, prezzo, caratteristiche in griglia, descrizione, features, share block sociale, contatto agenzia.

> **Nota ImmobilCloud (`/cloud`)**: il form contatto del portale B2C è distinto dal sito white-label. Su annuncio **agenzia** crea lead CRM (Cap. 18 §18.7); su annuncio **privato** crea inquiry al venditore (Cap. 18 §18.7b).
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

## 8.3 · Gallery 8 temi (D-150 / D-151)

**Filosofia**
Ogni tema è layout SSR (`theme_render` + `theme_css`): home, lista, scheda. Nessun framework JS lato pubblico — solo script minimi (copia link, box MLS). Un solo pack per **neo agenzia** e **restyling** (D-150). Ogni tema deve passare QA con `mls_enabled` true|false (D-149).

**Listino (D-151)**
| Path | Prezzo |
|---|:-:|
| Pro / Agency | gallery 8 **inclusa** |
| Starter neo — `minimal` \| `classic` | **€99** one-shot |
| Starter neo — altri 6 | **€199** one-shot |
| Restyling (caso 3) | **€199** one-shot |
Stripe checkout entitlement ancora ⏳; SoT prezzi in `plans.py` / `PRICING_OMNIA.md`.

**Il catalogo live**

### 1) Minimal (`simple` · €99)
Boutique, spazio bianco, Fraunces + system. Slot MLS chiaro (no blocco primary pieno).

### 2) Classic (`simple` · €99)
Mainstream istituzionale, blu notte + ottone, Playfair.

### 3) Bold (`premium` · €199)
Volume / moderno, arancio + nero, tipografia enorme, card image-dominant.

### 4) Luxury (`premium` · €199)
Pregio, nero + oro, foto grandi, header centrato.

### 5) Atelier (`premium` · €199)
Boutique urbana, CTA pill, luce studio, accent arancio.

### 6) Cinematic (`premium` · €199)
Full-bleed media, serif display, nav glass — prestigio + video hero.

### 7) Editorial (`premium` · €199)
Magazine / mono-quartiere, tipografia sobria, poco colore.

### 8) Mediterranean (`premium` · €199)
Sud / second home, fondi caldi, bordi sottili, accent champagne.

[SCREEN: cap8-theme-picker]

**Personalizzazione oltre il tema**
Override in `agency.website.theme_config`: palette (4 hex), typography, logo URL, tagline.

**Applicare un tema**
1. Brand Studio / Tema → card del tema.
2. `POST /website/theme/apply` (palette default del tema).
3. Badge attivo + Live Preview si aggiornano.

**Cambiare tema**
Idempotente e reversibile; il pubblico vede l'ultima versione (`applied_at`).

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

## 8.11 · Demo / template pack · **A-037** + **D-150/D-151** (agg. 09-Nov-2026)

### Cosa c’è oggi (onesto)
| Pezzo | Stato |
|-------|--------|
| Brand Extractor | ✅ palette/tono/logo |
| Gallery 8 temi + Brand Studio | ✅ live su main (#137) |
| Matrice MLS on/off per tema | ✅ D-149 / D-150 |
| Listino Starter €99/€199 · restyling €199 | ✅ SoT · Stripe entitlement ⏳ |
| Lead `/it/agenzie` «Hai un sito?» | ✅ |
| Loop automatico URL → demo pubblica vestita | ⚠️ assistito (capture+build), non fully auto |
| Recovery dominio non-proprietario | Cap. 17 · A-037 residuo path dominio |

### Promessa commerciale
Puoi promettere gallery 8 + MLS on/off + listino. Non promettere pixel-perfect clone né «solo sito» come SKU.

---

## 8.12 · Clone / migrazione sito · **D-023 / D-130 / D-149** (agg. 09-Nov-2026)

**D-130**: trasferimento look riconoscibile = P0 commerciale.  
**D-149**: casi 1–2 (MLS on/off + clone capture) shippati; restyling caso 3 in coda listino €199.

### Cosa c’è oggi
| Pezzo | Stato |
|-------|--------|
| Brand Extractor | ✅ |
| Gallery 8 | ✅ |
| `POST /app/website/clone-capture` (+ build) | ✅ |
| Preview `/api/p/{slug}/` · `/lista` · scheda | ✅ soglia home+lista+scheda |
| `website.clone_ready` | ✅ dopo smoke 3 pagine |
| Crawl Vision multi-pagina / headless D-022 | ❌ ancora gap vs clone «uguale al millimetro» |
| SKU «solo sito» | ❌ (sito = feature piano ImmoWeb) |

### Casi migrazione (D-149)
1. **MLS on** — box ricerca rete + sezione «Immobili dalla Rete MLS Partner» sulla home.
2. **MLS off** — solo search portafoglio; embed `/api/mls-box/*` → `mls_not_enabled`; `POST /app/mls/leave`.
3. **Restyling** — stesso pack temi, €199; in coda operativa rispetto a clone keep-brand.

### Cosa NON promettere
- «Resta uguale al millimetro» senza preview clone_ready.
- «Compri solo il sito» fuori listino ImmoWeb.

---

## 8.13 · MLS sul sito white-label (D-149)

Flag agenzia `mls_enabled` (join/leave MLS). Non cambia `theme_id`: cambia solo pezzi condizionali in `theme_render` / CSS.

| | MLS on | MLS off |
|---|---|---|
| Home | Box rete + sezione partner MLS | Solo search agenzia |
| Lista | Sidebar ricerca (rete se on) | Search senza chip rete |
| Embed mls-box | OK | `mls_not_enabled` |

Dettaglio operativo network: Cap. 27.

---

## Voci correlate (fuori capitolo)

- **Cap. 3 · Immobili** — solo gli immobili `status: active` sono pubblicati. La cover photo definisce l'anteprima home + og:image.
- **Cap. 3.4 · Privacy L1-L4** — il sito pubblico rispetta il livello privacy: L3/L4 non appaiono in vetrina agli anonimi.
- **Cap. 6 · Portali** — il sito pubblico OMNIA è **complementare** ai portali, non li sostituisce. Il feed XML degli 8 portali generalisti convive con questo sito.
- **Cap. 7 · Fascicolo Immobile** — mai visibile al pubblico. Nessun documento del Fascicolo passa nel sito.
- **Cap. 17 · Domain Vault** — verifica titolarità dominio + custom domain.
- **Landing `/it/agenzie`** — form Founders / richiedi demo (prezzi da `GET /billing/plans`, annuale = 11 mesi).

---

**Versione**: v1.3 · 09-Nov-2026 (gallery 8 · D-149/150/151 · §8.13 MLS sito) · v1.2 20-Ott-2026 · v1.1 30-Set-2026 · base v1.0 Feb 2026

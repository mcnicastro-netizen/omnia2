# Capitolo 21 · Valutatore immobiliare

> **Cosa trovi in questo capitolo**
> Il **Valutatore immobiliare** stima il valore di mercato orientativo di un immobile residenziale in Italia. Esistono **due livelli**: **Stima rapida (base)** gratuita per privati registrati (1× ogni 12 mesi) e **Valutazione UNI 10750 + PDF** a **€2,99** con carta (Stripe). Il capitolo copre: dove trovi lo strumento, differenza base vs UNI, passi operativi, pagamento, report PDF, uso agenzia, affidabilità dati, limitazioni v1 e errori comuni.

**Cosa NON è (D-051 onestà — regola cardine)**
- Non è una **perizia bancaria**, una **CTU** né un **documento vincolante** per mutuo o successione.
- Non sostituisce un **perito iscritto all'Albo** o una valutazione ufficiale di banca/notaio.
- La stima base **non include** superficie commerciale UNI, coefficienti di merito né PDF.
- **Non è anonimo** in v1: serve account ImmobilCloud (login + email verificata per la stima gratis).
- Il debito **crediti agenzia** (6 cr base / 12 cr UNI) sul portale `/cloud` per agenti loggati **non è automatico** in v1 — il gate B2C fa pass-through, ma lo scaling crediti resta al caller applicativo (backlog).

---

## 21.1 · Cos'è il Valutatore OMNIA e dove lo trovi

**In una frase**
Un motore di stima mercato che, a partire da città, tipologia, superficie e altri input, calcola un **valore orientativo** (min / medio / max), **€/m²**, livello di **affidabilità** e — sul tier UNI — breakdown UNI 10750 + **report PDF** scaricabile.

**I quattro punti di contatto**

### A) Portale B2C ImmobilCloud — pagina dedicata (`/it/cloud/valutatore`)
- Due **tier card** affiancate: **Stima rapida GRATIS** vs **UNI 10750 + PDF €2,99**.
- Richiede **login** ImmobilCloud. Visitatore anonimo vede banner *"Per usare il valutatore devi essere registrato"* con link Accedi/Registrati.
- Pre-fill da query string: `?tier=base|uni&city=...&property_type=...&surface_sqm=...`

### B) Scheda annuncio ImmobilCloud (`PropertyDetailPage`)
- Box sotto il comparatore mutui: **Stima gratuita** + **Report UNI €2,99** con pre-compilazione città/tipologia/mq dall'annuncio.

### C) Home ImmobilCloud (`CloudHomePage`)
- ActionCard **"Valutatore immobiliare"** full-width sotto le tre card principali (Cerca / Vendi / Affitta).

### D) Agente loggato su `/cloud/valutatore`
- Stessa UI, copy **"Usa crediti agenzia"** / **"12 crediti agenzia"** al posto di €2,99 sul tier UNI.
- Pass-through al gate B2C (no Stripe). ⚠️ Debito crediti non scalato automaticamente da questa pagina in v1.

[SCREEN: valutatore-tier-scelta]

**Cross-ref agenzia (ImmoWeb)**
- **Cap. 7 · Fascicolo immobile** — stima base integrata al load pagina (bypass gate B2C, motore interno).
- **Cap. 20 · API Keys** — partner Track B: `POST /api/v1/valuator` (5 crediti Track B per chiamata UNI).

---

## 21.2 · Stima rapida gratuita (tier BASE)

**A cosa serve**
Capire in pochi minuti l'**ordine di grandezza** del valore di un immobile senza pagare.

**Prezzo B2C**: **GRATIS**

**Limite anti-abuso**
- **1 valutazione ogni 12 mesi** per account (controllo server-side su collection `b2c_valuation_usage`).
- Se esaurita → messaggio con **data reset** (`reset_at`) + suggerimento upsell verso tier UNI a €2,99.

**Requisiti**
- Account ImmobilCloud **loggato**.
- **Email verificata** (`email_verified = true`). Senza → errore *"Verifica l'email per usare la stima gratuita"*.

**Campi del form (7 input base)**
- Ubicazione: indirizzo (autocomplete), città, zona (opzionale).
- Immobile: tipologia (9 valori: appartamento, attico, loft, villa, monolocale, rustico/casale, ufficio, negozio, garage/box), **mq calpestabili** (min 10), stato conservativo (7 valori), classe energetica (opzionale), piano (opzionale).

**Cosa calcola il motore (base)**
1. Prezzo base €/m² da dataset **OMI/Borsino 2025** per città + fascia zona (centro / semicentro / periferia).
2. Fallback a **provincia** (geocoding Nominatim/ANNCSU) o **regione** se città non in dataset.
3. Moltiplicatori: tipologia · condizione · classe energetica · piano.
4. Coefficienti regionali (liquidità mercato + trend semestrale).
5. Superficie usata = **mq calpestabili** (`method: calpestabile_only`).
6. Comparables: fino a 10 annunci attivi simili (stessa città + tipologia) se disponibili.

**Cosa ottieni a schermo**
- Valore stimato medio + range min/max.
- €/m².
- Livello affidabilità: **alta** / **media** / **orientativa** (score 0–110).
- Disclaimer integrato.

**Cosa NON ottieni (base)**
- ❌ Superficie commerciale UNI 10750 ponderata.
- ❌ Coefficienti di merito (esposizione, vista, ascensore…).
- ❌ Bottone **Scarica PDF**.
- ❌ Sezione Pro / superfici accessorie.

Footer form base: *"1 valutazione ogni 12 mesi · nessun PDF"*.

---

## 21.3 · Valutazione UNI 10750 + PDF (tier UNI — a pagamento B2C)

**A cosa serve**
Stima più vicina a una **perizia light** da banca: superficie commerciale normata + merito immobile + **report PDF** brandizzato.

**Prezzo B2C privati**: **€2,99** one-shot **Stripe** (carta).
**Prezzo agenti** sul portale cloud: copy **12 crediti agenzia** (rail B2B, no carta).

**Limite giornaliero**: max **5 acquisti UNI/giorno** per utente B2C (`daily_limit_per_user` in catalogo prodotti).

**Campi aggiuntivi (tier UNI)**
Oltre ai 7 campi base, compaiono:

### Superfici commerciali UNI 10750 (11 componenti, mq opzionali)
Veranda, terrazzo, balcone, cantina, soffitta, box auto, posto auto scoperto, giardino villa, giardino condominiale, taverna, mansarda abitabile.

Ponderazione esemplificativa (UNI 10750 / DPR 138/1998):
| Componente | Peso indicativo |
|------------|:---------------:|
| Principale (calpestabile) | 100% |
| Balcone / terrazzo (fino 25 mq) | 30% |
| Veranda | 60% |
| Cantina / soffitta | 25% |
| Box auto | 50% |
| Posto auto scoperto | 20% |
| Giardino villa (fino 25 mq) | 10% |
| Mansarda abitabile | 80% |
| Taverna | 60% |

### Coefficienti di merito (opzionali)
- **Piano**: da seminterrato (−15%) ad attico panoramico (+10%).
- **Esposizione**: da nord (−4%) a sud (+5%).
- **Vista/affaccio**: da interno (−4%) a mare (+12%).
- **Riscaldamento**: da assente (−8%) a pompa calore (+4%).
- **Ascensore**: penalità forte se assente su piano alto (−10%).
- **Anno costruzione**: deperimento oltre 30 anni (max −20%).
- **Vincoli**: storico −10%, paesaggistico −5%.
- **Locazione in essere**: breve −5%, lunga −15%, nuda proprietà −30%.

Totale merito **cappato** tra −40% e +30%.

**Pagamento e entitlement**
1. Compili form UNI → click **Calcola UNI · €2,99** (o equivalente agente).
2. Se non hai già pagato → redirect **Stripe Checkout** hosted.
3. Webhook conferma pagamento → record `b2c_purchases` con `status=paid`, `expires_at = +24h`.
4. Entitlement legato al **payload_hash** (SHA-256 dei campi immobile): stesso immobile entro 24h **non ripaga**.
5. Pagine post-checkout: `/it/cloud/checkout/success` (polling stato) e `/it/cloud/checkout/cancel`.

**Output UNI aggiuntivo**
- Breakdown superficie commerciale (componente per componente).
- Tabella coefficienti merito applicati.
- Affidabilità potenzialmente più alta (+10 punti se compili Pro).
- Bottone **Scarica report PDF** (solo se entitled).

[SCREEN: valutatore-uni-pro-form]
[SCREEN: valutatore-pdf-download]

---

## 21.4 · Differenza base vs UNI (tabella utente)

| | **Stima rapida (base)** | **UNI 10750 + PDF** |
|---|------------------------|---------------------|
| **Prezzo privato** | Gratis | **€2,99** carta |
| **Frequenza** | 1× ogni 12 mesi | A ogni acquisto |
| **Login richiesto** | Sì | Sì |
| **Email verificata** | Sì (base) | Consigliata |
| **Superficie** | Calpestabile | Commerciale UNI ponderata |
| **Merito (vista, piano…)** | No | Sì |
| **PDF** | No | Sì (dopo pagamento) |
| **Upsell** | → verso UNI | — |
| **Agente ImmoWeb** | Pass-through gate | Pass-through (12 cr copy, debito non auto v1) |

---

## 21.5 · Come fare una stima base (passi UI)

1. Vai su **ImmobilCloud → Valutatore** (`/it/cloud/valutatore`) o clicca **Stima gratuita** da scheda annuncio.
2. Se non loggato → **Accedi** o **Registrati** (redirect con `?next=` alla pagina valutatore).
3. Seleziona card **Stima rapida GRATIS** (tab sinistra).
4. Compila: città, tipologia, mq (obbligatori), zona/indirizzo/stato/energia/piano (consigliati).
5. Click **Ottieni la stima gratuita**.
6. Leggi risultato: valore, range, €/m², affidabilità.
7. Se ti serve di più → banner verde **"Passa a UNI · €2,99"** (upsell).

[SCREEN: valutatore-base-risultato-upsell]

**Se vedi errore limite**
- *"Hai già usato la stima gratuita di quest'anno"* → attendi la data **reset_at** indicata oppure passa al tier UNI a pagamento.

---

## 21.6 · Come ottenere il report UNI (passi UI)

1. Seleziona card **UNI 10750 + PDF** (tab destra) — oppure upsell da risultato base.
2. Compila campi base + superfici accessorie + merito (consigliato per stima accurata).
3. Click **Calcola UNI · €2,99** (privato) o **Calcola UNI (crediti agenzia)** (agente).
4. **Privato senza entitlement** → redirect Stripe → paga €2,99 → torna su `/checkout/success`.
5. Ricalcola o scarica: **Scarica report PDF**.
6. Il PDF include: dati immobile, valore + range, breakdown UNI, merito, comparables (se presenti), metodologia, disclaimer. Se agente loggato → **branding agenzia** (nome, colori, contatti).

**Stripe non configurato**
- Se ambiente preview senza `STRIPE_ENABLED=true` → checkout restituisce *"Il pagamento è in preparazione"*. In produzione va abilitato Stripe test/live.

---

## 21.7 · Valutatore per le agenzie (B2B)

**Stesso motore, rail diverso**

| Canale | Base | UNI + PDF |
|--------|:----:|:---------:|
| Portale `/cloud` (agente loggato) | Pass-through gate | Pass-through + copy 12 cr |
| Fascicolo immobile (Cap. 7) | Stima base integrata | Non esposto in UI fascicolo v1 |
| Piani B2B (`plans.py`) | 6 crediti (€0,30) | 12 crediti (€0,60) |
| API Track B (`/api/v1/valuator`) | — | 5 crediti Track B (€0,15) |

**Fascicolo immobile (Cap. 7)**
- Al load pagina chiama il motore in **base mode** internamente (`_estimate_value_core`) — **senza** gate B2C né limite 12 mesi.
- Mapping condizioni fascicolo → valutatore: *ottime→ottimo*, *buone→buono*.

**Onestà v1 — debito crediti agente su `/cloud`**
- Il gate B2C **non blocca** l'agente sul tier UNI (pass-through).
- Lo **scaling automatico** di 6/12 crediti dal wallet agenzia **non è implementato** su questa pagina in v1. Backlog prodotto.

---

## 21.8 · Affidabilità, dati di mercato e comparables

**Dataset prezzi**
- **Città curate** OMI/Borsino 2025 (`CITY_PRICES`) — centinaia di comuni.
- **Fallback provincia** via geocoding (Nominatim / ANNCSU ISTAT) con sconto 8–12% vs capoluogo per comuni piccoli.
- **Fallback regionale** se provincia non risolvibile.

**Endpoint pubblico metadati**
- Pagina info copertura: elenco città/province/regioni, tier zona, tipologie supportate, norme UNI 10750 applicate, anno dati 2025.

**Livelli affidabilità**

| Livello | Significato tipico |
|---------|-------------------|
| **Alta** | Città in dataset + zona esplicita + tipologia + condizione note |
| **Media** | Città OK ma zona inferita, o dati parziali |
| **Orientativa** | Fallback provinciale/regionale, o input incompleti |

**Comparables**
- Query su annunci **attivi**, **pubblici**, **moderati** (non pending/rejected) stessa città + tipologia.
- Mostra fino a 6 in UI, fino a 10 in response.
- Se zero comparables → stima basata solo su dati statistici (normale per città/periferie con poco stock).

**Notice fallback provincia**
- Se comune non in dataset diretto: banner *"Comune non in dataset diretto — usata media provinciale di [Provincia] come riferimento"*.

---

## 21.9 · Limitazioni oneste (D-051)

| Limitazione | Dettaglio |
|-------------|-----------|
| Non perizia vincolante | Disclaimer obbligatorio su ogni response e PDF |
| Login obbligatorio | Nessuna stima anonima illimitata |
| Base: no PDF/merito | Tier base non può accedere a Pro né PDF |
| UNI: pagamento richiesto (B2C) | 402 se `commercial_surfaces` o `merit` senza entitlement |
| Entitlement 24h | Stesso payload_hash; cambio immobile = nuovo pagamento |
| Stripe env | Checkout 503 se Stripe non abilitato in ambiente |
| Agente: crediti non auto | Pass-through senza debito wallet automatico su `/cloud` v1 |
| Lead capture form | Backend supporta `name`+`email` → `valuation_leads`, ma **form B2C dual-tier v1 non espone** campi contatto opzionali |
| Widget embed valutatore | Esiste su Track B (Cap. 20) — rail crediti partner, non tier B2C €2,99 |
| Visura/planimetria | Non integrate nel valutatore (prodotti B2C fase 2) |

---

## 21.10 · Errori comuni

| Problema | Causa | Cosa fare |
|----------|-------|-----------|
| *"Per usare il valutatore devi essere registrato"* | Non loggato | Accedi o registrati |
| *"Verifica l'email"* | Email non verificata | Conferma email da impostazioni account |
| *"Hai già usato la stima gratuita"* | Limite 12 mesi | Attendi `reset_at` o passa a UNI €2,99 |
| *"Valutazione UNI a €2,99"* (402) | Tier UNI senza pagamento | Completa checkout Stripe |
| PDF non scarica (402) | Manca entitlement UNI | Paga €2,99 o usa tier base senza PDF |
| *"Il pagamento è in preparazione"* | Stripe non configurato | Ambiente dev — abilitare Stripe test |
| Pro/superfici non visibili | Sei su tier base | Passa a card UNI 10750 + PDF |
| Valore strano per paese piccolo | Fallback provinciale | Normale — affidabilità "orientativa" |
| Agente: UNI gratis ma crediti non scalati | Pass-through v1 | Atteso — debito automatico in backlog |
| Fascicolo non mostra stima | Manca città o mq | Compila dati obbligatori immobile |

---

## 21.11 · Privacy

- La stima usa i dati immobile che inserisci; non vengono pubblicati.
- Account ImmobilCloud: trattamento dati secondo policy piattaforma (cross-ref **Cap. 19 · Impostazioni**).
- Collection `b2c_valuation_usage`: traccia solo `user_id`, tier, timestamp — per rate limit.
- Collection `b2c_purchases`: storico acquisti Stripe (product_key, session_id, payload_hash, scadenza entitlement).
- Lead `valuation_leads`: popolata solo se caller API invia `name`+`email` — **non dal form UI v1**.

---

## 21.12 · Collegamenti utili

- **Cap. 7 · Fascicolo immobile** — stima base integrata (agente, bypass gate).
- **Cap. 11 · Mutui comparatore** — dopo la stima, simula la rata per l'acquirente (box mutui anche su scheda annuncio).
- **Cap. 19 · Impostazioni** — verifica email, profilo account ImmobilCloud.
- **Cap. 20 · API Keys / Track B** — widget valutatore partner (`POST /api/v1/valuator`, 5 cr).
- **PRICING_B2C.md** — listino €2,99 UNI + regole anti-abuso.

---

**Versione**: v1.0 · Ago 2026 (post B2C-VAL-01 · dual-tier base 1×/12m + UNI €2,99 Stripe + PDF paywall)

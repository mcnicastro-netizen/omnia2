# Capitolo 19 · Impostazioni agenzia

> **Versione**: v1.0 · Feb 2026 · Onestà documentale D-051
> **Codice coperto**:
> - `frontend/src/apps/immoweb/SettingsPage.jsx` (358 righe · 5 sezioni form)
> - `backend/apps/immoweb/agencies.py` (180 righe · GET/PATCH `/agencies/me`)
> - `backend/shared/models/agency.py` (305 righe · `AgencyInDB`, `AgencyPublic`, `AgencyUpdate`, 5 sotto-schemi)
> - `frontend/src/apps/immoweb/pages/BillingPage.jsx` (235 righe · piani + credit packages + checkout Stripe)
> - `backend/apps/billing/routes.py` (473 righe · endpoint billing)
> - `backend/apps/billing/plans.py` (164 righe · LAUNCH_PLANS Founders + POST_TRACTION_PLANS)

> ⚠️ **Nota D-051 chiave**: la SettingsPage v1 copre **solo 5 sezioni di anagrafica agenzia + modalità sito web**. NON è un pannello impostazioni completo. Molti attributi presenti nello schema `AgencyInDB` (logo, colori, REA, FIAIP, plan_type, credits_mode) **non hanno UI di modifica v1**. Team, API Keys, Domain Vault, Notifiche, Billing sono pagine separate documentate rispettivamente in Cap. 13, Cap. Track B (futuro), Cap. 17, Cap. 18, e questa stessa pagina §19.10.

---

## 19.1 · Cos'è "Impostazioni agenzia" in OMNIA v1

**Definizione operativa**: SettingsPage.jsx è il pannello **anagrafica agenzia** con 5 sezioni compilabili + selezione modalità sito web. Aggiornabile solo dal titolare (`agency_admin` owner).

**Non è**:
- un centro impostazioni multi-tab (identità / fatturazione / team / notifiche / integrazioni)
- una pagina di gestione utenti (→ Cap. 13 Team & Ruoli, pagina `/app/settings/members`)
- una pagina di billing/piani (→ §19.10 BillingPage, pagina `/app/settings/billing`)
- una pagina di dominio custom (→ Cap. 17 Domain Vault, pagina `/app/settings/domain-verify`)
- una pagina di API keys (→ pagina `/app/api-keys`, non documentata come capitolo)

**È**:
- il posto dove il titolare compila `display_name`, `branding.tagline`, dati fiscali (`legal_name` + VAT + CF), indirizzo agenzia, contatti (email + telefono), e sceglie **modalità sito** (`external` URL vs `omnia_template`)
- l'endpoint `PATCH /api/app/agencies/me` in un unico save con validazione backend Pydantic (`AgencyUpdate`)

---

## 19.2 · Dove trovarlo

**In ImmoWeb**: menu laterale `AgencyShell` → voce **"Impostazioni"** (`current="settings"`). Route frontend: `/app/settings/agency`.

**Permessi accesso**:
- Titolare (`agency_admin` owner della propria agency): può leggere e modificare
- Super_admin: può leggere e modificare qualunque agenzia
- Agent/segreteria: possono aprire la pagina in read-only? **No** — l'endpoint PATCH usa `require_roles("agency_admin", "super_admin")` e restituisce 403 se ruolo diverso.

---

## 19.3 · Sezione 1 · Identità agenzia

**Campi UI**:
- `display_name` (input testo, richiesto min 2 max 120 char) — nome commerciale visualizzato ovunque nell'app + su portale pubblico
- `branding.tagline` (input testo opzionale, max 200 char) — slogan/motto visualizzato nell'header del portale pubblico

**Campi backend schema NON in UI**:
- `branding.logo_url` (max 500 char) — presente in `AgencyBranding` ma **nessun uploader v1**
- `branding.primary_color` (default `#0B1E3F`) — schema-only
- `branding.accent_color` (default `#1F6B5C`) — schema-only

**Note D-051**: il brand extractor (Cap. 8 Sito web) può popolare `website.extracted_profile` e `website.theme_config` con logo/colori estratti automaticamente. La Settings NON ha un uploader manuale.

---

## 19.4 · Sezione 2 · Dati fiscali

**Campi UI**:
- `fiscal.legal_name` (input testo, richiesto min 2 max 200 char) — ragione sociale ("Immobiliare Rossi S.r.l.")
- `fiscal.vat_number` (input testo opzionale, max 20 char) — Partita IVA IT
- `fiscal.fiscal_code` (input testo opzionale, max 20 char) — Codice Fiscale IT

**Campi backend schema NON in UI**:
- `fiscal.rea` (max 30 char) — Repertorio Economico Amministrativo, schema-only
- `fiscal.fiaip_code` (max 30 char) — codice agente FIAIP, schema-only

**Validazioni v1**:
- Nessuna validazione formato Partita IVA IT (11 cifre)
- Nessuna validazione formato Codice Fiscale (16 char)
- Nessun controllo unicità VAT (due agenzie possono avere stessa VAT — documentato)

---

## 19.5 · Sezione 3 · Indirizzo agenzia

**Campi UI**:
- `address.street` (input testo, opzionale max 200 char) — via + civico
- `address.city` (input testo, opzionale max 100 char)
- `address.province` (input testo max 2 char + uppercase automatico) — es. "RM", "MI"
- `address.postal_code` (input testo max 10 char)

**Campi backend schema NON in UI**:
- `address.country` (default `"IT"`, max 2 char) — hard-coded IT, nessun selector v1

**Note**: l'indirizzo compare sul portale pubblico agenzia (`/agenzia/{slug}`) e nel footer del sito omnia_template (Cap. 8). Non è geocoded (nessuna lat/lng), non è validato contro un database di CAP italiani.

---

## 19.6 · Sezione 4 · Contatti pubblici

**Campi UI**:
- `contact.email` (input tipo email, opzionale) — email visibile sul portale pubblico
- `contact.phone` (input testo max 30 char) — telefono agenzia visibile sul portale pubblico

**Campi backend schema NON in UI**:
- `contact.website` (max 200 char) — **duplicato** di `website.external_url`, presente nello schema ma non usato v1

**Note**: la `contact.email` è distinta dall'email di login del titolare (`user.email`). La `contact.email` è pubblica, la `user.email` è privata. Documentato onestamente.

---

## 19.7 · Sezione 5 · Sito web · 2 modalità mutually exclusive

**Modalità disponibili** (tramite bottoni cliccabili, toggle off al secondo click):

### Modalità A · `external` [SCREEN: cap19-settings-website-external]
Il titolare **ha già un sito web** e vuole solo che OMNIA gli produca il **feed XML** delle sue proprietà.

- Campo `website.external_url` (input URL, es. `https://www.tuoagenzia.it`)
- Nessun'altra configurazione richiesta
- OMNIA espone il feed XML a `/api/app/publishing/feed/{agency_slug}.xml` che il sito esterno può consumare

### Modalità B · `omnia_template` [SCREEN: cap19-settings-website-template]
Il titolare **non ha un sito** e vuole che OMNIA gli generi un portale con template.

- 3 preview visualizzate: `minimal`, `elegant`, `bold`
- ⚠️ **Tutti e 3 template marcati "presto disponibile" in v1** (mostra `settings.website_template_soon`)
- Nessun bottone "Seleziona template" funzionante v1
- Documentato onestamente: la Modalità B è **UI stub** senza backend template rendering v1
- Il sito viene creato altrove: Cap. 8 Sito web (con brand extractor + custom_domain via Cap. 17)

**Toggle off**: cliccare di nuovo il bottone modalità già attiva → deseleziona (`mode = null`).

**Salva backend**:
- Se `mode = "external"` → salvato `website.external_url`
- Se `mode = "omnia_template"` → salvato solo il flag (nessun template_id v1 selezionabile)
- Se `mode = null` → azzerato (nessuna modalità)

---

## 19.8 · Permessi e ownership

**Endpoint backend**: `PATCH /api/app/agencies/me` (`apps/immoweb/agencies.py:128-160`).

**Guardie**:
1. `require_roles("agency_admin", "super_admin")` decorator: solo questi 2 ruoli entrano.
2. `agency_ids` presente nell'utente: se lista vuota → HTTP 404 `no_agency`.
3. `existing["owner_id"] == user["id"]` **oppure** `user["role"] == "super_admin"`: altrimenti HTTP 403 `not_owner`.

**Conseguenza operativa**:
- Il collaboratore `agency_admin` invitato via magic-link (Cap. 13) può leggere `GET /me` **ma NON può fare PATCH** — non è owner della sua agency. Documentato onestamente.
- Solo il titolare che ha CREATO l'agency (via `POST /api/app/agencies` in onboarding) è il `owner_id`.

**Trasferimento ownership**: NON supportato v1. Documentato in Cap. 13 § limitazioni.

---

## 19.9 · Endpoint PATCH · come funziona

**URL**: `PATCH /api/app/agencies/me`
**Body**: JSON conforme al modello Pydantic `AgencyUpdate` (`shared/models/agency.py:149`) — tutti i campi opzionali.

```json
{
  "display_name": "Immobiliare Rossi S.r.l.",
  "fiscal": {"legal_name": "...", "vat_number": "..."},
  "address": {"street": "...", "city": "..."},
  "contact": {"email": "...", "phone": "..."},
  "branding": {"tagline": "..."},
  "website": {"mode": "external", "external_url": "https://..."}
}
```

**Logica applicativa**:
- Il frontend fa `cleanGroup(obj)` che rimuove chiavi con stringa vuota o null — permette upsert parziale.
- Il backend applica `payload.model_dump(exclude_unset=True)` e fa `$set` in Mongo.
- `mode: null` viene **preservato esplicitamente** (permette al titolare di deselezionare la modalità sito).

**Response**: agenzia aggiornata (schema `AgencyPublic`).

**Toast UI**: banner emerald embedded (`text-emerald-800 bg-emerald-50`) mostrato per 2500ms dopo save riuscito. **NON usa la libreria `sonner`** (Cap. 18) — è un toast locale al form. Errori mostrati come banner rosso persistente finché non si tenta un nuovo save.

---

## 19.10 · Billing · pagina separata (BillingPage.jsx)

**Route frontend**: `/app/settings/billing`. Componente `BillingPage.jsx` (235 righe).

**Stato billing (feature flag)**:
- Se `STRIPE_ENABLED != "true"` in env → endpoint restituiscono **HTTP 503** con `{"error": "stripe_not_configured", "message": "Billing è in preparazione."}`. In UI: la pagina carica ma i piani non sono attivabili.
- Se `STRIPE_ENABLED == "true"` E `STRIPE_SECRET_KEY` presente → billing operativo.

### 19.10.1 · Sezione piano corrente + wallet crediti

**Cosa mostra**:
- **Piano corrente**: dal `GET /billing/subscription`. Se nessun piano attivo → mostra "Nessuno" e "Attiva un piano per iniziare".
- **Wallet crediti**: `sub.wallet.balance` (integer, es. `120 crediti`). Se nessun subscription → 0.

**Stato subscription**: mostra `activeSub.status` (es. `active`, `past_due`, `canceled`) sotto il nome del piano.

### 19.10.2 · Sezione piani disponibili · Fase Founders

**Endpoint**: `GET /billing/plans` (public, no auth).

**Fase attiva** (via env `PRICING_PHASE`):
- `launch` (default) → `LAUNCH_PLANS`: Starter €49/mese, Pro €99/mese, Agency €249/mese, Enterprise €299/mese
- `post_traction` → `POST_TRACTION_PLANS`: Starter €79/mese, Pro €179/mese, Agency €349/mese, Enterprise €499/mese

**Piano Founders (LAUNCH)**:
| Tier | Prezzo mese | Prezzo anno | Max agenti | Max immobili | Crediti/mese |
|------|:-----------:|:-----------:|:----------:|:------------:|:------------:|
| starter | €49 | €490 | 3 | 30 | 120 |
| pro | €99 | €990 | 10 | 200 | 1200 |
| agency | €249 | €2490 | ∞ | ∞ | 3600 |
| enterprise | €299 | €2990 | ∞ | ∞ | 3600 |

**Nota Enterprise**: "TBD in sessione dedicata (posizionamento + Custom API). Mantenuto con prezzi legacy per non rompere il modello dati esistente." (commento nel codice, `plans.py:74-84`).

**Bottone "Attiva"** → `POST /billing/checkout` con `{plan_tier, billing_cycle: monthly|yearly}` → redirect a `data.checkout_url` (Stripe hosted checkout).

### 19.10.3 · Sezione credit packages (top-up)

**Endpoint**: `GET /billing/plans` restituisce anche `credit_packages`.

**Ratio ufficiale Founder** (`plans.py:130`): **1 credito = €0,05** (20 crediti/€).

| Package key | Crediti | Prezzo |
|-------------|:-------:|:------:|
| `pkg_400` | 400 | €20 |
| `pkg_1000` | 1000 | €50 |
| `pkg_2000` | 2000 | €100 |
| `pkg_5000` | 5000 | €250 |
| `pkg_10000` | 10000 | €500 |
| `pkg_20000` | 20000 | €1000 |

**Nota D-051**: nessuno sconto volume v1. Tutti i pacchetti al ratio identico €0,05/credito. Documentato onestamente.

**Bottone "Acquista"** → `POST /billing/credits/purchase` con `{package_key}` → redirect a `data.checkout_url`.

### 19.10.4 · Customer portal Stripe

**Endpoint**: `POST /billing/portal` → redirect a `stripe.com/p/session/*` (Stripe hosted customer portal).

**Cosa può fare l'utente nel portal Stripe**:
- Vedere le fatture past (last 3 anni, gestite da Stripe)
- Aggiornare metodo di pagamento
- Cambiare piano (upgrade/downgrade)
- Cancellare sottoscrizione (con dunning automatico Stripe)
- Aggiornare fatturazione (indirizzo billing, VAT)

**Cosa NON può fare nel portal**:
- Acquistare credit packages (deve tornare in OMNIA `/app/settings/billing`)
- Gestire team members (Cap. 13, pagina separata)

### 19.10.5 · Polling status post-checkout

Il redirect Stripe `success_url` include `?session_id={CHECKOUT_SESSION_ID}&ok=1`. La BillingPage rileva `session_id` in query e fa polling `GET /billing/status/{session_id}` finché lo stato non è `complete`. Al `complete`:
- Ricarica `GET /billing/subscription`
- Mostra `toast.success("Pagamento completato ✓")` (usa sonner)

Se lo stato resta pending o `?cancel=1`:
- Mostra `toast.error("Pagamento fallito")` o silent (cancel).

---

## 19.11 · Chi NON è coperto in Settings v1

Molte impostazioni logiche che l'utente si aspetta di trovare in una "pagina Settings" sono **pagine separate** in OMNIA v1. Elenco onesto:

| Cosa cerca l'utente | Dove è veramente | Cap. |
|---------------------|-------------------|:----:|
| Gestione team / collaboratori | `/app/settings/members` (MembersPage.jsx) | 13 |
| Invito nuovi collaboratori | `/app/settings/members` → "Invita" (InviteMemberModal) | 13 |
| Cambio piano | `/app/settings/billing` (BillingPage) o Stripe portal | 19 (§19.10) |
| Acquisto crediti | `/app/settings/billing` (BillingPage) | 19 (§19.10) |
| Fatture | Stripe customer portal (link da BillingPage) | 19 (§19.10.4) |
| Custom domain | `/app/settings/domain-verify` (DomainVerifyPage) | 17 |
| Domain sovereignty policy | `/app/domain-sovereignty-policy` (page pubblica) | 17 |
| API Keys | `/app/api-keys` (ApiKeysPage) | Track B (futuro) |
| Notifiche / preferenze email | ❌ NON esiste UI v1 | 18 (§18.10) |
| Sito web (template + brand) | Cap. 8 (extractor + themes + custom_domain) | 8 |
| Virtual staging credits guardrail | ❌ backlog A-013 | 9 (§9.5) |

---

## 19.12 · Errori comuni

### E1 · HTTP 403 `not_owner`
Il collaboratore agency_admin invitato via magic-link (Cap. 13) **non è owner** dell'agency creata dal titolare originale. Può leggere ma non modificare.

- **Chi lo vede**: agency_admin invitato (non fondatore).
- **Fix v1**: solo il titolare fondatore può modificare. Backlog: transfer ownership agenzia (non pianificato v1).

### E2 · HTTP 404 `no_agency`
L'utente autenticato non ha `agency_ids` popolato.

- **Chi lo vede**: utente registrato che ha saltato l'onboarding.
- **Fix**: completa l'onboarding (crea agency da `/app/onboarding`).

### E3 · Toast "Errore durante il salvataggio"
Errore di validazione Pydantic (es. `display_name < 2` char, VAT > 20 char, primary_color non hex, ecc.).

- **Fix**: guarda il messaggio errore inline (banner rosso). Se il messaggio è generico → dev deve controllare il response del PATCH.

### E4 · "Ho cliccato template Elegant ma non succede nulla"
Corretto: i 3 template omnia (`minimal`, `elegant`, `bold`) sono **stub UI marcati "presto disponibile"** v1. Nessun click handler attivo.

- **Fix**: aspetta v1.1 con template rendering attivo (backlog A-024, non ancora aperto).

### E5 · "Non trovo un uploader logo"
Corretto: v1 la Settings **NON ha uploader logo**. Il logo viene inferito dal brand extractor (Cap. 8) o non è visualizzato.

- **Fix**: usa Cap. 8 `POST /api/app/website/extract-from-url` per estrarre logo dal sito esistente. Backlog A-025 uploader manuale logo (non ancora aperto).

---

## 19.13 · Limitazioni v1 (elenco esaustivo · D-051)

### Cosa NON esiste nella SettingsPage v1

**Campi schema-only (nessuna UI di modifica)**:
- ❌ `branding.logo_url` (nessun uploader)
- ❌ `branding.primary_color` (default `#0B1E3F`)
- ❌ `branding.accent_color` (default `#1F6B5C`)
- ❌ `fiscal.rea`
- ❌ `fiscal.fiaip_code`
- ❌ `contact.website` (duplicato di `website.external_url`)
- ❌ `address.country` (default `IT` hard-coded)
- ❌ `plan_type` (turnkey/whitelabel/hybrid — decisione backend, no UI toggle)
- ❌ `group_id` / `branch_code` (M2.5.1 franchising — no UI v1)

**Template omnia stub**:
- ❌ Preview `minimal` / `elegant` / `bold` marcati "presto disponibile"
- ❌ Nessun `template_id` selezionabile via UI v1
- ❌ Nessun rendering template attivo (Cap. 8 usa il sito esterno o brand extracted, non i 3 template stub)

**Validazioni mancanti**:
- ❌ Nessuna validazione formato Partita IVA IT (11 cifre)
- ❌ Nessuna validazione Codice Fiscale IT (16 char)
- ❌ Nessun controllo unicità VAT tra agenzie
- ❌ Nessun autocomplete Google Places per indirizzo
- ❌ Nessuna geocodifica lat/lng
- ❌ Nessuna validazione CAP contro database CAP italiani
- ❌ Nessuna validazione telefono formato IT/internazionale

**Sezioni non presenti in Settings v1** (sono in altre pagine):
- ❌ Team & Ruoli (→ Cap. 13, `/app/settings/members`)
- ❌ Billing / Piani / Crediti (→ §19.10, `/app/settings/billing`)
- ❌ Custom Domain / DNS (→ Cap. 17, `/app/settings/domain-verify`)
- ❌ API Keys / Webhook (→ pagina `/app/api-keys`)
- ❌ Notifiche / preferenze email (→ Cap. 18, non esiste UI)
- ❌ Log attività / Audit trail (→ Cap. 18, non esiste UI)
- ❌ Cambio password / MFA / sessioni attive (→ pagina auth separata)

**Operazioni non supportate**:
- ❌ Trasferimento ownership agenzia (owner_id immutabile v1)
- ❌ Rinomina slug pubblico (slug creato all'onboarding, non modificabile v1)
- ❌ Import/export impostazioni (nessuna funzione JSON export)
- ❌ Storico modifiche impostazioni (nessun audit trail settings)
- ❌ Rollback modifica errata (nessun undo)
- ❌ Anteprima "come apparirà" prima di salvare (nessun preview render)

**Toast/UX**:
- ❌ Il toast success NON usa `sonner` (Cap. 18) — usa banner emerald embedded locale al form
- ❌ Il toast si autoazzera dopo 2500ms (non configurabile)
- ❌ Nessun undo dopo save (Ctrl+Z non funziona)

---

## 19.14 · Collegamenti agli altri capitoli

| Cap. | Modulo | Come si collega a Settings |
|:----:|--------|----------------------------|
| 1 | Primo accesso | L'onboarding crea l'agenzia con `display_name` e `fiscal.legal_name`. Post-onboarding la Settings permette di modificarli. |
| 3 | Immobili | Le immobili pubblicate ereditano `agency.address` per il portale pubblico. |
| 6 | Portali / Publishing | Il feed XML espone `contact.email` e `contact.phone` ai portali. |
| 8 | Sito web agenzia | La modalità `website.mode` in Settings decide se OMNIA fa feed XML (`external`) o rende template (`omnia_template`, stub v1). Cap. 8 dettaglia il brand extractor e temi. |
| 13 | Team & Ruoli | La Settings gestisce **anagrafica agenzia**, NON i membri. I membri stanno in `/app/settings/members` (`MembersPage.jsx`). |
| 17 | Domain Vault | La Settings NON gestisce il custom domain. Custom domain sta in `/app/settings/domain-verify` (`DomainVerifyPage.jsx`). `existing_domain` in agency è impostato in signup, non da Settings. |
| 18 | Notifiche | La Settings NON ha toggle preferenze notifiche v1 (backlog A-021). |
| 19 § 10 | Billing | Pagina separata `BillingPage.jsx` in `/app/settings/billing`. Piani Founders €49/€99/€249, crediti €0,05/cad, checkout Stripe. Se `STRIPE_ENABLED != true` → HTTP 503 "Billing in preparazione". |

---

## 19.15 · Screenshot da produrre (placeholder)

- `[SCREEN: cap19-settings-identity]` — SettingsPage sezione Identità (display_name + tagline)
- `[SCREEN: cap19-settings-fiscal]` — SettingsPage sezione Dati fiscali (legal_name + VAT + CF)
- `[SCREEN: cap19-settings-address]` — SettingsPage sezione Indirizzo (street + city + province + CAP)
- `[SCREEN: cap19-settings-contact]` — SettingsPage sezione Contatti (email + telefono)
- `[SCREEN: cap19-settings-website-external]` — SettingsPage modalità Sito web external con URL input
- `[SCREEN: cap19-settings-website-template]` — SettingsPage modalità Sito web omnia_template con 3 stub "presto disponibile"
- `[SCREEN: cap19-billing-plans]` — BillingPage con listino Founders (Starter/Pro/Agency/Enterprise)
- `[SCREEN: cap19-billing-credits]` — BillingPage sezione credit packages 400-20000

Totale: **8 screenshot Cap. 19** da aggiungere a `screenshots-index.md`.

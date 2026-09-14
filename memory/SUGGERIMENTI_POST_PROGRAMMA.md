# 💡 SUGGERIMENTI POST-PROGRAMMA — da esaminare quando OMNIA è completa

> Nessuno di questi è un fix urgente. Sono osservazioni raccolte durante l'audit
> profondo del codice per pilastri (architettura, qualità, funzionalità). Il
> Founder ha chiesto di memorizzarli e valutarli **solo a programma ultimato**.

---

## 🏗️ Architettura — pulizie latenti

### 1. Consolidare 19 helper duplicati in `shared/auth/tenant.py`
Copiati/incollati fra 19 router: `_agency`, `_agency_id`, `_agency_id_of`,
`_agency_of`, `_agency_for`, `_require_agency`, `_public`, `_strip`,
`_public_channel`.
**Rimedio proposto**: creare `shared/auth/tenant.py::require_agency_id(user)` e
`shared/db/serializers.py::strip_id(doc)`, migrare gradualmente file per file.
**ROI**: −200 righe boilerplate, previene divergenze quando dovremo introdurre
selezione multi-agency per `group_admin`.

### 2. Fix fallback preview URL obsoleto nei ~30 test file
Fallback hardcoded `https://omnia-crm-docs.preview.emergentagent.com`
è **la preview della prima sessione**. Se un giorno cambia il preview URL
il fallback punterà al vecchio. **Rimedio**: `pytest.ini` con `env-file
backend/.env` e rimuovere del tutto il fallback.

### 3. Consolidare 11 file frontend che duplicano `const BACKEND_URL = process.env.REACT_APP_BACKEND_URL`
Tutti dovrebbero usare `shared/lib/api.js` (già esistente). File coinvolti:
`ImmocloudApp.jsx`, `PropertyDetailPage.jsx`, `AddressAutocomplete.jsx`,
`ValuatorPage.jsx`, `WebsitePage.jsx`, `ModerationPage.jsx`, `PublishingCenter.jsx`,
`DomainVerifyPage.jsx`, `AgenziesLandingPage.jsx`, `WidgetsShowcasePage.jsx`,
`MortgageComparator.jsx`.

### 4. Split file monolitici (>500 righe)
- `properties.py` 717 → `_crud.py` + `_photos.py` + `_import.py`
- `themes.py` 777 → `_engine.py` + `_share.py` + `_seo.py`
- `virtual_staging.py` 750 → `_pipeline.py` + `_reaper.py`
- `al_agent.py` 706 → `_tools.py` + `_stream.py`
- `clients_ai_import.py` 631 → `_parser.py` + `_mapper.py`

### 5. Unico crypto system
Deprecare `OMNIA_PORTAL_ENC_KEY` (Fernet, per `portals.py` legacy) e migrare le
poche credenziali residue su `CREDENTIALS_MASTER_KEY` (AES-256-GCM). Rende
un solo pattern crypto in tutto il codebase.

### 6. Legacy `portals.py` fisicamente rimosso
Il menu sidebar già non lo mostra (fix P0-F), ma il router `/api/app/portals/*`
è ancora attivo. A programma completato migrare i test residui su
`/api/app/publishing/*` e rimuovere il file.

### 7. Cartelle frontend con doppia convenzione
`apps/immoweb/*.jsx` (18 file) e `apps/immoweb/pages/*.jsx` (11 file). Migrare
tutti sotto `pages/` e componenti sotto `components/`.

---

## 🎨 UX — piccole vittorie che non ho chiesto e non ho fatto

### 8. **Onboarding wizard sub-step Stripe**
Alla registrazione nuova agenzia, sub-step "Attiva prova gratuita 14 giorni"
che apre subito Stripe Checkout in `mode=subscription` con `trial_period_days:
14`. Elimina il trial-abandonment tra registrazione e primo login.

### 9. **Dashboard KPI storico + trend delta**
I KPI ora sono valori istantanei. Aggiungere `delta_label` (+8% vs 7gg fa) e
sparkline SVG inline sotto ogni card. Impatto UX ~+15% sul dwell time.

### 10. **Modal "Ricarica crediti" contestuale**
Quando un servizio a consumo (valuator, HAL, video) fallisce con 402
`insufficient_credits`, invece di errore secco mostrare modal inline con i 3
pacchetti crediti (checkout diretto).

### 11. **Email lead: template dark mode + click tracking**
Il template Resend attuale è OK ma monocromo. Aggiungere versione dark mode
inline + UTM tracking per capire quale sorgente lead genera più conversioni.

---

## 🔒 Sicurezza / compliance

### 12. **Rate limit per endpoint pubblici (unauth)**
`/api/cloud/property/{pid}`, `/api/mls-box/agency/{slug}`, `/api/feed/{slug}.xml`
non hanno rate-limit. Un competitor potrebbe scrapare l'intero portafoglio via
enumerazione slug. **Rimedio**: middleware `slowapi` con 60 req/min per IP.

### 13. **Content Security Policy sulle pagine iframe MLS Box**
Il render `/api/mls-box/agency/{slug}.html` non ha CSP. Aggiungere
`X-Frame-Options: SAMEORIGIN` con whitelist per il dominio dell'agenzia
(config in `agencies` collection, campo `allowed_embed_origins`).

### 14. **Log audit centralizzato per super_admin actions**
`db.audit_log` esiste ma è usato solo da Privacy Gate. Estenderlo a:
approvazioni moderazione, delete agency, credit ledger adjustments manuali,
promozioni ruolo.

### 15. **Backup automatico DB su Object Storage**
Snapshot mongodump giornaliero su bucket S3 dedicato con TTL 30gg. Non c'è
oggi. Rimedio: cron in `apps/immoweb/cron.py` (che oggi è quasi vuoto).

---

## 📈 Business / go-to-market

### 16. **Onboarding "Il tuo primo immobile" bonus 50 crediti**
Regala 50 crediti al primo immobile pubblicato → migliora activation-rate.

### 17. **Referral B2B**
"Invita un'altra agenzia → 100 crediti a te e 100 a lei quando attiva Pro".
Meccanismo virale zero-cost, calibrato sul ns. plan launch pricing.

### 18. **API rev-share partner dashboard**
Il gateway v1 già registra `partner_id`. Manca una UI dedicata dove il partner
vede utilizzo mensile + saldo commissioni maturate. Rimane sui documenti roadmap.

---

## 🔬 Analytics

### 19. **Analytics MLS Box embed**
Il widget renderizzato via iframe non tracca click sul detail_url. Aggiungere
endpoint `/api/mls-box/track/{property_id}?src=mls_box_embed` per contare le
conversioni portale-agenzia (fondamentale per convincere altre agenzie ad
adottare il widget).

### 20. **Funnel Stripe abbandono**
Metriche: `checkout.session.created` → `checkout.session.expired` vs
`checkout.session.completed`. Dashboard super_admin con conversion-rate.

---

## 🧪 Testing

### 21. **Fix test pre-esistente `test_immobilcloud_m3s4_contact.py`**
Fixture `agency_id` cerca `PROPERTY_ID` hardcoded che non esiste nel DB.
Rendere la fixture idempotente: `create-if-missing`.

### 22. **CI GitHub Actions**
Il repo su GitHub non ha workflow. Aggiungere `.github/workflows/tests.yml`
con pytest su push a main + notifica Discord/Telegram su failure.

---

## 📋 Manuale Operativo + Academy (in coda)

Come richiesto dal Founder ("tralascia e metti in coda il manuale e l'academy"):

- **M5.S2-pre Manuale Operativo**: scrittura degli 11 capitoli residui per il
  corpus RAG di HAL Knowledge (Immobili, Clienti, Match, Publishing, Portali,
  Sito web, Virtual Staging, HAL Legal, Fascicolo, Valuator, Impostazioni).
- **M6 Academy**: piattaforma corsi B2B/B2C.

Entrambi da riprendere quando OMNIA è testabile end-to-end.

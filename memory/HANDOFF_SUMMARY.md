# 🎯 OMNIA — HANDOFF SUMMARY (per prossimo agente)

**Ultimo aggiornamento**: 03 Luglio 2026
**Founder**: Marco Nicastro (`mcnicastro@gmail.com`)
**Lingua di comunicazione con il Founder**: 🇮🇹 **ITALIANO** (obbligatorio)
**Repo pubblico OMNIA**: https://github.com/mcnicastro/OMNIA

---

## 📌 REGOLE VINCOLANTI (da rispettare SEMPRE)

### D-035 (29-Giu-2026) — STOP PRE-LAUNCH
Il Founder ha esplicitamente vietato ogni attività di pre-launch commerciale finché:
1. Tutte le feature del Santo Graal non sono complete e funzionanti
2. Omnia Academy (M6) non è strutturata e operativa

**In pratica**:
- ❌ **NON proporre** azioni su: landing `/it/agenzie`, banner CTA cross-funnel, outreach Founders 50, Sora 2 videos, warm-up Resend, refinement copy commerciale
- ✅ **SEGUIRE** rigorosamente il `PROGRAMMA_OMNIA.md` sequenziale
- ✅ La sequenza vincolata è (D-032): **M5.S4 → M5.S5 → M5.S6 → M5.S2 → M6 → M4**

### D-032 — Sequenza M5 prima di M4
M5 (AI Suite) va completato prima di M4 (Stripe + MLS + Crediti). M4 è comunque bloccato in attesa della costituzione della nuova SRL del Founder.

### D-033 — Architettura Virtual Staging "premium 3-stage"
Pipeline SAM 2 → Flux inpainting → Real-ESRGAN. Provider unico: fal.ai. Costo target: ~€0.056/render.

---

## 🌟 IL SANTO GRAAL DEL PROGETTO

**File di riferimento visuale** (unica north-star di prodotto):
🔗 https://customer-assets.emergentagent.com/job_audit-tool-12/artifacts/aru1brrm_ChatGPT%20Image%2015%20apr%202026%2C%2018_03_21.png

**Cosa mostra**: schema originale dell'ecosistema OMNIA tripilastro definito dal Founder il 15 Aprile 2026.

**Tre pilastri**:
1. 🌐 **ImmobilCloud** (B2C portale) → cattura privati + genera lead
2. 🏢 **ImmoWeb** (B2B CRM) → motore centrale dell'agente
3. 🎓 **Omnia Academy** (LMS) → formazione + reperimento collaboratori

**Killer features evidenziate**:
- Paperless completo (firma digitale + visure)
- AI chatbot 24/7 (lato privato + lato agente)
- Toolkit tutto-in-uno: Valutatore · Virtual Staging · Comparatore mutui · APE
- Sistema a crediti pay-per-use
- Matching intelligente immobili/richieste (base MLS network)
- Siti agenzia con identità propria (sottodominio o dominio agenzia)

**PDF originale progetto**:
🔗 https://customer-assets.emergentagent.com/job_audit-tool-12/artifacts/tmhfg909_progetto%20Omnia.pdf

---

## 📷 SCREENSHOT DI RIFERIMENTO MLS (Agesta.NET + nicastroimmobiliare.it)

Il Founder ha fornito questi materiali come **benchmark UI/UX** per il modulo MLS (M4.S1+S2 futuro).

### 1. Dashboard Agesta.NET — AREA RISERVATA AGENZIA ⭐⭐⭐
🔗 https://customer-assets.emergentagent.com/job_audit-tool-12/artifacts/14ss24l9_area%20riservata%20agenzia.jpg

**Backend gestionale con blocco MLS completo**:
- Banner "Collaborazioni con altre agenzie": 17 destinatari · 96 offerte · 1 invito
- Blocco "Agesta.NET MLS":
  - "Il mio MLS" (inventory agenzia)
  - "MLS Catania" (network locale): 75 annunci · 5.811 richieste
  - "MLS Italia" (network nazionale): 1.803 annunci · 198.963 richieste
- Contatori cross-agency: 136 offerte inviate · 19 richieste condivise
- Menu: Agenzie partner · MLS API · Registrazione · Gestione Agenti · Statistiche · Report

### 2. Home nicastroimmobiliare.it — BOX MLS PUBBLICO ⭐⭐⭐
🔗 (screenshot fornito dal Founder il 03-Lug-2026, memorizzato in `/app/memory/MLS_RESEARCH.md`)

**Vetrina promozionale sul frontend pubblico**:
- Header verde con claim killer **"130.000 immobili condivisi"**
- 4 dropdown compatti (Contratto/Categoria/Provincia/Comune) + Prezzo min-max
- CTA "avvia la ricerca" + Badge footer "POWERED BY AGESTANET"
- Coesiste con box "Cerca il tuo immobile" (inventory solo agenzia, verde grande a destra)

**Insight strategico**:
Il pattern MLS ha DUE facce complementari:
- **Backend** = strumento operativo con contatori/offerte/richieste
- **Frontend pubblico** = vetrina che sfrutta volume network come selling point + canalizza il lead sul dominio agenzia

### 3. Screenshot secondari Agesta.NET (portali)
- Portali attivi: https://customer-assets.emergentagent.com/job_audit-tool-12/artifacts/ep3t3nfk_portali%201.jpg
- Portali inattivi: https://customer-assets.emergentagent.com/job_audit-tool-12/artifacts/jusfbywg_portali%202.jpg

---

## ✅ STATO ATTUALE DEL PROGETTO (03-Lug-2026)

### Milestone completate al 100%

| Milestone | Descrizione | Status |
|---|---|---|
| **M1** | Foundation (Auth JWT httpOnly, i18n IT/EN/ES, Resend, DNS Cloudflare, 3 sottodomini) | ✅ DONE |
| **M2** | ImmoWeb CRM B2B (7/7 sprint: properties + clients + matching + AI lead scoring + multiposting OSF + brand studio + custom domain) | ✅ DONE |
| **M3** | ImmobilCloud B2C (7/7 sprint: home + mappa Leaflet + valutatore GIS Pro + saved searches + alert email + moderazione + Sell/Publish + ANNCSU autocomplete) | ✅ DONE |
| **M5.S1** | AL Agents chatbot CRM (Gemini 3 Flash, tool-use JSON, streaming SSE) | ✅ DONE |
| **M5.S3** | AL Legal (5 sub-agenti + Tavily 7 fonti IT + anti-hallucination + upload PDF) | ✅ DONE |
| **M3.S6-pro** | Valutatore Pro UNI 10750 (107 province + 20.000+ comuni via Nominatim) | ✅ DONE |
| **M5.S4.1** | Virtual Staging pipeline 3-stage (SAM2 + Flux + ESRGAN) — costo reale €0.056/render, tempo 19s | ✅ DONE (03-Lug-2026) |

### Milestone da completare

| Milestone | Descrizione | Blocker |
|---|---|---|
| M5.S4.2 | Reverse Staging + 4 varianti parallele + prompt CRM-aware + **sub-task inline "Arreda questa foto"** nel form immobili | Nessuno (FAL_KEY attiva) |
| M5.S4.3 | Micro-tour video 5s (Kling) + embed listing B2C + export Reels 9:16 | FAL_KEY (già disponibile) |
| M5.S4.4 | A/B testing portale + dashboard analytics | Nessuno |
| M5.S5 | Comparatore Mutui (scraping tassi Intesa/Unicredit/BPER/CA + form + lead partner) | Nessuno |
| M5.S6 | APE calcolo orientativo (form + classe energetica + PDF) | Nessuno |
| M5.S2 | AL Knowledge (RAG chatbot manuale piattaforma) | 🟡 Manuale OMNIA da scrivere (6-10h) |
| M6 | Omnia Academy (5 sprint: LMS + quiz + tutor AL + marketplace + FIAIP) | Nessuno |
| M4.S1+S2 | MLS Network multi-agenzia (workflow 5gg + audit log + widget frontend "130k immobili") | Nessuno tecnico, ma post-M6 (D-032) |
| M4.S3+S4+S5 | Stripe + Crediti + Boost visibilità | 🔴 Nuova SRL Founder |
| M5.S7 | Modulistica AI | 🔴 post-SRL |
| M5.S8 | Firma elettronica + Visure (con `zornade/visura-api`) | 🔴 post-SRL |

---

## 🗂️ MAPPA FILE PIÙ IMPORTANTI DEL REPO

### 📁 Repo pubblico
🔗 **https://github.com/mcnicastro/OMNIA**

Il codice locale in `/app` è sincronizzato con questo repo (il Founder pusha via "Save to Github" della piattaforma Emergent).

### Backend (`/app/backend/`)

#### Core
- `/app/backend/server.py` — Entry point FastAPI + inclusione router
- `/app/backend/.env` — Credenziali (FAL_KEY, RESEND_API_KEY, TAVILY_API_KEY, EMERGENT_LLM_KEY, MONGO_URL, JWT_SECRET, ecc.)
- `/app/backend/requirements.txt` — Dependencies Python
- `/app/backend/shared/db/connection.py` — MongoDB Motor async client
- `/app/backend/shared/auth/dependencies.py` — `get_current_user` cookie-based auth
- `/app/backend/shared/email/` — Resend service + template HTML

#### ImmoWeb B2B CRM (M2)
- `/app/backend/apps/immoweb/routes.py` — Mount router principale `/api/app/*`
- `/app/backend/apps/immoweb/properties.py` — CRUD immobili + 16 tipologie
- `/app/backend/apps/immoweb/clients.py` — CRUD clienti 5 tipologie
- `/app/backend/apps/immoweb/matching.py` — Deterministic + AI scoring
- `/app/backend/apps/immoweb/lead_scoring.py` — Gemini 3 Flash lead scoring 4 livelli
- `/app/backend/apps/immoweb/portals.py` — Multiposting OSF 7 portali
- `/app/backend/apps/immoweb/themes.py` — Theme Registry headless (4 temi)
- `/app/backend/apps/immoweb/brand_extractor.py` — Gemini estrae brand da URL
- `/app/backend/apps/immoweb/site.py` — Site server SEO-clean `/api/p/{slug}/`
- `/app/backend/apps/immoweb/custom_domain.py` — CNAME + host-based routing
- `/app/backend/apps/immoweb/clients_ai_import.py` — Smart Import Excel/vCard/CSV/text
- `/app/backend/apps/immoweb/al_agent.py` — AL Agents chatbot (M5.S1)
- `/app/backend/apps/immoweb/al_legal/router.py` — AL Legal 5 sub-agenti (M5.S3)
- `/app/backend/apps/immoweb/al_legal/tavily.py` — Tavily search 7 fonti IT
- `/app/backend/apps/immoweb/al_legal/validator.py` — Anti-hallucination confidence 0.85
- `/app/backend/apps/immoweb/virtual_staging.py` — **⭐ NEW 03-Lug: pipeline 3-stage fal.ai**

#### ImmobilCloud B2C portale (M3)
- `/app/backend/apps/immocloud/routes.py` — Mount `/api/cloud/*`
- `/app/backend/apps/immocloud/search.py` — Ricerca portale + filtri
- `/app/backend/apps/immocloud/valuator.py` — Valutatore GIS Pro UNI 10750
- `/app/backend/apps/immocloud/anncsu.py` — ANNCSU autocomplete indirizzi (ArcGIS ISTAT + Nominatim fallback)
- `/app/backend/apps/immocloud/geocoding.py` — Nominatim wrapper
- `/app/backend/apps/immocloud/saved_searches.py` — Salvate + alert email

#### Marketing (in stato DORMIENTE per D-035, non toccare)
- `/app/backend/apps/marketing/founders.py` — `/api/founders/register` + `/spots`
- `/app/backend/shared/email/templates/founders_welcome.it.html`

### Frontend (`/app/frontend/`)

#### Core
- `/app/frontend/src/App.js` — Router principale (tutte le route)
- `/app/frontend/.env` — `REACT_APP_BACKEND_URL`
- `/app/frontend/src/shared/lib/api.js` — Axios client con cookie
- `/app/frontend/src/shared/i18n/locales/{it,en,es}.json` — Traduzioni
- `/app/frontend/src/shared/components/AgencyShell.jsx` — Layout CRM (nav sinistra)

#### ImmoWeb pages
- `/app/frontend/src/apps/immoweb/DashboardPage.jsx`
- `/app/frontend/src/apps/immoweb/ClientsPage.jsx` (+ ClientFormPage + ClientImportPage)
- `/app/frontend/src/apps/immoweb/MatchesPage.jsx` (+ MatchLeadScorePage)
- `/app/frontend/src/apps/immoweb/PortalsPage.jsx`
- `/app/frontend/src/apps/immoweb/WebsitePage.jsx` — Brand Studio
- `/app/frontend/src/apps/immoweb/ModerationPage.jsx`
- `/app/frontend/src/apps/immoweb/pages/VirtualStagingPage.jsx` — **⭐ NEW 03-Lug**
- `/app/frontend/src/apps/immoweb/components/AgencyShell.jsx` — Nav CRM

#### ImmobilCloud pages
- `/app/frontend/src/apps/immocloud/ImmocloudApp.jsx`
- `/app/frontend/src/apps/immocloud/components/ValuatorPage.jsx`
- `/app/frontend/src/apps/immocloud/components/AddressAutocomplete.jsx` — ANNCSU
- `/app/frontend/src/apps/immocloud/components/SearchPage.jsx`
- `/app/frontend/src/apps/immocloud/components/PropertyDetailPage.jsx`

#### Legal (M5.S3)
- `/app/frontend/src/apps/legal/LegalApp.jsx`

#### Landing (stato dormiente per D-035)
- `/app/frontend/src/apps/landing/AgenziesLandingPage.jsx`

### Documenti strategici (`/app/memory/`) — LEGGERE PER PRIMA COSA

| File | Priorità | Contenuto |
|---|---|---|
| `HANDOFF_SUMMARY.md` | ⭐⭐⭐ | Questo file |
| `PROGRAMMA_OMNIA.md` | ⭐⭐⭐ | Programma operativo completo v2.4 |
| `DECISIONS.md` | ⭐⭐⭐ | Tutte le decisioni D-001 → D-035 |
| `ROADMAP.md` | ⭐⭐ | Backlog ordinato per fase |
| `PRD.md` | ⭐⭐ | Product requirements + storico implementazioni |
| `CHANGELOG.md` | ⭐⭐ | Cronologia dettagliata modifiche |
| `MLS_RESEARCH.md` | ⭐⭐⭐ | Analisi Agesta.NET + nicastroimmobiliare + mappatura OMNIA (nuovo 03-Lug) |
| `OPEN_SOURCE_FINDINGS.md` | ⭐⭐ | Repo GitHub utili (zornade/visura-api, PArSe, dati_catastali, ecc.) |
| `PRICING_OMNIA.md` | ⭐ | Pricing v1.0 (Founders 50 €39/€99/€249) — congelato per D-035 |
| `BUSINESS_MODEL.md` | ⭐ | Stream revenue + margini |
| `RESEND_DOMAIN_GUIDE.md` | ⭐ | Config Resend + Cloudflare |
| `NEXT_SESSION_TIPS.md` | ⭐ | Tips operativi vari |
| `test_credentials.md` | ⭐⭐ | Admin: `mcnicastro@gmail.com` / `***ROTATED — vedi memory/test_credentials.env***` |

---

## 🔑 CREDENZIALI E CONFIG

- **Super Admin**: `mcnicastro@gmail.com` / `***ROTATED — vedi memory/test_credentials.env***`
- **Dominio email**: `omniarealestateecosystem.it` (Resend + Cloudflare DNS)
- **Sottodomini configurati**: `app.` (CRM), `nuvola.` (B2C), `imparare.` (Academy)
- **API keys attive** (in `/app/backend/.env`):
  - `EMERGENT_LLM_KEY` — Gemini/Claude/OpenAI universal + Sora 2
  - `RESEND_API_KEY` — email transactional
  - `TAVILY_API_KEY` — AL Legal search
  - `FAL_KEY` — Virtual Staging (attivata 03-Lug con top-up Founder)
  - `MONGO_URL` — MongoDB locale pod
  - `JWT_SECRET`, `OMNIA_PORTAL_ENC_KEY`

---

## 🛠️ COMANDI OPERATIVI PRINCIPALI

### Restart servizi
```bash
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
```

### Logs
```bash
tail -n 50 /var/log/supervisor/backend.err.log
tail -n 50 /var/log/supervisor/frontend.err.log
```

### Test API (con cookie auth)
```bash
API=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d'=' -f2)
COOKIE=/tmp/omnia.txt
curl -s -X POST "$API/api/auth/login" -c $COOKIE -H "Content-Type: application/json" \
  -d '{"email":"mcnicastro@gmail.com","password":"***ROTATED — vedi memory/test_credentials.env***"}' > /dev/null
curl -s "$API/api/app/staging/history" -b $COOKIE | python3 -m json.tool
```

### URL preview (dinamico)
```bash
grep REACT_APP_BACKEND_URL /app/frontend/.env
```

---

## 🎯 COSA FARE ALLA PROSSIMA SESSIONE

### 1. Al primo scambio con il Founder
- Saluta in **italiano**
- Chiedi conferma prima di iniziare qualsiasi task, usando `ask_human`
- Non deviare mai dalla sequenza D-032/D-035

### 2. Prossimo step naturale (sequenza D-032)
**M5.S4.2 Virtual Staging Sprint 2** con questi obiettivi:
- Reverse Staging (rimuovi arredo esistente + ri-arreda con stile diverso)
- 4 varianti parallele in una singola generation
- Prompt CRM-aware (legge zona/prezzo/buyer persona da CRM per prompt ottimale)
- **Sub-task**: inline "Arreda questa foto" — bottone accanto a ogni foto nel form immobili → apre modale Virtual Staging pre-caricato con URL foto listing → salva risultato come nuova foto dell'annuncio

### 3. Poi in ordine
M5.S4.3 → M5.S4.4 → M5.S5 Mutui → M5.S6 APE → M5.S2 Knowledge (dopo manuale) → **M6 Academy** → M4.S1+S2 MLS (usando reference Agesta.NET + nicastroimmobiliare) → M4.S3+S4+S5 Stripe (post-SRL) → M5.S7+S8

### 4. Attenzioni particolari
- **NON** proporre pre-launch o attività commerciali (D-035)
- **NON** modificare `.env`, `requirements.txt`, `package.json` senza il metodo corretto (pip install + freeze, yarn add)
- **NON** riscrivere file esistenti — usa search_replace
- **PARLA SEMPRE IN ITALIANO** con il Founder
- Rispetta i **data-testid** su ogni elemento interattivo
- Ogni auth-related bug → chiama `integration_playbook_expert_v2` prima di scrivere codice

---

## 📊 STACK TECNICO

| Layer | Tech |
|---|---|
| Backend | FastAPI (Python 3.11) + Motor MongoDB async |
| Frontend | React 18 + React Router + Tailwind + Shadcn UI |
| Database | MongoDB (locale pod) |
| Auth | JWT httpOnly cookie custom |
| Email | Resend (dominio verificato) |
| AI | Gemini 3 Flash (Emergent LLM Key) + Sora 2 |
| Video Gen | fal.ai (Kling in M5.S4.3) |
| Image Gen | fal.ai (SAM 2 + Flux + Real-ESRGAN) |
| Search | Tavily (AL Legal) |
| DNS | Cloudflare Free (`omniarealestateecosystem.it`) |
| Maps | Leaflet + OpenStreetMap + Nominatim + ANNCSU ArcGIS |
| Deployment | Emergent platform (Kubernetes container) |

---

## 🚨 BLOCKERS ESTERNI (dipendono dal Founder)

| Blocker | Sblocca | Quando serve |
|---|---|---|
| ✅ FAL_KEY | M5.S4 Virtual Staging | ATTIVATO 03-Lug-2026 |
| Manuale OMNIA scritto | M5.S2 AL Knowledge | Da scrivere (6-10h del Founder + E1 assist) |
| Nuova SRL costituita | M4.S3+S4+S5 Stripe + M5.S7/S8 | Data ignota, notaio + IBAN pending |
| Revisione avvocato T&C (~€200) | Commercializzazione AL Legal | Pending |
| Account SISTER (Agenzia Entrate) | M5.S8 visure via `zornade/visura-api` | Post-SRL |
| Accreditamento FIAIP/FIMAA | M6.S5 crediti formativi | Post-M6 base |

---

## 📞 QUANDO CHIEDERE AL FOUNDER

Alla prima interazione, chiedi tramite `ask_human`:
1. Conferma di riprendere dalla sequenza D-032 con M5.S4.2 (o alternativa)
2. Se serve `FAL_KEY` — verificare saldo attivo (03-Lug-2026 top-up eseguito)
3. Qualsiasi requisito specifico di comportamento

**Frase magica**: se il Founder dice "dove siamo" → mostra il quadro sintetico stato progetto (vedi PROGRAMMA_OMNIA.md Parte V).

---

**Fine handoff summary. Buon lavoro, agente successivo. 🚀**

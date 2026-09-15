# OMNIA — Real Estate Ecosystem

Piattaforma full-stack per il mercato immobiliare italiano: CRM B2B (**ImmoWeb**), portale B2C (**ImmobilCloud**), AI suite (**HAL**), API Gateway a crediti, billing Stripe. Academy esclusa dal perimetro corrente.

> **Direzione lavori**: Cursor (sostituisce Emergent.sh). Deploy FE: **Vercel**. Scala target: **≥ 10.000 agenzie**.

## Stack
- **Backend**: FastAPI + MongoDB (motor), JWT httpOnly cookies, multi-tenant `agency_id`
- **Frontend**: React (CRA + craco), Tailwind, i18n IT/EN/ES
- **LLM**: Gemini via adapter (M1) — bridge temporaneo al posto di Emergent
- **Deploy**: Frontend su Vercel; API ASGI + Mongo Atlas

## Setup locale (Cursor)
1. MongoDB in ascolto su `127.0.0.1:27017`
2. `cp backend/.env.example backend/.env` e `cp frontend/.env.example frontend/.env` — valorizza `JWT_SECRET`
3. **Stack stabile (consigliato)** — API + preview same-origin, auto-restart:
   ```bash
   bash scripts/omnia-stack.sh ensure   # oppure: watch
   ```
4. Apri l’area riservata tramite **Cursor → Ports → `omnia-preview` (43123)**  
   Non usare localtunnel / Cloudflare quick tunnel (sono la causa dei Bad Gateway).
5. Alternativa manuale:
   ```bash
   cd backend && python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn server:app --host 0.0.0.0 --port 43121
   # altro terminale:
   cd frontend && REACT_APP_BACKEND_URL= yarn build && node preview-server.js
   ```
6. Test: `cd backend && python -m pytest tests/ -q`

Credenziali di test: `memory/test_credentials.env` (gitignored).

## Modulistica + firma (M5.S7 / M5.S8 · D-082)
- CRM: `/it/app/modulistica` — template italiani, PDF white-label (branding agenzia), archivio documenti
- Firma: `ESIGN_PROVIDER=mock|yousign|docusign` (default mock; niente QES proprietaria — D-042)
- API Track B: `GET /api/v1/modulistica/templates`, `POST /api/v1/modulistica/render` (2 crediti)

## Porte di sviluppo
- **Preview area riservata (stabile)**: `http://127.0.0.1:43123` ← usa questa
- API diretta: `http://127.0.0.1:43121`
- Health: `http://127.0.0.1:43123/healthz`
- Health stack: `bash scripts/omnia-stack.sh status`
- Dopo modifiche FE: `bash scripts/omnia-stack.sh rebuild`

> **Bad Gateway**: quasi sempre tunnel esterni (localtunnel / trycloudflare). Lo stack ufficiale non li usa. In Cursor: pannello **Ports → omnia-preview**.

## Roadmap operativa (vincolante)
`M0 travaso → M1 LLM/storage → M2 MLS → M3 Manuale+HAL codice → M4 Vercel/harden`  
Dettaglio decisioni: `memory/DECISIONS.md` (D-071…D-074).

## Regole chiave
- Route backend prefissate `/api`
- Nessun segreto hardcoded
- Ruoli privilegiati solo via onboarding/invito
- Load test ladder: 10 → 50 → 500 → 1.000 → 5.000 → 10.000 agenzie

© OMNIA — Founder mcnicastro-netizen

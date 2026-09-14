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
3. Backend:
   ```bash
   cd backend && python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt   # emergentintegrations escluso (stub locale)
   uvicorn server:app --host 0.0.0.0 --port 43121
   ```
4. Frontend:
   ```bash
   cd frontend && yarn && PORT=43122 HOST=0.0.0.0 yarn start
   ```
5. Test: `cd backend && python -m pytest tests/ -q`

Credenziali di test: `memory/test_credentials.env` (gitignored).

## Porte di sviluppo (sessione corrente)
- API: `http://127.0.0.1:43121`
- FE: `http://127.0.0.1:43122`

## Roadmap operativa (vincolante)
`M0 travaso → M1 LLM/storage → M2 MLS → M3 Manuale+HAL codice → M4 Vercel/harden`  
Dettaglio decisioni: `memory/DECISIONS.md` (D-071…D-074).

## Regole chiave
- Route backend prefissate `/api`
- Nessun segreto hardcoded
- Ruoli privilegiati solo via onboarding/invito
- Load test ladder: 10 → 50 → 500 → 1.000 → 5.000 → 10.000 agenzie

© OMNIA — Founder mcnicastro-netizen

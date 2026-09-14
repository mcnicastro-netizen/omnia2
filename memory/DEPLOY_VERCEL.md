# Deploy OMNIA — Vercel (frontend) + API ASGI

## Frontend (Vercel)
1. Crea progetto Vercel con **Root Directory** = `frontend`
2. Build: `yarn build` · Output: `build`
3. Env Vercel:
   - `REACT_APP_BACKEND_URL=https://TUO_API_PUBBLICO` (URL dell'API in produzione)
4. `vercel.json` già presente (SPA rewrite).

## Backend (API)
Vercel hosta bene lo **static FE**. L'API FastAPI (SSE HAL, job lunghi, Mongo) va su un host ASGI
(es. Railway/Render/Fly/VPS) con:
- `MONGO_URL` → Mongo Atlas (obbligatorio a scala)
- `JWT_SECRET`, `GEMINI_API_KEY`, `CORS_ORIGINS` = dominio Vercel
- `STORAGE_BACKEND=local` solo dev; in prod S3/R2
- `COOKIE_SECURE=true` in HTTPS

## Scala ≥ 10.000 agenzie
```bash
cd backend && source .venv/bin/activate
python scripts/load_ladder_mls.py --tier 50
python scripts/load_ladder_mls.py --tier 500
# … fino a 1000 / batch superiori
```
Indici MLS e `agency_id` devono restare sempre nelle query list.

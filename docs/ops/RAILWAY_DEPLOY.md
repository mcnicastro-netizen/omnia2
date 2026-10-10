# Deploy API OMNIA su Railway (Plan B — Hetzner bloccato)

**Stato:** ✅ prep repo · ⏳ deploy in attesa Founder  
**Dominio target:** `https://api.omniarealestateecosystem.it` → servizio Railway  
**FE:** Vercel (dopo API live) · runbook: [`VERCEL_DEPLOY.md`](./VERCEL_DEPLOY.md)

---

## Cosa fai tu ora (UI Railway — 5 minuti)

Sei già loggato con GitHub. Poi:

### A. Token per l’agent (obbligatorio E2E)
1. https://railway.app/account/tokens → **Create Token** (scope **Account**)
2. Incolla in Cursor Secrets (env omnia2, scope **Environment**) come `RAILWAY_TOKEN`  
   (`scripts/railway-deploy.sh` lo rimappa a `RAILWAY_API_TOKEN` per la CLI: se lasci un Account token anche in `RAILWAY_TOKEN` process env, la CLI lo tratta come *project* token → Unauthorized.)
3. Nuovo agent + messaggio **«vai Railway»**

### B. Oppure crea il progetto a mano (se preferisci UI)
1. **New Project** → **Deploy from GitHub repo** → `mcnicastro-netizen/omnia2`
2. **Add Plugin / Database** → **MongoDB**
3. Nel service API (non Mongo):
   - Root Directory = repo root (usa `railway.toml` + `Dockerfile.railway`)
4. **Variables** (service API) — copia da vault / `.env` (valori, non in chat):

| Variabile | Note |
|-----------|------|
| `MONGO_URL` | Reference Railway: `${{ MongoDB.MONGO_URL }}` (o nome plugin) |
| `DB_NAME` | `omnia` |
| `JWT_SECRET` | nuovo lungo (`openssl rand -hex 32`) |
| `COOKIE_SECURE` | `true` |
| `CORS_ORIGINS` | `https://www.omniarealestateecosystem.it,https://app.omniarealestateecosystem.it,https://cloud.omniarealestateecosystem.it` (+ URL Vercel preview se serve) |
| `FRONTEND_URL` / `FRONTEND_BASE_URL` / `OMNIA_PUBLIC_URL` | `https://www.omniarealestateecosystem.it` (o URL Vercel finché DNS non è pronto) |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | seed Founder (stessi del vault) |
| `DEMO_ADMIN_PASSWORD` | seed demo |
| `GEMINI_API_KEY` | vault |
| `RESEND_API_KEY` | vault |
| `SENDER_EMAIL` | `OMNIA <info@omniarealestateecosystem.it>` |
| `STRIPE_*` / `OMNIA_SELF_SERVE_ENABLED` | come sandbox Cloud |
| `STORAGE_BACKEND` | `local` (poi volume) |
| `PUBLIC_BASE_URL` | URL pubblico API (dopo generate domain) |

5. **Settings → Networking → Generate Domain** → ottieni `https://….up.railway.app`
6. Imposta `PUBLIC_BASE_URL` = quell’URL (senza `/api`)
7. Smoke: `curl -sS https://….up.railway.app/api/health`
8. In Cursor vault: `OMNIA_API_PUBLIC_URL=https://….up.railway.app`  
   (poi, con CNAME Cloudflare `api` → Railway, diventa `https://api.omniarealestateecosystem.it`)

### C. Volume (media + backup)
Railway → service API → **Volumes**:
- mount `/app/.media` (foto)
- mount `/app/.backups` (hot backup)  
Opzionale: volume off-box path via `OFFBOX_BACKUP_ROOT`

---

## Flusso agent (dopo `RAILWAY_TOKEN`)

```bash
bash scripts/railway-prep-check.sh
bash scripts/railway-deploy.sh   # richiede RAILWAY_TOKEN
```

Poi DNS: `memory/DNS_SETUP_GUIDE.md` §4b (`api` → Railway).

---

## Costi indicativi
Hobby **$5/mese** + usage → tipico API+Mongo piccolo **≈ $15–35/mese**.

---

## Checklist Founder
- [x] Account Railway (GitHub)
- [ ] `RAILWAY_TOKEN` in vault omnia2
- [ ] Progetto + Mongo + variables
- [ ] Domain Railway + health OK
- [ ] `OMNIA_API_PUBLIC_URL` in vault
- [ ] Cloudflare CNAME `api`
- [ ] Poi **«vai Vercel»**

# Deploy API OMNIA su Railway (Plan B — Hetzner bloccato)

**Stato:** ✅ prep repo · ⏳ deploy in attesa Founder  
**Dominio target:** `https://api.omniarealestateecosystem.it` → servizio Railway  
**FE:** Vercel (dopo API live) · runbook: [`VERCEL_DEPLOY.md`](./VERCEL_DEPLOY.md)

---

## Cosa fai tu ora (UI Railway — 5 minuti)

Sei già loggato con GitHub. Poi:

### A. Token per l’agent (obbligatorio E2E)
1. https://railway.com/account/tokens → **Create Token**
2. Workspace: **No workspace** (account token — non un token di workspace)
3. Incolla in Cursor Secrets (env omnia2) come `RAILWAY_API_TOKEN`  
   Link env: https://cursor.com/dashboard/cloud-agents/environments/e/b80b635c-b592-11f1-bb68-864e54d14197
4. Nuovo agent + messaggio **«vai Railway»**

> Nome vault = `RAILWAY_API_TOKEN` (quello che legge la CLI 5 per creare progetti).  
> `RAILWAY_TOKEN` è il project token e **non** basta per `railway init`.

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

## Flusso agent (dopo `RAILWAY_API_TOKEN`)

Vault obbligatorio: **`RAILWAY_API_TOKEN`** = account token (Railway → Account → Tokens → workspace **No workspace**).  
La CLI 5 usa `RAILWAY_API_TOKEN` per create/link; `RAILWAY_TOKEN` è solo project-scoped.  
Un valore sbagliato (workspace token, project id, secret vuoto) viene rifiutato (`me` Not Authorized).

```bash
bash scripts/railway-prep-check.sh
bash scripts/railway-deploy.sh   # richiede RAILWAY_API_TOKEN
```

Lo script: classifica il token → `railway init` → MongoDB → variabili (senza stamparle) → volumi `/app/.media` e `/app/.backups` → `railway up` → dominio → smoke `/api/health`.

Poi DNS: `memory/DNS_SETUP_GUIDE.md` §4b (`api` → Railway).

---

## Costi indicativi
Hobby **$5/mese** + usage → tipico API+Mongo piccolo **≈ $15–35/mese**.

---

## Checklist Founder
- [x] Account Railway (GitHub)
- [ ] `RAILWAY_API_TOKEN` in vault omnia2 = **account token** (No workspace). 10-Ott-2026: in pod c’era solo `RAILWAY_TOKEN` (rifiutato); `RAILWAY_API_TOKEN` **unset**.
- [ ] Progetto + Mongo + variables
- [ ] Domain Railway + health OK
- [ ] `OMNIA_API_PUBLIC_URL` in vault
- [ ] Cloudflare CNAME `api`
- [ ] Poi **«vai Vercel»**

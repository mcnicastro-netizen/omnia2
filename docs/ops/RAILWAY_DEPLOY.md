# Deploy API OMNIA su Railway (Plan B — Hetzner bloccato)

**Stato:** ✅ prep repo · ⛔ go-live bloccato (trial scaduto + token CLI) · ⏳ ripresa dopo Founder  
**Dominio target:** `https://api.omniarealestateecosystem.it` → servizio Railway  
**FE:** Vercel (dopo API live) · runbook: [`VERCEL_DEPLOY.md`](./VERCEL_DEPLOY.md)

---

## Blocco attuale (2026-10-10 · «vai Railway»)

Probe agent (`scripts/railway-golive-probe.sh`):

1. **Trial scaduto** — GraphQL: `Your trial has expired. Please select a plan`. Progetti legacy Immocloud ancora `subscriptionType: trial`.
2. **Token vault sbagliato per CLI** — `RAILWAY_TOKEN` presente ma CLI: `Unauthorized` / `Invalid RAILWAY_TOKEN`. Per bootstrap serve **Account Token** in `RAILWAY_API_TOKEN` (non Project Token in `RAILWAY_TOKEN`).

### Cosa fai tu (5 minuti)

1. https://railway.app → **Upgrade / Billing** → piano **Hobby** (o superiore)
2. https://railway.app/account/tokens → **Create Token** (Account / Workspace)
3. Vault env omnia2:  
   - aggiungi `RAILWAY_API_TOKEN` = token account  
   - **rimuovi o svuota** `RAILWAY_TOKEN` finché non hai un Project Token post-progetto  
   Link: https://cursor.com/dashboard/cloud-agents/environments/e/b80b635c-b592-11f1-bb68-864e54d14197
4. Nuovo agent → **«vai Railway»**

Token types (Railway CLI):

| Env | Scope | Uso |
|-----|--------|-----|
| `RAILWAY_API_TOKEN` | Account / workspace | `init`, link, add Mongo, variables, bootstrap |
| `RAILWAY_TOKEN` | Project + environment | solo `railway up` / logs su progetto già creato |

Non settare entrambi durante il bootstrap (il project token vince e spegne l’account token).

---

## Flusso agent (dopo piano + `RAILWAY_API_TOKEN`)

```bash
bash scripts/railway-golive-probe.sh   # ESITO=READY
bash scripts/railway-deploy.sh
```

Poi DNS: `memory/DNS_SETUP_GUIDE.md` §4b (`api` → Railway).

---

## Variables servizio API

| Variabile | Note |
|-----------|------|
| `MONGO_URL` | Reference plugin: `${{MongoDB.MONGO_URL}}` (nome può variare) |
| `DB_NAME` | `omnia` |
| `JWT_SECRET` | vault |
| `COOKIE_SECURE` | `true` |
| `CORS_ORIGINS` | domini FE prod (+ preview Vercel se serve) |
| `FRONTEND_URL` / `FRONTEND_BASE_URL` / `OMNIA_PUBLIC_URL` | FE pubblico |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | seed Founder |
| `DEMO_ADMIN_PASSWORD` | seed demo |
| `GEMINI_API_KEY` / `RESEND_API_KEY` | vault |
| `SENDER_EMAIL` | `OMNIA <info@omniarealestateecosystem.it>` |
| `STRIPE_*` / `OMNIA_SELF_SERVE_ENABLED` | come sandbox Cloud |
| `STORAGE_BACKEND` | `local` (+ volume) |
| `PUBLIC_BASE_URL` | URL API pubblico (dopo Generate Domain) |

Volumes: `/app/.media`, `/app/.backups`.

Smoke: `curl -sS https://….up.railway.app/api/health`  
Vault: `OMNIA_API_PUBLIC_URL=https://….up.railway.app`

---

## Costi indicativi
Hobby **$5/mese** + usage → tipico API+Mongo piccolo **≈ $15–35/mese**.

---

## Checklist Founder
- [x] Account Railway (GitHub)
- [x] Prep repo (D-123 · `Dockerfile.railway` / `railway.toml`)
- [ ] **Upgrade piano** (trial scaduto)
- [ ] `RAILWAY_API_TOKEN` (Account) in vault — non Project Token in `RAILWAY_TOKEN`
- [ ] Progetto `omnia-api` + Mongo + variables
- [ ] Domain Railway + health OK
- [ ] `OMNIA_API_PUBLIC_URL` in vault
- [ ] Cloudflare CNAME `api`
- [ ] Poi **«vai Vercel»**

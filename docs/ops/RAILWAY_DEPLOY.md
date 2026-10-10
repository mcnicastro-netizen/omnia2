# Deploy API OMNIA su Railway (Plan B — Hetzner bloccato)

**Stato:** ✅ prep repo · ✅ API live (10-Ott-2026) · ⏳ vault Environment + DNS `api` + Vercel  
**API live (temporanea):** `https://omnia-api-production-2cec.up.railway.app`  
**Dominio target:** `https://api.omniarealestateecosystem.it` → servizio Railway  
**Progetto Railway:** `omnia-api` · id `1b31e62e-7ba7-4082-b643-72d221ee7fbe`  
**FE:** Vercel (dopo vault + DNS) · runbook: [`VERCEL_DEPLOY.md`](./VERCEL_DEPLOY.md)

Smoke verificato: `GET /api/health` → `status=ok` · `db=ok`.

---

## Cosa fai tu (domani — vault Environment)

### A. Token + URL in vault omnia2 (scope **Environment**)
1. https://railway.app/account/tokens → **revoca** token esposti in chat → **Create Token** (scope **Account**)
2. Cursor → Environments → **omnia2** (`b80b635c-b592-11f1-bb68-864e54d14197`) → Secrets → scope **Environment** (non Personal):
   - `RAILWAY_TOKEN` = token Account nuovo
   - `RAILWAY_PROJECT_ID=1b31e62e-7ba7-4082-b643-72d221ee7fbe`
   - `OMNIA_API_PUBLIC_URL=https://omnia-api-production-2cec.up.railway.app`
3. **Nuovo agent** (le chat vecchie non rileggono il vault)

**CLI quirk:** il nome vault resta `RAILWAY_TOKEN`. `scripts/railway-deploy.sh` lo rimappa a `RAILWAY_API_TOKEN` e unsetta `RAILWAY_TOKEN` (altrimenti Unauthorized).

**UI Cursor:** in chat normale `add_secrets` spesso non mostra «Agent is blocked» / apre solo Personal — bug prodotto. Usare Secrets UI Environment.

### B. Progetto (già creato — riferimento)
1. Progetto `omnia-api` + servizio `omnia-api` + plugin **MongoDB**
2. Root = repo root · `Dockerfile.railway` (pin via GraphQL `dockerfilePath`)
3. Variables già impostate in deploy (MONGO_URL reference `${{MongoDB.MONGO_URL}}`, JWT, CORS, Stripe test, OpenAPI, …)
4. Domain: `omnia-api-production-2cec.up.railway.app` · `PUBLIC_BASE_URL` settata
5. Volumes: `/app/.media` · `/app/.backups`

### C. DNS (dopo vault)
Vedi `memory/DNS_SETUP_GUIDE.md` §4c — CNAME `api` → Railway. Poi aggiorna `OMNIA_API_PUBLIC_URL` a `https://api.omniarealestateecosystem.it`.

---

## Flusso agent (redeploy)

```bash
bash scripts/railway-prep-check.sh
bash scripts/railway-deploy.sh   # richiede RAILWAY_TOKEN in vault
```

---

## Costi indicativi
Hobby **$5/mese** + usage → tipico API+Mongo piccolo **≈ $15–35/mese**.

---

## Checklist Founder
- [x] Account Railway (GitHub)
- [x] Progetto + Mongo + variables + domain + health OK
- [ ] `RAILWAY_TOKEN` fresco in vault **Environment** omnia2 (revoca esposti)
- [ ] `RAILWAY_PROJECT_ID` + `OMNIA_API_PUBLIC_URL` in vault Environment
- [ ] Cloudflare CNAME `api`
- [ ] Poi **«vai Vercel»**

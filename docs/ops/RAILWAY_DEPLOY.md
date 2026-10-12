# Deploy API OMNIA su Railway (Plan B — Hetzner bloccato)

**Stato:** ✅ prep repo · ✅ API live · ✅ DNS `api.` + TLS (12-Ott-2026) · ✅ Stripe → `api.` · ⏳ vault `OMNIA_API_PUBLIC_URL` + Vercel  
**API live (temporanea):** `https://omnia-api-production-2cec.up.railway.app`  
**Dominio target:** `https://api.omniarealestateecosystem.it` → servizio Railway  
**Progetto Railway:** `omnia-api` · id `1b31e62e-7ba7-4082-b643-72d221ee7fbe`  
**FE:** Vercel (dopo vault + DNS) · runbook: [`VERCEL_DEPLOY.md`](./VERCEL_DEPLOY.md)

Smoke: `GET /api/health` → `status=ok` · `db=ok`.  
Stripe Test: destinazione `omnia-railway-api` → `/api/billing/webhook` · consegna `checkout.session.completed` **200 OK**.

---

## Stripe webhook (sandbox → Railway) — fatto 12-Ott-2026

| Voce | Valore |
|------|--------|
| Dashboard | Stripe **Test / Sandbox** |
| Destinazione | `OMNIA Railway API (sandbox)` · id `we_1UPksi5fTeVVWdDf21htElsf` |
| Descrizione | `OMNIA Railway API (sandbox)` — **non** usare `…auto-sync` (lo riscriverebbe `sync-stripe-webhook-url.py` sul tunnel) |
| URL | `https://omnia-api-production-2cec.up.railway.app/api/billing/webhook` |
| Secret | `whsec_…` → Variable Railway service `omnia-api` = `STRIPE_WEBHOOK_SECRET` |
| Verifica | Workbench Shell: `stripe trigger checkout.session.completed` → consegna **200 OK** |

Endpoint Emergent `…emergentagent.com/api/stripe/webhook` = **obsoleto** (mail Stripe 404); non ricreare.  
Cloud dogfood può avere un **secondo** endpoint trycloudflare con descrizione `OMNIA Cloud Agent portal (auto-sync)` — vault Cloud vs Variable Railway = `whsec` diversi.

---

## Cosa fai tu (vault Environment + DNS)

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
- [x] Stripe sandbox webhook → Railway (`omnia-railway-api` · 200 OK)
- [x] `RAILWAY_TOKEN` Account in vault **Environment** omnia2
- [x] `RAILWAY_PROJECT_ID` in vault Environment
- [x] Cloudflare CNAME `api` + TXT verify + cert VALID
- [ ] `OMNIA_API_PUBLIC_URL=https://api.omniarealestateecosystem.it` in vault Environment
- [ ] Poi **«vai Vercel»**

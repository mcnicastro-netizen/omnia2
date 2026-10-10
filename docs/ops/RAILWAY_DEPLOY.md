# Deploy API OMNIA su Railway (Plan B — Hetzner bloccato)

**Stato:** ✅ prep repo · ✅ API live · ✅ DNS `api.` + TLS · ✅ Stripe → `api.` · ✅ Vercel FE (D-074)  
**API pubblica:** `OMNIA_API_PUBLIC_URL`  
**Alias Railway:** `https://omnia-api-production-2cec.up.railway.app`  
**Progetto Railway:** `omnia-api` · id ``RAILWAY_PROJECT_ID` (vault)`  
**FE:** Vercel `omnia-frontend` live · runbook: [`VERCEL_DEPLOY.md`](./VERCEL_DEPLOY.md)

Smoke: `GET /api/health` → `status=ok` · `db=ok`.  
Stripe Test: destinazione `OMNIA Railway API (sandbox)` → ``OMNIA_API_PUBLIC_URL` + `/api/billing/webhook``.

---

## Stripe webhook (sandbox → Railway) — fatto 12-Ott-2026

| Voce | Valore |
|------|--------|
| Dashboard | Stripe **Test / Sandbox** |
| Destinazione | `OMNIA Railway API (sandbox)` · id `we_1UPksi5fTeVVWdDf21htElsf` |
| Descrizione | `OMNIA Railway API (sandbox)` — **non** usare `…auto-sync` (lo riscriverebbe `sync-stripe-webhook-url.py` sul tunnel) |
| URL | ``OMNIA_API_PUBLIC_URL` + `/api/billing/webhook`` |
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
   - `RAILWAY_PROJECT_ID=`RAILWAY_PROJECT_ID` (vault)`
   - `OMNIA_API_PUBLIC_URL=`OMNIA_API_PUBLIC_URL`` (solo URL)
3. **Nuovo agent** (le chat vecchie non rileggono il vault)

**CLI quirk:** il nome vault resta `RAILWAY_TOKEN`. `scripts/railway-deploy.sh` lo rimappa a `RAILWAY_API_TOKEN` e unsetta `RAILWAY_TOKEN` (altrimenti Unauthorized).

**UI Cursor:** in chat normale `add_secrets` spesso non mostra «Agent is blocked» / apre solo Personal — bug prodotto. Usare Secrets UI Environment.

### B. Progetto (già creato — riferimento)
1. Progetto `omnia-api` + servizio `omnia-api` + plugin **MongoDB**
2. Root = repo root · `Dockerfile.railway` (pin via GraphQL `dockerfilePath`)
3. Variables già impostate in deploy (MONGO_URL reference `${{MongoDB.MONGO_URL}}`, JWT, CORS, Stripe test, OpenAPI, …)
4. Domain: `api.omniarealestateecosystem.it` (+ alias `omnia-api-production-2cec.up.railway.app`) · `PUBLIC_BASE_URL` = `api.`
5. Volumes: `/app/.media` · `/app/.backups`

### C. DNS (fatto 12-Ott-2026)
Vedi `memory/DNS_SETUP_GUIDE.md` §4c — CNAME `api` → `d13di0kp.up.railway.app` + TXT `_railway-verify.api` · cert VALID.

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
- [x] Stripe sandbox webhook → `api.` (`OMNIA Railway API (sandbox)`)
- [x] `RAILWAY_TOKEN` Account in vault **Environment** omnia2
- [x] `RAILWAY_PROJECT_ID` in vault Environment
- [x] Cloudflare CNAME `api` + TXT verify + cert VALID
- [x] `OMNIA_API_PUBLIC_URL=`OMNIA_API_PUBLIC_URL`` (solo URL)
- [x] Vercel FE + DNS apex/www/app/cloud (smoke 200)

## Probe go-live (diagnostica)

Prima di «vai Railway»: `bash scripts/railway-golive-probe.sh` (token + trial/plan).

# Deploy Vercel FE — prep + go-live (D-074)

**Stato prep:** ✅ repo pronto (10-Ott-2026)  
**Stato deploy:** ⏳ in attesa token Founder (pausa)  
**DNS SoT:** [`memory/DNS_SETUP_GUIDE.md`](../../memory/DNS_SETUP_GUIDE.md)

---

## Dopo la pausa — cosa metti tu in vault (solo nomi)

Dashboard Cursor → env **omnia2** → Secrets (poi **nuovo** agent boot):

| Secret | Dove prenderlo | Serve a |
|--------|----------------|---------|
| `VERCEL_TOKEN` | [Vercel → Account → Tokens](https://vercel.com/account/tokens) | Deploy CLI E2E |
| `VERCEL_ORG_ID` | Vercel → Team/Account Settings → General | Scope progetto |
| `VERCEL_PROJECT_ID` | Dopo primo link progetto (o crealo a mano una volta) | Redeploy |
| `CLOUDFLARE_API_TOKEN` | CF → My Profile → API Tokens (Zone.DNS Edit) | Aggiornare CNAME |
| `CLOUDFLARE_ZONE_ID` | CF → dominio → Overview (Zone ID) | API DNS |
| `OMNIA_API_PUBLIC_URL` | URL HTTPS stabile dell’API prod (es. `https://api.omniarealestateecosystem.it`) | Build FE `REACT_APP_BACKEND_URL` |

Opzionale (se deploy API nello stesso flusso): host già raggiungibile; questo runbook = **FE Vercel**.

**Non mettere in chat** i valori — solo vault.

---

## Cosa è già pronto nel repo

| Pezzo | Path |
|-------|------|
| Config Vercel | `frontend/vercel.json` |
| Env esempio FE | `frontend/.env.example` |
| Check pre-deploy | `scripts/vercel-prep-check.sh` |
| Deploy (quando ci sono token) | `scripts/vercel-deploy.sh` |
| DNS post-deploy | `memory/DNS_SETUP_GUIDE.md` §4 |

---

## Flusso E2E (agent, post-pausa)

Quando Founder dice **«vai Vercel»** e i secret sono nel vault:

1. `bash scripts/vercel-prep-check.sh` → PASS  
2. `bash scripts/vercel-deploy.sh` → build + deploy production  
3. Aggiungere domini in Vercel (apex, www, app, cloud)  
4. Aggiornare Cloudflare (script o checklist DNS_SETUP §4) — togliere Emergent  
5. Smoke: `https://www.omniarealestateecosystem.it/` + login demo  
6. Aggiornare `FRONTEND_*` / CORS sull’API prod  

Finché manca `OMNIA_API_PUBLIC_URL`, il FE in Vercel non può chiamare l’API (build richiede URL assoluto).

---

## Vincoli tecnici (non dimenticare)

1. **`REACT_APP_BACKEND_URL`** in produzione = URL API **assoluto** (es. `https://api.…`).  
   Vuoto = same-origin `/api` → ok solo tunnel/preview, **non** Vercel.  
2. Cookie auth cross-site: API con `COOKIE_SECURE=true` + CORS origins = domini Vercel/CF.  
3. Stripe webhook resta sull’**API**, non su Vercel.  
4. Demo finché non live: tunnel Cloud (`omnia-stack.sh`).

---

## Checklist Founder (pausa → resume)

- [ ] Account Vercel collegato a GitHub `mcnicastro-netizen/omnia2` (o token)  
- [ ] `VERCEL_TOKEN` (+ org/project id se già creato) in vault omnia2  
- [ ] Deciso host API HTTPS (anche temporaneo) → `OMNIA_API_PUBLIC_URL`  
- [ ] (Consigliato) `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ZONE_ID`  
- [ ] Nuovo Cloud Agent su omnia2  
- [ ] Messaggio: **«vai Vercel»**

---

## Verifica locale prep (senza token)

```bash
bash scripts/vercel-prep-check.sh
# opzionale build:
cd frontend && yarn build
```

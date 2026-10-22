# Incident Railway — rotazione credenziali (22-Ott-2026)

**Fonte**: mail Railway Support *Urgent: Railway Security Disclosure - Rotate Credentials*  
**Impatto**: possibile accesso non autorizzato a variabili d’ambiente (anche decrittografate) sui progetti Railway.  
**OMNIA**: progetto `omnia-api` (API live + plugin MongoDB) → **trattare come esposto**.

Railway può aver **bloccato le build** fino a loro ripristino → status: https://status.railway.com

---

## Cosa fare (ordine)

### 1) Provider esterni — revoca e nuova key (prima di riscrivere Railway)

| Secret / area | Dove ruotare | Note |
|---------------|--------------|------|
| `STRIPE_SECRET_KEY` + `STRIPE_PUBLISHABLE_KEY` | Stripe Dashboard → API keys (**Test** e **Live** se usate) | Revoca vecchie; crea nuove |
| `STRIPE_WEBHOOK_SECRET` | Stripe → Webhooks → destinazione Railway | Dopo nuova key: aggiorna endpoint o “Roll secret” → copia `whsec_` nuovo |
| `GEMINI_API_KEY` / `EMERGENT_LLM_KEY` | Google AI Studio / Cloud | Revoca + nuova (HAL, staging vision, brand) |
| `FAL_KEY` | fal.ai dashboard | Staging / video |
| `RESEND_API_KEY` | Resend → API Keys | Mail |
| `OPENAPI_API_KEY` (+ token se usato) | OpenAPI.it console | Visura / planimetria |
| `TAVILY_API_KEY` | Tavily | Se presente su Railway |
| `YOUSIGN_API_KEY` | YouTrust console | Già in scadenza ~25/10 — ruotare ora |
| `JWT_SECRET` | Genera nuovo (`openssl rand -hex 32`) | **Tutti i login scadono** dopo il deploy |
| `ADMIN_PASSWORD` / password demo se su Variables | Cambia e aggiorna | Se erano in chiaro su Railway |
| MongoDB (plugin Railway) | Railway → Mongo service → credentials / rotate | Poi aggiorna `MONGO_URL` (o reference) |
| `RAILWAY_TOKEN` (Account) | railway.app/account/tokens → **revoca tutti** + Create Token | Poi vault Cursor Environment `RAILWAY_TOKEN` |
| Cloudflare / Vercel token | Solo se erano anche Variables Railway | Altrimenti vault Cursor basta |

URL pubblici (`OMNIA_API_PUBLIC_URL`, `PUBLIC_BASE_URL`, CORS) **non** sono segreti: si possono lasciare.

### 2) Railway → Variables del service `omnia-api`

1. Apri progetto `omnia-api` → service `omnia-api` → **Variables**.
2. Sostituisci **ogni** valore sensibile con le key nuove del passo 1 (non lasciare le vecchie).
3. Plugin Mongo: se ruoti DB user/password, aggiorna `MONGO_URL` / reference `${{MongoDB.MONGO_URL}}`.
4. Redeploy quando Railway riabilita le build (fino ad allora può fallire).

### 3) Vault Cursor Environment **omnia2** (in parallelo)

Stesse key usate in Cloud Agent: aggiornale nello scope **Environment** (non Personal), poi **nuovo agent**.  
Vedi `memory/CLOUD_SECRETS_INVENTORY.md`.

### 4) Verifiche post-rotazione

```bash
# health API
curl -sS "$OMNIA_API_PUBLIC_URL/api/health"

# Stripe webhook (sandbox) dopo nuovo whsec su Railway
stripe trigger checkout.session.completed
# → delivery 200 sulla destinazione «OMNIA Railway API (sandbox)»

bash scripts/check-secrets-presence.sh   # in Cloud Agent dopo inject
```

Controlla log: Stripe, Resend, fal, Google AI, OpenAPI.it, YouTrust — attività anomala.

---

## Cosa NON fare

- Non incollare key in chat / PR / commit  
- Non riusare le stesse key “per velocità”  
- Non assumere che solo Cursor vault sia a rischio: **Railway Variables = priorità**  
- Non aspettare il clone sito / feature: questo viene prima  

---

## Chi fa cosa

| Ruolo | Azione |
|-------|--------|
| **Founder** | Revoca/crea key nei dashboard provider + aggiorna Variables Railway + vault Cursor |
| **Agent** | Dopo inject: smoke health/webhook, aggiornare inventario se cambiano *nomi* (non valori) |

**Stato**: 🟠 APERTO — Founder in esecuzione rotazione · 22-Ott-2026

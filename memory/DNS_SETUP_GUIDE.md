# 🌐 DNS — omniarealestateecosystem.it (Cloudflare)

**Aggiornato:** 10 Ottobre 2026  
**Repo:** `mcnicastro-netizen/omnia2`  
**Stato deploy FE:** ⏳ **Vercel NON ancora fatto** (D-074) · ✅ prep repo: [`docs/ops/VERCEL_DEPLOY.md`](../docs/ops/VERCEL_DEPLOY.md)  
**Stato DNS email:** ✅ Resend VERIFIED — vedi [`RESEND_DOMAIN_GUIDE.md`](./RESEND_DOMAIN_GUIDE.md)

---

## 0. Chi fa cosa

| Ruolo | Chi |
|-------|-----|
| **Registrar** | Aruba (solo registrazione dominio) |
| **DNS autoritativo** | **Cloudflare Free** — nameserver `brit.ns.cloudflare.com` + `jose.ns.cloudflare.com` |
| **Email transazionale** | Resend (`info@omniarealestateecosystem.it`) |
| **Email casella** | Aruba mail (record MX `@` invariati) |
| **FE produzione (target)** | Vercel — progetto `frontend/` + `vercel.json` — **⏳ non deployato** |
| **API produzione (target)** | Host ASGI dedicato (non Emergent) — URL tipico `api.omniarealestateecosystem.it` |
| **Dev / demo Cloud** | Tunnel `*.trycloudflare.com` via `scripts/omnia-stack.sh` — **non** è produzione |

**Storico (non usare più come target prod):** Emergent `*.emergent.host` / `audit-tool-12.emergent.host`.  
Se su Cloudflare trovi ancora CNAME `app`/`cloud` → Emergent, sono **legacy** da sostituire al primo deploy Vercel+API.

---

## 1. Schema sottodomini (D-012 — invariato)

| Host | App | Path FE (monorepo) |
|------|-----|--------------------|
| `omniarealestateecosystem.it` / `www` | Landing | `/` |
| `app.omniarealestateecosystem.it` | ImmoWeb CRM | `/app/*` |
| `cloud.omniarealestateecosystem.it` | ImmobilCloud | `/cloud/*` |
| `learn.omniarealestateecosystem.it` | Academy | `/learn/*` (coming soon) |
| `api.omniarealestateecosystem.it` | Backend FastAPI | `/api/*` |
| `agencies.omniarealestateecosystem.it` | Target CNAME siti agenzia (custom domain) | host routing |

Fallback codice: `backend/shared/public_base.py` → `https://omniarealestateecosystem.it`.

---

## 2. Stato attuale (10-Ott-2026) — onesto

| Voce | Stato |
|------|--------|
| NS Cloudflare | ✅ delegati (Aruba → brit/jose) |
| Resend DKIM/SPF/MX/DMARC | ✅ VERIFIED |
| Apex / www risolvono | ✅ Cloudflare anycast |
| HTTP home pubblica | ⚠️ spesso **403** — nessun origin Vercel collegato |
| Deploy Vercel | ⏳ **non fatto** |
| API su `api.` | ⏳ pending host prod |
| Dev demo | Tunnel Cloud Agent (cambia a ogni sessione) |

**Non promettere** `www.omniarealestateecosystem.it` come demo finché Vercel non è collegato.

---

## 3. Record da TENERE (email / Resend) — non toccare

Dettaglio valori in [`RESEND_DOMAIN_GUIDE.md`](./RESEND_DOMAIN_GUIDE.md). Sintesi:

- MX + A `mx` Aruba → casella `@omniarealestateecosystem.it` (**DNS only** ☁️)
- TXT/MX Resend su `send` / `resend._domainkey` / `_dmarc` (**DNS only**)
- Proxy 🟠 solo dove serve HTTP site; **mai** proxy arancione su MX mail

---

## 4. Record FE/API — **dopo** deploy Vercel (checklist)

Quando fai «vai Vercel» + hai URL Vercel + URL API prod  
(runbook completo: [`docs/ops/VERCEL_DEPLOY.md`](../docs/ops/VERCEL_DEPLOY.md)):

### 4a. Vercel (frontend)

1. Import repo `omnia2` → root directory **`frontend`** (usa `frontend/vercel.json`).
2. Env: `REACT_APP_BACKEND_URL=https://api.omniarealestateecosystem.it` (o URL API temporaneo HTTPS).
3. In Vercel → Project → Domains, aggiungi in ordine:
   - `omniarealestateecosystem.it`
   - `www.omniarealestateecosystem.it`
   - `app.omniarealestateecosystem.it`
   - `cloud.omniarealestateecosystem.it`
   - (opz.) `learn.omniarealestateecosystem.it`
4. Vercel mostra i record da mettere su Cloudflare (A/CNAME). **Copia quelli**, non inventare IP.

### 4b. Cloudflare — sostituire legacy Emergent

| Tipo | Nome | Valore (esempio — **usa quelli di Vercel**) | Proxy |
|------|------|-----------------------------------------------|-------|
| A / CNAME | `@` | target Vercel apex | 🟠 o come da Vercel |
| CNAME | `www` | `cname.vercel-dns.com` (o target Vercel) | 🟠 |
| CNAME | `app` | stesso target FE Vercel | 🟠 |
| CNAME | `cloud` | stesso target FE Vercel | 🟠 |
| CNAME | `learn` | stesso target FE Vercel (quando Academy) | 🟠 |

**Rimuovere** (quando Vercel è live):

- CNAME `app` → `audit-tool-12.emergent.host`
- CNAME `cloud` → `audit-tool-12.emergent.host`
- eventuali A apex verso IP Emergent morti

### 4c. API

| Tipo | Nome | Valore | Proxy |
|------|------|--------|-------|
| A o CNAME | `api` | host del backend prod (IP/VPS/Railway/Fly/…) | ☁️ o 🟠 secondo TLS |

Poi env API:

```env
CORS_ORIGINS=https://omniarealestateecosystem.it,https://www.omniarealestateecosystem.it,https://app.omniarealestateecosystem.it,https://cloud.omniarealestateecosystem.it
FRONTEND_URL=https://omniarealestateecosystem.it
FRONTEND_BASE_URL=https://omniarealestateecosystem.it
OMNIA_PUBLIC_URL=https://omniarealestateecosystem.it
```

Webhook Stripe (post-live): `https://api.omniarealestateecosystem.it/api/billing/webhook` — vedi `STRIPE_ONBOARDING.md`.

### 4d. Custom domain agenzie

Invariato: CNAME cliente → `agencies.omniarealestateecosystem.it`  
(`OMNIA_CUSTOM_DOMAIN_CNAME_TARGET`, `custom_domain.py`).

---

## 5. Finché Vercel non c’è — cosa usare

| Uso | URL |
|-----|-----|
| Demo / dogfood Cloud | tunnel da `bash scripts/omnia-stack.sh ensure` → `/tmp/omnia-stack/SHARE_URL.txt` |
| Login demo | `{SHARE_URL}/it/login` · `demo.admin@omniaecosystem.it` |
| Non pubblicare | apex/www come “sito ufficiale” (403 / origin assente) |

Tunnel runbook: [`docs/ops/TUNNEL_RUNBOOK.md`](../docs/ops/TUNNEL_RUNBOOK.md).

---

## 6. Verifiche rapide

```bash
# Nameserver
dig +short NS omniarealestateecosystem.it
# atteso: brit.ns.cloudflare.com / jose.ns.cloudflare.com

# Apex
dig +short omniarealestateecosystem.it A
curl -sI https://www.omniarealestateecosystem.it/ | head -5

# Dopo Vercel: deve essere 200 (non 403)
```

---

## 7. Checklist go-live dominio (ordine)

- [ ] Deploy Vercel FE (`frontend/`) — **pending**
- [ ] Host API HTTPS stabile
- [ ] Domini aggiunti in Vercel + record CF aggiornati (no Emergent)
- [ ] `api.` punta all’API
- [ ] CORS + `FRONTEND_*` + `REACT_APP_BACKEND_URL`
- [ ] Resend ancora VERIFIED (non toccare MX mail Aruba)
- [ ] Smoke: landing / login demo / billing plans
- [ ] Solo dopo: Stripe live webhook su `api.`

---

## 8. Riferimenti

| Doc | Ruolo |
|-----|--------|
| Questo file | SoT DNS + percorso Vercel |
| `RESEND_DOMAIN_GUIDE.md` | Email / migrazione CF storica + record Resend |
| `DECISIONS.md` D-007 · D-012 · D-074 | Dominio · sottodomini · Vercel |
| `STRIPE_ONBOARDING.md` | Webhook su `api.` |
| `frontend/vercel.json` | Config build FE |

*Founder 10-Ott-2026: aggiornare guide; deploy Vercel ancora da fare.*

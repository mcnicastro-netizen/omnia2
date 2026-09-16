# OMNIA — Checklist sicurezza completa (dati · codice · anti-crash · anti-scrape)

**Aggiornato**: 16-Sep-2026 · Owner: Founder + agente  
**Obiettivo**: nessun singolo guasto abbatte l’ecosistema; scraping/clonazione massiva resa costosa e rilevabile.

Legenda stato: ✅ fatto · 🟡 parziale · ❌ da fare · ⏸️ deferred (post-Vercel / decision)

---

## A · Autenticazione & sessioni

| # | Controllo | Stato | Note |
|---|-----------|:-----:|------|
| A1 | JWT access breve + refresh revocabile | ✅ | cookie HttpOnly |
| A2 | Brute-force login (5/15min) | ✅ | `brute_force.py` |
| A3 | Password bcrypt, min 8 | ✅ | |
| A4 | Ruoli + no self-promote admin | ✅ | |
| A5 | MFA / 2FA | ❌ | backlog pre-live enterprise |
| A6 | CSRF esplicito se SameSite=none | 🟡 | SameSite + CORS; token CSRF deferred |
| A7 | Logout invalida refresh | ✅ | |

## B · Multi-tenant & isolamento

| # | Controllo | Stato | Note |
|---|-----------|:-----:|------|
| B1 | Filtro `agency_id` sugli endpoint | ✅ | disciplina per-route |
| B2 | Middleware Mongo auto-tenant | ❌ | rischio: endpoint nuovi senza filtro |
| B3 | HAL Agent injecta agency_id server-side | ✅ | |
| B4 | Isolation fault: errore in un modulo non ferma gli altri | ✅ | lifespan try/except + circuit breaker |

## C · Segreti & cifratura

| # | Controllo | Stato | Note |
|---|-----------|:-----:|------|
| C1 | Credenziali portali AES-256-GCM | ✅ | |
| C2 | Blocco prod senza `CREDENTIALS_MASTER_KEY` | ✅ | `OMNIA_ENV=production` |
| C3 | API keys solo hash SHA-256 | ✅ | show-once |
| C4 | Object storage at-rest encryption | 🟡 | dipende dal provider deploy |
| C5 | Secrets fuori dal repo | ✅ | `.env` gitignored |

## D · API pubbliche & anti-scrape / anti-clone

| # | Controllo | Stato | Note |
|---|-----------|:-----:|------|
| D1 | Rate limit IP search/map/contact | ✅ | |
| D2 | Rate limit globale path pubblici | ✅ | middleware |
| D3 | Rate limit per API key | ✅ | 120/h |
| D4 | Rate limit feed XML | ✅ | |
| D5 | Friction bot (User-Agent / Accept) | ✅ | path bulk |
| D6 | Security headers (nosniff, frame, referrer) | ✅ | |
| D7 | OpenAPI/docs disabilitati in production | ✅ | |
| D8 | Cap page_size / scan window | ✅ | cloud + smart clients |
| D9 | Watermark / branding su media generati | ✅ | staging + video |
| D10 | Legal: ToS + divieto scraping commercial | 🟡 | pagine; enforcement legale offline |
| D11 | Obfuscation FE / DRM codice | ⏸️ | inutile vs reverse; focus API |

## E · Privacy & GDPR

| # | Controllo | Stato | Note |
|---|-----------|:-----:|------|
| E1 | Privacy L1–L4 listings | ✅ | |
| E2 | GDPR hard su contact / register | ✅ | |
| E3 | GDPR hard su lead mutui | ✅ | |
| E4 | DSAR / erasure self-service | ❌ | processo email |
| E5 | Consent log audit | 🟡 | flag su lead |

## F · Pagamenti

| # | Controllo | Stato | Note |
|---|-----------|:-----:|------|
| F1 | Stripe webhook signature | ✅ | |
| F2 | Feature flag STRIPE_ENABLED | ✅ | |
| F3 | Live keys solo post-Vercel | ⏸️ | Founder |

## G · Input & injection

| # | Controllo | Stato | Note |
|---|-----------|:-----:|------|
| G1 | SSRF guard URL fetch | ✅ | path noti |
| G2 | re.escape + cap search | ✅ | |
| G3 | Pydantic validation | ✅ | |
| G4 | Global exception handler no stack leak | ✅ | |

## H · Anti-crash / resilience

| # | Controllo | Stato | Note |
|---|-----------|:-----:|------|
| H1 | Lifespan: seed/scheduler/HAL best-effort | ✅ | warning, non abort |
| H2 | Circuit breaker servizi esterni | ✅ | email / LLM / geocode |
| H3 | Email fallita non alza 500 al caller | ✅ | return status error |
| H4 | Health: DB down → status error, process up | ✅ | |
| H5 | FE ErrorBoundary globale | ✅ | |
| H6 | FE ErrorBoundary per area (cloud / app) | ✅ | |
| H7 | Scheduler job isolated | ✅ | try/except per job |
| H8 | Rate-limit Mongo failure = fail-open log | ✅ | non abbatte request critical path auth |

## I · Operativo go-live (Founder)

| # | Controllo | Stato |
|---|-----------|:-----:|
| I1 | `OMNIA_ENV=production` | ⏸️ |
| I2 | `CREDENTIALS_MASTER_KEY` 32 byte b64 | ⏸️ |
| I3 | `CORS_ORIGINS` espliciti (no `*`) | ⏸️ |
| I4 | `JWT_SECRET` forte e unico | ⏸️ |
| I5 | Mongo Atlas network allowlist | ⏸️ |
| I6 | Backup Mongo schedulati | ⏸️ |
| I7 | Monitoraggio 5xx / 429 (Sentry o equiv.) | ❌ |
| I8 | Rotate API keys procedure | 🟡 | manuale |

---

## Come verificare

```bash
cd backend && source .venv/bin/activate
python scripts/stress_platform_full.py
# Security headers:
curl -sI http://127.0.0.1:43121/api/health | grep -iE 'x-content|x-frame|referrer|permissions'
# Docs nascosti in prod (simula):
OMNIA_ENV=production  # docs/openapi disabilitati
```

## Priorità residua pre-live

1. MFA (A5)  
2. DSAR/erasure API (E4)  
3. Monitoraggio errori (I7)  
4. CSRF token se cookie SameSite=none in prod (A6)  
5. Mongo tenant middleware (B2) — difesa in profondità  

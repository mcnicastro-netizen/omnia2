# Prossima sessione — programma passi

**Aggiornato**: 10 Ottobre 2026 (sera) — API Railway live · pausa Founder  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Branch**: `main`

---

## 🎯 SoT freccia

| Ruolo | Doc |
|-------|-----|
| Freccia | [`docs/audit/OMNIA_COERENZA_SISTEMA.md`](../docs/audit/OMNIA_COERENZA_SISTEMA.md) — S1–S10 ✅ |
| Pre-demo | [`docs/ops/PRE_DEMO_CHECKLIST.md`](../docs/ops/PRE_DEMO_CHECKLIST.md) · [`OMNIA_PRE_DEMO_8.md`](../docs/audit/OMNIA_PRE_DEMO_8.md) |
| **API Railway** | [`docs/ops/RAILWAY_DEPLOY.md`](../docs/ops/RAILWAY_DEPLOY.md) — D-123 · **API live** · vault/DNS pending |
| **Vercel go-live** | [`docs/ops/VERCEL_DEPLOY.md`](../docs/ops/VERCEL_DEPLOY.md) — dopo vault + DNS `api` |

---

## ⚠️ Non dimenticare (domani)

| Voce | Nota |
|------|------|
| **Vault Environment omnia2** | id `b80b635c-b592-11f1-bb68-864e54d14197` — **non** Personal |
| **Revoca token Railway** | `omnia-cursor` (e qualsiasi token finito in chat) → Create nuovo Account token |
| **Salva in Environment** | `RAILWAY_TOKEN` · `RAILWAY_PROJECT_ID=1b31e62e-7ba7-4082-b643-72d221ee7fbe` · `OMNIA_API_PUBLIC_URL=https://omnia-api-production-2cec.up.railway.app` |
| **CLI quirk** | Account token in `RAILWAY_TOKEN` process env → Unauthorized; script rimappa a `RAILWAY_API_TOKEN` |
| **add_secrets UI** | In chat desktop spesso **non** mostra «Agent is blocked» / apre Personal — usare Secrets UI Environment |
| **«vai Vercel»** | Dopo CNAME `api` (o con URL `*.up.railway.app` temporaneo) |
| **Pre-demo probe** | `python scripts/pre_demo_probe.py` prima di ogni invio demo |

---

## Prossimo passo tipico

1. Founder: vault Environment (3 secret sopra) → **nuovo agent**  
2. Cloudflare CNAME `api` → Railway (`memory/DNS_SETUP_GUIDE.md` §4c)  
3. **«vai Vercel»** (D-074)  
4. Demo: tunnel finché dominio FE non è live  

---

## Stato rapido

| Voce | Esito |
|--|--|
| S1–S10 | ✅ |
| **D-123 Railway API** | ✅ live `omnia-api-production-2cec.up.railway.app` · health ok |
| Vault Railway / DNS `api` | ⏳ |
| **D-122 pre-demo ≥8** | ✅ |
| Vercel FE (D-074) | ⏳ |
| D-038 / S3.1 | ⏳ |

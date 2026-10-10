# Prossima sessione — programma passi

**Aggiornato**: 10 Ottobre 2026 (Vercel prep · post-pausa E2E)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Branch**: `main`

---

## 🎯 SoT freccia

| Ruolo | Doc |
|-------|-----|
| Freccia | [`docs/audit/OMNIA_COERENZA_SISTEMA.md`](../docs/audit/OMNIA_COERENZA_SISTEMA.md) — S1–S10 ✅ |
| Pre-demo | [`docs/ops/PRE_DEMO_CHECKLIST.md`](../docs/ops/PRE_DEMO_CHECKLIST.md) · [`OMNIA_PRE_DEMO_8.md`](../docs/audit/OMNIA_PRE_DEMO_8.md) |
| **Vercel go-live** | [`docs/ops/VERCEL_DEPLOY.md`](../docs/ops/VERCEL_DEPLOY.md) — prep ✅ · deploy ⏳ |

---

## ⚠️ Non dimenticare

| Voce | Nota |
|------|------|
| **«vai Vercel»** | Dopo pausa: vault (`VERCEL_TOKEN`, `OMNIA_API_PUBLIC_URL`, CF…) poi agent E2E |
| **Pre-demo probe** | `python scripts/pre_demo_probe.py` prima di ogni invio demo |
| **OFFBOX_BACKUP_ROOT** | In prod = volume esterno (Cloud default `/tmp`) |
| **S3.1** | Firma meter storage |
| **D-038** | Partner APE |
| Stripe live / outreach | Solo con «vai» Founder |
| **Vercel deploy** | ⏳ pending (D-074) — DNS: `memory/DNS_SETUP_GUIDE.md` |

---

## Prossimo passo tipico

1. Founder (pausa): secrets vault da `docs/ops/VERCEL_DEPLOY.md`  
2. Nuovo agent + **«vai Vercel»** → deploy FE + DNS CF  
3. In parallelo: checklist pre-demo manuale 5–10 min / demo su tunnel  

---

## Stato rapido

| Voce | Esito |
|--|--|
| S1–S10 | ✅ |
| **D-122 pre-demo ≥8** | ✅ off-box · dry-run · preflight · C5 KPI/MLS · probe |
| D-038 / S3.1 | ⏳ |

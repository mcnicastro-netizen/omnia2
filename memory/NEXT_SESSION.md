# Prossima sessione — programma passi

**Aggiornato**: 20 Novembre 2026 (~20:00 CET — Europe/Rome)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Lavoro aperto**: PR **#240** `cursor/d175-deal-chat-dossier-h4-e393`  
**Merge #240**: **NO** — in attesa review finale Founder

---

## Dove siamo

| Item | Stato |
|------|-------|
| FIX-01…06 | Chiusi + regressione PASS |
| FIX-07 PDF watermark fail-closed | **Chiuso** |
| FIX-08 reject solo pending | **Chiuso** |
| FIX-09 allegato chat same-collab | **Chiuso** |
| Suite D-175 in CI | **Integrata** in `.github/workflows/ci.yml` |
| Unit remediation | **28 PASS** |
| C5 H4 | **34 PASS** |
| Smoke Dogfood FIX789 | **PASS** |
| H4 sealed / Stripe TEST checkout | **BLOCKED** (fuori autorizzazione) |

## Prossimo passo (Founder)

1. Review conclusiva PR #240 sul tip patch FIX-07/08/09.  
2. Decidere merge **solo** dopo OK esplicito.  
3. Non aprire H4 / Stripe TEST senza nuovo mandato.

## Non fare

- Nuova remediation generale / nuovo ciclo audit.  
- Merge su `main` senza OK Founder.  
- Aprire H4 sealed / Stripe LIVE.

## Letture rapide

- `docs/ops/D175-PR240-DEFINITIVE-REMEDIATION-REPORT.md`
- `memory/DECISIONS.md` (D-175 / D-190)

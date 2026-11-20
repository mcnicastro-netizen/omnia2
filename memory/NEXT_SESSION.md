# Prossima sessione — programma passi

**Aggiornato**: 20 Novembre 2026 (~17:20 CET — Europe/Rome) · fine giornata  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Lavoro aperto**: PR **#240** `cursor/d175-deal-chat-dossier-h4-e393` tip **`1eda988`** (fix remediation **`68b0fc6`**)  
**main**: include D-175 C1–C4 (C4 merge #234); **non** include Deal/chat/mini-dossier di #240  
**Merge #240**: **NO** (Founder — fine giornata)

---

## Dove siamo

| Item | Stato |
|------|-------|
| D-175 C1–C4 | **CHIUSI in main** |
| PR #240 Deal / chat / mini-dossier / watermark | **Aperta** — remediation fatta, **non approvata al merge** |
| FIX-01…06 originari | **Chiusi in codice** (verificati su tip) |
| Bugbot post-remediation | **3 residuali**: PDF watermark fail-hard · reject solo pending · allegato chat same-collab |
| Suite D-175 su tip | 22 + 34 C5 + smoke Dogfood **PASS** (non coperte dal job CI B04) |
| H4 sealed / Stripe TEST checkout | **BLOCKED** — senza nuova autorizzazione |

## Domani — primo passo (obbligatorio)

**Patch mirata PR #240** (solo i 3 finding), sullo stesso branch:

1. `shared/mls_collab/watermark.py` — se `merge_page` PDF fallisce → errore, **mai** servire originale con header watermark.  
2. `collaborations.respond` — `reject` consentito **solo** se status `pending` (active → usare revoke).  
3. `post_chat_message` — richiedere `dr.collaboration_id == thread.collaboration_id`.  
4. Test unit dedicati + smoke Dogfood breve + aggiornare report.  
5. **Non mergeare** finché Founder non approva dopo re-review.

## Non fare

- Nuova remediation generale / nuovo ciclo audit.  
- Merge su `main` senza OK Founder.  
- Aprire H4 sealed / Stripe LIVE.  
- Confondere CI B04 verde con regressione D-175 completa.  
- Dichiarare Deal/chat «in produzione» finché #240 non è mergiata.

## Letture rapide

- `memory/DECISIONS.md` → **D-190**  
- `memory/RIPRENDI_2026-11-20.md`  
- `docs/ops/D175-PR240-DEFINITIVE-REMEDIATION-REPORT.md`  
- PR: https://github.com/mcnicastro-netizen/omnia2/pull/240  
- Cap.27 MLS v1.2 · HAL `api.d175-pr240` / `mls.collaborazioni-workspace`

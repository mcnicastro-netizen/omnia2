# Prossima sessione — programma passi

**Aggiornato**: 17 Settembre 2026 — repo ufficiale GitHub `omnia2` popolato  
**Stato base**: Sprint 1→4 **CONCLUSO**. Stress: `PLATFORM_STRESS_REPORT.md` + `STRESS_REPORT.md`.  
**Preprod gate**: `memory/PREPROD_GATE_REPORT.md` (PASS required — no vendor burn).  
**Repo ufficiale**: https://github.com/mcnicastro-netizen/omnia2 ✅ (Emergent `OMNIA` = backup, non cancellare)  
**Nord prodotto B2C**: `memory/PRODUCT_NORTHSTAR_B2C.md` (**obbligatorio** prima di ship `/cloud`).

---

## Ripresa (checklist)

1. `bash scripts/omnia-stack.sh ensure`
2. **Domani**: eseguire `memory/GESTIONALE_TOOLS_QC_PLAN.md` (prova tutti i tool ImmoWeb, no vendor burn) → report `GESTIONALE_TOOLS_QC_REPORT.md`
3. Review QC esterna (17-Set): prodotto solido; rischio = gerarchia sidebar + dashboard non «cosa fare oggi»; Clienti/HAL differenziante — **no implementazione redesign senza «vai»**
4. Spegnere `CRM_PUBLIC_PREVIEW` dopo review esterna (`=0` + restart-preview)
5. Founder: **«vai»** sull’ID se fuori programma
6. **D-084**: ogni ship aggiorna manuale+YAML
7. Preprod: `python scripts/preprod_confidence_gate.py` prima di go-live / ship rischiosi

---

## Dove siamo

| Area | Stato |
|------|:-----:|
| Sprint 1→4 | ✅ |
| Gap ImmobilCloud + stress | ✅ |
| Preprod confidence gate (no € / no ban) | ✅ (17-Set) |
| Repo ufficiale GitHub `omnia2` | ✅ (17-Set) |
| Gestionale ingresso CRM + dashboard quick actions | ✅ (17-Set) |
| Gestionale stress S0–S6 @ 2000 clients | ✅ PASS (`GESTIONALE_STRESS_REPORT.md`) |
| Home B2C visual + SSR preview | ✅ (16-Set) |
| Layout altre pagine B2C | ✅ (17-Set) |
| Scout v1 + fiducia + voce lister | ✅ |
| Scout thin visita + documenti | ✅ (17-Set) |
| Contatto privato email/tel/WA + UI panel | ✅ (17-Set) |
| Nord A / B′ / C | ✅ |
| Nord **B** home claim | ✅ di fatto (hero già pre-visita; ritocco fine ⬜ opzionale) |
| Nord **D** intake annuncio esterno | ⏸️ solo con «vai» + legale |
| Demo **A-025** | ❌ **next di programma** (architettare, non shippare a caso) |
| A-026 micro-tour agenzia (501→Kling) | 🔬 da approfondire |
| Stripe live / A-014 | ⏸️ post-Vercel |
| Prod flags readiness (`cookie_secure`, CORS, master key, monitoring, `OMNIA_ENV`) | ⚠️ solo su host prod |
| Competitor «prima visita» | ✅ ricercato (remoto agent-led ≠ Scout) |

---

## Ordine consigliato

| # | Cosa | Note |
|:-:|------|------|
| 1 | **A-025 demo prodotto** | GTM / walkthrough Scout end-to-end — richiede «vai» |
| 2 | Home claim micro-ritocco | Solo se Founder vuole ancora più “pre-visita” |
| — | Intake annuncio esterno (Nord D) | Solo dopo ok Founder + scope legale |
| — | A-026 path Kling agenzia | Approfondire UX (docs Cap.23 già allineati) |
| — | A-014 Stripe live | post-Vercel |
| — | Go-live env flags | readiness WARN locali → set su Vercel |

Report: `memory/PREPROD_GATE_REPORT.md` · `memory/PLATFORM_STRESS_REPORT.md` · `memory/STRESS_REPORT.md` · `memory/PRODUCT_NORTHSTAR_B2C.md`

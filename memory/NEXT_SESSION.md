# Prossima sessione — programma passi

**Aggiornato**: 18 Settembre 2026 — Tools QC gestionale chiuso  
**Stato base**: Sprint 1→4 **CONCLUSO**. Stress: `PLATFORM_STRESS_REPORT.md` + `STRESS_REPORT.md`.  
**Preprod gate**: `memory/PREPROD_GATE_REPORT.md` (PASS required — no vendor burn).  
**Repo ufficiale**: https://github.com/mcnicastro-netizen/omnia2 ✅ (Emergent `OMNIA` = backup, non cancellare)  
**Nord prodotto B2C**: `memory/PRODUCT_NORTHSTAR_B2C.md` (**obbligatorio** prima di ship `/cloud`).

---

## Ripresa (checklist)

1. `bash scripts/omnia-stack.sh ensure`
2. ✅ **Tools QC ImmoWeb** eseguito → `memory/GESTIONALE_TOOLS_QC_REPORT.md` (**PASS 69 / FAIL 1 / SKIP 2 / GAP 1**)
3. Review QC esterna → backlog **A-028**: gerarchia sidebar, cockpit «Oggi», Match Score explainability, HAL contestuale — **no implementazione senza «vai»**
4. ✅ `CRM_PUBLIC_PREVIEW=false` (preview healthz)
5. Founder: **«vai»** su Top 5 A-028 (o ID fuori programma)
6. **D-084**: ogni ship aggiorna manuale+YAML
7. Preprod: `python scripts/preprod_confidence_gate.py` prima di go-live / ship rischiosi
8. Nota tecnica: `GET /app/matches` agency-wide sotto stress seed (~2M pairs) uccide API — usare solo client-scoped `min_score`+`limit`

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
| **Gestionale tools QC A→E + loop mattina** | ✅ (18-Set) `GESTIONALE_TOOLS_QC_REPORT.md` |
| Home B2C visual + SSR preview | ✅ (16-Set) |
| Layout altre pagine B2C | ✅ (17-Set) |
| Scout v1 + fiducia + voce lister | ✅ |
| Scout thin visita + documenti | ✅ (17-Set) |
| Contatto privato email/tel/WA + UI panel | ✅ (17-Set) |
| Nord A / B′ / C | ✅ |
| Nord **B** home claim | ✅ di fatto (hero già pre-visita; ritocco fine ⬜ opzionale) |
| Nord **D** intake annuncio esterno | ⏸️ solo con «vai» + legale |
| Demo **A-025** | ❌ **next di programma** (architettare, non shippare a caso) |
| **A-028** redesign gerarchia ImmoWeb | ⏸️ solo con «vai» post-report |
| A-026 micro-tour agenzia (501→Kling) | 🔬 da approfondire |
| Stripe live / A-014 | ⏸️ post-Vercel |
| Prod flags readiness (`cookie_secure`, CORS, master key, monitoring, `OMNIA_ENV`) | ⚠️ solo su host prod |
| Competitor «prima visita» | ✅ ricercato (remoto agent-led ≠ Scout) |

---

## Ordine consigliato

| # | Cosa | Note |
|:-:|------|------|
| 1 | **A-028 Top 5** (cockpit Oggi → score → sidebar → HAL contestuale → Attività) | Solo «vai» Founder |
| 2 | **A-025 demo prodotto** | GTM / walkthrough Scout end-to-end — richiede «vai» |
| 3 | Fix perf `GET /app/matches` agency-wide | FAIL QC A8 — pagination/early-exit sotto seed 2k |
| — | Home claim micro-ritocco | Solo se Founder vuole ancora più “pre-visita” |
| — | Intake annuncio esterno (Nord D) | Solo dopo ok Founder + scope legale |
| — | A-026 path Kling agenzia | Approfondire UX (docs Cap.23 già allineati) |
| — | A-014 Stripe live | post-Vercel |
| — | Go-live env flags | readiness WARN locali → set su Vercel |

Report: `memory/GESTIONALE_TOOLS_QC_REPORT.md` · `memory/PREPROD_GATE_REPORT.md` · `memory/PLATFORM_STRESS_REPORT.md` · `memory/STRESS_REPORT.md` · `memory/PRODUCT_NORTHSTAR_B2C.md`

# Prossima sessione — programma passi

**Aggiornato**: 17 Settembre 2026 — preprod confidence gate  
**Stato base**: Sprint 1→4 **CONCLUSO**. Stress: `PLATFORM_STRESS_REPORT.md` + `STRESS_REPORT.md`.  
**Preprod gate**: `memory/PREPROD_GATE_REPORT.md` (PASS required — no vendor burn).  
**Nord prodotto B2C**: `memory/PRODUCT_NORTHSTAR_B2C.md` (**obbligatorio** prima di ship `/cloud`).

---

## Ripresa (checklist)

1. `bash scripts/omnia-stack.sh ensure`
2. Ports → **omnia-preview :43123** (o tunnel CF verso 43123)
3. Rileggere `PRODUCT_NORTHSTAR_B2C.md`
4. Founder: **«vai»** sull’ID se fuori programma
5. **D-084**: ogni ship aggiorna manuale+YAML ✅ (17-Set: Cap.18 inquiry privato + Cap.23 Ken Burns)
6. Preprod: `python scripts/preprod_confidence_gate.py` prima di go-live / ship rischiosi

---

## Dove siamo

| Area | Stato |
|------|:-----:|
| Sprint 1→4 | ✅ |
| Gap ImmobilCloud + stress | ✅ |
| Preprod confidence gate (no € / no ban) | ✅ (17-Set) |
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

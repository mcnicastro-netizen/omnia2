# Prossima sessione — programma passi

**Aggiornato**: 21 Settembre 2026 — ripristino flusso GitHub omnia2 (D-087) · hub import A–E · D-086 Cloud  
**Stato base**: Sprint 1→4 **CONCLUSO**. Stress: `PLATFORM_STRESS_REPORT.md` + `STRESS_REPORT.md`.  
**Preprod gate**: `memory/PREPROD_GATE_REPORT.md` (PASS required — no vendor burn).  
**Repo ufficiale**: https://github.com/mcnicastro-netizen/omnia2 ✅ — **apri gli agent QUI**. Origin-tmp non è master. Setup: `memory/OMNIA2_REPO_SETUP.md`.  
**Nord prodotto B2C**: `memory/PRODUCT_NORTHSTAR_B2C.md` (**obbligatorio** prima di ship `/cloud`).

---

## Ripresa (checklist)

1. `bash scripts/omnia-stack.sh ensure`
2. ✅ **Tools QC ImmoWeb** eseguito → `memory/GESTIONALE_TOOLS_QC_REPORT.md` (**PASS 69 / FAIL 1 / SKIP 2 / GAP 1**)
3. Review QC esterna → backlog **A-028**: gerarchia sidebar, cockpit «Oggi», Match Score explainability, HAL contestuale — **no implementazione senza «vai»**
4. ✅ `CRM_PUBLIC_PREVIEW=false` (preview healthz)
5. ✅ **Valutatore mini-sample** → `memory/GESTIONALE_VALUATOR_ACCURACY_SAMPLE.md` (**PASS 20 / FAIL 0** — non è prova OMI ~27k)
6. ✅ **Cap. 21 + HAL + `hal-index.json`** allineati 100% (PDF white-label + roll-forward FOI/trend)
7. ✅ **18-Set gestionale**: Social 6 canali · planimetrie Cap.3 · Portali wizard/i18n/Compliance · `hal-index` **v0.20** (339 voci)
8. ✅ **19-Set HAL live reindex** `force=true` (super_admin): aggiornato con Cestino (v0.22)
8b. ✅ **19-Set Gruppo Real Estate Spa** + API key + sim Ruota PASS · Cap.20/24 + HAL `api-keys.ruota-chiave-smarrita` · index **v0.21-gruppi-rotate**
8c. ✅ **19-Set Cestino 30gg** immobili/clienti · `/app/trash` · Cap.3/4 semplici · HAL `cestino.ripristinare` · index **v0.22-cestino**
8d. ✅ **19-Set D-085** quota 30/100/300 + polish errori «spazio esaurito» Cap.3/7/19 + HAL · reindex **846** chunk / **342** voci
9. Founder: **«vai»** su Top 5 A-028 (o ID fuori programma)
10. **D-084**: ogni ship aggiorna manuale+YAML+index (sempre 100%)
11. Preprod: `python scripts/preprod_confidence_gate.py` prima di go-live / ship rischiosi
12. Nota tecnica: `GET /app/matches` agency-wide sotto stress seed (~2M pairs) uccide API — usare solo client-scoped `min_score`+`limit`
13. ✅ **Cleanup Emergent incrementale** (19-Set): shared.llm · alias key · stub/pacchetti fuori · FE visual-edits fuori · test URL locali
14. ⏸️ **i18n EN/ES copertura uniforme gestionale** — selettore OK; molte UI ancora IT hardcoded — solo con «vai»
15. ⏸️ Residui minori Emergent (CDN BrandLab, `STORAGE_BACKEND=emergent` dead path, alias env) — opzionale
16. ✅ **Backup + quota storage (D-085)** — 30/100/300 GB + extra €15 · meter · blocco upload · backup cron
17. ⏸️ Residui minori Emergent (CDN BrandLab, `STORAGE_BACKEND=emergent` dead path, alias env) — opzionale
18. ⏸️ Seed Stripe price `storage_100gb_monthly` + testo contratto/DPA fine abbonamento (legale)
19. ✅ **D-087**: apri i prossimi Cloud Agent **solo** su GitHub `omnia2` (vedi `OMNIA2_REPO_SETUP.md`)

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
| **A-028a Cockpit Dashboard «Oggi»** | ✅ (18-Set) `/app/dashboard/today` |
| **Valutatore mini-sample accuratezza** | ✅ (18-Set) PASS 20/20 — `GESTIONALE_VALUATOR_ACCURACY_SAMPLE.md` |
| **Report PDF UNI (layout elegante)** | ✅ (18-Set) OMNIA + whitelabel + hybrid — `valuation_pdf.py` |
| **Cap.21 / HAL / hal-index 100%** | ✅ (18-Set) FOI roll-forward + PDF brand |
| **Social Publisher 6 canali (WA/WABA/GBP)** | ✅ (18-Set) Cap.15 + HAL |
| **Planimetrie JPEG/PDF su immobile** | ✅ (18-Set) Cap.3 + HAL |
| **Portali wizard UX + i18n `portali`** | ✅ (18-Set) Cap.6 + HAL |
| **HAL Mongo reindex live (force)** | ✅ (19-Set) v0.23 D-085 polish |
| **Gruppo Real Estate Spa + Ruota API key** | ✅ (19-Set) sim PASS · Cap.20/24 · smoke Ruota top-1 |
| **Cestino 30gg immobili/clienti** | ✅ (19-Set) `/app/trash` · Cap.3/4 · soft-delete |
| **D-085 Storage quota + backup** | ✅ (19-Set) 30/100/300 + €15 · meter · blocco · backup cron |
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
| A-026 micro-video agenzia (501→Kling) | 🔬 da approfondire |
| Cleanup residui Emergent | ✅ (19-Set) core fatto; CDN BrandLab / alias env opzionali |
| i18n EN/ES copertura uniforme CRM | ⏸️ solo con «vai» |
| Stripe live / A-014 | ⏸️ post-Vercel |
| Prod flags readiness (`cookie_secure`, CORS, master key, monitoring, `OMNIA_ENV`) | ⚠️ solo su host prod |
| Competitor «prima visita» | ✅ ricercato (remoto agent-led ≠ Scout) |

---

## Ordine consigliato

| # | Cosa | Note |
|:-:|------|------|
| 1 | **A-028 Top rimanenti** (score → sidebar → HAL contestuale → Attività) | A-028a cockpit ✅ 18-Set; resto solo «vai» |
| 2 | **A-025 demo prodotto** | GTM / walkthrough Scout end-to-end — richiede «vai» |
| 3 | Fix perf `GET /app/matches` agency-wide | FAIL QC A8 — pagination/early-exit sotto seed 2k |
| — | Cleanup Emergent / i18n EN-ES full | Emergent core ✅ 19-Set; i18n solo con «vai» |
| — | Home claim micro-ritocco | Solo se Founder vuole ancora più “pre-visita” |
| — | Intake annuncio esterno (Nord D) | Solo dopo ok Founder + scope legale |
| — | A-026 path Kling agenzia | Approfondire UX (docs Cap.23 già allineati) |
| — | A-014 Stripe live | post-Vercel |
| — | Seed Stripe `storage_100gb_monthly` + contratto/DPA fine abbonamento | residuo D-085 · con legale |
| — | Go-live env flags | readiness WARN locali → set su Vercel |

Report: `memory/GESTIONALE_TOOLS_QC_REPORT.md` · `memory/GESTIONALE_VALUATOR_ACCURACY_SAMPLE.md` · `memory/PREPROD_GATE_REPORT.md` · `memory/PLATFORM_STRESS_REPORT.md` · `memory/STRESS_REPORT.md` · `memory/PRODUCT_NORTHSTAR_B2C.md`

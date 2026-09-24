# Prossima sessione — programma passi

**Aggiornato**: 24 Settembre 2026 — D-093 P0 (stats privato + alert preferiti ended) · poi **analisi gestionale**  
**Stato base**: Sprint 1→4 **CONCLUSO**. Stress: `PLATFORM_STRESS_REPORT.md` + `STRESS_REPORT.md`.  
**Preprod gate**: `memory/PREPROD_GATE_REPORT.md` (PASS required — no vendor burn).  
**Repo ufficiale**: https://github.com/mcnicastro-netizen/omnia2 ✅ — **apri gli agent QUI**. Origin-tmp non è master. Setup: `memory/OMNIA2_REPO_SETUP.md`.  
**Nord prodotto B2C**: `memory/PRODUCT_NORTHSTAR_B2C.md` (**obbligatorio** prima di ship `/cloud`).

---

## Ripresa (checklist)

1. `bash scripts/omnia-stack.sh ensure`
2. Login demo: `demo.admin@omniaecosystem.it` / `DEMO_ADMIN_PASSWORD` (tunnel HTTPS: cookie Secure OK su Safari/Firefox/Chrome)
3. **Founder: analisi del gestionale** (tema ancora aperto)
4. ✅ **D-092** shippata: Dashboard destinazioni, Import hub, Clienti↔Richieste, Portali 3 tab, API Keys in Impostazioni, wizard Gruppo
5. ✅ Login tunnel: same-origin `/api` + Secure cookie rewrite in `preview-server.js`
6. ✅ **D-093 P0**: A-029 stats privato · A-030 alert preferiti ended (A-031…033 backlog, solo con «vai»)
7. ✅ Tools QC ImmoWeb → `memory/GESTIONALE_TOOLS_QC_REPORT.md`
8. Backlog **A-028** (sidebar gerarchia, Match Score explainability, HAL contestuale) — **no implementazione senza «vai»**
9. **D-084**: ogni ship aggiorna manuale+YAML+index
10. Preprod: `python scripts/preprod_confidence_gate.py` prima di go-live / ship rischiosi
11. ✅ **D-087**: Cloud Agent solo su GitHub `omnia2`
12. ✅ **D-088 / D-089 / D-090 / D-091**: Mongo JIT, Richieste, matching notturno, no MyAgency
13. ⏸️ i18n EN/ES uniforme gestionale — solo con «vai»
14. ⏸️ Seed Stripe `storage_100gb_monthly` + DPA fine abbonamento (legale)

---

## Dove siamo

| Area | Stato |
|------|:-----:|
| Sprint 1→4 | ✅ |
| D-092 UX CRM | ✅ (23-Set) |
| D-093 P0 B2C gap Imm/Idealista | ✅ A-029/A-030 (24-Set) |
| Login tunnel HTTPS | ✅ Secure cookies |
| Richieste + matching D-089/090 | ✅ |
| Repo GitHub `omnia2` | ✅ |
| Prossima: analisi gestionale | 🔜 |

---

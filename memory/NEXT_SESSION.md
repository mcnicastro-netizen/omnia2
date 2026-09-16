# Prossima sessione — programma passi

**Aggiornato**: 16 Settembre 2026 — stress CRM 10k clienti eseguito  
**Stato base**: Sprint 1→4 **CONCLUSO**. Stress: `memory/STRESS_REPORT.md`.

---

## Ripresa (checklist)

1. `bash scripts/omnia-stack.sh ensure`
2. Ports → **omnia-preview :43123**
3. Founder: **«vai»** sull’ID (o su fix stress)
4. **D-084**: ogni ship aggiorna manuale+YAML

---

## Dove siamo

| Area | Stato |
|------|:-----:|
| Sprint 1→4 | ✅ |
| D-084 sync manuale | ✅ |
| Stress CRM clienti → 10k | ✅ report |
| Bottleneck `/clients/smart` | 🔴 da fix |
| Demo A-025 | ❌ |
| Stripe live | ⏸️ post-Vercel |

---

## Ordine consigliato

| # | Cosa | Note |
|:-:|------|------|
| 1 | **Fix `/app/clients/smart` scale** | Stress: 17s p95 @ 10k |
| 2 | **A-025** demo prodotto | GTM |
| 3 | Ladder agenzie MLS 5k/10k | `load_ladder_mls.py` |
| — | A-014 Stripe live | solo post-Vercel |

Report: `memory/STRESS_REPORT.md` · JSON: `memory/reports/stress_clients_latest.json`

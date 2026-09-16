# Prossima sessione — programma passi

**Aggiornato**: 16 Settembre 2026 — D-084 sync manuale attivo · Cap. 18 allineato  
**Stato base**: Sprint 1→4 **CONCLUSO**. Ultimo feature ship: **A-017**. Ultimo docs: **D-084**.

---

## Ripresa (checklist)

1. `bash scripts/omnia-stack.sh ensure`
2. Ports → **omnia-preview :43123**
3. Founder: **«vai»** sull’ID
4. **Obbligo D-084**: ogni ship aggiorna `manuale/` + `hal/*.yaml` nello stesso giro (`MANUAL_SYNC.md`)

**Non ripartire da** Stripe live / webhook / Emergent / Vercel.

---

## Dove siamo

| Area | Stato |
|------|:-----:|
| Sprint 1→4 | ✅ |
| Manuale 27/27 redazione | ✅ |
| Sync manuale automatico (D-084) | ✅ regola attiva |
| Cap. 18 post A-017/A-021 | ✅ v1.1 |
| Drift Cap. 9/12/13 (A-013/A-006/A-007) | ✅ |
| Demo prodotto | ❌ **A-025** |
| Stripe live | ⏸️ post-Vercel |
| M4 / M6 | ⏸️ |

---

## Ordine con «vai»

| # | ID | Cosa |
|:-:|---|---|
| 1 | **A-025** | Architettura demo prodotto (GTM) |
| 2 | A-008 | Cambio ruolo membro |
| 3 | A-018 | Activity feed (post A-017) |

Fine percorso: Vercel → A-014 Stripe live.

Credenziali: `memory/test_credentials.env`.

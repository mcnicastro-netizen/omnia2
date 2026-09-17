# Prossima sessione — programma passi

**Aggiornato**: 17 Settembre 2026 — layout roll-out B2C  
**Stato base**: Sprint 1→4 **CONCLUSO**. Stress: `PLATFORM_STRESS_REPORT.md` + `STRESS_REPORT.md`.  
**Nord prodotto B2C**: `memory/PRODUCT_NORTHSTAR_B2C.md` (**obbligatorio** prima di ship `/cloud`).

---

## Ripresa (checklist)

1. `bash scripts/omnia-stack.sh ensure`
2. Ports → **omnia-preview :43123** (o tunnel CF verso 43123)
3. Rileggere `PRODUCT_NORTHSTAR_B2C.md`
4. Founder: **«vai»** sull’ID se fuori programma
5. **D-084**: ogni ship aggiorna manuale+YAML

---

## Dove siamo

| Area | Stato |
|------|:-----:|
| Sprint 1→4 | ✅ |
| Gap ImmobilCloud + stress | ✅ |
| Home B2C visual + SSR preview | ✅ (16-Set) |
| Layout altre pagine B2C | ✅ (17-Set) — search, scheda, account, valuta, mutui, vendi, register, visura |
| Scout v1 (completezza / zona / domande) | ✅ base |
| Scout fiducia (fascia + perché + confidenza) | ❌ **next** |
| Demo A-025 | ❌ |
| Stripe live | ⏸️ post-Vercel |

---

## Ordine consigliato (filtrato — solo utile al portale)

| # | Cosa | Note |
|:-:|------|------|
| 1 | **Scout depth + fiducia** | Fascia prezzo, perché, limiti/confidenza; lacune; domande; UI leggibile. Vedi northstar P0–P1 |
| 2 | **Home B2C allineata al nord** | Claim = pre-visita / “cosa sapere prima”; Valuta/Mutui/Vendi secondari (già avviato in home) |
| 3 | **Scout thin “visita + documenti”** | Stesso pannello, non nuovo prodotto |
| 4 | A-025 demo prodotto | GTM |
| — | Intake “annuncio da altri portali” | Solo dopo 1–3 + ok Founder |
| — | A-014 Stripe live | solo post-Vercel |
| — | Ladder MLS / reti locali | Binario **B2B**, non copy home privati |

**Chiusura 17-Set (mattina):** layout/grafica allineata su superfici cloud via `CloudPageHero` + navy/brass/Fraunces/foto. Next = Scout depth.

Report: `memory/PLATFORM_STRESS_REPORT.md` · `memory/STRESS_REPORT.md` · `memory/PRODUCT_NORTHSTAR_B2C.md`

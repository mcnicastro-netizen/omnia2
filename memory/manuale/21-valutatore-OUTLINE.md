# Cap. 21 · Valutatore immobiliare — OUTLINE (post-implementazione B2C-VAL-01)

**Stato**: ✅ PUBBLICATO — Cap. 21 scritto post B2C-VAL-01 (Ago 2026)  
**Regola D-051**: ogni paragrafo deve riflettere UI/codice live al momento della scrittura  
**Cursor scrive**: MD + YAML HAL dopo merge Founder su `main`

---

## Obiettivo capitolo

Spiegare al privato su ImmobilCloud e all'agente (cross-ref) come funzionano **due livelli** di valutazione, senza jargon API.

---

## Struttura proposta (~12 voci HAL)

### §21.1 Cos'è il Valutatore OMNIA
- Strumento stima mercato per immobili residenziali in Italia
- Due livelli: **Stima rapida (base)** vs **Valutazione UNI 10750 + PDF**
- Dove si trova: `/cloud/valutatore` + CTA su scheda annuncio

### §21.2 Stima rapida gratuita (base)
- Cosa serve: città, zona, tipologia, mq, stato, energia
- Limite: **1 ogni 12 mesi** · account con email verificata
- Cosa ottieni: valore orientativo + range + €/m²
- Cosa **non** include: superficie commerciale UNI, coefficienti merito, PDF

### §21.3 Valutazione UNI 10750 + PDF (a pagamento B2C)
- Prezzo privati: **€2,99** carta
- Cosa aggiunge: superfici ponderate (balconi, box, cantina…), merito (esposizione, vista, piano…)
- Report PDF brandizzato (OMNIA o agenzia se agente loggato)
- Disclaimer: stima orientativa, non perizia vincolante

### §21.4 Differenza base vs UNI (tabella utente)
| | Base | UNI + PDF |
|---|------|-----------|
| Prezzo | Gratis | €2,99 |
| Frequenza | 1×/12 mesi | A pagamento |
| Superficie | Calpestabile | Commerciale UNI |
| Merito | No | Sì |
| PDF | No | Sì |

### §21.5 Come fare una stima base (passi UI)
1. Accedi a ImmobilCloud
2. Scegli "Stima rapida"
3. Compila form
4. Leggi risultato + upsell UNI

### §21.6 Come ottenere il report UNI (passi UI)
1. Scegli tier UNI o upsell da risultato base
2. Compila Modalità Pro (superfici + merito)
3. Paga €2,99 (Stripe)
4. Scarica PDF

### §21.7 Valutatore per le agenzie (cross-ref B2B)
- Stesso motore, rail **crediti** (non carta)
- Base: 6 crediti · UNI+PDF: 12 crediti
- Cross-ref Cap. 7 Fascicolo (stima base integrata)
- Cross-ref Cap. 20 API partner (Track B, 5 crediti)

### §21.8 Affidabilità e dati di mercato
- Dataset OMI/Borsino 2025, fallback provincia/regione
- Livelli confidence (alta/media/orientativa)
- Comparables da annunci attivi piattaforma

### §21.9 Limitazioni oneste (D-051)
- Non sostituisce perizia bancaria o CTU
- Comuni piccoli: fallback provinciale
- Tier base: no PDF, no merito

### §21.10 Errori comuni
- "Ho esaurito la stima gratis" → attendere 12 mesi o passare a UNI
- "Non scarica il PDF" → serve pagamento UNI
- "Pro non disponibile" → tier sbagliato o non loggato

### §21.11 Privacy e lead
- Email opzionale su base → lead `valuation_leads` se compilata
- GDPR: cross-ref impostazioni account

### §21.12 Collegamenti utili
- Cap. 11 Mutui (capacità di acquisto dopo stima)
- Cap. 3 Immobili / Cap. 8 Sito (widget futuro?)
- Cap. 19 Impostazioni account

---

## Voci HAL YAML (prefisso suggerito `valutatore.*`)

1. `valutatore.cos-e`
2. `valutatore.tier-base-gratis`
3. `valutatore.tier-uni-pdf`
4. `valutatore.differenza-base-uni`
5. `valutatore.passi-stima-base`
6. `valutatore.passi-report-uni`
7. `valutatore.agenzie-crediti`
8. `valutatore.affidabilita-dati`
9. `valutatore.limitazioni`
10. `valutatore.errori-comuni`
11. `valutatore.privacy-lead`
12. `valutatore.collegamenti`

---

## Screenshot placeholder

- `[SCREEN: valutatore-tier-scelta]`
- `[SCREEN: valutatore-base-risultato-upsell]`
- `[SCREEN: valutatore-uni-pro-form]`
- `[SCREEN: valutatore-pdf-download]`
- `[SCREEN: valutatore-cta-scheda-annuncio]`

---

*Outline Cursor · post B2C-VAL-01*

# TASK B2C-VAL-01 — Valutatore ImmobilCloud dual-tier (implementazione integrale)

Sei su branch main, repo OMNIA. Implementa TUTTO quanto segue. Non chiedere conferme intermedie.

Prima azione: crea la cartella /app/memory/briefs/ e salva questo stesso testo in
/app/memory/briefs/EMERGENT_TASK_B2C_VALUATOR_DUAL_TIER.md
Poi implementa subito.

═══════════════════════════════════════════════════════════════
CONTESTO
═══════════════════════════════════════════════════════════════

Founder decisione 16-Ago-2026. Riferimento pricing: /app/memory/PRICING_B2C.md v1.0
e /app/backend/apps/billing/b2c_products.py (stub già presente).

PROBLEMA OGGI su /it/cloud/valutatore:
- Stima base ILLIMITATA e gratis per tutti (anche anonimi)
- Modalità Pro UNI 10750 GRATIS
- PDF report GRATIS con un click
- Nessun upsell, nessuna CTA su scheda annuncio

COSA DEVE ESSERCI DOPO IL TASK:
- TIER BASE: stima rapida GRATIS, 1 valutazione ogni 12 mesi, solo utente loggato con email verificata, NO PDF, NO merito UNI, NO commercial_surfaces
- TIER UNI: superficie commerciale UNI 10750 + coefficienti merito + PDF a €2,99 via Stripe one-shot
- Upsell da base verso UNI
- CTA valutatore su scheda annuncio immobile

Il motore esiste già ed è OK — NON riscriverlo:
- backend/apps/immocloud/valuator.py
- backend/apps/immocloud/data/coefficients.py
- backend/apps/immocloud/valuation_pdf.py

Manca solo: gate commerciale + checkout Stripe + UX a due livelli.

Regola D-051: implementa esattamente quanto scritto. Zero fallback "PDF gratis se Stripe fallisce".

═══════════════════════════════════════════════════════════════
TIER 1 — BASE (lead magnet)
═══════════════════════════════════════════════════════════════

Prezzo B2C: GRATIS
Limite: 1 valutazione ogni 12 mesi per user_id (server-side, collection MongoDB)
Requisito: utente LOGGATO ImmobilCloud + email_verified = true
Anonimo: 401 "Accedi per la stima gratuita" — NON permettere stima base anonima

Input ammessi SOLO campi semplici:
  city, zone, address, property_type, surface_sqm (calpestabile), condition, energy_class, floor
Input VIETATI (se presenti → 402 payment_required):
  commercial_surfaces, merit

Superficie usata: surface_sqm calpestabile (method calpestabile_only nel response)
Output: valore + range + €/m² + comparables + disclaimer
PDF: NON disponibile sul tier base — nessun bottone PDF nei risultati base

Anti-abuso: collection b2c_valuation_usage, max 1 record tier=base negli ultimi 365 giorni per user_id.
Se limite esaurito → 429 con messaggio chiaro + data reset + CTA verso tier UNI a pagamento.

═══════════════════════════════════════════════════════════════
TIER 2 — UNI 10750 + PDF
═══════════════════════════════════════════════════════════════

Prezzo B2C: €2,99 one-shot Stripe
Product key: b2c_valuator_uni_pdf (da b2c_products.py, stripe_lookup_key: b2c_valuator_uni_pdf)
Daily cap: max 5 acquisti UNI/giorno per utente

Input: campi base + commercial_surfaces + merit (esattamente la "Modalità Pro" attuale in ValuatorPage.jsx)
Superficie: commerciale ponderata UNI 10750
Output: breakdown superfici + coefficienti merito + confidence più alta
PDF: SOLO dopo pagamento confermato O entitlement B2B (crediti agenzia)
Entitlement UNI valido 24h per stesso payload_hash (sha256 del payload JSON) — non far ripagare entro 24h.

Upsell obbligatorio dopo ogni stima base completata:
  "Vuoi una valutazione UNI 10750 con report PDF professionale? €2,99"

═══════════════════════════════════════════════════════════════
AGENTE B2B (ImmoWeb) — eccezione
═══════════════════════════════════════════════════════════════

Se utente loggato è agente con agency_id:
- NON usare Stripe B2C
- Scala crediti agenzia come già in plans.py:
  valuator_base = 6 crediti, valuator_uni_pdf = 12 crediti
- PDF brandizzato agenzia (già in valuation_pdf.py) resta attivo
- UI /cloud/valutatore: mostra "Usa crediti agenzia" invece di €2,99

CRITICO — NON rompere fascicolo.py:
Il Fascicolo immobile chiama estimate_value in base mode lato agenzia.
Soluzione: flag interno caller=agency_fascicolo (query param o header interno) che bypassa gate B2C.
Verifica che _compute_valuation in fascicolo.py continui a funzionare senza gate B2C.
Test regressione obbligatorio.

═══════════════════════════════════════════════════════════════
BACKEND — cosa creare/modificare
═══════════════════════════════════════════════════════════════

1) NUOVO: backend/apps/billing/b2c_entitlements.py
   Funzioni:
   - check_base_valuation_allowed(user_id) -> (bool, reset_at)
   - record_base_valuation(user_id, valuation_id)
   - check_uni_entitlement(user_id, payload_hash) -> bool
   - hash_valuation_payload(payload) -> sha256 str
   Collections MongoDB:
   - b2c_valuation_usage: { user_id, tier, created_at, valuation_id }
   - b2c_purchases: { id, user_id, product_key, stripe_session_id, payload_hash, status, created_at, expires_at }

2) NUOVO: backend/apps/billing/b2c_checkout.py
   POST /api/billing/b2c/checkout
   Body: { product_key: "b2c_valuator_uni_pdf", success_url, cancel_url, payload_hash? }
   Response: { checkout_url }
   - Usa stripe_lookup_key da b2c_products.py
   - Crea Stripe Product+Price se mancanti (lookup key b2c_valuator_uni_pdf, €2.99)
   - Webhook checkout.session.completed → scrivi b2c_purchases status=paid, expires_at=+24h
   - Registra router in billing routes esistenti

3) GET /api/billing/b2c/valuator-status (utile per UI)
   Response: { base_remaining: 0|1, base_reset_at, uni_price_eur: 2.99, has_uni_entitlement, agency_credits_available }

4) MODIFICA: backend/apps/immocloud/valuator.py — POST ""
   Aggiungi get_optional_user dependency.
   Logica gate:
   | Payload | Auth | Azione |
   |---------|------|--------|
   | no commercial_surfaces, no merit | anonimo | 401 |
   | no commercial_surfaces, no merit | B2C email verified | check rate limit → 200 o 429 |
   | no commercial_surfaces, no merit | B2C email NOT verified | 403 |
   | commercial_surfaces o merit | B2C con entitlement UNI | 200 |
   | commercial_surfaces o merit | agente con crediti | debit + 200 |
   | commercial_surfaces o merit | nessun entitlement | 402 { code: payment_required, product_key: b2c_valuator_uni_pdf } |
   | caller=agency_fascicolo | agente | 200 (bypass B2C gate) |

5) MODIFICA: backend/apps/immocloud/valuation_pdf.py — POST /report-pdf
   - Richiede SEMPRE entitlement UNI (pagamento B2C o crediti B2B o caller agency)
   - Payload solo base → 402
   - Branding agenzia invariato

═══════════════════════════════════════════════════════════════
FRONTEND — cosa modificare
═══════════════════════════════════════════════════════════════

1) frontend/.../ValuatorPage.jsx — REFACTOR COMPLETO UX
   RIMUOVI il modello attuale "tutto gratis + checkbox Pro".
   NUOVO layout:
   - Hero con DUE card/tab side-by-side (mobile: stack):
     Card 1: "Stima rapida" — "1 valutazione gratuita ogni 12 mesi"
     Card 2: "UNI 10750 + PDF" — "€2,99 · report professionale"
   - Form base (card 1): location + property — NO Pro toggle, NO PDF button
   - Form UNI (card 2): tutti i campi + sezione Pro (superfici + merito)
   - Risultato base: valore + upsell CTA verso UNI — ZERO bottone PDF
   - Risultato UNI: PDF attivo solo se entitled, altrimenti "Paga €2,99 e scarica"
   - Banner: non loggato → "Accedi o registrati"; base esaurito → data reset
   - Se agente loggato: copy "Usa crediti agenzia" al posto di €2,99
   - Gestisci query params pre-fill: ?tier=base&city=...&property_type=...&surface_sqm=...

2) i18n namespace valuator.* — aggiungi:
   tier_base_title, tier_uni_title, tier_base_limit, tier_uni_price,
   upsell_uni_cta, payment_required, base_limit_reached, login_required
   Rimuovi copy che implica Pro/PDF gratis.

3) PropertyDetailPage.jsx (cloud) — CTA sotto prezzo (speculare al box mutui):
   "Quanto vale questo immobile?"
   [ Stima gratuita ] → /it/cloud/valutatore?tier=base&city=...&property_type=...&surface_sqm=...
   [ Report UNI €2,99 ] → /it/cloud/valutatore?tier=uni&...

4) Home cloud — aggiungi link/card "Valutatore immobiliare"

5) Pagine checkout minime:
   /it/cloud/checkout/success?session_id=...
   /it/cloud/checkout/cancel

═══════════════════════════════════════════════════════════════
COSA NON FARE
═══════════════════════════════════════════════════════════════
❌ NON implementare checkout staging €0,90 o HAL Legal €1,00 (task futuro B2C-CHECKOUT-02)
❌ NON cambiare prezzi/crediti B2B in plans.py
❌ NON cambiare motore UNI / coefficients.py
❌ NON scrivere Cap. 21 manuale (lo fa Cursor dopo merge)
❌ NON lasciare fallback "PDF gratis se Stripe fallisce"
❌ NON lasciare Pro UNI gratis sul portale pubblico

═══════════════════════════════════════════════════════════════
TEST OBBLIGATORI — crea tests/test_b2c_valuator_gates.py
═══════════════════════════════════════════════════════════════
1. Base anonimo → 401
2. Base user verified, 0 usage → 200
3. Base user verified, 1 usage <12mo → 429
4. Base payload con merit → 402
5. UNI user senza pagamento → 402
6. UNI user con purchase valido → 200 + breakdown
7. PDF senza entitlement → 402
8. PDF con entitlement → 200 application/pdf
9. Agente con crediti UNI → 200 + debit 12cr
10. Fascicolo agency base call → 200 (no regressione)

Tutti i test devono passare. Esegui pytest prima di chiudere.

Smoke manuale preview:
- /it/cloud/valutatore → due tier visibili, Pro non gratis
- Stima base loggato → OK → upsell → no PDF
- Seconda base entro 12 mesi → blocco
- UNI → Stripe test mode → PDF scaricabile
- Scheda annuncio → CTA valutatore presente

═══════════════════════════════════════════════════════════════
ORDINE IMPLEMENTAZIONE
═══════════════════════════════════════════════════════════════
Fase 1: b2c_entitlements.py + gate valuator.py + pytest gate
Fase 2: b2c_checkout.py + webhook Stripe + b2c_purchases
Fase 3: gate valuation_pdf.py
Fase 4: refactor ValuatorPage.jsx two-tier UX
Fase 5: CTA PropertyDetailPage + home cloud + checkout pages
Fase 6: pytest tutti verdi + aggiorna PRICING_B2C.md §7 stato implementazione + GAP.md voce valutatore ✅

═══════════════════════════════════════════════════════════════
DEFINITION OF DONE (tutti obbligatori)
═══════════════════════════════════════════════════════════════
[ ] Portale B2C non regala più UNI né PDF
[ ] Base limitato 1×/12 mesi server-side
[ ] Checkout Stripe €2,99 funzionante (test mode OK)
[ ] Upsell post-base in UI
[ ] CTA su PropertyDetailPage
[ ] Pytest 10/10 verdi + no regressione fascicolo
[ ] PRICING_B2C.md §7 aggiornato
[ ] GAP.md voce valutatore chiusa con ✅
[ ] Brief salvato in memory/briefs/

═══════════════════════════════════════════════════════════════
COMMIT MESSAGE
═══════════════════════════════════════════════════════════════
feat(b2c): valuator dual-tier — base 1×/12m free, UNI+PDF €2.99 Stripe

- Gate commercial_surfaces/merit behind B2C payment or agency credits
- Rate limit base valuations server-side (verified email)
- POST /api/billing/b2c/checkout for b2c_valuator_uni_pdf
- ValuatorPage two-tier UX + upsell + property detail CTA
- PDF download requires UNI entitlement

═══════════════════════════════════════════════════════════════
FINE TASK
═══════════════════════════════════════════════════════════════
Implementa tutte le 6 fasi in sequenza.
A fine task: report dettagliato con checklist DoD (✅/❌ per ogni voce), file modificati, pytest output, commit message.

STOP — non procedere ad altri task B2C (staging, HAL Legal) senza "vai" Founder.

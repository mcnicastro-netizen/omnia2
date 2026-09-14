# 💳 OMNIA — Pricing B2C (ImmobilCloud privati)

**Versione**: 1.0
**Ultima revisione**: 6 Agosto 2026 — approvato dal Founder
**Stato**: 🟢 ATTIVO in documentazione · backend stub in `backend/apps/billing/b2c_products.py` · checkout Stripe one-shot = **sprint successivo**
**Sovrascrive**: la sezione ImmobilCloud B2C di `PRICING_OMNIA.md` v2.0 (ripristinata qui)

> 📌 **Rail separato**: questo listino è **solo B2C** su portale `/cloud`.
> Rail = **Stripe one-shot con carta**. Nessun credito, nessun pacchetto minimo €20, nessun abbonamento.
> Per le agenzie (B2B) vedi `PRICING_OMNIA.md` v3.0 (crediti + abbonamenti).

---

## 🎯 Principio guida

1. **B2C paga con carta**, non con crediti (i crediti sono un concetto B2B).
2. **Nessun servizio B2C sotto €0,99** (tranne lead magnet espliciti come Valutatore base gratuito e Comparatore mutui gratuito).
3. **Prezzi retail > prezzi B2B** (l'agenzia deve avere un margine se rivende).
4. **Anti-abuso**: email verificata + rate limit sui lead magnet.
5. **Ricchezza percepita**: annunci privati con logica generosa iniziale (2 gratis, prezzi aggressivi -25/-45% vs Idealista).

---

## 1️⃣ Annunci privati

Ripristinati dalla sezione ImmobilCloud B2C di `PRICING_OMNIA.md` v2.0.

### Pubblicazione

| Servizio | Prezzo B2C | Note |
|---|:-:|------|
| **Primi 2 annunci attivi** | **GRATIS** | Include foto standard, geolocalizzazione, contatto in-portale |
| **Annuncio extra** (dal 3°, 90gg di visibilità) | **€14,90** | -25% vs Idealista |
| **Immobili premium** (>€1M) / **Affitti alti** (>€2.500/mese) | **€19,90** | Tariffa speciale unica |
| **Nascondi indirizzo esatto** | **€5,90** | -40% vs Idealista (€9,90). Add-on per annuncio |
| **Foto extra** (pacchetto 10 foto oltre il base) | **€3,90** | Bundle unico |

### Boost visibilità (Premium / TOP)

| Boost | Durata | Prezzo B2C | vs Idealista | vs Immobiliare.it |
|---|:-:|:-:|:-:|:-:|
| **Premium** | 30 gg | **€19,90** | -33% (€29,90) | -41% (€34 medio) |
| **Premium** | 90 gg | **€49,90** | n/a | -38% (€79 medio) |
| **Premium** | 180 gg | **€89,90** | n/a | -35% (€139 medio) |
| **TOP** | 30 gg | **€29,90** | -19% (€36,90) | -45% (€54 medio) |
| **TOP** | 90 gg | **€79,90** | n/a | -27% (€109 medio) |
| **TOP** | 180 gg | **€149,90** | n/a | -22% (€189 medio) |

**Strategia**: sconto aggressivo 25-45% sotto Idealista in **Fase 1 acquisition**. Da Fase 2 (12+ mesi) allinearsi a -15%.

---

## 2️⃣ Strumenti self-service (portale `/cloud`)

Servizi che un privato può usare senza agenzia, pagando con carta al momento (o gratis se lead magnet).

| Servizio | Prezzo B2C | Limite | Costo vivo | Note |
|----------|:-:|--------|:-:|------|
| **Valutatore base** | **GRATIS** | 1 valutazione per account/email verificato ogni 12 mesi | ~€0,04-0,10 | Lead magnet + upsell UNI. Anti-abuso: email verify + cap |
| **Valutatore UNI 10750 + PDF brandizzato** | **€2,99** carta | per report | ~€0,10-0,15 | Stripe checkout prima del download. Retail > B2B (€0,60) |
| **Comparatore mutui** | **GRATIS** | illimitato | ~€0,01 | Lead → agenzia partner / mediatore |
| **Virtual Staging** | **€0,90 / foto** | max 3 foto per annuncio UGC | ~€0,056 | Stesso € agenzia, rail carta. Anti-abuso: legato all'annuncio |
| **HAL Legal — 1 domanda** | **€1,00 / query** | per query | ~€0,04 | Portale B2C. Disclaimer obbligatorio prima della risposta |
| 🔒 **Visura catastale** | **in arrivo** | — | ~€0,40 | Checkout NON implementato. Sezione placeholder — fase 2 |
| 🔒 **Planimetria catastale** | **in arrivo** | — | ~€6,90 | Checkout NON implementato. Margine da validare fase 2 |

**Regola operativa**
- **Nessun micro-servizio B2C sotto €0,99** (tranne i due lead magnet Valutatore base e Comparatore mutui).
- **Ogni pagamento** è **carta one-shot Stripe**, mai crediti.
- **Disclaimer HAL Legal** obbligatorio ad ogni query (informazione generale, non consulenza legale).

---

## 3️⃣ Esclusi dal B2C (dominio B2B esclusivo)

Non offriamo mai a privati:
- ❌ Crediti / pacchetti ricarica
- ❌ Widget & API mensili
- ❌ Multiposting sui portali nazionali
- ❌ CRM, matching engine, Match
- ❌ MLS network
- ❌ Abbonamenti mensili
- ❌ Portal Wizard custom

Questi restano su `PRICING_OMNIA.md` v3.0 come **funzioni riservate alle agenzie**.

---

## 4️⃣ Margini indicativi (documentazione interna)

**Stripe fees standard**: ~1,4% + €0,25 per transazione europea con carta.
Rende alcuni micro-prezzi meno favorevoli di quanto sembri — motivo della regola *"mai sotto €0,99"*.

### Valutatore UNI 10750 + PDF (€2,99)
| Voce | Valore |
|------|:-:|
| Prezzo lordo | €2,99 |
| Stripe fees | ~€0,29 (1,4% + €0,25) |
| Costo vivo (AI + storage PDF) | ~€0,15 |
| **Margine netto** | **~€2,55** (~85%) |

### HAL Legal — 1 query (€1,00)
| Voce | Valore |
|------|:-:|
| Prezzo lordo | €1,00 |
| Stripe fees | ~€0,26 |
| Costo vivo (Emergent LLM + retrieval) | ~€0,04 |
| **Margine netto** | **~€0,70** (70%) |

### Virtual Staging (€0,90/foto)
| Voce | Valore |
|------|:-:|
| Prezzo lordo | €0,90 |
| Stripe fees | ~€0,26 |
| Costo vivo (pipeline 3-stage) | ~€0,06 |
| **Margine netto** | **~€0,58** (65%) |

> ⚠️ **Attenzione margini bassi**: Virtual Staging al retail è **borderline**. Vale come lead-in per il servizio "annuncio con render professionali" — non come profitto puro.

---

## 5️⃣ Allineamento B2B vs B2C — stesso motore, rail diverso

Molti servizi esistono **sia lato agenzia (a crediti)** sia **lato privato (a carta)**. Ecco il confronto:

| Servizio | Agenzia (crediti · €0,05) | Privato (carta) | Delta retail |
|----------|:-:|:-:|:-:|
| Valutatore base | €0,30 (6 crediti) | GRATIS (1×/12 mesi) | Lead magnet |
| Valutatore UNI + PDF | €0,60 (12 crediti) | **€2,99** | +€2,39 (~5× B2B) |
| Virtual Staging | €0,90 (18 crediti) | €0,90 | pari (retail = B2B) |
| HAL Legal query | €0,60 (12 crediti) | **€1,00** | +€0,40 (~66% B2B) |

**Perché queste differenze**:
- **UNI + PDF (5×)**: retail deve giustificare margine buono, l'agenzia è un rivenditore.
- **Staging (pari)**: costo vivo è quasi tutto in AI, difficile differenziare. Vale come funnel verso l'agenzia locale.
- **HAL Legal (+66%)**: costo AI simile, l'agenzia paga meno perché usa in volume.

---

## 6️⃣ Anti-abuso — regole di piattaforma

| Servizio | Meccanismo anti-abuso |
|----------|-----------------------|
| Valutatore base gratis | Email verificata + 1 valutazione ogni 12 mesi per account (limite lato server) |
| Comparatore mutui | Nessun limite (input finti non consumano risorse LLM significative) |
| Virtual Staging €0,90 | Rate limit implicito: max 3 foto per annuncio UGC del cliente |
| HAL Legal €1,00 | Rate limit 20 query/ora per IP (protezione crawler) |
| Annunci privati | Moderazione manuale super_admin (Cap. 25 manuale) |

---

## 7️⃣ Stato implementazione (backend + frontend)

| Componente | Stato | Sprint |
|-----------|:-:|:-:|
| Prodotti B2C definiti in `b2c_products.py` | ✅ (stub 6-Ago-2026) | Attuale |
| Stripe Product+Price creati per `b2c_valuator_uni_pdf` (lookup key + lazy-create) | ✅ (16-Ago-2026 · B2C-VAL-01) | Attuale |
| Endpoint `POST /api/billing/b2c/checkout` (Stripe one-shot) | ✅ (16-Ago-2026) | Attuale |
| Endpoint `GET /api/billing/b2c/valuator-status` (UI status) | ✅ (16-Ago-2026) | Attuale |
| Endpoint `GET /api/billing/b2c/status/{session_id}` (polling) | ✅ (16-Ago-2026) | Attuale |
| Webhook `checkout.session.completed` → `apply_b2c_purchase_side_effects` | ✅ (16-Ago-2026) | Attuale |
| Rate limit lato server per lead magnet Valutatore base (1×/12mo su `b2c_valuation_usage`) | ✅ (16-Ago-2026) | Attuale |
| Gate `commercial_surfaces`/`merit` in `POST /api/cloud/valuator` (402 payment_required) | ✅ (16-Ago-2026) | Attuale |
| Gate PDF `POST /api/cloud/valuator/report-pdf` (402 senza entitlement UNI) | ✅ (16-Ago-2026) | Attuale |
| Bypass fascicolo agenzia (`_estimate_value_core` diretto, no HTTP gate) | ✅ (16-Ago-2026) | Attuale |
| Pagina `/it/cloud/checkout/success` + `/cancel` | ✅ (16-Ago-2026) | Attuale |
| UI dual-tier `ValuatorPage.jsx` (BASE gratis + UNI €2,99, upsell, no PDF su base) | ✅ (16-Ago-2026) | Attuale |
| CTA Valutatore su `PropertyDetailPage.jsx` (base + UNI) | ✅ (16-Ago-2026) | Attuale |
| ActionCard "Valutatore immobiliare" su `CloudHomePage.jsx` | ✅ (16-Ago-2026) | Attuale |
| Pytest `test_b2c_valuator_gates.py` (10/10 verdi) | ✅ (16-Ago-2026) | Attuale |
| Checkout staging €0,90 (B2C-CHECKOUT-02) | ❌ | Prossimo |
| Checkout HAL Legal €1,00 (B2C-CHECKOUT-02) | ❌ | Prossimo |
| Cap. 21 manuale HAL YAML | ❌ (post-merge · Cursor) | Prossimo |

**Task B2C-VAL-01 chiuso il 16-Ago-2026**: dual-tier valuator con gate €2,99 Stripe, rate limit 1×/12mo, paywall PDF, refactor UX, CTA su scheda annuncio, pytest 10/10.

---

## 🗓️ Storico versioni

| Data | Versione | Note |
|------|:-:|------|
| 06-Ago-2026 | **v1.0** | Prima stesura ufficiale. Numeri annunci privati ripristinati da PRICING_OMNIA v2.0. Tabella strumenti self-service con margini validati. Stub backend in `b2c_products.py`. |
| 16-Ago-2026 | **v1.1** | Task B2C-VAL-01 completato. §7 aggiornato: gate valutatore dual-tier + Stripe checkout €2,99 + paywall PDF + rate limit 1×/12mo + refactor UX + CTA scheda annuncio + pytest 10/10. |

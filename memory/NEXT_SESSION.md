# Prossima sessione — Calendario Founder

**Data nota**: 14 Settembre 2026  
**Stato sessione odierna**: ✅ chiusa (Tavily, Stripe, listino D-079/D-080)

---

## 📅 In calendario — prossimo lavoro

### 1. CTA «Richiedi demo» → Calendly (o equivalente)
- **Cosa**: sostituire/affiancare «Attiva» (checkout diretto) con **Richiedi demo guidata** che apre un link calendario.
- **Perché**: D-080 — demo prima, abbonamento dopo; evita sorprese e filtra lead.
- **Dove**: `BillingPage.jsx` (+ eventuale landing agenzie).
- **Serve da Marco**: URL Calendly (o Google Calendar appointment) da mettere in `REACT_APP_DEMO_CALENDAR_URL` / `backend/.env`.
- **Stima tecnica**: piccolo (link + copy); nessun pagamento in quel passo.

### 2. (Opzionale stesso giro)
- Form «lascia email» se non vogliono prenotare subito.
- Conferma post-demo → sblocca checkout Stripe.

---

## Già fatto oggi (non riprendere)

- Tavily + Stripe test operativi; webhook su tunnel
- Annuale −1 mese (D-079)
- Agency €299, no Enterprise, no trial self-serve (D-080)
- Gemini fallback stabilizzato; Legal con fonti whitelist

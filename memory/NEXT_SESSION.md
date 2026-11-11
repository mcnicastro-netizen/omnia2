# Prossima sessione — programma passi

**Aggiornato**: 11 Novembre 2026 (~17:30 CET — Europe/Rome)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  

---

## Domani (priorità Founder) — contatori automatici, zero controllo a mano

1. **Abbonamenti — scadenze**
   - Contatore / data `current_period_end` in **Cabina Ops** (lista tenant + scheda).
   - Stessa data in **Piano & Crediti** lato cliente.
   - Cron + email promemoria (es. 30 / 7 / 1 giorno prima del rinnovo) al titolare; alert Ops se `past_due` / in scadenza.
2. **Crediti pacchetto**
   - Un solo saldo chiaro (`credit_wallets`) in Cabina per agenzia + soglia «crediti bassi».
   - Contatore cliente già in Billing: allineare etichette Ops (no confusione con crediti Kling/`agencies.credits_balance`).
   - Alert automatico low-credits (titolare + Ops), niente check manuale.
3. **Decisione da fissare in DECISIONS** (D-16x): soglie giorni/crediti + template Resend.

## Oggi chiuso (riferimento)

- D-163/164 auto-KYC + reconcile Stripe
- Toggle mensile/annuale waiting
- Fix aggancio email attivazione → login gestionale (`enter_url`)

## SoT

| Voce | Doc |
|------|-----|
| Login | **D-161** |
| Auto-KYC | **D-163** |
| Stripe period | **D-164** |
| Fattura | **A-038** aperta |

Vault: [`CLOUD_SECRETS_INVENTORY.md`](./CLOUD_SECRETS_INVENTORY.md).

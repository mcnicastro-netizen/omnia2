# Prossima sessione — programma passi

**Aggiornato**: 12 Novembre 2026 (~09:10 CET — Europe/Rome)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  

---

## In corso / appena shippato — D-166 contatori

- Cabina + Piano & Crediti: scadenze + crediti pacchetto
- Cron 07:15 UTC + template Resend + alert Ops
- Trigger manuale: `POST /app/cron/billing/reminders`

## Dopo merge

1. Smoke Cabina lista clienti (giorni abb. + cr pacchetto) e Billing Nicastro.
2. Opzionale: trigger cron reminders a mano una volta.
3. **A-038** solo con «vai».

## SoT

| Voce | Doc |
|------|-----|
| Contatori | **D-166** |
| Login | **D-161** |
| Auto-KYC | **D-163** |
| Stripe period | **D-164** |
| Enter email | **D-165** |
| Fattura | **A-038** aperta |

Vault: [`CLOUD_SECRETS_INVENTORY.md`](./CLOUD_SECRETS_INVENTORY.md).

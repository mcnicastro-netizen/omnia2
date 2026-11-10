# Audit Super Admin / Area Founder — 10-Nov-2026

## Verdetto
L’ambiente attuale **non** è una console Super Admin funzionale. È un **cruscotto costi + coda attivazione** (D-077 / D-152) montato dentro lo shell agenzia. I “tools” dell’admin agenzia in sidebar non hanno logica di piattaforma: sono CRM di un tenant (o residui dogfood).

## Cosa c’è oggi (`/app/ops`)
| Blocco | Ruolo reale |
|--------|-------------|
| Coda attivazione + Attiva | Gate onboarding (utile, da tenere) |
| Overview costi / incassi / margini | Telemetria P&L (utile, da tenere come *un* modulo) |
| Backup health + alert | Ops infrastruttura (utile) |
| Link Moderazione / Ops Legal | Pezzi sparsi, non un hub |
| Shell menu CRM (clienti, immobili, …) | **Fuori posto** per Super Admin: logica tenant, non piattaforma |

## Cosa manca (richiesta Founder)
1. **Archivio clienti** (tutte le agenzie / B2C) + dati collegati  
2. **Archivio fornitori** (fal, Resend, Stripe, Gemini, portali, legali, …) + contratti/stato  
3. **API clienti** (chiavi Track B): elenco, blocco, rotazione/rigenerazione, audit  
4. **API fornitori servizi**: chiavi/circuiti attivi, health, spend, kill-switch  
5. **Listino prezzi** editabile (B2B/B2C) con audit modifiche — oggi SoT è markdown/`plans.py`, non UI  
6. E oltre: tenant lifecycle, fatturazione assistita, GDPR erase, domain vault overview, …

## Ripensamento proposto (IA)
Console **separata** dallo shell agenzia (home Super Admin ≠ CRM):

1. **Ingresso** — coda attivazione, alert critici, health  
2. **Clienti** — agenzie + B2C; scheda con dati, piano, API keys, crediti  
3. **Fornitori** — registry provider + circuit breaker + costi  
4. **API & integrazioni** — client keys + provider keys (mai valori in chiaro)  
5. **Listino & billing** — piani, SKU one-shot, grant assistiti  
6. **Contenuti & rischio** — moderazione UGC, Ops Legal  
7. **Piattaforma** — backup, blank-slate/script, deploy notes  

Niente menu «Clienti / Immobili / Staging» da agency_admin sulla home Super Admin, salvo *impersonation* esplicita «apri come agenzia X».

## Prossimo passo
Non deploy di un redesign a caso. Decidere con Founder priorità moduli 1→5, poi PR dedicata (fuori dal pack Accedi/PEC #155).

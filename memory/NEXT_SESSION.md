# Prossima sessione — programma passi

**Aggiornato**: 17 Novembre 2026 (~16:50 CET — Europe/Rome)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  

---

## Dove siamo

| Item | Stato |
|------|-------|
| Verifica statica Blocchi 0–7 | CHIUSA |
| B01 / B02 / B03 design | CHIUSI |
| Slice 1 codice | **MERGIATA** — PR [#208](https://github.com/mcnicastro-netizen/omnia2/pull/208) |
| B04 design | **CHIUSO** — SoT `_export_audits/B04-ANO-008-DESIGN-BILLING.md` (DES-01…10) |
| B04-I (Stripe Customer / stati / catalogo) | **MERGIATA** — PR [#210](https://github.com/mcnicastro-netizen/omnia2/pull/210) |
| B04-II (wallet / lotti / FIFO / ledger) | **MERGIATA** — PR [#211](https://github.com/mcnicastro-netizen/omnia2/pull/211) |
| B04-H1/H2 (revoke isolation + authz wallet) | **MERGIATA** — PR [#212](https://github.com/mcnicastro-netizen/omnia2/pull/212) + CI Actions |
| B04-H3 / H4 / migrazione legacy R-04 | NON AUTORIZZATI |
| B04-III…VII | NON AUTORIZZATI |
| B05–B07 / MLS / deploy prod | ESCLUSI |

## CI

Workflow `.github/workflows/ci.yml` attivo su `main` (suite billing/B04 unit).  
Post-merge #212: run su `main` **success**.

## Residui aperti (non bloccanti merge H1/H2)

- Gap modellistico: non esiste ruolo DB `main_admin`; `agency_admin` esatto su filiale del CC può ancora amministrare quel wallet.
- H3 (allocate solo org linkate al CC), H4 (top-up/storage con Customer Stripe del CC), censimento/migrazione legacy.

## Follow-up design

> `_export_audits/B04-OPEN-FOLLOWUPS.md` — **B04-OPEN-01** repricing (sessione dedicata).

## Prossimo passo operativo

Attendere autorizzazione Founder esplicita per il prossimo pacchetto (es. H3+H4, oppure B04-III).  
Niente slice nuova senza mandato.

SoT: `_export_audits/B04-ANO-008-DESIGN-BILLING.md` · `B04-DES-REGISTRO.md` · `B04-H1-H2-IMPLEMENTATION-REPORT.md` · D-173 · D-174

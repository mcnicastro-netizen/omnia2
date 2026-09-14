# Capitolo 27 · MLS Network

> Collaborazioni multi-agenzia. **Non più placeholder**: v1 attiva con seed demo (anche a zero clienti reali).

## 27.1 · Dove
- CRM: `/app/mls` (Il mio MLS · locale · Italia · partner · offerte).
- Pubblico: dual-box ImmobilCloud + `GET /api/app/mls/search/public`.
- Join: `POST /api/app/mls/join`.

## 27.2 · Visibilità immobili
- Condivisi in network se `visibility` = `public` o `mls_only`.
- `private` esclusi dalle offerte MLS.

## 27.3 · Partner e offerte
- Inviti partner, accept/reject.
- Offerte su immobile condiviso verso altra agenzia MLS.

## 27.4 · Seed / scala
- `POST /api/app/mls/seed` (super_admin) ladder 10/50/500/1000…
- Indici Mongo su partners/requests/properties pensati per ≥10k agenzie.

## 27.5 · Limitazioni v1
- No Academy.
- Contatori demo da seed finché non ci sono clienti reali.
- Grafica OMNIA (struttura ispirata Agesta, non clone).

## 27.6 · Collegamenti
Cap. 3 Immobili · Cap. 25 Privacy · Cap. 5 Match.

**Versione capitolo**: v1.0 (2026-09-14 · Cursor M3).

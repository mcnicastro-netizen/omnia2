# Prossima sessione — programma passi

**Aggiornato**: 17 Novembre 2026 (~20:20 CET — Europe/Rome)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**SoT chiusura master**: `_export_audits/MASTER-CHIUSURA-POST-AUDIT-PIANO.md`

---

## Dove siamo

| Item | Stato |
|------|-------|
| Verifica statica Blocchi 0–7 | CHIUSA (strato A) |
| B01 / B02 / B03 design | CHIUSI (strato A) |
| Slice 1 codice | **MERGIATA** — PR [#208](https://github.com/mcnicastro-netizen/omnia2/pull/208) |
| B04 design | **CHIUSO** — DES-01…10 |
| B04-I | **MERGIATA** — PR [#210](https://github.com/mcnicastro-netizen/omnia2/pull/210) |
| B04-II | **MERGIATA** — PR [#211](https://github.com/mcnicastro-netizen/omnia2/pull/211) |
| B04-H1 (revoke CC isolation) | **MERGIATA** — PR [#212](https://github.com/mcnicastro-netizen/omnia2/pull/212) |
| B04-H2 Main Admin residuale (D01–D12 + fix) | **MERGIATA** — PR [#216](https://github.com/mcnicastro-netizen/omnia2/pull/216) @ `c3baebc` (include `99a967e`) |
| CI post-merge #216 su `main` | **SUCCESS** |
| B04-H3 / H4 / legacy / B04-III…VII | **NON AUTORIZZATI** — `FASE_SUCCESSIVA` |
| B05–B07 / MLS / Stripe live / prod | **FUORI_MASTER** chiusura attuale |

## Strati di chiusura

| Strato | Significato | Stato |
|--------|-------------|-------|
| A — Audit + design | Decisioni e audit con stato finale | Chiudibile (conferma Founder) |
| B — Impl autorizzata | Slice1 + B04-I/II + H1 + H2 su `main` | Chiudibile dopo accettazione residui + report finale |
| C — Readiness commerciale | III…VII, impl B01–B03, migrazione, prod | Aperto · fuori perimetro |

Dettaglio inventario: `MASTER-CHIUSURA-POST-AUDIT-PIANO.md` (MC-001…).

## Residui H2 (accettazione Founder richiesta per chiudere strato B)

- MC-040 UI Cabina accept (API ok, FE fuori)
- MC-041 expiry lazy
- MC-042 read «limitata» su CC non operativo (whitelist non definita)
- MC-043 CC senza Main Admin → deny finché Ops nomina (intenzionale)

## Follow-up design (non codice)

> `_export_audits/B04-OPEN-FOLLOWUPS.md` — **B04-OPEN-01** repricing

## Prossimo passo operativo

1. Founder conferma piano chiusura + accetta residui MC-040…043 (o decide MC-042).  
2. Dichiarazione `MASTER STRATO B CHIUSO` **oppure** elenco MC ancora aperti.  
3. Solo dopo: autorizzazione esplicita al **prossimo** pacchetto (H3+H4 **oppure** B04-III).  

Niente slice nuova senza mandato.  
`OMNIA-HANDOFF-PER-CHATGPT.md` (14 nov) è **STALE**.

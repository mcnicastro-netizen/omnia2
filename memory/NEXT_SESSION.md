# Prossima sessione — programma passi

**Aggiornato**: 18 Novembre 2026 (~13:05 CET — Europe/Rome)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Baseline codice verificata**: `main` @ `6a1293238329f2095455fe8fde4639e9a249c7cf` (merge PR #220)  
**SoT chiusura**: `_export_audits/MASTER-CHIUSURA-POST-AUDIT-PIANO.md`  
**SoT verifica post-merge**: `_export_audits/VERIFICA-POST-MERGE-217-220-2026-11-18.md`

---

## Dove siamo

| Item | Stato |
|------|-------|
| PR #217 docs firme / allineamento | **MERGED** · `684eb8a` |
| PR #218 MC-042 wallet deny / fail-open | **MERGED** · `547f67f` |
| PR #219 MC-040 / 041 / 043 | **MERGED** · `4946390` |
| PR #220 MC-042 v2 + MC-054 B + MC-055…059 | **MERGED** · `6a12932` (= HEAD) |
| CI tip `main` | **verde** (Backend billing / B04 unit) |
| MC-026b | **FIRMATA** `CONFORME CON RISERVE` |
| `MASTER STRATO B CHIUSO` | **FATTO** 18/11 |
| Riserve B (042 v2 / 054 / 055…059) | **Codice su main** — vedi verifica; gap MC-055 saldo pieno ancora aperto |

## Strati

| Strato | Stato |
|--------|-------|
| A — Audit + design | **Chiuso** |
| B — Impl autorizzata master | **Dichiarato chiuso** + riserve implementate su main |
| C — Readiness commerciale | **Non aperto** — mandato separato |

## Prossimo (attende Founder)

1. Commit/push allineamento documentale (se autorizzato).  
2. Decisione su gap **MC-055** (`invoice.paid` senza check debito residuo).  
3. Scelta primo slice Strato C (raccomandazione verifica: fix MC-055 **oppure** H3 MC-045).  
4. **Non** Stripe live / prod senza mandato dedicato.

## Non fare

- Riaprire D01–D12.  
- Confondere cessazione (MC-042) e sospensione (MC-054).  
- Usare handoff 14 nov come SoT.  
- Dichiarare OMNIA pronto produzione.

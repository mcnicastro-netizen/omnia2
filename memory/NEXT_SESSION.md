# Prossima sessione — programma passi

**Aggiornato**: 9 Ottobre 2026 · Onda **J GREEN** · fascicolo D-118 · P-046…P-058 aperti  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Branch audit**: `cursor/portale-audit-onda-d-live-4532` (PR #12)

---

## 🎯 Prossimo passo — coda «vai» (programma analisi chiuso)

**Fascicolo**: [`OMNIA_PORTALE_AUDIT_FASCICOLO.md`](../docs/audit/OMNIA_PORTALE_AUDIT_FASCICOLO.md)

### Fix prioritari (consigliati)
| ID | Sev | Note |
|--|--|--|
| **P-051** | P1 | `COOKIE_SECURE=true` su tunnel HTTPS → CSRF on |
| **P-049** | P1 | B2C status → Stripe retrieve fallback |
| **P-046** | P1 | Backup include `b2c_*` + consent/favorites |
| P-050 | P2 | Rate limit register + Visura |
| P-047/048 | P2 | Restore docs · soft-delete UGC |
| P-033 | P2 | Search L3/L4 (dopo) |
| P-054/055/057 | P2 | i18n · SEO scheda · UGC notify |
| P-052/053/056/058 | P3 | API-down · alert dedup · noindex · runbook |

Comando tipico: `vai P-051 P-049 P-046`

---

## ✅ Stato

| Onda | Esito |
|--|--|
| **A–J** | ✅ GREEN (analisi) |
| **D-118** | ✅ fascicolo pronto |

**PR draft**: https://github.com/mcnicastro-netizen/omnia2/pull/12  
**Matrice J**: `docs/audit/portale-matrici/2026-10-09-onda-j.md`

# S4 — Una regola di visibilità pubblica (portale / brand)

**Data:** 10 Ottobre 2026  
**Stato:** ✅ spec + codice · LIVE sotto  
**Chiude:** C4 · P-034 (ex WONTFIX)  
**SoT codice:** `backend/shared/db/public_visibility.py`

---

## Problema

Stesso immobile poteva essere:

- **visibile** su sito brand `/api/p/{slug}` (solo `status=active`)
- **nascosto** su ImmobilCloud (manca `visibility=public`, moderazione pending, ecc.)

Pitch “gestionale + portale” debole.

---

## Contratto unico

### Superficie pubblica condivisa (`public_surface_base`)

| Campo | Valore |
|-------|--------|
| `status` | `active` |
| `visibility` | `public` |
| `moderation_status` | ∉ `{pending, rejected}` |
| trash | `with_not_trashed` |

### Delta intenzionali (non bug)

| Delta | Portale | Brand `/p/{slug}` |
|-------|---------|-------------------|
| `is_listed_on_immobilcloud` | deve essere ≠ `false` | **non** richiesto (opt-out portale ≠ nascosto sul proprio sito) |
| `privacy_level` L3/L4 | **esclusi** dal feed/detail anon | **ammessi** (sito agenzia) |
| `agency_id` | tutti i tenant | solo agency dello slug |

---

## Superfici codice

| Superficie | Filtro |
|------------|--------|
| ImmobilCloud search/detail/… | `portal_listing_filter()` via `_base_filter()` |
| Brand index / detail / sitemap | `brand_site_filter(agency_id)` |
| Theme preview | `brand_site_filter(agency_id)` |

---

## Verifica

- Unit: `backend/tests/test_s4_public_visibility.py`
- LIVE: artefatto `docs/ops/runs/s4-visibilita-pubblica-live.log`

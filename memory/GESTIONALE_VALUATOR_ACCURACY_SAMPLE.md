# Valutatore — mini-sample accuratezza

**Run**: 2026-09-18T10:02:49.880306+00:00 → 2026-09-18T10:02:50.482529+00:00 (`7a54c63c`)
**Profilo**: {'zone': 'semicentro', 'property_type': 'appartamento', 'surface_sqm': 80, 'condition': 'buono'}
**Tolleranza banda**: ±12%
**Counts**: {'PASS': 20, 'FAIL': 0, 'SKIP': 0}

## Cosa valida (e cosa no)

- Sì: campione rappresentativo (grandi città curate + comuni piccoli con fallback provincia).
- Sì: €/m² medio dentro banda attesa (snapshot 2025-Q1 roll-forward FOI+trend / provincia×0.88).
- Sì: ordinamento relativo Milano/Firenze/Bologna vs Catania/Palermo/Bari.
- No: non è una prova sulle ~27.000 zone OMI ufficiali.

## Risultati città

| Città | Layer | €/m² avg | Banda attesa | Status | Note |
|-------|-------|---------:|--------------|:------:|------|
| Milano | city | 6846 | 5793–7899 | **PASS** | — |
| Roma | city | 4952 | 4170–5734 | **PASS** | — |
| Napoli | city | 2708 | 2207–3210 | **PASS** | — |
| Torino | city | 2316 | 1913–2719 | **PASS** | — |
| Bologna | city | 4026 | 3346–4705 | **PASS** | — |
| Firenze | city | 4310 | 3635–4985 | **PASS** | — |
| Catania | city | 1372 | 1136–1609 | **PASS** | — |
| Palermo | city | 1420 | 1136–1704 | **PASS** | — |
| Bari | city | 2128 | 1782–2474 | **PASS** | — |
| Genova | city | 2200 | 1842–2558 | **PASS** | — |
| Venezia | city | 4368 | 3597–5139 | **PASS** | — |
| Cagliari | city | 2002 | 1660–2344 | **PASS** | — |
| Saronno | province | 1854 | 1576–2132 | **PASS** | — |
| Belpasso | province | 1374 | 1166–1583 | **PASS** | — |
| Carpi | province | 1841 | 1564–2116 | **PASS** | — |
| Sulmona | province | 1120 | 948–1292 | **PASS** | — |

## Ordinamenti relativi

| Check | Status | Detail |
|-------|:------:|--------|
| `Milano>Catania` | **PASS** | 6846 vs 1372 |
| `Milano>Bari` | **PASS** | 6846 vs 2128 |
| `Firenze>Palermo` | **PASS** | 4310 vs 1420 |
| `Bologna>Catania` | **PASS** | 4026 vs 1372 |

JSON: `/workspace/memory/reports/valuator_accuracy_sample_latest.json`

# Valutatore — mini-sample accuratezza

**Run**: 2026-09-18T09:38:56.319382+00:00 → 2026-09-18T09:38:58.080491+00:00 (`9b4c33b7`)
**Profilo**: {'zone': 'semicentro', 'property_type': 'appartamento', 'surface_sqm': 80, 'condition': 'buono'}
**Tolleranza banda**: ±12%
**Counts**: {'PASS': 20, 'FAIL': 0, 'SKIP': 0}

## Cosa valida (e cosa no)

- Sì: campione rappresentativo (grandi città curate + comuni piccoli con fallback provincia).
- Sì: €/m² medio dentro banda attesa (dataset curato / provincia×0.88).
- Sì: ordinamento relativo Milano/Firenze/Bologna vs Catania/Palermo/Bari.
- No: non è una prova sulle ~27.000 zone OMI ufficiali.

## Risultati città

| Città | Layer | €/m² avg | Banda attesa | Status | Note |
|-------|-------|---------:|--------------|:------:|------|
| Milano | city | 6582 | 5500–7500 | **PASS** | — |
| Roma | city | 4792 | 4000–5500 | **PASS** | — |
| Napoli | city | 2635 | 2200–3200 | **PASS** | — |
| Torino | city | 2264 | 1900–2700 | **PASS** | — |
| Bologna | city | 3888 | 3200–4500 | **PASS** | — |
| Firenze | city | 4154 | 3500–4800 | **PASS** | — |
| Catania | city | 1360 | 1200–1700 | **PASS** | — |
| Palermo | city | 1406 | 1200–1800 | **PASS** | — |
| Bari | city | 2074 | 1800–2500 | **PASS** | — |
| Genova | city | 2142 | 1800–2500 | **PASS** | — |
| Venezia | city | 4240 | 3500–5000 | **PASS** | — |
| Cagliari | city | 1956 | 1700–2400 | **PASS** | — |
| Saronno | province | 1782 | 1496–2024 | **PASS** | — |
| Belpasso | province | 1362 | 1232–1672 | **PASS** | — |
| Carpi | province | 1778 | 1496–2024 | **PASS** | — |
| Sulmona | province | 1100 | 968–1320 | **PASS** | — |

## Ordinamenti relativi

| Check | Status | Detail |
|-------|:------:|--------|
| `Milano>Catania` | **PASS** | 6582 vs 1360 |
| `Milano>Bari` | **PASS** | 6582 vs 2074 |
| `Firenze>Palermo` | **PASS** | 4154 vs 1406 |
| `Bologna>Catania` | **PASS** | 3888 vs 1360 |

JSON: `/workspace/memory/reports/valuator_accuracy_sample_latest.json`

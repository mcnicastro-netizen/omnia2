# Platform stress report — suite completa

**Data**: 16-Sep-2026  
**Run**: `8a83a360` · `memory/reports/platform_stress_latest.json`  
**Script**: `backend/scripts/stress_platform_full.py`

## Ambito

| Area | Cosa |
|------|------|
| CRM gestionale | clients, smart, properties, KPI, analytics overview |
| Portale ImmobilCloud | search, facets, map, advanced, MLS public, valuator, mutui |
| Concorrenza | fan-out portal + CRM + smart |
| Sicurezza | unauth walls, brute-force login, rate-limit endpoint vivo |
| Pagamenti | billing plans / visura catalog / mutui config + flag Stripe |
| API keys | `/api/v1/health` + list keys admin |
| Database | estimated counts + indici smoke |

Seed portale: **2.000** annunci pubblici stress (`_stress=platform_stress_v1`).

## Risultati chiave (run `8a83a360`)

| Metrica | Valore |
|---------|-------:|
| Portal search (1 req) | **~17 ms** |
| Portal search conc. p95 | **~162 ms** |
| Clients smart (1 req) | **~408 ms** |
| Clients smart conc. p95 | **~114 ms** |
| Security checks | **ok** |

## Gap chiusi nello stesso giro

1. Ricerca avanzata FE (multi-città / near-me)  
2. MLS box home → search (`mls=1`)  
3. Saved-search frequency bugfix + APScheduler orario (A-019/A-020)  
4. Preferiti B2C  
5. Micro-tour su scheda portale  
6. Privacy L1–L4 UI scheda immobile  
7. Analytics A/B dashboard CRM  
8. Rate limit IP portale + per API key (anti-scraping)

## Ripeti

```bash
cd backend && source .venv/bin/activate
python scripts/stress_platform_full.py --seed-portal 2000
python scripts/stress_platform_full.py --cleanup
```

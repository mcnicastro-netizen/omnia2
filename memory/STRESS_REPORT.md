# Stress report — scala clienti CRM fino a 10.000

**Data**: 16-Sep-2026  
**Run**: `c1ea364f` · agenzia `demo-agency-001`  
**Script**: `backend/scripts/stress_scale_ladder.py` (D-072)  
**JSON**: `memory/reports/stress_clients_latest.json`  
**Ambiente**: API locale `:43121` + Mongo locale

## Cosa abbiamo testato

Ladder **10 → 50 → 500 → 1.000 → 5.000 → 10.000** clienti CRM sintetici (`_stress=stress_ladder_v1`) + fino a 200 immobili stress.

Hot path HTTP (auth cookie Founder):
- `GET /app/clients` (paginato)
- `GET /app/clients/smart`
- `GET /app/dashboard/kpis`
- `GET /app/properties`
- fan-out concorrente 20 worker × 40 GET (10 per smart)

Non incluso in questo giro (già coperto altrove / da fare dopo):
- 10k **agenzie** tenant (script MLS `load_ladder_mls.py` — DB già ~502 agenzie MLS)
- write storm massiva (POST create), match engine full, HAL, Stripe, upload foto

## Risultati chiave (latenza)

| Clienti | Seed | GET /clients (1 req) | GET /clients/smart (1 req) | KPI | Conc. /clients p95 | Conc. /smart p95 |
|--------:|-----:|---------------------:|---------------------------:|----:|-------------------:|-----------------:|
| 10 | 16 ms | ~48 ms ✅ | ~48 ms ✅ | ~52 ms | ~49 ms | ~39 ms |
| 50 | 2 ms | ~48 ms ✅ | ~52 ms ✅ | ~48 ms | ~56 ms | ~77 ms |
| 500 | 20 ms | ~48 ms ✅ | ~56 ms ✅ | ~48 ms | ~51 ms | **~536 ms** |
| 1.000 | 20 ms | ~48 ms ✅ | **~107 ms** | ~48 ms | ~55 ms | **~1,1 s** |
| 5.000 | 79 ms | ~48 ms ✅ | **~853 ms** | ~48 ms | ~58 ms | **~8,0 s** |
| **10.000** | **186 ms** | **~52 ms ✅** | **~1,6 s** | **~52 ms** | **~62 ms** | **~17 s** |

Errori HTTP sulle path sane: **0** (dopo fix seed: status/`email` validi).

## Verdetto

1. **Lista clienti paginata scala bene** fino a 10k: ~50 ms, indipendente dal totale (indici + `page_size`).
2. **Dashboard KPI** stabile ~50 ms anche a 10k.
3. **Immobili list** stabile sotto carico concorrente.
4. **Bottleneck critico: `/app/clients/smart`** — cresce quasi linearmente col numero clienti (a 10k: ~1,6 s singola, ~17 s p95 sotto concorrenza; payload ~1,3 MB). Probabile full-scan / scoring su tutto il set invece di page-first.
5. Seed 10k clienti: **&lt;0,2 s** (bulk Mongo) — OK.

## Bug / gap trovati durante lo stress

| Issue | Impatto |
|-------|---------|
| Seed con `status=active` + email `.test` → **500** su `GET /clients` (validazione Pydantic) | Script corretto; dati reali devono rispettare enum/email |
| `GET /app/agencies/me` usa `agency_ids[0]`, non `active_agency_id` | Switch agenzia inconsistente vs KPI/list |
| `/clients/smart` non scala | UX Smart Clients inutilizzabile oltre ~1–2k senza ottimizzazione |

## Come ripetere

```bash
bash scripts/omnia-stack.sh ensure
cd backend && source .venv/bin/activate
python scripts/stress_scale_ladder.py --all          # ladder completa
python scripts/stress_scale_ladder.py --tier 1000    # singolo step
python scripts/stress_scale_ladder.py --cleanup-only # rimuove docs _stress
# Agenzie MLS (tenant ladder):
python scripts/load_ladder_mls.py --tier 1000
```

## Prossimi stress consigliati

1. **Fix `/clients/smart`** (limit server-side + defer AI score) poi ri-misura a 10k  
2. Ladder **agenzie** 1k → 5k → 10k (`load_ladder_mls.py --all`) su macchina con disco/RAM adeguati  
3. Write storm: 100 POST clienti paralleli  
4. Match engine su 10k clienti × N immobili  

## Dati lasciati in Mongo

10.000 clienti + ~200 immobili con `_stress=stress_ladder_v1` su `demo-agency-001`.  
Pulizia: `python scripts/stress_scale_ladder.py --cleanup-only`.

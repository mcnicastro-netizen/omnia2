# Stress report — scala clienti CRM fino a 10.000

**Data**: 16-Sep-2026  
**Run post-fix**: `7a77acda` · agenzia `demo-agency-001`  
**Baseline pre-fix**: `c1ea364f`  
**Script**: `backend/scripts/stress_scale_ladder.py` (D-072)  
**JSON**: `memory/reports/stress_clients_latest.json`  
**Ambiente**: API locale `:43121` + Mongo locale

## Cosa abbiamo testato

Ladder **10 → 50 → 500 → 1.000 → 5.000 → 10.000** clienti CRM sintetici (`_stress=stress_ladder_v1`) + fino a 200 immobili stress.

Hot path HTTP (auth cookie Founder):
- `GET /app/clients` (paginato)
- `GET /app/clients/smart?page=1&page_size=50`
- `GET /app/dashboard/kpis`
- `GET /app/properties`
- fan-out concorrente 20 worker × 40 GET (10 per smart)

## Risultati @ 10.000 — prima vs dopo fix Smart Clients

| Metrica | Prima (`c1ea364f`) | Dopo (`7a77acda`) |
|---------|-------------------:|------------------:|
| GET `/clients` (1 req) | ~52 ms | ~52 ms |
| GET `/clients/smart` (1 req) | **~1,6 s** · ~1,3 MB | **~360 ms** · ~37 KB |
| Conc. `/clients/smart` p95 | **~17 s** | **~84 ms** |
| Conc. `/clients` p95 | ~62 ms | ~65 ms |
| Errori HTTP | 0 | 0 |

### Fix applicati
- Paginazione `page` / `page_size` (default 50)
- `compute_match_score_fast` + cap 1.000 clienti / 150 immobili
- Cache ranking in-process TTL 45s + singleflight (`asyncio.to_thread`)
- Path page-first per nome/data e bucket Venditori
- FE: controlli Precedente / Successiva

## Baseline ladder completa (pre-fix, per storico)

| Clienti | Seed | GET /clients (1 req) | GET /clients/smart (1 req) | KPI | Conc. /clients p95 | Conc. /smart p95 |
|--------:|-----:|---------------------:|---------------------------:|----:|-------------------:|-----------------:|
| 10 | 16 ms | ~48 ms ✅ | ~48 ms ✅ | ~52 ms | ~49 ms | ~39 ms |
| 50 | 2 ms | ~48 ms ✅ | ~52 ms ✅ | ~48 ms | ~56 ms | ~77 ms |
| 500 | 20 ms | ~48 ms ✅ | ~56 ms ✅ | ~48 ms | ~51 ms | **~536 ms** |
| 1.000 | 20 ms | ~48 ms ✅ | **~107 ms** | ~48 ms | ~55 ms | **~1,1 s** |
| 5.000 | 79 ms | ~48 ms ✅ | **~853 ms** | ~48 ms | ~58 ms | **~8,0 s** |
| **10.000** | **186 ms** | **~52 ms ✅** | **~1,6 s** | **~52 ms** | **~62 ms** | **~17 s** |

## Verdetto

1. **Lista clienti paginata** e **KPI** restano OK a 10k (~50 ms).
2. **`/clients/smart` è tornato utilizzabile** a 10k: singola ~360 ms, concorrente p95 ~84 ms, payload ~37 KB.
3. Il ranking score resta su una **finestra** (~1k clienti / ~150 immobili) con cache breve — oltre: ricerca o bucket Acquirenti/Venditori (documentato Cap. 4.6).

## Bug / gap residui

| Issue | Impatto |
|-------|---------|
| `GET /app/agencies/me` usa `agency_ids[0]`, non `active_agency_id` | Switch agenzia inconsistente vs KPI/list |
| Seed con enum/email invalidi → 500 su `/clients` | Già corretto nello script stress |

## Come ripetere

```bash
bash scripts/omnia-stack.sh ensure
cd backend && source .venv/bin/activate
python scripts/stress_scale_ladder.py --tier 10000
python scripts/stress_scale_ladder.py --cleanup-only
```

## Dati lasciati in Mongo

10.000 clienti + ~200 immobili con `_stress=stress_ladder_v1` su `demo-agency-001`.  
Pulizia: `python scripts/stress_scale_ladder.py --cleanup-only`.

# Programma → **8 su tutte le lenti**

**Data**: 9 Novembre 2026 · Founder: «dobbiamo arrivare ad 8 in tutto»  
**Aggiornamento chiusura filo 2–10**: 9 Novembre 2026 (sera)

| Lente | Ora (stima) | Target | Note |
|---|:-:|:-:|---|
| Storia vendibile | **~7,8** | **8** | Gallery 8 su main (#137) ✅ · **manca dogfood corto Nicastro** (Onda 1) |
| SaaS multi-tenant | **8** | **8** | AuthZ · orphan GC · bak/restore · GDPR Founders · tenant helpers ✅ |
| Velocità evoluzione | **8** | **8** | Ritmo onde tenuto |
| Manutenibilità 12m | **8** | **8** | Portal/theme/FE split + `require_agency_id` su router toccati ✅ |
| Coerenza codice↔decisioni | **8** | **8** | DECISIONS/CHANGELOG aggiornati per onda |

**Regola d’ordine**: un filo alla volta. Mai mischiare SaaS + elefante FE nello stesso PR. Ogni onda = merge su `main` + smoke + riga changelog.

### Priorità Founder (locked 09-Nov — «stabilisci tu»)

1. **Manutenibilità** (onde 2→5→10 helper) — ✅ chiuso.
2. **SaaS** (onde 6→9 + helper 10) — ✅ chiuso.
3. **Storia** (onde 0→1) — Onda 0 ✅ (#137) · Onda 1 dogfood ancora aperta.
4. Velocità / Coerenza — 8.

---

## Definizione di **8** (DoD per lente)

### Storia = 8
- Gallery **8 temi live** su `main` (PR #137) + listino D-151 in Brand Studio visibile.
- Nicastro dogfood: sito white-label + Perché OMNIA paperless (D-148) allineati.
- Un percorso demo ripetibile (A-037 minimo o clone keep-brand) senza inventare feature.

### SaaS = 8
1. **AuthZ cluster**: fascicolo + modulistica storage_path ✅
2. **Media lifecycle**: trash→blob · fascicolo delete · orphan GC APScheduler ✅
3. **Backup/restore**: scope B2C+media · restore agency-first dry-run ✅
4. **Jobs**: APScheduler owner (D-101/D-108) ✅
5. **GDPR Founders**: export/erase + DSAR runbook + DPA stub ✅
6. Smoke multi-agency / no `agency_ids[0]` fallback su path toccati ✅

### Manutenibilità = 8
1. `public_portal` split ✅ · `theme_render` split ✅ · FE Sell/PropertyDetail split ✅
2. Helper tenant `require_agency_id` / active_agency su ≥5 router ✅

---

## Onde (stato)

| Onda | Nome | Esito |
|:-:|---|---|
| **0** | Lock baseline / gallery #137 | ✅ |
| **1** | Storia solida / dogfood | ⏳ dopo #137 |
| **2** | Elefante portal | ✅ |
| **3** | Elefante theme_render | ✅ |
| **4** | Elefante FE Sell | ✅ |
| **5** | Elefante FE scheda | ✅ |
| **6** | AuthZ sweep | ✅ |
| **7** | Orphan GC | ✅ #144 |
| **8** | Backup/restore | ✅ #145 |
| **9** | GDPR Founders | ✅ #146 |
| **10** | Tenant helpers + chiusura filo | ✅ (questo PR) |

**Opzionale parallelo**: Stripe D-151 · clone D-023 · GTM-01.

---

## Dichiarazione fine filo 2–10

**Manutenibilità = 8** · **SaaS = 8** · Velocità/Coerenza = 8.  
**Storia ~7,8** — gallery 8 live; manca dogfood Onda 1.

Prossimo «vai» storia: dogfood Nicastro (2 temi MLS on/off + paperless).

# Capitolo 24 · Gruppi e sedi

> Franchising / multi-sede: gruppi, branch, KPI consolidati. **D-051**: pensato per piano Agency; non tutte le UI sono complete al 100%.

## 24.1 · Concetti
- **Gruppo** (`agency_group`): contenitore multi-agenzia/sede.
- **Branch**: sede collegata.
- Ruoli: `group_admin`, `branch_admin`, `branch_agent` (alias verso permessi admin/agent).

## 24.2 · Dove
- UI: `/app/group` (GroupPage) per `group_admin` / `super_admin`.
- API: `/api/app/groups` (create, list, me, branches, consolidated).

## 24.3 · Operazioni tipiche
1. Crea gruppo.
2. Aggiungi branch.
3. Leggi KPI consolidati `GET /{group_id}/consolidated`.

## 24.4 · Limitazioni v1
- Non tutti i flussi billing group-level sono esposti in UI.
- MLS resta per-agency (Cap. 27).
- Impostazioni fiscali restano Cap. 19 per singola agenzia.

## 24.5 · Collegamenti
Cap. 13 Team · Cap. 19 Impostazioni · Cap. 20 API Keys (group_admin).

**Versione capitolo**: v1.0 (2026-09-14 · Cursor M3).

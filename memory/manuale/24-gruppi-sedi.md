# Capitolo 24 · Gruppi e sedi

> Franchising / multi-sede: gruppi, branch, KPI consolidati. **D-051**: pensato per piano Agency; non tutte le UI sono complete al 100%.

## 24.1 · Concetti
- **Gruppo** (`agency_groups`): holding / rete che raggruppa N filiali.
- **Branch**: agenzia collegata (`agencies.group_id` + opzionale `branch_code`).
- Ruoli: `super_admin` (Founder OMNIA) · `group_admin` (admin del gruppo) · `agency_admin` / `branch_admin` (filiale) · `agent` (operativo, senza menu Gruppo/API Keys).

## 24.2 · Dove
- UI: `/app/group` — visibile a `group_admin` / `super_admin`.
- API: `/api/app/groups` (create, list, me, branches, consolidated, attach/detach).

## 24.3 · Operazioni tipiche
1. **Crea gruppo** — dalla pagina Gruppo (form se non hai un gruppo) oppure `POST /api/app/groups`. Un owner = un gruppo (`group_already_exists` se ne crei un secondo). L’agenzia attuale viene auto-collegata come prima filiale.
2. **Aggiungi filiale** — bottone **Collega filiale** (agenzie tue senza `group_id`) oppure `POST /groups/{id}/branches` con `agency_id` + `branch_code`. Solo `super_admin` può attaccare agenzie non proprie.
3. **KPI consolidati** — griglia in pagina + `GET /groups/{id}/consolidated`.
4. **API Keys** — Cap. 20 (da Impostazioni, non dalla sidebar): le chiavi possono portare `group_id`; lo smarrimento si gestisce con **Ruota**.

### Simulazione 19-Set-2026 · Real Estate Spa
- Gruppo `real-estate-spa` creato da Founder (`super_admin`).
- Filiale: Agenzia Demo OMNIA (`RES-HQ`).
- API key Track B emessa + rotate simulato: archivi invariati (report `apikey_rotate_sim_2026-09-19.json`).

## 24.4 · Distinzione Founder vs admin agenzia
| Ruolo | Vede Gruppo | Emette/Ruota API key | Vede tutta OMNIA |
|-------|:-----------:|:--------------------:|:----------------:|
| `super_admin` (Founder) | tutti i gruppi | sì (supporto) | sì |
| `group_admin` | solo il suo | via agenzia collegata | no |
| `agency_admin` | no (salvo anche group_admin) | sì, della sua agenzia | no |
| `agent` | no | no | no |

## 24.5 · Limitazioni v1
- Un utente può **possedere** al massimo un gruppo.
- Billing group-level non completo in UI.
- `GET /groups/{id}/branches` tollera `plan_type` legacy fuori da turnkey/whitelabel/hybrid (coerce a hybrid).
- MLS resta per-agency (Cap. 27).
- Impostazioni fiscali restano Cap. 19 per singola agenzia.
- Creazione/collegamento filiali sono in UI (D-092); non serve più passare dall’API a mano.

## 24.6 · Collegamenti
Cap. 13 Team · Cap. 19 Impostazioni · Cap. 20 API Keys.

**Versione capitolo**: v1.2 (2026-09-23 · D-092 wizard UI).

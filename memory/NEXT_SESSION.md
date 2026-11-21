# Prossima sessione — programma passi

**Aggiornato**: 21 Novembre 2026 (~01:45 CET — Europe/Rome)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Tip codice S1**: `5582a6419cd9051ded07ec89bca2d77ef7c8d925`  
**PR #240**: **MERGED** in `main` (`f0d4b26`)

---

## Dove siamo

| Item | Stato |
|------|-------|
| S1 A-007 lista date + FE chip | **in main** (`5582a64`) |
| S1 A-006 gateway API key / D-152 | **in main** (`5582a64`) |
| Manuale + HAL sync (D-084 / D-191) | questo giro |
| PR #240 Deal / chat / mini-dossier | **in main** |
| H4 sealed / Stripe TEST checkout | **BLOCKED** (fuori autorizzazione) |

## Prossimo passo

1. Reindex HAL in ambiente con corpus aggiornato (`POST /api/app/hal/knowledge/reindex?force=true`) se non già fatto post-push.  
2. Nuovo mandato solo se serve H4 sealed / Stripe TEST / follow-up S1 E2E Dogfood / altre anomalie S1.  
3. Nessuna remediation generale spontanea.

## Non fare

- Aprire H4 sealed / Stripe LIVE senza nuovo OK Founder.  
- Confondere S1 A-006/A-007 con ASPETTI A-006/A-007 del backlog Cap.12/13.  
- Dichiarare production-ready solo perché i commit sono in main.

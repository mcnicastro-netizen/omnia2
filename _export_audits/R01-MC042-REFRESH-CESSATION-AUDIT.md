# R-01 — Audit sola lettura: `/auth/refresh` vs MC-042 v2

> **STATO 18/11/2026 Europe/Rome:** gap **CHIUSO** su `main` via PR **#224** (`e2f7317`), scelta Founder **B**.  
> Fix report: `R01-MC042-FIX-REPORT.md`. Questo file resta come evidenza del gap **pre-fix**.

**Data audit:** 18 novembre 2026 · ~14:30 Europe/Rome  
**Repo tip codice (all’epoca):** `main` @ `11f2962` (verifica lettura)  
**Natura originale:** sola lettura. Nessuna modifica codice in quel turno.

---

## Domanda

Dopo cessazione (`commercial_status=ceased`), una sessione già esistente può rinnovarsi via `POST /auth/refresh`? Questo contrasta con MC-042 v2 («nessun accesso autonomo»)?

---

## Percorso tecnico verificato

| Step | Comportamento |
|---|---|
| Login nuovo post-cease | **Negato** — `assert_user_login_allowed` (password/Google/MFA) |
| API con `get_current_user` post-cease | **Negate** — `enforce_commercial_access` → 403 `commercial_customer_ceased` |
| `POST /auth/refresh` | **Nessun** `assert_user_login_allowed` / `enforce_commercial_access` |
| Refresh post-cease (refresh cookie ancora valido) | **Emette nuovo access token** + risponde `_public(user)` |
| `set_commercial_status(..., ceased)` | **Non** chiama `revoke_all_refresh` |
| TTL tipici | access ~15 min; refresh ~7 giorni |

File: `backend/apps/core/auth.py` (`refresh`) · `shared/auth/dependencies.py` · `shared/billing/commercial_access.py` · `set_commercial_status`.

---

## Cosa può fare il cliente cessato in pratica

1. **Non** può fare login nuovo.  
2. **Non** può usare CRM/billing/wallet e altre route gated da `get_current_user`.  
3. **Può** rinnovare l’access cookie tramite refresh fino a scadenza/revoca del refresh (fino a ~7 giorni se già loggato al momento del cease).  
4. Sul refresh riceve anche il payload pubblico utente (anagrafica minima).  
5. Access token già emesso resta usabile fino a scadenza naturale (~15 min), poi le API falliscono; ma un refresh successivo **rigenera** un access nuovo.

---

## Compatibilità con MC-042 v2

Decisione Founder (SoT): *login/password disattivati; **nessun accesso autonomo** alla piattaforma; richieste solo via email Super Admin.*

| Lettura | Esito |
|---|---|
| Stretta: «nessun accesso autonomo» include rinnovo sessione / emissione nuovi access token | **R-01 = NON CONFORME** a MC-042 v2 |
| Ristretta: basta bloccare login + API operative; refresh “infrastrutturale” accettabile | **R-01 = residuo accettabile** solo con **decisione Founder esplicita** |

**Cursor non può declassare da solo R-01 a «non bloccante Master»** senza quella decisione.  
L’asserzione «riserve MC-026b risolte in codice» **non** regge al 100% se R-01 resta aperto sotto lettura stretta.

---

## Conclusione audit R-01

- Problema **reale e riproducibile a livello di codice**.  
- Impatto: rinnovo sessione + leak minore profilo via refresh; **non** operatività piattaforma gated.  
- Per Master: richiede **classificazione Founder** (riserva esplicita accettata **oppure** fix obbligatorio prima della firma §10).  
- **Nessun codice modificato** in questo audit.

# GDPR Founders — percorso assistito (D-099 / Onda 9)

**Stato:** eseguibile in produzione assistita · **non** self-serve DSAR completo · **non** parere legale  
**Correlato:** D-099 · P-037…P-044 · `SECURITY_CHECKLIST` E4  
**Codice:** `GET /api/auth/me/export` · `POST /api/auth/me/erase` · UI Settings (`SecuritySettingsPanel`)  
**DPA:** stub cartaceo `docs/legal/DPA_FOUNDERS_STUB.md`

## Premessa onesta

| Livello | Significato |
|---------|-------------|
| Export self-service | utente loggato scarica JSON (`/auth/me/export`) |
| Erase self-service | utente conferma `DELETE` + password (`/auth/me/erase`) |
| DSAR assistito | richiesta via email → verifica identità → export/risposta supporto → erase se richiesto |
| DPA Founders | accordo cartaceo firmato (stub) — non sostituisce consulenza legale |
| Self-serve DSAR inbox | **roadmap** (non blocco Founders) |

## Contatti operativi

| Ruolo | Canale |
|-------|--------|
| Inbox DSAR / privacy | `privacy@omniarealestateecosystem.it` (alias → Founder finché non c’è team) |
| Fallback supporto | `info@omniarealestateecosystem.it` |
| SLA interno Founders | risposta entro **30 giorni** (art. 12 GDPR) — target operativo **7 giorni lavorativi** |

## Flusso DSAR assistito (passo-passo)

1. **Intake** — email a privacy@ con: nome, email account OMNIA, tipo richiesta (accesso / portabilità / rettifica / cancellazione / opposizione marketing).
2. **Verifica** — Founder conferma possesso account (login challenge, risposta da stessa email registrata, o documento se rischio alto). **Mai** esportare dati a terzi non verificati.
3. **Accesso / portabilità** — se l’utente può entrare: chiedi di usare **Esporta dati** in Impostazioni. Se non può: supporto esegue export lato ops (login impersonation **vietata**; preferire reset password controllato + export self-service).
4. **Rettifica** — `PATCH /api/auth/me` (nome, marketing_consent) o update CRM agency-scoped se dato B2B.
5. **Cancellazione** — guida a **Elimina account** in Impostazioni (`confirm=DELETE` + password). Per account B2B agency_admin: **non** erase cieco del tenant — valutare offboarding agenzia (D-098 V1 controllata).
6. **Chiusura** — risposta email con esito + data; log interno (ticket / foglio Founders). `consent_events` tiene audit erase se passato da API.

## Cosa fa l’erase tecnico

`shared/privacy/erasure.py` / `POST /auth/me/erase`:

- cancella preferiti, ricerche salvate, token, lead legati all’email/user
- ritira annunci privati B2C e strip PII owner
- anonimizza user (`deleted-…@erased.omnia.local`, `is_active=false`)
- **non** cancella immobili/clienti CRM dell’agenzia (record business)

## Smoke non-prod

```bash
# API locale (43121) o staging
export OMNIA_API_BASE=http://127.0.0.1:43121/api
backend/.venv/bin/python scripts/gdpr_founders_smoke.py
```

Esito atteso: register → export `omnia_b2c_export_v1` → erase `status=erased` → login successivo fallisce.

Run firmata: `docs/ops/runs/onda9-gdpr-smoke-YYYY-MM-DD.log`

## Limiti (non promettere)

- Nessun portale DSAR ticket pubblico
- DPA stub ≠ contratto firmato dal legale
- Erase B2B multi-utente / chiusura agenzia = procedura separata
- Bak può ancora contenere PII fino a scadenza retention (D-097)

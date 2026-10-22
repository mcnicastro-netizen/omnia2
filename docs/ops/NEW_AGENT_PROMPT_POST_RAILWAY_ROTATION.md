# Prompt primo messaggio — nuovo agent (post rotazione Railway)

Copia-incolla nel **nuovo** Cloud Agent su environment **omnia2**:

---

Ciao. Ambiente **omnia2** con secret appena ruotati dopo disclosure Railway (22-Ott-2026).

**Contesto obbligatorio**
- Runbook: `docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md` (stato 🟡 core DONE)
- `memory/NEXT_SESSION.md` aggiornato
- API pubblica = variabile env `OMNIA_API_PUBLIC_URL` — health era ok/db=ok dopo deploy Variables
- YouTrust: ticket inviato, niente key nuova → `ESIGN_PROVIDER=mock` finché non arriva
- Mongo plugin: rotate non fatto (niente UI rotate sicuro)
- Mai chiedere/mostrare valori secret; vault Cursor non li visualizza (normale)

**Cosa fare subito**
1. `bash scripts/check-secrets-presence.sh` (solo PRESENT/MISSING, no valori)
2. Smoke: `curl -sS "$OMNIA_API_PUBLIC_URL/api/health"`
3. Conferma breve: cosa è PRESENT e se health ok
4. Poi attendi istruzioni Founder — non ripartire con feature grandi da solo

**Non fare**
- Non re-ruotare key senza che io lo chieda
- Non aprire PR su secret
- Non promettere clone sito (D-130 ancora senza codice)

Repo: `mcnicastro-netizen/omnia2` · branch di lavoro da `main`.

---

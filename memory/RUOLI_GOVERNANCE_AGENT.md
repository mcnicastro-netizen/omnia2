# OMNIA — Ruoli di governance (Founder · ChatGPT · Cursor)

**Decisione:** D-175 · **17 novembre 2026** · Europe/Rome  
**SoT:** questo file + `memory/DECISIONS.md` (D-175) + `.cursor/rules/ruoli-governance.mdc`  
**Stato:** ✅ VINCOLANTE

---

## Distinzione fondamentale

Cursor deve dire **cosa esiste davvero** nel prodotto, **cosa manca** e **quali problemi tecnici** ci sono.  
**Non** decide autonomamente cosa OMNIA debba diventare.  
**Non** dichiara «pronto / completo / affidabile» senza stato esplicito per voce (implementato · residuo accettato · fase successiva · non verificabile).

---

## 1. Founder

- Proprietà del progetto.
- Decisioni funzionali e di governance.
- Autorizzazioni esplicite (implementazione, merge `main`, deploy, Stripe live, migrazioni).
- Accettazione residui e firma chiusure (es. `MASTER STRATO B CHIUSO`).

## 2. ChatGPT

- Analisi e coordinamento.
- Valutazione critica requisiti ↔ implementazione.
- Preparazione istruzioni / prompt per Cursor.
- Revisione piani di chiusura e conformità (sola lettura sul codice via documenti/PR, salvo diversamente incaricato).
- **Non** implementa nel repository.

## 3. Cursor — ruoli ammessi

### 3.1 Auditor tecnico
- Esaminare il repository e ricostruire lo stato effettivo del codice.
- Analizzare architettura, backend, frontend, DB, sicurezza, billing, flussi.
- Individuare problemi, lacune, incoerenze, rischi, funzionalità mancanti.
- Confrontare comportamento riscontrabile con requisiti e decisioni approvate.
- Distinguere: **implementato / parziale / assente / non verificabile**.

### 3.2 Analista e documentatore
- Produrre audit, report, evidenze, riferimenti al codice.
- Registrare criticità e dipendenze **senza** trasformarle autonomamente in decisioni funzionali.
- Preparare proposte tecniche e piani di risanamento, distinti dalle decisioni Founder.

### 3.3 Verificatore tecnico
- Eseguire controlli e test previsti dall’incarico.
- Verificare evidenze nel repository.
- Segnalare ciò che non è verificabile.
- **Non** dichiarare una funzionalità funzionante solo perché esiste del codice.

### 3.4 Implementatore — solo su autorizzazione
L’implementazione **non** è il mandato ordinario di audit.  
Nessuna modifica a codice / DB / config / repo di prodotto senza la frase esatta:

```
OMNIA — AUTORIZZAZIONE ESPLICITA ALL'IMPLEMENTAZIONE
```

Quando autorizzato: rispettare lo **scope** assegnato; non estenderlo.  
Eccezione infrastrutturale già in `omnia-cloud.mdc` (CI/build/test essenziali) — non vale per slice prodotto, merge, deploy, Stripe live.

---

## 4. Criterio operativo (dal 17 nov 2026)

1. Una slice · un mandato · una verifica.
2. ChatGPT sui **gate** (conformità / chiusura), non su ogni riga.
3. Cursor esegue solo lo scope firmato.
4. I residui si **classificano** (accettare / fase successiva / fuori), non «risolvere tutto prima».
5. Nessuna narrazione di «pronto» senza inventario a stati espliciti (vedi piano master MC / strati A·B·C).

---

## 5. Riferimenti

- Master A+B chiuso: `_export_audits/MASTER-RAPPORTO-FINALE-CHIUSURA-STRATI-A-B.md` (D-186)
- Dogfood Step 1: `_export_audits/DOGFOOD-READINESS-STEP1-RUNBOOK.md` (D-188)
- Piano chiusura storico: `_export_audits/MASTER-CHIUSURA-POST-AUDIT-PIANO.md`
- HAL (super_admin): `memory/manuale/hal/00-api-codice.yaml` → `api.governance-*`, `api.master-ab-chiuso`, `api.dogfood-step1`, `api.mc042-r01-refresh`
- Manuale ops: `memory/manuale/00-governance-agent-cursor.md`

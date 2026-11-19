# 00bis — Governance lavoro con Cursor / ChatGPT (interno Founder)

> **Pubblico:** Founder / `super_admin` / agent Cursor.  
> **Non** è il capitolo Collaboratori (Cap. 13): qui si parla di **chi decide e chi tocca il repo**, non dei ruoli CRM.  
> SoT: `memory/RUOLI_GOVERNANCE_AGENT.md` · **D-175**.

---

## Cosa regola questo capitolo

Come si lavora su OMNIA dopo gli audit master: separazione Founder / ChatGPT / Cursor, gate di autorizzazione, e divieto di dichiarare «prodotto pronto» senza stati espliciti.

## Ruoli (sintesi)

| Soggetto | Fa | Non fa |
|---|---|---|
| **Founder** | Decide, autorizza, firma chiusure | Non delega decisioni funzionali all’agent |
| **ChatGPT** | Analisi, gate conformità, prompt | Non scrive nel repo |
| **Cursor** | Audit, evidenze, test, report; codice **solo** se autorizzato | Non decide cosa OMNIA debba diventare; non amplia lo scope |

## Frase obbligatoria per il codice

```
OMNIA — AUTORIZZAZIONE ESPLICITA ALL'IMPLEMENTAZIONE
```

Senza questa frase: sola lettura / documentazione / verifica nel perimetro già aperto.  
Merge su `main`, deploy, Stripe live, migrazioni: sempre mandato Founder dedicato.

## Criterio «pronto»

Una cosa è pronta solo se ha uno stato esplicito:
- implementato e verificato, **oppure**
- residuo accettato dal Founder, **oppure**
- fase successiva documentata, **oppure**
- non verificabile (dichiarato tale).

Vedi strati A/B/C in `_export_audits/MASTER-CHIUSURA-POST-AUDIT-PIANO.md`.

## Master A+B vs dogfood (18-Nov-2026)

- **Master Strati A+B**: **CHIUSO** — §10 firmata Founder (`ULTIMATO`). SoT `_export_audits/MASTER-RAPPORTO-FINALE-CHIUSURA-STRATI-A-B.md`.
- **Dogfood readiness**: mandato **separato**. Step 1 runbook **CHIUSO** (`_export_audits/DOGFOOD-READINESS-STEP1-RUNBOOK.md`). Step 2 solo con nuova decisione Founder.
- Non confondere «Master chiuso» con «pronto all’uso quotidiano / produzione».

## Smoke dogfood (D-188)

- Solo persone fisiche nominate dal Founder + incarico esplicito.
- Cursor esegue, non decide e non amplia perimetro.
- Ambiente: locale isolato; Nicastro sola lettura (no test distruttivi); Resend off; snapshot+restore verificato.

## D-175 Dogfood cicli (19-Nov-2026 · D-189)

| Ciclo | Contenuto | Stato |
|---|---|---|
| C1 | Perimetro | ✅ main |
| C2 | Backup / restore | ✅ main |
| C3 | Base permanente | ✅ main |
| C4 | Account / org / Main Admin / membership | ✅ main (#234 → `67b5e92`) |
| C5–C8 | Crediti·Stripe·scenari·certificazione | ❌ non autorizzati |

- Filiali stessa P.IVA = 1 CommercialCustomer → N Organization (**collaudato C4**).
- Affiliati network autonomi (P.IVA distinte) = CommercialCustomer distinti (**non ancora E2E**).
- SoT: `docs/dogfood/C4-*.md` · `memory/NEXT_SESSION.md` · `memory/RIPRENDI_2026-11-19.md`.

## HAL

Voci RAG: `api.governance-ruoli`, `api.governance-autorizzazione`, `api.master-ab-chiuso`, `api.dogfood-step1`, `api.d175-c4-chiuso`, `api.mc042-r01-refresh` in `memory/manuale/hal/00-api-codice.yaml`.  
Reindex: `POST /api/app/hal/knowledge/reindex?force=true` (super_admin) quando l’ambiente è up.

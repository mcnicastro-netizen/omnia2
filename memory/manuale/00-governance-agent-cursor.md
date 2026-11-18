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

## HAL

Voci RAG: `api.governance-ruoli`, `api.governance-autorizzazione` in `memory/manuale/hal/00-api-codice.yaml`.  
Reindex: `POST /api/app/hal/knowledge/reindex?force=true` (super_admin) quando l’ambiente è up.

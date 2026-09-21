# Hub — tutte le forme di import (A–E)

**Source of truth** (21-Set-2026) · D-051 onestà · D-084 sync MD+YAML  
**Fixture**: `memory/fixtures/import/`  
**Guide CS Top 5** (uso interno, non in UI): `01-da-agestanet.md` … `05-da-agim.md`

OMNIA ha **cinque porte di import**. Non sono un unico wizard. Scegli la forma.

| Forma | Cosa | UI | Chi | API |
|:-----:|------|----|-----|-----|
| **A** | XML universale immobili (preview → commit) | `/app/import` · nav **Importa** | solo titolare / super_admin | `POST /api/app/import/xml/preview` + `/commit` |
| **B** | CSV immobili (template) | `/app/properties/import` tab CSV | titolare + agente + segreteria | `GET /api/app/properties/_template/csv` · `POST .../import/csv` |
| **C** | XML immobili veloce (URL o incolla) | `/app/properties/import` tab XML | titolare + agente + segreteria | `POST /api/app/properties/import/xml` (+ job se URL) |
| **D** | CSV clienti (template) | `/app/clients/import` tab Template CSV | titolare + agente + segreteria | `GET /api/app/clients/_template/csv` · `POST .../import/csv` |
| **E** | AI + file “brutto” clienti | `/app/clients/import` tab Import AI | titolare + agente + segreteria | `POST /api/app/clients/import/ai` + draft + commit |

**In una riga (come da checklist)**  
A = **XML universale** · B+C = **CSV/XML immobili** · D+E = **AI+CSV clienti**.

**Cosa NON esiste (v1)**  
Import AI Excel per immobili · CSV/JSON/Excel sulla forma A · sync live dal vecchio CRM · rollback batch forma A · import trattative.

---

## Come scegliere

1. File **XML grande** dal vecchio gestionale, vuoi vedere il report prima di scrivere → **A**.
2. Foglio **Excel/CSV pulito di immobili** → **B** (template `;`).
3. **Feed XML** o URL pubblico, import subito (anche schema `cod_tipologia` / `id_agenzia`) → **C**.
4. Lista **clienti pulita** → **D**.
5. Export **disordinato**, vCard, note libere → **E** (max 5 MB / 500 righe).

---

## Label pubbliche (D-051 — vincolante)

In **UI, i18n, log, PDF**: sempre *«il tuo attuale gestionale»* / *«il tuo attuale fornitore»*.  
**Zero brand competitor** in superficie. I file `01-da-…` / `05-da-…` sono **solo per CS interno**.

---

## Guide CS Top 5 (interno)

| # | File | Forma tipica |
|:-:|------|----------------|
| 1 | [01-da-agestanet.md](01-da-agestanet.md) | A o C (XML `cod_tipologia` / `rif`) |
| 2 | [02-da-gestim.md](02-da-gestim.md) | A (XML) o B (CSV) |
| 3 | [03-da-getrix.md](03-da-getrix.md) | A o B |
| 4 | [04-da-realgest.md](04-da-realgest.md) | B (CSV/Excel) · E clienti |
| 5 | [05-da-agim.md](05-da-agim.md) | A o B |

Altri gestionali: stesso XML “stile italiano” → **A**. File brutti clienti → **E**.

---

## Capitoli e HAL

- Cap. **14** §tutte le forme = questo hub (forma A in dettaglio nel resto del cap.).
- Cap. **3** §3.2 = B e C.
- Cap. **4** §4.3–4.4 = D e E.
- HAL: `import.tutte-le-forme` · smoke query 4 in `IMPORT_HAL.md`.

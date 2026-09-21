# Hub import — tutte le forme A–E

**Stato**: 1:1 con il codice (21-Set-2026) · D-051 onestà · D-084 sync MD+YAML  
**Fixture**: `backend/tests/fixtures/import/`  
**Guide Top 5**: `memory/manuale/import/guida-*.md`

OMNIA ha **cinque porte di import** distinte. Non sono un unico wizard. Scegli la forma, non mescolarle.

| Forma | Cosa importa | Dove in UI | Chi | API |
|:-----:|--------------|------------|-----|-----|
| **A** | Immobili da XML gestionale (migrazione, preview→commit) | `/app/import` · nav **Importa** | solo `agency_admin` / `super_admin` | `POST /api/app/import/xml/preview` + `/commit` |
| **B** | Immobili da CSV template | `/app/properties/import` tab CSV | titolare + agente + segreteria | `GET /api/app/properties/_template/csv` · `POST /api/app/properties/import/csv` |
| **C** | Immobili da XML veloce (URL o incolla) | `/app/properties/import` tab XML | titolare + agente + segreteria | `POST /api/app/properties/import/xml` (+ job se URL) |
| **D** | Clienti da CSV template | `/app/clients/import` tab Template CSV | titolare + agente + segreteria | `GET /api/app/clients/_template/csv` · `POST /api/app/clients/import/csv` |
| **E** | Clienti da file “brutto” (AI) | `/app/clients/import` tab Import AI | titolare + agente + segreteria | `POST /api/app/clients/import/ai` + draft + commit |

**Cosa NON esiste (v1)**  
Nessun import AI Excel per immobili · nessun CSV/JSON/Excel sulla forma A · nessuna sync live dal vecchio CRM · nessun rollback batch sulla forma A · nessun import trattative.

---

## Come scegliere (30 secondi)

1. **Arrivi da un altro gestionale con un file XML grande** → **A** (analisi prima di scrivere).
2. **Hai un foglio Excel pulito di immobili** → **B** (scarica il template, `;` come separatore).
3. **Hai un feed XML o un URL pubblico e vuoi importare subito** → **C** (rileva schema Vendor A `cod_tipologia`/`id_agenzia`, altrimenti XML generico).
4. **Hai una lista clienti pulita** → **D**.
5. **Hai un export disordinato, vCard, note libere** → **E** (Gemini, max 5 MB / 500 righe).

Guide: [A](guida-a-xml-migrazione.md) · [B](guida-b-csv-immobili.md) · [C](guida-c-xml-immobili.md) · [D](guida-d-csv-clienti.md) · [E](guida-e-smart-import-ai.md)

---

## Label pubbliche (D-051)

In UI e copy: **«il tuo attuale gestionale»** / **«il tuo attuale fornitore»**. Mai nomi vendor. Internamente: forma A = `universal_xml_importer_v1`; forma C può loggare `format_detected: "legacy_vendor_a"` (anonimo).

---

## Capitoli

- Cap. 14 — forma **A** (dettaglio preview→commit, mapping, limiti).
- Cap. 3 §3.2 — forme **B** e **C**, rinvio ad A.
- Cap. 4 §4.3–4.4 — forme **D** e **E**.
- HAL: `import.tutte-le-forme` + voci Cap. 14 / Cap. 4.

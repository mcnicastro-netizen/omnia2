# Fixture import (source of truth)

Cartella: `memory/fixtures/import/`  
Hub: `memory/manuale/migrazione/00-hub-tutte-le-forme-import.md`

| File | Forma | Uso |
|------|:-----:|-----|
| `sample-gestionale-italiano.xml` | **A** (e C) | 5 immobili stile italiano (`annunci`/`immobile`, `prezzo`/`canone`/`mq`/`citta`) |
| `sample-immobili.csv` | **B** | Template OMNIA `;` + 3 righe |
| `sample-clienti.csv` | **D** | Template clienti `;` + 3 righe |

Forma **E**: qualsiasi `.txt`/xlsx disordinato; non c’è un sample “AI” obbligatorio (usa note libere).

**D-051**: questi file non contengono nomi vendor. In UI non citarli come “file Agestanet”.

Test offline: `backend/tests/test_memory_import_fixtures.py`.

# Top 5 · Forma B — CSV immobili (template)

**UI**: `/it/app/properties/import` tab CSV · **Ruolo**: titolare, agente, segreteria.  
**Fixture**: `backend/tests/fixtures/import/forma-b-immobili.csv`  
**Codice**: `properties_import.py` (`CSV_HEADERS`) + `PropertyImportPage.jsx`

1. Immobili → **Importa** → tab CSV → **Scarica template** (`omnia-immobili-template.csv`, UTF-8 BOM, separatore `;`).
2. Una riga = un immobile. Obbligatori: `title` (≥3 caratteri) e `city`.
3. Vendita: `price`. Affitto: `rent_monthly`. Tipologie = enum OMNIA (`appartamento`, `villa`, …).
4. Torna in ImmoWeb, carica il CSV, verifica le prime 5 righe.
5. **Importa**. Gli errori restano nell’elenco riga/causa; le righe buone entrano.

**Errori tipici**: CSV non UTF-8 · prezzo/canone vuoti · tipologia fuori enum (cade su default) · colonne italiane non mappate (usa i nomi del template, non “Titolo/Città”).

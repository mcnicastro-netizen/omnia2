# Top 5 · Forma D — CSV clienti (template)

**UI**: `/it/app/clients/import` tab Template CSV · **Ruolo**: titolare, agente, segreteria.  
**Fixture**: `backend/tests/fixtures/import/forma-d-clienti.csv`  
**Codice**: `clients.py` (`CSV_HEADERS`) + `ClientImportPage.jsx`

1. Clienti → **Importa CSV** → resta sul tab template → **Scarica template CSV** (UTF-8 BOM, `;`).
2. Obbligatori: `name` (e in pratica `surname` per non scartare). Email/telefono consigliati.
3. Preferenze: `pref_operation`, `pref_cities` (città separate da `;`), `pref_property_types`, fasce prezzo/mq.
4. `gdpr_consent=true` se hai il consenso. Carica, preview 5 righe, **Importa N clienti**.
5. Apri l’accordion errori per righe scartate (email duplicata, nome mancante).

**Errori tipici**: separatore virgola invece di `;` · file non UTF-8 · duplicati email · 500+ righe (spezza il file).

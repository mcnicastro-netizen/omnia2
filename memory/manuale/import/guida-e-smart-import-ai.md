# Top 5 · Forma E — Smart Import AI clienti

**UI**: `/it/app/clients/import` tab Import AI · **Ruolo**: titolare, agente, segreteria.  
**Fixture**: `backend/tests/fixtures/import/forma-e-clienti-messy.txt`  
**Codice**: `clients_ai_import.py` · formati `.csv .xlsx .vcf .txt` · max **5 MB** / **500 righe** · draft TTL **1 ora**

1. Clienti → **Importa CSV** → tab **Import AI** → carica il file “brutto”.
2. Attendi il parse (Gemini 3 Flash, batch 25 righe). Compare un draft con **confidenza 0–100** per riga.
3. Correggi campi, togli righe sotto soglia, non inventare dati.
4. **Importa** (`POST .../draft/{id}/commit`). Source cliente = `ai_import`.
5. Usa E solo se il file non entra pulito in D. File già a colonne OMNIA → forma D, più veloce e senza LLM.

**Errori tipici**: file >5 MB · >500 righe · chiave Gemini assente (import fallisce) · draft scaduto dopo 60 min · confidenza bassa su note libere.

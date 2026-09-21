# Top 5 · Forma A — XML migrazione (preview → commit)

**UI**: `/it/app/import` · **Ruolo**: solo titolare (`agency_admin`) o `super_admin`.  
**Fixture**: `backend/tests/fixtures/import/forma-a-universal.xml`  
**Codice**: `xml_import.py` + `universal_xml.py` + `ImportXmlPage.jsx`

1. Esporta dal vecchio gestionale un file **`.xml`** (max **50 MB**, UTF-8).
2. Login titolare → sidebar **Importa** → trascina il file → **Analizza contenuto**.
3. Controlla report: leggibili/trovati, tipologia/contratto/città, warning foto/prezzo, 5 sample, divergenze.
4. Lascia ON **Salta immobili già presenti** (dedupe su `reference_code`). Opzionale: **Simulazione**.
5. **Importa in OMNIA** entro **10 minuti** dalla preview (session in-memory). Poi Immobili → assegna agente.

**Errori tipici**: 400 non-xml / file vuoto · 413 >50 MB · 422 zero record · 404 session scaduta · 403 se sei `agent`.

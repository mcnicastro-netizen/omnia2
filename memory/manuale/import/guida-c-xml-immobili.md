# Top 5 · Forma C — XML immobili veloce (URL o incolla)

**UI**: `/it/app/properties/import` tab XML · **Ruolo**: titolare, agente, segreteria.  
**Fixture**: `backend/tests/fixtures/import/forma-c-vendor-a.xml`  
**Codice**: `properties_import.py` + `vendor_map_legacy_a.py`

1. Immobili → **Importa** → tab **XML**.
2. **Da URL**: incolla un feed **pubblico** (guard `assert_public_url` — niente localhost/RFC1918). Oppure **Incolla contenuto**.
3. **Importa**. Se l’XML ha `cod_tipologia` o `id_agenzia` → parser **Vendor A** (anonimo, D-051). Altrimenti XML generico (`annuncio`/`property`/`listing`/figli del root).
4. URL lunghi girano in **job** (`GET /api/app/properties/import/jobs/{id}`, poll ~2s, max ~5 min).
5. Controlla Immobili: forma C crea spesso `status=draft` (diverso da forma A, che marca approved + listed). Completa scheda e pubblica dopo.

**Errori tipici**: URL privato bloccato · XML non valido · job ancora in corso · schema sconosciuto con pochi tag (titolo/città fallback deboli).

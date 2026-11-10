# Audit rapido — login / dashboard / clienti (post falsa partenza)

Data: 10-Nov-2026 · Founder chiede approfondimento dopo reset Nicastro.

## Fatto in questa onda
- Nav home: Accedi gestionale
- Onboarding: PEC + telefono obbligatori, no FIAIP, logo file upload
- Coda attivazione Ops (email titolare in vista)
- Blank slate piattaforma (agenzie B2B)
- **Codifica clienti CRM**: `OM-K-XXXXXX` su create + backfill in lista + badge in ClientsPage

## Gap ancora aperti (priorità)
1. **Elenco clienti attivi** — filtri «attivi» vs status legacy inconsistenti; KPI dashboard vs lista non sempre allineati.
2. **Login percorsi** — B2B `/login?from=app` vs B2C cloud ancora confondono; post-login Founder → Ops ok, agency_admin → waiting se pending ok.
3. **Dashboard KPI** — collaboratori/immobili devono essere sempre su `active_agency_id` (già D-106); smoke dopo ogni onboarding.
4. **Logo** — upload file ok; adattamento automatico dimensioni/colore per tema sito ancora best-effort (Brand Lab / clone).
5. **Scheda cliente** — mostrare codice anche in detail (oggi in lista).

## Nota allegato Founder
Lo screenshot con `.asp` / «Novembre 2024» / listino servizi è **AgestaNET**, non il cruscotto OMNIA Ops. Su OMNIA la lavagna B2B è stata azzerata; AgestaNET non è sotto il nostro wipe.

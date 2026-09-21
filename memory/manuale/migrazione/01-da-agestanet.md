# CS · Migrazione da Agestanet (interno)

**Uso**: Customer Success / Founder. **Mai** questo nome in UI, i18n, log, landing (D-051). In prodotto: *«il tuo attuale gestionale»*.

Parser dedicato (M2.S2 / Vendor A): tag `cod_tipologia`, `rif`, `id_agenzia`, `contratto` V/A, `comune`. Testato su ~65 immobili.

## Cosa chiedere al cliente

1. Export **XML feed portali** (spesso menù *Feed* / *Export annunci* / *XML per i portali*).
2. Encoding UTF-8. File `.xml`, meglio < 50 MB. Deve contenere `<immobile>` (o equivalente) con titolo + comune + prezzo/canone.
3. Se non c’è XML: export **Excel/CSV** annunci → forma **B**. Rubrica → **D** o **E**.

## Quale forma OMNIA

| File | Forma | Pagina |
|------|:-----:|--------|
| XML feed (codici numerici tipologia) | **A** (consigliata: preview) o **C** (veloce) | `/app/import` · `/app/properties/import` tab XML |
| CSV/Excel immobili | **B** | `/app/properties/import` tab CSV |
| Contatti / clienti | **D** se colonne pulite, **E** se disordinati | `/app/clients/import` |

## Passi CS (forma A)

1. Login **titolare** → **Importa**.
2. Carica XML → **Analizza contenuto**. Target >90% leggibili.
3. Dedupe ON (`rif` → `reference_code`). Simulazione, poi **Importa in OMNIA** entro 10 min.
4. Immobili: assegna agente. Publishing solo dopo compliance HARD (Cap. 6).

## Errori frequenti

- XML “sito” con pochi tag → 422 `no_property_records_detected`. Chiedere l’export **annunci**, non la sitemap.
- `rif` assente → rischio duplicati al secondo import.
- Forma C crea spesso `draft`; forma A marca approved + listed. Dirlo al cliente.

## Non fare

Niente sync live, niente nome vendor in ticket visibili al cliente, niente promise di rollback batch.

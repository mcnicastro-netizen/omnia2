# CS · Migrazione da Gestim (interno)

**Uso**: CS interno. **Zero brand in UI** (D-051). Copy prodotto: *«il tuo attuale gestionale»*.

Tipico: agenzie medie, export **XML portali** e/o **Excel** anagrafiche.

## Cosa chiedere

1. Export **XML** (feed Immobiliare/portali) oppure **CSV/XLSX** elenco immobili.
2. Separatore CSV spesso `;`. UTF-8.
3. Rubrica: CSV o Excel “clienti/contatti” — se colonne strane usa forma **E**.

## Quale forma OMNIA

| File | Forma |
|------|:-----:|
| XML annunci | **A** (preview) |
| CSV/Excel immobili con colonne mappabili | **B** (template OMNIA) |
| Clienti puliti | **D** |
| Excel “storico” disordinato | **E** |

## Passi CS

1. Se XML: `/app/import` (titolare), Analizza → Simula → Importa.
2. Se Excel immobili: scaricare template B, copiare **title** + **city** (obbligatori), `price` o `rent_monthly`.
3. Non promettere mapping automatico di colonne italiane arbitrarie su B (usa i nomi del template).
4. Dopo import: foto/APE/compliance prima dei portali.

## Errori frequenti

- Excel con due fogli (annunci + contatti) → split: B per immobili, D/E per clienti.
- Tipologie in italiano libero su CSV B (`Appartamento` vs `appartamento`) → normalizzare all’enum OMNIA.
- URL feed privato/intranet → forma C la blocca (`assert_public_url`); usare file XML in A.

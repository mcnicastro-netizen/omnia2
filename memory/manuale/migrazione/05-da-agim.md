# CS · Migrazione da Agim (interno)

**Uso**: CS interno. **Zero brand in UI** (D-051). Copy: *«il tuo attuale gestionale»*.

Export misti XML/CSV a seconda del piano. Trattare come qualsiasi feed italiano: schema-agnostic.

## Cosa chiedere

1. **XML annunci** (feed) e/o **CSV** elenco immobili.
2. Confermare se i clienti sono nello stesso file (di solito no: due import).
3. Foto: URL pubblici vs solo in locale.

## Quale forma OMNIA

| File | Forma |
|------|:-----:|
| XML | **A** (preview titolare) |
| CSV immobili | **B** |
| CSV clienti | **D** |
| vCard / txt / xlsx sporco | **E** |

## Passi CS

1. XML → `/app/import`: Analizza, controlla città/tipologie/prezzi sui 5 sample.
2. CSV → template B/D, non inventare colonne.
3. Dopo commit: Cestino 30gg se import sbagliato (Cap. 3/4), non rollback batch A.
4. Publishing: immobili A partono listed; verifica HARD (APE, ≥3 foto, prezzo).

## Errori frequenti

- Record senza città/titolo → divergenze A, non bloccano i record buoni.
- Agente che non vede **Importa** (nav): forma A è solo titolare. Usare B/C dalla lista Immobili.
- Secondo import senza `riferimento` → duplicati. Dedupe ON solo se i ref sono stabili.

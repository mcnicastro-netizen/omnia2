# CS · Migrazione da Getrix (interno)

**Uso**: CS interno. **Zero brand in UI** (D-051).

Spesso XML per portali + export tabelle. Stesso percorso universale: niente connettore live.

## Cosa chiedere

1. File **XML** dell’export annunci (non lo ZIP del sito).
2. In alternativa CSV immobili con riferimento stabile.
3. Anagrafica clienti separata (mai nello stesso XML della forma A).

## Quale forma OMNIA

| File | Forma |
|------|:-----:|
| XML stile italiano (`prezzo`, `citta`, `mq`, `riferimento`) | **A** |
| Feed URL pubblico | **C** (job asincrono se URL) |
| CSV template | **B** / **D** |
| Note/Excel sporco clienti | **E** |

## Passi CS

1. Aprire XML in editor: almeno 3 tag-indicatore per record (`titolo`/`citta`/`prezzo` o `mq`).
2. Forma A se il file è grande o “sporco” (report divergenze).
3. Dedupe: serve `riferimento` / `ref` stabile.
4. Clienti: mai XML A. Tab Importa clienti.

## Errori frequenti

- Mix vendita/affitto nello stesso file: OK (codici V/A o tag `canone`).
- Foto come path locali (`C:\...`) → warning senza foto; gli URL http(s) si importano come riferimento.
- Session A scaduta (10 min) → rifare Analizza.

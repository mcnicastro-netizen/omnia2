# CS · Migrazione da Realgest (interno)

**Uso**: CS interno. **Zero brand in UI** (D-051).

Profilo tipico: agenzia piccola, **Excel/CSV** più che XML. Premium OMNIA ≠ stesso prezzo del vecchio tool (non argomentare in UI).

## Cosa chiedere

1. Export **Excel o CSV** immobili (un foglio, una riga = un annuncio).
2. Export clienti se serve (secondo foglio o file a parte).
3. Se esiste comunque un XML portali → forma **A**.

## Quale forma OMNIA

| File | Forma |
|------|:-----:|
| CSV/Excel immobili | **B** (mappa sul template) |
| XML | **A** |
| Clienti strutturati | **D** |
| Rubrica “nome e cellulare a caso” | **E** |

## Passi CS

1. Scaricare template B. Obbligatori: `title` (≥3), `city`. Vendita: `price`. Affitto: `rent_monthly`.
2. Separatore `;`, UTF-8 BOM (Excel IT).
3. Preview 5 righe in UI prima di confermare.
4. Clienti: se l’Excel ha colonne `Nome / Telefono / Cerca trilocale` → **E**, non D.

## Errori frequenti

- Virgola come separatore (Excel US) → parsing colonne fuse. Riesportare con `;`.
- Prezzi con `€` e punti migliaia: B tenta `_to_float`, ma meglio numeri nudi.
- Nessun import AI immobili in v1: Excel immobili = B, non E.

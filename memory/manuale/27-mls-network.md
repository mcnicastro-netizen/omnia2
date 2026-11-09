# Capitolo 27 · MLS Network

> Collaborazioni multi-agenzia. Versione v1 attiva (anche in fase demo).

## 27.1 · Dove lo trovi
- Nel menu a sinistra: **MLS**.
- Da ImmobilCloud: riquadro della rete / MLS.
- Dentro: Il mio MLS · rete locale · MLS Italia · Partner · Offerte.

## 27.2 · Entrare nel network
- Serve l’account del **titolare**.
- Apri MLS → clicca **Entra nel network**.
- Dopo l’adesione vedi inventario e collaborazioni.

## 27.3 · Quali immobili si condividono
- Entra in rete se la privacy è **pubblica** o **solo MLS**.
- Gli immobili **privati** restano solo in agenzia e non compaiono nelle offerte MLS.

## 27.4 · Partner e offerte
- **Partner**: inviti da accettare o rifiutare.
- **Offerte**: proposte di collaborazione su un immobile condiviso verso un’altra agenzia.

## 27.5 · Cosa vede il pubblico
- Sul lato Cloud c’è una ricerca semplificata degli immobili in rete (zona / prezzo).
- In fase iniziale alcuni contatori possono essere di dimostrazione.

## 27.5b · MLS sul sito white-label dell’agenzia (D-149 · 09-Nov-2026)

Il flag `mls_enabled` (join/leave da menu MLS) governa anche il sito pubblico `/api/p/{slug}/`:

| | MLS on (caso 1) | MLS off (caso 2) |
|---|---|---|
| Home sito | Box ricerca rete + sezione «Immobili dalla Rete MLS Partner» | Solo search portafoglio agenzia |
| Lista | Sidebar ricerca (rete se on) | Search senza chip/rete |
| Embed `/api/mls-box/*` | OK | `mls_not_enabled` |

Non cambia il tema scelto in Brand Studio: cambiano solo i pezzi condizionali. Ogni tema della gallery 8 deve passare QA on|off (D-150). Dettaglio sito: Cap. 8 §8.13.

## 27.6 · Limiti v1
- Academy non inclusa in MLS.
- Immobili privati esclusi dalle collaborazioni.
- Grafica e flussi OMNIA (struttura ispirata alle reti multi-agenzia, non copia di terzi).

## 27.7 · Collegamenti
Cap. 3 Immobili · Cap. 8 Sito web (§8.13) · Cap. 25 Privacy · Cap. 5 Match.

**Versione capitolo**: v1.2 (2026-11-09 · D-149 sito MLS on/off) · v1.1 2026-09-14.

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
- Accettare un’offerta MLS **attiva una collaborazione** sull’immobile: **non** genera da sola richieste documentali né condivide il fascicolo.

## 27.5 · Collaborazioni operative (workspace)
- Nel menu: **Collaborazioni** (`/app/collaborations`) e **Deal** (`/app/deals`); collegamenti anche da MLS.
- Flusso previsto: collaborazione accettata → visita ufficiale → **mini-dossier = solo feedback/rating** post-visita → (eventuale) **richiesta documentale esplicita** → chat contestuale → Deal.
- **Mini-dossier** non è fascicolo immobile né richiesta documenti.
- Documenti condivisi solo su richiesta esplicita, con watermark sul file scaricato e tracciamento; la **revoca** collaborazione chiude anche gli accessi documentali.
- Chat **solo** nel contesto collaborazione (+ visita / Deal se presenti), non chat generica interagenzia.

## 27.6 · Deal
- Il Deal è l’opportunità di compravendita (dopo interesse), distinto da matching e da offerta MLS.
- Owner e partner hanno azioni diverse (proposta / accettazione-rifiuto-controproposta); la UI mostra solo le azioni consentite dal backend.
- Con collaborazione collegata, il Deal richiede collaborazione **attiva**.

## 27.7 · Cosa vede il pubblico
- Sul lato Cloud c’è una ricerca semplificata degli immobili in rete (zona / prezzo).
- In fase iniziale alcuni contatori possono essere di dimostrazione.

## 27.8 · Limiti e stato (nov 2026)
- Academy non inclusa in MLS.
- Immobili privati / non `mls_shared` esclusi dalle collaborazioni.
- PR #240 (branch `cursor/d175-deal-chat-dossier-h4-e393`): remediation aperta — **non mergiata**; restano 3 fix mirati (PDF watermark fail-hard, reject solo su pending, allegato chat same-collab) prima di eventuale approvazione.
- Stripe TEST checkout completo dietro H4 sealed: fuori perimetro senza nuova autorizzazione.

## 27.9 · Collegamenti
Cap. 3 Immobili · Cap. 7 Fascicolo · Cap. 25 Privacy · Cap. 5 Match.

**Versione capitolo**: v1.2 (2026-11-20 · Collaborazioni / mini-dossier / Deal / chat · D-190).

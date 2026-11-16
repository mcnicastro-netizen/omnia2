# VERIFICA MIRATA COERENZA SOGGETTI, PERMESSI E FLUSSI MLS

**Fonte:** `bc-9c71b53d-ff76-40a6-ba5f-8b96c6181433` (OMNIA DS: navy + oro)  
**Prompt msg index:** 23473 · **Report msg:** 23507  
**URL agent:** https://cursor.com/agents/bc-9c71b53d-ff76-40a6-ba5f-8b96c6181433

---

## Prompt commissionato

# OMNIA — VERIFICA MIRATA DELLA COERENZA TRA SOGGETTI, PERMESSI E FLUSSI MLS
## Modalità obbligatoria: ASK — SOLA LETTURA
Questa richiesta NON è un nuovo audit generale del progetto.
Devi effettuare esclusivamente una verifica mirata delle questioni elencate in questo documento, utilizzando il codice e la documentazione già esistenti.
**DIVIETO ASSOLUTO DI MODIFICHE**
Non modificare:
- codice sorgente;
- database, dati o schema;
- configurazioni e dipendenze;
- migrazioni;
- test;
- documentazione;
- branch, commit o file di qualsiasi genere.
Non eseguire operazioni mutative, deploy o implementazioni.
Il risultato deve essere restituito esclusivamente nella chat di Cursor.
---
## 1. Contesto e definizioni fondamentali
OMNIA è una piattaforma gestionale immobiliare white-label, utilizzata da agenzie immobiliari indipendenti.
Le figure previste nel gestionale sono:
- Admin dell'agenzia;
- Agenti e collaboratori.
L'Admin gestisce l'organizzazione, le autorizzazioni e i collaboratori della propria agenzia.
Gli agenti e collaboratori operano secondo le autorizzazioni ricevute.
Esiste inoltre il Super Admin della piattaforma, che corrisponde al Founder e ha responsabilità distinte da quelle degli amministratori delle agenzie.
**Non confondere mai:**
- piattaforma;
- Super Admin;
- agenzia;
- Admin dell'agenzia;
- agente o collaboratore;
- agenzia collaboratrice;
- cliente e proprietario.
Il modello tecnico multi-tenant dovrebbe già rispettare queste distinzioni. Non presumere che sia errato: verifica quanto esiste effettivamente.
### Calendari
Ogni agenzia dispone del proprio calendario.
Il calendario deve essere sempre facilmente accessibile e costituisce uno strumento quotidiano di lavoro per organizzare visite, appuntamenti e impegni.
Nel caso MLS:
- l'agenzia titolare dell'immobile registra l'appuntamento concordato;
- l'appuntamento deve comparire anche nel calendario dell'agenzia collaboratrice;
- entrambe le agenzie devono poterlo consultare secondo le rispettive autorizzazioni;
- non devono esistere due appuntamenti indipendenti e potenzialmente discordanti.
È possibile prevedere un calendario personale del Super Admin, ma deve essere completamente separato dai calendari, dagli appuntamenti e dalle attività delle agenzie.
Il Super Admin non deve comparire come partecipante operativo nelle attività delle agenzie.
---
## 2. Identità degli interlocutori MLS
Una collaborazione MLS può avvenire:
- tra due agenzie;
- tra due agenti appartenenti ad agenzie diverse.
L'interlocutore operativo può quindi essere l'agenzia oppure il singolo agente che la rappresenta.
Il sistema deve mantenere distinte:
- identità dell'agenzia;
- identità dell'agente referente;
- identità degli altri operatori autorizzati.
Il rating MLS appartiene esclusivamente all'agenzia, non al singolo agente.
Verifica che il modello attuale possa rappresentare correttamente entrambe le modalità di collaborazione senza confondere l'identità dell'interlocutore con quella dell'organizzazione.
---
## 3. Flusso richiesta e accettazione della collaborazione MLS
Verifica attentamente il flusso realmente implementato, sia lato frontend sia lato backend.
Il comportamento funzionale concordato è il seguente:
1. L'agenzia o l'agente interessato consulta la scheda MLS dell'immobile.
2. Invia una richiesta di collaborazione, proponendo almeno tre possibili date e orari per la visita.
3. L'agenzia titolare dell'immobile riceve la richiesta.
4. Può accettare una delle date proposte oppure rifiutarle tutte e proporre alternative.
5. Le parti possono anche accordarsi telefonicamente su date differenti.
6. Quando la richiesta di collaborazione viene accettata, si attiva la chat relativa a quella specifica collaborazione, raggiungibile dalla scheda dell'immobile.
7. L'accordo sulla visita viene poi formalizzato operativamente attraverso la registrazione dell'appuntamento nel calendario.
8. La registrazione viene effettuata dall'agenzia titolare dell'immobile.
9. L'appuntamento compare nei calendari delle rispettive agenzie e vengono inviate le notifiche ai soggetti interessati.
**Precisazione fondamentale:** l'attivazione della chat dipende dall'accettazione della richiesta di collaborazione, non dall'avvenuta registrazione dell'appuntamento.
Non confondere:
- accettazione della richiesta di collaborazione;
- accordo definitivo sull'orario della visita;
- registrazione dell'appuntamento in calendario.
Verifica se il flusso tecnico attuale distingue correttamente questi passaggi.
Se non li distingue, segnala esattamente dove si trova la discrepanza. Non proporre modifiche al codice.
---
## 4. Gestione MLS e responsabilità
Le decisioni funzionali sono:
- Solo l'agente responsabile può modificare la scheda MLS del proprio immobile e gestire le relative richieste di collaborazione.
- L'Admin dell'agenzia mantiene la supervisione e riceve le notifiche previste.
- In caso di assenza o uscita dell'agente, quest'ultimo propone un sostituto.
- La sostituzione deve essere approvata dall'Admin dell'agenzia.
- Solo dopo l'approvazione il sostituto acquisisce le autorizzazioni operative.
- Il sostituto autorizzato può gestire anche richieste già aperte e appuntamenti futuri.
Verifica che il sistema non confonda mai Admin dell'agenzia e Super Admin della piattaforma.
---
## 5. Condizioni economiche, preferiti ed esclusioni
Le condizioni economiche standard sono indicate dall'agenzia titolare nella scheda MLS.
Eventuali accordi privati tra agenti o agenzie:
- non devono essere obbligatoriamente registrati;
- non modificano la condizione standard;
- valgono esclusivamente tra le parti interessate;
- non devono essere visibili alle altre agenzie.
La modifica della condizione standard può essere proposta dall'agente responsabile, ma richiede l'approvazione dell'Admin dell'agenzia.
Le agenzie possono inoltre:
- inserire altre agenzie tra i preferiti;
- escludere altre agenzie;
- non avere la stessa agenzia contemporaneamente in entrambe le liste.
L'esclusione riguarda nuove ricerche e nuove collaborazioni, senza interrompere quelle già avviate.
Le agenzie preferite hanno priorità nei risultati MLS, anche quando si ordina per prezzo o data.
Verifica soltanto eventuali confusioni tra responsabilità, visibilità e permessi.
---
## 6. Chat MLS — Riesame delle decisioni G36–G37 e G50–G52
La chat:
- è esclusivamente tra agenzie diverse che collaborano;
- non è una chat interna aziendale;
- non è uno strumento di comunicazione tra operatori e piattaforma;
- è raggiungibile dalla scheda dell'immobile per cui è stata richiesta la collaborazione;
- si attiva soltanto dopo l'accettazione della richiesta;
- è accessibile ai referenti e agli operatori autorizzati delle rispettive agenzie.
OMNIA non deve fornire o gestire chat interne tra collaboratori della stessa agenzia.
Riesamina le precedenti decisioni:
**G36 — Partecipanti**
Referenti e collaboratori autorizzati dalle rispettive agenzie.
**G37 — Storico**
Lo storico rimane disponibile all'agenzia. Un collaboratore che perde l'accesso alla piattaforma non può più accedere alle conversazioni.
**G50 — Archiviazione**
Al termine della collaborazione la chat viene archiviata. La possibilità di riaprirla deve essere valutata in coerenza con G51.
**G51 — Nuova collaborazione**
Una nuova collaborazione tra le stesse agenzie sullo stesso immobile genera una nuova chat. La precedente rimane archiviata.
**G52 — Ricerca**
Ricerca per immobile, agenzia, parole contenute nei messaggi e date.
Verifica la coerenza tra queste decisioni.
In particolare, chiarisci se G50 e G51 siano compatibili oppure se debbano essere interpretate così: le chat archiviate restano consultabili, ma una nuova collaborazione genera sempre una nuova conversazione.
Non considerare G53 (notifiche della chat) come decisione già approvata.
---
## 7. Documenti MLS — Revisione sostanziale delle precedenti decisioni G38–G49
Questa sezione contiene una precisazione del Founder che sostituisce le precedenti interpretazioni sulla condivisione documentale.
**L'agenzia collaboratrice NON deve MAI poter accedere al fascicolo documentale dell'agenzia titolare dell'immobile.**
Non deve poter:
- navigare nel fascicolo;
- visualizzare l'elenco dei documenti presenti;
- aprire direttamente documenti dal fascicolo;
- accedere a documenti tramite autorizzazioni generiche sul fascicolo.
Il documento richiesto dall'agenzia collaboratrice viene allegato materialmente alla collaborazione dall'agenzia titolare, attraverso l'Admin, l'agente, la segreteria o altro personale autorizzato dall'Admin.
Il documento allegato diventa una copia destinata alla specifica collaborazione, non un'apertura del fascicolo originale.
Riesamina quindi le decisioni G38–G49 alla luce di questo principio:
- G38: allegati PDF o immagini, preferibilmente provenienti dai documenti già disponibili all'agenzia.
- G39: non esiste accesso condiviso al fascicolo originale.
- G40: il documento allegato rappresenta la versione trasmessa; eventuali aggiornamenti richiedono un nuovo invio.
- G41: verificare la possibilità di revocare l'accesso alla copia condivisa, tenendo conto che non si possono cancellare copie già scaricate.
- G42: i documenti scaricabili devono avere watermark.
- G43: possono allegare documenti gli operatori autorizzati dall'Admin.
- G44: l'Admin definisce le autorizzazioni generali del personale.
- G45–G47: verificare se le precedenti autorizzazioni speciali e la loro durata siano ancora necessarie e coerenti con il nuovo modello.
- G48: l'Admin riceve le richieste di autorizzazione speciale quando necessarie.
- G49: si tracciano le operazioni significative, come allegati, download e revoche, senza registrare ogni apertura.
Il watermark deve essere discreto ma leggibile, con identificazione dell'agenzia destinataria e data, senza alterare l'originale conservato dall'agenzia titolare.
Non introdurre un sistema di accesso incrociato ai fascicoli.
---
## 8. Rating e contestazioni — Precisazione del Founder
Il rating appartiene all'agenzia.
L'algoritmo di OMNIA determinerà il rating sulla base dei criteri già discussi:
- numero di collaborazioni;
- feedback ricevuti e validati;
- affidabilità delle risposte;
- andamento nel tempo.
La formula e i relativi pesi devono ancora essere configurati.
Il Super Admin:
- non attribuisce manualmente il rating;
- non sostituisce l'algoritmo;
- può cercare di risolvere eventuali controversie tra agenzie, esclusivamente su richiesta esplicita degli interessati.
Verifica che le precedenti decisioni G19–G30 siano coerenti con questa precisazione.
In particolare, non confondere la gestione di una controversia con la determinazione del punteggio reputazionale.
---
## 9. Perimetro della verifica
Non voglio un nuovo audit completo.
Non voglio una revisione generale delle funzionalità di OMNIA.
Non voglio nuove proposte di architettura non richieste.
Voglio soltanto verificare se le decisioni del Founder, comprese le precisazioni contenute in questo documento, sono coerenti con quanto effettivamente presente nel progetto.
Concentrati su:
1. identità dei soggetti;
2. proprietà dei dati;
3. separazione tra agenzie;
4. multi-tenancy;
5. ruoli e autorizzazioni;
6. calendari;
7. flusso MLS di richiesta e accettazione;
8. attivazione della chat;
9. gestione degli allegati;
10. rating e controversie.
## 10. Formato obbligatorio del risultato
Restituisci un rapporto sintetico con queste sole sezioni:
### A. Anomalie effettive
Per ogni anomalia indica:
- decisione interessata;
- comportamento attuale riscontrato;
- comportamento atteso;
- file, componenti, endpoint o modelli coinvolti;
- eventuale gravità.
### B. Decisioni coerenti
Indica sinteticamente quali aspetti risultano già rispettati.
### C. Contraddizioni tra decisioni
Segnala soltanto contraddizioni reali, non differenze terminologiche irrilevanti.
### D. Questioni non verificabili
Indica ciò che non è possibile confermare dal codice o dalla documentazione disponibile.
### E. Decisioni G36–G52
Fornisci una tabella con:
- numero;
- decisione;
- confermata, da correggere o da chiarire;
- eventuale motivazione.
### F. Sintesi finale
Elenca soltanto le questioni che richiedono una decisione del Founder.
Non chiedere al Founder di ripetere decisioni già espresse.
Non trasformare una decisione già concordata in una nuova domanda.
Non proporre implementazioni.
**Il tuo compito è verificare, non riprogettare.**

---

## Report

Verifica sul codice di `origin/main` (app identica a questo checkout) e su `memory/DECISIONS.md`. Le etichette G36–G52 **non** risultano nel repo: le tratto come decisioni di questa conversazione. G1–G30 in `memory/AUDIT_ARCHITETTURA_NOTE.md` sono **cestino/backup**, non rating: numerazione diversa, non le mescolo.

---

### A. Anomalie effettive

1. **Flusso MLS (richiesta collaborazione + 3 date)**  
   **Oggi:** `POST /app/mls/offers` crea un’offerta **sul proprio** immobile verso un’altra agenzia (`mls.py` 439–453: `property_id` con `agency_id == aid`). `MlsPage.jsx` elenca e **risponde** (accept/reject), senza date.  
   **Atteso:** richiesta sul listing **altrui**, tre slot, accettazione/alternative/telefono.  
   **Gravità:** alta — mestiere invertito, i tre passi (accettazione collaborazione / orario / calendario) **non esistono** come stati distinti.

2. **Calendario agenzia e appuntamento unico su due tenant**  
   **Oggi:** nessun insert su `calendar_events`; la dashboard **legge** quella collection (`dashboard.py` 120–126, 536–554). Le visite CRM sono `activities` per `agency_id` (`activities.py`). Nessuna pagina calendario. D-138: calendario slot condiviso **fuori scope v1**.  
   **Atteso:** un appuntamento, titolare lo registra, visibile anche al collaboratore.  
   **Gravità:** alta sul requisito MLS; oggi non c’è calendario operativo.

3. **Super Admin come ruolo MLS operativo**  
   **Oggi:** `require_roles(..., "super_admin")` su dashboard, join/leave, inventory, partners, offers, respond (`mls.py` 152, 237, 265, 293, 332, 368, 442, 479). Join MLS è `agency_admin` **o** `super_admin`. Tenant guard: `super_admin` bypass (`tenant_guard.py` 59). Cabina: `POST /bridge/impersonate` (`founder_bridge.py` 724).  
   **Atteso:** Super Admin ≠ Admin agenzia; non partecipa alle attività delle agenzie.  
   **Gravità:** media sul join/offer; impersonation è strumento Ops, non calendario, ma lo stesso utente può operare nel tenant.

4. **Solo l’agente responsabile modifica scheda MLS / richieste**  
   **Oggi:** `PATCH` immobile: qualsiasi `agency_admin` o `agent` della sede (`properties.py` 456–461). `listing_agent_id` si imposta in create (411), **nessun check** in update. `respond_offer`: solo `agency_admin` e `super_admin`, **non** l’agent (`mls.py` 475–479).  
   **Atteso:** mutazioni MLS = responsabile; Admin supervisione/notifiche; sostituto dopo approvazione Admin.  
   **Gravità:** media. Non c’è flusso sostituto.

5. **Identità interlocutore MLS**  
   **Oggi:** `mls_partners` e `mls_requests` sono `agency_a`/`agency_b`, `from_agency_id`/`to_agency_id`. `listing_agent_id` è sul listing, non sulla collaborazione.  
   **Atteso:** agenzia **e** agente referente distinti.  
   **Gravità:** bassa sul modello User/Agency (esistono); alta sul **record di collaborazione**, che è solo tenant.

6. **Preferiti / esclusioni tra agenzie**  
   **Oggi:** `favorites` è B2C ImmobilCloud (`immocloud/favorites.py`). `mls_partners` è partnership bilaterale, non preferito/escluso.  
   **Atteso:** liste agenzia, mutuamente esclusive, esclusione solo su **nuove** collaborazioni.  
   **Gravità:** funzione assente, non un comportamento contrario già in produzione.

Non classifico come anomalia «il codice sbaglia» ciò che **non è stato implementato** (chat MLS, rating, watermark allegati, condizioni economiche). Sta in D e nella tabella E.

---

### B. Decisioni coerenti

- Tenant: `active_agency_id`, niente fallback `agency_ids[0]` (`tenant.py`). Query CRM con `agency_id`.
- Figure: `UserRole` distingue `super_admin` / `agency_admin` / `agent` (`user.py`). Founder Ops è un altro albero (`founder_ops.py`, Cabina).
- Fascicolo **non** è condiviso cross-agenzia: `_get_property` filtra `agency_id` (`fascicolo.py` 54–67). Allineato a **G39** (nessun accesso al fascicolo del titolare).
- Nessuna chat interna di sede (HAL è assistente AI, D-040/D-075) — coerente con «OMNIA non gestisce chat intra-agenzia».
- Isolamento Client/owner: projection MLS senza `owner` (`mls.py` `_prop_projection`).
- Notifiche in-app per-utente esistono (`notifications`); non sono ancora il flusso MLS.
- `listing_agent_id` esiste come campo; l’identità agente **può** essere rappresentata, non è usata come ACL MLS.

---

### C. Contraddizioni tra decisioni

1. **Rating: persona vs agenzia.** Specifica MLS 1.0 §2.3: rating dell’**operatore**. Questo documento §2 e §8: rating **solo dell’agenzia**. Vale **questo** testo (precisazione Founder). Non va riletto come domanda.

2. **G50 vs G51.** Non si contraddicono se: chat archiviata **resta consultabile** (G37, G50); **nuova** collaborazione stesso immobile/stesse agenzie = **nuova** conversazione (G51); **niente riapertura operativa** della vecchia. G50 «riaprire» si interpreta così, non come secondo thread vivo.

3. **G45–G47 vs G39.** Autorizzazioni speciali/durata sul fascicolo **non** sono più coerenti: il collaboratore non entra nel fascicolo. Restano G43–G44 (chi può **allegare copie** alla collaborazione) e G41 (revoca della copia, sapendo che il download già fatto non si cancella).

4. **D-138 vs calendario MLS.** D-138 mette il calendario condiviso fuori scope v1 (B2C). Il requisito MLS chiede un appuntamento unico su due agenzie. Non è la stessa decisione: vanno tenute **separate** (B2C vs B2B).

Nessun conflitto G36/G37/G52 tra loro. G53 notifiche chat: **non approvata**, non la uso.

---

### D. Questioni non verificabili

- G19–G30 **rating** (formula, contestazioni): non sono in `DECISIONS.md`; nel repo G1–G30 = cestino. Codice rating MLS: assente. Super Admin **non** assegna punteggi (non c’è nulla da assegnare).
- Chat MLS, allegati-copia, watermark destinatario+data, tre slot visita, follow-up, preferiti/esclusioni B2B, condizioni economiche standard vs accordo privato, flusso sostituto: **non nel codice**.
- Comportamento produzione Railway.
- Se l’impersonation Cabina è usata in MLS: non verificabile da qui; esiste solo il meccanismo.

---

### E. Decisioni G36–G52

| # | Decisione | Esito | Motivazione |
|---|---|---|---|
| G36 | Partecipanti: referenti e autorizzati delle due agenzie | **Confermata** | Coerente con ruoli sede; in codice la collab è solo `agency_id`. |
| G37 | Storico all’agenzia; chi perde accesso non legge più | **Confermata** | Allineata a membership JWT; chat non esiste. |
| G38 | Allegati PDF/immagini da documenti già in agenzia | **Confermata** | Copia verso collab, non share fascicolo. |
| G39 | Nessun accesso al fascicolo originale | **Confermata** | Già vero in `fascicolo.py`. |
| G40 | Copia = versione inviata; update = nuovo invio | **Confermata** | — |
| G41 | Revoca accesso copia; download già fatti restano | **Confermata** | Limite di fatto, non di prodotto. |
| G42 | Watermark agenzia destinataria + data | **Confermata** | Watermark attuale = staging «Render virtuale OMNIA», altro scopo. |
| G43 | Allegano gli autorizzati dall’Admin | **Confermata** | — |
| G44 | Admin definisce permessi generali del personale | **Confermata** | Oggi ruoli grossi, niente ACL fine. |
| G45–G47 | Autorizzazioni speciali e durata sul fascicolo | **Da correggere** | Superate da G39; non servono per il collaboratore. |
| G48 | Admin riceve richieste di autorizzazione speciale | **Da correggere** | Stesso motivo, salvo un eventuale permesso «può allegare in MLS» in G44. |
| G49 | Audit allegati/download/revoche, non ogni apertura | **Confermata** | — |
| G50 | Fine collab → chat archiviata | **Confermata** | Consultabile, non «riaperta» come thread vivo. |
| G51 | Nuova collab → nuova chat; precedente archiviata | **Confermata** | Compatibile con G50 come sopra. |
| G52 | Ricerca immobile / agenzia / testo / date | **Confermata** | Include anche archiviate (coerente G37). |

---

### F. Sintesi finale

Nessuna domanda nuova al Founder. Già deciso in questo testo: rating = **agenzia**; Super Admin ≠ operatore MLS; fascicolo titolare **chiuso**; chat solo inter-agenzia dopo accettazione collaborazione; un appuntamento, due viste calendario; G50/G51 = archivio consultabile + conversazione nuova.

Unico scarto da registrare in progettazione (non da rivotare): **G45–G48** sul fascicolo condiviso non applicarle; restano permessi Admin su **chi allega copie** (G43–G44).

Il progetto **oggi** isola bene i tenant e il fascicolo; **non** realizza il flusso MLS concordato (richiesta, chat, calendario unico, ACL agente responsabile). Super Admin risulta ancora nei `require_roles` MLS.

Nessuna implementazione. Mi fermo.

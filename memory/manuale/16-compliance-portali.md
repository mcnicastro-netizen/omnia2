# Capitolo 16 · Compliance Portali — validatore HARD/SOFT

> **Cosa trovi in questo capitolo**
> Il **Compliance Validator** è il "buttafuori normativo" di OMNIA: prima che un immobile finisca sui portali (o sul feed pubblico), passa da una serie di check tecnici che verificano la presenza dei campi richiesti dalla normativa italiana e dai portali stessi. Il capitolo copre: il contesto normativo (D.Lgs 192/2005 APE, AGCM trasparenza prezzi), l'architettura del validatore (funzioni pure senza DB), le **5 regole HARD** con i **7 codici** che generano, le **4 regole SOFT** che segnalano qualità senza bloccare, il mapping campi-immobile → regola, la differenza fra feed pubblico e sync portale, l'esclusione automatica degli immobili con privacy L3/L4, e i limiti onesti v1.
>
> **Cap. 16 vs Cap. 6**: Cap. 6 spiega **come cliccare** (attiva portale, sync, wizard). Cap. 16 spiega **perché e quali campi** (regole, codici errore, contesto normativo). Non ripete l'operativo.

**Cosa NON è (D-051 onestà — regola cardine)**
- Non è un **legal advisor**. Non fornisce interpretazione giuridica sui casi limite. Cita la normativa italiana come **contesto** (D.Lgs 192/2005, AGCM trasparenza prezzi) ma non sostituisce un consulente legale in caso di dubbio (es: quando un immobile è veramente esente APE).
- Non è una **pagina UI dedicata**. Non esiste `CompliancePage.jsx` standalone — il modulo è **inline** nella pagina Publishing (`PublishingPage.jsx`) sotto forma di **modale compliance** aperta dal bottone *"Vedi compliance"* accanto a ogni portale.
- Non è **configurabile per agenzia**. Le soglie (`MIN_PHOTOS=3`, `MIN_TITLE_CHARS=10`, `MIN_DESCRIPTION_CHARS=50`) sono **hardcoded** nel codice. Non ci sono impostazioni per personalizzarle.
- Non **riscrive automaticamente** i campi mancanti. Segnala il problema — la correzione la fai tu manualmente dalla scheda immobile (Cap. 3).
- Non gestisce **portali extra-italiani** (Zillow, Rightmove, ecc.). Le regole HARD sono progettate sulla normativa italiana e sugli standard dei portali IT.
- Non è un **audit trail**: le violazioni non sono salvate storicamente in una collezione dedicata. Vengono ricalcolate on-the-fly ogni volta che chiami l'endpoint compliance.

---

## 16.1 · Perché esiste il validatore (contesto normativo)

**In una frase**
Se pubblichi un immobile senza APE, senza prezzo trasparente o con meno di 3 foto, rischi **sanzioni AGCM** e/o il **rifiuto dei portali** che rimbalzano l'annuncio (o peggio, ti bannano). Il Compliance Validator ti dice cosa manca **prima** che il portale te lo faccia notare.

**Cornice normativa italiana (contesto — non consulenza legale)**
- **D.Lgs 192/2005**: obbligo di dichiarare la **classe energetica (APE)** in ogni annuncio commerciale immobiliare. Modificato dal D.Lgs 48/2020 (Ecobonus) e successive integrazioni.
- **Delibera AGCM sulla trasparenza dei prezzi**: obbligo di indicare in modo chiaro **prezzo** (vendita) o **canone mensile** (affitto). Ammesso *"prezzo su richiesta"* (`price_on_request=true`) per casi specifici (immobili di lusso, aste, ecc.).
- **Standard dei portali IT** (Immobiliare.it, Idealista, Casa.it, Subito, Bakeca, ecc.): **minimo 3 foto** per annuncio pubblico è oggi lo standard de-facto. Sotto le 3 foto, i portali retrocedono la posizione nei risultati di ricerca (o rifiutano l'ingest, dipende dal portale).
- **IPE (Indice Prestazione Energetica)** numerico: strettamente **raccomandato**, non bloccante di legge (viene marcato SOFT nel nostro validatore).

**Il ruolo di OMNIA**
OMNIA implementa **il minimo comune denominatore** delle regole IT: se passa il validatore OMNIA, l'annuncio è a norma per **la maggior parte** dei portali IT. Alcuni portali possono avere requisiti aggiuntivi specifici (es. IG richiede foto HTTPS pubbliche — cfr. Cap. 15) che OMNIA gestisce **prima** dell'ingest lato portale (Cap. 6 §sync).

---

## 16.2 · Architettura del validatore (funzioni pure, no DB)

**A cosa serve capirlo**
Il validatore è progettato per essere **veloce e testabile**: nessuna chiamata DB, nessuna dipendenza esterna, solo funzioni pure che leggono il dizionario `property` (JSON) e restituiscono un risultato strutturato.

**Dove vive il codice**
`backend/shared/validators/compliance.py` — file singolo, ~170 righe.

**Le 3 API pubbliche**
1. **`validate_property(prop: dict) → dict`**
   Ritorna il risultato completo:
   ```json
   {
     "publishable": true,
     "hard_violations": [],
     "soft_warnings": ["title_too_short", "ipe_missing"]
   }
   ```
2. **`is_publishable(prop: dict) → (bool, list[str])`**
   Wrapper backwards-compat: `(publishable, hard_violations_list)`. Usato dal feed generator (`publishing.py`) e dal sync engine (`sync_engine.py`).
3. **`summarize_agency_compliance(properties: list[dict]) → dict`**
   Aggregatore per la modale in UI — ritorna `total`, `publishable`, `with_warnings`, `blocked`, `top_hard_reasons` (top 5), `top_soft_reasons` (top 5).

**Dove viene chiamato**
- **Feed generator** (`publishing.py` linea 553): filtra gli immobili prima di comporre il feed XML pubblico che i portali PULL scaricano.
- **Sync engine** (`sync_engine.py` linea 165-175): filtra la lista prima di ogni sync manuale/schedulato + genera il messaggio `blocked_by_compliance:{count}` nel `sync_log`.
- **Modale compliance dashboard** (`publishing.py` linea 255-273): endpoint `GET /api/app/publishing/connections/{conn_id}/compliance` chiamato al click sul bottone *"Vedi compliance"* accanto a un portale attivo.

**Nessuna persistenza dei risultati**
I risultati **non vengono salvati**. Ogni chiamata rilancia il check da zero sulla lista immobili dell'agenzia. Vantaggio: sempre sincronizzato con lo stato attuale. Costo: nessun trend storico (*"6 mesi fa avevi 20 immobili bloccati, oggi 5"* — non lo sappiamo).

---

## 16.3 · Le 5 regole HARD — panoramica

**A cosa serve capirlo**
Le regole HARD **bloccano** l'immobile: se anche una sola fallisce, l'immobile **non entra** nel feed pubblico e **non viene sincronizzato** con i portali.

**Le 5 regole business → i 7 codici che possono generare**

| # | Regola business | Campo(i) `property` | Codici generati |
|:-:|-----------------|---------------------|-----------------|
| 1 | Prezzo o canone presente | `operation`, `price`, `rent_monthly`, `price_on_request` | `missing_price` |
| 2 | Superficie in mq > 0 | `surface_sqm` | `missing_surface` |
| 3 | Classe APE valida | `energy.energy_class` | `missing_energy_class`, `invalid_energy_class` |
| 4 | Almeno 3 foto con URL | `photos[].url` | `less_than_3_photos`, `no_valid_photo_url` |
| 5 | Città + Provincia | `city`, `province` | `missing_address` |

**Perché sono 5 regole ma 7 codici**
- La regola APE emette 2 codici distinti (`missing` se mancante, `invalid` se presente ma fuori dalle 14 classi ammesse).
- La regola foto emette 2 codici distinti (`less_than_3_photos` se meno di 3 foto, `no_valid_photo_url` se ce ne sono ma nessuna ha URL valido).

**Il flag `publishable`**
Se `hard_violations` è vuota → `publishable: true`.
Se anche un solo codice è presente → `publishable: false`.

---

## 16.4 · HARD prezzo/canone — sale vs rent vs "prezzo su richiesta"

**A cosa serve capirlo**
Questa regola è la più sottile perché **cambia comportamento** in base al tipo di contratto (`operation`).

**Logica esatta (`compliance.py:52-63`)**
```python
def _has_price(prop):
    op = (prop.get("operation") or "sale").lower()
    if op == "rent":
        rent = prop.get("rent_monthly")
        return isinstance(rent, (int, float)) and rent > 0
    # sale or auction
    price = prop.get("price")
    if isinstance(price, (int, float)) and price > 0:
        return True
    if prop.get("price_on_request") is True:
        return True
    return False
```

**In pratica**

| Scenario | `operation` | Campi presenti | HARD? |
|----------|:-:|----------------|:-:|
| Vendita con prezzo esplicito | `sale` | `price: 250000` | ✅ pass |
| Vendita "prezzo su richiesta" | `sale` | `price_on_request: true` | ✅ pass |
| Vendita senza prezzo né flag | `sale` | (nessuno dei due) | ❌ **`missing_price`** |
| Vendita `price: 0` | `sale` | `price: 0` | ❌ **`missing_price`** |
| Affitto con canone esplicito | `rent` | `rent_monthly: 800` | ✅ pass |
| Affitto senza canone | `rent` | (nessuno) | ❌ **`missing_price`** ⚠️ |
| Asta con prezzo base | `auction` | `price: 100000` | ✅ pass |

**⚠️ Onestà D-051 · label vs codice**
Il backend emette **sempre** il codice `missing_price` — anche per gli affitti senza `rent_monthly`. In UI il file `PublishingPage.jsx` ha una label `REASON_LABELS.missing_rent = "Canone mensile mancante"`, ma **il backend non emette mai `missing_rent`**. Quella label è una **ghost label** (definita ma inutilizzata). Quindi in schermata vedrai *"Prezzo mancante"* anche per un affitto — leggibilmente impreciso, ma è quello che c'è oggi (v1).

**Cosa NON blocca**
- Presenza di **entrambi** `price` e `rent_monthly` insieme (permesso — pass).
- Prezzo negativo o non-numerico: `isinstance(price, (int, float))` filtra, quindi stringhe come `"€250.000"` sono trattate come mancanti (attenzione all'import CSV/XML — cfr. Cap. 14).

---

## 16.5 · HARD superficie e indirizzo

### HARD superficie (`missing_surface`)
- Campo controllato: `prop.get("surface_sqm")`
- Regola: `isinstance(s, (int, float)) and s > 0`
- Se manca o è ≤ 0 → codice `missing_surface`
- **Nessuna distinzione** tra superficie commerciale e utile in v1: si guarda solo `surface_sqm`. Se hai `surface_utile` ma non `surface_sqm`, l'immobile risulta non pubblicabile.

### HARD indirizzo (`missing_address`)
- Campi controllati: `city` **AND** `province`
- Regola: entrambi non-vuoti dopo `strip()`
- Se anche uno solo manca → codice `missing_address`
- **NON** vengono controllati: via, civico, CAP, coordinate GPS, quartiere.
- Motivo: la maggior parte dei portali IT richiede **almeno** città+provincia per l'ingest. L'indirizzo preciso è "raccomandato" ma non bloccante lato portale.

---

## 16.6 · HARD APE · le 14 classi ammesse

**A cosa serve capirlo**
Se pubblichi senza APE (o con APE non riconosciuta), l'immobile è bloccato per legge (D.Lgs 192/2005). Il validatore controlla che il campo esista **E** che il valore sia una delle **14 classi ammesse** definite in `VALID_ENERGY_CLASSES`.

**Le 14 classi ammesse (`compliance.py:20-24`)**

| Classe | Significato |
|:-:|-------------|
| `A4`, `A3`, `A2`, `A1`, `A` | Alta efficienza (A4 = massima) |
| `B`, `C`, `D`, `E`, `F` | Efficienza decrescente |
| `G` | Minima efficienza (edifici vecchi non isolati) |
| `EXEMPT_IN_PROGRESS` | Esente perché **attestato in preparazione** (edificio nuovo o ristrutturato in attesa dell'APE ufficiale) |
| `EXEMPT_NOT_APPLICABLE` | Esente perché **normativamente non applicabile** (es: rudere non abitabile, immobile agricolo non riscaldato) |

**Come si compila**
Dalla scheda immobile (Cap. 3) — sezione **Efficienza energetica** — scegli dal dropdown la classe. Le 14 opzioni sono quelle sopra. La classe viene salvata in `property.energy.energy_class` (uppercase).

**I 2 codici distinti**
- **`missing_energy_class`**: `property.energy.energy_class` è vuoto, `null`, o non esiste.
- **`invalid_energy_class`**: c'è un valore ma **non è** in `VALID_ENERGY_CLASSES` (es: qualcuno ha scritto `"H"` o `"A5"` manualmente via import XML, cfr. Cap. 14 §14.4 tabella `ENERGY_CODE_MAP`).

**Casi limite (onestà D-051)**
- Se metti `EXEMPT_IN_PROGRESS` ma poi non aggiorni quando l'APE arriva → l'immobile resta pubblicato ma stai violando la legge. **OMNIA non fa promemoria** per aggiornare l'APE (limite v1).
- Se il tuo cliente ti dice *"esente"* senza specificare il motivo → devi decidere tu quale delle due `EXEMPT_*` usare. Non c'è UI di aiuto.

---

## 16.7 · HARD foto · `less_than_3_photos` vs `no_valid_photo_url`

**A cosa serve capirlo**
La regola foto emette **due codici distinti** per aiutarti a capire **cosa** correggere.

**Il conteggio (`compliance.py:32-45`)**
```python
def _photos_count(prop):
    photos = prop.get("photos") or []
    return len([p for p in photos if isinstance(p, dict) and p.get("url")])

def _first_photo_ok(prop):
    photos = prop.get("photos") or []
    for p in photos:
        if isinstance(p, dict) and p.get("url"):
            return True
    return False
```

**I 3 scenari**

| `photos` array | Codici generati |
|----------------|-----------------|
| `[]` (vuoto) | `less_than_3_photos` + `no_valid_photo_url` |
| `[{"url": "https://..."}, {"url": "https://..."}]` (2 valide) | `less_than_3_photos` (ma non `no_valid_photo_url`) |
| `[{"caption": "foto1"}, {"caption": "foto2"}, {"caption": "foto3"}]` (3 senza URL) | `less_than_3_photos` + `no_valid_photo_url` |
| `[{"url": "https://..."}, {"url": "https://..."}, {"url": "https://..."}]` (3 valide) | ✅ pass |

**Perché due codici**
- Se hai **2 foto valide** → devi solo aggiungerne una terza.
- Se hai **3+ entry ma nessuna con URL** (caso raro post-import XML rotto) → il problema è tecnico, non di quantità.

**MIN_PHOTOS costante**
`MIN_PHOTOS = 3` hardcoded. Non configurabile per agenzia in v1.

---

## 16.8 · Le 4 regole SOFT · warning di qualità

**A cosa serve capirlo**
Le SOFT **non bloccano** la pubblicazione — sono suggerimenti di qualità che ti aiutano a fare annunci migliori (più visualizzazioni, più contatti, migliore posizionamento).

**Le 4 regole SOFT (`compliance.py:113-123`)**

| Codice | Regola | Costante |
|--------|--------|:-:|
| `title_too_short` | `len(title.strip()) < 10` | `MIN_TITLE_CHARS=10` |
| `description_too_short` | `len(description.strip()) < 50` | `MIN_DESCRIPTION_CHARS=50` |
| `rooms_not_specified` | `rooms` è `None` o `0` | — |
| `ipe_missing` | `energy.ipe` non presente | — |

**In UI**
Le SOFT compaiono come **badge ambra** ("con warning") nella modale compliance, ma l'immobile è comunque `publishable: true` e finisce nel feed. Il conteggio è nella card *"Con warning"*.

**Perché queste 4 e non altre**
- **Titolo/descrizione troppo corti**: minano il posizionamento SEO e i portali retrocedono.
- **Rooms**: campo molto usato dai filtri utente sui portali — se manca, riduci il match potenziale.
- **IPE numerico**: raccomandato dagli aggiornamenti recenti al D.Lgs 192/2005 come complemento della classe APE (kWh/m²·anno). Non bloccante legalmente perché la sola classe è sufficiente per l'obbligo minimo.

**Cosa NON è SOFT** (D-051)
- Foto principale a bassa risoluzione (non controllato).
- Prezzo troppo basso/alto rispetto a media zona (non controllato — richiederebbe API market).
- Descrizione con refusi (non controllato).
- Coordinate GPS mancanti (non controllato).

---

## 16.9 · Mapping campi immobile → regola compliance

**A cosa serve capirlo**
Se apri la scheda di un immobile bloccato e vuoi sapere *"dove correggo?"*, questa tabella ti mappa 1:1 il codice di violazione al campo esatto della scheda (o del JSON `property`).

**Mapping HARD**

| Codice | Campo scheda (Cap. 3) | Campo JSON | Correzione |
|--------|----------------------|------------|------------|
| `missing_price` | Sezione Prezzo → Prezzo di vendita (o Canone mensile per affitti) | `price` (sale) / `rent_monthly` (rent) / `price_on_request: true` | Inserisci un numero > 0 oppure spunta *"prezzo su richiesta"* |
| `missing_surface` | Sezione Caratteristiche → Superficie (mq) | `surface_sqm` | Inserisci un numero > 0 (in mq) |
| `missing_energy_class` | Sezione Efficienza energetica → Classe energetica | `energy.energy_class` | Scegli una delle 14 classi (A4/A3/A2/A1/A/B/C/D/E/F/G/EXEMPT_IN_PROGRESS/EXEMPT_NOT_APPLICABLE) |
| `invalid_energy_class` | Idem | Idem | Idem — il valore attuale non è in `VALID_ENERGY_CLASSES` (probabile bug import) |
| `less_than_3_photos` | Sezione Foto (Cap. 3 §foto) | `photos: [...]` | Carica almeno 3 foto (drag & drop o upload) |
| `no_valid_photo_url` | Idem | `photos[].url` | Le foto hanno metadati ma URL non risolti — ricarica |
| `missing_address` | Sezione Localizzazione → Città + Provincia | `city`, `province` | Inserisci entrambi (obbligatori) |

**Mapping SOFT**

| Codice | Campo scheda | Campo JSON | Correzione |
|--------|--------------|------------|------------|
| `title_too_short` | Header → Titolo annuncio | `title` | Scrivi almeno 10 caratteri (es: *"Trilocale via Roma, ristrutturato"*) |
| `description_too_short` | Sezione Descrizione | `description` | Scrivi almeno 50 caratteri (usa HAL Agent → Migliora descrizione se serve — Cap. 10) |
| `rooms_not_specified` | Sezione Caratteristiche → Locali | `rooms` | Inserisci un numero > 0 |
| `ipe_missing` | Efficienza → IPE (kWh/m²·anno) | `energy.ipe` | Inserisci il valore numerico dall'APE ufficiale |

[SCREEN: compliance-mapping-campi]

---

## 16.10 · Feed pubblico vs sync portale — dove filtra il validatore

**A cosa serve capirlo**
Il validatore è **lo stesso** in entrambi i casi, ma il *"cosa succede se un immobile è bloccato"* cambia leggermente.

**Feed pubblico (PULL)**
- Endpoint: `GET /publishing/feed/{portal_slug}` (Cap. 6 §feed).
- Il feed generator itera le properties dell'agenzia e **le filtra** con `is_publishable(p)[0]`.
- Gli immobili bloccati **non entrano nel XML** — spariscono silenziosamente dal feed.
- Il portale che scarica il feed vede solo gli immobili pubblicabili.
- **Nessun log per-immobile-escluso** in v1: se ti aspetti di vedere 50 immobili sul portale ma ne vedi 40, apri la modale compliance per capire quali 10 sono bloccati.

**Sync portale (PUSH — M2.6c/d)**
- Endpoint: `POST /publishing/connections/{id}/sync` (Cap. 6 §sync).
- Il sync engine (`sync_engine.py`) filtra la lista prima di iniziare le chiamate al portale.
- Se ci sono immobili bloccati, il campo `error_message` del `sync_log` diventa `blocked_by_compliance:12` (dove 12 è il numero di immobili filtrati).
- Il sync **prosegue lo stesso** sugli immobili pubblicabili — non è un fail globale.

**Modale compliance (UI)**
- Endpoint: `GET /publishing/connections/{conn_id}/compliance`.
- Ritorna il summary aggregato + `blocked_details` (primi 20 immobili bloccati con motivo).
- **Non filtra** — solo mostra lo stato. Ricalcola tutto on-the-fly.

[SCREEN: compliance-modale-hard]

---

## 16.11 · Privacy L3/L4 esclusi dal feed pubblico

**A cosa serve capirlo**
Un immobile può essere **compliance-clean** (5 HARD tutti pass) e comunque **non finire** sul feed pubblico. Il motivo: la sua privacy è L3 o L4.

**Recap privacy immobile (dettaglio in Cap. 3 §privacy)**
- **L1 · Pubblico completo**: dati anagrafici visibili, foto pubblicate, indirizzo pieno.
- **L2 · Pubblico anonimo**: come L1 ma senza dati proprietario.
- **L3 · Riservato agenzia**: **visibile solo agli agenti dell'agenzia**, mai a portali/utenti B2C.
- **L4 · Off-market**: **visibile solo al team ristretto** (owner + agenti autorizzati), mai al feed.

**Cosa succede tecnicamente**
Il feed generator (`publishing.py`) applica **due filtri in cascata**:
1. Filtro privacy: escludi tutti gli immobili con `is_private_listing: true` o `visibility: "internal"` (che corrispondono a L3/L4).
2. Filtro compliance: escludi quelli con `hard_violations` non vuote.

Un immobile in L4 non arriva neanche al secondo filtro — è già escluso dal primo.

**In sintesi**
Se un immobile non appare sui portali, controlla nell'ordine:
1. È **privacy L3/L4**? (scheda immobile → toggle *"Visibilità pubblica"*)
2. È **bloccato compliance**? (modale compliance dashboard)
3. Il **portale è attivo**? (Cap. 6 §attivazione)

---

## 16.12 · Come si legge la modale compliance

**Da dove parti**
1. Vai in **Publishing** (sidebar → *"Portali & Publishing"*).
2. Cerca la card del portale attivo (es. Subito, Bakeca).
3. Clic sul bottone **"Vedi compliance"** (`data-testid="portal-compliance-{portal_slug}"`).

**Cosa vedi nella modale (`PublishingPage.jsx` linee 281-340)**

- **Header**: nome portale + close button.
- **Riga metriche** (4 box):
  - *"Totale"*: quanti immobili in totale nell'agenzia.
  - *"Pubblicabili"*: quanti passano tutti gli HARD.
  - *"Bloccati"*: quanti hanno almeno un HARD.
  - *"Con warning"*: quanti sono pubblicabili ma hanno SOFT.
- **Top motivi HARD** (se ce ne sono): elenco dei 5 codici più frequenti con conteggio, tradotti con `REASON_LABELS` in italiano.
- **Immobili bloccati** (primi 20): tabella con titolo immobile + elenco motivi bloccanti separati da `·`.

**Cosa NON c'è**
- Bottone *"Correggi tutto"* — nessuna automazione.
- Link diretto *"Vai alla scheda immobile"* dalla riga bloccata — devi navigare a mano.
- Export CSV della lista bloccati per lavoro offline.
- Filtro per tipo di violazione.

[SCREEN: compliance-soft-warnings]

---

## 16.13 · Limiti onesti v1 (D-051)

**Cosa il modulo Compliance NON fa oggi**

- ❌ **Nessuna pagina UI dedicata**. La compliance è **inline** nella pagina Publishing come modale. Non c'è `/it/app/compliance` o simile.
- ❌ **`api_push` è `simulated_push`**. Il campo `action_status` del sync per portali `api_push` (M2.6c/d wizard) restituisce `simulated_push` — nessuna vera chiamata al portale. Il compliance filter agisce comunque prima. Cfr. Cap. 6 §sync.
- ❌ **Nessuna sync-log UI dedicata**. Il log dei sync esiste in `sync_log` collection ma non c'è pannello UI che lo mostra. Si accede via API o super_admin dal DB.
- ❌ **Ghost label `missing_rent`**. Il frontend ha `REASON_LABELS.missing_rent = "Canone mensile mancante"`, ma il backend **non emette mai** questo codice — usa sempre `missing_price` anche per gli affitti. In UI vedrai *"Prezzo mancante"* anche per un affitto senza canone.
- ❌ **Nessun bottone "Sospendi sync"**. In UI l'endpoint `PATCH /connections/{id}` esiste (per aggiornare status → `paused`) ma **non c'è bottone** — l'agente vede solo *"Attiva sync automatico"* e *"Disconnetti"*.
- ❌ **Legacy PORTAL_CATALOG vs CATALOG_SEED**. Nel codice `publishing.py` c'è ancora una variabile legacy `PORTAL_CATALOG` (M2.6a) affiancata dal nuovo `CATALOG_SEED` (M2.6d). **Idealista NON è in v1** — cfr. Cap. 6 §catalogo.
- ❌ **Nessun trend storico**. Il validatore è stateless — non sa se ieri avevi 3 bloccati e oggi 5. Non c'è dashboard *"andamento compliance"*.
- ❌ **Nessun promemoria APE**. Se metti `EXEMPT_IN_PROGRESS` e poi ti dimentichi di aggiornare quando arriva l'APE ufficiale, OMNIA non ti manda notifiche.
- ❌ **Nessun bottone "Correggi" dalla modale**. La modale mostra *"Immobili bloccati"* ma non ha un link cliccabile che apre la scheda immobile. Devi copiare il titolo e cercarlo a mano in Immobili.
- ❌ **Soglie hardcoded**. `MIN_PHOTOS=3`, `MIN_TITLE_CHARS=10`, `MIN_DESCRIPTION_CHARS=50` non sono configurabili per agenzia.
- ❌ **Nessun controllo semantico**. Un titolo di 10 caratteri *"aaaaaaaaaa"* passa il SOFT. La qualità testuale non è misurata.
- ❌ **Nessun audit trail delle correzioni**. Se correggi un immobile bloccato e diventa pubblicabile, non c'è log *"L'utente X ha risolto Y violazioni per l'immobile Z alle ore W"*.

**Cosa può cambiare in futuro**
Se il campo esprime la necessità: pagina dedicata `/compliance`, deep link scheda immobile dalla modale, trend storico settimanale, notifiche APE in scadenza, soglie configurabili, bottone "Sospendi sync", promozione `missing_rent` a codice backend distinto, audit trail correzioni.

---

## 16.14 · Cross-ref con altri capitoli

- **Cap. 3 · Immobili**: la scheda immobile è il posto dove **correggi** le violazioni. Ogni codice compliance rimanda a un campo specifico della scheda (§16.9 mapping).
- **Cap. 6 · Portali & Publishing**: **operativo** (attivazione portali, sync, wizard). Cap. 16 è il **riferimento tecnico** delle regole applicate. Complementari.
- **Cap. 14 · Import XML**: gli immobili importati via XML possono arrivare **non-compliant** (mancano campi non presenti nel feed sorgente). Verifica sempre la modale compliance dopo un import.
- **Cap. 10 · HAL Agent CRM**: puoi chiedere a HAL Agent *"Correggi la descrizione di questo immobile"* per risolvere velocemente il warning `description_too_short` (Cap. 10 §write_description).
- **Cap. 12 · HAL Knowledge**: puoi chiedere a HAL Knowledge *"Cosa significa less_than_3_photos?"* → risposta con fonti da `16-compliance-portali.yaml`.

---

**Progressione manuale**: 16/26 capitoli (62%).
**Voci HAL totali**: **196** (Cap. 1-16, +14 nuove voci Cap. 16).
**Versione capitolo**: v1.0 (Feb 2026 · TASK M).

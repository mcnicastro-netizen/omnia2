# Capitolo 14 · Import XML — Migrazione da altro gestionale

> **Cosa trovi in questo capitolo**
> Il modulo **Import XML** è il ponte che porta il tuo attuale portafoglio immobili da un gestionale legacy dentro OMNIA, senza reinserimento manuale. Funziona con qualsiasi feed XML "in stile italiano" (i formati che i CRM immobiliari esportano da 15 anni): l'importatore è **schema-agnostic** — riconosce le strutture più comuni tramite tabelle euristiche interne, senza dipendere da un fornitore specifico. Copre: dove trovarlo, il flusso a 2 fasi (**Preview → Commit**), il parsing e le tabelle di mapping (tipologia, energia, contratto, features), il dedupe per `reference_code`, la simulazione dry-run, i limiti onesti v1.

**Cosa NON è (D-051 onestà — regola cardine)**
- Non è un **connettore live/API** verso il tuo gestionale attuale. Non fa pull automatici, non si sincronizza in tempo reale, non riesporta verso il vecchio sistema. È un import **one-shot** che parte da un file XML che tu esporti tu manualmente dal vecchio strumento.
- Non è un **wizard di mappatura personalizzabile** (a la Zapier/Make). Le mappature sono **euristiche interne** basate su tabelle hardcoded — se il tuo XML usa termini/codici troppo esotici, alcuni campi possono finire nella sezione *"divergenze"* invece che nel dato principale.
- Non importa **clienti / lead / trattative** via XML. Solo **immobili** (`properties`). Per i clienti esiste un flusso separato (`/clients/csv-import`, Cap. 4 §clienti-import).
- Non fa **rollback batch**: una volta finalizzato il commit, gli immobili sono dentro. Se ti accorgi dopo che c'era un problema, li elimini uno alla volta dal modulo Immobili (o via `bulk` — Cap. 3).
- Non fa **fuzzy match** sul titolo o sull'indirizzo per il dedupe. Il dedupe usa **solo `reference_code`**: se il tuo XML non ha ref stabili, il dedupe è meno efficace.
- Non salva un log persistente delle preview. Una preview vive **10 minuti in memoria** sul processo backend. Se il backend riavvia (deploy, restart), la preview scompare e ti tocca ricaricare il file.
- Non supporta formati diversi da XML in v1 (no CSV, no JSON, no Excel).

---

## 14.1 · Cos'è il modulo Import XML e a chi serve

**In una frase**
Uno strumento di migrazione a due fasi che legge un file XML esportato dal tuo gestionale attuale, ti fa vedere **cosa contiene** (immobili leggibili, tipologie, città, warning), e — se sei d'accordo — li **inserisce nel tuo portafoglio OMNIA** sotto la tua agenzia.

**A chi serve**
- **Nuovi clienti OMNIA** che arrivano da un gestionale immobiliare esistente e non vogliono reinserire a mano 100-500 immobili.
- **Agenzie che cambiano gestionale** con backlog di annunci ancora attivi che vogliono migrare in un colpo solo, senza fermare l'operatività.
- **Titolari** che ricevono da un franchising/network una prima esportazione una tantum del portafoglio storico.

**Zero riferimenti a competitor**
Il modulo è progettato per accettare **qualsiasi XML "in stile italiano"** (feed con tag come `prezzo`, `canone`, `mq`, `citta`, `codice_tipologia`, `riferimento`, ecc.). Nella UI e nel codice **non c'è mai un nome di vendor specifico** — la label è sempre *"il tuo attuale gestionale"*.

[SCREEN: import-xml-upload]

---

## 14.2 · Dove trovare Import XML

**Rotta**: `/it/app/import` (o `/en/app/import`, `/es/app/import`).

**Come arrivarci**
1. Fai login a ImmoWeb come **titolare** (`agency_admin`) o `super_admin`.
2. Nella barra a sinistra, sezione **Migrazione** o **Impostazioni**, clicca **"Import da altro gestionale"**.
3. Si apre la pagina *"Importa da altro gestionale"*.

**Chi può accedere**
Solo `agency_admin` e `super_admin`. Gli agenti (`agent`) non vedono la voce menu e ricevono `403 Forbidden` se provano a chiamare gli endpoint direttamente. Motivo: l'import scrive su tutta la collezione immobili dell'agenzia, è un'operazione delicata riservata al titolare.

---

## 14.3 · Il flusso a 2 fasi — Preview → Commit

**A cosa serve capirlo**
Il modulo è progettato per **non sorprenderti**: prima ti mostra *"ho letto N immobili, questi 5 come esempio, questi warning"* — poi tocca a te decidere se procedere. Nessun cambiamento al DB avviene finché non premi *"Importa in OMNIA"*.

**Le 3 fasi visibili in schermata**

### FASE 1 · Upload
- Trascini o selezioni un file `.xml` (max 50 MB).
- Cliccando **"Analizza contenuto"** viene chiamato `POST /api/app/import/xml/preview` con il file come multipart.
- Il backend parsa il file, calcola statistiche, restituisce un **session_id** (10 minuti di validità).
- **Nessuna scrittura sul DB** in questa fase.

### FASE 2 · Preview report
Ricevi in schermata:
- **Totale letto**: *"N / M immobili leggibili"* (M = record trovati; N = parseabili senza errori bloccanti).
- **Aggregazioni**: 3 cards con **Per tipologia** / **Per contratto** / **Per città**.
- **Warning**: quanti immobili senza foto, quanti senza prezzo/canone.
- **Anteprima 5 immobili**: tabella con Ref, Titolo, Città, Tipo, Contratto, Prezzo, MQ, N. foto.
- **Divergenze**: elenco espandibile dei record scartati/anomali (max 50 righe).
- **Opzioni pre-commit**: toggle *"Salta immobili già presenti (dedupe per codice riferimento)"* — di default **ON**.

Da qui puoi:
- Cliccare **"Simulazione (nessuna scrittura)"** — chiama commit con `dry_run=true`.
- Cliccare **"Importa in OMNIA"** — chiama commit con `dry_run=false`.
- Cliccare **"Annulla"** — chiude la preview, torna al passo 1.

### FASE 3 · Commit result
Dopo il commit vedi:
- **Simulazione**: *"In caso di import reale sarebbero stati inseriti X immobili, Y saltati per duplicato."*
- **Import reale con inseriti**: *"✅ X immobili importati con successo, Y saltati (già presenti)."*
- **Import reale con 0 inseriti**: *"ℹ️ Tutti gli Y immobili erano già presenti (dedupe attivo)."*

[SCREEN: import-xml-preview]

**Endpoint API sotto il cofano**
| Endpoint | Metodo | Ruolo richiesto | Cosa fa |
|----------|:-:|:-:|---------|
| `/api/app/import/xml/preview` | POST multipart | `agency_admin` / `super_admin` | Legge XML, ritorna report + session_id (10min) |
| `/api/app/import/xml/commit` | POST JSON | `agency_admin` / `super_admin` | Applica preview al DB (o simula se `dry_run=true`) |
| `/api/app/import/xml/session/{id}` | GET | `agency_admin` / `super_admin` | Rilegge il report di una sessione ancora valida |

**Session ID pattern**
Formato: `prv_{millisecondi}_{primi 8 char user id}` (es. `prv_1738419300123_a1b2c3d4`). Legato all'utente che ha fatto upload — un altro utente della stessa agenzia con quella session id riceve `403 session_owner_mismatch`.

---

## 14.4 · Cosa riconosce il parser — tabelle di mapping

**A cosa serve capirlo**
Se il tuo XML usa **codici numerici o abbreviazioni** al posto di valori leggibili, il parser prova a tradurli tramite tabelle euristiche. Sapere quali codici sono riconosciuti ti evita sorprese.

### Tipologia immobile (18 codici → 12 tipi OMNIA)
Il campo `codice_tipologia` (o `type_code`) viene interpretato come codice numerico legacy:

| Codice | Diventa in OMNIA | | Codice | Diventa in OMNIA |
|:-:|:-:|--|:-:|:-:|
| `3` | appartamento | | `40` | ufficio |
| `10`, `33` | villa | | `50` | loft |
| `31` | attico | | `51` | monolocale |
| `32`, `34` | villetta_a_schiera | | `54` | negozio (bar) |
| `4` | negozio | | `60` | terreno_edificabile |
| `20` | magazzino | | `61` | terreno_agricolo |
| `70` | garage_box | | `80` | capannone |
| `90` | palazzo_stabile | | `11` | rustico_casale |

Codici fuori tabella o campi testuali (es. `<tipologia>appartamento</tipologia>`) restano nell'output ma potrebbero essere marcati come divergenze se il parser non li riconosce.

### Contratto / Operazione (`V/A/S/R/RB/ASTA`)
| Lettera | Contratto OMNIA |
|:-:|:-:|
| `V` | sale (vendita) |
| `A` | rent (affitto) |
| `S` | rent (sfitto/stagionale) |
| `R` | rent |
| `RB` | rent_to_buy |
| `ASTA` | auction |

### Classe energetica (19 codici → APE OMNIA)
Il parser accetta sia la stringa esplicita (`"A"`, `"A4"`, `"B"`, …) sia i codici numerici legacy `1`-`8`, `10`-`19`, `99` (esente). Sotto il cofano vengono normalizzati alle classi standard OMNIA: `A4/A3/A2/A1/A/B/C/D/E/F/G/exempt`.

### Categoria (`R/U/C`)
- `R` → residenziale
- `U` → ufficio  
- `C` → commerciale

### Features (25 keyword → boolean)
Il parser scansiona il testo di descrizioni/note cercando parole-chiave (case-insensitive, partial match). Esempi:
- `"balcon"` → `balcone: true`
- `"terraz"` → `terrazza: true`
- `"giardin"` → `giardino: true`
- `"piscin"` → `piscina: true`
- `"ascensor"` → `ascensore: true`
- `"aria_cond"` / `"climatiz"` → `aria_condizionata: true`
- `"cantin"` → `cantina: true`
- `"posto_auto"` → `posto_auto: true`
- `"box"` → `box_auto: true`
- `"blindat"` → `porta_blindata: true`
- `"parquet"` → `parquet: true`
- `"panoram"` / `"vista_mar"` → `vista_panoramica: true`
- `"solar"` → `pannelli_solari: true`
- `"disabili"` → `accesso_disabili: true`

*(Totale 25 keyword mappate — vedi `FEATURE_KEYWORDS` in `universal_xml.py:93-119`.)*

### Condizione immobile
Parole chiave: `nuov` → `nuovo`, `ristruttura` → `ristrutturato`, `da_ristruttura` → `da_ristrutturare`, `ottim` → `ottime`, `buon` → `buone`.

### Cosa succede se un campo non è mappabile
Il record viene comunque salvato con **il valore grezzo o `null`** per il campo problematico, e viene aggiunta una riga in **`divergences`** nella preview (es. *"map_error ref=XYZ: unexpected_energy_code=42"*).

---

## 14.5 · Cosa sono le "divergenze" e come leggerle

**A cosa serve capirlo**
Sotto la preview trovi una sezione espandibile *"Divergenze rilevate"*. Sono i **campanelli d'allarme**: il parser ha letto qualcosa che non gli tornava e vuole segnalartelo prima di scrivere.

**Tipi di divergenza comuni**

| Riga tipica | Significato |
|-------------|-------------|
| `xml_parse_error: ...` | Il file non è XML ben formato (es. tag non chiusi). Il parsing si è interrotto — il totale letto sarà 0. |
| `map_error ref=XYZ: ...` | Un immobile con `reference=XYZ` ha causato un errore durante il mapping (es. valore inatteso in un campo obbligatorio). Il record viene **scartato**. |
| `missing_city_or_title ref=XYZ` | Il record non ha né città né titolo → viene **scartato** (guard obbligatorio nel parser). |

**Il tetto di 50 divergenze**
Per non intasare la UI, la preview mostra al massimo **50 righe** di divergenze. Se il tuo XML ne ha di più, controlla i log server (super_admin) o rifai un import parziale con file più piccolo.

**Cosa fare se ci sono molte divergenze**
1. Apri il dettaglio (click sulla riga *"Divergenze rilevate (N)"*).
2. Verifica se sono **record borderline** (senza città) o **problemi strutturali** (tag XML errati).
3. Se sono strutturali → chiedi al fornitore del vecchio gestionale un export "più pulito".
4. Se sono su singoli campi → puoi comunque procedere con l'import: i record scartati **non finiscono nel DB**, ma quelli parsati sì.

---

## 14.6 · Dedupe per `reference_code` — evita doppioni

**A cosa serve**
Se importi lo stesso XML due volte, o rilanci un import dopo aver corretto qualcosa, non ti ritrovi con 200 duplicati.

**Come funziona**
- Alla fase Commit, se il toggle **"Salta immobili già presenti"** è attivo (default), il backend:
  1. Estrae la lista di `reference_code` dagli immobili da inserire.
  2. Cerca in `db.properties` con filtro `agency_id={tua_agenzia} + reference_code IN [...]`.
  3. **Salta** gli immobili con ref già presente.
  4. Inserisce solo i nuovi.
- Il report finale mostra: *"X inseriti, Y saltati per duplicato"* + fino a 50 codici saltati (per audit).

**Scope agency**
Il match è **scoped all'agenzia**: se un altro CRM di un'altra agenzia OMNIA usa lo stesso `reference_code`, non impatta il tuo import. Sicurezza multi-tenant garantita.

**Cosa succede se disattivo il dedupe**
- Se togli la spunta prima del commit, il backend **inserisce tutto** senza controllo.
- Utile solo in casi specifici (test, agenzie con ref non stabili tra export successivi). Usalo con cautela.

**Il campo `_import_reference`**
Nel documento MongoDB salvato, il parser aggiunge in coda **due campi di tracciabilità**:
- `_import_source: "universal_xml_importer_v1"`
- `_import_reference: <valore del tag riferimento o attributo id>`

Non compaiono nella UI immobili, ma sono utili al super_admin per rintracciare l'origine di un record.

---

## 14.7 · Simulazione dry-run — provare senza scrivere

**A cosa serve**
Vuoi sapere **quanti immobili sarebbero effettivamente inseriti** dopo il dedupe (potresti avere il dubbio di aver già importato una parte). La simulazione ti dà il numero **senza scrivere nulla**.

**Come funziona**
1. Dalla preview, invece di cliccare *"Importa in OMNIA"*, clicca **"Simulazione (nessuna scrittura)"**.
2. Chiama `POST /commit` con `dry_run: true`.
3. Il backend fa tutti i controlli di dedupe come nell'import reale.
4. Restituisce lo stesso payload di risposta con `dry_run: true` — ma **non inserisce nulla**.
5. Puoi rilanciare il commit vero dopo (la session è ancora valida per 10 minuti, la simulazione **non la consuma**).

**Differenza chiave con l'import reale**
- Simulazione (`dry_run=true`): la session rimane valida, puoi rilanciare simulazioni multiple o passare al commit reale.
- Commit reale (`dry_run=false`): al termine la session viene **consumata** (rimossa dallo store), non puoi rieseguirla — devi ricaricare il file.

---

## 14.8 · Il file XML: cosa deve contenere per essere leggibile

**A cosa serve capirlo**
Se il tuo XML non passa nemmeno la fase Preview con errore *"no_property_records_detected"* (422), è perché non abbiamo trovato record che sembrano immobili.

**Regola euristica del parser (`looks_like_property`)**
Un elemento XML è considerato un immobile se contiene **almeno 3 tag** tra questi indicatori:
- `prezzo`, `canone`, `mq`, `citta`, `città`
- `tipologia`, `codice_tipologia`, `indirizzo`, `titolo`, `riferimento`
- `surface`, `city`, `price`
- qualsiasi tag che inizi con `url` (es. `url_foto_1`, `url_planimetria`)

**Struttura tipica accettata**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<annunci>
  <immobile id="A123">
    <riferimento>REF-001</riferimento>
    <titolo>Trilocale via Roma</titolo>
    <citta>Milano</citta>
    <indirizzo>Via Roma 10</indirizzo>
    <codice_tipologia>3</codice_tipologia>
    <prezzo>250000</prezzo>
    <mq>85</mq>
    <descrizione>Balcone, ascensore, cantina.</descrizione>
    <url_foto_1>https://.../foto1.jpg</url_foto_1>
  </immobile>
  <immobile id="A124">
    ...
  </immobile>
</annunci>
```

**Struttura equivalente accettata**
Anche con nomi tag inglesi (`price`, `city`, `surface`) o con `<root><item>` invece di `<annunci><immobile>`. Il parser è **schema-agnostic** sulla superficie.

**Vincolo minimo per non essere scartato dopo il parse**
Ogni record deve avere almeno:
- Un **titolo** (`<titolo>` o `<title>`) — se manca finisce in `divergences` come `missing_city_or_title`.
- Una **città** (`<citta>` / `<città>` / `<city>`) — idem.

**Campi opzionali ma consigliati**
- `<riferimento>` per il dedupe.
- `<prezzo>` o `<canone>` (altrimenti warning "senza prezzo").
- Almeno una `<url_foto_1>` (altrimenti warning "senza foto").
- `<mq>` / `<surface>` per una scheda immobile completa.

---

## 14.9 · Errori comuni

| Problema | HTTP code | Cosa succede | Soluzione |
|----------|:-:|--------------|-----------|
| File non `.xml` | 400 `file_must_be_xml` | Upload bloccato. | Rinomina o riesporta come `.xml`. Backend accetta anche `.txt` come workaround, la UI però filtra su `.xml`. |
| File < 40 byte | 400 `file_empty_or_too_small` | Upload rifiutato. | Sicuramente file corrotto — riesporta. |
| File > 50 MB | 413 `file_too_large` | Upload rifiutato. | Splitta l'export in blocchi da 50 MB. |
| Zero immobili riconosciuti | 422 `no_property_records_detected` | Il parser non trova strutture che sembrano immobili. | Verifica che il file abbia tag come `prezzo`/`mq`/`citta`/`riferimento` (almeno 3 per record). Chiedi al vecchio gestionale un export "standard". |
| Session scaduta | 404 `preview_session_not_found_or_expired` | Sono passati > 10 minuti dalla preview. | Ricarica il file (Preview + Commit). |
| Session di altro utente | 403 `session_owner_mismatch` | Stai provando a committare una session_id che non è tua. | Ogni utente ha le proprie session. Fai tu il preview + commit dallo stesso utente. |
| Ruolo non consentito | 403 (require_roles) | Sei `agent` invece che `agency_admin`. | Chiedi al titolare di fare l'import. |
| Molte divergenze | Nessuno | Parsing riuscito ma molti record scartati (senza città/titolo, o mapping fallito). | Apri il dettaglio divergenze. Correggi l'XML alla fonte o accetta che i record borderline vengano scartati (i buoni entrano lo stesso). |
| Import fatto ma non vedo gli immobili | Nessuno | Il commit ha inserito X immobili ma non li vedi in lista. | Refresh pagina Immobili. Verifica il filtro attivo (potresti avere un filtro che esclude gli stati appena inseriti). Ogni immobile è creato con `moderation_status: "approved"` e `is_listed_on_immobilcloud: true`. |

---

## 14.10 · Limiti onesti v1 (D-051)

**Cosa il modulo Import XML NON fa oggi**

- ❌ **Solo XML in v1** — no CSV, no JSON, no Excel, no API pull da CRM esterni. Il backend accetta anche `.txt` come workaround per feed rinominati, ma la UI filtra `.xml`.
- ❌ **Nessuna sync automatica**. Ogni import è **one-shot**: tu esporti dal vecchio gestionale, tu carichi in OMNIA. Non c'è polling, webhook, cron.
- ❌ **Nessun wizard di mappatura personalizzabile**. Le tabelle sono euristiche interne (`TYPE_CODE_MAP`, `ENERGY_CODE_MAP`, `OPERATION_CODE_MAP`, `FEATURE_KEYWORDS`). Se il tuo XML usa codici mai visti, finiscono in divergenze.
- ❌ **Nessun rollback batch**. Una volta finalizzato il commit, gli immobili sono nel DB — vanno cancellati uno alla volta (o via bulk dalla pagina Immobili, Cap. 3).
- ❌ **Session in-memory, non persistita**. Se il backend riavvia (deploy, restart), tutte le preview attive scompaiono. Devi rifare l'upload.
- ❌ **TTL session solo 10 minuti**. Se ti distrai fra preview e commit più a lungo → devi ricaricare il file.
- ❌ **Nessuna preview delle foto** nella tabella samples. Solo il **conteggio** delle foto (`photos_count`). Le foto vengono comunque scaricate/riferite dagli URL indicati nel feed.
- ❌ **Nessun import di clienti / lead / trattative via XML**. Solo `properties`. Per clienti B2B c'è `/clients/csv-import` (Cap. 4), per la generazione lead da immobili c'è il modulo Match (Cap. 5).
- ❌ **Dedupe solo per `reference_code`**. Non fa fuzzy match su titolo/indirizzo/coordinate. Se il tuo export non ha `<riferimento>` stabile, il dedupe è inefficace e potresti creare doppioni.
- ❌ **Nessuna assegnazione automatica a un agente specifico**. Gli immobili importati non hanno `agent_id` — verranno visti come immobili "dell'agenzia" senza responsabile finché il titolare non li ri-assegna manualmente (o via bulk).
- ❌ **Nessuna traccia dello storico import**. Non c'è un pannello *"Ecco tutti gli import fatti in passato, con data e conteggi"*. I singoli record hanno `_import_source` e `_import_reference` in DB, ma non c'è UI.

**Cosa può cambiare in futuro**
Se il campo esprime la necessità, in versioni successive: CSV/JSON, sync periodica via API/URL, wizard mappatura, rollback batch, session persistita, import clienti via XML, storico import lato UI, assegnazione automatica agente.

---

## 14.11 · Cross-ref con altri capitoli

- **Cap. 3 · Immobili**: dopo l'import, la scheda immobile è editabile normalmente (foto, planimetrie, publishing). Cap. 3 §privacy governa cosa vedono gli agenti degli immobili importati (L1-L4).
- **Cap. 4 · Clienti**: per importare clienti da CSV c'è un flusso separato (`/clients/csv-import`), non copre questo capitolo.
- **Cap. 6 · Portali & Publishing**: gli immobili importati con `is_listed_on_immobilcloud: true` sono immediatamente candidati al publishing (dopo compliance HARD/SOFT).
- **Cap. 12 · HAL Knowledge**: puoi chiedere a HAL Knowledge *"Come importo da un vecchio gestionale?"* → risposta con fonti da `14-import-xml.yaml`.
- **Cap. 13 · Team & Ruoli**: l'endpoint richiede `agency_admin` — gli agenti non hanno accesso.

---

## 14.12 · Cosa fare adesso (checklist migrazione)

**Se stai migrando da un altro gestionale**
1. **Esporta** il tuo portafoglio dal vecchio strumento come XML (opzione tipica: *"Export feed portali"* o *"Esporta annunci"*).
2. Verifica il file: apri con un editor testuale, controlla che contenga tag come `<prezzo>`, `<citta>`, `<mq>`.
3. Vai in OMNIA **Import XML** → carica il file → clicca **Analizza contenuto**.
4. Leggi la preview: verifica che "leggibili / trovati" sia una % accettabile (idealmente > 90%).
5. Guarda le 5 righe di **anteprima**: sono immobili sensati? I prezzi, le città, le tipologie sono corrette?
6. Espandi **Divergenze** se il conteggio è > 0: quali record vengono scartati? Sono importanti?
7. (Opzionale) Clicca **Simulazione** per vedere quanti sarebbero effettivamente inseriti (dopo dedupe).
8. Se tutto ti torna, clicca **Importa in OMNIA** — il commit inserisce e consuma la session.
9. Vai in **Immobili** e verifica il conteggio: dovrebbero esserci gli immobili appena importati.
10. **Assegna un agente** ai nuovi immobili (bulk edit se sono tanti, Cap. 3).

**Se hai importato per errore**
- Vai in Immobili, filtra per data creazione (oggi) o per il flag `_import_source` (se hai accesso super_admin).
- Elimina in bulk o singolarmente.
- Poi rilancia con l'XML corretto.

---

**Progressione manuale**: 14/26 capitoli (54%).
**Voci HAL totali**: **168** (Cap. 1-14, +13 nuove voci Cap. 14).
**Versione capitolo**: v1.0 (Feb 2026 · TASK K).

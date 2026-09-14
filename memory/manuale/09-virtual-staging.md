# Capitolo 9 · Virtual Staging

> **Cosa trovi in questo capitolo**
> Il modulo **Virtual Staging** ti permette di arredare virtualmente stanze vuote (o **svuotare e ri-arredare** stanze già arredate) usando l'AI generativa (SAM 2 + Flux + Real-ESRGAN). Il capitolo copre: come funziona la pipeline in 3 stage, i 5 stili disponibili, i 6 tipi stanza, le 2 modalità (standard e reverse), le varianti parallele, i crediti consumati, il watermark obbligatorio, i limiti operativi e come salvare un render come foto dell'immobile.

**Cosa NON è (D-051 onestà)**
- Non è un **editor manuale**: scegli stile + stanza, l'AI decide. Nessun controllo pixel-level in v1.
- Non produce **foto reali**: sono **render fotorealistici** con watermark "Render virtuale OMNIA" **obbligatorio e non rimovibile** (conformità AGCM 2024 + Art. 21 Codice Consumo).
- Non fa **video**: solo immagini singole. Per micro-tour video vedi capitolo dedicato (in arrivo).
- Non usa **modelli locali**: le chiamate vanno a **fal.ai** (SaaS esterno).

---

## 9.1 · Cos'è il Virtual Staging

**In una frase**
Trasforma la foto di una stanza vuota in una versione arredata (o svuota una stanza arredata e la ri-arreda con un altro stile) in ~15-25 secondi.

**A cosa serve nel funnel commerciale**
- **Casa da ristrutturare**: farla immaginare arredata al lead senza spendere per servizio fotografico dopo lavori.
- **Immobile in svuotamento**: quando il proprietario ha già portato via i mobili ma l'annuncio deve partire subito.
- **A/B su gusti diversi**: proporre al lead 4 varianti (modern, classic, scandi, luxury) per capire il target buyer.

**Chi può usarlo**
- **Titolare** (`agency_admin`): sempre.
- **Agente**: sempre.
- **Segreteria**: come agente (concetto operativo, non ruolo backend).
- **Ogni render consuma crediti** dal saldo dell'agenzia (vedi §9.8).

**Come arrivi qui**
- Barra a sinistra → **Virtual Staging**.
- URL diretto: `/it/app/staging`.

[SCREEN: cap9-staging-panoramica]

---

## 9.2 · Come funziona la pipeline (3 stage AI)

**A cosa serve capirlo**
Se il render fallisce a metà, il messaggio d'errore dice **quale stage** è saltato — così sai se rilanciare, correggere la foto sorgente o segnalare il problema.

**Stage 1 — Segmentazione (SAM 2)**
- Modello `fal-ai/sam2/auto-segment`.
- Genera una **maschera** della stanza (parete, pavimento, aree arredabili).
- Durata tipica: **5-8 secondi**.
- Costo fal.ai: $0,001.

**Stage 1b (solo modalità reverse) — Svuotamento**
- Modello `fal-ai/flux-lora/inpainting` con prompt *"empty room, bare walls, clean bare floor..."*.
- **Rimuove l'arredo esistente** riempiendo con pareti e pavimento coerenti.
- Durata tipica: **4-6 secondi**.
- Costo fal.ai: $0,05.

**Stage 2 — Arredamento (Flux Inpainting)**
- Modello `fal-ai/flux-lora/inpainting` con prompt combinato (stile + tipo stanza + eventuale frammento CRM-aware).
- Guidance scale: 3.5 · Inference steps: 28 · Safety checker attivo.
- Genera **1-4 varianti** in parallelo (vedi §9.6).
- Durata tipica: **4-8 secondi per variante**.
- Costo fal.ai: $0,05 per variante.

**Stage 3 — Upscale 4x (Real-ESRGAN)**
- Modello `fal-ai/esrgan` con `RealESRGAN_x4plus`, scale 4.
- Porta il render a **risoluzione ~4K** per download bello grande.
- Durata tipica: **4-6 secondi per variante**.
- Costo fal.ai: $0,005 per variante.
- **Non-fatal**: se l'upscale fallisce su una variante, si conserva la versione base non-upscalata (badge `upscaled: false`).

**Tempo totale end-to-end (per 1 variante standard)**: ~**15-20 secondi**.
**Tempo totale reverse + 4 varianti**: ~**30-45 secondi**.

**Prompt CRM-aware (best-effort, silente)**
Se il render è collegato a un immobile, HAL invia i dati CRM (tipologia, città, zona, prezzo, superficie) a Gemini 3 Flash che restituisce **una frase inglese (≤25 parole)** da aggiungere al prompt (es. *"targeting upscale professional couple, refined finishes, warm palette for Milano Brera"*). Se Gemini non risponde in 15 s o fallisce, si usa il prompt base senza CRM. **Zero impatto sul risultato** se la chiave LLM non è configurata.

---

## 9.3 · I 5 stili disponibili

| Chiave | Etichetta | Cifra stilistica |
|:-:|-----------|------------------|
| `modern` | Moderno | minimalista, colori neutri, luci naturali, mobili contemporanei di fascia alta, parquet |
| `classic` | Classico | eleganza italiana tradizionale, colori caldi, mobili in legno, tende, lampadari, parquet |
| `scandi` | Scandinavo | pareti bianche, legno chiaro, mobili minimal, tessili cozy, atmosfera *hygge* |
| `industrial` | Industriale | mattoni a vista, metalli, pavimento in cemento, divano in pelle, lampadine Edison, urban chic |
| `luxury` | Luxury | pavimento in marmo, mobili di design, dettagli oro, soffitti alti, finiture premium |

Ogni stile ha un **prompt calibrato** per stanze reali (nessun modello di fashion o styling non abitativo).

**Come sceglierli**
- **Modern** → appartamenti moderni in centro, target giovane professional / famiglia contemporanea.
- **Classic** → appartamenti storici, target famiglia italiana media.
- **Scandi** → monolocali, mini appartamenti, target single/coppia giovane.
- **Industrial** → loft, ex uffici convertiti, target creativi / lavoratori in remoto.
- **Luxury** → ville, attici, immobili sopra €500k, target alto spendente.

**Custom stile non supportato in v1**
Non puoi aggiungere stili tuoi. Se vuoi variare, cambia tipo stanza o usa la modalità multi-style per generare in parallelo su più stili default.

---

## 9.4 · I 6 tipi stanza

| Chiave | Etichetta | Cosa mette la pipeline |
|:-:|-----------|-------------------------|
| `living` | Soggiorno | divano, tavolino, area TV, piante decorative |
| `bedroom` | Camera da letto | letto matrimoniale, comodini, armadio, luci soft |
| `kitchen` | Cucina | isola, elettrodomestici, area pranzo, lampadari a sospensione |
| `dining` | Sala da pranzo | tavolo per 6, sedie, credenza, illuminazione elegante |
| `bathroom` | Bagno | sanitari moderni, doccia, mobile lavabo, asciugamani, piante |
| `office` | Studio | scrivania, sedia ergonomica, libreria, luce naturale |

**Attenzione (D-051 onestà)**
- Se lanci `living` su una foto di camera da letto, l'AI cerca comunque di piazzare divano + tavolino → risultato **strano**. Usa sempre il tipo giusto per la foto.
- Non esistono tipi come *terrazzo*, *cantina*, *box auto*, *giardino esterno* — il modello Flux è calibrato solo per interni.

---

## 9.5 · Modalità Standard vs Reverse

### Standard (foto di stanza vuota)
- **Input**: foto di una stanza **già svuotata** (o comunque con arredi minimi).
- **Pipeline**: SAM 2 → Flux → Upscale.
- **Uso tipico**: immobile appena consegnato dopo trasloco, casa da ristrutturare senza arredi, foto architetto del vuoto.
- **Costo tipico per 1 variante**: ~$0,056 fal.ai.

### Reverse (svuota + ri-arreda)
- **Input**: foto di una stanza **già arredata** (con mobili del proprietario, non i tuoi).
- **Pipeline**: SAM 2 → **Flux "empty room"** (svuota) → Flux (arreda) → Upscale.
- **Uso tipico**: immobile dove il proprietario sta ancora abitando ma vuoi mostrare al lead una **versione con arredo diverso** (più moderno, più minimale, ecc.).
- **Costo tipico per 1 variante**: ~$0,106 fal.ai (aggiunge lo stage svuotamento).

**Quando conviene reverse**
- Il proprietario non vuole rimuovere i mobili per il servizio fotografico.
- I mobili attuali sono *dated* o disordinati e distraggono il lead.
- Vuoi mostrare *"come sarebbe con il tuo stile"* al lead in trattativa.

**Quando NON usare reverse**
- La stanza è **piccola** e piena di roba: il modello fatica a ripulire → risultati poco puliti.
- Ci sono **persone/animali** nella foto: la pipeline non li rimuove sempre bene. Meglio scattare una foto senza persone.
- **Mai** su foto con marchi visibili (schermi con loghi, quadri identificabili): il modello prova a mantenerli e crea artefatti.

---

## 9.6 · Varianti parallele (1-4 render in un colpo)

**A cosa serve**
Vedere in un solo job più risultati e scegliere il migliore, o mostrare al cliente più opzioni.

**Due modalità di varianti**

### `same_style` — 1-4 render con lo **stesso stile**
- Utile quando **non sei sicuro del risultato singolo**: 4 seed diversi = 4 arredamenti diversi nello stesso stile.
- Costo: **N × $0,05** per Flux + **N × $0,005** per upscale.

### `multi_style` — 1-4 render con **stili diversi**
- Puoi scegliere quali stili (fino a 4 chiavi tra `modern`, `classic`, `scandi`, `industrial`, `luxury`) o accettare i default (`modern`, `classic`, `scandi`, `luxury`).
- Se non specifichi la lista o passi una lista vuota → default.
- Ogni stile è renderizzato in parallelo con **stessa maschera** e **stessa base** (stanza vuota o originale).
- Costo: **N × $0,05** per Flux + **N × $0,005** per upscale.

**Numero varianti**
- Min: 1, Max: **4** (`num_variants` validato `ge=1, le=4` in Pydantic).
- Ogni variante consuma **crediti** e **rate limit** (vedi §9.8, §9.10).

**Fallimento parziale**
- Se in `multi_style` una singola variante fallisce, il job **procede** con quelle riuscite (log warning, no crash).
- Se **tutte** falliscono, il job passa a `failed` con errore *"Tutte le varianti multi-style sono fallite"*.

---

## 9.7 · Lanciare un render (passi)

1. Vai in **Virtual Staging** dalla barra a sinistra.
2. **Carica** la foto sorgente (dropzone drag&drop):
   - Formati accettati: **JPEG, PNG, WebP** (`ALLOWED_MIME`).
   - Peso max: **12 MB** (`MAX_UPLOAD_MB=12`, HTTP 413 se sfori).
   - L'upload va su fal.ai storage (async, viene restituito URL pubblico).
3. Scegli **stile** (5 pillole).
4. Scegli **tipo stanza** (6 pillole).
5. (Opzionale) Scegli **modalità** — Standard o Reverse.
6. (Opzionale) Scegli **num_variants** (1-4) e **variant_mode** (same_style / multi_style).
7. (Opzionale) Collega a un **immobile del CRM** per prompt CRM-aware.
8. Clicca **Genera render**.
9. **Vedi in tempo reale** i 3 (o 4 se reverse) stage progredire: `queued → running → done` con durata + costo.
10. Al completamento appare la vista **Before/After** side-by-side con bottone *"Scarica con watermark"*.

**Cosa NON puoi fare in v1**
- ❌ Ritagliare la foto sorgente prima dell'upload (fallo con Anteprima/Photoshop prima).
- ❌ Scegliere quale zona della stanza arredare (SAM 2 decide in automatico).
- ❌ Modificare parametri Flux (guidance scale, steps): sono fissi 3.5 / 28.
- ❌ Testare il prompt prima del render.

[SCREEN: cap9-staging-pipeline]

---

## 9.8 · Crediti e costo (D-051 onestà)

**Costo fal.ai reale per render (misurato)**
| Modalità | Stage | Costo/variante |
|----------|-------|:-:|
| Standard | SAM 2 + Flux + Upscale | **$0,056** |
| Reverse | SAM 2 + Flux(empty) + Flux + Upscale | **$0,106** |

**Consumo crediti B2B ImmoWeb**
- **1 render Virtual Staging = 18 crediti** (vedi `plans.py:CREDIT_COSTS`).
- Con listino Founder (1 cr = €0,05) → **€0,90 lordi per render**.
- Con listino Standard post-Founder (1 cr = €0,05) → **€0,90 lordi per render**.
- La regola è: **1 job = N varianti = N × 18 crediti** (multi-style 4 varianti costa **72 crediti** ≈ €3,60).

**Margine per l'agenzia (per capire il posizionamento)**
- Costo vivo fal.ai ~$0,056 (0,051 €) per render → margine ~94% a €0,90.
- Il servizio è pensato come **strumento di acquisizione mandato**, non revenue center.

**Costo B2C ImmobilCloud**
- Modulo Virtual Staging pubblico non implementato in v1 (previsto **€0,90/foto max 3 per annuncio UGC** — vedi `PRICING_B2C.md`, non attivo in checkout).

**Quando parte l'addebito crediti**
- Al momento della `POST /generate` la richiesta è validata e il job entra in `pending`.
- **Non c'è pre-check crediti in v1** (`generate_staging` non chiama il credit ledger): l'addebito è **posticipato** in altra sessione. Se il tuo saldo è a zero puoi comunque tecnicamente lanciare. **In arrivo: hard-gate a saldo insufficiente.**
- Se il job fallisce a metà pipeline, **il costo fal.ai è stato comunque speso** e comunque va scalato dai crediti (il modello non ha rollback su chiamate fal.ai avvenute).

**Cosa NON succede al momento**
- ❌ Non c'è ancora ricevuta/movimento crediti visibile in real-time (arriva con hard-gate).
- ❌ Non c'è avviso *"stai per spendere 72 crediti"* prima del click Genera.

---

## 9.9 · Watermark obbligatorio "Render virtuale OMNIA"

**Regola cardine (D-051 onestà + compliance)**
- **Ogni download** di un render (via `GET /jobs/{id}/download` o `/dataurl`) applica **server-side** un watermark *"Render virtuale OMNIA"* nell'angolo in basso a destra.
- Il watermark è **impresso nell'immagine JPEG**, non è un overlay CSS rimovibile.
- **Non c'è modo di scaricare la versione senza watermark** in v1.

**Perché è obbligatorio**
- **AGCM 2024** (Autorità Garante della Concorrenza e del Mercato): le immagini generate da AI devono essere chiaramente identificate come tali quando presentate in contesti commerciali.
- **Art. 21 Codice del Consumo**: le pratiche commerciali ingannevoli sono vietate. Presentare un render come foto reale può configurare pratica ingannevole.
- **Autoregolamentazione real-estate**: alcune associazioni di categoria (FIAIP) chiedono trasparenza esplicita.

**Cosa fa esattamente il watermark**
- Testo *"Render virtuale OMNIA"* in DejaVu Sans Bold.
- Font size proporzionale (`max(20, width/40)`).
- Riquadro nero semi-trasparente (alpha 160) sotto al testo per garantire leggibilità su sfondi chiari e scuri.
- Posizionato in basso a destra con padding uniforme.
- Output JPEG qualità 90.

**Rescale opzionale**
- Endpoint `/dataurl` (per salvare come foto immobile) applica watermark + **rescale a max 1600px** di larghezza (`MAX_PHOTO_WIDTH=1600`).
- Endpoint `/download` scarica alla risoluzione originale post-upscale (~4K).

**Errori comuni**

| Sintomo | Perché succede | Cosa fare |
|---------|----------------|-----------|
| *"Job non ancora completato" (409)* | Hai cliccato download prima che pipeline sia `done` | Attendi che tutti gli stage siano ✅ |
| *"Variante X non trovata" (404)* | Hai cercato di scaricare variante > numero disponibili | Verifica quante varianti ha prodotto il job |

---

## 9.10 · Limiti operativi (rate limit + upload + storage)

**Rate limit (per anti-abuso, non revenue-cap)**
- **20 render/ora per utente** (`SOFT_RATE_LIMIT_USER_HOUR=20`).
- **80 render/ora per agenzia** (`SOFT_RATE_LIMIT_AGENCY_HOUR=80`).
- Multi-style con 4 varianti conta come 4 render (aggregato via `$ifNull: ["$num_variants", 1]`).
- Superato il limite → HTTP 429 con messaggio *"Limite orario utente/agenzia raggiunto"*.
- Il contatore ha finestra scorrevole 1 ora (basato su `created_at`).

**Upload sorgente**
- **Max 12 MB per foto**.
- Solo MIME `image/jpeg`, `image/jpg`, `image/png`, `image/webp`.
- L'upload va su fal.ai storage (URL restituito).
- Foto molto pesanti → riduci con iLovePDF/TinyPNG prima di caricare.

**SSRF/abuse guard**
- Il campo `image_url` accetta:
  - URL interni OMNIA (`/api/media/...`), oppure
  - URL pubbliche http(s) che superano `assert_public_url` (bloccati IP privati, metadata endpoint, ecc.).
- Non puoi passare URL locali `localhost`, `127.0.0.1`, o range IP privati.

**Storage jobs**
- **TTL 30 giorni** (`JOB_TTL_DAYS=30`): dopo 30 giorni i job vengono candidati alla pulizia.
- **Stale reaper**: se un job resta in `pending`/`running` per più di **10 minuti** (`STALE_JOB_MINUTES=10`) viene marcato `failed` al prossimo startup (server crash-safe).

**Storia utente**
- Endpoint `GET /history?limit=50` mostra fino a **100 job** dell'utente corrente, ordinati per `created_at` decrescente.

**Eliminare un job**
- `DELETE /jobs/{id}` rimuove il job dal DB (permanente, senza cestino).
- Solo l'owner (`user_id` del job) può cancellare.
- Le foto già salvate su immobile con `save-to-property` NON vengono rimosse dall'immobile.

---

## 9.11 · Salvare un render come foto dell'immobile

**A cosa serve**
Portare direttamente il render nel Fascicolo/annuncio senza download + re-upload manuale.

**Come funziona**
- Endpoint `POST /jobs/{id}/save-to-property` con body `{"variant_index": 0-3, "property_id": "..."}` (opzionale, override del `job.property_id`).
- Il backend:
  1. Scarica la variante scelta.
  2. Applica watermark + rescale a 1600px.
  3. Converte in base64 `data:image/jpeg;base64,...`.
  4. Aggiunge al `photos[]` dell'immobile con caption *"Render virtuale OMNIA · {Tipo Stanza} {Stile}"* (es. *"Render virtuale OMNIA · Soggiorno Moderno"*).
  5. Se è la prima foto dell'immobile → viene impostata anche come `is_cover: true`.
- Il job viene marcato `saved_to_property_id: {property_id}`.

**Cosa vede il pubblico**
- Sul sito pubblico OMNIA (Cap. 8), la foto compare con la sua caption.
- Il **watermark è visibile** in basso a destra — il visitatore capisce che è un render (non una foto reale).

**Cosa NON fa**
- ❌ Non elimina foto esistenti dell'immobile (aggiunge in coda).
- ❌ Non sostituisce la cover se ce n'è già una.
- ❌ Non ri-pubblica automaticamente sui portali (dipende dal ciclo sync — vedi Cap. 6).

---

## 9.12 · Errori comuni (raccolta)

| Problema | Dove | Cosa fare |
|----------|------|-----------|
| *"MIME non supportato"* (400) | Upload | Converti in JPEG/PNG/WebP prima di caricare |
| *"File troppo grande (max 12 MB)"* (413) | Upload | Comprimi la foto (iLovePDF, TinyPNG, Squoosh) |
| *"Stile non supportato"* (400) | Generate | Scegli tra i 5 stili whitelist (modern/classic/scandi/industrial/luxury) |
| *"Tipo stanza non supportato"* (400) | Generate | Scegli tra i 6 tipi (living/bedroom/kitchen/dining/bathroom/office) |
| *"Limite orario utente raggiunto (20 render/ora)"* (429) | Generate | Attendi 1 ora rolling window, o passa il testimone a un collega |
| *"Immobile non trovato"* (404) | Generate con property_id | L'immobile è di un'altra agenzia o è stato eliminato |
| Job resta *"running"* per > 10 minuti | Pipeline | Al prossimo restart il reaper lo marca `failed`. Rilancia il job |
| SAM 2 restituisce *"no mask"* | Stage 1 | La foto è troppo scura/sfocata/non riconoscibile come stanza. Migliora la foto sorgente |
| Flux restituisce *"no images"* | Stage 2 | Il safety checker ha bloccato per contenuto (raro su interni). Riprova o cambia foto sorgente |
| Upscale fallisce ma il resto è OK | Stage 3 | Non-fatal: hai comunque la versione base non-upscalata (`upscaled: false` sulla variante) |
| Il render è brutto / distorto | Risultato | La qualità della foto sorgente conta molto. Preferisci foto ben illuminate, angolo grandangolo, no persone |
| Non vedo il render nel Fascicolo dopo *"salva come foto"* | Save-to-property | Ricarica la pagina Fascicolo (Cap. 7 §7.9) — la miniatura appare tra i render `done` |
| *"Nessun immobile collegato al job"* (400) | Save-to-property | Passa esplicitamente `property_id` nel body, oppure ricollega il job |

---

## Voci correlate (fuori capitolo)

- **Cap. 3 · Immobili** — le foto virtual staging entrano in `photos[]` dell'immobile.
- **Cap. 7 · Fascicolo Immobile** — sezione *Render Virtual Staging* mostra fino a 12 render `done` per immobile.
- **Cap. 8 · Sito web** — i render appaiono nella scheda pubblica (con watermark visibile).
- **Cap. 6 · Portali** — i render pubblicati come foto immobile finiscono anche sui portali via sync XML (vedi §6 sync automatico).

---

**Versione**: v1.0 · Feb 2026 (TASK F · Cap. 9 Virtual Staging)

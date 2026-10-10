# S3 — Meter economia storage (post-S2)

**Data:** 10 Ottobre 2026 · **agg. listini pubblici** stesso giorno  
**Stato:** ✅ numeri su **listini pubblici** + modello post-S2 · **proposta Founder: LISTINO FERMO**  
**Dipende da:** S2 bak O0 runtime · D-085 · D-114 · O0 design  
**Artefatto live:** `docs/ops/runs/s3-meter-economia.log`  
**Script:** `scripts/meter_storage_economia.py`

---

## 0. Perché listini pubblici (non “aspettiamo la fattura”)

Aspettare la bill del primo mese clienti **può essere troppo tardi** per firmare i canoni.

| Fonte | Attendibilità pre-GTM | Limite |
|-------|----------------------|--------|
| €0,04/GB “storico O0” | Bassa (claim non ancorato) | Inventato |
| **Listini pubblici provider** | **Alta per decisione** | Listino ≠ sconto; manca ops/egress se non modellati |
| Fattura nostra | Massima | Arriva dopo il rischio |

**Scelta S3:** ancorare i costi a listini pubblici (consultati 10-Ott-2026), non al claim €0,04.

---

## 1. Ancore €/GB pubbliche (storage)

Fonti aperte (solo **storage**; vedi note egress):

| Provider / prodotto | Prezzo listino | ≈ €/GB/mese | Uso tipico OMNIA |
|---------------------|----------------|------------:|------------------|
| **Cloudflare R2** Standard | **$0,015 / GB-month** ([docs](https://developers.cloudflare.com/r2/pricing/)) | **~€0,014** | Object storage media (path target) · **egress $0** |
| **AWS S3** Standard us-east-1 | **$0,023 / GB-month** ([aws](https://aws.amazon.com/s3/pricing/)) | **~€0,021** | Object storage · **egress ~$0,09/GB** (trappola) |
| **AWS S3** Standard eu-central-1 | **~$0,0245 / GB-month** | **~€0,023** | Come sopra, EU |
| **Hetzner Cloud Volume** | **€0,0572 / GB/mese** ([docs price adj.](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/)) | **€0,057** | Disco tipo FS locale su VPS (as-is vicino) |
| **Hetzner Storage Box** BX11 | **~€3,81 / 1 TB/mese** (tier fisso) | **~€0,0037** | Bak cold / archivio · non hot serve |

Cambio $→€ ≈ 0,92 (ordine di grandezza; ricalcolare al rate del giorno se serve precisioni contabili).

**Regola di lettura:**  
- Path **object (R2)** → usare ~€0,014 (+ ops R2, egress 0).  
- Path **volume Hetzner** (simile a oggi) → usare **€0,057**.  
- **Non** usare S3 AWS come baseline senza modellare egress.

---

## 2. Misura LIVE ambiente (ancora utile, non sufficiente)

| Voce | Valore |
|------|--------|
| Media live du | **0 B** (seed senza foto) |
| Bak du | ~15 KB |
| Retention | **7** (S2) |
| Meter agenzie | 0 GB usati |

Prova S2 hardlink: apparent 2× · reale ~1× → il moltiplicatore pieno non è più ×32.

---

## 3. Listino OMNIA storage (D-085 · invariato)

| Piano | Canone | Quota |
|-------|-------:|------:|
| Starter | €49 | 30 GB |
| Pro | €99 | 100 GB |
| Agency | €299 | 300 GB |
| Addon | €15 | +100 GB |

---

## 4. Modello ops post-S2 × listini pubblici

Ops GB ≈ live × moltiplicatore (hardlink + hot 7g):

| Scenario | × | Nota |
|----------|--:|------|
| best | 1,05 | file stabili |
| **mid** | **2,5** | riferimento O0 |
| worst | 7,2 | rewrite ogni giorno |

Agency a quota piena → ops mid ≈ **750 GB**.

### Agency 300 GB live · mid ×2,5 (750 GB ops) — solo storage

| Ancora listino | €/GB | Costo / mese | % di €299 | Esito |
|----------------|-----:|-------------:|----------:|-------|
| R2 ~€0,014 | 0,014 | **€10,50** | 3,5% | OK |
| S3 storage-only ~€0,023 | 0,023 | **€17,25** | 5,8% | OK (*senza* egress) |
| Hetzner Volume €0,057 | 0,057 | **€42,75** | 14,3% | OK |
| Claim O0 €0,04 (legacy) | 0,04 | €30,00 | 10,0% | OK (solo confronto) |

### Starter / Pro / Addon — mid ×2,5 · due ancore principali

| Tier | Ops GB | @ R2 €0,014 | @ Hetzner Vol €0,057 | vs canone |
|------|-------:|------------:|---------------------:|-----------|
| Starter 30 | 75 | €1,05 | €4,28 | OK / OK |
| Pro 100 | 250 | €3,50 | €14,25 | OK / OK |
| Agency 300 | 750 | €10,50 | €42,75 | OK / OK |
| Addon +100 | 250 | €3,50 | **€14,25** | OK / **stretto vs €15** |

### Pre-S2 ×32 · stessa ancora Hetzner Volume (perché S2 era obbligatorio)

| Tier | Ops | @ €0,057 | vs canone |
|------|----:|---------:|-----------|
| Pro | 3200 | **€183** | **> €99** |
| Agency | 9600 | **€549** | **> €299** |

Anche a R2 €0,014, pre-S2 Agency 9600×0,014 ≈ **€134** — ancora alto vs altri costi; a Volume era fallimento netto.

### Nota egress (perché R2 batte S3 AWS in brochure)

Se si **servono** media al browser da AWS S3, egress ~$0,09/GB può superare lo storage.  
R2: egress **$0** sul listino pubblico → listino OMNIA più difendibile su path object.

---

## 5. Verdetto proposto (Founder)

**LISTINO FERMO** — €49/€99/€299 · quote 30/100/300 · addon €15/100 GB.

Motivi aggiornati (listini pubblici):

1. Post-S2, anche sul path **caro** (Hetzner Volume €0,057), Agency mid resta ~14% del canone.  
2. Sul path **target object (R2)** il disco è ~3–4% del canone Agency.  
3. Pre-S2 ×32 resta economicamente rotto su Volume (e pesante anche su R2).  
4. Unico punto stretto: **addon @ Volume €0,057 mid** (~€14 su €15) → se restiamo a lungo su solo volume locale, monitorare; su R2 l’addon è comodo (€3,50).  
5. Non è ancora la *nostra* fattura, ma è **abbastanza attendibile per non rivedere i prezzi oggi**.

---

## 6. Firma Founder

| Campo | Valore |
|-------|--------|
| Data | |
| Ha letto §0–§4 (listini pubblici) | sì / no |
| Decisione listino | **FERMO** / revisione (specificare) |
| Path storage assunto | Volume Hetzner / R2 / altro |
| Note | |
| Firma | |

---

## 7. Limiti

- Listino pubblico ≠ sconto enterprise ≠ nostra architettura finale.  
- Ops R2 (Class A/B) e CPU/AI/Stripe **non** in questa tabella.  
- Sandbox senza media clienti.  
- Prezzi verificati 10-Ott-2026 — rivalutare se i provider cambiano listino.

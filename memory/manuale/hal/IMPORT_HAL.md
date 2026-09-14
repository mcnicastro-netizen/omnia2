# 📚 HAL Knowledge — Import & Cold Start (v0.17)

**Ultimo aggiornamento**: 16-Ago-2026 (post-Cap. 21 · Valutatore immobiliare · post B2C-VAL-01)
**Corpus attuale**: **267 voci HAL YAML** su **21 capitoli** (Cap. 1-21)
**Motore**: `hal_knowledge.py` con loader YAML **attivo** (Opzione A applicata in TASK B-bis · 6 Ago 2026) · **Fix Feb 2026**: `memory/manuale/*.md` **escluso** dal RAG ingest (chunk atomici YAML = sola sorgente retrieval per il manuale).
**Prossimo passo**: reindex HAL **batch** a fine manuale (regola Founder — NON rigenerare `hal-index.json` per singoli capitoli). Attendere completamento Cap. 22-26 prima del reindex live.

---

## 🎯 Cosa fa questo documento

- Descrive **come indicizzare** le 56 voci HAL nel motore già esistente `hal_knowledge.py`.
- Definisce la **strategia di chunking** (chunk = 1 voce YAML atomica, non arbitrary split).
- Fornisce le **5 query test di controllo** per validare il retrieval prima del rilascio.
- Documenta i **limiti attuali** (v0.1 è un cold start: il vero rilascio è dopo Cap. 5+).

---

## 🧠 Come funziona il retrieval in OMNIA (contesto tecnico)

**Motore**: `/app/backend/apps/immoweb/hal_knowledge.py` (già live).

**Approccio (D-061)**:
- **Retrieval**: **TF-IDF + cosine similarity** — no chiamate LLM sull'embedding.
  - Corpus attuale piccolo (~56 voci + docs interni) → TF-IDF batte in latenza gli embeddings neurali senza degradare la qualità per domande italiane.
- **Generation**: Gemini 3 Flash Preview via Emergent LLM Key (streaming SSE).
- **Confidence gate**:
  - `< 0.08` → risposta "insufficient_context" (rifiuta di rispondere).
  - `>= 0.08 && < 0.20` → risposta "medium" (con caveat).
  - `>= 0.20` → risposta "high-confidence".
- **Idempotenza**: chunk indicizzato con MD5 del contenuto sorgente, re-ingest solo se cambiato.

**Collezioni Mongo**:
- `hal_knowledge_chunks`: chunk indicizzati
- `hal_knowledge_meta`: matrice TF-IDF + vocab
- `hal_knowledge_sessions`: storico Q&A

**Rotte**:
- `GET /api/app/hal/knowledge/status` → stato indice
- `POST /api/app/hal/knowledge/reindex` → forza reingest
- `POST /api/app/hal/knowledge/ask` → domanda (streaming SSE)
- `GET /api/app/hal/knowledge/history` → storico sessioni utente

---

## 🧩 Strategia di chunking per il manuale (v0.1)

**Regola cardine**: **1 voce HAL YAML = 1 chunk indipendente**.

Motivi:
1. Ogni voce è **già atomica** (domanda naturale + a_cosa_serve + quando_si_usa + passi + errori_comuni + permessi).
2. Ogni voce è **già ottimizzata per query semantica** (`domanda_naturale` è la classe di query attesa).
3. Un chunk = una risposta completa → nessun rischio di "risposta tagliata a metà".
4. Chunk piccoli (media ~1.5 KB) → matrice TF-IDF sparsa, retrieval veloce.

**Struttura testo del chunk** (concatenazione predefinita per l'ingestion):

```
[TITOLO] {titolo}
[MODULO] {modulo}
[DOMANDA] {domanda_naturale}
[A COSA SERVE] {a_cosa_serve}
[QUANDO SI USA] {quando_si_usa}
[PASSI]
- {passo_1}
- {passo_2}
...
[ERRORI COMUNI]
- {problema_1} → {soluzione_1}
...
[PERMESSI]
- {permesso_1}
- {permesso_2}
...
[TAGS] {tag1, tag2, ...}
```

**Metadati preservati** (per filtering/boosting):
- `id`, `modulo`, `capitolo`, `livello`, `pubblico`, `tags`, `correlati`

---

## 📇 Index statico — `hal-index.json`

**Cos'è**: catalogo delle 56 voci con metadati e MD5 (no contenuto full).
**A cosa serve**:
- Lookup rapido lato frontend (autocomplete, "voci correlate").
- Fingerprint per invalidazione cache (`content_md5` per voce, `md5` per file).
- Base per lo script di ingestion (itera l'index, carica la voce completa dal `.yaml` sorgente).

**Snapshot corrente** (`generated_at` nel file):

```json
{
  "version": "v0.6-cap10",
  "stats": {
    "totale_voci": 117,
    "per_capitolo": {"01": 10, "02": 8, "03": 15, "04": 12, "05": 11, "06": 12, "07": 12, "08": 12, "09": 12, "10": 13},
    "per_modulo":   {"Primo accesso": 10, "Dashboard": 8, "Immobili": 15, "Clienti": 12, "Match": 11, "Portali": 12, "Fascicolo": 12, "Sito web": 12, "Virtual Staging": 12, "HAL Agent": 13},
    "per_livello":  {"base": 83, "intermedio": 34},
    "per_pubblico": {"titolare": 117, "agente": 102, "segreteria": 68},
    "totale_correlati": 274,
    "totale_tags_unici": 289
  }
}
```

**Regenerazione dell'index** (ogni volta che aggiungi/modifichi voci):

```bash
cd /app && python3 -c "
import yaml, json, hashlib, os
from datetime import datetime, timezone

HAL_DIR = '/app/memory/manuale/hal'
files = sorted(f for f in os.listdir(HAL_DIR) if f.endswith('.yaml') and f[0].isdigit())
corpus = {
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'version': 'v0.1-cold-start',
    'source_files': [], 'voci': [],
    'stats': {'totale_voci': 0, 'per_capitolo': {}, 'per_modulo': {},
              'per_livello': {}, 'per_pubblico': {}},
}
# ... (vedi script inline in b2c CHANGELOG 2026-08-06)
"
```

*(Lo script completo è nella pipeline di sviluppo interno; lo esegue il main agent al momento della creazione dell'index.)*

---

## 🚀 Come indicizzare le voci nel motore RAG

### Opzione A (raccomandata) — Aggiungere il loader YAML in `hal_knowledge.py`

`hal_knowledge.py` attualmente indicizza solo file `.md` in `memory/`. Per includere le voci del manuale serve un piccolo add-on nella funzione `ingest_corpus`:

```python
# In hal_knowledge.py, dentro ingest_corpus():
# ... dopo aver processato i file .md ...

# --- NEW: manuale HAL YAML (chunk = 1 voce atomica) --------------------
HAL_YAML_DIR = MEMORY_ROOT / "manuale" / "hal"
for yaml_file in sorted(HAL_YAML_DIR.glob("*.yaml")):
    if yaml_file.name.startswith("hal-index"):
        continue
    with yaml_file.open("rb") as f:
        raw = f.read()
    file_md5 = hashlib.md5(raw).hexdigest()
    data = yaml.safe_load(raw.decode("utf-8"))
    for v in data.get("voci", []):
        chunk_text = _render_voce_hal(v)   # helper dedicato
        chunks.append({
            "file": yaml_file.name,
            "section": v["modulo"],
            "chunk_id": v["id"],
            "text": chunk_text,
            "md5_source": file_md5,
            "metadata": {
                "id": v["id"],
                "modulo": v["modulo"],
                "livello": v["livello"],
                "tags": v["tags"],
                "correlati": v.get("correlati", []),
                "domanda_naturale": v["domanda_naturale"],
            },
        })
```

**Helper `_render_voce_hal(v)`**: produce il testo di chunk secondo la struttura documentata sopra (vedi "Struttura testo del chunk").

**Impatto**:
- 56 chunk aggiuntivi → matrice TF-IDF cresce ma resta sotto i 200 chunks totali (attualmente ~80 con solo i `.md`).
- Nessuna nuova dipendenza (`yaml` è già usato altrove).
- Idempotenza garantita da `md5_source` per file + `chunk_id` per voce.

### Opzione B (script standalone) — Se non vuoi toccare `hal_knowledge.py`

Uno script `scripts/ingest_manual_hal.py` che:
1. Legge i YAML manuale.
2. Chiama `POST /api/app/hal/knowledge/reindex?include_manual=true` (previa piccola modifica endpoint).
3. Riporta il risultato.

**Preferenza raccomandata**: Opzione A (integrata, unica sorgente di verità).

---

## 🚦 Stato UI HAL Knowledge

**Pagina attuale** (`HalKnowledgePage.jsx`): funzionante per admin/agente. Corpus attuale = solo file `.md` in `memory/` (PRD, ROADMAP, DECISIONS, CHANGELOG, ecc.).

**Banner aggiunto in questo TASK**:
- Se il corpus manuale HAL YAML **non è ancora indicizzato** (nessun chunk con `file` che finisce in `.yaml`), la pagina mostra in alto:
  > 📖 **Corpus manuale in indicizzazione** — Le 56 voci del Manuale Operativo (Cap. 1-5) saranno disponibili a breve. Nel frattempo HAL Knowledge risponde già su PRD, ROADMAP, DECISIONS e altri documenti tecnici.
- Il banner scompare automaticamente non appena l'ingestion delle voci YAML è completata (verifica lato server nell'endpoint `/status`).

---

## ✅ 5 Query di test (per validare il retrieval)

Prima di dichiarare il cold start "attivo", eseguire manualmente queste 5 query dalla pagina HAL Knowledge (o via `POST /api/app/hal/knowledge/ask`) e verificare che il chunk **top-1** ritornato corrisponda all'`id` atteso.

### Query 1 · Eliminazione cliente con vincoli

- **Domanda**: *"Come cancello un cliente che ha immobili in carico?"*
- **Voce attesa (top-1)**: `clienti.archiviare-eliminare`
- **Contesto attivato**: passi "il sistema blocca l'eliminazione con il messaggio 'Impossibile eliminare: N immobile/i in carico'" + soluzione riassegna/rimuovi collegamento.
- **Confidence attesa**: ≥ 0.20 (high)

### Query 2 · Privacy avanzata

- **Domanda**: *"Cosa vede un anonimo di un immobile marcato L3?"*
- **Voce attesa (top-1)**: `immobili.privacy-4-livelli-cosa-sono` o `immobili.privacy-scegliere-livello`
- **Contesto attivato**: matrice L1/L2/L3/L4 + soglia minima.
- **Confidence attesa**: ≥ 0.20 (high)

### Query 3 · Interpretazione temperatura

- **Domanda**: *"Perché un cliente è marcato ROVENTE?"*
- **Voce attesa (top-1)**: `match.scala-temperature` o `clienti.temperatura-lead-scoring`
- **Contesto attivato**: range 85-100 punti + significato + azione tipica ("chiama entro 24 ore").
- **Confidence attesa**: ≥ 0.20 (high)

### Query 4 · Troubleshooting operativo

- **Domanda**: *"Perché la pagina Match è vuota?"*
- **Voce attesa (top-1)**: `match.zero-match`
- **Contesto attivato**: checklist 5 punti (bozze, preferenze, filtro score, tipi cliente, coerenza portafoglio).
- **Confidence attesa**: ≥ 0.20 (high)

### Query 5 · Import complesso

- **Domanda**: *"Ho un file Excel disordinato del vecchio CRM, come lo importo?"*
- **Voce attesa (top-1)**: `clienti.smart-import-ai`
- **Contesto attivato**: formati supportati (.csv/.xlsx/.vcf/.txt) + limiti (5 MB, 500 righe) + passi confidenza.
- **Confidence attesa**: ≥ 0.20 (high)

### Criteri di accettazione cold start v0.1

- **5/5** query devono avere la voce attesa nel **top-3** (non richiesto top-1 stretto).
- Almeno **4/5** devono superare confidence 0.20 (high).
- **0/5** deve ritornare "insufficient_context".
- Se ≥2 query falliscono → analizzare TF-IDF vocab (probabilmente serve espandere stopword italiane o preprocess).

---

## 🚫 Cosa NON è in scope di questo TASK B

- ❌ Chiamare LLM per generare embeddings (TF-IDF resta la scelta).
- ❌ Modificare il chunk strategy per i `.md` esistenti.
- ❌ Reindex globale in produzione (l'attivazione va confermata dal Founder).
- ❌ Aggiungere Cap. 6+ al corpus (arriveranno con l'avanzamento del manuale).

---

## 📅 Prossimo giro

1. **Verifica**: Founder approva strategia sopra.
2. **Implementazione Opzione A** in `hal_knowledge.py` (piccolo commit di ~30 righe).
3. **Rigenerazione index** + **reindex manuale** → verifica delle 5 query test.
4. **Rimozione banner** "corpus in indicizzazione" quando `hal_knowledge_chunks` contiene ≥ 56 voci con `file` YAML.
5. Ogni nuovo capitolo del manuale → **rigenera index** + **reindex incrementale** (idempotente per MD5).

---

## 🗓️ Storico versioni

| Data | Versione | Note |
|------|:-:|------|
| 06-Ago-2026 | **v0.1-cold-start** | Prima stesura. hal-index.json generato su 56 voci Cap. 1-5. Strategia chunk = 1 voce YAML atomica. 5 query test documentate. |
| 06-Ago-2026 (sera) | **v0.2-attivato** | Opzione A applicata in `hal_knowledge.py` (loader YAML in `ingest_corpus`). 56 voci indicizzate come chunk atomici, 5/5 query PASS. |
| 06-Ago-2026 (notte) | **v0.2-cleanup** | CHANGELOG.md rimosso dal corpus (`hal_knowledge.py:CORPUS_FILES`) per rompere feedback loop TF-IDF. |
| 06-Ago-2026 (Cap. 6) | **v0.2-cap6** | Cap. 6 Portali/Publishing aggiunto (+12 voci → 68). |
| Feb-2026 (Cap. 7) | **v0.3-cap7** | Cap. 7 Fascicolo Immobile aggiunto (+12 voci → 80). Reindex live post-push. |
| Feb-2026 (Cap. 8) | **v0.4-cap8** | Cap. 8 Sito web agenzia aggiunto (+12 voci → 92). Reindex live post-push. |
| Feb-2026 (Cap. 9) | **v0.5-cap9** | Cap. 9 Virtual Staging aggiunto (+12 voci → 104). Reindex live post-push. |
| Feb-2026 (Cap. 10) | **v0.6-cap10** | Cap. 10 HAL Agent CRM aggiunto (+13 voci → 117). Convenzione naming Fase 0: HAL nel manuale, `al_*` nel codice invariato. |
| Feb-2026 (G-bis) | **v0.6.1-cap10-gbis** | Micro-fix retrieval Cap. 9 `staging.crediti-costo` (+8 tag, +1 correlato, domanda_naturale estesa, a_cosa_serve arricchito con "prezzo render"). Nessun voce aggiunta, totale resta 117. |
| Feb-2026 (Cap. 11) | **v0.7-cap11** | Cap. 11 Mutui comparatore aggiunto (+12 voci → 129). Reindex live post-push. |
| Feb-2026 (H-bis) | **v0.7.1-cap11-hbis** | Fix onestà D-051 Cap. 11: 9→**8 banche distinte** (banks_count=8 in /mutui/config), 11→**9 offerte Consap**, ING NON Consap (né Fisso né Variabile). Voce rinominata `mutui.offerte-14-banche-9` → `mutui.offerte-14-banche-8`. |
| Feb-2026 (Cap. 12) | **v0.8-cap12** | Cap. 12 HAL Knowledge (meta-doc del RAG stesso) aggiunto (+13 voci → 142). Copertura hal_knowledge.py (617 righe) + HalKnowledgePage.jsx (307 righe): TF-IDF + Gemini 3 Flash Preview, corpus 7 file + Cap. 1-11, CHANGELOG.md escluso (B-ter), soglie confidence 0.08/0.20, storico per-utente, reindex super_admin idempotente. Distinzione D-040 fra HAL Knowledge / HAL Agent CRM / HAL Legal. |
| Feb-2026 (Cap. 13) | **v0.9-cap13** | Cap. 13 Team & Ruoli / Collaboratori aggiunto (+13 voci → 155). Copertura `invites.py` (286 righe) + `agencies.py` (180 righe) + `MembersPage.jsx` (225 righe) + `InviteMemberModal.jsx` (134 righe) + `AcceptInvitePage.jsx` (186 righe): magic-link invite 7gg, ruoli agency_admin/agent (segreteria = concetto operativo), stati pending/accepted/revoked/expired, upgrade role solo se client. |
| Feb-2026 (Cap. 14) | **v0.10-cap14** | Cap. 14 Import XML / Migrazione da altro gestionale aggiunto (+13 voci → 168). Copertura `xml_import.py` (192 righe) + `universal_xml.py` (546 righe) + `ImportXmlPage.jsx` (341 righe): flusso 2 fasi Preview→Commit, session TTL 10min in-memory, dedupe per reference_code, dry-run, tabelle mapping (TYPE_CODE_MAP 18 codici, ENERGY_CODE_MAP 19, OPERATION_CODE_MAP 6, FEATURE_KEYWORDS 25), zero riferimenti a competitor, limiti v1 esplicit (no CSV, no sync, no rollback batch). |
| Feb-2026 (Cap. 15) | **v0.11-cap15** | Cap. 15 Social Publisher (FB Page + IG Business + Telegram) aggiunto (+14 voci → 182). Copertura `social_publisher.py` (578 righe) + `SocialPublisherPage.jsx` (470 righe): white label D-041 (ogni post sotto la Pagina/Bot dell'agenzia), credenziali AES-GCM cifrate, on-demand push (no scheduling), Meta Graph v20 + Telegram Bot API, caption default 5-righe con emoji, audit `social_posts`, limiti v1 (no X/LinkedIn/TikTok, no carosello/video, no analytics engagement, no bulk publish). |
| Feb-2026 (Cap. 16) | **v0.12-cap16** | Cap. 16 Compliance Portali (validatore HARD/SOFT deep-dive normativo) aggiunto (+14 voci → 196). Copertura `shared/validators/compliance.py` (171 righe) + `publishing.py` compliance endpoint + `sync_engine.py` filter + `PublishingPage.jsx` modale inline: 5 regole HARD → 7 codici, 4 SOFT, 14 classi APE ammesse, feed vs sync, ghost label `missing_rent` documentata onestamente, distinzione da Cap. 6 operativo. |
| Feb-2026 (Cap. 17) | **v0.13-cap17** | Cap. 17 Domain Vault (sovranità digitale D-054) aggiunto (+15 voci → 211). Copertura `domain_vault.py` (155 righe) + `custom_domain.py` (454 righe) + `domain_check.py` (359 righe): promessa D-054 (OMNIA never registers a domain), 3 componenti (sovereignty confirm + custom domain DNS TXT+CNAME + RDAP checker pubblico), audit trail append-only `domain_vault_events`, help-to-connect NON transfer. |
| Feb-2026 (Cap. 18) | **v0.14-cap18** | Cap. 18 Notifiche e attività aggiunto (+16 voci → 227). Copertura `shared/email/client.py` (117 righe · Resend + mock mode) + 7 template Resend (`welcome`, `password_reset`, `agency_invite`, `lead_notification`, `saved_search_alert`, `founders_welcome`, `founders_admin_notification`) + `apps/immoweb/cron.py` (saved-search trigger super_admin) + `apps/immocloud/saved_searches.py` (cron logic + digest HTML max 6 righe) + `frontend/src/components/ui/sonner.jsx` (toast). **Onestà D-051 estrema**: NO router `/notifications`, NO Bell icon, NO activity feed, NO push/SMS/WhatsApp, NO retry queue, NO webhook Resend, NO UI preferenze, `frequency` saved-search flag salvato ma cron ignora, `push` in schema `User.notification_channels` = dead code. 16 chunk YAML documentano email transazionali + toast + cron + audit trail interno (~10 collezioni non-UI) + limitazioni v1 esaustive. |
| Feb-2026 (Cap. 19) | **v0.15-cap19** | Cap. 19 Impostazioni agenzia aggiunto (+14 voci → 241). Copertura `SettingsPage.jsx` (358 righe) + `apps/immoweb/agencies.py` (180 righe · GET/PATCH `/agencies/me`) + `shared/models/agency.py` (305 righe · AgencyInDB/AgencyUpdate + 5 sotto-schemi) + `BillingPage.jsx` (235 righe) + `apps/billing/routes.py` (473 righe) + `apps/billing/plans.py` (LAUNCH Founders €49/€99/€249/€299 + POST_TRACTION €79/€179/€349/€499 + 6 credit packages €0,05/cred). **Onestà D-051**: v1 solo 5 sezioni anagrafica (identità/fiscale/indirizzo/contatti/modalità sito), 3 template omnia stub "presto disponibile", NO uploader logo/color picker, campi schema-only (logo_url/primary_color/accent_color/REA/FIAIP/contact.website/country/plan_type/group_id/branch_code), NO validazione P.IVA/CF/CAP/telefono/geocoding, NO transfer ownership (owner_id immutabile), NO audit trail settings, toast success = banner embedded (NON sonner Cap. 18). Team/API Keys/Domain/Notifiche/Billing = pagine SEPARATE. |
| Feb-2026 (Cap. 20) | **v0.16-cap20** | Cap. 20 API Keys e integrazioni (Track B / API Gateway) aggiunto (+14 voci → 255). Copertura `ApiKeysPage.jsx` (351 righe) + `apps/immoweb/api_keys.py` (199 righe · router `/api/app/api-keys`) + `apps/v1/gateway.py` (Bearer consumer `/api/v1/*`) + `shared/auth/api_key.py` (issuance/hash/require_api_key) + `shared/models/api_key.py` (ApiKeyInDB/Public/Create/IssueResponse). **Onestà D-051 pricing dual-track**: Track B = €0,03/cred vs Track A = €0,05/cred (wallet contabilmente separati). Endpoint `/api/v1/*` documentati con costi (valuator 5, mortgages 1, legal 3, feed/me/health 0, staging ~15). Plaintext `omk_live_<28chars>` show-once + hash SHA-256. NO auto-ricarica Stripe (top-up manuale), NO UI usage detail, NO reportistica per-partner, NO rate limit, NO scoping endpoint, NO IP whitelist, NO webhook, NO rotazione. Widget embed via `<script data-key data-widget>`. |

---

## 🚦 Smoke Cap. 20 — 3 query attese dopo reindex

1. **"Come emetto una nuova API key OMNIA? Posso rileggerla dopo?"** → top-1 atteso `20-api-keys-integrazioni.yaml::api-keys.emissione-show-once`
2. **"Quanto costa un credito Track B? È diverso dai piani B2B?"** → top-1 atteso `20-api-keys-integrazioni.yaml::api-keys.pricing-track-b`
3. **"Quali endpoint /api/v1 esistono? Come autentico?"** → top-1 atteso `20-api-keys-integrazioni.yaml::api-keys.api-v1-endpoints`

Criteri smoke: top-1 chunk_id atteso OR **stesso file** `20-api-keys-integrazioni.yaml` · sim ≥ 0.08.

---

## 🚦 Smoke Cap. 19 — 3 query attese dopo reindex

1. **"Come cambio il nome della mia agenzia in OMNIA?"** → top-1 atteso `19-impostazioni-agenzia.yaml::settings.sezione-identita` (o `settings.cos-e`)
2. **"Perché non riesco a modificare le impostazioni? Sono agency_admin invitato."** → top-1 atteso `19-impostazioni-agenzia.yaml::settings.permessi-ownership` (o `settings.errori-comuni`)
3. **"Dove attivo un piano OMNIA? Come funzionano i Founders?"** → top-1 atteso `19-impostazioni-agenzia.yaml::settings.billing-pagina-separata`

Criteri smoke: top-1 chunk_id atteso OR **stesso file** `19-impostazioni-agenzia.yaml` · sim ≥ 0.08.

---

## 🚦 Smoke Cap. 18 — 3 query attese dopo reindex

1. **"Esiste una pagina Notifiche o una Bell icon in OMNIA?"** → top-1 atteso `18-notifiche-attivita.yaml::notifiche.cos-e` (o `notifiche.limitazioni-v1`)
2. **"Quali email invia OMNIA automaticamente?"** → top-1 atteso `18-notifiche-attivita.yaml::notifiche.email-panoramica`
3. **"C'è un feed attività recenti nella dashboard?"** → top-1 atteso `18-notifiche-attivita.yaml::notifiche.dashboard-vs-activity-feed`

Criteri smoke: top-1 chunk_id atteso OR **stesso file** `18-notifiche-attivita.yaml` · sim ≥ 0.08.

---

## 🚦 Smoke Cap. 17 — 3 query attese dopo reindex

1. **"OMNIA registra il mio dominio a nome suo?"** → `17-domain-vault.yaml::domain.d-054-promise`
2. **"Come collego il mio dominio al sito OMNIA?"** → `17-domain-vault.yaml::domain.custom-domain-flow` ⚠️ **collision Cap. 8**: `sito.custom-domain` vince (stessa `domanda_naturale`, chapter overlap). Da disambiguare in task futuro.
3. **"Come verifico chi possiede un dominio prima di iscrivermi?"** → `17-domain-vault.yaml::domain.domain-checker-pubblico`

Criterio: top-1 chunk_id atteso OR **stesso file** `17-domain-vault.yaml` · sim ≥ 0.08.

---

## 🚦 Smoke Cap. 13 — 3 query attese dopo reindex (Fix RAG Feb 2026)

1. **"Come invito un collega nella mia agenzia?"** → top-1 atteso `13-team-ruoli.yaml::team.invitare-membro`
2. **"Quali ruoli posso assegnare a un collaboratore quando lo invito?"** → top-1 atteso `13-team-ruoli.yaml::team.ruoli-disponibili`
3. **"Posso rimuovere un membro dal team? Posso cambiare ruolo?"** → top-1 atteso `13-team-ruoli.yaml::team.limitazioni-v1` (dopo micro-fix Feb 2026 · pre-fix vinceva `ASPETTI_DA_APPROFONDIRE.md::71`)

Criteri smoke: top-1 chunk_id atteso OR **stesso file** `13-team-ruoli.yaml` · sim ≥ 0.08.

---

## 🚦 Smoke Cap. 14 — 3 query attese dopo reindex (Fix RAG Feb 2026)

1. **"Come importo immobili da un file XML del vecchio gestionale?"** → top-1 atteso qualunque chunk di `14-import-xml.yaml` (post fix Pattern B: `immobili.importare-xml` di Cap. 3 depreca)
2. **"Come evito di importare due volte lo stesso immobile via XML?"** → top-1 atteso `14-import-xml.yaml::import.dedupe`
3. **"Cosa NON fa Import XML? Posso usarlo per CSV o sync automatica?"** → top-1 atteso `14-import-xml.yaml::import.limitazioni-v1`

Criteri smoke: top-1 chunk_id atteso OR **stesso file** `14-import-xml.yaml` · sim ≥ 0.08.

---

## 🚦 Smoke Cap. 15 — 3 query attese dopo reindex (Fix RAG Feb 2026)

1. **"Come pubblico un immobile su Facebook e Instagram con un click?"** → top-1 atteso `15-social-publisher.yaml::social.pubblicare-immobile`
2. **"Su quali social posso pubblicare? Ci sono X/Twitter, TikTok o LinkedIn?"** → top-1 atteso `15-social-publisher.yaml::social.canali-supportati`
3. **"Il Social Publisher supporta scheduling analytics o LinkedIn?"** → top-1 atteso `15-social-publisher.yaml::social.limitazioni-v1` (dopo micro-fix Feb 2026 · pre-fix vinceva `social.collegamenti`)

Criteri smoke: top-1 chunk_id atteso OR **stesso file** `15-social-publisher.yaml` · sim ≥ 0.08.

---

## 🚦 Smoke Cap. 16 — 3 query attese dopo reindex

1. **"Quali campi devo compilare per passare compliance HARD?"** → top-1 atteso `16-compliance-portali.yaml::compliance.mapping-campi-immobile`
2. **"Perché un affitto risulta prezzo mancante?"** → top-1 atteso `16-compliance-portali.yaml::compliance.hard-prezzo-canone` (o `compliance.affitto-vs-vendita`)
3. **"Differenza fra violazione HARD e warning SOFT?"** → top-1 atteso `16-compliance-portali.yaml::compliance.soft-warning-qualita` (o `compliance.panoramica-validatore`)

Criteri smoke (post reindex Founder): top-1 chunk_id atteso OR **stesso file** `16-compliance-portali.yaml` · sim ≥ 0.08 (`CONFIDENCE_MIN`).

---

## 🚦 Smoke Cap. 11 — 3 query attese dopo reindex

1. **"Cos'è il Comparatore Mutui di OMNIA?"** → top-1 atteso `11-mutui-comparatore.yaml::mutui.cos-e`
2. **"Come viene calcolato il TAEG del mutuo?"** → top-1 atteso `11-mutui-comparatore.yaml::mutui.motore`
3. **"OMNIA è mediatore creditizio?"** → top-1 atteso `11-mutui-comparatore.yaml::mutui.disclaimer-tub` (risposta: **no**, art. 128-sexies TUB)

---

## 🚦 Smoke Cap. 9 — 1 query di verifica G-bis

Da eseguire dopo reindex per verificare la fix retrieval:

- **"Quanto costa un render Virtual Staging?"** → top-1 atteso **`09-virtual-staging.yaml::staging.crediti-costo`** (era `07-fascicolo-immobile.yaml::fascicolo.staging-nel-fascicolo` a sim 0.334 pre-fix). Confidence attesa ≥ 0.20.

---

## 🚦 Smoke Cap. 10 — 3 query attese dopo reindex

1. **"Cos'è HAL Agent in OMNIA?"** → top-1 atteso `10-hal-agent-crm.yaml::hal.cos-e`
2. **"A cosa serve il pulsante 'Migliora con HAL' nei form?"** → top-1 atteso `10-hal-agent-crm.yaml::hal.improve-titolo-descrizione`
3. **"Cosa NON può fare HAL Agent?"** → top-1 atteso `10-hal-agent-crm.yaml::hal.limiti-cosa-non-fa` (risposta: sola lettura, no legale, no web, no memoria fra sessioni, no foto)

Confidence attesa ≥ 0.15 su tutte e 3.

---

## 🚦 Smoke Cap. 9 — 3 query attese dopo reindex

1. **"Come faccio un render Virtual Staging?"** → top-1 atteso `09-virtual-staging.yaml::staging.lanciare-render` (o `staging.cos-e`)
2. **"Quanto costa un render Virtual Staging?"** → top-1 atteso `09-virtual-staging.yaml::staging.crediti-costo`
3. **"Posso rimuovere il watermark 'Render virtuale OMNIA'?"** → top-1 atteso `09-virtual-staging.yaml::staging.watermark` (risposta: **no**, obbligatorio AGCM + Art. 21)

Confidence attesa ≥ 0.15 su tutte e 3.

---

## 🚦 Smoke Cap. 8 — 3 query attese dopo reindex

Da eseguire dalla UI HAL Knowledge (o via `POST /api/app/hal/knowledge/ask`) subito dopo il reindex forzato successivo al deploy del Cap. 8:

1. **"Come collego il mio dominio al sito OMNIA?"** → top-1 atteso `08-sito-web.yaml::sito.custom-domain`
2. **"Come estraggo il brand dal mio sito esistente?"** → top-1 atteso `08-sito-web.yaml::sito.brand-extractor`
3. **"Quali temi posso scegliere per il sito?"** → top-1 atteso `08-sito-web.yaml::sito.temi-disponibili`

Confidence attesa ≥ 0.15 su tutte e 3.

---

## 🚦 Smoke Cap. 7 — 3 query attese dopo reindex

Da eseguire dalla UI HAL Knowledge (o via `POST /api/app/hal/knowledge/ask`) subito dopo il reindex forzato successivo al deploy del Cap. 7:

1. **"Quali documenti servono per portare un immobile a rogito?"** → top-1 atteso `07-fascicolo-immobile.yaml::fascicolo.checklist-rogito`
2. **"Come funziona la stima AI mostrata nel Fascicolo?"** → top-1 atteso `07-fascicolo-immobile.yaml::fascicolo.stima-ai`
3. **"Il Fascicolo mi ordina l'APE se non ce l'ho?"** → top-1 atteso `07-fascicolo-immobile.yaml::fascicolo.ape-partner` (risposta chiara: **no**, partner "in valutazione").

Confidence attesa ≥ 0.15 su tutte e 3 (similarity range simile a Cap. 5/6).

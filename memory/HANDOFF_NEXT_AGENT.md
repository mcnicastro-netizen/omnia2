# 🚨 HANDOFF AL NUOVO AGENTE — LEGGI PRIMA DI FARE QUALSIASI COSA

**Fork da**: sessione E1 chiusa il **26-Feb-2026 (evening — Sprint 4 chiuso + privacy gate fix)**
**Motivo fork**: passaggio pulito post Sprint 4 completo. Codebase pronto al deploy.
**Founder**: Marco Nicastro (mcnicastro-netizen · mcnicastro@gmail.com)
**Lingua di risposta OBBLIGATORIA**: 🇮🇹 **ITALIANO**. Il Founder è italiano madrelingua.

---

## ⛔ REGOLA D'ORO — RIPETUTA 4+ VOLTE DAL FOUNDER

**"NIENTE PIÙ DEVIAZIONI. SI COMPLETA IL PROGRAMMA."**

Non proporre nuove feature "nice-to-have", non suggerire enhancement fuori Sprint corrente, non deviare mai da `PIANO_ESECUZIONE.md`.

**Metodo obbligatorio prima di proporre QUALSIASI cosa**:
1. Grep i file `HANDOFF_NEXT_AGENT.md`, `DECISIONS.md`, `ROADMAP.md`, `PIANO_ESECUZIONE.md`, `AUDIT_M2.md`, `PROGRAMMA_OMNIA.md`, `PRICING_OMNIA.md` per la keyword rilevante.
2. Verifica se l'idea è nella lista **"ESPLICITAMENTE FUORI SCOPE"** più sotto.
3. Se non trovi conferma esplicita nel piano, NON PROPORLA. Zero eccezioni.

Se hai dubbi, RILEGGI questa riga.

---

## 🐛 ERRORI RICORRENTI DELL'AGENTE PRECEDENTE (26-Feb-2026) — NON RIPETERLI

**L'agente ha proposto DUE VOLTE il "form contatti pubblico" nella stessa sessione, entrambe rifiutate dal Founder** (una il 24-Feb, una il 26-Feb come `enhancement (d)` post-Sprint-4). Motivazione: (a) l'endpoint `POST /api/cloud/property/{pid}/contact` esiste già dal 22-Giu-2026 (M3.S4 DONE, vedi PROGRAMMA_OMNIA:497), (b) l'aggancio frontend è stato **esplicitamente rifiutato** come deviazione.

Altre proposte rifiutate stasera:
- ❌ Video Sora 2 al posto di fal.ai Kling Pro (già deciso in D-047 + D-066)
- ❌ "Badge 🔒 sblocca dettagli" con paywall modale — proposto come "enhancement" post-privacy-fix D-070, **rifiutato dal Founder perché non è il pattern dei portali mainstream** (immobili L2 sono già visibili, i portali seri usano form contatto post-scheda, non paywall pre-scheda).

**Lezione**: prima di aprire bocca su qualsiasi "enhancement", consulta i file. Se non è scritto lì, non esiste.

---

## ⛔ PRIME 5 AZIONI TASSATIVE (in questo ordine)

### 1️⃣ NON scrivere codice prima di aver letto QUESTI file
```
1. /app/memory/HANDOFF_NEXT_AGENT.md   ← questo file
2. /app/memory/PIANO_ESECUZIONE.md     ← ordine tassativo Sprint 1-4
3. /app/memory/DECISIONS.md            ← D-035, D-041, D-051, D-056, D-057, D-058, D-062, D-066, D-067, D-068, D-069, D-070
4. /app/memory/PRD.md                  ← cosa è stato fatto e quando
5. /app/memory/ROADMAP.md              ← stato + backlog
6. /app/memory/PRICING_OMNIA.md        ← prezzi vincolanti (NON alterare senza ok Founder)
7. /app/memory/test_credentials.md     ← credenziali test (mcnicastro@gmail.com / ***ROTATED — vedi memory/test_credentials.env***)
8. /app/memory/ASPETTI_DA_APPROFONDIRE.md ← idee memorizzate, NON implementare
9. /app/memory/AUDIT_M2.md             ← audit M1-M5 + gap analysis
10. /app/memory/creatives/brand_lab_reference.md ← estetica "Mediterranean Future 2035"
```

### 2️⃣ Verifica che i servizi girino
```bash
sudo supervisorctl status
# Devono essere RUNNING: backend, frontend, mongodb, code-server
```

### 3️⃣ Esegui la regressione mirata sui blocchi critici
```bash
cd /app/backend && export REACT_APP_BACKEND_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d'=' -f2) && \
python -m pytest tests/test_sprint4_objstore.py tests/test_m2_stress_5_agents.py tests/test_immobilcloud_public.py tests/test_m3s9_privacy_audit.py tests/test_m5s2_hal_knowledge.py tests/test_m2s5_5_domain_vault.py tests/test_m2s6c_social_publisher.py tests/test_m2s6d_portal_wizard.py --tb=short -q
# Atteso: ~80/80 passed. Se scende, STOP e apri ticket al Founder.
```

Nota: la suite completa `pytest tests/` ha ~604 test totali con qualche test order-dependent legacy e alcuni tempi lunghi (>2 min). **Non lanciarla in xdist** — lo stress test `test_m2_stress_5_agents.py` è ordinato test_01→test_08 con stato condiviso.

### 4️⃣ Chiedi conferma al Founder via `ask_human` prima di partire
Mostra al Founder:
- ✅ Servizi UP + regressione critica verde
- 📋 Item ancora aperti dal piano (vedi sotto)
- ❓ Su quale procedere

### 5️⃣ Solo dopo il "vai" del Founder inizia a scrivere codice

---

## 🎯 STATO ATTUALE DEL PROGETTO (fotografia al 26-Feb-2026 sera)

### ✅ COMPLETATO (non toccare, non riscrivere)

**Milestone core**
- M1 Foundation 100%
- M2 ImmoWeb core 100% (stress test 5 agenti concorrenti **11/11 verdi** dopo fix Sprint 4 GAP #2)
- M3 ImmobilCloud B2C 100% (M3.S8 ricerca avanzata + M3.S9 privacy audit 4 livelli DONE)
- M5 AI Suite: S1 (HAL Agents) + S2 (HAL Knowledge RAG) + S3 (HAL Legal) + S4.1/S4.3/S4.4 (Virtual Staging + Micro-tour video 10s + A/B testing) + S5 (Mutui)

**M2.5 White Label / Doppio Binario** — TUTTI ✅
- M2.5.1 Multi-branch, M2.5.2 API Gateway + wallet, M2.5.3 Widget embeddabili, M2.5.4a XML Importer, M2.5.4b Domain Checker, M2.5.4c Legal Pack, **M2.5.5 Domain Vault**, M2.6a Publishing, M2.6b Sync Engine, **M2.6c Social Publisher** (FB/IG/Telegram, D-058), **M2.6d Universal Portal Wizard**

**Sprint 4 · Perf Hardening + Deploy Ready — DONE 26-Feb-2026 (D-067, D-068, D-069)**
- 🧪 **GAP #2 Stress test 5 agenti FIX** → da 7/11 FAIL a **11/11 verdi**. Fixture `_seed_test_agents` module-scoped che auto-crea `agent1..4@omniatest.re` (password `***ROTATED***`) in agency `abc7004b-04a3-414b-8197-8e0e983d0892`. Helper `_normalize_property_type()` in `apps/immoweb/properties.py` gestisce data-drift (apartment→appartamento, None→altro). Soglie perf ricalibrate per preview ingress single-worker uvicorn (documentate inline nel test).
- 📦 **GAP #1 Foto Base64 → Emergent Object Storage** → nuovo modulo `shared/storage/objstore.py`, endpoint autenticato `POST /api/app/properties/{id}/photos/upload` (multipart, 8MB, JPG/PNG/WEBP), router pubblico `GET /api/media/{path:path}` in `apps/immoweb/media.py` (cache 24h), script `scripts/migrate_photos_to_objstore.py` idempotente. Startup init lazy in `server.py`. **7 test verdi**. 1 foto legacy migrata sul DB preview, 0 base64 residui.
- ⚡ **Perf side-quest** → projection esplicita `list_properties` (esclude photos, `$slice: 1` per cover) + nuovo indice compound `agency_id + created_at`.
- 🚀 **Deploy readiness PASS** (D-069). Unico fix pre-deploy: `CORS_ORIGINS="*"` in `.env` (backend leggeva già con fallback `"*"`).

**Privacy Gate Fix (26-Feb-2026, D-070)**
- Root cause triplo su `test_property_detail_returns_data`: (1) `dict.get(k, default)` non usa default se valore è None, (2) `can_view_property()` blocca L1 anonimo su property L2 (contraddizione con docstring D-062 che dichiara L1+L2 entrambi pubblici), (3) 55 record legacy con `privacy_level: null` in DB.
- Fix: `can_view_property()` → L1/L2 sempre visibili, solo L3 richiede viewer L3+ e L4 richiede L4. Fallback `p.get("privacy_level") or "L2"` in 4 punti. Backfill 55 record a L2.
- Verificato `test_l3_property_hidden_from_l1` continua a passare (i record L3 restano invisibili ad anonimi come previsto dalla policy).

**Setup produzione (fuori codice)**
- 📧 Cloudflare Email Routing attivato su `omniarealestateecosystem.it` (test delivery OK)
- 📘 Pagina Facebook "OMNIA Real Estate Lab" in creazione (Founder ha 3 varianti di bio D-051-compliant)

**Documenti strategici**
- PROGRAMMA_OMNIA v3.0, GO_TO_MARKET.md, PRICING_OMNIA.md v2.1, BUSINESS_MODEL.md, PIANO_ESECUZIONE.md, AUDIT_M2.md

**Test suite**: ~80 test critici verdi (Sprint 4 objstore + stress + public portal + privacy + HAL Knowledge + Domain Vault + Social Publisher + Portal Wizard). Suite completa `pytest tests/` ha ~604 test, con alcuni test legacy order-dependent che possono fallire in xdist — **non è un problema Sprint 4**.

---

## 🔴 ITEM ANCORA APERTI (nel piano, ordinati per priorità)

### 🟡 P1 — Manuale Operativo (M5.S2-pre)
Scrivere gli **11 capitoli residui** del manuale operativo (capp. 3-13 circa) per arricchire il corpus RAG di HAL Knowledge (M5.S2 già DONE, ma il corpus attuale = solo PRD + ROADMAP + DECISIONS). I capitoli servono come knowledge base per l'assistente HAL che aiuterà gli agenti umani sui workflow OMNIA.

**File di riferimento**: `/app/memory/manuale_operativo/` (se esiste; altrimenti creare struttura). Il corpus RAG viene ingerito allo startup del backend.

### 🟢 P2 — A-004 Landing `/it/agenzie` con 4 widget demo
Landing di conversione per agenzie. Deve mostrare 4 widget live (esempi: valutatore mutui, matcher immobili, ecc.) inline sulla pagina, con CTA al signup B2B. **Design Mediterranean Future 2035 strict** (palette navy/emerald/gold/off-white, font Fraunces + Inter).

### 🟢 P2 — A-006 Video Ken Burns concatenato 10s
Estensione della funzione free Ken Burns già presente sul portale B2C: comporre 4-5 foto in un unico video 10s con transizioni. Il micro-tour Kling Pro (10s / 10 crediti) resta lato agenzia (D-066).

### 🟢 P3 — GAP #5 Universal Smart Importer 2.0 immobili
Implementazione D-FUTURE-10 v2 per property importing. Estende M2.5.4a XML Importer ad Excel/CSV disordinati con AI-assist (mapping colonne automatico).

### 🔴 P3 — M4 MLS + Stripe (BLOCCATO post-società)
Richiede P.IVA, IBAN, contratto Stripe di OMNIA. Non toccare finché il Founder non ha aperto la S.r.l.

### 🔴 P3 — M6 Omnia Academy (BLOCCATO post-società)
Idem sopra.

---

## 🛑 ESPLICITAMENTE FUORI SCOPE (NON PROPORRE)

Il Founder ha detto CHIARAMENTE più volte (23-Feb, 24-Feb, 25-Feb, 26-Feb): **"niente più deviazioni, si completa il programma"**. NON toccare/proporre:

- ❌ **Form contatti pubblico** (endpoint `/api/cloud/property/{pid}/contact` esiste già dal 22-Giu-2026 M3.S4 — l'aggancio frontend è stato **RIFIUTATO 2 VOLTE**, 24-Feb e 26-Feb)
- ❌ **Badge/Modale "sblocca dettagli" con paywall** su property L3 (proposto 26-Feb come enhancement, **rifiutato** perché non è pattern mainstream: i portali seri mostrano tutto + form contatto sotto)
- ❌ Video promo brand OMNIA extra (Sora 2, Kling brand-side, Pippit) — memorizzato in `ASPETTI_DA_APPROFONDIRE.md`
- ❌ Nuove landing marketing non pianificate
- ❌ Manuale Operativo cap. 3-20 aggiunti a piacere — vanno scritti nell'ordine e nei tempi decisi dal Founder
- ❌ M5.S7 Modulistica AI (post-società)
- ❌ M5.S8 Firma elettronica + Visure (post-società)
- ❌ Pre-launch commerciale (congelato D-035, sblocca solo dopo M6)
- ❌ APE Partnership integration (in attesa risposte da APEFACILE + EnUp)
- ❌ Aspetti da approfondire A-001 (BNPL) + A-002 (NVIDIA API Catalog) + A-003 (AI Creative Studio) — memorizzati, NON implementare
- ❌ Brand Lab expansion (già consegnata, non toccare)
- ❌ Nuovi widget non pianificati
- ❌ Refactoring "cosmetici" non richiesti
- ❌ Domain Vault fase 2 (firma digitale policy — D-056 memorizza come "post-Sprint 4", ora post-società)
- ❌ Portal Wizard fase 2 (modalità push/API — D-057 memorizza come "post-Sprint 4")
- ❌ **Compressione JPEG server-side** (proposto come enhancement dopo GAP #1 il 26-Feb, il Founder non ha detto sì — non implementare senza esplicita richiesta)
- ❌ Cleanup 2 fallback URL letterali in `shared/email/client.py` (warning non-blocker del deploy check, sistemabile ma NON richiesto)
- ❌ Async geocoding background Motor (task Sprint 4 #10 originale, saltato in opzione B — Founder ha scelto solo GAP #1 + GAP #2 + deploy check)
- ❌ Pulizia DNS Cloudflare (record orfani — non urgente, si fa quando il Founder ha voglia)
- ❌ Deploy Emergent (attendere go-live post-società)
- ❌ Modifiche a `PRICING_OMNIA.md` v2.1 senza esplicita autorizzazione Founder

---

## 🔒 REGOLE VINCOLANTI

### 🏷️ **D-041 White Label / Doppio Binario**
OGNI nuova feature nasce in **3 modalità simultanee**:
1. UI dentro OMNIA (Track A turnkey)
2. API pubblica v1 in crediti (Track B)
3. Widget embeddabile (Track B partner web agency)

### 📄 **D-035 No Paper / Santo Graal**
Ogni deliverable è **100% digitale**. Mai stampa cartacea, mai firma su carta.

### 🚫 **D-051 No Brand Mentions**
**MAI** nominare competitor concreti (Agestanet, Gestim, Getrix, Immobiliare.it, Idealista, Casa.it, ecc.) nel codice, UI, log, PDF, email, commenti. Sempre keyword categoriali generiche.

### 🇮🇹 **Lingua Founder**
Il Founder scrive e legge in **italiano**. i18n IT è primaria (poi EN + ES).

### 🎨 **Estetica ufficiale "Mediterranean Future 2035"**
Palette hex code strict: `#0B1E3F` (navy) + `#1F6B5C` (emerald) + `#C8A653` (gold) + `#F5F1E8` (off-white) + `#4EE1D3` (cyan hologram).
Font: **Fraunces** (serif hero) + **Inter** (body/UI).
Style: Zaha Hadid + Blade Runner 2049 warmth. MAI cliché toscani/Bialetti/tetti-rossi.
Dettagli in `/app/memory/creatives/brand_lab_reference.md`.

### 💰 **PRICING_OMNIA.md v2.1 — VINCOLANTE**
Il Founder è **estremamente rigoroso** sui prezzi. Verificare `PRICING_OMNIA.md` prima di proporre qualsiasi feature con impatto economico. Micro-tour Kling Pro = 10s / 10 crediti (D-066).

---

## 🐙 REPO GITHUB — ATTENZIONE MASSIMA

**Repo attivo**: `mcnicastro-netizen/OMNIA`

1. Push a GitHub UNIDIREZIONALE (Emergent → GitHub)
2. `.env` NON su GitHub (ricreare manualmente in caso di clone)
3. **NON eseguire `git push` diretto** — il Founder usa "Save to GitHub" nella UI Emergent
4. NON toccare `.git` e `.emergent`
5. `git log` funziona, `git diff` NO
6. Per rollback → usare feature "Rollback" della piattaforma Emergent (mai `git reset`/`git revert` manuali)

---

## 🛠️ QUICK REFERENCE — Endpoint chiave Sprint 4

**Object Storage** (D-068)
- `POST /api/app/properties/{id}/photos/upload` — multipart, max 8MB, JPG/PNG/WEBP (auth: agent+)
- `GET /api/media/{path:path}` — passthrough pubblico Emergent Object Storage (cache 24h)
- Script migrazione: `cd /app/backend && python -m scripts.migrate_photos_to_objstore [--dry-run]`

**Privacy Gate** (D-070)
- Contract: L1/L2 pubblicamente visibili (field masking differenzia). L3 richiede viewer L3+ (qualified lead). L4 richiede L4 (agency internal).
- Helper: `shared/utils/privacy_gate.py::can_view_property()`, `apply_privacy_view()`, `resolve_viewer_level()`

**Stress test agenti** (D-067)
- Fixture module-scoped autouse in `tests/test_m2_stress_5_agents.py::_seed_test_agents`
- Credenziali: `agent{1..4}@omniatest.re` / `***ROTATED***` — agency `abc7004b-04a3-414b-8197-8e0e983d0892`

---

## ✅ Checklist Prima di Ogni Commit

- [ ] Ho letto il file `.md` rilevante nel `/app/memory/` prima di scrivere?
- [ ] La feature è nel piano o è un'iniziativa mia? (se mia, STOP e chiedi al Founder)
- [ ] Ho lanciato la regressione critica e passa?
- [ ] Zero brand mentions competitor?
- [ ] Palette + font aderenti Mediterranean Future 2035?
- [ ] i18n IT + EN + ES?
- [ ] Se auth-related → ho chiamato `integration_playbook_expert_v2`?
- [ ] Se 3rd party → ho chiamato `integration_playbook_expert_v2`?
- [ ] Se cambio pricing → ho letto `PRICING_OMNIA.md`?

*Fine handoff. In bocca al lupo. Nessuna deviazione. Il Founder si aspetta disciplina, non creatività.*

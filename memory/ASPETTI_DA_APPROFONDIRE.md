# 🔬 Aspetti da approfondire — OMNIA

> File di appoggio per **temi strategici/tecnici** che il Founder ha esplicitamente segnalato come "da rivedere più avanti", **senza essere ancora decisioni**. Ogni voce va promossa in `DECISIONS.md` o `ROADMAP.md` quando si decide di procedere.

**Ultimo aggiornamento**: Feb 2026 (post-Cap. 18 · Notifiche e attività · +A-017 → A-023)

> **Backlog qualità prodotto (A-006+)**: voci tracciate durante lo sprint manuale Cap. 1-18. Priorità assegnata da Cursor (P1=alto ROI/costo basso, P3=futuro). Decisione Founder post-manuale — **NON implementare senza "vai" esplicito**.

---

## 🟠 A-001 — BNPL B2B (Buy Now Pay Later) per contratti annuali OMNIA

**Data inserimento**: 05-Feb-2026
**Segnalato da**: Founder (Nicastro)
**Contesto**: Domanda spontanea del Founder — *"e se inserissimo oltre stripe anche una di quelle soluzioni che consentono il pagamento in tre/quattro mesi per i contratti annuali?"*

### Idea di fondo
Affiancare a **Stripe** una soluzione BNPL (rate senza interessi) per abbassare l'attrito d'acquisto sui **piani annuali OMNIA** (€1.490-3.600/anno). Il fornitore BNPL anticipa a OMNIA il 100% dell'importo (meno commissione ~3-6%) e si prende il rischio di credito.

### Perché ha senso (pro)
- **+30-50% conversion rate** stimato su piano annuale (dati aggregati Scalapay/Klarna B2B)
- **Cassa immediata annuale** vs. rischio churn mensile
- Difende il piano annuale dal churn (vincolo contrattuale)
- Segnale di maturità del brand vs. gestionali legacy (Findomestic/Compass sono standard nel settore)
- Psicologicamente il cliente percepisce "€124/mese × 12" invece dello shock di "€1.490 subito"

### Contro / rischi da studiare
- **Commissione 3-6%** → margine perso o da prezzare dentro
- **Complessità legale IT**: contratto tripartito, adempimenti Banca d'Italia B2B, GDPR condivisione dati con lender
- **Denial rate ~15-25%** → serve sempre Stripe come fallback visibile
- **Integrazione tecnica**: webhook stato rate, logica sospensione account su rata insoluta, coordinamento fatturazione IT (chi emette fattura, quando)

### Opzioni fornitori identificate (da valutare in profondità)
1. 🥇 **Scalapay B2B** — italiana, fino a 12 rate, commissione ~4-5%, adempimenti fiscali IT nativi, riconoscibile dai commercialisti agenzie *(da confermare copertura P.IVA)*
2. 🥈 **Klarna Business** — brand forte, fino a 24 rate, meno diffuso B2B IT, commissione più alta ~5-6%
3. 🥉 **Stripe Payment Plans / Capital** — rate integrate nel Payment Element esistente, un solo vendor, ~3-4%, meno brand awareness IT
4. 🏆 **Soisy / Findomestic Pay** — per contratti > €5K (franchise/LMS/multi-branch), istruttoria creditizia vera

### Strategia proposta (in bozza — NON ancora decisione)
- **Fase 1 (MVP)**: Stripe Payment Plans (zero nuovo vendor, riuso stack esistente)
- **Fase 2 (dopo 20-30 clienti)**: aggiungere Scalapay B2B se il segnale di conversione è forte
- **Fase 3 (enterprise)**: Soisy/Findomestic per contratti €10K+

### Timing consigliato (mia proposta)
**NON adesso**. Attivare **dopo M2.6b (Sync Engine)** e almeno insieme al primo push commerciale reale (verosimilmente dopo M2.5.4b Domain Checker come lead magnet). Il BNPL è ottimizzazione commerciale, non funzionalità core.

### Domande aperte per il Founder
1. Il target primario acquista già annuale cash, o vende principalmente mensile? *(se mensile → BNPL è killer feature)*
2. La commissione 4-5% va scaricata sul prezzo o assorbita?
3. Clausole di sospensione servizio se rata insoluta: come le vogliamo scritte nei ToS?
4. Timing lancio: prima del primo cliente enterprise, o dopo 10 clienti "normali" validati?

### Stato
🟠 **DA APPROFONDIRE** — Founder ha chiesto esplicitamente di memorizzare per rivederlo. Nessuna implementazione, nessuna decisione presa.

### Trigger di ripresa
- Definizione pricing definitivo v2 (M2.5.0)
- Primo cliente enterprise in pipeline
- Segnale espressivo di friction sul checkout Stripe annuale

---

## 🟠 A-002 — NVIDIA API Catalog (build.nvidia.com) come provider LLM complementare

**Data inserimento**: 05-Feb-2026
**Segnalato da**: Founder (Nicastro) — domanda spontanea *"nvidia ha aperto una porta tramite APIKEY per l'utilizzo di tutte le ia che la utilizzano?"*
**Contesto**: NVIDIA ha reso disponibile su `build.nvidia.com` un catalogo unificato con **1 API key (`nvapi-...`)** che sblocca 100-160+ modelli IA, endpoint OpenAI-compatible (`https://integrate.api.nvidia.com/v1`). Free tier: **1.000 crediti** senza CC (estendibili a 5.000), **nessuna scadenza**, rate limit 40 RPM. Uso produzione richiede licenza NVIDIA AI Enterprise (trial 90gg gratis).

### Perché è potenzialmente utile per OMNIA
Non è "sostituto" dell'Emergent LLM Key: è **complementare**. Ogni provider farebbe quello che sa fare meglio, al costo migliore. Architettura target:

```
HAL Chatbot (conversazioni utente)      → Gemini (Emergent LLM Key) — attuale
Analisi foto immobili (batch)           → Llama Vision (NVIDIA) — NEW
Embedding RAG manuale/Academy           → nv-embed-v2 (NVIDIA) — NEW
Parser XML legacy sporchi (M2.5.4a)     → DeepSeek V4 (NVIDIA) — opzionale
Contenuti creativi (annunci, email)     → Claude (Emergent LLM Key) — attuale
```

### 🎯 Use case #1 — Vision Auto-tagging foto immobili ⭐⭐⭐ (KILLER FEATURE candidata)
**Modello target**: Llama 3.2 Vision 90B (o equivalente vision-instruct del catalogo)
**Cosa fa**: L'agente carica 15 foto immobile → il sistema analizza automaticamente e produce:
- **Tag automatici**: "cucina moderna, parquet, doppia esposizione, terrazzo, ristrutturato"
- **Auto-compilazione descrizione base** dell'annuncio
- **Estrazione feature strutturate**: elettrodomestici incassati, isola centrale, tipo pavimento, esposizione stimata
- **Suggerimento stile Virtual Staging** più adatto (moderno/classico/scandinavo)
- **Compliance check foto** (utile a M2.6b Compliance Validator):
  - Foto duplicate/ripetute
  - Foto sfocate o sotto risoluzione minima
  - Watermark di altri portali visibili (rischio legale)
  - Presenza persone identificabili (GDPR)

**Perché NVIDIA e non Gemini Vision (già in casa)?**
- Gemini Vision consuma budget Emergent LLM Key
- Llama 3.2 Vision 90B via NVIDIA = **gratis** nei primi 1000 crediti, poi ~1/5 del costo Gemini
- Task batch: 100 foto × 50 immobili nuovi/mese = 5.000 chiamate/mese → risparmio sostanziale

**Timing consigliato**: candidato feature per **M2.7 (Post-Publishing Center)** o **M3.S8 (Property Enrichment)** — vedi ROADMAP quando definiremo il modulo.

**Effetto competitivo**: nessun gestionale italiano oggi ha auto-tagging AI delle foto → forte differenziatore in demo commerciale.

### 🎯 Use case #2 — Embedding gratuiti per HAL Knowledge (RAG) ⭐⭐⭐
**Modelli target**: `nv-embed-v2`, `nvidia/embed-qa-4` (embedding di livello SOTA)
**Cosa fa**: Quando arriveremo a **M5.S2 HAL Knowledge** (chatbot che consulta manuale operativo OMNIA + Academy) servirà una pipeline RAG con embedding vettoriali.

**Scala stimata**:
- Manuale Operativo: ~20 capitoli × ~500 chunk = ~10.000 embedding
- Omnia Academy (M6): ~500 lezioni × ~20 chunk = ~10.000 embedding
- Re-index periodici quando cambiano contenuti

**Perché NVIDIA**: su Emergent LLM Key gli embedding contano come chiamate. Su NVIDIA sono gratis nei 1000 crediti iniziali → risparmio silenzioso ma sostanziale su scala 20K+ embedding.

**Timing**: **prerequisito M5.S2 HAL Knowledge** (fase P2 del PROGRAMMA_OMNIA v3.0).

### ❌ Cose del catalogo NVIDIA che NON ci servono (evitare distrazioni)
- Modelli reasoning generici (GLM, Kimi K2, Nemotron 550B) → HAL usa già Gemini
- Modelli coding → il codice lo scriviamo noi
- Speech/TTS → fuori roadmap OMNIA
- Modelli biologia/scientifici → fuori dominio
- Modelli 3D/simulazione → Virtual Staging usa fal.ai specializzato

### ⚠️ Contro / rischi da considerare
- Rate limit 40 RPM → OK dev, non produzione con 100+ agenzie concorrenti
- Free tier "development only" ufficialmente → uso produzione richiede AI Enterprise license
- 2 sistemi di key management → un pizzico di complessità operativa in più
- Dipendenza da un ulteriore vendor esterno

### Strategia proposta (in bozza)
1. **Fase esplorativa** (30 minuti, gratuito): registrare account, ottenere `nvapi-...`, salvare in variabile env `NVIDIA_API_KEY` — chiave nel cassetto pronta all'uso
2. **Fase POC Vision** (~4 ore): prototipo di auto-tagging foto su 20 immobili demo, valutare qualità output vs Gemini Vision
3. **Fase decisione**: se qualità ≥ Gemini e costo < Gemini → promuovere ad architettura ufficiale in M2.7 / M3.S8
4. **Fase produzione**: valutare se serve licenza AI Enterprise o se restiamo self-hosted con NIM container

### Domande aperte per il Founder
1. Vogliamo che OMNIA offra auto-tagging AI delle foto come **feature commerciale visibile** (differenziatore vs competitor) o come feature interna (miglior UX agente)?
2. In caso di uso produzione: preferiamo licenza AI Enterprise (SaaS pronto) o self-hosting NIM (sovranità dati per clienti enterprise/GDPR-sensibili)?
3. Timing: aspettiamo M5.S2 HAL Knowledge per attivarlo su embedding, o partiamo prima con la POC Vision?

### Stato
🟠 **DA APPROFONDIRE** — Founder ha confermato interesse (opzione "a" del 05-Feb-2026). Nessuna implementazione avviata, nessuna chiave ancora generata.

### Trigger di ripresa
- Definizione modulo M2.7 (post-Publishing Center) o M3.S8 (Property Enrichment)
- Avvio pianificazione M5.S2 HAL Knowledge (embedding RAG)
- Richiesta esplicita cliente enterprise di sovranità dati AI (self-hosted NIM)

---

## 🟠 A-003 — AI Creative Studio (Brand Analysis + Multi-format Generation + Editor Integrato)

**Data inserimento**: 20-Feb-2026
**Segnalato da**: Founder (Nicastro)
**Contesto**: Il Founder ha condiviso la specifica di un "AI Creative Studio" per agenzie immobiliari — evoluzione naturale del Marketing Autopilot già previsto nel pilastro D-045.

### 🎯 Cosa fa
Un modulo che permette a un'agenzia (o a un privato B2C su ImmobilCloud) di generare in automatico tutti i materiali marketing di una campagna partendo dal proprio sito web.

### 🧩 Le 3 componenti chiave

**1️⃣ Analisi del Brand automatica**
- Input: URL del sito web dell'agenzia
- L'AI estrae automaticamente:
  - 🎨 **Identità visiva** — palette colori, font, stile grafico
  - ✍️ **Tono di voce** — formale/informale, tecnico/emotivo, tagline ricorrenti
  - 🏷️ **Elementi brand** — logo, valori, target implicito

**2️⃣ Generazione Multiformato**
Da un singolo brief l'AI produce contemporaneamente:
- 📸 **Inserzioni pubblicitarie statiche** (Facebook Ads, Instagram Feed, Instagram Stories)
- 📱 **Post social media** (formato quadrato, verticale 9:16, carosello)
- ✉️ **Sequenze email** (welcome, nurturing, follow-up post-visita)
- 🎬 **Script video UGC** (User-Generated Content style, ottimizzati per TikTok/Reels)
- Ogni asset è ottimizzato per la piattaforma target (dimensioni, hook, CTA, copy length)

**3️⃣ Editor integrato**
- 🔀 **Browser proposte** — sfogliare varianti grafiche multiple per lo stesso brief
- 💬 **Chat di personalizzazione** — modificare hook, tagline, CTA via conversazione naturale con HAL
- ✂️ **Rifinitura pre-export** — micro-editing su testi, colori, immagini prima di scaricare/pubblicare

### 🏗️ Base già disponibile in OMNIA (precursore in casa)
Il **Brand Profile Extractor** (M2.S5 Layer D Phase 1, D-023) fa già il 60% del punto 1️⃣:
- `POST /api/app/website/extract-from-url` accetta un URL
- Usa BeautifulSoup + Gemini via Emergent LLM Key
- Restituisce: palette (4 hex), typography (family+scale), structure, voice (tone+tagline), logo_hint, confidence 0-100
- Persistito in `agency.website.extracted_profile`
- Testato su tecnocasa.it con confidence 95

Quando svilupperemo A-003 ripartiremo da QUESTO endpoint estendendolo, non da zero.

### 🎯 Modalità di consumo (D-041 White Label — 3 modalità obbligatorie)
- **UI OMNIA** — sezione "Studio Creativo" dentro CRM agenzia con wizard 3-step (Brand → Brief → Editor)
- **API v1 pubblica** — `POST /api/v1/creative/generate` con crediti (verosimilmente 10-25 per generazione full-set)
- **Widget embeddabile** — "Studio Creativo mini" per privati sul portale ImmobilCloud (generazione post social per l'annuncio del proprio immobile)

### 📄 No Paper (D-035) — implicito
Delivery 100% digitale: file scaricabili (PNG/MP4/PDF email), pubblicazione diretta su FB/IG/Telegram via M2.6c Social Publisher (quando pronto), zero output cartaceo.

### 🤖 Stack AI candidato (da valutare al momento dello sviluppo)
- **Estrazione brand**: Emergent LLM Key (Gemini) — già in uso
- **Copy generation** (annunci, post, email): Claude Sonnet via Emergent (miglior naming/tono in italiano)
- **Immagini/creativity**: 
  - Nano Banana (Gemini image gen) per varianti rapide
  - GPT Image 1 per output pubblicitario più curato
  - fal.ai (già in casa per Virtual Staging) per composizioni immobile+creativo
- **Script video UGC**: Claude per lo storyboard + Sora 2 per la generazione video (opzionale, alto costo)

### 🔗 Sinergie forti con moduli esistenti/pianificati
- 🧠 **HAL Copywriter** (M5.S1) — già scrive titolo/descrizione immobili → estenderlo a copy adv
- 🎨 **Virtual Staging** (M5.S4) — già genera visual immobili → riusare come "base immagine" per ads
- 📤 **M2.6c Social Publisher** — quando pronto, publish diretto dagli asset generati qui
- 🏢 **Multi-branch/Franchise** (M2.5.1) — asset con brand della singola filiale, non del gruppo (co-branding)
- 🤝 **Partner Web Agency** (D-046) — potente killer widget per la loro offerta ai clienti finali

### ⚠️ Contro / rischi da studiare
- **Costo compute alto** su generazione video (Sora 2 = €0,50-1,50/clip) → serve pricing "à la carte"
- **Qualità output pubblicitario** vs strumenti dedicati (Canva Magic Studio, AdCreative.ai) → dobbiamo essere "buoni abbastanza" non "i migliori", vantaggio è integrazione con il CRM immobiliare
- **Rights management immagini** — le foto dell'immobile sono dell'agenzia, ma se rigeneriamo con AI (stile, mix) chi le possiede? Serve TOS chiaro
- **AGCM/pubblicità comparativa** — attenzione a claim generati automaticamente ("il migliore", "il più", ecc.) che potrebbero violare regole pubblicità immobiliare

### Domande aperte per il Founder
1. Target primario: **agente professionista** (uso quotidiano nel CRM) o **privato B2C** (uso occasionale sul portale)? Cambia sostanzialmente le UX e il pricing.
2. Formato prioritario di lancio: **statici Facebook/Instagram** (più semplice, valore immediato) o **video UGC TikTok/Reels** (più wow, più costoso)?
3. Vogliamo pubblicare direttamente sui social (richiede token FB/IG dell'utente) o solo generare + scaricare per pubblicazione manuale?
4. Pricing: pay-per-generation (crediti) o piano mensile "creative studio" separato?

### Timing consigliato
**NON ora**. Prerequisiti tecnici e strategici:
- ✅ M2.5.4c Legal Templates (in coda)
- ✅ M2.5.5 Domain Vault (in coda)
- 🎯 **M2.6c Social Publisher** — auto-post FB/IG/Telegram (dà il canale di delivery)
- 🎯 **M5.S2 HAL Knowledge** — HAL deve conoscere la voice della singola agenzia via RAG
- Idealmente: dopo aver definito pricing v3 (unit economics stabili) e aver validato i primi 20 clienti Track A

### Stato
🟠 **DA APPROFONDIRE** — Founder ha esplicitamente chiesto di memorizzare per svilupparlo più avanti. Nessuna implementazione avviata.

### Trigger di ripresa
- Completamento M2.6c Social Publisher (dà il canale di distribuzione)
- Feedback dai primi clienti su carenza di materiale creativo
- Feedback da web agency partner interessate a rivendere il modulo
- Definizione pricing v3 con "creative credits" separati dal wallet API

---

<!-- Aggiungere qui nuovi aspetti da approfondire con progressivo A-004, A-005, ... -->

---

## A-004 — Landing `/it/agenzie` con demo widget live embeddati (24-Feb-2026)

### Contesto
Con la chiusura di Sprint 1.5 recovery (D-059) i 4 widget di M2.5.3 sono tutti live e serviti pubblicamente dal loader `/api/widgets/v1/loader.js`:
- Valuator (UNI 10750)
- Mortgages Compare
- Virtual Staging demo
- HAL Legal Q&A

Oggi il pubblico esterno non li vede: sono strumento tecnico per web agency partner Track B. La landing `/it/agenzie` (target: gestionali italiani legacy da aggredire con il pivot Doppio Binario) è oggi puramente **brochure/testuale**.

### Idea
Trasformare la landing da "brochure che racconta" a **demo interattiva che dimostra**: 4 widget embeddati dentro la pagina stessa via lo snippet 1-line ufficiale (dogfooding). Il visitatore Trackk B non deve immaginare cosa può integrare — lo tocca sulla pagina di vendita.

### Perché ha valore
- **Prova live** = conversione superiore rispetto a screenshot statici (pattern Stripe / Cal.com / Linear).
- **Dogfooding**: se il nostro widget non regge il carico sulla landing di vendita, la scopriamo prima del cliente.
- **SEO**: pagina interattiva riduce bounce rate, aumenta dwell time — segnali positivi per search.
- **Zero maintenance**: usa esattamente lo stesso loader.js dei partner, nessuna forkatura di codice.

### Elementi tecnici
- 4 sezioni della landing, ognuna con un widget embeddato via `<div data-widget="staging"><script src=".../loader.js" data-key="omk_demo_..."></script>`.
- API key dedicata `omk_demo_*` con **rate-limit stretto** (5 req/min per IP) e credit balance dedicato + eventualmente allowed_origins = solo `omniarealestateecosystem.it`.
- Copy affiancato ad ogni widget che descrive il caso d'uso.

### Vincoli / rischi
- **Zero brand mentions** dei competitor (vincolo assoluto Founder).
- **Abusi**: la landing è pubblica → serve rate-limit robusto per prevenire quota-exhaustion via demo.
- **AGCM / pubblicità immobiliare**: dimostrare Virtual Staging pubblicamente OK, ma la valuazione UNI 10750 sul widget demo deve avere disclaimer chiaro "valore orientativo" (già presente nel widget stesso).

### Timing consigliato
**Congelato fino a M6 chiuso (D-035)**. Nessun pre-launch commerciale prima dell'Academy. Riprendere dopo Sprint 4 (perf hardening) e prima del go-live commerciale.

### Stato
🟠 **DA APPROFONDIRE post-M6** — Idea generata dall'agente durante Sprint 1.5 recovery, memorizzata su richiesta del Founder ("memorizzalo e metti in coda al fine programma").

### Trigger di ripresa
- Chiusura M6 Omnia Academy (unlock pre-launch commerciale, D-035)
- Rilascio pubblico di `/it/agenzie` come landing di conversione Track B
- Sopravvivenza dei 4 widget a stress test 5 agenti paralleli (GAP #2 audit M2, Sprint 4)

---

## 🟠 A-005 — HAL Assist · supporto ticket con remediation guidata (e remote assist futuro)

**Data inserimento**: 06-Ago-2026
**Segnalato da**: Founder (Nicastro)
**Contesto**: Durante la stesura del Manuale Operativo (Cap. 7–9) e HAL Knowledge RAG, il Founder ha immaginato un upgrade futuro: **HAL sul gestionale conosce abbastanza prodotto/codice da intervenire quando un cliente apre un ticket** — idealmente con **autorizzazione esplicita del titolare**, in stile assistenza remota (AnyDesk / TeamViewer / co-browsing).

> **Nota di scope**: questa idea è **indipendente** da altri progetti esterni (es. repo open source di social listening). Resta **interna all'ecosistema OMNIA / ImmoWeb**.

### 🎯 Visione Founder (north star)
Dopo consenso del cliente, HAL **non solo spiega** ma **risolve** il problema (sync portali, compliance, configurazione, HAL reindex, ecc.) — riducendo carico L1/L2 umano e tempi di risoluzione.

### Cosa esiste già (base da non rifare)
| Modulo HAL attuale | Ruolo |
|--------------------|--------|
| **HAL Knowledge** | How-to utente (manuale YAML + GAP + doc interni) |
| **HAL Agent CRM** | Chat + tool CRM read-only + *Migliora con HAL* su annunci |
| **HAL Legal** | Q&A giuridico con citazioni (dominio separato) |

A-005 è un **quarto pilastro**: **HAL Assist** orientato a **ticket + remediation**, non sostituto degli altri.

### Architettura proposta (fasi — dalla più realistica alla più ambiziosa)

**Fase 1 — Ticket intelligence (MVP)** 🟢 fattibile
- Classificazione automatica ticket (Portali / Fascicolo / Billing / HAL / Import…)
- RAG su: manuale + GAP + CHANGELOG + DECISIONS + **playbook per categoria** (10–15 scenari ricorrenti)
- Output: diagnosi probabile + checklist verifica + bozza risposta al cliente
- Escalation umana sotto soglia confidence (allineato D-051)

**Fase 2 — Fix in-app con consenso** 🟢 fattibile (core OMNIA)
- Azioni **whitelist server-side** eseguibili solo dopo click *"Autorizzo HAL Assist"* del **titolare** (`agency_admin`)
- Esempi candidati: sync manuale portale, reindex HAL agenzia, reset flag compliance preview, riapertura wizard dominio
- **Audit log immutabile** (chi, quando, cosa, esito) — prerequisito legale

**Fase 3 — Guida in-app / co-browsing** 🟡 medio termine
- HAL evidenzia passi nell'UI ImmoWeb (tooltip, tour contestuale sul ticket)
- Opzionale: session replay / screen share **solo dentro l'app** (no desktop intero)
- Utente conferma ogni step sensibile

**Fase 4 — Supporto umano + HAL copilot** 🟡 medio termine
- Operatore OMNIA in sessione remota (AnyDesk/TeamViewer) **solo su escalation**
- HAL prepara diagnosi, script e monitora — **umano al mouse**, HAL in cuffia
- Durata limitata (es. 30 min), consenso scritto, registrazione opzionale

**Fase 5 — Remote unattended (HAL risolve da solo sul PC cliente)** 🔴 R&D / long-term
- Tecnologia emergente (*computer use*, vision + automazione desktop)
- **Non raccomandato** come target produzione B2B immobiliare nei prossimi 1–2 anni: GDPR, responsabilità civile, affidabilità click, variabilità PC cliente
- Per un CRM **cloud** la maggior parte dei fix **non richiede** accesso al desktop

### Corpus tecnico (cosa indicizzare — NON "tutto GitHub")
- ❌ Indicizzare l'intero repo grezzo → rumoroso, costoso, rischio allucinazioni
- ✅ Sottoinsieme curato:
  - Playbook ticket + messaggi errore HTTP (`detail=...`) mappati a cause
  - Router/moduli per area ad alto volume ticket (publishing, fascicolo, staging, billing, hal_knowledge)
  - GAP.md, DECISIONS.md, runbook operativi Founder
  - Test pytest come "specifica comportamentale" (estratti, non raw)

### Perché AnyDesk non è il primo passo
ImmoWeb è **SaaS browser-based**. I ticket tipici si risolvono **in cloud** (sync, compliance, crediti, permessi). AnyDesk serve solo per edge case locali (cache browser, antivirus, file Excel import sul PC) — **minoranza** del volume.

### ⚠️ Rischi / vincoli (da risolvere prima di promuovere a DECISIONS)
- **D-051 onestà**: HAL non deve promettere fix o UI inesistenti
- **Multi-tenant**: zero leak dati tra agenzie nel contesto ticket
- **GDPR / consenso**: remediation = trattamento dati; serve base giuridica + ToS + log
- **Responsabilità**: azioni su annunci/portali/prezzi → serve human-in-the-loop o whitelist stretta
- **Costo LLM**: ogni ticket con retrieval largo va budgettato (crediti supporto o piano Agency)
- **Manutenzione**: reindex corpus tecnico ad ogni release, altrimenti HAL "conosce il codice di ieri"

### Relazione con altri HAL (naming)
- Brand utente sempre **HAL** (mai "AL" nel prodotto/supporto)
- Proposta nome modulo: **HAL Assist** o **HAL Support**
- Distinto da HAL Knowledge (FAQ) e HAL Legal (normativa)

### Timing consigliato
**NON ora** — dopo:
- Manuale operativo ≥ **50%** (Cap. ~13+) o catalogo **15+ playbook ticket** ricorrenti osservati in preview/pilot
- Sistema ticket formalizzato in ImmoWeb (anche minimale: form + stato + assegnazione)
- HAL Knowledge stabile su corpus manuale (≥ 100 voci, smoke test routine)

**Ordine suggerito**: Fase 1 → Fase 2 → Fase 3/4 → valutare Fase 5 solo se volume supporto lo giustifica.

### Domande aperte per il Founder
1. Ticket system: **interno ImmoWeb** o integrazione esterna (Zendesk, Freshdesk, email)?
2. Chi può autorizzare remediation: **solo titolare** o anche agente senior?
3. Fix automatici ammessi in v1: quali 5 azioni whitelist sono accettabili legalmente?
4. Remote desktop: **mai**, **solo escalation umana**, o **pilota HAL+umano**?
5. Pricing: HAL Assist incluso in Agency o add-on support premium?

### Stato
🟠 **DA APPROFONDIRE** — Founder ha chiesto esplicitamente di annotare come possibile future upgrade (06-Ago-2026). Nessuna implementazione, nessuna decisione presa.

### Trigger di ripresa
- Primi **10+ ticket ricorrenti** catalogati con causa root nota
- Apertura canale supporto ufficiale (post-M6 o post-primi Founders)
- Manuale + GAP coprono moduli ad alto volume ticket (Portali, Fascicolo, Staging, Billing)
- Richiesta esplicita cliente Agency di SLA / assistenza proattiva

---

# 📋 Backlog qualità prodotto (A-006 → A-016)

Voci **tracciate durante lo sprint manuale Cap. 1-15** (Feb 2026).
Origine: **Cursor review** dei moduli documentati + **Emergent Spark** filtrati.
Priorità assegnata da Cursor. **Nessuna decisione Founder presa** — attende review post-manuale.

**Voce già chiusa** ✅ (non elencata):
- `chunk_id` in `/ask` sources[] — fix applicato Feb 2026, in `main` su GitHub. Non serve tracking.

---

## 🟢 A-006 — Tooltip badge confidence su HalKnowledgePage

**Data inserimento**: Feb-2026
**Segnalato da**: Emergent Spark Cap. 12 (HAL Knowledge)
**Contesto**: Il badge di confidence (verde/ambra/rosso) mostra colori senza spiegazione inline in UI. Il Cap. 12 del manuale spiega le soglie 0.08/0.20, ma l'utente medio non le conosce.

### Perché ha senso (pro)
- Chiude cerchio *"HAL spiega HAL"* — riduce ticket ricorrenti tipo *"cosa significa il colore?"*
- Effort ~15 min (tooltip Shadcn/UI già disponibile in codebase)
- Zero rischio regressione — additivo puro

### Contro / complessità
- Zero revenue diretto — solo qualità supporto

### Priorità
**P1** · effort molto basso · ROI supporto alto

### Timing consigliato
Post-manuale (dopo primi 5-10 utenti che hanno chiesto info sui colori)

### File coinvolti
- `frontend/src/apps/immoweb/HalKnowledgePage.jsx` — aggiungere `<Tooltip>` inline al badge

### Aggiornamento manuale post-ship
- Cap. 12 § *"12.3 Come leggere la risposta"* — aggiungere nota *"il tooltip UI ripete la definizione"* (D-051)

### Domande aperte per il Founder
Nessuna — decisione autonoma implementazione se il Founder dice "vai".

### Stato
🟢 **DA APPROFONDIRE** — attende OK Founder

---

## 🟢 A-007 — Rimozione membro agenzia (endpoint + UI minima)

**Data inserimento**: Feb-2026
**Segnalato da**: Emergent Spark Cap. 13 (Team & Ruoli)
**Contesto**: Cap. 13 §13.12 dichiara onestamente *"NO rimozione membro in UI"* come limite v1. È il primo gap che i titolari incontreranno appena un collaboratore lascia l'agenzia.

### Perché ha senso (pro)
- **Primo pain reale** dei titolari dopo l'invito (ciclo vita completo)
- Piccolo endpoint + un bottone conferma sulla pagina Collaboratori
- Onestà D-051 già scritta nel manuale — colmando il gap chiudi l'anello

### Contro / complessità
- **Vincoli anti-lock obbligatori** (spec di sicurezza):
  - No `self-remove` (agency_admin non può rimuovere se stesso)
  - No `last-owner-remove` (non si può rimuovere l'ultimo `agency_admin` di un'agenzia)
  - No rimozione di `owner_id` dell'agenzia (transfer ownership è flusso separato)
- Distinzione tra *"remove from agency"* (unlink `agency_ids`) vs *"delete user"* (mai fare)

### Spec minima
- `DELETE /api/app/agencies/me/members/{user_id}` · `require_roles("agency_admin", "super_admin")`
- Errori espliciti: `403 self_remove_forbidden`, `400 last_owner_forbidden`, `404 member_not_found`
- Behavior: `$pull` da `users.agency_ids`, no cancellazione utente

### Priorità
**P1** · effort medio (2-3h backend + 1h UI) · pain concreto documentato

### Timing consigliato
Post-manuale (Founder ha detto che discuterà tutto a fine manuale)

### File coinvolti
- `backend/apps/immoweb/agencies.py` — nuovo endpoint DELETE
- `frontend/src/apps/immoweb/MembersPage.jsx` — bottone Rimuovi con `AlertDialog` conferma

### Aggiornamento manuale post-ship
- Cap. 13 §13.7 — aggiungere sezione *"Rimuovere un membro"* con 3 vincoli
- Cap. 13 §13.12 — spostare la voce da "limiti v1" a "risolto post-v1.0"
- YAML: aggiornare `team.limitazioni-v1` (rimuovere "NO rimozione membro") + nuova voce `team.rimuovere-membro`

### Domande aperte per il Founder
1. Confermi i 3 vincoli anti-lock (self, last-owner, owner_id) o vuoi variarli?
2. Cosa vede il membro rimosso al login successivo — pagina *"Nessuna agenzia collegata"* o auto-logout?

### Stato
🟢 **DA APPROFONDIRE** — attende OK Founder

---

## 🟡 A-008 — Cambio ruolo membro post-join (estensione A-007)

**Data inserimento**: Feb-2026
**Segnalato da**: Cursor (gap manuale Cap. 13, non Spark ma correlato ad A-007)
**Contesto**: Cap. 13 §13.10 documenta onestamente che un `agent` non può essere promosso a `agency_admin` post-accept via invito (upgrade role solo se pre-role era `client`). Workaround attuale: revoke+re-invite via super_admin backend.

### Perché ha senso (pro)
- Spesso richiesto **insieme ad A-007** (rimozione = caso limite di gestione membri)
- Evita workaround revoke+re-invite che perde storico
- Onestà D-051 già scritta nel manuale

### Contro / complessità
- **Audit trail obbligatorio**: chi ha promosso chi, quando (nuova collezione `member_role_changes` o campo su `users`)
- **Edge case**: `agent → agency_admin` OK; `agency_admin → agent` = degradazione (attenzione al vincolo *"almeno un agency_admin per agenzia"*, cfr. A-007)
- **Permessi**: solo `agency_admin` può promuovere, solo `super_admin` può degradare (o entrambi possono fare entrambe?)

### Spec minima (alternativa)
Due alternative da valutare:
- **A**: `PATCH /api/app/agencies/me/members/{user_id}/role` con body `{"role": "agent"|"agency_admin"}`
- **B**: Documentare formalmente il flusso re-invite (più semplice ma perde continuity utente)

### Priorità
**P2** · effort medio-alto se `A` scelto, minimo se `B` scelto

### Timing consigliato
Post-manuale, insieme ad A-007 (stessa pagina UI = stesso rilascio)

### File coinvolti
- `backend/apps/immoweb/agencies.py` — nuovo endpoint PATCH (se A)
- `frontend/src/apps/immoweb/MembersPage.jsx` — select ruolo inline sulla riga membro
- Nuova collezione `member_role_changes` (audit) — opzionale ma consigliato

### Aggiornamento manuale post-ship
- Cap. 13 §13.3 — aggiungere sezione *"Cambiare ruolo a un membro esistente"*
- Cap. 13 §13.12 — rimuovere "NO cambio ruolo post-join" dai limiti v1
- YAML: aggiornare `team.ruoli-disponibili` + `team.limitazioni-v1`

### Domande aperte per il Founder
1. Scegli A (endpoint dedicato) o B (documenta re-invite)?
2. Se A: chi può degradare `agency_admin → agent` — solo `super_admin` o anche altri `agency_admin`?
3. Audit visibile in UI o solo server-side?

### Stato
🟡 **DA APPROFONDIRE** — attende decisione Founder A vs B

---

## 🟡 A-009 — Bulk-assign agente post-import XML

**Data inserimento**: Feb-2026
**Segnalato da**: Emergent Spark Cap. 14 (Import XML)
**Contesto**: Cap. 14 §14.10 documenta che gli immobili importati **non hanno `agent_id`** — vanno assegnati manualmente. Su import da 100+ immobili questo diventa un pain significativo.

### Perché ha senso (pro)
- Post-migrazione il titolare risparmia 5-10 minuti di ricerca manuale
- Sfrutta i metadati `_import_source` e `_import_reference` già in DB (documentati Cap. 14)
- Post-import è un "momento naturale" per fare bulk assign

### Contro / complessità
- **NON è "30 secondi"** come dichiarato inizialmente. Serve:
  - Filtro `_import_reference` (o timestamp import) nell'endpoint list `properties`
  - Nuovo endpoint `POST /properties/bulk-update-agent` (o estendere bulk-edit esistente Cap. 3)
  - UI: bottone post-commit *"Assegna agente a questi X immobili"* → apre modal con select agente
- **Distinzione tra "appena importati"** e **"già assegnati"** — meglio non sovrascrivere se già assegnato
- Nessun endpoint bulk-update-agent esiste oggi (da verificare)

### Priorità
**P2** · effort medio-alto · dipendenze non triviali

### Timing consigliato
Post-manuale, con priorità sotto A-006/A-007 (che coprono casi più frequenti)

### File coinvolti
- `frontend/src/apps/immoweb/pages/ImportXmlPage.jsx` — bottone post-commit
- `backend/apps/immoweb/xml_import.py` — restituire lista `inserted_ids` nel commit response
- `backend/apps/immoweb/properties.py` (o simile) — endpoint bulk-update-agent + filtro `_import_reference`

### Aggiornamento manuale post-ship
- Cap. 14 §14.10 — rimuovere "no assegnazione automatica agente"
- Cap. 14 §14.12 checklist — aggiornare step 10 *"Assegna agente"* con la nuova UI
- YAML: aggiornare `import.limitazioni-v1` + nuova voce `import.bulk-assign-agente`

### Domande aperte per il Founder
1. Il bottone deve essere **subito post-commit** (nel result) o come sezione separata *"Ultimi immobili importati"* nella pagina Import?
2. Assegnare un solo agente a tutti, o ripartizione round-robin fra N agenti?

### Stato
🟡 **DA APPROFONDIRE** — attende decisione UX Founder

---

## 🟡 A-010 — Storico import XML lato UI

**Data inserimento**: Feb-2026
**Segnalato da**: Cursor (gap manuale Cap. 14, non Spark)
**Contesto**: Cap. 14 §14.10 documenta *"NO storico import UI"*. Oggi i metadati `_import_source` e `_import_reference` sono per-immobile in `properties`, ma non c'è un pannello aggregato *"cosa ho importato e quando"*.

### Perché ha senso (pro)
- Audit/trust per migrazioni ripetute
- Titolare vuole sapere *"quel batch di 50 immobili l'ho importato a Novembre o Ottobre?"*
- Utile a super_admin per debug problemi post-import
- Base per futuro rollback batch (A-xxx futuro)

### Contro / complessità
- **Struttura dati da decidere**: nuova collezione `import_batches` (id, agency_id, user_id, filename, count, timestamp, `_import_reference` shared) o aggregate query on-the-fly
- Ritenzione: da definire (per sempre, 90gg, 1 anno?)
- Modifica `xml_import.py` per creare record batch a ogni commit

### Priorità
**P2** · audit-driven · non blocca operatività

### Timing consigliato
Dopo primi clienti che hanno fatto migrazione (feedback reale)

### File coinvolti
- Nuova collezione `import_batches` (o simile)
- `backend/apps/immoweb/xml_import.py` — creare record batch nel commit
- Nuova rotta `/it/app/import/history` o tab nella pagina Import esistente

### Aggiornamento manuale post-ship
- Cap. 14 §14.10 — rimuovere "no storico UI"
- YAML: aggiornare `import.limitazioni-v1` + nuova voce `import.storico-batch`

### Domande aperte per il Founder
1. Nuova collezione o aggregate su properties?
2. Retention log (90gg, 1y, per sempre)?
3. Anche stats aggregate (X immobili importati totali, ultimo import quando)?

### Stato
🟡 **DA APPROFONDIRE** — attende decisione Founder

---

## 🟠 A-011 — Social Publisher · scheduling minimal

**Data inserimento**: Feb-2026
**Segnalato da**: Emergent Spark Cap. 15 (Social Publisher)
**Contesto**: Cap. 15 §15.11 documenta *"NO scheduling"* come primo limite v1. È il pain più cliccato dei concorrenti (Meta Business Suite, Hootsuite, Buffer vendono scheduling a €10-50/mese).

### Perché ha senso (pro)
- Differenziazione vs concorrenti social scheduling a €50/mese
- Sfrutta caption default + audit `social_posts` già presenti
- Possibile upsell in pricing

### Contro / complessità
- **Effort ALTO** (10-20h di sviluppo):
  - Cron/scheduler background (APScheduler o simile) — nuovo componente nel backend
  - Campo `scheduled_at` in `social_posts` + status `scheduled`
  - Retry logic (token scaduto al momento programmato)
  - Timezone handling (agenzia italiana, ma anche gestione UTC)
  - UI: calendar picker + gestione coda + cancellazione post schedulati
- **Prematuro prima di ≥5 agenzie attive su Social Publisher** (feedback reale > speculazione)
- Rate limit Meta post-schedule da testare

### Priorità
**P3** · alto effort · attendere validation

### Timing consigliato
Dopo ≥5 agenzie attive su Social Publisher (validation reale della domanda)

### File coinvolti
- `backend/apps/immoweb/social_publisher.py` — nuovo endpoint POST `/schedule`
- Nuovo modulo `backend/apps/immoweb/social_scheduler.py` (cron job)
- Frontend `SocialPublisherPage.jsx` — vista calendario/coda scheduled

### Aggiornamento manuale post-ship
- Cap. 15 §15.11 — rimuovere "NO scheduling" dai limiti
- Cap. 15 §15.7 — aggiungere sezione *"Programmare una pubblicazione"*
- YAML: aggiornare `social.limitazioni-v1` + nuova voce `social.scheduling`

### Domande aperte per il Founder
1. Vale sviluppare senza validation dei primi 5 clienti, o aspettiamo?
2. Se sviluppiamo: massima orizzonte scheduling (24h, 7g, 30g)?
3. Pricing: incluso nel piano base o add-on premium?

### Stato
🟠 **DA APPROFONDIRE** — attendere validation da primi utenti Social

---

## 🟠 A-012 — Social Publisher · metrics/insights post-pubblicazione

**Data inserimento**: Feb-2026
**Segnalato da**: Emergent Spark Cap. 15 (Social Publisher)
**Contesto**: Cap. 15 §15.11 documenta *"NO analytics engagement"*. Oggi sappiamo solo `success/failed` + `external_id`.

### Perché ha senso (pro)
- Trasforma modulo da *utility "push"* a *strumento marketing con feedback loop*
- Meta Graph API + Telegram Bot API espongono insights (limite: solo IG/FB, non Telegram)
- Complementare ad A-011 (scheduling)

### Contro / complessità
- **Effort ALTO** (15-25h):
  - Fetch `GET /{external_id}/insights` per FB/IG (con Page Access Token)
  - Token refresh proattivo (long-lived scadono a 60g, insights arrivano dopo)
  - Storage: nuova collezione `social_post_metrics` con snapshot a T+24h, T+72h, T+7g
  - Rate limit Meta (200 chiamate/ora — attenzione al fanout)
  - Telegram: no insights nativi, solo view count sul messaggio (parziale)
- **Dipendenza da A-011** o demand esplicito (senza scheduling, le metriche di 1-2 post/mese hanno poco valore)

### Priorità
**P3** · alto effort · dipendenze significative

### Timing consigliato
Dopo A-011 (o insieme, se il Founder decide di andare full-marketing su Social)

### File coinvolti
- `backend/apps/immoweb/social_publisher.py` — nuovo endpoint GET `/posts/{id}/metrics`
- Nuovo modulo `backend/apps/immoweb/social_metrics_fetcher.py` (cron)
- Nuova collezione `social_post_metrics`
- Frontend `SocialPublisherPage.jsx` — colonna metrics sulla lista post

### Aggiornamento manuale post-ship
- Cap. 15 §15.11 — rimuovere "NO analytics engagement"
- YAML: aggiornare `social.limitazioni-v1`

### Domande aperte per il Founder
1. Priorità metrics vs scheduling — quale prima?
2. Metrics visibili solo al titolare o anche agli agenti (per KPI personali)?

### Stato
🟠 **DA APPROFONDIRE** — bassa priorità v1, alta priorità v2

---

## 🟢 A-013 — Hard-gate crediti Virtual Staging (pre-check saldo)

**Data inserimento**: Feb-2026
**Segnalato da**: SPRINT_STATUS backlog + Cursor
**Contesto**: Cap. 9 documenta il flusso staging + costo crediti. Oggi il pre-check saldo avviene solo al momento del render (SAM2 + Flux) — se il saldo è insufficiente, l'utente scopre il problema DOPO aver atteso l'AI.

### Perché ha senso (pro)
- **Qualità UX critica**: l'agente scopre il saldo insufficiente **prima** del render costoso
- Evita "debito crediti" (partial charge se render inizia ma fallisce a metà)
- Bassa complessità: il saldo è già disponibile via `/credits/balance`

### Contro / complessità
- Messaggio errore chiaro da localizzare (it/en/es)
- Timing: pre-check al click di *"Genera"* o inline nella pagina staging?

### Priorità
**P1** · già in SPRINT_STATUS backlog · quality UX + revenue protection

### Timing consigliato
Post-manuale (parte del batch task tecnici backlog)

### File coinvolti
- `backend/apps/immoweb/virtual_staging.py` — pre-check saldo prima di innescare Flux
- `frontend/src/apps/immoweb/pages/VirtualStagingPage.jsx` — check preventivo al click

### Aggiornamento manuale post-ship
- Cap. 9 §crediti — flusso errore migliorato
- YAML: aggiornare `staging.crediti-costo` (o creare `staging.pre-check-saldo`)

### Domande aperte per il Founder
Nessuna — implementazione autonoma se dà "vai".

### Stato
🟢 **DA APPROFONDIRE** — pronto per implementazione post-manuale

---

## 🟢 A-014 — Billing UI listino Founder + B2C Stripe checkout live

**Data inserimento**: Feb-2026
**Segnalato da**: SPRINT_STATUS backlog
**Contesto**: PRICING_B2B (€49/€99/€249 Founder) e PRICING_B2C sono approvati. Backend stub `b2c_products.py` esiste. Ma UI + checkout live NON sono attivi.

### Perché ha senso (pro)
- **REVENUE-CRITICAL** — è il modulo che monetizza OMNIA
- Founder 50 waitlist attende attivazione checkout
- Backend stub già presente, serve completare + UI

### Contro / complessità
- `STRIPE_ENABLED` env variable (test/live switch)
- Webhook Stripe (signature verify, retry logic)
- Test sandbox obbligatorio prima di live
- Manuale: **NON documentare finché non live** (D-051 · onestà)

### Priorità
**P1** · revenue-critical · founder ha listino approvato

### Timing consigliato
Prossimo sprint tecnico (post-manuale)

### File coinvolti
- `backend/apps/immoweb/billing/routes.py` — completare endpoint
- `backend/apps/immoweb/billing/b2c_products.py` — attivare stub
- `frontend/src/apps/immoweb/BillingPage.jsx` — UI listino Founder + checkout
- Frontend B2C landing — CTA checkout

### Aggiornamento manuale post-ship
- Cap. futuro Billing (Cap. 24?) — **da scrivere SOLO post-ship** (D-051)
- Cap. 1 §pricing — aggiornare quando checkout live

### Domande aperte per il Founder
1. Test sandbox prima → conferma flusso → poi live?
2. Rollout graduale (prima Founder 50, poi Agency generale)?

### Stato
🟢 **DA APPROFONDIRE** — pronto, revenue-blocker

---

## 🟡 A-015 — Sito Web v2 · scope P0 (Hero + Chi Siamo + Contatti + Footer + extractor esteso)

**Data inserimento**: Feb-2026
**Segnalato da**: SPRINT + conversazione Founder (task aperto)
**Contesto**: Cap. 8 documenta il sito agenzia v1 (basic template). Il Founder ha discusso in passato un upgrade major con Hero + Chi Siamo + Contatti + Footer + estensione brand extractor.

### Perché ha senso (pro)
- Sito agenzia = vetrina commerciale primaria per lead gen
- Cap. 8 documenta v1 con menzione template *"in arrivo"* (D-051)
- Brand extractor esistente parziale — estenderlo è naturale

### Contro / complessità
- **Scope ampio** — serve separare P0 (essenziale) da P1 (nice-to-have)
- Modifiche non triviali a `themes.py` + `site.py` + landing components
- Testing SEO + performance su domini custom (Cap. 8 Domain Vault)

### Priorità
**P2** · task aperto Founder · alto valore commerciale ma effort significativo

### Timing consigliato
Post-manuale, dopo review scope con Founder (Cap. 16 potrebbe essere HAL Legal o Domain Vault prima di v2 sito)

### File coinvolti
- `backend/apps/immoweb/site.py` — endpoint modelli sezioni
- `backend/apps/immoweb/themes.py` — nuove varianti tema
- `backend/apps/immoweb/brand_extractor.py` — estensioni ai selettori
- Frontend `landing/` — nuovi componenti Hero, ChiSiamo, Contatti, Footer

### Aggiornamento manuale post-ship
- Cap. 8 aggiornamento **major v2.0** SOLO post-ship (D-051)
- YAML: aggiornare tutte le voci `sito.*` o creare `sito-v2.*`

### Domande aperte per il Founder
1. Scope P0 confermato? (Hero + Chi Siamo + Contatti + Footer + extractor esteso)
2. Timing rispetto a Cap. 16-26 manuale — prima o dopo?
3. Design-driven (mockup Founder) o code-first (poi UI polish)?

### Stato
🟡 **DA APPROFONDIRE** — scope confermato ma timing da decidere

---

## 🟡 A-016 — Micro-fix retrieval HAL · boost tag mutui "banche"

**Data inserimento**: Feb-2026
**Segnalato da**: Cursor (gap iter.35 post H-bis)
**Contesto**: Durante il testing_agent H-bis (Cap. 11), query *"quante banche ci sono?"* ha restituito sim `0.142` — sotto la soglia HIGH (0.20) e sotto il min ideale (0.15) documentato in `IMPORT_HAL.md` Smoke expectations.

### Perché ha senso (pro)
- Top-1 `mutui.offerte-14-banche-8` diventerebbe più stabile
- Riduce rischio *insufficient_context* su domanda molto frequente
- Semplice ottimizzazione tag YAML — nessun cambio codice

### Contro / complessità
- Retrieval già **PASS** iter.35 (con confidence media) — non è blocker
- Boost YAML opzionale (D-061 dice "premiare i tag" — ma sono già tunati)

### Priorità
**P3** · nice-to-have · non blocker

### Timing consigliato
Solo se emergono altri gap retrieval simili (raggruppare i micro-fix in un batch)

### File coinvolti
- `memory/manuale/hal/11-mutui-comparatore.yaml` — potenziare tags della voce `mutui.offerte-14-banche-8` con parole tipo *"quante banche"*, *"totale banche"*
- (Solo se non basta) `backend/apps/immoweb/hal_knowledge.py` — non toccare senza motivo

### Aggiornamento manuale post-ship
Nessuno — è un micro-fix retrieval, non un cambio funzionalità.

### Domande aperte per il Founder
Nessuna — decisione tecnica autonoma se conveniente.

### Stato
🟡 **DA APPROFONDIRE** — nice-to-have, priorità sotto A-006/A-007

---

## 🟡 A-017 — Notification center in-app (Bell icon + inbox + unread badge)

**Data inserimento**: Feb 2026 (Spark Cap. 18 Notifiche e attività)
**Segnalato da**: Cursor (redazione Cap. 18 D-051)
**Contesto**: Cap. 18 documenta onestamente che OMNIA v1 NON ha una pagina Notifiche. Backlog per v1.1.

**Idea**: aggiungere una Bell icon nella navbar ImmoWeb + ImmobilCloud, con dropdown "Ultime N notifiche" cliccabili, contatore unread, mark-as-read persistente. Backend: nuovo router `/notifications` + collezione Mongo `notifications` (record per evento con status read/unread).

**Sorgenti candidate per unificare in inbox**:
- Match nuovi (Cap. 5) → notifica al titolare
- Lead nuovi (Cap. 6 portale pubblico) → notifica all'agente owner
- Invito accettato/rifiutato (Cap. 13) → notifica al titolare
- Import XML completato (Cap. 14) → notifica al titolare
- Social post pubblicato/fallito (Cap. 15) → notifica all'agente
- Compliance HARD violation (Cap. 16) → notifica al titolare
- DNS verify domain (Cap. 17) → notifica al titolare

**Effort stimato**: L (15-25h) · nuovo router + collezione + UI navbar Bell + polling/SSE per real-time.

### Stato
🟡 **P1** — alto valore percepito, elemento cardine di completezza CRM

---

## 🟡 A-018 — Activity feed dashboard (timeline aggregato audit collections)

**Data inserimento**: Feb 2026 (Spark Cap. 18)
**Segnalato da**: Cursor (redazione Cap. 18 § 18.13)
**Contesto**: la Dashboard ImmoWeb v1 mostra 6 KPI counter ma NON un activity feed. Cap. 18 documenta esplicitamente questa mancanza.

**Idea**: aggiungere sotto la Dashboard KPI una sezione "Ultime attività della tua agenzia" che aggrega:
- `al_audit` (chat HAL)
- `match_audit` (nuovi match)
- `publishing_events` (sync portali)
- `social_posts` (post social)
- `calendar_events` (visite)
- `domain_vault_events` (DNS)
- `privacy_audit_events` (cambio privacy immobile)
- `hal_knowledge_sessions` (domande HAL)

**Rendering**: timeline con timestamp, attore (nome utente), azione (i18n label), link al dettaglio se disponibile. Filtri per tipo/utente/data.

**Effort stimato**: M-L (8-15h) · backend aggregation + UI timeline + i18n label per evento.

### Stato
🟡 **P2** — utile ma dipende da A-017 (notification center) per architettura eventi condivisa

---

## 🟡 A-019 — Frequency-aware saved-search cron (rispetta instant/daily/weekly)

**Data inserimento**: Feb 2026 (bug D-051 documentato Cap. 18 § 18.8)
**Segnalato da**: Cursor (bug funzionale trovato in `saved_searches.py:271`)
**Contesto**: la collezione `saved_searches` salva `frequency: instant|daily|weekly` MA il cron `run_all_active_saved_searches()` IGNORA il valore e processa TUTTE le active ricerche ad ogni chiamata. Documentato onestamente in Cap. 18.

**Idea**: filtrare il cron per rispettare la frequenza:
- `instant`: processa sempre
- `daily`: processa solo se `last_run_at < now - 24h`
- `weekly`: processa solo se `last_run_at < now - 7d`

**Effort stimato**: XS (~30min) · aggiungere clausola time-based nel filtro Mongo. Test regression con fixtures date-mocked.

### Stato
🟢 **P2** — bug funzionale ma workaround (super_admin lancia manualmente) è accettabile v1

---

## 🟡 A-020 — Internal APScheduler per saved-search cron (no dipendenza esterna)

**Data inserimento**: Feb 2026 (Spark Cap. 18 § 18.9)
**Segnalato da**: Cursor (redazione Cap. 18)
**Contesto**: `apps/immoweb/cron.py` espone `POST /api/app/cron/saved-searches/run-all` (super_admin only) ma nessuno scheduler interno lo chiama. C'è già un APScheduler attivo per publishing sync (06:00 UTC) — si può estendere.

**Idea**: aggiungere un job APScheduler dedicato a saved-search che parte 3× al giorno (es. 08:00, 14:00, 20:00 UTC) e chiama `run_all_active_saved_searches()`. Prerequisito: implementare A-019 (frequency-aware) per non spammare i daily/weekly.

**Effort stimato**: S (~2h) · nuovo job + logging + toggle env `SAVED_SEARCH_SCHEDULER_ENABLED`.

### Stato
🟡 **P2** — dipende da A-019, priorità post-primi clienti B2C ImmobilCloud

---

## 🟡 A-021 — UI notification preferences (toggle canale + tipo email)

**Data inserimento**: Feb 2026 (Spark Cap. 18 § 18.10)
**Segnalato da**: Cursor (redazione Cap. 18)
**Contesto**: `User.notification_channels` esiste in schema (default `["email"]`) ma non c'è UI per modificarlo post-registrazione né granularità per tipo email.

**Idea**: aggiungere in ImmoWeb `SettingsPage.jsx` e ImmobilCloud `AccountDashboard.jsx` un pannello "Notifiche" con:
- Toggle canale (email/push — push disabilitato v1 con tooltip "In arrivo v1.1")
- Toggle per tipo (welcome/agency_invite/lead_notification/saved_search_alert) — con nota "Le email di password_reset sono sempre inviate per sicurezza account"
- Frequency picker per digest (saved-search: instant/daily/weekly — visibile solo B2C)

**Effort stimato**: M (~4h) · backend PATCH `/api/me/notification-preferences` + UI form + tests.

### Stato
🟡 **P1** — GDPR-friendly (utente controlla i propri canali) + requisito per Notification Directive UE

---

## 🟡 A-022 — Retention policy audit collections (archivio dopo 90 giorni)

**Data inserimento**: Feb 2026 (Spark Cap. 18 § 18.12)
**Segnalato da**: Cursor (redazione Cap. 18)
**Contesto**: le 10 audit collections (`al_audit`, `match_audit`, `publishing_events`, ecc.) crescono indefinitamente in Mongo. Nessuna policy retention v1 → rischio di crescita disco su lungo periodo.

**Idea**: definire retention per collezione:
- `al_audit`, `al_legal_audit`, `hal_knowledge_sessions`: 90gg (poi archivio S3 o eliminazione)
- `match_audit`, `publishing_events`, `social_posts`, `domain_vault_events`: 365gg (auditability GDPR)
- `privacy_audit_events`, `legal_kit_events`: 5 anni (compliance normativa)
- `calendar_events`: no retention (sono operativi, non log)

Implementazione: TTL index Mongo dove semantica lo consente + job archivio S3 mensile.

**Effort stimato**: M (~4h) · index TTL + job archive + policy documentata in DECISIONS.md.

### Stato
🟢 **P3** — post-primi clienti (rischio disco basso v1)

---

## 🟢 A-023 — Toast duration tuning (config per toast singolo)

**Data inserimento**: Feb 2026 (Spark Cap. 18 § 18.11)
**Segnalato da**: Cursor (redazione Cap. 18)
**Contesto**: i toast sonner hanno durata default ~4-5s. Alcuni feedback critici (es. "Pagamento fallito, contatta il supporto") potrebbero necessitare durata più lunga o dismissal manuale.

**Idea**: nel wrapper `components/ui/sonner.jsx` esporre un preset:
- `toast.success(msg)` → 4s (default)
- `toast.error(msg)` → 6s
- `toast.critical(msg, { duration: Infinity })` → richiede dismissal manuale (es. errori pagamento)

**Effort stimato**: XS (~15min) · configurazione wrapper + eventualmente 1-2 refactor di call site.

### Stato
🟢 **P3** — nice-to-have, priorità bassa

---

# 📊 Tabella riepilogo Backlog qualità (A-006 → A-023)

| ID | Titolo | P | Effort | Origine | Timing |
|----|--------|:-:|:-:|---------|:-:|
| A-006 | Tooltip badge confidence HAL | **P1** | XS (~15min) | Spark Cap.12 | Post-manuale |
| A-007 | Rimozione membro agenzia | **P1** | M (2-3h) | Spark Cap.13 | Post-manuale |
| A-008 | Cambio ruolo membro post-join | P2 | M-L | Cursor gap Cap.13 | Post-A-007 |
| A-009 | Bulk-assign agente post-import | P2 | M-L | Spark Cap.14 | Post-A-007 |
| A-010 | Storico import XML UI | P2 | M | Cursor gap Cap.14 | Post-primi clienti |
| A-011 | Social scheduling minimal | P3 | L (10-20h) | Spark Cap.15 | Post ≥5 utenti Social |
| A-012 | Social metrics/insights | P3 | L (15-25h) | Spark Cap.15 | Post-A-011 |
| A-013 | Hard-gate crediti Staging | **P1** | S | SPRINT + Cursor | Post-manuale |
| A-014 | Billing UI + B2C Stripe live | **P1** | L | SPRINT (revenue) | Prossimo sprint |
| A-015 | Sito Web v2 (Hero, Chi Siamo, ...) | P2 | XL | SPRINT + Founder | Da decidere con Founder |
| A-016 | Boost tag mutui "banche" | P3 | XS | Cursor gap iter.35 | Raggruppare micro-fix |
| A-017 | Notification center in-app | **P1** | L (15-25h) | Spark Cap.18 | Post v1.0 lancio |
| A-018 | Activity feed dashboard | P2 | M-L (8-15h) | Spark Cap.18 | Post-A-017 |
| A-019 | Frequency-aware saved-search cron | P2 | XS (~30min) | Bug D-051 Cap.18 | Raggruppare micro-fix |
| A-020 | Internal APScheduler saved-search | P2 | S (~2h) | Spark Cap.18 | Post-A-019 |
| A-021 | UI notification preferences | **P1** | M (~4h) | Spark Cap.18 | Prossimo sprint |
| A-022 | Retention policy audit collections | P3 | M (~4h) | Spark Cap.18 | Post-primi clienti |
| A-023 | Toast duration tuning | P3 | XS (~15min) | Spark Cap.18 | Raggruppare micro-fix |

**Legenda priorità**: **P1** alta (ROI alto/effort basso o revenue-critical) · P2 media · P3 futuro (validation-gated)
**Legenda effort**: XS <30min · S 30min-2h · M 2-6h · L 6-20h · XL >20h

---

## Voci già chiuse (non attive)

- ✅ **`chunk_id` in `/ask` sources[]** — fix applicato Feb 2026 (`hal_knowledge.py:~580`) + test regression aggiornati. Su GitHub `main`. Non serve tracking A-xxx.

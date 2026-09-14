# 🔍 COMPETITIVE ANALYSIS — TRACK B (White Label / Headless / API)

**Data**: 06 Luglio 2026
**Scopo**: base fattuale per `GO_TO_MARKET.md` + `PRICING_OMNIA.md` v2 (M2.5.0 — P0)
**Complementare a**: `COMPETITIVE_ANALYSIS_IDEALISTA.md` (portali B2C) + `COMPETITIVE_ANALYSIS_AGESTANET.md` (gestionali Track A)
**Metodo**: web research 06-Lug-2026 su 7 fronti (12 ricerche), fonti citate in coda a ogni sezione

---

## ⚡ EXECUTIVE SUMMARY — le 7 scoperte chiave

1. **🥇 WHITE SPACE CONFERMATO**: in Italia NON esiste una piattaforma headless immobiliare integrata (valutatore + staging + legal AI + mutui + feed + MLS via API/widget con un solo contratto e un solo wallet crediti). Il mercato si arrangia componendo 4-5 fornitori diversi (CASAFARI per dati, DomusReport per valutazioni, staging SaaS USA, nessuno per il legale). **OMNIA Track B non ha un competitor diretto: ha 5 competitor parziali.**
2. **I franchising NON cambieranno CRM**: Tecnocasa è su Salesforce (TecnoCloud, 10.000+ utenti, 2.600 agenzie), RE/MAX Italia è migrata a HubSpot, Gabetti ha My Agency + Toolbox 4.0 (gestionale onOffice). Investimenti multi-milionari pluriennali. **Vendere "sostituzione CRM" a un franchising = porta in faccia. Vendere widget/API/feed che si innestano sul loro stack = porta aperta.** Questo valida al 100% la scelta Track B.
3. **Il valutatore white-label è un mercato già prezzato**: DomusReport €50-100/mese (50-150 valutazioni), RealAdvisor €50-500/mese, Sprengnetter Lead €539/anno (1.200 chiamate + €0,80/extra), PriceHubble solo enterprise su preventivo (min 12 mesi). **Corridoio di mercato chiaro: €40-150/mese per singola agenzia.** Il nostro Valuator (UNI 10750 + coefficienti merito + copertura 100% IT) è tecnicamente superiore a DomusReport (solo OMI).
4. **Virtual staging: il nostro margine è mostruoso**: retail di mercato $0,53-2,67/foto (Virtual Staging AI), $0,20-0,29 i più aggressivi (Stagently). Il nostro costo pipeline 3-stage è €0,056/render. **Anche vendendo a €0,90/img (D-032) siamo sotto il retail USA di qualità con margine ~94%.**
5. **HAL Legal non ha NESSUN equivalente**: i chatbot white-label generici costano $99-1.299/mese (piattaforma) e le agenzie li rivendono a $300-1.500/mese. Nessuno offre un chatbot giuridico-notarile immobiliare italiano con citazioni normative e anti-hallucination. **È il nostro prodotto hero Track B a pricing power massimo.**
6. **MLS italiano = mercato piccolo e caro**: Frimm/MLS Agent RE (ex Replat) costa €1.000-1.500/anno, ~3.500 agenti connessi, ~20.000 immobili. **MLS incluso nel piano Agency OMNIA = disruption immediata su un incumbent debole.**
7. **Mutui white-label: buco normativo-tecnologico**: MutuiOnline/Facile.it/Segugio non offrono widget white-label pubblici. La L.118/2022 ha reso compatibili mediazione creditizia e agenzia immobiliare. Credipass offre "corner creditizi" gratuiti alle agenzie. **Il nostro comparatore in-house embeddabile è unico; la monetizzazione vera arriverà da un accordo di mediazione (post-volumi, come da D-037).**

---

## 1️⃣ FRONTE 1 — Valutazione immobiliare white-label / API

### 1.1 Mappa dei player

| Player | Paese | Modello | Prezzo | White label | API | Note |
|---|---|---|---|---|---|---|
| **PriceHubble** | CH/EU (leader) | Enterprise bespoke | Non pubblico, contratti min 12 mesi, non cancellabili | Sì (widget + API) | Sì | AI Agents Suite lanciata 2026. Target banche/istituzionali, NON singole agenzie. Nessun listino → friction commerciale alta |
| **RealAdvisor** | CH/IT/EU | SaaS agenzie | **€50-150/mese** (piccole), **€150-500/mese** (medie, multi-utente) | Sì (valutatore integrato nel sito agenzia) | Parziale | Include vetrina/visibilità + "Opinione di Valore" per convertire in mandati esclusivi. Ben indicizzato SEO in IT |
| **DomusReport** 🇮🇹 | Italia | SaaS freemium | **Free €0 (5 val/mese) · Basic €50 (50 val) · Premium €100/mese (150 val, API access)** | Sì (Premium: zero riferimenti al fornitore, CSS custom, PDF brandizzato) | Sì (Premium) | **Competitor italiano più diretto del nostro Valuator widget**. Dati OMI + AI, lead qualification, CRM integrato. Trial 7gg |
| **ImmobiliareAI** (agenteimmobiliareai.com) 🇮🇹 | Italia | Setup una tantum | **€1.500-3.000 setup** + costo/lead marginale €2-8 | Sì (full: logo, colori, dominio es. `valuta.tuaagenzia.it`) | n.d. | OMI + AI 50+ parametri, stima in 60s. Pacchetto enterprise per network 3+ sedi. Claim: +40% conversioni, ROI 600-1200% |
| **Sprengnetter** | DE/AT | Coins + flat | **Lead widget: €538,80/anno (1.200 chiamate) + €0,80/extra** · Value: 150 coins/valutazione (750 coins = €239 → ~€47,80/valutazione pro) · singola €49 | Sì (corporate design del makler, max 2 domini) | Sì | Leader DE. Database 2M+ prezzi di compravendita REALI (non asking). ImmoWertV-konform. Benchmark d'oro per il modello a crediti |
| **Chimnie** | UK | Pay-per-call | **£0,05-0,15/lookup** | — | Sì | Benchmark low-cost per il puro dato |
| **CASAFARI** | PT/EU | Enterprise | Non pubblico | — | Sì (Property Data API, 20+ paesi) | Dati deduplicati/comparables, non valutatore widget per agenzie |

### 1.2 Cosa impariamo

- **Il prezzo di riferimento del widget valutatore per agenzia singola è €40-100/mese** con 50-150 valutazioni incluse. Sopra €150/mese si entra nel territorio "medie agenzie multi-utente" (RealAdvisor fino a €500).
- **Il modello vincente è flat + incluse + overage** (Sprengnetter: flat annuale + €0,80/chiamata extra). Nessuno usa il puro pay-per-call verso le agenzie (troppa ansia da contatore); il pay-per-call vive solo nel B2B dati (Chimnie).
- **La lead capture è il vero prodotto**: tutti posizionano il widget come lead generator ("chi chiede la stima sta per vendere"), non come tool di stima. Il valore percepito = costo/lead evitato (€25-80 sui portali vs €2-8 self-generated).
- **Punti deboli sfruttabili**: DomusReport è solo-OMI (no UNI 10750, no coefficienti merito, no comparables live dal DB); PriceHubble è inaccessibile alle agenzie (no listino, 12 mesi lock-in); ImmobiliareAI chiede €1.500-3.000 upfront (barriera).

### 1.3 Vantaggi tecnici OMNIA da mettere in vetrina
- Pipeline 5-stage con **UNI 10750/DPR 138** (superficie commerciale ponderata) + coefficienti merito + liquidità regionale → output "stile perizia" che nessun widget IT fornisce
- Copertura **100% del territorio nazionale** (~7.900 comuni: 124 città curate + 107 province + fallback regionale via Nominatim) — nessun competitor IT la offre con questo livello di dettaglio
- Audit trail dei moltiplicatori (trasparenza vs "scatola nera" AI dei competitor)
- Lead già qualificato dentro un CRM (per Track A) o forwardato via webhook (Track B)

**Fonti**: pricehubble.com/docs, chimnie.com/compare, ruesch.tech (PriceHubble widget review), realadvisor.it/it/pro/blog, domusreport.com, agenteimmobiliareai.com, shop.sprengnetter.de, it.casafari.com

---

## 2️⃣ FRONTE 2 — Virtual Staging SaaS

### 2.1 Benchmark prezzi retail (mercato USA/global, 2026)

| Provider | Piano min | Prezzo/foto | Note |
|---|---|---|---|
| **Virtual Staging AI** (leader) | $16/mese (6 foto) | **$0,53-2,67** | Enterprise $79/mese = 150 foto + API access. Revisioni illimitate, 10s/render |
| **REimagine Home** | $19/mese (30 foto) | $0,63 | |
| **Apply Design** | $10,50/mese | $0,53-1,50 | Sistema "coins" confuso (leva di differenziazione per noi: pricing chiaro) |
| **Stagently** | $29/mese (100 foto) | **$0,20-0,29** | Business: $0,20/foto per 1.000 img — il più aggressivo |
| **Collov** | n.d. | $0,23 | AI-first low cost |
| Staging "umano" tradizionale | — | $15-29/foto | Il vecchio mercato che l'AI sta erodendo |

### 2.2 Cosa impariamo
- **Corridoio retail AI: $0,20-0,95/foto** a volume; $2-3/foto solo per chi fa 5-10 foto/mese.
- Il nostro costo pipeline premium 3-stage (SAM2 + Flux Inpainting + ESRGAN) = **€0,056/render**: possiamo stare a **€0,90/img retail (D-032 confermata)** o scendere a €0,40-0,60 in bundle API senza intaccare il margine (>85%).
- **Nessun player IT/EU offre virtual staging embeddato nel flusso del gestionale/CRM o come widget white-label per il sito dell'agenzia**: vendono tutti SaaS standalone con upload manuale. Il nostro "Arreda questa foto" inline (D-033 S4.2) + widget demo Track B = differenziazione reale.
- L'API access è sempre relegata al tier Enterprise ($79+): noi possiamo darla dal primo tier Track B (è il nostro core business, non un add-on).
- Watermark AGCM: i player USA non lo gestiscono (non hanno vincolo normativo IT) → la nostra "trasparenza normativa" (D-033) è un argomento di compliance verso i franchising, sensibilissimi al rischio reputazionale.

**Fonti**: virtualstagingai.app/prices, housingwire.com, stagently.com/pricing, aihomedesign.com

---

## 3️⃣ FRONTE 3 — Lo stack tecnologico dei franchising italiani (target Track B)

### 3.1 Chi usa cosa (verificato)

| Rete | CRM / Piattaforma | Base tecnologica | Implicazione per OMNIA |
|---|---|---|---|
| **Tecnocasa** (~2.600 agenzie, 10.000+ utenti) | **TecnoCloud** | **Salesforce** (progetto con TelNext + Capgemini) | Investimento enorme, mai sostituibile. Entrata: widget sui siti delle singole agenzie + feed. Decisione centralizzata → ciclo vendita lungo, deal potenzialmente enorme |
| **RE/MAX Italia** (400+ agenzie) | **HubSpot** (migrata DA Salesforce) + MAXimizer (gestionale immobiliare) | HubSpot + SAP + BI | Ha appena cambiato CRM → zero appetito per altro cambio. HubSpot ha marketplace integrazioni: un **connettore OMNIA→HubSpot** (lead forwarding) è la chiave d'ingresso |
| **Gabetti** | **My Agency** + **Toolbox 4.0** (suite AI: descrizioni annunci, Hubique) | onOffice (gestionale) + partner Treere | Già compra AI da terzi (Treere) → è culturalmente pronto a comprare feature AI esterne. Target ideale per HAL Legal + Valuator via API |
| **Toscano, Frimm, Grimaldi** | Gestionali propri o Getrix/Agestanet | misto | Reti medie: più agili, decisione meno centralizzata. Beachhead realistico per i primi pilot M2.5 |

### 3.2 Cosa impariamo (CRITICO per il GTM)
1. **Il pitch Track B NON è "sostituisci il gestionale"** — è: *"tieni Salesforce/HubSpot/onOffice; noi ti diamo le feature AI che il tuo stack non avrà mai (legal chatbot, staging, valutatore perizia-style) come widget sul sito e API nel tuo CRM"*.
2. **Due livelli di vendita**: (a) sede centrale (deal API/feed di rete, ciclo 6-18 mesi), (b) singola agenzia affiliata (widget sul proprio sito, ciclo 1-4 settimane, carta di credito). **Il GTM deve partire dal livello (b)**: le affiliate hanno autonomia sul proprio sito web e budget marketing proprio → i widget si vendono alla singola affiliata SENZA aspettare la casa madre. La trazione bottom-up diventa poi leva per il deal centrale.
3. **Gabetti dimostra che i franchising comprano AI da terzi** (Toolbox 4.0 con Treere): esiste già il precedente contrattuale/culturale.
4. Il **multi-branch (M2.5.1)** serve esattamente a questo: quando la casa madre firma, servono `agency_group` + rollup + crediti group-vs-branch dal giorno 1.

**Fonti**: salesforce.com/it/customer-stories/tecnocasa, franchising.remax.it/blog (HubSpot), gabetti.it (Toolbox 4.0), dailyonline.it, smau.it

---

## 4️⃣ FRONTE 4 — Modelli di pricing API/crediti nel PropTech

### 4.1 Pattern osservati

| Modello | Chi lo usa | Pro | Contro |
|---|---|---|---|
| **Flat + incluse + overage** | Sprengnetter Lead (€539/anno, 1.200 incl., €0,80/extra) | Prevedibilità per il cliente, ricavo ricorrente per noi | Cap da calibrare bene |
| **Coins/crediti prepagati a pacchetti** | Sprengnetter Value (750 coins €239), Apply Design | Pay-as-you-go puro, ottimo per uso sporadico | Apply Design dimostra che se opaco irrita i clienti |
| **Tier a scaglioni di volume** | DomusReport (5/50/150 val/mese), Virtual Staging AI | Semplice da comunicare | Salti di prezzo bruschi |
| **Pay-per-call puro** | Chimnie (£0,05), API dati | Zero barriera d'ingresso | Ricavo imprevedibile, race to the bottom |
| **Enterprise bespoke** | PriceHubble, Getrix, CASAFARI | Massimizza deal grandi | Uccide il self-service; friction (nessun listino = sfiducia, come da nostra D-024 anti-opacità) |

### 4.2 Raccomandazione per PRICING_OMNIA.md v2 (logica crediti Track B)
- **Modello ibrido a 2 livelli** (coerente con D-024 "listino pubblico" e D-032):
  1. **Abbonamento widget flat** per singola agenzia/filiale: quota mensile con N azioni incluse per widget (valutazioni, query legal, render) + **overage a crediti** con prezzo per credito PUBBLICO.
  2. **Wallet crediti API** per integrazioni server-to-server: pacchetti prepagati (es. 100/500/2.500 crediti) con sconto volume, contabilità group-vs-branch (M2.5.1), auto-ricarica opzionale.
- **1 credito = 1 unità di valore chiara** (no coins opachi alla Apply Design): pubblichiamo la tabella conversione (es. 1 valutazione = 1 credito, 1 render staging = 2 crediti, 1 query HAL Legal = 1 credito, 1 video tour = 8 crediti).
- **Free tier Track B**: dev sandbox con quota mensile bassa (es. 25 chiamate/mese, watermark "Powered by OMNIA") → serve ad agganciare gli sviluppatori/web agency dei siti agenzia, che sono il canale reale d'installazione dei widget.
- **Ancoraggi di prezzo derivati dal mercato** (da rifinire in PRICING v2):
  - Valutazione via API/widget: **€0,50-0,80/extra** (= Sprengnetter €0,80; DomusReport implicito €0,66-1,00)
  - Render staging: **€0,90/img** (D-032 confermata; corridoio retail $0,53-0,95)
  - Query HAL Legal: **€0,60/query** (D-032 confermata; nessun benchmark diretto → pricing power)
  - Widget valutatore flat: **€39-79/mese** per affiliata singola (sotto DomusReport Basic/Premium a parità di volumi, con motore superiore)

**Fonti**: shop.sprengnetter.de, domusreport.com, chimnie.com, zuplo.com/learning-center (API pricing models)

---

## 5️⃣ FRONTE 5 — MLS italiani (rilevante per M4, influenza il GTM franchising)

| Aspetto | Frimm / MLS Agent RE (ex REplat) — l'unico incumbent |
|---|---|
| Struttura | MLS Italia Srl (spin-off Frimm SpA, riorganizzata 2025) |
| Scala | ~3.000 utenti registrati, ~3.500 agenti, ~20.000 immobili condivisi |
| Prezzo | **€1.000 + IVA primo anno → €1.500 al 4° anno** (convenzione FIMAA Bergamo); sconti via FIMAA/FIAIP; no fee ingresso, no penale uscita, preavviso 60gg |
| Prodotto | MLS Agent RE entry-level acquistabile online con carta; matching automatico; regole deontologiche su spartizione provvigioni |
| Debolezze | Percepito legato a Frimm (conflitto: è anche una rete franchising concorrente); tecnologia datata; nessuna AI; prezzo alto per il valore |

### Cosa impariamo
- Il mercato accetta di pagare **€83-125/mese solo per l'MLS**. OMNIA che include MLS nel piano Agency (€79/mese lancio, D-024) con AI e CRM inclusi = **value gap enorme e comunicabile in una riga**.
- La neutralità è il punto debole di Frimm (MLS gestito da un franchising concorrente): **OMNIA come "Svizzera dell'MLS"** è un posizionamento da usare in M4.
- Le convenzioni FIMAA/FIAIP sono il canale distributivo dell'MLS in Italia → da agganciare anche per Academy (M6, D-FUTURE-03).

**Fonti**: replat.com, news.frimm.com, immobilio.it (thread prezzi), ilsole24ore.com

---

## 6️⃣ FRONTE 6 — Chatbot AI white-label (benchmark HAL Legal/Knowledge)

| Segmento | Prezzo mercato | Note |
|---|---|---|
| Piattaforme white-label generiche (SiteSpeakAI, Stammer, Trillet) | **$99-1.299/mese** (fee piattaforma per web agency) | Le agency li rivendono a **$300-1.500/mese/cliente** + setup $1.000-5.000 |
| Usage-based | $0,50-6,00 per chat risolta | |
| Enterprise (Qualified) | da $42.000/anno | Fuori scala per agenzie |
| **Chatbot giuridico-notarile immobiliare IT con citazioni normative** | **NON ESISTE** | HAL Legal è unico: web-search su fonti ufficiali + anti-hallucination + analisi PDF |

### Cosa impariamo
- Il mercato paga cifre alte per chatbot **generici** senza dominio verticale. HAL Legal (verticale, citazioni normative, validator, disclaimer L.247/2012) ha **zero comparabili** → possiamo prezzarlo a valore, non a costo: widget HAL Legal pubblico a **€49-99/mese** per sito agenzia è sotto qualsiasi rivendita white-label USA e sopra i nostri costi di ~2 ordini di grandezza.
- Il costo AGCM/compliance di sbagliare un chatbot legale è la barriera d'ingresso che protegge questo moat (anti-hallucination + audit log 5 anni = argomento di vendita ai franchising risk-averse).

**Fonti**: trillet.ai/blogs, sitespeak.ai/blog, quickchat.ai, stammer.ai

---

## 7️⃣ FRONTE 7 — Mutui white-label (benchmark M5.S5 come prodotto Track B)

- **MutuiOnline** (leader, 32 banche), **Mutui.it/Facile**, **Segugio**: nessun programma white-label/widget/API pubblico. Modello: remunerazione dalle banche per pratica avviata (~€750/pratica, cfr. D-032).
- **Normativa (L.118/2022)**: mediazione creditizia e agenzia immobiliare ora compatibili — le società di mediazione possono fare mediazione immobiliare e viceversa (con società dedicata + iscrizione OAM + procedure di controllo OAM).
- **Credipass**: offre alle agenzie immobiliari "corner creditizi" brandizzati **gratis** (guadagna sulle pratiche) → conferma che il canale agenzia è conteso dai mediatori.
- **Auxilia Finance** (FIAIP) ha già partnership con piattaforme AI per agenzie (Metacasa) → è il tipo di partner che potrebbe volere il NOSTRO widget.

### Cosa impariamo
- Il nostro comparatore in-house embeddabile è **unico come tecnologia** (nessuno lo dà in white-label), ma **non monetizzabile direttamente sui grandi volumi** senza accordo di mediazione: la strategia resta quella di D-037 — widget come **lead magnet + aggancio** (rata stimata sugli annunci), e quando avremo volumi, accordo con un mediatore vigilato OAM (Auxilia/Credipass più realistici di MutuiOnline che ha già rifiutato).
- Nel PRICING v2 il widget Mutui va prezzato **basso o incluso in bundle** (è acquisizione, non profit center — il profit center arriverà dalla revenue share con il mediatore: benchmark €750/pratica).

**Fonti**: mutuionline.it, races.it (normativa), organismo-am.it, credipass.it, auxiliafinance.it

---

## 📄 FRONTE 8 — BENCHMARK DOCUMENTALE: il caso reale del Founder (PDF "listini a confronto", Nov 2025)

Dati estratti dai contratti/proposte REALI dell'agenzia del Founder (Nicastro Immobiliare, Catania). È la fotografia esatta di cosa paga oggi un'agenzia media italiana.

### 8.1 Agestanet / BasicSoft (contratto attivo)
| Voce | Listino | Pagato (sconto convenzione Catania) |
|---|---|---|
| AgestaNET gestionale (cod. 9491): CRM + MLS (1.500 agenzie, 280k immobili) + matching + Remail + AgestaMail 50 mail/mese + mobile | €350/anno | €350/anno |
| AgestaWeb sito Ultimate (nicastroimmobiliare.it) €400 + Web MLS €100 | €500/anno | €300/anno (sconto €200) |
| **Totale Agestanet** | **€850/anno** | **~€650/anno + IVA ≈ €793** (coerente con i €786/anno noti da D-016) |

### 8.2 Immobiliare.it (proposta contratto #20251125, 14/11/2025→13/11/2026)
| Aspetto | Dato reale |
|---|---|
| **Listino pieno** | **€2.268/anno** |
| **Pagato (scontato)** | **€708/anno** (12 rate SEPA da €59) → **sconto 69%** |
| Contenuto | Solo **5 annunci vendita + 5 affitto** (+ mirror Trovacasa/MioAffitto) + area Pro + app + report base + ImmoVisita + FotoPlan + Telefono Smart |
| Rinnovo | No tacito rinnovo (art. 3.1) — ma il rinnovo negoziato riparte dal listino €2.268 |
| Clausole | Penale 1/3 dell'importo + intero dovuto in caso di inadempimento (art. 7.4); foro Milano; responsabilità limitata |
| **Costo per annuncio** | €5,90/annuncio/mese scontato → **€18,90/annuncio/mese a listino** |

### 8.3 Pacchetto visibilità Idealista + Casa.it (proposta "Pack Max Basic")
| | Opzione 1 | Opzione 2 "Consigliata" |
|---|---|---|
| Annunci indicizzati (idealista + Casa.it + Silver) | 10 | 15 |
| Premium/Gold | 2 intercambiabili | 3 sempre attivi |
| Evidenza | 1 | 1 |
| **Prezzo primi 12 mesi** | **€179,50/mese** (€2.154/anno) | **€194,50/mese** (€2.334/anno) |
| **Listino al rinnovo (AUTOMATICO)** | **€359/mese** (€4.308/anno) | **€389/mese** (€4.668/anno) |
| Meccanica | ⚠️ "Sconto solo per i primi 12 mesi, poi il servizio si rinnova al valore del pacchetto" + **rinnovo automatico** + SEPA | idem |
| **Salto di prezzo al 13° mese** | **+100%** | **+100%** |

### 8.4 Il conto totale (stack completo di un'agenzia media, 10-15 annunci)
| | Anno 1 (scontato) | Anno 2+ (a regime) |
|---|---|---|
| Agestanet (gestionale+sito+MLS) | €650 | €850 |
| Immobiliare.it (10 annunci) | €708 | €2.268 |
| Idealista+Casa.it pack (15 annunci) | €2.334 | €4.668 |
| **TOTALE** | **€3.692/anno (€308/mese)** | **€7.786/anno (€649/mese)** |
| **OMNIA Pro (Founders 50)** | **€1.188/anno (€99/mese)** | **€1.188/anno** (lock 24m, poi €124 sconto vita) |
| **Risparmio con OMNIA** | **-68%** | **-85% (~€6.600/anno)** |

### 8.5 Lezioni per GTM e Pricing v2
1. **Il "bait & switch" è il modello di mercato**: sconto 50-69% anno 1, raddoppio automatico anno 2 (SEPA attivo → l'agenzia se ne accorge dall'estratto conto). Il nostro contro-posizionamento: *"il prezzo che vedi è il prezzo che pagherai anche tra 3 anni"* — Founders 50 blocca il prezzo IN BASSO, i competitor lo bloccano IN ALTO.
2. **Il costo unitario dell'annuncio sui portali è folle**: €18,90/annuncio/mese (Immobiliare.it a listino), €26-31/annuncio/mese (pack idealista+Casa.it a regime). ImmobilCloud ne include 15-70 nel canone → argomento quantificabile per il B2C listing pricing.
3. **L'agenzia media paga 3 fornitori scollegati** (gestionale + 2 contratti portali) con 3 scadenze, 3 SEPA, zero integrazione. "1 contratto, 1 fattura, 1 login" è un beneficio operativo da mettere nel pitch.
4. **Agestanet è economico ma povero** (€350/anno il gestionale): il vero salasso sono i portali. Quindi il nostro nemico n.1 nel messaging non è il gestionale — è **la spesa portali a rinnovo raddoppiato**. ImmobilCloud (annunci inclusi) + Site-as-Feed è l'arma.
5. Il claim "stack tradizionale €10-12k/anno" va calibrato: per un'agenzia media documentata è **~€7.800/anno a regime** (senza foto pro, senza extra). Restiamo credibili usando il range **€7.500-12.000** con questo PDF come pezza d'appoggio.

**Fonte**: contratti/proposte reali agenzia Founder, PDF "listini a confronto" (artifact 06-Lug-2026).

---

## 🗺️ MAPPA DI POSIZIONAMENTO TRACK B


```
                    VERTICALE IMMOBILIARE
                            ▲
                            │
         DomusReport ●      │      ★ OMNIA Track B
       (solo valutazioni)   │   (suite integrata: valuator+
                            │    staging+legal+mutui+feed+MLS
        RealAdvisor ●       │    con 1 contratto, 1 wallet)
     (valutazioni+lead)     │
                            │        ● PriceHubble
   Sprengnetter ●           │       (enterprise only,
   (valutazioni DE)         │        banche/istituzionali)
                            │
────────────────────────────┼────────────────────────────▶
 SINGOLO TOOL               │                SUITE COMPLETA
                            │
        Stammer/SiteSpeak ● │ ● CASAFARI (dati)
        (chatbot generici)  │
                            │
                    GENERALISTA
```

**La cella "suite verticale integrata self-service per agenzie/franchising IT" è VUOTA.** I competitor sono tutti single-tool (DomusReport, staging SaaS) o enterprise-only (PriceHubble, CASAFARI).

---

## ⚠️ MINACCE E CONTROMOSSE

| Minaccia | Probabilità | Contromossa |
|---|---|---|
| **PriceHubble scende sul mercato agenzie IT** con listino self-service (ha appena lanciato AI Agents Suite) | 🟡 Media (12-24 mesi) | Velocità + prezzo pubblico + verticalità IT (UNI 10750, OMI, normativa) che PH non ha. Lock-in dolce via wallet crediti multi-feature |
| **Immobiliare.it/Getrix aggiunge widget white-label** per le agenzie clienti | 🟡 Media | Getrix non ha AI né incentivo a potenziare i siti proprietari delle agenzie (vive del portale). Il conflitto d'interesse è il nostro argomento |
| **DomusReport si allarga** (staging, chatbot) | 🟢 Bassa-media | È mono-prodotto con team piccolo; noi abbiamo già 4 feature hero live. Correre su M2.5 |
| **Le case madri franchising costruiscono in-house** (Gabetti Toolbox docet) | 🟡 Media | Toolbox dimostra che comprano da terzi (Treere). Offrire co-branding "Powered by" + revenue share al network |
| **Race-to-the-bottom sul staging** (Stagently $0,20) | 🔴 Alta | Non competere sul prezzo puro: qualità 3-stage + compliance AGCM + integrazione CRM/widget. Il staging standalone è commodity, il nostro è embedded |

---

## 🎯 IMPLICAZIONI OPERATIVE PER M2.5.0 (input diretti per i 2 documenti P0)

### Per GO_TO_MARKET.md
1. **Motion bottom-up**: primo target = **singola agenzia affiliata** di rete media (Toscano/Grimaldi/Frimm) + agenzie indipendenti strutturate con sito proprio. La casa madre arriva dopo, tirata dalla trazione delle affiliate.
2. **Canale web agency**: i siti delle agenzie li fanno le web agency locali → free tier developer + snippet 1-line + rev-share da valutare = distribuzione moltiplicativa.
3. **Prodotti hero in ordine di vendibilità Track B**: ① Valuator widget (mercato educato da DomusReport/RealAdvisor, si vende da solo) → ② HAL Legal widget (unico, wow-effect, pricing power) → ③ Staging API (volume) → ④ Feed/ImmoCloud (rete).
4. **Precedente contrattuale**: citare Gabetti+Treere come prova che i franchising comprano AI di terzi.
5. **Neutralità MLS** (vs Frimm) come tema per M4.

### Per PRICING_OMNIA.md v2 (corridoi benchmark-derived)
| Item | Corridoio mercato | Proposta di partenza OMNIA (da rifinire) |
|---|---|---|
| Widget Valuator (flat, per sito/filiale) | €40-150/mese | **€39/mese** (50 val. incl.) · **€79/mese** (150 val. + API) — undercut DomusReport a parità+ di motore |
| Valutazione extra (overage/API) | €0,66-1,00 | **€0,60-0,80/credito** |
| Render staging (API) | $0,20-0,95 | **€0,90 retail · €0,40-0,60 in bundle** (costo €0,056) |
| Query HAL Legal (API/widget) | nessun comparabile | **€0,60/query** o flat widget **€49-99/mese** |
| Widget Mutui | nessun comparabile | **incluso nei bundle** (lead magnet; profit futuro: rev-share mediatore ~€750/pratica) |
| Wallet crediti | coins Sprengnetter €0,32/coin | pacchetti 100/500/2.500 con sconto volume 0/10/20%, prezzo credito PUBBLICO |
| Free tier Track B | DomusReport 5 val/mese | **~25 azioni/mese** con badge "Powered by OMNIA" (il badge È il canale di acquisizione) |
| MLS (per M4) | Frimm €1.000-1.500/anno | **incluso nel piano Agency** — argomento killer |

### Regole d'oro confermate dalla ricerca
- **Listino pubblico sempre** (D-024): PriceHubble/Getrix/CASAFARI opachi = friction; DomusReport/Sprengnetter trasparenti = self-service. Noi stiamo con i secondi.
- **Crediti chiari, mai coins opachi** (lezione Apply Design).
- **Flat+overage batte pay-per-call** per il segmento agenzie.
- **Il badge "Powered by OMNIA" sul free tier** è marketing gratuito distribuito (modello Intercom/Typeform).

---

*Documento creato il 06-Lug-2026 come prerequisito di M2.5.0 (P0). Da aggiornare quando: (a) PriceHubble pubblica listino self-service, (b) risposta partner APE (D-038), (c) primi 3 pilot Track B forniscono willingness-to-pay reale.*

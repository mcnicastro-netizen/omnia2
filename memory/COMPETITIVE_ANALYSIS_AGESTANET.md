# 🎯 OMNIA — Analisi Agestanet (competitor diretto)

**Data**: 18 Giugno 2026
**Fonti**: 3 screenshot reali del Founder (dashboard + portali) + XML feed reale (367KB, 25 immobili) + chat strategica
**Scopo**: capire ESATTAMENTE cosa Agestanet fa, dove vince, dove sbaglia → derivare la strategia OMNIA M2.S5/M2.S6

---

## 1. Cosa fa Agestanet — feature inventory

### Dashboard agenzia
- Sidebar densissima: Gestione Account, Profilo, **Invita un collega** (€5 referral), Annunci e scadenze, Collaborazioni con altre agenzie, Gestione Annunci, Immobili (Nuovo annuncio, Lista immobili), Nuova richiesta, **Richiesta avanzata**, Cancella, **Best Price**, **Bacheca Agenzia**, **Estrazione dati** (Nuova/Effettuata), **Report**, **Pubblicità**, **Portale connettività**, **Stampa e-receipts**, **Utenti**, **Gestione App**, Gestione Agenzia, **MLS Italia**, Impostazioni, Agenti (Attivi/Archivio/Report)
- 4 widget colorati: contratto in scadenza (urgenza), Collaborazioni (1 annuncio, 0 richieste), **AgenteNET MLS** (sub-network), Invita un collega (referral)

### MLS network (asset di lock-in #1)
- **MLS Italia**: **1.803 agenzie · 198.963 immobili · 1.439.292 richieste**
- **MLS Catania** (locale): 75 agenzie · 5.811 immobili · 24.164 richieste
- Read-only condivisione tra agenzie aderenti
- "Il mio MLS" = tracker condivisioni proprie

### Portale connettività (asset di lock-in #2)
- **92 portali immobiliari** gestiti in tabella unica
- Per ogni portale: nome, URL portale, **frequenza** (dropdown: giornaliera/oraria/manuale), username/email, password (stored), note pubblicazione, azioni (Salva/Abilita/Imposta/Disabilita)
- Messaggio testa: *"Gestisci la tua pubblicità in automatico senza perdite di tempo"*
- "Aggiorna i tuoi siti web" + **"Invia i tuoi immobili al catalogo di Facebook"**
- "Attiva servizio: ATTIVO. PROSSIMO TRASFERIMENTO: 16/06/2026"
- Modello Idealista (raccontato dal Founder): *"Idealista legge dal mio sito ogni 1-2h, gli annunci diventano 'annunci in evidenza' sul portale"* → pull da URL, non push

### Schema XML feed (analisi del file reale)
- Root: `<import>` con N `<immobile id="…">`
- **Oltre 100 campi per immobile**, inclusi:
  - **Multilingua nativo**: testo + testo_eng + testo_ted + testo_fra + testo_spa + testo_rus
  - **Codici tipologia numerici**: 3=Appartamento, 10=Villa, 31=Attico, 32=Villa schiera, 33=Bifamiliare, 34=Semi-indipendente, 4=Att. commerciale, 20=Laboratorio, 54=Bar (etc.)
  - **Codici classe energetica numerici**: 2=A, 3=B, 8=G, 10=A4, 18=F (necessita decodifica)
  - **Codice categoria**: R=Residenziale, U=Ufficio, C=Commerciale
  - **Codice contratto**: V=Vendita, A=Affitto, S=Sfitto/Stagionale
  - Coordinate lat/lng, mappa_visibile flag
  - 7 classi energetiche DL2015 separate (EpglRen, EpglNRen, EpiInv, EpeEst, PefInverno, PefEstate, QuasiZero)
  - Foto: titoloN + urlN + tipoN (tipo F=Foto, P=Piantina) ripetuti per ogni foto, su CDN Agestanet
  - Tipo incarico: E=esclusivo
  - Note: riservate, condivise, luogo appuntamento, orario visite
  - Flag: prestigio, rent_to_buy, permuta, asta, investimento, vista_mare, ult_piano (ultimo piano flag)

---

## 2. Dove Agestanet vince (non sottovalutare)
1. **92 portali multiposting con auto-trasferimento schedulato**
2. **MLS network italiano massiccio** (~2.000 agenzie, ~200k immobili, ~1.4M richieste)
3. **XML schema standardizzato** (codici numerici, multi-lingua)
4. **Sito web auto-generato** dal feed
5. **Crediti referral integrati**
6. **Anni di esperienza** = parser dei portali stabili

## 3. Dove Agestanet perde (le nostre leve)
1. **UI orribile** (dashboard sembra del 2010, sidebar fitta, micro-text, low contrast)
2. **Nessuna AI** (zero matching intelligente, zero copywriting, zero lead scoring)
3. **Siti web tutti uguali** (template autogenerato)
4. **Password portali stored in chiaro/centralizzati** (rischio sicurezza)
5. **Prezzo crescente** (€786/anno → €786+ + portali a parte)
6. **Nessun listino pubblico** (opacità)
7. **Multilingua presente nel feed ma forse non in UI**
8. **Sito web auto-aggiornato dal feed = lock-in di formato**

---

## 4. 🎯 Strategia OMNIA — risposta diretta alla domanda del Founder

> *"Cosa pensi ci risponda un'agenzia con centinaia di immobili e decine di subagenti quando gli diremo di migrare tutto verso il nostro gestionale?"*

**Risposta**: NO, e ha ragione. Il rischio operativo di "spegnere Agestanet domani" è troppo alto. → la migrazione non è una scelta, è una **rampa graduale**.

### Modello commerciale a 4 tier (formalizza la richiesta del Founder A+B)

| Tier | Cosa include | Lancio | Target |
|---|---|---|---|
| **OMNIA Listing** | Solo portale pubblicitario OMNIA + 2 annunci gratuiti + tools privati base | GRATIS fino a 5 annunci, poi €19/mese | Privati venditori / micro-agenzie |
| **OMNIA Bridge** 🔥 | Clone-from-URL del sito + **Multiposting OMNIA (92 portali stile Agestanet)** + Lead Aggregator + Sistema crediti AI base. **Mantieni il tuo gestionale** (Agestanet/Gestim/Realgest…) | €49/mese | Agenzie con CRM funzionante che vogliono sostituire **solo** sito + risparmiare su portali |
| **OMNIA Full** | Bridge + CRM completo (clienti/immobili/match/AI lead score) + crediti AI piena potenza + import bidirezionale | €99/mese | Agenzie pronte a sostituire anche CRM, graduale |
| **OMNIA Enterprise** | Full + multi-sede + sub-agenzie illimitate + Academy + custom domain + analytics + dedicated success manager | da €299/mese | Network/franchising/grandi agenzie |

### Killer feature OMNIA Bridge (tier che attacca direttamente Agestanet)
- **Stesso schema XML Agestanet IN/OUT** → import 1-click + export verso portali che già pullano da Agestanet
- **92 portali multiposting** replicati (lo so ora, ho lo schema)
- **Sito clone-from-URL** → l'agenzia non perde nulla (cliente finale non si accorge del cambio)
- **MLS bridge mode**: continuiamo a leggere da MLS Agestanet (read-only) finché OMNIA MLS non scala
- **Lead Scoring AI** (M2.S4 già live) come "extra" vs Agestanet zero-AI

---

## 5. Piano tecnico M2.S5 — 4 layer

### Layer A — Portal Manager
- Tabella stile Agestanet con N portali (partenza: Idealista, Immobiliare.it, Casa.it, Wikicasa, Subito.it, Bakeca, Trovacasa, Subito, **Facebook Catalog**, **YouTube embed**)
- Per agenzia: credenziali per portale (encrypted AES-256 per agency)
- Schedulazione: oraria/giornaliera/manuale
- Stato: ATTIVO/DISATTIVO/ERROR + ultimo trasferimento + prossimo trasferimento
- Audit log push/pull

### Layer B — Feed XML Generator
- **Endpoint pubblico per-agenzia**: `https://feed.omniarealestateecosystem.it/{agency-slug}.xml`
- Schema in 2 dialetti:
  - **Agestanet-compatible** (default): replica 1:1 lo schema XML che ho appena analizzato → tutti i portali che già pullano da Agestanet continuano a funzionare
  - **OMNIA-extended**: stesso schema + tag custom (lead_score, ai_description, virtual_tour_url)
- Cache CDN edge per le agenzie con migliaia di immobili

### Layer C — Site as listing source (Idealista mode)
- Per agenzie con sito OMNIA (clone-from-URL): le pagine immobili sono già crawlable per Idealista
- Per agenzie con sito esterno: forniamo widget JS embed che inietta annunci da OMNIA nel loro sito esistente

### Layer D — Clone-from-URL (M2.S5 o M2.S6)
- Playwright + Gemini Vision → bundle Next.js statico identico al vecchio sito
- Deploy automatico su dominio dell'agenzia (CNAME)

---

## 6. Domande aperte / prossime decisioni

1. **Pricing Bridge €49/mese**: ok o ricalibriamo? (Agestanet costa al Founder €786/anno solo gestionale base, +portali a parte)
2. **Quanti dei 92 portali partire?** Suggerisco fase 1 = top 8 (Idealista, Immobiliare.it, Casa.it, Wikicasa, Subito, Bakeca, **Facebook Catalog**, Trovocasa) + altri 84 da espandere progressivamente
3. **Multilingua nel CRM**: replicare i 5 idiomi Agestanet (it/en/de/fr/es/ru) dal giorno 1 OPPURE solo it/en/es (le 3 attuali OMNIA) e altri opt-in?
4. **MLS Bridge read-only Agestanet**: tecnicamente fattibile se Agestanet espone API/feed lettura. Da indagare con il Founder se ha accesso alle API o se ha solo l'export XML
5. **Dominio feed**: `feed.omniarealestateecosystem.it` o sottodominio cliente?

---

## 7. Stato
- ✅ Analisi competitiva Agestanet completata 18/06/2026
- ✅ XML schema decodificato (mapping per parser/generator)
- ⏳ Decisione finale modello commerciale (Founder)
- ⏳ Avvio M2.S5 Layer A (Portal Manager) — prima feature dopo conferma

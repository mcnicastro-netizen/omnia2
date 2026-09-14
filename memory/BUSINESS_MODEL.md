# 💰 OMNIA — Business Model & Revenue Streams
## Documento strategico — versione 1.0 (24 Giugno 2026)

> **Lettura critica del Founder**: l'analisi iniziale considerava SOLO subscription B2B → sottostima di ~88% del valore reale.
> Questa versione è la mappa corretta a 7 stream.

---

## 🎯 OMNIA NON è un CRM SaaS
È un **marketplace immobiliare multi-side** con 4 attori e 7 stream di ricavo:

```
        ┌───────────────────────────────────────────────────┐
        │              OMNIA Real Estate Ecosystem          │
        └───────────────────────────────────────────────────┘
                 ↑              ↑                ↑
            B2B Agenzie    Privati B2C    Partner servizi
            (subscription  (annunci      (mutui, notai,
            + crediti)     a pagamento)  APE, foto, ecc.)
                 ↑              ↑                ↑
                 └──────────────┴────────────────┘
                       Network effect:
                       più agenzie ⟶ più annunci ⟶ più privati ⟶
                       più lead ⟶ più valore per agenzie...
```

Il riferimento corretto non è Agestanet (puro SaaS), ma **Idealista + Zillow + Compass** ibridati per il mercato italiano.

---

## 📊 I 7 stream di ricavo dettagliati

### 1️⃣ Subscription B2B agenzie
| Tier | Prezzo/agenzia/mese | Bucket incluso | Costo nostro | Margine |
|---|---:|---|---:|---:|
| Starter | €69 | 2 agenti · 30 annunci · 40 staging + 8 video | ~€15 | 78% |
| Pro | €189 | 6 agenti · 150 annunci · 200 staging + 40 video | ~€50 | 74% |
| Premium | €499 | illimitati · 1000 staging + 200 video soft cap | ~€152 | 70% |
| Enterprise | custom (€1.200+) | white-label · API · SSO | variable | 60-70% |

**Stima 1000 agenzie a regime**: €2.064.000/anno

### 2️⃣ Overage / Credits B2B (consumo extra)
Letteratura SaaS: 20-40% del subscription fee aggiunto in overage.

| Voce | Prezzo | Costo | Margine |
|---|---:|---:|---:|
| Staging extra | €0,90/img | €0,06 | 93% |
| Pacchetto 50 staging | €39 | €3 | 92% |
| Video extra | €3,90 | €0,31 | 92% |
| Pacchetto 20 video | €69 | €6,20 | 91% |
| AL Legal extra | €0,60/query | €0,02 | 97% |
| Vetrina annuncio portale | €19/mese | €0,80 | 96% |
| Top spotlight homepage | €99/mese | €1,50 | 98% |
| Setup brand + foto pro | €299 una tantum | €120 | 60% |
| Account manager dedicato | €200/mese | €100 | 50% |
| API access franchise | €99/mese | €15 | 85% |
| Storage upgrade +100GB | €10/mese | €2 | 80% |

**Stima a regime**: €700.000/anno (~30-50% del subscription)

### 3️⃣ B2C annunci privati (LO STREAM PIÙ GRANDE)
Mancato nella prima analisi. Modello allineato a Idealista/Subito.it.

| Pacchetto | Prezzo | Durata | Cosa include |
|---|---:|---|---|
| Free | €0 | 60 gg | 1 annuncio base, 5 foto |
| Vetrina | €19 | 30 gg | Badge "in vetrina", foto extra, 3-5× visibility |
| Premium | €49 | 30 gg | Top categoria + virtual staging (3 inclusi) + statistiche + supporto |
| Top placement | €99 | 30 gg | Homepage carosello + video micro-tour + lead routing diretto + URL custom |
| **Pacchetto Vendi Casa Tutto Compreso** | €299 una tantum | – | Premium 90gg + 8 staging + video + AL Legal review proposta + lead SMS |

#### Add-on transactional B2C
| Servizio | Prezzo | Costo | Margine |
|---|---:|---:|---:|
| Valutazione PDF firmata | €9,90 | €0,30 | 97% |
| Staging singolo on-demand | €4,90 | €0,06 | 99% |
| Set 4 staging | €14,90 | €0,24 | 98% |
| Video micro-tour | €9,90 | €0,31 | 97% |
| Foto pro (terzisti) | €99 (40% a OMNIA) | – | 40% |
| Boost 24h homepage | €4,90 | €0,20 | 96% |
| Estensione +30gg | €9,90 | €0,15 | 99% |

**Stima 10k annunci/mese anno 2-3**:
- Vetrina (35%): €66.500/mese
- Premium (18%): €88.200/mese
- Top (5%): €49.500/mese
- Pacchetto completo (2%): €59.800/mese
- Add-on misti: €25.000/mese
- **Totale: ~€290.000/mese = €3.500.000/anno**

### 4️⃣ Lead-gen premium
- Lead "qualificati" (scoring AI ≥80): €15-25/cad
- Lead "esclusivi" (non condivisi): €39-59/cad
- Inclusi nei tier Premium/Enterprise

**Stima**: 750 agenti × 10 lead/mese × €18 = **€135.000/mese = €1.620.000/anno**, margine 98%

> ⚠️ **GDPR**: il B2C deve dare consenso esplicito al routing multi-agenzia. Da inserire nel flusso contatto.

### 5️⃣ Marketplace partner commissions (M5+)
| Servizio | Commissione | Volume anno 3 |
|---|---|---|
| Mutui broker (M5.S5) | 0,3-1% mutuo erogato | 200 pratiche/mese = €150k/mese |
| APE certification (M5.S6) | €15-30 commissione | 800/mese = €20k/mese |
| Notai referral | €30-100/pratica | 100/mese = €8k/mese |
| Assicurazione casa (referral) | 10-15% premio annuo | 300/mese = €12k/mese |
| Fotografia professionale (marketplace) | 25% | 500/mese × €100 = €12.5k/mese |
| Cleaning + staging fisico (terzisti) | 20% | 200/mese × €150 = €6k/mese |
| **TOTALE Stream 5** | | **~€208k/mese = €2.5M/anno** |

Margine ~100% (pure commission).

### 6️⃣ Data insights B2B (anno 3+)
- Report mercato a banche (UniCredit, Intesa) per pricing mutui dinamico
- Sviluppatori real estate (Coima, Hines) per scelta zone
- Pubblicazioni di settore

**Stima anno 3+**: €100-300k/anno, margine 95%.

### 7️⃣ Omnia Academy (M6)
- Subscription Academy: €29/agente/mese
- Corsi singoli: €99-499
- Certificazioni: €299

**Stima anno 2-3**: 30% degli agenti totali × €29 = ~€26.000/mese = €310.000/anno

---

## 💎 RICAVO TOTALE CONSOLIDATO

### Anno 3 (1000 agenzie + portale B2C maturo)

| Stream | Ricavo annuo | % | Margine |
|---|---:|---:|---:|
| 1. Subscription B2B | €2.064.000 | 19% | 80% |
| 2. Overage credits B2B | €700.000 | 6% | 92% |
| 3. **B2C annunci privati** | **€3.500.000** | **32%** | 93% |
| 4. Lead-gen premium | €1.620.000 | 15% | 98% |
| 5. Marketplace partners | €2.500.000 | 23% | 100% |
| 6. Data insights | €200.000 | 2% | 95% |
| 7. Academy | €310.000 | 3% | 75% |
| **TOTALE ANNUO ANNO 3** | **€10.894.000** | 100% | **media 89%** |

**Costi totali annui (variabili + fissi a 1000 agenzie + ops B2C)**: ~€1.500.000

**EBITDA stimato anno 3**: **~€9.400.000 (86% margine)**

---

## 📈 Confronto vs analisi precedente

| Voce | Analisi vecchia (Stream 1 only) | Analisi corretta (7 stream) | Δ |
|---|---:|---:|---:|
| Ricavo annuo @1000 agenzie | €1.282.000 | €10.894.000 | **+750%** |
| Margine medio | 80% | 89% | +11% |
| EBITDA stimato | €1M | €9,4M | **+840%** |
| Posizionamento | "CRM Italian SaaS" | "Real estate marketplace + SaaS" | – |

---

## 🎯 Implicazioni strategiche chiave

1. **Le agenzie sono il funnel, non il profit center**. Il vero motore di ricavi è il **B2C privati + marketplace partner**.
2. **Pricing aggressivo per agenzie** è giustificato: cross-stream da ogni agenzia attiva è €2k-5k/anno (oltre subscription).
3. **Founder 50 a −50% lock-in 24 mesi** è il GTM consigliato: pesa solo €40k/anno mancati ma sblocca ~30-50 annunci/agenzia → €60k+/anno indiretti.
4. **Priorità roadmap aggiornata**:
   - **M4 — Stripe + crediti + monetizzazione B2C portale** = LA PRIORITÀ ASSOLUTA dopo M5.S4 (sblocca Stream 2, 3, 4)
   - **M5.S4 Virtual Staging** = abilita Vetrina/Premium/Top B2C
   - **M5.S5 Comparatore mutui** = sblocca Stream 5 (€150k/mese partner commission)
   - **M5.S6 APE** = altro pezzo Stream 5
   - **M6 Academy** = Stream 7

---

## 🚨 Necessità validazione esterna

Le stime di volume B2C (10.000 annunci/mese anno 2) sono **plausibili ma non garantite**. Dipendono da:
- SEO + ads + network effect + churn
- Posizionamento marketing vs Idealista (con 15M visitatori/mese)
- Velocità di adozione agenti pilot

**Founder richiede consulenza esperta esterna** prima di committare risorse pesanti:

### Profili consigliati
- **Commercialista fiscale startup SaaS** (€200-300/mese): VivaCloud Studio, TaxFin, Italian Startup Lawyers
- **Fractional CFO real estate** (€800-1.500/mese, 10h/sett): CFOforHire.it, Treeesy, CFOhub
- **Advisor real estate ex-CFO** (€1.500-3.000 una tantum): cerca ex-CFO Casa.it/Idealista/Tecnocasa su LinkedIn

**Budget minimo consulenza pre-lancio**: €1.500-3.000 una tantum + €300/mese commercialista ongoing.

---

## 📋 Action items dopo questa analisi

1. ⏳ **Attendere validazione esperto esterno** dei volumi B2C
2. 🟡 Sviluppare prima **M5.S4 Virtual Staging** (sblocca vetrina/premium B2C)
3. 🟡 Sviluppare **M4 Stripe + crediti** subito dopo M5.S4 (sblocca monetizzazione)
4. 🟡 Costruire **landing pricing** con simulatore "Quanto risparmi con OMNIA"
5. 🟡 Lanciare **Founder 50** a −50% lock-in 24 mesi
6. 🟡 Architecture review GDPR per lead-gen multi-agenzia (consenso esplicito B2C)

---

*Documento da revisionare ogni trimestre o dopo cambiamenti significativi del mercato.*
*Ultimo aggiornamento: 24 Giugno 2026.*
*Owner: mcnicastro-netizen + E1*

# 🔍 OPEN-SOURCE FINDINGS PER OMNIA

**Data ricerca**: 29 Giugno 2026
**Trigger**: Founder ha chiesto se su GitHub ci sono progetti utili a OMNIA che non richiedano GPU pesanti.
**Risultato**: 7 progetti game-changer/strong-add + 4 backlog interessanti + 5 esclusi GPU-heavy.

---

## 🟢 GAME CHANGER — Sostituiscono integrazioni a pagamento previste

### 1. `zornade/visura-api` ⭐⭐⭐
- **URL**: https://github.com/zornade/visura-api
- **License**: GPL-3.0
- **Stack**: Python (FastAPI) + Playwright headless
- **Cosa fa**: automatizza estrazione visure catastali dal portale SISTER dell'Agenzia delle Entrate
- **Sostituisce**: VisureItalia API (€2-8/visura)
- **Risparmio stimato**: €3.000-12.000/anno a regime su 50 agenzie
- **Effort integrazione**: 3-5 giorni (post-SRL)
- **Quando integrare**: M5.S8 (firma elettronica + visure)
- **Caveat legale**: Playwright headless su SISTER è grey-area, richiede revisione avvocato (~€200 una tantum, insieme a T&C AL Legal). Serve account SISTER ufficiale (post-SRL).

### 2. Zornade platform ⭐⭐⭐
- **URL**: https://zornade.com
- **Cosa fa**: 85 milioni particelle catastali italiane già arricchite + dati OMI + 15+ fonti ufficiali (rischio sismico, demografia, ISTAT). REST API + dataset scaricabili + plugin QGIS.
- **Sostituisce**: parte del dataset città/province manuale del Valuator + buona parte di servizi GIS futuri
- **Risparmio stimato**: €1.500-5.000/anno
- **Effort integrazione**: 1 giorno (API consumption)
- **Quando integrare**: upgrade Valuator post-MVP o quando serve granularità sub-quartiere
- **Caveat**: piattaforma ospitata da terzi → valutare SLA + possibile fork in-house

### 3. `ondata/dati_catastali` ⭐⭐
- **URL**: https://github.com/ondata/dati_catastali
- **Stack**: Parquet + DuckDB
- **Cosa fa**: query dati catastali vettoriali 2025 ufficiali Agenzia delle Entrate (foglio + particella → coordinate → poligono via WFS)
- **Impatto OMNIA**:
  - Arricchimento Valuator con superficie catastale ufficiale
  - Verifica indirizzi a livello particella (M5.S6 APE serve dati esatti)
- **Costi**: zero
- **Quando integrare**: parallelo a M5.S6 APE o sub-step del Valuator Pro

---

## 🟡 STRONG ADD — Migliorano feature esistenti

### 4. `SenatoDellaRepubblica/PArSe` ⭐⭐
- **URL**: https://github.com/SenatoDellaRepubblica/PArSe
- **Cosa fa**: parser ufficiale del Senato per testi normativi italiani (leggi, articoli, commi, decreti). Strutturazione semantica.
- **Impatto OMNIA — AL Legal (M5.S3)**:
  - Migliora qualità citazioni inline (oggi parsate ad-hoc da Tavily)
  - Strutturazione semantica: "Art. 1567 c.c. → comma 2 → lettera a)"
  - Riduce hallucination: validator confidence 0.85 → potenziale 0.95
- **Effort integrazione**: 1-2 giorni
- **Quando integrare**: enhancement M5.S3 (AL Legal v2)

### 5. `italia/awesome-italian-public-datasets` ⭐⭐
- **URL**: https://github.com/italia/awesome-italian-public-datasets
- **Cosa fa**: catalogo curato dataset open della PA italiana (Developers Italia ufficiale)
- **Impatto OMNIA**:
  - Bacino di fonti dati per Valuator (popolazione comune, redditi medi ISTAT, indici criminalità, scuole, trasporti pubblici, hot-spot turistici)
  - Migliora comparables con micro-dati di quartiere
- **Quando integrare**: continuo, lookup quando serve enrichment Valuator/Search

### 6. `AgID/cruscotto-italia` ⭐
- **URL**: https://github.com/AgID
- **Cosa fa**: piattaforma AgID federante dataset ufficiali per comune (OMI + catasto + demografia + rischio sismico/idrogeologico)
- **Impatto OMNIA**:
  - Fonte ufficiale governativa → vantaggio legale (citabile in AL Legal e nelle valutazioni)
  - Affidabilità superiore vs Zornade (zero rischio shutdown)
- **Risparmio stimato**: €500-2.000/anno (dataset sparsi a pagamento)
- **Effort integrazione**: 1-2 giorni
- **Quando integrare**: parallelo a #5

### 7. `opendataloader-project/opendataloader-pdf` ⭐⭐
- **URL**: https://github.com/opendataloader-project/opendataloader-pdf
- **Cosa fa**: parser PDF open-source che estrae testo strutturato + tabelle anche da PDF complessi (planimetrie commentate, perizie, APE storici, atti notarili scansionati)
- **Impatto OMNIA**:
  - Upgrade modulo PDF analysis AL Legal (oggi max 5MB / 60 pp / 40k char)
  - Sblocca eventuale modulo "importa perizia esistente" (utente carica perizia → OMNIA estrae automaticamente dati immobile)
- **Effort integrazione**: ½ giornata
- **Quando integrare**: enhancement M5.S3 v2 oppure D-FUTURE-09 (AI Smart Import v2 PDF+Screenshot)

---

## 🔵 BACKLOG INTERESSANTE — Valutare quando arriviamo lì

### 8. `pigreco/workshop-estate-gis-2021`
- Tutorial QGIS + WMS Agenzia Entrate (`wms.cartografia.agenziaentrate.gov.it`) per visualizzare/digitalizzare particelle catastali
- License CC BY 4.0
- Utile per documentare flusso GIS interno + futuro tool "vedi catasto sulla mappa" su portale B2C
- Quando: post-M3 enhancement Valuator/Search

### 9. `CarbonImage/BatchPlan`
- Estrae planimetrie/layout da file IFC (architettura BIM), no GPU
- Utile solo se OMNIA integra mai BIM/architetti — improbabile prima di 12+ mesi
- Quando: backlog far-future

### 10. `TeaganLi/HouseExpo`
- Dataset 35.126 planimetrie 2D con etichette stanze (cucina/camera/bagno)
- Potenziale: training classificatore "leggi pianta → conta stanze" per auto-popolare form annuncio
- Quando: P3 backlog AL features

### 11. `mehanix/arcada`
- Editor planimetrie browser (React + Pixi.js)
- Potenziale: tool "disegna pianta del tuo immobile" su Sell Page B2C
- Quando: nice-to-have, marginale

---

## ❌ ESCLUSI — GPU-heavy o non rilevanti

| Progetto | Perché scartato |
|---|---|
| Stable Diffusion ONNX su CPU (`microsoft/ONNX-Stable-Diffusion`) | 30-90s/immagine = inutilizzabile in produzione. fal.ai a €0,06/immagine è giusto compromesso |
| AUTOMATIC1111 webui --cpu | Stesso problema CPU lentezza |
| HouseCrafter | Richiede GPU A100 |
| LayoutGMN | Richiede GPU |
| Tutti i video generator OS | GPU-heavy + qualità inferiore a Sora 2 |

---

## 📊 IMPATTO POTENZIALE A REGIME (50 agenzie)

| Progetto | Sostituisce | Risparmio annuo | Effort |
|---|---|---|---|
| `zornade/visura-api` | VisureItalia | €3.000-12.000 | 3-5 giorni |
| `ondata/dati_catastali` | nuova feature | gratis upgrade Valuator | 1-2 giorni |
| Zornade platform | OMI + GIS futuri | €1.500-5.000 | 1 giorno |
| `PArSe` Senato | qualità AL Legal | N/A (+30% qualità) | 1-2 giorni |
| `cruscotto-italia` AgID | dataset sparsi | €500-2.000 | 1-2 giorni |
| `opendataloader-pdf` | PDF parsing | N/A (+ qualità) | ½ giornata |

**Risparmio totale stimato**: **€5.000-19.000/anno** + qualità di prodotto significativamente superiore.

---

## 🎯 ORDINE DI INTEGRAZIONE PROPOSTO

Seguendo il `PROGRAMMA_OMNIA.md` originale (D-035) e la sequenza D-032:

1. **Nessuna integrazione ORA** — la sequenza vincolata è M5.S4 → M5.S5 → M5.S6 → M5.S2 → M6 → M4
2. **Durante M5.S3 v2** (enhancement AL Legal): integrare `PArSe` + `opendataloader-pdf`
3. **Durante M5.S6 APE**: integrare `ondata/dati_catastali` + `cruscotto-italia` per dati ufficiali
4. **Durante M5.S8** (post-SRL): integrare `zornade/visura-api` come stack visure ufficiale
5. **Continuo**: lookup su `awesome-italian-public-datasets` per micro-enrichment Valuator/Search
6. **Backlog**: BatchPlan / HouseExpo / arcada quando emerge bisogno specifico

---

## ⚠️ ACTION ITEM PER FOUNDER

- [ ] **Revisione legale visura-api** (insieme a T&C AL Legal, ~€200 una tantum avvocato): valutare grey-area Playwright headless su SISTER prima di integrare in produzione
- [ ] **Account SISTER ufficiale** (Agenzia delle Entrate): apertura post-SRL, necessario per `visura-api`
- [ ] **Decisione fork Zornade in-house**: valutare se dipendere da loro API o forkare il codice e ospitarlo internamente (controllo SLA)

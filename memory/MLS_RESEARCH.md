# 🎯 MLS Reference Research — Agesta.NET + nicastroimmobiliare.it

**Data ricerca**: 03 Luglio 2026
**Obiettivo**: Recuperare i materiali di riferimento MLS forniti dal Founder in sessioni precedenti, per l'implementazione futura di M4.S1+S2 (MLS Network multi-agenzia).

---

## ✅ MATERIALI TROVATI — Agesta.NET (nostro benchmark)

### 1. `area riservata agenzia.jpg` ⭐⭐⭐ (fonte primaria)
- **URL**: https://customer-assets.emergentagent.com/job_audit-tool-12/artifacts/14ss24l9_area%20riservata%20agenzia.jpg
- **Contenuto**: Dashboard Agesta.NET con blocco "Agesta.NET MLS" completo

**Struttura UI da replicare in OMNIA**:

#### Header banner "Collaborazioni con altre agenzie" (verde)
- 17 destinatari (agenzie in network)
- 96 offerte (share attive)
- 1 invito (pending)

#### Blocco "Agesta.NET MLS" (3 sotto-sezioni)
- **"Il mio MLS"** = inventory agenzia:
  - N immobili shared
  - N attività esclusive
  - N immobili con foto (quality flag)
- **"MLS [Provincia]"** = network locale:
  - 75 annunci
  - 5.811 richieste
- **"MLS Italia"** = network nazionale:
  - 1.803 annunci
  - 198.963 richieste

#### Contatori attività cross-agency (a lato)
- 136 offerte inviate da altre agenzie
- 19 richieste condivise
- 24.164 richieste totali
- 1.439.292 richieste storico

#### Menu navigation MLS-related
- Agenzie partner
- MLS API
- Registrazione in AgestaNET
- Gestione Agenti
- Statistiche
- Report

#### Alert "Contratto in scadenza" (banner rosso 39%)
→ pattern per notifiche urgenti/scadenze

### 2. `portali 1.jpg` (fonte secondaria)
- **URL**: https://customer-assets.emergentagent.com/job_audit-tool-12/artifacts/ep3t3nfk_portali%201.jpg
- **Contenuto**: Sezione "PORTALI IMMOBILIARI ATTIVI"
- Note: distribuzione multi-portale, non MLS in senso stretto. Utile solo per confronto UX portali.

### 3. `portali 2.jpg` (fonte secondaria)
- **URL**: https://customer-assets.emergentagent.com/job_audit-tool-12/artifacts/jusfbywg_portali%202.jpg
- **Contenuto**: "AGGREGATORI DI ANNUNCI" + "PORTALI IMMOBILIARI NON ATTIVI (17)"
- Note: gestione stato portali (attivo/inattivo), workflow "Richiedi" attivazione.

---

## ❌ MATERIALI NON TROVATI

### ~~Screenshot box MLS su nicastroimmobiliare.it~~ ✅ RICEVUTO 03-Lug-2026
Founder ha caricato lo screenshot della home nicastroimmobiliare.it che mostra:

### Box MLS pubblico (a sinistra della home)
- **Header verde**: **"130.000 immobili condivisi"** (in bianco) → CLAIM KILLER del network AgestaNet
- **4 dropdown compatti**:
  - Contratto: `Vendita` (default)
  - Categoria: `Residenziale` (default)
  - Provincia: `CATANIA` (pre-selezionato → contesto agenzia)
  - Comune: `Scegli`
- **Range Prezzo**: 2 input (min, max)
- **CTA**: bottone grigio "avvia la ricerca"
- **Footer badge**: "POWERED BY AGESTANET" (in nero, prominente)

### Box "Cerca il tuo immobile" (a destra, verde grande)
Inventory SOLO dell'agenzia Nicastro (non MLS):
- Contratto, Categoria (Tutti/Tutti default)
- Tipologia, Provincia
- Comune, Prezzo (da-a)
- Mq (da-a), Vani (da-a)
- Camere (da-a), Riferimento
- Ordine: Rilevanza
- CTA: bottone nero "Avvia la ricerca"

### 🎯 Insight strategico fondamentale
**Il pattern MLS ha DUE facce**:
1. **Backend agenzia** (dashboard Agesta.NET area riservata) → strumento operativo con contatori offerte/richieste/collaborazioni tra agenzie
2. **Frontend pubblico** (home sito agenzia) → **vetrina promozionale** che sfrutta il volume del network come selling point: "130k immobili condivisi" attrae il buyer, poi lo canalizza sul sito dell'agenzia

Il visitor sulla home ha **scelta binaria**:
- Ricerca ristretta (inventory Nicastro) → form ricco a destra
- Ricerca ampia (network MLS nazionale) → form semplificato a sinistra

**Coesistenza dei due box** è la chiave: l'agenzia mostra ampiezza (network) MA canalizza il lead sul proprio dominio.

### Traduzione OMNIA
Sul sito white-label agenzia (`agenzia.omnia/{slug}` o custom domain):
- Box "Cerca nel network OMNIA" a sx (con contatore live "N immobili condivisi")
- Box "Cerca nella nostra agenzia" a destra (inventory proprio)
- Badge "POWERED BY OMNIA" opzionale (Founders 50: gratis; free tier: obbligatorio)

Screenshot memorizzato negli asset del job (Founder upload 03-Lug-2026).

---

## 🎯 MAPPATURA PROPOSTA Agesta.NET → OMNIA (M4.S1+S2 future)

| Concetto Agesta.NET | Traduzione OMNIA | File / entità |
|---|---|---|
| "Il mio MLS" (inventory agenzia) | `properties.privacy_level = "mls_member"` (già campo modello) | `apps/immoweb/properties.py` |
| "MLS [Provincia]" (network locale) | Query filtered by `province_sigla` + `privacy_level="mls_member"` | Nuovo `apps/immoweb/mls.py` |
| "MLS Italia" (network nazionale) | Query aggregate senza filtro geografico | Nuovo `apps/immoweb/mls.py` |
| "17 destinatari" (agenzie in network) | `mls_partners` collection: `{agency_id, partner_id, since, status}` | Nuovo modello |
| "96 offerte / 1 invito" | `mls_requests`: `{from_agency, to_agency, property_id, type, status, expires_at}` | Nuovo modello |
| "Registrazione in AgestaNET" | Onboarding wizard MLS → firma agreement + T&C | Estensione `apps/immoweb/agencies.py` |
| Contatore "5.811 richieste" | `mls_events` collection audit log 5 anni retention | Nuovo modello |
| Notifica scadenza contratto | Sistema notifiche in-app + email (Resend) | Estensione notifications |
| **Box "130.000 immobili condivisi"** (frontend pubblico) | Widget "Cerca nel network OMNIA" (counter live + form semplice provincia/comune/prezzo) da inserire sui siti white-label agenzie | Nuovo componente in `apps/immoweb/themes.py` |
| **Badge "POWERED BY AGESTANET"** (footer box) | Badge "POWERED BY OMNIA" (opzionale Founders 50, obbligatorio free tier) | Estensione themes.py |

---

## 📋 DECISIONE STRATEGICA APERTA

Dal `PROGRAMMA_OMNIA.md` + D-032: M4 (Stripe + MLS) è **rinviato post-società**. Ma la struttura MLS può essere sviluppata **prima** dello Stripe (D-032 M5 prima di M4), quindi:

**Ordine tecnico consigliato**:
1. M5.S4.2 → M5.S4.3 → M5.S4.4 (completamento Virtual Staging) — 2-3 sessioni
2. M5.S5 Comparatore Mutui — 1-2 sessioni
3. M5.S6 APE calcolo orientativo — 1-2 sessioni
4. M5.S2 AL Knowledge RAG (dopo manuale) — 2 sessioni
5. **M6 Academy struttura base** — 3-4 sessioni (obbligatorio per Founder per riaprire pre-launch, D-035)
6. **M4.S1+S2 MLS** — 3-4 sessioni (fattibile senza Stripe usando queste reference Agesta.NET)
7. M4.S3+S4+S5 Stripe + Crediti + Boost — dopo SRL

---

## 🔗 Link diretti per riferimento veloce nelle prossime sessioni

- Area riservata Agesta.NET (dashboard MLS): https://customer-assets.emergentagent.com/job_audit-tool-12/artifacts/14ss24l9_area%20riservata%20agenzia.jpg
- Portali attivi Agesta.NET: https://customer-assets.emergentagent.com/job_audit-tool-12/artifacts/ep3t3nfk_portali%201.jpg
- Portali inattivi Agesta.NET: https://customer-assets.emergentagent.com/job_audit-tool-12/artifacts/jusfbywg_portali%202.jpg
- Schema Santo Graal OMNIA: https://customer-assets.emergentagent.com/job_audit-tool-12/artifacts/aru1brrm_ChatGPT%20Image%2015%20apr%202026%2C%2018_03_21.png
- PDF Progetto Omnia originale: https://customer-assets.emergentagent.com/job_audit-tool-12/artifacts/tmhfg909_progetto%20Omnia.pdf

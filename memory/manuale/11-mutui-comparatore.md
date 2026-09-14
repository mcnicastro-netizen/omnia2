# Capitolo 11 · Mutui — comparatore ipotecario

> **Cosa trovi in questo capitolo**
> Il **Comparatore Mutui** simula in modo orientativo l'importo della rata, il TAEG e il costo totale di un mutuo prima casa/seconda casa, confrontando fino a **14 offerte curate** di **8 banche italiane**. Serve al proprietario in vendita per capire "quanto rende mensilmente" un immobile a un potenziale acquirente, e all'acquirente/lead per orientarsi prima del colloquio bancario. Il capitolo copre: come funziona il motore, dove trovi il comparatore (B2C + tool CRM), i vincoli LTV/Consap under-36, sostenibilità rata/reddito, disclaimer legale e limitazioni v1.

**Cosa NON è (D-051 onestà — regola cardine)**
- Non è **offerta al pubblico** né **mediazione creditizia** ai sensi dell'**art. 128-sexies TUB**. È una simulazione informativa.
- Non è un **preventivo bancario ufficiale**: le condizioni effettive le decide la banca al colloquio, potendo differire dalla simulazione.
- Non c'è **convenzione commerciale** con nessuna banca (D-037). Le offerte curate sono nell'interesse dell'utente, non di una specifica banca.
- I dati (spread, benchmark, spese) sono **aggiornati manualmente** (ultimo aggiornamento Giugno 2026): non c'è scraping in tempo reale sui siti delle banche.
- Non genera un **documento SECCI/PIES** né un contratto. Se il lead vuole procedere, deve andare in banca.

---

## 11.1 · Cos'è il Comparatore Mutui e dove lo trovi

**In una frase**
Un motore matematico + tabella curata di 14 offerte di 8 banche italiane che, a partire da prezzo immobile + anticipo + durata + tipo tasso, ti dice **quanto pagheresti di rata mensile**, **quanto TAEG**, **quanto costo totale**, **quanto anticipo minimo serve** e **se la rata è sostenibile** rispetto al tuo reddito.

**I tre punti di contatto**

### A) Portale B2C ImmobilCloud (`/it/cloud/mutui`)
- Pubblico, senza autenticazione.
- Target: privato che vuole comprare/vendere.
- Il visitatore può lasciare un **lead** (con GDPR consent) → viene salvato in `mortgage_leads`.
- Include disclaimer legale in evidenza.

### B) Tool CRM ImmoWeb (`/it/app/tools/mutui`)
- Accessibile a titolare/agente/segreteria dell'agenzia.
- Ideale per l'agente in trattativa: apre il comparatore accanto al cliente e mostra le rate mensili.
- Nessuna raccolta lead (l'agente è già in contatto con il cliente).

### C) Widget embeddabile (partner Web Agency)
- Snippet `<script>` riutilizzabile su siti terzi (partner Track B, D-046).
- Rate limit + credit balance per prevenire abusi.

[SCREEN: cap11-mutui-panoramica]

**Chi può usarlo**
- **B2C**: chiunque, anonimo, senza login.
- **B2B**: titolare, agente, segreteria (tutti gli utenti autenticati agenzia).
- **Widget**: chiunque legga il sito partner che l'ha embeddato.

---

## 11.2 · Come funziona il motore (ammortamento francese + TAEG IRR + soglia usura)

**A cosa serve capirlo**
Se il TAEG di un'offerta ti sembra strano, capisci **come è stato calcolato** e con quali parametri.

**Il motore in 4 stage**

### Stage 1 — Determinazione dell'importo mutuo (LTV)
- `loan_amount = property_price - down_payment`
- `ltv = (loan_amount / property_price) × 100`
- **LTV massimo standard**: **80%** (`MAX_LTV_STANDARD`).
- **LTV massimo under-36 prima casa** (Fondo Consap): **95%** (`MAX_LTV_UNDER36`).
- Se LTV richiesto > max ammesso → il comparatore risponde `eligible: false` con indicazione dell'**anticipo minimo necessario**.

### Stage 2 — Calcolo TAN e rata (per ciascuna offerta)
- **TAN** = `benchmark + spread_banca`
  - **Benchmark fisso** = **Eurirs** per la durata più vicina (curva: 10 anni 2,94% · 15 anni 3,05% · 20 anni 3,17% · 25 anni 3,15% · 30 anni 3,12% — Giugno 2026).
  - **Benchmark variabile** = **Euribor 3M** (2,05% Giugno 2026), con floor a 0 (clausola contrattuale standard).
- **Rata** = ammortamento **francese**: `rata = C × i / (1 - (1+i)^-n)` dove `C` = capitale, `i` = tasso mensile, `n` = numero mesi.
- **Spese upfront**: istruttoria (% o flat con minimo), perizia, **imposta sostitutiva** (0,25% prima casa, 2% seconda casa).
- **Incasso rata**: 0-3,75 €/mese a seconda della banca.

### Stage 3 — Calcolo TAEG via IRR (bisezione)
- Il **TAEG** rappresenta il costo totale del credito annualizzato composto.
- Formula: **IRR mensile** del flusso `(erogato - spese) → rate + oneri` risolto con bisezione (80 iterazioni, precisione ~1e-6).
- Il TAEG risulta **sempre > TAN** perché include spese iniziali e ricorrenti.

### Stage 4 — Controllo soglia usura (TEGM Banca d'Italia)
- Ogni tipo tasso ha un **TEGM** (Tasso Effettivo Globale Medio) rilevato **trimestralmente** dalla Banca d'Italia:
  - **Fisso**: TEGM 4,05% → soglia usura **9,0625%** (TEGM × 1,25 + 4).
  - **Variabile**: TEGM 4,08% → soglia usura **9,10%**.
- Ogni offerta ha un flag `usury_ok`: se `taeg < soglia` → OK, altrimenti la banca **non può** applicare quel tasso legalmente.
- **Aggiornamento manuale trimestrale** (Q1/Q2/Q3/Q4). Vedi §11.9 su cadenza aggiornamento dati.

**Cosa vedi in output** (per ogni offerta ammissibile)
- Banca, prodotto, tipo tasso.
- Benchmark, spread, **TAN**, **TAEG**.
- **Rata mensile** in euro.
- Costi upfront (istruttoria + perizia + imposta sostitutiva).
- Costo totale del mutuo (rate + incasso rata + upfront).
- Interessi totali.
- Rank (1 = miglior TAEG).
- Flag `consap_eligible` (offerta compatibile con Fondo Consap under-36).

---

## 11.3 · Vincoli LTV e Fondo Garanzia Consap under-36

**Cos'è il Fondo Consap prima casa under-36**
- **Consap** (Concessionaria Servizi Assicurativi Pubblici) gestisce un **Fondo di garanzia mutui prima casa** dello Stato.
- Se il richiedente ha **< 36 anni** ed è **prima casa** → può ottenere un mutuo con **LTV fino al 95%** (invece dell'80%).
- Solo alcune banche aderiscono al Fondo Consap (offerta ha `consap: true`).

**Come lo attiva il comparatore**
1. Devi mettere spuntare *"Prima casa"* e *"Under 36"* nel form.
2. Il comparatore calcola il tuo `max_ltv_user = 95` invece che 80.
3. Filtra le offerte con `consap: true` e ammette LTV fino al 95%.
4. Nel risultato appare `consap_applied: true` se l'LTV richiesto è > 80%.

**Attenzione (D-051 onestà)**
- Il **fondo ha un plafond annuale** deciso dal Ministero. Se esaurito, la banca **può rifiutare** anche se sulla carta hai i requisiti.
- Ci sono **altri requisiti reddituali** (ISEE ≤ 40.000 €) che il comparatore **non verifica**: te li chiederà la banca al colloquio.
- Se sei sopra i 36 anni al momento del contratto → **decade il beneficio Consap**, anche se avevi meno di 36 al preventivo.
- Il **tasso Consap** è vincolato ad un **cap** (media Eurirs 10 anni + spread max ~0,45%) — alcune offerte curate potrebbero non rispettarlo. Il comparatore in v1 **non applica ancora** il cap.

**Offerte Consap-eligible in v1** (9 su 14 — dato Giugno 2026)
- Intesa Sanpaolo (Domus Fisso + Variabile)
- UniCredit (Mutuo UniCredit Fisso + Variabile)
- BPER Banca (Fisso + Variabile)
- Crédit Agricole (CA Fisso + Variabile)
- Banca MPS (MPS Fisso)

**Offerte NON Consap** (5 su 14): BNL Fisso, ING Arancio **Fisso**, ING Arancio **Variabile**, Webank Fisso + Variabile → filtrate se attivi il flag under-36.

---

## 11.4 · Sostenibilità rata/reddito

**A cosa serve**
Prima di ottenere il mutuo, la banca controlla che la **rata mensile** non superi una certa percentuale del tuo **reddito netto**. La regola prudenziale universale è ~30-35%.

**Come funziona nel comparatore**
- Il campo `income_monthly` (reddito mensile netto) è **opzionale** nel form.
- Se lo compili, il comparatore calcola:
  - `ratio_pct = (best_rata / income_monthly) × 100`
  - `max_pct = 35%` (`MAX_RATA_REDDITO = 0.35`)
  - `ok = ratio ≤ 0.35`
  - `max_sustainable_rata = income_monthly × 0.35`
- In UI vedi un badge verde ("Sostenibile") o ambra ("Rata > 35% del reddito").

**Cosa NON considera il calcolo (D-051)**
- Altre rate esistenti (prestiti auto, carte revolving, altri mutui).
- Spese fisse mensili (affitto attuale, utenze, spese figli).
- Reddito parziale/stagionale/atipico.
- Presenza di coobbligati (rate divise).

Il colloquio bancario **rileva tutto questo** — la simulazione da la prima indicazione, la valutazione vera arriva dopo.

**Regola d'oro operativa per l'agente**
Se il rapporto rata/reddito è **> 30%**, avvisa già il cliente: la pratica sarà borderline. Meglio proporre subito una **durata maggiore** (rata più bassa) o un **anticipo maggiore** (mutuo più piccolo).

[SCREEN: cap11-mutui-sostenibilita]

---

## 11.5 · Le 14 offerte curate (aggiornate Giugno 2026)

**Chi c'è e chi manca**

| Banca | Fisso | Variabile | Consap under-36 |
|---|:-:|:-:|:-:|
| Intesa Sanpaolo | ✅ Domus | ✅ Domus | ✅ |
| UniCredit | ✅ | ✅ | ✅ |
| BPER Banca | ✅ | ✅ | ✅ |
| Crédit Agricole | ✅ | ✅ | ✅ |
| Banca MPS | ✅ | ⬜ (non in v1) | ✅ (solo Fisso) |
| BNL BNP Paribas | ✅ | ⬜ (non in v1) | ❌ |
| ING | ✅ Arancio | ✅ Arancio | ❌ (nessuna offerta ING Consap in v1) |
| Webank (BPM) | ✅ | ✅ | ❌ |

**Totale**: **14 offerte** di **8 banche distinte** · **9 offerte Consap-eligible** · **5 non-Consap**.

**Range spread osservato Giugno 2026**
- **Fisso**: 0,40% (Webank più aggressivo) → 0,80% (BNL). ING/Webank spesso più economici (canale digitale).
- **Variabile**: 0,80% (Webank) → 1,25% (BPER).

**Range spese**
- **Istruttoria**: 0 € (ING/Webank canale digitale) → 750 € (BPER flat), oppure 0,5-0,6% dell'importo con minimo 400-500 € (banche tradizionali).
- **Perizia**: 250 € (BPER) → 320 € (Intesa).
- **Incasso rata**: 0 €/mese (ING/Webank) → 3,75 €/mese (Intesa Sanpaolo).

**Chi manca in v1** (aggiornamento futuro)
- Deutsche Bank, BPM Fideuram, Findomestic mutui, Kìron, Facile.it (mediazione)
- Banche credito cooperativo/popolari locali (troppa varianza)
- Fintech (Fabrick, ecc.) — appena avranno spread pubblici stabili

**Cosa NON è la lista v1 (D-051)**
- Non è la **classifica delle banche italiane**.
- Non c'è **influenza commerciale** nella selezione (D-037).
- La selezione è pensata per coprire i **profili tipici** (grande banca tradizionale, banca popolare, canale digitale) — non l'universo.

**Data di aggiornamento**
- Ogni response API contiene il campo `data_updated_at` (formato `YYYY-MM`).
- **Aggiornamento manuale trimestrale** consigliato (allineato al TEGM Banca d'Italia). Attualmente **Giugno 2026** (`DATA_UPDATED_AT`).

---

## 11.6 · Come lanci una simulazione (passi B2C)

**Passi utente pubblico su `/cloud/mutui`**
1. Apri `https://omniarealestateecosystem.it/it/cloud/mutui` (o clicca *"Comparatore mutui"* dall'header di ImmobilCloud).
2. Compila il form:
   - **Prezzo immobile** (€) — obbligatorio, min 10.000 €, max 10 M€.
   - **Anticipo** (€) — obbligatorio, non può essere ≥ prezzo.
   - **Durata** — 10/15/20/25/30 anni (`DURATIONS` whitelist).
   - **Tipo tasso** — fisso / variabile / **entrambi** (default).
   - **Reddito mensile netto** (€) — opzionale, per sostenibilità.
   - Spunta **"Prima casa"** e (se sotto 36 anni) **"Under 36"** per attivare Consap.
3. Clicca **Confronta offerte**.
4. Vedi la tabella ordinata per **miglior TAEG** con dettagli.
5. Puoi cliccare **Vedi piano ammortamento** su un'offerta per il dettaglio mensile del primo anno + riepilogo per anno (endpoint separato `/mutui/plan`).
6. Puoi **contattare un agente OMNIA** per approfondire (lead form con GDPR).

**Vincoli input**
- Durata whitelisted (`DURATIONS = [10, 15, 20, 25, 30]`): 12 anni → errore 400.
- Prezzo `> 10.000 € e ≤ 10 M€` (Pydantic).
- Anticipo `≥ 0` e `< prezzo`.
- Tipo tasso in `{fisso, variabile, entrambi}`.

**Errori comuni**

| Codice | Perché | Cosa fare |
|--------|--------|-----------|
| **400 `Durata non supportata`** | Hai messo un valore non nella whitelist | Scegli 10/15/20/25/30 |
| **400 `L'anticipo non può essere ≥ del prezzo`** | Errore di battitura | Correggi l'anticipo |
| **200 `eligible: false, reason: ltv`** | LTV richiesto sopra il max | Il comparatore ti dice l'anticipo minimo necessario nella risposta |

---

## 11.7 · Piano di ammortamento dettagliato

**A cosa serve**
Vedere mese per mese la composizione della rata: quanta parte è **interessi** e quanta è **capitale rimborsato**.

**Come funziona (`POST /mutui/plan`)**
- Input: `loan_amount`, `tan_pct`, `duration_years`.
- Output: `rata` + `months_first_year` (dettaglio primi 12 mesi) + `years` (aggregato per anno).
- Per ogni mese: `rata` (uguale in tutti i mesi), `interest`, `principal`, `balance` residuo.
- Ammortamento **francese** = rata costante, ma nei primi anni prevalgono gli interessi, poi il capitale.

**Perché è utile per l'agente**
- Spiegare al cliente che nei primi 10 anni di un mutuo 30 anni, quasi **il 50% della rata sono interessi**. Se rivende dopo 5 anni, ha rimborsato pochissimo capitale.
- Confrontare 15 vs 30 anni sullo stesso importo: interessi totali crescono in modo non lineare.

**Cosa NON fa il piano ammortamento v1**
- Non gestisce **rate a tasso misto** (fisso per N anni, poi variabile).
- Non gestisce **surroga** (cambio banca a metà).
- Non gestisce **estinzione anticipata** parziale/totale (impatto su saldo).

[SCREEN: cap11-mutui-piano-ammortamento]

---

## 11.8 · Lead capture B2C (GDPR)

**Dove appare**
- Solo sul portale **B2C ImmobilCloud** (`/cloud/mutui`), non nel tool B2B CRM.

**Cosa raccoglie** (`POST /mutui/lead`)
- **Obbligatori**: nome (2-100 caratteri), email valida.
- **Opzionali**: telefono (max 30 caratteri), rata migliore trovata, importo mutuo, durata, tipo tasso.
- **Consenso GDPR**: flag `gdpr_consent` (boolean). **In v1 il consenso non è bloccante** — se manca, il lead viene comunque salvato ma con `gdpr_consent: false`. Roadmap: consenso hard-gate + testo esteso.

**Dove finisce il lead**
- Collection MongoDB: `mortgage_leads`.
- Campi: `id`, `name`, `email` (lowercased), `phone`, `property_price`, `loan_amount`, `duration_years`, `rate_type`, `best_rata`, `gdpr_consent`, `created_at` (ISO UTC), `source: "ImmobilCloud-Mutui"`.

**Chi vede il lead**
- **Super_admin** OMNIA (query lato admin manuale in v1).
- **Nessuna dashboard dedicata** in v1 per gestire lead mutui.
- **Nessun invio automatico** a banche/agenzie: i lead sono al momento un **repository di interesse**, non un funnel commerciale attivo.

**Ciclo di vita del lead** (v1)
- Nessuna nurturing email automatica.
- Nessun assegnamento a un agente specifico.
- Nessun forward a partner bancari.
- Solo repository. La roadmap prevede assegnamento manuale in dashboard super_admin.

**GDPR base**
- Consenso separato per marketing (informativa link nella pagina).
- **Right to be forgotten**: cancellazione manuale su richiesta scritta a `privacy@omniarealestateecosystem.it` in v1.
- **Retention**: nessun TTL automatico in v1.

---

## 11.9 · Aggiornamento dati (cadenza + procedura)

**Cadenza consigliata: trimestrale (allineata al TEGM)**

Ogni trimestre la **Banca d'Italia** pubblica la nuova rilevazione **TEGM** (Q1: gennaio, Q2: aprile, Q3: luglio, Q4: ottobre). In quello stesso momento vanno aggiornati anche:
- **Eurirs**: valore rilevato da Il Sole 24 Ore o Bloomberg (curva 10-30 anni).
- **Euribor 3M**: valore ufficiale Emmi (`https://www.emmi-benchmarks.eu`).
- **Soglie usura**: ricalcolate come `TEGM × 1,25 + 4`.
- **Spread offerte banche**: consultare fogli informativi ufficiali pubblicati sui siti banca (spesso a fine trimestre) o su servizi tipo *Facile.it* / *MutuiOnline*.

**Procedura di aggiornamento** (super_admin / dev)
1. Aprire `/app/backend/apps/immocloud/data/mortgage_data.py`.
2. Aggiornare `EURIRS`, `EURIBOR_3M`, `TEGM`.
3. Aggiornare `BANK_OFFERS` (verificare spread + spese pubblici di ogni banca).
4. Aggiornare `DATA_UPDATED_AT` (formato `YYYY-MM`).
5. Deploy backend (nessun DB migration, tutto in codice).

**Cosa NON è aggiornato automaticamente**
- **Nessun scraping** (D-037 decisione esplicita). Motivo: siti banche instabili + termini d'uso spesso vietano scraping + qualità dati curati batte scraping su volume basso.
- **Nessuna integrazione API** con banche in v1: nessuna banca italiana espone spread mutui via API pubblica.
- Se una banca **cambia condizioni a metà trimestre**, la simulazione può risultare fuori linea di un decimo di punto.

**Cosa succede se i dati sono vecchi**
- Il TAEG mostrato può essere sotto/sopra la realtà attuale.
- Il visitatore va comunque in banca a farsi fare il **preventivo ufficiale**: la simulazione è indicativa (disclaimer presente).
- **Errore massimo tipico**: ±0,20% sul TAEG se il ritardo è > 3 mesi.

---

## 11.10 · Il disclaimer legale (visibile su ogni pagina)

**Testo integrale del disclaimer** (`response.disclaimer`, sempre presente)
> *"Simulazione orientativa basata su dati pubblici e fogli informativi. Non costituisce offerta al pubblico né attività di mediazione creditizia ai sensi dell'art. 128-sexies TUB. Condizioni effettive soggette a valutazione della banca."*

**Perché è obbligatorio** (D-051)
- **Art. 128-sexies TUB** (Testo Unico Bancario): la **mediazione creditizia** (mettere in contatto cliente e banca a fronte di compenso) è **attività riservata** con requisiti abilitativi (iscrizione OAM, capitale sociale minimo, ecc.).
- OMNIA **NON è mediatore creditizio** e **NON percepisce compensi** dalle banche per lead qualificati. Il comparatore è un **tool informativo** — la trattativa avviene direttamente tra cliente e banca.
- Il disclaimer **evita** che il tool possa essere qualificato come attività di mediazione.

**Cosa NON dice il disclaimer (e va detto a voce dall'agente)**
- I dati sono aggiornati **manualmente ogni trimestre**: possono essere leggermente sfasati rispetto al preventivo bancario del giorno.
- Il comparatore **non conosce la tua storia creditizia** (CRIF/EURISC): la banca può alzare lo spread se la scoring è bassa.
- Non c'è **valutazione dell'immobile** (perizia): la banca potrebbe **erogare meno** se la perizia è sotto il prezzo di acquisto.

**Chi vede il disclaimer**
- Ogni response API contiene il campo `disclaimer`.
- La UI (B2C + B2B + widget) deve mostrarlo in fondo alla lista offerte in font leggibile (non nascosto).
- Non è opzionale né rimovibile lato client.

---

## 11.11 · Errori comuni (raccolta)

| Problema | Dove | Cosa fare |
|----------|------|-----------|
| *"Anticipo insufficiente, minimo X €"* | Eligibility check | Aumenta l'anticipo o attiva Consap under-36 se hai i requisiti |
| *"Nessuna offerta disponibile"* | Filtro rate_type + LTV | Prova con `rate_type: entrambi` invece che solo fisso o solo variabile |
| Il TAEG di ING/Webank è più basso ma nessun sportello fisico | Confronto | Sono banche digitali. Se preferisci sportello vicino, filtra manualmente le banche tradizionali |
| *"Rata > 35% del reddito"* (badge ambra) | Sostenibilità | Aumenta la durata (rata più bassa) o l'anticipo (mutuo più piccolo) |
| Non vedo Consap under-36 | Filtri | Verifica di aver spuntato **entrambe** *"Prima casa"* + *"Under 36"* |
| La simulazione dice X€ ma la banca mi ha proposto X+30€ | Colloquio bancario | Normale. Il tuo profilo creditizio o la perizia possono aver alzato lo spread. La simulazione era orientativa (disclaimer) |
| Ho lasciato un lead ma nessuno mi ha chiamato | Lead capture v1 | I lead sono al momento un repository, nessun funnel commerciale automatico. Roadmap: assegnamento manuale + nurturing |
| L'imposta sostitutiva è 0,25% o 2%? | Costi upfront | 0,25% prima casa, 2% seconda casa. Il comparatore usa il valore corretto in base al flag `first_home` |
| Voglio simulare tasso misto (10 anni fisso + 20 variabile) | Non supportato v1 | Fai due simulazioni separate e sommale manualmente |
| Vorrei un mutuo a 40 anni | Non supportato v1 | Whitelist durate 10/15/20/25/30. Le banche italiane raramente offrono oltre 30 anni |

---

## Voci correlate (fuori capitolo)

- **Cap. 3 · Immobili** — collega prezzo immobile alla rata simulata (utile per titolo annuncio: *"rata da 890€/mese con 20% anticipo"*).
- **Cap. 8 · Sito web agenzia** — il comparatore può essere embeddato come sezione della vetrina sito agenzia (widget partner).
- **Cap. 10 · HAL Agent CRM** — puoi chiedere a HAL *"quanto verrebbe la rata di RIF-124 a 25 anni?"* → risponde usando i dati Cap. 3 + comparatore.
- **HAL Legal** (in arrivo) — per domande legali sul contratto mutuo (surroga, rinegoziazione, decadenza Consap): NON attivo in v1.

---

**Versione**: v1.0.1 · Feb 2026 (TASK H-bis · allineamento D-051 al codice: 8 banche / 9 Consap / ING interamente fuori Consap)

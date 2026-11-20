# RICONCILIAZIONE — Primo E2E gestionale vs E2E INTEGRALE PRE-GTM (20 novembre 2026)

**Modalità:** READ-ONLY · nessuna implementazione · nessun nuovo audit mutativo  
**Data rapporto:** 20 novembre 2026 (Europe/Rome)  
**Domanda guida:** il gestionale è davvero peggiorato, oppure oggi abbiamo verificato di più, con criteri più severi e copertura diversa?

---

## 1. Sintesi esecutiva

### Cosa è davvero cambiato (dimostrabile)

1. **Il “primo E2E gestionale” dogfood non è un mistero:** è la campagna **`D175-E2E-DEEP`** del **20 novembre 2026 ~15:55–16:05 Europe/Rome**, SHA **`9aec192`**, DB **`omnia_df_clean_c4` in kind CLEAN**, sessione C7 `0d961b03-7393-45e0-a483-3a2bae7928ef`. Fonte primaria: `/opt/cursor/artifacts/D175-E2E-DEEP-FINAL-REPORT.md` + `D175-E2E-DEEP-RESULTS.json` + `D175-E2E-DEEP-SUPPLEMENT.json`.
2. **L’E2E INTEGRALE PRE-GTM** (sera, ~20:50) gira su SHA **`759d628`** (dopo merge **PR #240** Deal/chat/docs) sullo **stesso DB name** `omnia_df_clean_c4`, ma dichiarato **CONTINUITY** (non drop fresco). Fonte: `E2E-INTEGRALE-00-PREFLIGHT.md`, `E2E-INTEGRALE-ENV.json`, `E2E-INTEGRALE-PREVIOUS-RECOVERY.json`.
3. **Zero card SUPERATO nel dossier odierno non significa “zero funzioni lavorano”.** Il dossier INTEGRALE applica criteri di scheda più ampi (Livello 2–3: UI click, provider reali, volumi, percorsi alternativi). Molte funzioni con nucleo API già PASS nel DEEP restano **PARZIALE** perché manca collaudo UI (A-004: 0 click) o altri gap di copertura.
4. **Tra i due run il codice non è “peggiorato” sul nucleo CRM/MLS:** PR #240 **aggiunge** Deal/chat/document-requests/watermark (aree che nel DEEP erano **FAIL/assenti**). Il recupero esplicito lo conferma: `E2E-INTEGRALE-PREVIOUS-RECOVERY.json`.
5. **A-007 (lista immobili 500 `created_at`) non è una regressione dimostrata del DEEP→INTEGRALE sul codice tip:** nel DEEP `properties_list` era **PASS** con `total=1` (record appena creati, completi). L’INTEGRALE fallisce con `page_size≥3` quando la pagina include **record legacy incompleti** accumulati/visibili in CONTINUITY. È un **difetto latente di prodotto** esposto da dati/volumi diversi + probe più aggressivo — non una prova che “il DEEP mentiva sul PASS” sul percorso che aveva eseguito.

### Cosa non è dimostrabile

- Che esista un E2E gestionale dogfood **precedente al 20/11 pomeriggio** con verbali formali: **EVIDENZA STORICA NON REPERITA** (oltre stress/QC settembre su `demo-agency` e smoke R04 del 18/11, che **non** sono quel primo E2E dogfood multi-filiale).
- Una percentuale di “funzionamento” del gestionale: **non calcolata** (vietato inventarla contando le PARZIALI).
- Regressioni commerciali Stripe/H4: già **BLOCKED** nel DEEP; restano BLOCKED nell’INTEGRALE (H4 non aperto in entrambi).

### Verdetto in una frase

**Il peggioramento apparente (49 card senza SUPERATO) è spiegato soprattutto da criteri più severi, perimetro più ampio e DB CONTINUITY più “sporco”; non da un crollo generale del nucleo gestionale rispetto al DEEP. Regressioni confermate sul nucleo CRM/MLS tra DEEP e INTEGRALE: nessuna con prove equivalenti. Unico deterioramento operativo rilevante emerso sul percorso “elenco immobili” è A-007, classificato come problema latente/copertura insufficiente nel primo test, non come regressione tip `9aec192→759d628` dimostrata.**

---

## 2. Inventario evidenze originali del primo E2E

### 2.1 Cluster primario (primo E2E gestionale dogfood)

| Percorso | Data (mtime / dichiarazione) | Natura | Funzionalità verificate | Esito dichiarato |
|----------|------------------------------|--------|-------------------------|------------------|
| `/opt/cursor/artifacts/D175-E2E-DEEP-FINAL-REPORT.md` | 20/11/2026 ~16:05 Rome | Rapporto finale unico | Matrice A–H (identità, CRM, MLS, Deal, wallet, storage, H4, security, UI shell) | Verdetto **OPERATIVAMENTE PARZIALE** |
| `/opt/cursor/artifacts/D175-E2E-DEEP-RESULTS.json` | 20/11 14:59 UTC | 84 probe harness | Login, members, properties CRUD/list, clients, MLS routes, Deal absent, wallet, H4, security, UI HTTP | Harness grezzo: **PASS 68 / FAIL 15 / PARTIAL 1** |
| `/opt/cursor/artifacts/D175-E2E-DEEP-SUPPLEMENT.json` | 20/11 15:01 UTC | Secondo passaggio | Clients/requests/matching, MLS join/offer, H4 gate 503, note fixture | CRM/MLS/H4 gate recuperati a **PASS** ove eseguiti |
| `/opt/cursor/artifacts/D175-E2E-DEEP-HARNESS.log` | 20/11 14:59 | Log tecnico | Esecuzione harness | Supporto |
| `/opt/cursor/artifacts/D175-E2E-DEEP-PREFLIGHT.log` | 20/11 14:55 | Preflight | C1/stack | OK |
| `/opt/cursor/artifacts/D175-E2E-DEEP-SESSION-*.json` + `SESSION-ID.txt` | 14:56–15:01 | Sessione C7 | Open/bind/close/verify | Sessione `0d961b03-…` |
| `/opt/cursor/artifacts/d175_e2e_deep_harness.py` | 14:59 | Script (solo artifacts) | Harness | Non in git |
| `/agent/repos/omnia2/dogfood/sessions/events/0d961b03-….jsonl` | 15:01 | Journal (gitignored) | Eventi sessione | 196 eventi |
| Checkpoint unsigned `dogfood/sessions/unsigned_checkpoints/ffd1deb2-….json` | 15:01 | Checkpoint | Tip hash | **PENDING_SIGNATURE** |

**Git / ambiente DEEP (dichiarati nel FINAL-REPORT):**

- Commit: `9aec1921e92207db078f710b2c3fdc7586b061dd` (`origin/main`, pre-PR#240)
- Kind: **CLEAN** / workcopy `omnia_df_clean_c4`
- Mongo: `127.0.0.1:27018` · API `:43121` · preview `:43123` · `OMNIA_ENV=dogfood`
- H4 sealed: **ASSENTE** · Stripe: `test` (nessun LIVE)
- Account (post rewrite email): `giulia…ma`, `luca…sede`, `sara…nord`, `paolo…sud` `@dogfood-c4.example`

**Prove concrete di PASS sul nucleo (post-supplement, non solo HTTP 200 isolati):**  
login multi-ruolo → create property → status active → clients → requests → matching score 100 → fascicolo → MLS join → partner/offer accept → withdraw/reopen → cross-org deny → H4 `503 h4_not_ready` → logout. Fonte: sezioni 3 e 6 di `D175-E2E-DEEP-FINAL-REPORT.md`.

**Fixture operative sul solo CLEAN (dichiarate, non scorciatoie H4):** rewrite email `.test`→`.example`; `activation_status` org → `active`; allineo `users.role` ↔ membership. Senza di esse il DEEP documenta CRM/inviti/MLS bloccati.

### 2.2 Antecedenti correlati — NON equivalenti al primo E2E dogfood

| Percorso | Natura | Nota |
|----------|--------|------|
| `memory/GESTIONALE_STRESS_REPORT.md` (2026-09-17) | Stress su `demo-agency-001` | Non journey dogfood multi-filiale |
| `memory/GESTIONALE_TOOLS_QC_REPORT.md` (2026-09-18) | QC tool/API | STALE; non dogfood C4 |
| `_export_audits/R04-E2E-UI-SMOKE-REPORT.md` + `r04-*.png` (18/11) | Smoke UI demo | Esplicitamente ≠ dogfood E2E |
| `D175-C4-*` (19/11) | Seed/verify T1–T13 | Struttura; non journey prodotto |
| `DOGFOOD-READINESS-*`, audit B04/STEP2* | Readiness/design | Censimento ≠ E2E |
| Smokes PR#240 / FIX789 (pomeriggio–sera 20/11) | Remediazione post-DEEP | Non “primo” E2E |

### 2.3 EVIDENZA STORICA NON REPERITA

- Verbali formali “primo E2E gestionale” con altro nome/data precedenti al DEEP.
- Screenshot / computer-use del D175-E2E-DEEP.
- Voce dedicata in `memory/CHANGELOG.md` / `DECISIONS.md` / `HANDOFF_*` sul run `0d961b03`.
- Checkpoint firmato (resta PENDING).
- Harness versionato in git.
- Prompt storico etichettato “primo E2E gestionale” separato dal mandato DEEP.
- Sessione CONTINUITY E2E **prima** dell’INTEGRALE (solo seed `omnia_df_cont_c4` strutturale).

**Regola rispettata:** non si attribuisce PASS a funzioni solo perché citate in audit architetturali.

---

## 3. Tabella comparativa dei due contesti

| Elemento | Primo E2E (`D175-E2E-DEEP`) | E2E 20 novembre sera (INTEGRALE) |
|----------|----------------------------|----------------------------------|
| Commit / branch | `9aec192` · `origin/main` (detached) | `759d628` · `main` (PR#240 in ancestry via `f0d4b26`) |
| Ambiente | Dogfood API `:43121` / preview `:43123` | Stesso stack dichiarato |
| Database (nome) | `omnia_df_clean_c4` @ `27018` | `omnia_df_clean_c4` @ `27018` |
| Tipo sessione | **CLEAN** (kind dichiarato) | **CONTINUITY** (stesso DB name, non drop fresco) |
| Sessione Dogfood C7 | `0d961b03-7393-45e0-a483-3a2bae7928ef` | NON VERIFICATO come nuova sessione C7 dedicata; riuso CONTINUITY |
| Account | Stesso set C4 email `.example` | Stesso set; meta mostra drift (`giulia` role=agent; `paolo` agency_id=null) — `E2E-INTEGRALE-ACCOUNTS-META.json` |
| Org / filiali | Sede / Nord / Sud C4 | Stesse org id di base; + side-effect gruppo J2 (A-008) |
| Fixture | Email/activation/role allineate **durante** DEEP | Riuso post-DEEP + accumulo collaudi; MA/CC ancora `pre_activation` |
| Procedure | Harness 84 probe + supplement mirato CRM/MLS | Journey 1–13 + inventory OpenAPI/UI + developer/provider matrix |
| Criteri di PASS | Operativo: flusso API multi-ruolo su agenzia simulata; Deal assente = FAIL gap; H4 chiuso = gate PASS / acquisto BLOCKED; UI = shell HTTP PARTIAL | Schede Founder/Tecnico: **SUPERATO** richiede prova più completa; assenza UI click → quasi tutto **PARZIALE**; 0 SUPERATO |
| Copertura UI | Shell HTTP 200; computer-use non eseguito | Inventario 1411 elementi; **0 click** (A-004) |
| Perimetro prodotto | Gestionale CRM+MLS + gap Deal + billing gates | Ecosystem intero (cloud, tools, API v1, GTM) |

**Non equivalenza dichiarata:** stesso *nome* DB ≠ stesso *stato* dati; CLEAN ≠ CONTINUITY; `9aec192` ≠ `759d628` (Deal/chat entrati in main).

---

## 4. Matrice funzionale (classificazioni A–G)

Legenda: **A** confermata funzionante · **B** regressione confermata · **C** problema già presente · **D** copertura insufficiente (primo test) · **E** parziale per criteri più ampi · **F** non confrontabile · **G** evidenze contraddittorie.

Solo perimetro confrontabile col primo test gestionale (+ note dove INTEGRALE ha esteso).

| Funzionalità | Esito DEEP | Evidenza DEEP | Esito dossier attuale | Evidenza attuale | Diff. contesto | Classificazione | Confidenza |
|--------------|------------|---------------|-----------------------|------------------|----------------|-----------------|------------|
| Login agenzia (sede/nord/collab) | PASS | RESULTS AUTH login_* 200; FINAL §A | ACC-01 PARZIALE | J1 smoke | Criterio UI | **E** (+ nucleo **A** a Livello 1) | Alta |
| Logout | PASS | FINAL §H | ACC-02 PARZIALE | PERF/J11-13 | Criterio UI | **E** | Alta |
| Registrazione privato ImmobilCloud | Non nel perimetro DEEP gestionale | — | ACC-03 PARZIALE | J6 | Fuori primo test | **D** | Alta |
| Recupero password | PASS messaggio generico | FINAL §H forgot-password 200 | ACC-04 NON ESEGUITO | inventario | Criterio E2E email diverso | **E** / parziale overlap | Media |
| Inviti collaboratori | PASS dopo allineo role | SUPPLEMENT invites_after_role_align; FINAL §A | ACC-05 PARZIALE | J13; A-003 | Fixture CONTINUITY | **E** + rischio **F** su agent | Media |
| Ruoli / permessi / isolamento | PASS cross-org 404 | FINAL §A/H; RESULTS property_get_cross_org | ACC-06 / SEC-01 PARZIALE | J13 | Criterio matrice UI | **E** | Alta |
| Org / gruppo / filiali | Struttura C4 PASS | FINAL §E strutturale | ORG-01/02 PARZIALE | J2 | J2 crea gruppo → A-008 | **E** | Media |
| Main Admin / wallet context | BLOCKED / FAIL context | FINAL §E; RESULTS wallet_get_main_admin 400 | ORG-03 BLOCCATO; BILL-03 BLOCCATO | J12; A-003 | Equivalente | **C** (già presente) | Alta |
| Dashboard KPIs | NON collaudata come scenario dedicato DEEP | — | CRM-01 PARZIALE | PERF | Fuori/parziale DEEP | **D** | Media |
| Clienti CRUD | PASS (supplement) | SUPPLEMENT crm_clients_create | CRM-02 PARZIALE | J4 | Criterio UI/import | **E** | Alta |
| Immobili create/get/status | PASS (dopo status literal corretto) | FINAL §B; SUPPLEMENT withdraw/reopen | CRM-03 PARZIALE | J3 | Criterio foto/UI | **E** | Alta |
| **Elenco immobili** | PASS `total=1` | RESULTS `properties_list` 200 | CRM-04 **FALLITO** (A-007) | A007-ps*; RELIABILITY | CONTINUITY + page_size≥3 + legacy | **C** + **D** (latente; non **B** tip) | Media-Alta |
| Richieste / matching | PASS score 100 | SUPPLEMENT crm_matching_score100 | CRM-05 PARZIALE | J4/J5 | Criterio UI/volumi | **E** | Alta |
| Agenda / attività | NOT VERIFIED | FINAL §B | CRM-06 PARZIALE | J4/J13 | DEEP non collaudava | **D** → oggi parziale | Media |
| Multiposting | Non nel DEEP | — | CRM-07 NON VERIFICATO | J11 | Fuori | **D** | Alta |
| ImmobilCloud ricerca/preferiti/contact | Non nel DEEP gestionale core | — | CLD-* PARZIALE | J6/J6X | Fuori primo test | **D** | Alta |
| MLS collaborazione / offer | PASS | FINAL §C; SUPPLEMENT mls_* | MLS-01 PARZIALE | J7-10 | Criterio UI; modello collab post-#240 | **E** (nucleo) / **F** (modello API evoluto) | Media |
| Visite / feedback | NOT VERIFIED | FINAL | MLS-02 PARZIALE | J8 | DEEP non collaudava; #240 abilita | **D** | Alta |
| Deal | **FAIL** (API assente) | RESULTS deal_* 404 | DEA-01 PARZIALE | J9 | **Miglioramento prodotto** via #240 | non B; progresso + **E** | Alta |
| Chat contestuale | **FAIL** | FINAL §D | DOC-01 PARZIALE | J10 | Introdotto #240 | progresso + **E** | Alta |
| Documenti + watermark | Assente / non collaudato | PREVIOUS-RECOVERY “gaps now in main” | DOC-02 PARZIALE; A-005 | J8 | Introdotto #240 | **D** nel DEEP → oggi **E** | Alta |
| H4 / acquisti | Gate PASS 503; acquisto BLOCKED | FINAL §G; SUPPLEMENT h4_* | BILL-02 / PROV-01 BLOCCATO; A-002 | J12 | Equivalente (H4 chiuso) | **C** | Alta |
| UI click | PARTIAL shell HTTP | FINAL UI | UI-01 NON ESEGUITO; A-004 | UI-COLLAUDO | Stesso limite piattaforma | **C** / **E** | Alta |
| API developer / sandbox | Non nel DEEP | — | DEV-02 BLOCCATO; DEV-03 FALLITO; A-006 | J-DEVELOPER | Fuori primo test | **D** | Alta |

### Perché zero SUPERATO non contraddice i PASS del DEEP

Nel DEEP un **PASS** = operazione API (e flusso multi-step dichiarato) riuscita sul percorso collaudato.  
Nel dossier INTEGRALE una scheda **SUPERATO** implica, nella pratica adottata, chiusura anche di lacune tipiche di Livello 2–3 (soprattutto UI). Con A-004 attivo, le schede restano **PARZIALE** anche dove il Livello 1 è verde. **Non è prova di regressione.**

---

## 5. Analisi individuale A-001 … A-008

| ID | Esisteva nel DEEP? | Fuori perimetro DEEP? | Regressione successiva? | Fixture/ambiente? | Difetto prodotto? | Limite test? | Causa attribuibile con prove? |
|----|--------------------|------------------------|-------------------------|-------------------|-------------------|--------------|-------------------------------|
| **A-001** Deal post-revoca 404 opaco | Deal **assente** nel DEEP → non osservabile | Sì (gap prodotto) | No: emerge solo post-#240 collaudo J9 | No | Sì (tassonomia errori) | Parziale | Sì: J9-07; non confrontabile col DEEP |
| **A-002** Acquisti / H4 | Sì: BLOCKED / gate 503 | No | **No** — già presente | CC `pre_activation` già DEEP | Gate sealed + CC | Sì (H4 non aperto) | Sì: FINAL §G + J12 |
| **A-003** Fixture MA/Agent | Sì: seed role drift, MA no context; DEEP aveva allineato role per lavorare | No | **Parziale drift CONTINUITY**: meta INTEGRALE mostra ancora `giulia` role=agent; `paolo` agency_id=null; login agent contestato vs smoke | **Sì** | Qualità seed Dogfood | Sì | Sì: FINAL anomalie alta #5–7 + ACCOUNTS-META |
| **A-004** Zero UI click | Sì (shell only) | No | No | No | No | **Sì** (spend limit) | Sì: entrambi i report |
| **A-005** Watermark qualità | Watermark non in DEEP | Sì | No | No | Residuo qualità | Sì | Solo post-#240 |
| **A-006** agency_inactive API key | Non collaudato nel DEEP | **Sì** | Non dimostrabile come regressione DEEP | Possibile coerenza `is_active` vs `activation_status` | **Sì** (gateway) | Scoperta copertura | Sì sull’INTEGRALE; **D** vs DEEP |
| **A-007** lista `created_at` | Lista PASS con `total=1` | Probe page_size/legacy **non** eseguito | **Non confermata come regressione tip** `9aec192→759d628` (PR#240 è Deal/docs). Condizione di guasto = legacy in pagina | **Sì** (CONTINUITY + volumi) | **Sì** (KeyError serializer) | DEEP non stressava legacy | **C+D**: latente; esposto ora |
| **A-008** role → group_admin | Non nel DEEP (nessun create group collaudato così) | Sì come side-effect J2 | Side-effect del collaudo INTEGRALE, non regressione prodotto preesistente dimostrata | **Sì** | Possibile side-effect API groups | Artefatto di test | Sì: A-ROLE / J2 |

---

## 6. Regressioni effettivamente confermate

**Nessuna regressione confermata** sul nucleo gestionale CRM/MLS tra DEEP (`9aec192`, CLEAN) e INTEGRALE (`759d628`, CONTINUITY) con condizioni sufficientemente equivalenti.

| Candidato | Perché NON è regressione confermata |
|-----------|-------------------------------------|
| CRM-04 / A-007 | DEEP non ha fallito sullo stesso caso (lista piccola, record completi). Manca prova che lo stesso dataset legacy fallisse già a `9aec192` *oppure* che il merge #240 abbia introdotto il KeyError. |
| Deal errori post-revoca | Deal non esisteva nel DEEP. |
| DEV-02 / A-006 | Fuori perimetro DEEP. |
| Zero SUPERATO | Cambio di **scala di giudizio**, non di esito API. |

Se in futuro si ripete **solo** `GET /properties` con gli stessi legacy su tip `9aec192` in sola lettura: potrebbe consolidare A-007 come **C** puro (già presente nel tip DEEP). **Non eseguito in questo mandato** (richiederebbe ripristino tip/runtime; vietato mutare / non autorizzato re-test invasivo). Stato: **NON ESEGUITO qui**.

---

## 7. Problemi già presenti (nel o prima del DEEP)

1. **H4 sealed assente** → nessun acquisto TEST (A-002).  
2. **CC `pre_activation`** → wallet MA non operable.  
3. **Deal/chat/mini-dossier assenti** pre-#240 (gap prodotto, FAIL DEEP).  
4. **Seed C4 incoerente** (email `.test`, activation pending, `users.role` vs membership) — A-003 radice.  
5. **UI non collaudata a click** — A-004.  
6. **A-007 latente** (serializer fragile su campi mancanti) — esposto dopo, ma logica di guasto tipica di difetto già nel codice lista.

---

## 8. Verifiche mancanti nel primo test (DEEP)

- ImmobilCloud B2C completo (ricerca/preferiti/contact/private).  
- Journey visite/feedback dedicati.  
- Deal/chat/docs (allora assenti).  
- Developer gateway `/api/v1` e sandbox.  
- Provider matrix (Resend send, fal generate, APE E2E, multiposting sync).  
- Lista immobili con `page_size` elevati e record legacy incompleti.  
- UI browser click / screenshot.  
- Stripe checkout+webhook con H4.  
- Lifecycle sospensione/deroga/cease.  
- Matrice ruoli a schermo; Main Admin operable reale.

---

## 9. Funzionalità oggi PARZIALI soprattutto per copertura più ampia (classe E)

Esempi ad alta confidenza (nucleo DEEP già PASS / flusso completo dichiarato):

- ACC-01/02 login/logout  
- CRM-02/03/05 clienti, create immobile, matching  
- MLS-01 collaborazione/offer (nucleo API)  
- SEC-01 isolamento cross-org  
- Fascicolo come proxy documentale  

Restano PARZIALI nel dossier perché mancano UI e/o percorsi extra — **non** perché il DEEP PASS sia stato smentito sugli stessi endpoint.

---

## 10. Limiti delle conclusioni e prove non reperite

- CONTINUITY ha **mutato** il DB dopo il DEEP (collaudi, gruppo, proprietà aggiuntive): confronto dati non sterile.  
- Criteri SUPERATO vs PASS DEEP **non omogenei**.  
- Modello MLS/collaborazioni post-#240 **non identico** alle route MLS del DEEP → confronto MLS solo a livello “agenzia collabora”, non bit-a-bit.  
- Nessun re-test mutativo autorizzato in questo mandato.  
- Stress/QC settembre e R04 **non** usati come “primo E2E gestionale”.  
- Checkpoint DEEP non firmato.

---

## 11. Valutazione finale sullo stato del gestionale

| Livello | DEEP (pomeriggio) | INTEGRALE (sera) | Lettura |
|---------|-------------------|------------------|---------|
| **1 — Nucleo applicativo** | CRM+MLS multi-filiale **lavorano** dopo fixture | Nucleo ancora osservato funzionante nei journey; **A-007** rompe la lista a certi page size | Non “morto”; lista fragile su legacy |
| **2 — E2E coerente** | Flusso dichiarato completo su CRM/MLS; Deal no; billing no | Deal/docs **entrati**; billing ancora no; fixture MA confuse | Ampiezza ↑; completezza commerciale no |
| **3 — Prontezza commerciale** | Esplicitamente **NO** | Esplicitamente **NO** (GTM) | Allineati |

**Risposta alla domanda del Founder:**  
il gestionale **non risulta, dalle prove, generalmente peggiorato** rispetto al primo E2E dogfood. Il dossier odierno è **più severo, più largo e su dati CONTINUITY**. Il segnale serio **nuovo rispetto alla narrazione “lista OK”** è **A-007**, da trattare come difetto reale da correggere **dopo autorizzazione**, non come prova che il DEEP fosse una frode: il DEEP aveva ragione sul campione che aveva, e torto (per copertura) sul caso legacy.

---

## 12. Risposte esplicite alle 10 domande

1. **Nel primo E2E quali funzioni erano realmente provate?**  
   Identità multi-ruolo, members, inviti (post-fix role), CRM property/client/request/match/fascicolo, MLS join/partner/offer, isolation/security, storage usage, gate H4 503, UI shell HTTP. Deal/chat assenti = FAIL gap. Wallet MA / Stripe E2E = BLOCKED. Visite dedicate = NOT VERIFIED.

2. **Quali erano state effettivamente superate?**  
   Il DEEP non usa “SUPERATO”; usa PASS operativo. Superati (PASS post-supplement) i flussi CRM+MLS elencati in FINAL §6. Non superati: Deal/chat, acquisti, UI click, lifecycle paid.

3. **Quali funzionano ancora oggi?**  
   Sulle prove INTEGRALE: nuclei login, CRM create/match, MLS/deal/docs (deal ora presente), isolation — con schede PARZIALI. Lista immobili: **non** affidabile (A-007). Billing acquisto: ancora no.

4. **Esistono regressioni confermate?**  
   **No**, con lo standard del mandato.

5. **Se sì, quali e con quali prove?**  
   Nessuna. Candidato A-007: **non** elevato a B.

6. **Quali problemi già presenti o mai verificati?**  
   H4/CC, seed roles, UI, Deal pre-#240, A-007 latente, developer API, cloud/tools fuori perimetro DEEP.

7. **Quanto del peggioramento apparente dipende da criteri più ampi?**  
   **La maggior parte** del “0 SUPERATO” e di molte PARZIALI su funzioni già PASS DEEP.

8. **Quanto da ambiente/DB/account/fixture?**  
   **Rilevante** per A-007 (legacy/CONTINUITY), A-003/A-008 (fixture drift), e per non-equivalenza CLEAN vs CONTINUITY.

9. **Meno funzionante o lacune di copertura?**  
   **Soprattutto lacune di copertura + criteri più severi + un difetto lista esposto dai dati.** Non un crollo generale del gestionale.

10. **Problemi reali da affrontare per primi (solo dopo autorizzazione distinta)?**  
    Ordine suggerito dalle prove (non è mandato di fix): **A-007** (lista immobili) → **A-006** (se si vende API) → **A-002/H4 TEST** (se si vende billing) → **A-003** fixture → **A-004** UI reale → **A-001** errori Deal.  
    **Nessuna implementazione avviata.**

---

## 13. Riferimenti prova (indice rapido)

- Primo E2E: `/opt/cursor/artifacts/D175-E2E-DEEP-FINAL-REPORT.md`  
- Probe grezzi: `/opt/cursor/artifacts/D175-E2E-DEEP-RESULTS.json` (`properties_list` PASS total=1)  
- Supplement: `/opt/cursor/artifacts/D175-E2E-DEEP-SUPPLEMENT.json`  
- Ponte storico: `/opt/cursor/artifacts/E2E-INTEGRALE-PREVIOUS-RECOVERY.json`  
- Preflight INTEGRALE: `/opt/cursor/artifacts/E2E-INTEGRALE-00-PREFLIGHT.md`  
- Anomalie: `/opt/cursor/artifacts/E2E-INTEGRALE-ANOMALIE.md`  
- Account meta: `/opt/cursor/artifacts/E2E-INTEGRALE-ACCOUNTS-META.json`  
- Dossier Founder (0 SUPERATO): `/opt/cursor/artifacts/E2E-COPERTURA-MATRIX.md`  
- Delta git dichiarata: `9aec192..759d628` include merge PR#240 Deal/chat/docs

---

**STOP.**  
Nessun nuovo ciclo E2E, nessuna correzione, nessuna PR/commit da questo mandato.  
Rapporto consegnato al Founder per valutazione.  
**Questo documento NON costituisce autorizzazione all’implementazione.**

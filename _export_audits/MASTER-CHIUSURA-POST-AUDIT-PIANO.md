# OMNIA — Piano di chiusura master post-audit

**Data originale:** 17 novembre 2026 · ~20:20 Europe/Rome  
**Aggiornamento verifica:** 18 novembre 2026 · ~13:05 Europe/Rome  
**Baseline codice (verificata):** `main` @ `11f29621dd2ddef9e4a61fa3ece569a65f94eaf9` (merge PR #222 H3)  
**Baseline intermedia 18/11:** `6a12932` (#220) · `0919cda` (#221) — superate dal tip  
**Baseline storica 17/11:** `c3baebc` (PR #216) — superata  
**Rapporto chiusura A+B:** `_export_audits/MASTER-RAPPORTO-FINALE-CHIUSURA-STRATI-A-B.md`  
**Evidenza verifica Git/PR:** `_export_audits/VERIFICA-POST-MERGE-217-220-2026-11-18.md`  
**Natura:** piano di riconciliazione e chiusura. **Non** è autorizzazione a implementare.  
**Destinatari:** Founder · ChatGPT (analisi/programma) · Cursor (esecuzione solo con mandato esplicito)

---

## 0. Cosa significa «chiudere il master»

Il master post-audit **non** è «OMNIA prodotto completo in produzione».  
È la chiusura verificabile del percorso:

**FASE 1 (verifica statica)** → **FASE 2 (design B01–B04)** → **slice implementative autorizzate e mergiate**.

Si lavorano **tre strati distinti**. Confonderli produce falsi «chiuso».

| Strato | Domanda | Può chiudersi ora? |
|---|---|---|
| **A — Audit + design** | Ogni audit/decisione ha stato finale esplicito? | **Quasi**: design B01–B04 chiusi; audit FASE1 chiusi come verifica statica |
| **B — Implementazione autorizzata** | Slice1 + B04-I/II + H1 + H2 residuali su `main`, CI verde, residui classificati? | **Sì, chiudibile** dopo i gate MC di questo piano |
| **C — Readiness commerciale / resto risanamento** | B04-III…VII, impl B01–B03, B05–B07, migrazione, Stripe live, prod? | **No** — **fuori** dal master di chiusura attuale; restano fase successiva |

**Regola:** non tutto ciò che emerse negli audit va implementato prima della chiusura master.  
Deve avere uno di: *implementato e verificato* · *residuo accettato esplicitamente* · *fase successiva documentata* · *fuori perimetro*.

---

## 1. Fonti usate (non memoria di chat)

| Fonte | Ruolo | Freschezza |
|---|---|---|
| `CHIUSURA-VERIFICA-STATICA-BLOCCHI-0-7.md` | Chiusura FASE 1 | 16 nov |
| `FASE-2-BACKLOG-PIANIFICAZIONE-RISANAMENTO.md` | Backlog B01–B07 | 16 nov |
| `B01…B03-*-CHIUSURA-DEFINITIVA-DESIGN.md` | Design chiusi | 16–17 nov |
| `B04-ANO-008-DESIGN-BILLING.md` + `B04-DES-REGISTRO.md` | Design B04 DES-01…10 | 17 nov |
| `B04-H1-H2-IMPLEMENTATION-REPORT.md` | H1 + H2 ruoli exact | 17 nov · PR #212 |
| `B04-H2-MAIN-ADMIN-*` | Design/D01–D12/impl/handoff residuale | 17 nov · PR #216 |
| `B04-OPEN-FOLLOWUPS.md` | Repricing (non design) | 17 nov |
| `memory/NEXT_SESSION.md` | Stato operativo slice | **aggiornato 17 nov ~20:20** (post-#216) |
| `OMNIA-HANDOFF-PER-CHATGPT.md` | Handoff storico ChatGPT | **STALE (14 nov)** — non usare come SoT corrente |
| `MASTER-CHIUSURA-HANDOFF-CHATGPT.md` | Pacchetto revisione ChatGPT del piano | 17 nov |

---

## 2. Consolidamento verificato oggi (M-01 / M-02)

| Check | Esito | Evidenza |
|---|---|---|
| M-01 CI su `99a967e` | **VERDE** | 2× `Backend billing / B04 unit` SUCCESS (PR #216) |
| M-01 CI post-merge `main` | **VERDE** | Actions run su `c3baebc` → success |
| M-02 codice su `main` | **ALLINEATO** | `99a967e` antenato di `origin/main`; presenti `main_admin_service.py`, TTL 48h, `is_active is not True`, `cabina_notify_failed`, resolve CC esplicito |
| PR #216 | **MERGED** | `mergedAt` 17 nov 19:07 UTC · merge `c3baebc` |
| PR #212 H1/H2 exact | **MERGED** | `0911510` |
| PR #210 / #211 B04-I/II | **MERGED** | confermati via `gh` |
| Slice 1 | **MERGED** | PR #208 (per `NEXT_SESSION.md`) |

---

## 3. Legenda stati (obbligatoria)

| Stato | Significato |
|---|---|
| `AUDIT_CHIUSO` | Verifica statica acquisita; non da ripetere |
| `DESIGN_CHIUSO` | Decisioni Founder approvate; codice non necessariamente presente |
| `IMPL_MERGIATO` | Codice su `main` + test/CI del perimetro |
| `RESIDUO_ACCETTABILE` | Gap noto, non bloccante per lo strato B, richiede accettazione Founder |
| `FASE_SUCCESSIVA` | Nel backlog, **fuori** chiusura master strato B |
| `BLOCCANTE_APERTO` | Impedisce dichiarare chiuso lo strato indicato |
| `FUORI_MASTER` | Escluso dal perimetro di questa chiusura |
| `DOC_STALE` | Documento da aggiornare (non blocco prodotto) |

**Priorità:** `P0` bloccante chiusura strato · `P1` necessaria prima del successivo slice · `P2` consolidamento · `P3` programma lungo

---

## 4. Inventario unico numerato (senza duplicati)

### 4.1 Audit FASE 1 e riconciliazione aree

| ID | Descrizione | Stato attuale | Evidenza richiesta | Dipendenze | Priorità | Criterio oggettivo di chiusura |
|---|---|---|---|---|---|---|
| **MC-001** | Chiusura verifica statica Blocchi 0–7 | `AUDIT_CHIUSO` | `CHIUSURA-VERIFICA-STATICA-BLOCCHI-0-7.md` | — | P0 | Founder conferma: FASE1 non si riapre; residuali mappati in MC-* |
| **MC-002** | Pacchetto audit 01–16 (indice) | `AUDIT_CHIUSO` | `00-INDICE-AUDIT.md` + report singoli | MC-001 | P0 | Ogni file ha riga «stato finale» in questo piano (§5) |
| **MC-003** | Area Sicurezza/RBAC (B11/B02/RBAC audit) | `DESIGN_CHIUSO` + impl parziale | B02 chiusura + codice authz esistente + H1/H2 | MC-001 | P1 | Matrice decisione→codice per B02-DEC; gap residui classificati |
| **MC-004** | Area Identità/Membership (B1/B15/B01/B03) | `DESIGN_CHIUSO` · **impl non master-B** | B01/B03 chiusura design; Slice1 parziale | MC-001 | P1 | Design chiuso OK per strato A; impl → `FASE_SUCCESSIVA` esplicita |
| **MC-005** | Area Billing/Stripe (B16/B04) | `DESIGN_CHIUSO` + `IMPL_MERGIATO` parziale | DES-01…10; PR #208/#210/#211/#212/#216 | MC-004 (modello CC) | P0 | Strato B: slice autorizzate mergiate; resto III…VII in MC-030+ |
| **MC-006** | Area Wallet/crediti | `IMPL_MERGIATO` (B04-II+H1+H2) | report B04-II/H1/H2; test 57+CI | MC-005 | P0 | Wallet CC + FIFO + revoke isolato + Main Admin binding su `main` |
| **MC-007** | Area limiti commerciali aggregati | `DESIGN_CHIUSO` · non impl | DES-05/05b; B04-IV | MC-005 | P1 | Classificato `FASE_SUCCESSIVA` (B04-IV); non bloccante strato B |
| **MC-008** | Area dati/conservazione/cessazione | `DESIGN_CHIUSO` · non impl | DES-07; B16; B06/B07 | — | P2 | `FASE_SUCCESSIVA` / `FUORI_MASTER` per chiusura B |
| **MC-009** | Area operatività CI/test | `IMPL_MERGIATO` (CI billing) | workflow CI; run success su `main` | — | P0 | CI verde sul tip `main` del perimetro B04 |

### 4.2 Design B01–B04 (strato A)

| ID | Descrizione | Stato attuale | Evidenza richiesta | Dipendenze | Priorità | Criterio di chiusura |
|---|---|---|---|---|---|---|
| **MC-010** | B01 design (P.IVA / CC / org) | `DESIGN_CHIUSO` | `B01-…-CHIUSURA-DEFINITIVA` | — | P0 | Nessuna decisione B01 riaperta; impl separata |
| **MC-011** | B02 design (authz/audit) | `DESIGN_CHIUSO` | `B02-…-CHIUSURA-DEFINITIVA` | MC-010 | P0 | Idem |
| **MC-012** | B03 design (sessioni/inviti/email) | `DESIGN_CHIUSO` | `B03-…-CHIUSURA` + DEC email | MC-010/011 | P0 | Idem |
| **MC-013** | B04 design DES-01…10 | `DESIGN_CHIUSO` | `B04-ANO-008` + registro | MC-010–012 | P0 | Registro DES tutti «Approvata» |
| **MC-014** | B04-H2 decisioni D01–D12 | `DESIGN_CHIUSO` + recepite in codice | conformity + service su `main` | MC-013 | P0 | D01–D12 non riaperte; fix post-ChatGPT su `main` |
| **MC-015** | B04-OPEN-01 repricing | `FASE_SUCCESSIVA` | `B04-OPEN-FOLLOWUPS.md` | DES-03 | P3 | Non nel master B; sessione dedicata Founder |

### 4.3 Implementazione autorizzata (strato B)

| ID | Descrizione | Stato attuale | Evidenza richiesta | Dipendenze | Priorità | Criterio di chiusura |
|---|---|---|---|---|---|---|
| **MC-020** | Slice 1 commercial/customer sessions | `IMPL_MERGIATO` | PR #208 + test slice1 | MC-010 | P0 | Su `main`; test regressione verdi |
| **MC-021** | B04-I fondazioni Stripe/CC/stati/catalogo | `IMPL_MERGIATO` | PR #210 | MC-020 | P0 | Su `main`; CI B04 |
| **MC-022** | B04-II wallet/lotti/FIFO/ledger | `IMPL_MERGIATO` | PR #211 | MC-021 | P0 | Su `main`; test ledger |
| **MC-023** | B04-H1 revoke isolation CC | `IMPL_MERGIATO` | PR #212 | MC-022 | P0 | Cross-tenant revoke → 404 no mutation |
| **MC-024** | B04-H2 exact roles (pre-binding) | `IMPL_MERGIATO` (superato da MC-025) | PR #212 | MC-023 | P2 | Storico; autorità ora = Main Admin binding |
| **MC-025** | B04-H2 Main Admin residuale D01–D12 | `IMPL_MERGIATO` | PR #216 @ `99a967e` → `c3baebc` | MC-014, MC-023 | P0 | Binding + transfer 48h + deny-by-default + D07 + fix D10/D08/D02/D04 |
| **MC-026a** | Codice D01–D12 post-fix su `main` | `IMPL_MERGIATO` | PR #216 @ `99a967e` ⊂ `c3baebc`; CI verde; report residuale | MC-025 | P0 | Tip `main` contiene fix D10/D08/D02/D04 |
| **MC-026b** | Accettazione Founder conformità D01–D12 + decisioni 18/11 | **`FIRMATA`** 18/11 `CONFORME CON RISERVE` | checklist + MC-052 | MC-026a, MC-042, MC-054…059 | P0 | Riserve: lockout v2, wallet giorno 8 completo, deroga |
| **MC-027** | Suite test B04 locale + CI | `IMPL_MERGIATO` | CI success tip `main` post-#218 | MC-020–025, MC-028 | P0 | Actions success sul tip |
| **MC-028** | MC-042 wallet deny + fail-open CC | `IMPL_MERGIATO` (pezzo) | PR #218 @ `413d2aa` → `547f67f` | MC-042 v1 storica | P0 | **Non** equivale a MC-042 v2 completo |

### 4.4 Residui B04-H2 / H1 (classificazione)

| ID | Descrizione | Stato attuale | Evidenza richiesta | Dipendenze | Priorità | Criterio di chiusura |
|---|---|---|---|---|---|---|
| **MC-040** | UI Cabina accept transfer | `DECISO` 18/11 · **impl autorizzata** (pulsante Accetta) | D-183 | MC-025 | P0 | FE Accetta in Cabina/notifiche |
| **MC-040** | UI Cabina Accetta transfer | `IMPL_MERGIATO` PR #219 · `4946390` | D-183 | MC-025 | P0 | NotificationBell Accetta |
| **MC-041** | Expiry transfer job automatico | `IMPL_MERGIATO` PR #219 | D-184 | MC-025 | P0 | APScheduler 15m + expire |
| **MC-042** | Cessazione definitiva (v2) | `IMPL_MERGIATO` parziale+#220 · gate login/session + wallet · **GAP** refresh senza gate / no revoke session on cease | `MC-042-DECISIONE-FOUNDER.md` · D-177 | D05, DES-07/08 | P0 | Verifica 18/11 |
| **MC-043** | Nomina MA obbligatoria su CC nuovo + sblocco | `IMPL_MERGIATO` PR #219 | D-185 | D01 | P0 | bind_initial + Attiva gate |
| **MC-054** | Sospensione mancato pagamento giorno 8 (opz. B) | `IMPL_MERGIATO` PR #220 · collab off / MA billing / wallet deny | `MC-054-059-…md` · D-178 | DES-07, MC-032 | P0 | ≠ cessazione |
| **MC-055** | Riattivazione automatica saldo pieno Stripe | `IMPL_MERGIATO` path + **fix saldo** (no reactivate se insoluti residui) | stesso · D-179 | DES-02/09 | P0 | Founder 18/11: «fix» |
| **MC-056** | Deroga eccezionale Super Admin | `IMPL_MERGIATO` PR #220 Ops grant | stesso · D-180 | ≠ D07 | P0 | Audit collection |
| **MC-057** | Durata/scadenza deroga | `IMPL_MERGIATO` job expire | stesso · D-180 | MC-056 | P0 | Sospensione auto a scadenza |
| **MC-058** | Comms automatiche deroga | `IMPL_MERGIATO` email best-effort + reminder 48h | stesso · D-181 | MC-056 | P1 | Template riusa `agency_pending` |
| **MC-059** | Deroghe indipendenti per CC | `IMPL_MERGIATO` | stesso · D-182 | MC-056 | P1 | Isolamento tenant |
| **MC-044** | Gap storico «agency_admin filiale = wallet» pre-binding | **CHIUSO da MC-025** | assert Main Admin | MC-025 | — | Non riaprire: superato dal binding |
| **MC-045** | H3 allocate solo org linkate al CC | `IMPL_MERGIATO` / **CHIUSO** PR #222 · `11f2962` | assert_organization_linked_to_cc | MC-022 | P1 | CI include test + concurrency = miglioramenti separati |
| **MC-046** | H4 top-up/storage = Stripe Customer del CC | `FASE_SUCCESSIVA` | idem | MC-021 | P1 | Idem |
| **MC-047** | Legacy billing / migrazione R-04 / dual-write | `FASE_SUCCESSIVA` | B04 design §legacy; B07 | MC-010, B07 | P1 | Riconciliazione umana; nessuna auto-euristica |

### 4.5 Fasi successive esplicite (non bloccano strato B)

| ID | Descrizione | Stato attuale | Evidenza richiesta | Dipendenze | Priorità | Criterio di chiusura (quando aperte) |
|---|---|---|---|---|---|---|
| **MC-030** | B04-III allowance/cicli | `FASE_SUCCESSIVA` | design §6 | MC-025 | P1 | Slice autorizzata + test + merge |
| **MC-031** | B04-IV limiti aggregati | `FASE_SUCCESSIVA` | DES-05/05b | MC-030 o parallelo controllato | P1 | Hard-block atomico verificato |
| **MC-032** | B04-V stati insoluto/disdetta | `FASE_SUCCESSIVA` | DES-02/06/09 | MC-030 | P1 | Macchina a stati + notifiche |
| **MC-033** | B04-VI entitlements + area amm. | `FASE_SUCCESSIVA` | DES-07/08 | MC-025, MC-032 | P2 | Matrice entitlements |
| **MC-034** | B04-VII riconciliazione/collaudo | `FASE_SUCCESSIVA` | design §6 | MC-030–033 | P1 | Collaudo multi-org documentato |
| **MC-035** | Impl codice B01 (oltre Slice1) | `FASE_SUCCESSIVA` | B01 design | MC-010 | P1 | Criteri B01 §completamento |
| **MC-036** | Impl codice B02 | `FASE_SUCCESSIVA` | B02 design | MC-011, MC-035 | P1 | Capability+audit centrale |
| **MC-037** | Impl codice B03 | `FASE_SUCCESSIVA` | B03 design | MC-012, MC-036 | P1 | Sessioni/inviti/email gate |
| **MC-038** | B05 MLS | `FUORI_MASTER` | FASE2 backlog | B02 | P2 | Fuori chiusura master attuale |
| **MC-039** | B06 documenti collaborativi | `FUORI_MASTER` | FASE2 | B05/B02 | P2 | Fuori |
| **MC-048** | B07 migrazione/integrità dati | `FUORI_MASTER` / `FASE_SUCCESSIVA` | FASE2 B07 | modello definitivo | P0 *(quando aperta)* | Nessuna ricostruzione per supposizione |
| **MC-049** | Stripe live / produzione / deploy | `FUORI_MASTER` | — | autorizzazione separata | P0 | Vietato senza mandato Founder dedicato |

### 4.6 Igiene documentale (chiusura master)

| ID | Descrizione | Stato attuale | Evidenza richiesta | Dipendenze | Priorità | Criterio di chiusura |
|---|---|---|---|---|---|---|
| **MC-050** | Aggiornare `memory/NEXT_SESSION.md` post-#216 | `CHIUSO` | `memory/NEXT_SESSION.md` (17 nov ~20:20+) | MC-025 | P0 | Contiene strati A/B/C, #216, residui, SoT piano |
| **MC-051** | SoT handoff ChatGPT stale | `CHIUSO` (banner STALE + nuovi handoff) | `OMNIA-HANDOFF…` STALE; `MASTER-CHIUSURA-HANDOFF-CHATGPT.md` | — | P0 | ChatGPT non usa handoff 14 nov come verità |
| **MC-052** | Report finale chiusura master strato B | **`CHIUSO`** — Founder ha dichiarato `MASTER STRATO B CHIUSO` 18/11 | report finale | MC-026b, MC-040–043 | P0 | Firmato |
| **MC-053** | Indice audit aggiornato con questo piano | `CHIUSO` su PR #217 | `00-INDICE-AUDIT.md` voci 35+ | — | P1 | Voci piano + handoff + review presenti |

---

## 5. Stato finale per audit storici (MC-002)

Sintesi senza ripetere gli audit:

| Audit / blocco | Stato finale per il master |
|---|---|
| Master architecture + follow-up MLS | `AUDIT_CHIUSO` → gap → FASE2 B05 `FUORI_MASTER` |
| B1 / B14 / B15 account-login-reg | `AUDIT_CHIUSO` → design B03 `DESIGN_CHIUSO` → impl `FASE_SUCCESSIVA` |
| B11 / RBAC / FE permessi | `AUDIT_CHIUSO` → B02 `DESIGN_CHIUSO` → partial code + H2 binding |
| B12 log | `AUDIT_CHIUSO` → B02 audit design; impl centrale `FASE_SUCCESSIVA` |
| Inventario Mongo | `AUDIT_CHIUSO` (fotografia) |
| Register/invite/KYC | `AUDIT_CHIUSO` → B03 |
| B16 billing pacchetti | `AUDIT_CHIUSO` → **superato come SoT** da B04 DES; baseline post-Slice1 |
| Blocchi 0–7 chiusura | `AUDIT_CHIUSO` |

---

## 6. Criteri per dichiarare chiusi gli strati

### Strato A — Audit + design

1. MC-001…MC-015 senza `BLOCCANTE_APERTO`  
2. Nessuna decisione Founder «approvata ma senza stato»  
3. Follow-up (OPEN-01, B05–B07) etichettati `FASE_SUCCESSIVA`/`FUORI_MASTER`

### Strato B — Implementazione autorizzata

1. MC-020…MC-025 + **MC-026a** + **MC-028** (pezzo wallet #218) `IMPL_MERGIATO`  
2. **MC-026b** conformità accettata dal Founder (checklist aggiornata)  
3. MC-042 **v2** decisione funzionale già; enforcement completo **non** richiesto per chiudere B **solo se** Founder firma riserve esplicite  
4. MC-054…059 decisioni funzionali già; impl **non** richiesta per B **solo con** riserve Founder  
5. MC-040/041/043 conferma Founder ancora necessaria  
6. MC-045…MC-049 **non** richiesti  
7. MC-050/051/053 chiusi; **MC-052 firmato** dal Founder  
8. CI verde su `main` tip  
9. Report finale firmato con scostamenti accettati espliciti

### Strato C — Readiness commerciale

**Non** chiudibile con questo piano. Richiede MC-030…MC-037 + MC-048/049 e mandato separato.

---

## 7. Sequenza operativa (aggiornata 18 nov — secondo turno)

1. ~~ChatGPT revisiona piano~~ → **fatto**.  
2. ~~MC-042 v1 + PR #218 wallet/fail-open~~ → **mergiato** su `main` @ `547f67f`.  
3. ~~Founder MC-042 v2 + MC-054…059~~ → **decisioni funzionali** 18/11 (secondo turno).  
4. Cursor **allinea docs** su PR #217 (questo turno) — **nessun codice**.  
5. Verifica tecnica sospensione/deroga (sola lettura) → poi mandato impl se serve.  
6. Founder conferma **MC-040 / MC-041 / MC-043**.  
7. Founder firma **MC-026b** (checklist) + strato A + `MASTER STRATO B CHIUSO`.  
8. Merge PR #217 **solo** su ordine Founder.  
9. Solo dopo: autorizzazione esplicita al prossimo pacchetto codice (MC-042 v2 lockout / MC-054…059).

---

## 8. Cosa NON fare in nome della «chiusura»

- Riaprire D01–D12 / DES-01…10 / B01–B03 DEC  
- Implementare H3/H4/B04-III…VII / B05–B07 / MC-054…059 / MC-042 v2 lockout senza mandato  
- Dichiarare MC-042 o deroga «implementate» perché #218 ha chiuso il pezzo wallet  
- Migrare legacy o toccare Stripe live  
- Dichiarare «prodotto pronto» confondendo strato B con strato C  
- Usare `OMNIA-HANDOFF-PER-CHATGPT.md` (14 nov) o **D-176** come SoT vigente  
- Merge #217 senza ordine Founder

---

## 9. Verdetto (18 nov 2026 — post decisioni secondo turno)

| Domanda | Risposta |
|---|---|
| CI #216 / #218 | **OK** · `main` @ `547f67f` |
| Codice H2 | **OK** (accettazione MC-026b ancora aperta) |
| MC-042 v2 | **Decisione APPROVATA** · enforcement completo **NO** · wallet ceased **PARZIALE** (#218) |
| MC-054…059 | **Decisioni APPROVATE** · codice **mancante/non conforme** (giorno 8 read/allocate) |
| Master strato A | **SÌ COND** — manca firma Founder |
| Master strato B | **SÌ COND** — manca MC-026b + MC-040/041/043 + MC-052 |
| Master strato C | **NO** · fuori |
| Prossimo codice | **Nessuno** senza autorizzazione esplicita |

### Scostamenti MC-026b (evidenza, non firma) — baseline `547f67f`

| Tema | Decisione | Codice | Esito |
|---|---|---|---|
| MC-042 v2 lockout totale | No login/accesso autonomo; Super Admin via email | Non implementato come chiusura totale | **SCOSTAMENTO** |
| MC-042 wallet su ceased | No wallet | Gate operable + fail-open fix (#218) | **PARZIALE** |
| MC-054 giorno 8 wallet/crediti | Deny read+mutate+spend | Spend sì; read/allocate ancora su `billing_only` | **SCOSTAMENTO** |
| MC-055…059 | Riattivazione/deroga/comms | Assenti (≠ D07) | **SCOSTAMENTO / MANCANTE** |
| D01–D12 resto H2 | Conformità | #216 su `main` | **Impl sì — firma Founder no** |

**STOP:** nessun merge #217, nessun codice, nessuna chiusura strato B da Cursor.

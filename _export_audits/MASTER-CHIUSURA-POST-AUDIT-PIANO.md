# OMNIA — Piano di chiusura master post-audit

**Data:** 17 novembre 2026 · ~20:20 Europe/Rome  
**Baseline codice:** `main` @ `c3baebc40559641590f5a1bac8705400ef992537` (merge PR #216)  
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
| **MC-026** | Conformità D01–D12 post-fix | `IMPL_MERGIATO` · **accettazione Founder pendente** | report residuale aggiornato; CI verde | MC-025 | P0 | Founder (o ChatGPT+Founder) firma «CONFORME / CONFORME CON RISERVE accettate» |
| **MC-027** | Suite test B04 locale + CI | `IMPL_MERGIATO` | 57 passed; CI success `c3baebc` | MC-020–025 | P0 | Log pytest + Actions success sul tip |

### 4.4 Residui B04-H2 / H1 (classificazione)

| ID | Descrizione | Stato attuale | Evidenza richiesta | Dipendenze | Priorità | Criterio di chiusura |
|---|---|---|---|---|---|---|
| **MC-040** | UI Cabina accept transfer | `RESIDUO_ACCETTABILE` | report H2 §limiti | MC-025 | P2 | Accettazione Founder: API ok, FE fuori scope master B |
| **MC-041** | Expiry transfer lazy (no cron) | `RESIDUO_ACCETTABILE` | D09 + codice `_expire_if_needed` | MC-025 | P3 | Accettato come lazy |
| **MC-042** | Read wallet su CC non operativo «limitata» | `RESIDUO_ACCETTABILE` · **whitelist non definita** | design D05; report | MC-014 | P2 | O decisione Founder su whitelist **oppure** accettazione esplicita «consultazione non ristretta finché non definita» |
| **MC-043** | CC senza Main Admin → deny finché Ops nomina | `RESIDUO_ACCETTABILE` (intenzionale D01) | report migrazione | — | P1 | Runbook Ops nomina post-deploy (doc) |
| **MC-044** | Gap storico «agency_admin filiale = wallet» pre-binding | **CHIUSO da MC-025** | assert Main Admin | MC-025 | — | Non riaprire: superato dal binding |
| **MC-045** | H3 allocate solo org linkate al CC | `FASE_SUCCESSIVA` | NEXT_SESSION; H1 report | MC-022 | P1 | Non nel master B; slice dedicata se autorizzata |
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
| **MC-050** | Aggiornare `memory/NEXT_SESSION.md` post-#216 | `BLOCCANTE_APERTO` (doc) | questo piano + PR #216 | MC-025 | P0 | File riflette merge H2 residuale + strati A/B/C |
| **MC-051** | Sostituire SoT handoff ChatGPT stale | `DOC_STALE` | nuovo puntatore a questo piano | — | P0 | ChatGPT usa questo file + indice, non handoff 14 nov come verità |
| **MC-052** | Report finale chiusura master strato B | `BLOCCANTE_APERTO` | template §6 | MC-026, MC-040–043 accettati | P0 | Report firmato Founder «MASTER STRATO B CHIUSO» |
| **MC-053** | Indice audit aggiornato con questo piano | in corso su questo branch | `00-INDICE-AUDIT.md` | — | P1 | Voce 35+ presente |

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

### Strato B — Implementazione autorizzata (obiettivo chiusura «oggi»)

1. MC-020…MC-027 `IMPL_MERGIATO`  
2. MC-026 conformità accettata dal Founder  
3. MC-040…MC-043 con **accettazione esplicita** o decisione  
4. MC-045…MC-049 **non** richiesti  
5. MC-050…MC-052 completati  
6. CI verde su `main` tip  
7. Report finale: implementato / testato / mergiato / residuo accettato / fuori scope

### Strato C — Readiness commerciale

**Non** chiudibile con questo piano. Richiede MC-030…MC-037 + MC-048/049 e mandato separato.

---

## 7. Sequenza operativa consigliata (senza codice nuovo)

1. **Founder legge questo piano** e conferma strati A/B/C.  
2. **Accetta o decide** sui residui MC-040…MC-043 (soprattutto MC-042).  
3. **ChatGPT (opzionale):** riesame conformità MC-026 sul codice già mergiato — sola lettura.  
4. Cursor aggiorna `NEXT_SESSION.md` + report finale MC-052 (**doc only**, questo branch).  
5. Founder dichiara: `MASTER STRATO B CHIUSO` **oppure** elenca MC ancora aperti.  
6. Solo dopo: autorizzazione esplicita al **prossimo** pacchetto (es. H3+H4 **oppure** B04-III) — mai implicita.

---

## 8. Cosa NON fare in nome della «chiusura»

- Riaprire D01–D12 / DES-01…10 / B01–B03 DEC  
- Implementare H3/H4/B04-III…VII / B05–B07 senza mandato  
- Migrare legacy o toccare Stripe live  
- Dichiarare «prodotto pronto» confondendo strato B con strato C  
- Usare `OMNIA-HANDOFF-PER-CHATGPT.md` (14 nov) come stato corrente

---

## 9. Verdetto Cursor (17 nov 2026)

| Domanda | Risposta |
|---|---|
| CI #216 / post-merge | **OK** |
| Codice H2 su `main` | **OK** (`c3baebc` include `99a967e`) |
| Master strato A | **Chiudibile** con conferma formale Founder su MC-001…015 |
| Master strato B | **Chiudibile dopo** MC-026 firma + accettazione residui MC-040…043 + MC-050…052 |
| Master strato C | **Aperto** · fuori perimetro |
| Prossimo codice | **Nessuno** finché Founder non sceglie e autorizza il pacchetto successivo |

**STOP esecutivo:** nessun H3/H4/legacy/B04-III avviato da questo documento.

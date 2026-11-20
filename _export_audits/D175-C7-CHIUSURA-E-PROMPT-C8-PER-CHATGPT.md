# OMNIA D-175 — Briefing C7 chiuso + Prompt C8 per ChatGPT

**Data:** 20 novembre 2026 · ~14:50 Europe/Rome  
**Destinatario:** ChatGPT (governance / design)  
**Autore pacchetto:** Cursor, su mandato Founder  
**Repo SoT:** `github.com/mcnicastro-netizen/omnia2`  
**main tip certificabile come baseline post-C7:** `9aec1921e92207db078f710b2c3fdc7586b061dd` (merge PR #238)

> Questo file **non** è autorizzazione all’implementazione di C8.  
> Non riaprire C1–C7. Non Stripe LIVE. Non produzione. Non sealed mint.

Copia di lavoro anche in artifact Cursor: `/opt/cursor/artifacts/D175-C7-CHIUSURA-E-PROMPT-C8-PER-CHATGPT.md`

---

# PARTE A — Cosa abbiamo fatto (C7) — per ChatGPT

## A1. Verdetto

**D-175 C7 (Registro sessioni Dogfood + catalogo scenari) è CHIUSO in `main`.**

| Voce | Valore |
|---|---|
| PR | https://github.com/mcnicastro-netizen/omnia2/pull/238 |
| Merge commit | `9aec192` (20 nov 2026, ~14:45 Europe/Rome) |
| Tip branch pre-merge | `0fd07d6` |
| CI tip | verde (2/2) |
| Bugbot | 4 issue → fix `ba6eac4`, poi CI verde |
| Baseline design C7 | `8b3723d` (post-C6) |
| Sealed H4 | **ancora ASSENTE** |
| Stripe LIVE | vietato |
| Base permanente | non toccata |

## A2. Cosa chiudeva C7 (e cosa abbiamo consegnato)

Obiettivo C7 (piano Step2C W5): **registro sessioni + scenari ripetibili**, non la certificazione Founder (quella è C8).

### Consegnato in codice/docs

1. **Registro FS append-only** sotto `dogfood/sessions/` (gitignored runtime)
   - header, events jsonl, tip, index
   - hash chain SHA-256 con `prev_hash` (genesis = 64 zeri)
   - serializzazione `omnia.dogfood.jcanonical.v1` (RFC 8785 / JCS-compatible, no float, timestamp UTC stretti)
2. **Seal-before-recover** su coda parziale (solo sessioni `OPEN`): evidenze fsyncate → recovered → `INTERRUPTED`
3. **Binding CLEAN/CONTINUITY**
   - CLEAN: DENY se `git status --porcelain` non vuoto (`CLEAN_DENIED_DIRTY_TREE`)
   - assert SHA / branch / workcopy
4. **Checkpoint unsigned + verify Ed25519 pure (RFC 8032)**
   - firma offline Founder; Dogfood **non** ha la privata
   - domain separation: `OMNIA_DOGFOOD_CHECKPOINT_V1\n` + canonical JSON
5. **Pubkey installata**
   - `docs/dogfood/c7_registry_verify.pub`
   - `docs/dogfood/c7_registry_verify.fingerprint`
   - fingerprint: `sha256:e7bd2c5fa33a26ee9e34760a99fe64cb45924396b7a77a11be95b6ff0a1253ac`
   - `attach-sig` legge fingerprint dal file (niente export obbligatorio)
6. **CLI**
   - `scripts/dogfood_session.py` — open/bind/close/verify/recover-partial/attach-sig/fingerprint
   - `scripts/dogfood_c7_sign_offline.py` — firma offline (privata fuori repo)
7. **Catalogo scenari stub versionato**
   - `docs/dogfood/scenarios/catalog.yaml` (`df-catalog-2026.11.1`)
   - include gap prodotto obbligatori D-C7-04: Deal / Chat / Mini-dossier (`product_gap: true`)
8. **Test**
   - `backend/tests/test_d175_c7_session_registry.py` → **14 passed** al tip merge

### Decisioni Founder recepite (chiuse)

| ID | Sintesi |
|---|---|
| D-C7-01 | Tamper-evident, hash chain, checkpoint firmati, mirror riscontro; WORM fuori C7 |
| D-C7-02 | Privata Ed25519 offline solo Founder |
| D-C7-03 | Filesystem unica SoT; niente registro Mongo parallelo |
| D-C7-04 | Deal, chat, mini-dossier obbligatori nel perimetro Dogfood |
| D-C7-05 | CLEAN deny assoluto se dirty tree |
| D-C7-06 | Pubkey in docs + fingerprint |
| P-C7-01 | Copia **off-host** evidenze = **requisito futuro** (non bloccante C7/C8 ora) |
| P-C7-02 | Assenza mirror off-host **non** blocca close né certificazione; **M3 non vincolo** |
| P-C7-04 | Ed25519 pure RFC 8032 |

### Remediazioni Bugbot (prima del merge)

1. `attach-sig` legato al **prefisso journal** del checkpoint (non al tip grezzo)
2. `OMNIA_DOGFOOD_SESSIONS_ROOT` senza doppio `/sessions`
3. recover solo se status `OPEN`
4. fsync evidenze prima di `os.replace`

## A3. Cosa C7 NON ha fatto (ancora vero)

- **Non** è certificazione Founder (C8)
- **Non** ha eseguito la matrice completa DF-* E2E “sessione collaudo”
- **Non** ha chiuso i gap prodotto Deal/Chat/Mini-dossier (catalogati, non “OUT”)
- **Non** ha acceso sealed H4 / Stripe E2E TEST reale / Stripe LIVE
- **Non** ha implementato mirror off-host (P-C7-01 futuro)
- **Non** ha aggiornato ancora `memory/NEXT_SESSION.md` / DECISIONS EOD (memoria ancora ferma a “C5–C8 non autorizzati” — **stale** rispetto a main; C5–C7 sono in main)

## A4. Stato cicli (verità operativa post-merge)

| Ciclo | Contenuto | Stato |
|---|---|---|
| C1 | Perimetro | **CHIUSO in main** |
| C2 | Backup/restore | **CHIUSO in main** |
| C3 | Base permanente | **CHIUSO in main** |
| C4 | Account/org/Main Admin | **CHIUSO in main** |
| C5 | Acquisti H4 Main Admin | **CHIUSO in main** (#236) |
| C6 | Fulfillment/storage SoT | **CHIUSO in main** (#237 → `8b3723d`) |
| C7 | Registro/scenari | **CHIUSO in main** (#238 → `9aec192`) |
| C8 | Certificazione CF1–CF18 + firma Founder | **NON AVVIATO / NON AUTORIZZATO** |
| Dogfood E2E “completo” | dopo C8 | **NON AUTORIZZATO** |

## A5. Regola certificazione sessione (già design-chiusa in C7)

Una sessione è **certificabile** solo se:

```
status == COMPLETED
∧ signature_status == SIGNED_VERIFIED
∧ verify_chain == PASS
```

Mirror off-host **non** richiesto (P-C7-02).

## A6. Custodia chiave Founder (ops)

- Pubkey + fingerprint: in repo (`docs/dogfood/c7_registry_verify.*`)
- Privata: salvata dal Founder **fuori repo** (file Desktop/vault); generata in sessione C7 e consegnata out-of-band
- Dogfood non deve mai contenere la privata

---

# PARTE B — PROMPT DA INCOLLARE IN CHATGPT (C8)

Copia tutto il blocco sotto (da `OMNIA — MANDATO` fino a fine).

```text
OMNIA — MANDATO CHATGPT · D-175 C8 CERTIFICAZIONE (READ-ONLY)

Ruolo tuo: ChatGPT = governance / design / checklist / domande Founder.
Cursor = codice solo dopo formula esplicita (NON data qui).

============================================================
0. CONTESTO FISSATO (NON RIAPRIRE)
============================================================
Repo SoT: github.com/mcnicastro-netizen/omnia2
main tip post-C7: 9aec1921e92207db078f710b2c3fdc7586b061dd
(merge PR #238 C7)

Cicli C1–C7: CHIUSI in main. Non riaprire decisioni già firmate.
Sealed H4: ASSENTE. Stripe LIVE: VIETATO. Produzione: VIETATA.
Base permanente: nessuna modifica.
P-C7-01 off-host: requisito FUTURO; per P-C7-02 non blocca certificazione.
P-C7-02 / P-C7-04 / D-C7-01…06: CHIUSE (vedi Parte A del pacchetto Cursor).

C7 ha consegnato:
- registro FS append-only + hash chain + jcanonical.v1
- seal-before-recover
- CLEAN deny dirty + binding SHA/branch/workcopy
- checkpoint Ed25519 pure verify + pubkey/fingerprint installati
- catalog scenari df-catalog-2026.11.1 (stub; Deal/Chat/Mini-dossier = product_gap obbligatori)
- CLI dogfood_session + sign_offline
- test C7 verdi; Bugbot remediated; merge #238

Regola sessione certificabile (già chiusa):
COMPLETED ∧ SIGNED_VERIFIED ∧ chain PASS.
Mirror off-host NON richiesto ora.

============================================================
1. OBIETTIVO C8 (dal piano Step2C)
============================================================
C8 = Wave W6 Certificazione.
Uscita attesa: checklist CF1–CF18 verificata con evidenze + verbale + FIRMA Founder.
C8 NON è “scrivere altro prodotto”.
C8 NON è merge produzione.
C8 NON riapre H4 sealed / Stripe LIVE senza mandato separato.

Checklist target (Step2B CF1–CF14 + Step2C delta):

CF1  Isolamento dimostrato (DB/URL/env)
CF2  Nessun instradamento produzione
CF3  Resend protetto
CF4  Backup+restore verificati su probe
CF5  Base permanente protetta
CF6  Copie CLEAN/CONTINUITY + SHA manifest
CF7  H4 completato e verificato
CF8  Stripe TEST + webhook E2E (+ Dashboard Founder)
CF9  Wallet/crediti/storage coerenti con CC
CF10 Scenari ripetibili disponibili (allineare a catalogo DF-* C7, non solo S01–S16 legacy)
CF11 Registro sessioni funzionante (≥1 sessione collaudo completa firmata)
CF12 E2E senza anomalia bloccante/grave aperta
CF13 Hard-gate rimosso solo dopo CF7–CF9 (oggi sealed ASSENTE → probabilmente NON soddisfatto)
CF14 Tip SHA certificato = baseline approvato
CF15 Protezione permanente (test deny)
CF16 Allowlist host fail-closed
CF17 Copertura funzionale: ogni scenario DOGFOOD-REQUIRED = PASS oppure NON DISPONIBILE con ack Founder esplicito
CF18 Privilegi Mongo: runtime ≠ write sulla permanente

Fallisce certificazione se manca uno qualsiasi dei CF1–CF18 (salvo ack Founder esplicito di deroga documentata — se proponi deroga, deve essere domanda separata, mai silenziosa).

============================================================
2. MODALITÀ (OBBLIGATORIA)
============================================================
- READ-ONLY rispetto al codice: tu NON implementi; NON chiedere a Cursor di implementare in questo mandato.
- NON inventare evidenze. Se manca prova → stato NON VERIFICATO / BLOCCATO.
- Distingui sempre:
  (a) già dimostrato da C1–C7 con evidenza in main
  (b) dimostrabile ora senza sealed/Stripe E2E
  (c) bloccato da gated dipendenze (H4 sealed, Stripe E2E TEST, gap prodotto)
  (d) richiede solo procedura/firma Founder
- Una sola decisione Founder aperta alla volta.
- Output in italiano, strutturato, ID stabili (es. C8-Q01, C8-G1, CF7-BLOCK).

============================================================
3. DELIVERABLE RICHIESTI (UNICO PACCHETTO)
============================================================
Produci UN documento con queste sezioni obbligatorie:

§1 Executive summary
- Verdetto C8: PRONTA / NON PRONTA / PRONTA CON RISERVE
- 5–10 righe max

§2 Matrice CF1–CF18 (tabella)
Colonne: ID | Criterio | Stato(PASS/FAIL/BLOCKED/UNKNOWN) | Evidenza già in main (ref) | Gap | Blocco gated? | Azione C8

§3 Sessione di certificazione (design operativo)
Come usare il registro C7 per C8:
- open CLEAN (o CONTINUITY se motivato)
- bind + verify chain
- esecuzione scenari REQ (o ack NON DISPONIBILE)
- close COMPLETED
- unsigned checkpoint → firma offline Founder → attach-sig → SIGNED_VERIFIED
Cosa va nel verbale. Cosa firma il Founder. Cosa NON firma.

§4 Gate Stripe/H4 (chiarire senza riaprire C5/C6)
Tabella a 3 livelli:
- unit/API mock (già usati C5/C6)
- E2E Stripe TEST reale (dual-gate H4+sealed) — stato attuale
- Stripe LIVE — vietato
Impatto su CF7/CF8/CF13: possono essere PASS ora? Se no, quali opzioni Founder (differire / deroga esplicita / mandato sealed separato)? NON raccomandare LIVE.

§5 Gap prodotto vs gap Dogfood (D-C7-04)
Deal / Chat / Mini-dossier: obbligatori. Se non E2E-verificabili → CF17 NON DISPONIBILE richiede ack Founder, non “OUT silenzioso”.

§6 Piano C8 senza codice (procedurale)
Passi numerati Founder/Cursor/ChatGPT. Nessuna fase di coding salvo elenco “eventuali tool minimi C8” SE strettamente necessari alla checklist (es. script verbale) — e anche quelli restano NON autorizzati finché non arriva la formula.

§7 Domande Founder aperte (max 5, priorità)
Solo se bloccano il verdetto. Formato: ID | Domanda | Opzioni | Impatto CF

§8 Esclusioni
H4 sealed mint, Stripe LIVE, produzione, off-host P-C7-01 come lavoro C8, merge prod, E2E “Dogfood completo” oltre C8.

§9 Formula di chiusura design
Alla fine: DESIGN C8 CHIUSO / NON CHIUSO.
Se chiuso: testo esatto che il Founder dovrà usare per autorizzare eventuale esecuzione procedurale/implementativa C8 (separata), sul baseline `9aec192`.

============================================================
4. INPUT ALLEGATI / RIFERIMENTI
============================================================
Usa come fonti:
- Questo mandato + Parte A (chiusura C7) del pacchetto Cursor
- Piano: Step2C v1.1 (C8 = CF1–CF18 firma); Step2B §5 CF1–CF14
- Docs repo: docs/dogfood/C7-SESSION-REGISTRY.md
- Catalog: docs/dogfood/scenarios/catalog.yaml
- PR #238 merge `9aec192`

Se ti manca un’evidenza runtime (es. drill C2 verbale), marca UNKNOWN e chiedi a Cursor un audit read-only mirato — non inventare PASS.

============================================================
5. COSA NON FARE
============================================================
- Non riaprire C1–C7
- Non dichiarare Dogfood “completo” solo perché C7 è merged
- Non trattare product_gap Deal/Chat/Dossier come OUT
- Non chiedere implementazione Cursor senza formula Founder
- Non proporre WORM/Mongo registry parallelo (D-C7-03 chiusa)
- Non rendere off-host un blocker (P-C7-02)

Inizia da §1 + bozza matrice CF, poi fermati sulla prima domanda Founder davvero bloccante.
```

---

# PARTE C — Nota operativa Founder (non per ChatGPT)

1. Incolla in ChatGPT la **Parte B** (blocco `OMNIA — MANDATO…`).
2. Se ChatGPT chiede evidenze mancanti: torna a Cursor con audit read-only mirato C8.
3. Solo dopo design C8 chiuso + tua formula esplicita si esegue C8.
4. Memoria repo (`NEXT_SESSION.md`) è stale su C5–C8: aggiornamento EOD da fare con mandato docs (non confondere con C8 coding).

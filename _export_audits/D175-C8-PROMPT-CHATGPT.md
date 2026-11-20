# OMNIA · C7 chiuso → mandato C8 (ChatGPT)

**Data:** 20 nov 2026 Europe/Rome  
**Repo:** `mcnicastro-netizen/omnia2`  
**main tip:** `9aec192` (merge C7 PR #238)  
**Questo file NON autorizza implementazione.**

---

## A. Cosa ha chiuso C7

Registro sessioni Dogfood in main: journal append-only + hash chain, seal-before-recover, CLEAN deny dirty, checkpoint Ed25519 (pubkey in `docs/dogfood/c7_registry_verify.*`), catalog `df-catalog-2026.11.1`, CLI `dogfood_session` + sign offline. Bugbot fixati. CI verde.

**C1–C7 chiusi in main. C8 non avviato.**  
Sealed H4 assente. Stripe LIVE vietato. Permanente intoccata.  
Off-host (P-C7-01) = futuro; non blocca cert (P-C7-02).

Sessione certificabile: `COMPLETED` ∧ `SIGNED_VERIFIED` ∧ chain PASS.

---

## B. Prompt C8 (incolla tutto sotto)

```
OMNIA — MANDATO CHATGPT · D-175 C8 CERTIFICAZIONE (READ-ONLY)

Tu = design/checklist/domande Founder. Cursor = codice solo dopo formula esplicita (non data qui).

FISSO
- main tip 9aec192 · C1–C7 CHIUSI · non riaprire
- sealed H4 ASSENTE · Stripe LIVE vietato · produzione vietata
- C7 già ha registro + firma verify + catalog scenari (Deal/Chat/Dossier = product_gap obbligatori, non OUT)
- cert sessione: COMPLETED ∧ SIGNED_VERIFIED ∧ chain PASS · off-host NON richiesto

OBIETTIVO C8
Checklist CF1–CF18 + verbale + firma Founder. Non prodotto nuovo. Non merge prod.

CF1 isolamento · CF2 no prod · CF3 Resend · CF4 backup/restore · CF5 permanente · CF6 CLEAN/CONTINUITY
CF7 H4 verificato · CF8 Stripe TEST+webhook E2E · CF9 wallet/storage CC · CF10 scenari DF-*
CF11 registro (≥1 sessione firmata) · CF12 E2E no bloccanti · CF13 hard-gate solo dopo CF7–9
CF14 tip SHA · CF15 permanente deny · CF16 allowlist · CF17 REQ=PASS|NON DISPONIBILE+ack Founder
CF18 Mongo runtime ≠ write permanente

MODALITÀ
Read-only. No inventare evidenze. Distingui: (a) già in main (b) dimostrabile ora (c) gated H4/Stripe/gap (d) solo firma Founder.
Una domanda Founder alla volta.

DELIVERABLE (un doc)
§1 verdicto C8 (PRONTA / NON PRONTA / RISERVE)
§2 matrice CF1–CF18: ID|criterio|PASS|FAIL|BLOCKED|UNKNOWN|evidenza|gap|azione
§3 procedura sessione cert con CLI C7 + cosa firma Founder
§4 gate Stripe/H4 a 3 livelli (mock / E2E TEST sealed / LIVE) → impatto CF7/8/13; opzioni Founder senza LIVE
§5 Deal/Chat/Dossier → CF17 ack, non OUT
§6 piano procedurale (no coding autorizzato)
§7 max 5 domande Founder bloccanti
§8 esclusioni (sealed mint, LIVE, prod, off-host come lavoro C8)
§9 DESIGN C8 CHIUSO/NON + formula esatta autorizzazione futura su baseline 9aec192

Inizia da §1 + bozza matrice. Fermati sulla prima domanda Founder bloccante.
```

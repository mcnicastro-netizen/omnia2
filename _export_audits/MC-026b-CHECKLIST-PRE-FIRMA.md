# MC-026b — Checklist conformità Strato B

**Aggiornato:** 18 novembre 2026 · ~14:35 Europe/Rome  
**ID:** MC-026b  
**Stato firma Founder (storica):** **FIRMATA** 18/11/2026 — `CONFORME CON RISERVE`  
**Baseline codice:** `main` @ `11f29621dd2ddef9e4a61fa3ece569a65f94eaf9`  
**Rapporto:** `_export_audits/MASTER-RAPPORTO-FINALE-CHIUSURA-STRATI-A-B.md` (revisione R-01)

---

## Lessico

| Termine | Significato |
|---|---|
| Affrontata | Implementazione presente su `main` |
| Risolta | Affrontata e conforme alla decisione senza gap aperti rilevanti |
| Parziale | Affrontata con gap documentato |

---

## A. D01–D12

| Tema | Esito | Nota |
|---|---|---|
| Binding/transfer/D07 | Affrontata → trattabile **risolta** (Master) | #216+#219 |

---

## B. MC-042 v2

| Requisito | Esito | Evidenza / test | In CI B04? |
|---|---|---|---|
| Login deny | Affrontata → **risolta** | #220 · `test_mc042_v2_suspend_deroga` | No |
| API deny (`get_current_user`) | Affrontata → **risolta** | #220 · unit enforce | No |
| Wallet deny | Affrontata → **risolta** | #218+#220 · `test_mc042_cc_non_operable_wallet` | Parziale (`b04ii`) |
| Refresh/session post-cease (R-01) | **NON risolta** | Audit sola lettura 18/11 | — |
| Conservazione dati | Principio OK | | |

---

## C. MC-054…059

| ID | Esito | Test | In CI B04? |
|---|---|---|---|
| MC-054 B | Affrontata → trattabile **risolta** | `test_mc042_v2_suspend_deroga` | No |
| MC-055 saldo | Affrontata → trattabile **risolta** | outstanding balance unit | No |
| MC-056…059 | Affrontata → trattabile **risolta** | deroga unit | No |

---

## D. MC-040/041/043/045

| ID | Esito | Evidenza |
|---|---|---|
| 040/041/043 | Risolta (Master) | #219 |
| 045 H3 | Risolta | #222 · `test_mc045_h3_allocate_link` (**non** in CI) |

---

## E. Firma storica 18/11 — invariata

- [x] `CONFORME CON RISERVE` all’epoca (042/054/055…059 da implementare)  
- Founder: Marco Nicastro · 18/11/2026  

**Post-riserve:** implementazioni **affrontate**; chiusura «tutto risolto» **sospesa** finché Founder non classifica R-01 (§10 rapporto A/B).

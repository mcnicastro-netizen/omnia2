# D175-PR240-DEFINITIVE-REMEDIATION-REPORT

## A. Identificazione
| Campo | Valore |
|-------|--------|
| Branch | `cursor/d175-deal-chat-dossier-h4-e393` |
| SHA iniziale dichiarato (mandato patch) | `1eda988b611928956741fdd8df228ffd61efd7ed` |
| Codice funzionale precedente | `68b0fc6` |
| Tip pre-patch (EOD docs) | `758df8632f41d340871b1c67d55a64342a34b70e` |
| SHA codice patch (testato) | `122d5386f6050c375b3432960c8fda686287161c` |
| SHA tip branch (allineato) | `96de408cd76186d568240b52cde3e1fea3483398` |
| PR | https://github.com/mcnicastro-netizen/omnia2/pull/240 |
| Ambiente | Dogfood `OMNIA_ENV=dogfood` · `DB_NAME=omnia_df_clean_c4` · Mongo `:27018` |
| Working tree pre-intervento | pulito su `758df86` |
| Merge | **Autorizzato Founder 20-Nov-2026 (Europe/Rome) — in corso** |
| Perimetro | **solo** FIX-07, FIX-08, FIX-09 + CI suite D-175 + report |

## B. Registro FIX-01…06 (invariati — regressione)
I sei fix precedenti restano invariati nel comportamento. Rieseguiti in `tests/test_d175_pr240_remediation.py` + bundle collab/deal handlers: **PASS**.

| FIX | Regressione | Esito |
|-----|-------------|-------|
| FIX-01 webhook `subscription.deleted` | `test_fix01_*` | PASS |
| FIX-02 isolamento thread chat | `test_fix02_*` | PASS |
| FIX-03 revoke → documenti | `test_fix03_*` | PASS |
| FIX-04 Deal richiede collab attiva | `test_fix04_*` | PASS |
| FIX-05 no duplicazione da offerta | `test_fix05_*` | PASS |
| FIX-06 gate MLS | `test_fix06_*` | PASS |

## C. Patch finale Bugbot — FIX-07 / FIX-08 / FIX-09

### FIX-07 — Watermark PDF fail-closed
- **Causa:** `merge_page` in `except: pass` → pagina originale distribuita con header `X-OMNIA-Watermark: 1`.
- **Modifica:** `_watermark_pdf` fail-closed su overlay/merge/write; errore HTTP 500 controllato `watermark_apply_failed` + log stage senza secret; nessuna consegna parziale; originale non mutato.
- **File:** `backend/shared/mls_collab/watermark.py`
- **Test:** `test_fix07_*` (valid multipagina, merge fail, overlay fail, midpage, download header solo se WM, download deny se WM fallisce) — **PASS**
- **Dogfood:** download PDF 200, header WM=1, testo watermark nel PDF, originale invariato — **PASS**

### FIX-08 — Reject solo su collaborazione `pending`
- **Causa:** `reject` non richiedeva `pending` → active poteva diventare `rejected` senza revoca chat/documenti.
- **Modifica:** `reject` solo se `pending`; su `active` → `400 use_revoke_for_active_collaboration`; `rejected`/`revoked` idempotenti; `revoke` idempotente se già revoked (con conseguenze chat/doc).
- **File:** `backend/apps/immoweb/collaborations.py` (`respond_collaboration`)
- **Test:** `test_fix08_*` — **PASS**
- **Dogfood:** reject active 400; revoke → download 403 + chat 403; revoke idempotent — **PASS**

### FIX-09 — Allegato chat stesso `collaboration_id`
- **Causa:** `post_chat_message` non verificava `dr.collaboration_id == thread.collaboration_id`.
- **Modifica:** check esistenza DR; mismatch → `403 attachment_collaboration_mismatch`; status/permessi/accessibilità invariati; nessun messaggio persistito sul deny.
- **File:** `backend/apps/immoweb/collaborations.py` (`post_chat_message`)
- **Test:** `test_fix09_*` — **PASS**
- **Dogfood:** same-collab 201; cross-collab 403 e count messaggi invariato — **PASS**

## D. CI — regressione permanente
- **File:** `.github/workflows/ci.yml`
- **Modifica:** aggiunto `tests/test_d175_pr240_remediation.py` al job unit esistente (niente workflow duplicato).
- Suite offline-safe: FakeDB, no LIVE Stripe, no H4 sealed, no DB permanente.
- Stato CI sullo SHA finale: vedi sezione I (post-push).

## E. Test eseguiti (dichiarati solo se eseguiti)

| Tipo | Suite | Risultato | Log |
|------|-------|-----------|-----|
| Unit | `test_d175_pr240_remediation.py` (FIX-01…09) | **28 PASS** | `/opt/cursor/artifacts/d175-pr240-fix789-pytest.log` |
| Unit bundle | remediation + deal_collab_chat + collab_api_handlers | **35 PASS** | `/opt/cursor/artifacts/d175-pr240-fix789-regression-bundle.log` |
| Unit | C5 H4 purchase authz | **34 PASS** | `/opt/cursor/artifacts/d175-pr240-h4-regression.log` |
| Smoke Dogfood API | FIX-07/08/09 flussi coinvolti | **PASS** `PASS_E2E_FIX789` | `/opt/cursor/artifacts/d175-pr240-fix789-e2e-smoke.log` |
| CI GitHub | job `backend-billing-unit` su tip | post-push | PR checks |

Regressione FIX-01…06: **PASS** (nessuna ricomparsa dei 6 difetti).

## F. Sicurezza / vincoli rispettati
- Nessun Stripe LIVE / mint sealed / H4 aperto / accesso Ed25519.
- Nessuna modifica a `main` / nessun merge.
- Working tree dogfood-only per smoke (reset password sintetici Dogfood per login smoke; non produzione).
- Watermark: originale mai restituito; header WM solo su bytes watermarkati.

## G. Stripe / H4
| Tipo | Stato |
|------|--------|
| Mock / gate H4 (C5) | PASS (34) |
| Checkout TEST live / sealed | **BLOCKED — fuori autorizzazione** |
| LIVE | non usato |

## H. Residui espliciti (non blocking per i 3 finding)
1. UI Super Admin dispute: solo API (preesistente).
2. Stripe TEST checkout completo resta BLOCKED da H4 sealed.
3. Watermark video/audio non supportato (rifiutato).

Nessun defect blocking residuo su FIX-07/08/09.

## I. Verdetto
**`READY FOR FINAL FOUNDER REVIEW` → merge autorizzato Founder**

Tre finding chiusi, regressioni superate, suite D-175 in CI, evidenze codice su `122d538`, tip allineato a questo report. Merge su `main` su richiesta esplicita Founder. Non dichiarato production-ready; Stripe TEST/H4 non completati.

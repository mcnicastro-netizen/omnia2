# MERGE PR #247 — Integrazione D-193 + CMJ + A4

**Data (Europe/Rome):** 2026-11-26 16:26 CET  
**Autore:** Cursor (Cloud Agent)  
**Autorizzazione:** Founder — esecuzione merge esclusivo PR #247  
**Repository:** `mcnicastro-netizen/omnia2`

---

## 0. Esito

**MERGE COMPLETATO** — evidenza GitHub verificabile.

| Voce | Valore |
|------|--------|
| PR | [#247](https://github.com/mcnicastro-netizen/omnia2/pull/247) **MERGED** |
| mergedAt (UTC) | 2026-11-26T15:25:31Z → **16:25 CET** |
| Metodo | `gh pr merge 247 --merge` (merge commit, storia preservata) |
| Merge commit | `2dfee7f6943787c85add865c8519be006a614f59` |
| Nuovo HEAD `main` | `2dfee7f6943787c85add865c8519be006a614f59` |
| Parents | `e5647be…` (main pre) + `e8f21c4…` (integration tip) |
| Deploy | **non eseguito** (fuori autorizzazione) |

---

## 1. Stato iniziale del PR (pre-merge)

| Campo | Valore |
|-------|--------|
| State | OPEN |
| Draft | false |
| Base | `main` @ `e5647be39e463d9d407aed0d2b542a3053be3f61` |
| Head branch | `cursor/integration-d193-cmj-a4-b894` |
| Head OID | `e8f21c4036db1f9a9cc1d7026891b7f8267c041e` |
| mergeable | MERGEABLE |
| mergeStateStatus | CLEAN |
| reviewDecision | (nessuna review richiesta / vuoto) |
| Reviews | [] |
| CI pre-merge | 2/2 SUCCESS (`Backend billing / B04 unit`) |

URL: https://github.com/mcnicastro-netizen/omnia2/pull/247

---

## 2. Verifiche pre-merge

### 2.1 Identità tip vs staging-deep
- Ultimo commit noto atteso: `e8f21c4036db1f9a9cc1d7026891b7f8267c041e` → **coincide con HEAD PR** PASS
- Codice staging-deep: `9b695b1d6597565ea3d4c3d06948daf9b0155ad1` → **antenato di HEAD** PASS
- Diff `9b695b1..e8f21c4`: **solo docs** `docs/reports/STAGING-DEEP-INTEGRATO-D193-CMJ-A4.md` (+289 righe) → nessun codice prodotto post staging-deep PASS

### 2.2 Contenuto integrazione
- Merge commits D-193 / CMJ / A4 presenti nella storia del PR PASS
- `backend/shared/billing/credit_wallet_service.py` (D-193) PASS
- `proposed_slots_min` / visite CMJ in `collaborations.py` PASS
- MLS inventory in `mls.py` PASS
- `backend/tests/test_integration_d193_cmj_a4.py` PASS

### 2.3 Condizioni di merge
- PR aperto PASS
- Base `main` PASS
- CI verde PASS
- Assenza conflitti (CLEAN) PASS
- Nessun requisito review pendente osservato PASS
- `allow_merge_commit: true` PASS

**Nessun blocco.** Merge autorizzato ed eseguito.

---

## 3. Metodo utilizzato

```text
gh pr merge 247 --merge \
  --subject "Merge PR #247: integrazione D-193 + CMJ + A4 (staging-deep PASS)"
```

- Strategia: **merge commit** (non squash, non rebase) per preservare la storia dell’integrazione no-ff.
- Nessuna modifica codice per risolvere conflitti (non necessari).
- Nessun reset / clean / stash / force-push.
- Nessun deploy.

---

## 4. Verifiche post-merge

### 4.1 PR e main
| Check | Esito |
|-------|--------|
| PR #247 state MERGED | PASS |
| `origin/main` == `2dfee7f…` | PASS |
| Subject merge | `Merge PR #247: integrazione D-193 + CMJ + A4 (staging-deep PASS)` |
| `9b695b1` raggiungibile da main | PASS |
| `e8f21c4` raggiungibile da main | PASS |

### 4.2 Contenuti su main
| Path / marker | Presente |
|---------------|----------|
| `backend/shared/billing/credit_wallet_service.py` | SÌ |
| CMJ `proposed_slots_min` / visite | SÌ |
| A4 `backend/apps/immoweb/mls.py` inventory | SÌ |
| `frontend/src/apps/immoweb/components/VisitSlotsPicker.jsx` | SÌ |
| `backend/tests/test_integration_d193_cmj_a4.py` | SÌ |
| `docs/reports/STAGING-DEEP-INTEGRATO-D193-CMJ-A4.md` | SÌ |
| `docs/reports/INTEGRAZIONE-D193-CMJ-A4-LOCAL.md` | SÌ |

### 4.3 CI post-merge su main
| Run | SHA | Conclusion |
|-----|-----|------------|
| [45848970831](https://github.com/mcnicastro-netizen/omnia2/actions/runs/45848970831) | `2dfee7f…` | **success** |
| Job | Backend billing / B04 unit | **success** |

---

## 5. PR sorgente #244 / #245 / #246

### Intento operativo
Non è stata invocata alcuna operazione `merge` / `close` / `edit` sui PR #244, #245, #246.

### Stato osservato dopo il merge di #247
GitHub ha aggiornato automaticamente lo stato perché i rispettivi head commit sono diventati raggiungibili da `main` tramite #247:

| PR | Head OID (invariato) | State pre | State post |
|----|----------------------|-----------|------------|
| #244 D-193 | `eafb931a592b61465faab7c0f19ff2e0d5d6105c` | OPEN | **MERGED** (auto GitHub) |
| #245 CMJ | `7935673c4dd9b23bc8a6c946746d3abb8a97bd73` | OPEN | **MERGED** (auto GitHub) |
| #246 A4 | `888b713254d84504b12938ef5f665d5f85b764b5` | OPEN | **MERGED** (auto GitHub) |

**Anomalia / side-effect documentato:** lo stato non è rimasto OPEN. È il comportamento standard di GitHub quando i commit di un PR confluiscono in `main` via un altro PR. Head OID invariati; nessun merge diretto eseguito su quei PR dall’agent.

---

## 6. Limiti rispettati

- Solo PR #247 mergeato esplicitamente
- Nessun deploy (staging / produzione)
- Nessuna modifica DB, Stripe, email
- Nessuna modifica codice per conflitti
- Nessuna operazione distruttiva (reset/clean/stash/force)

---

## 7. Anomalie / note

1. **Auto-MERGED #244/#245/#246** — side-effect GitHub; OID head invariati; non invocati dall’agent.
2. Titolo PR #247 conteneva ancora «no merge main» (testo storico staging-deep); il Founder ha poi autorizzato esplicitamente questo merge.
3. Questo report è documentation post-merge; non fa parte del merge commit `2dfee7f`.

---

## 8. Evidenze GitHub

- PR MERGED: https://github.com/mcnicastro-netizen/omnia2/pull/247
- Merge commit: https://github.com/mcnicastro-netizen/omnia2/commit/2dfee7f6943787c85add865c8519be006a614f59
- CI main: https://github.com/mcnicastro-netizen/omnia2/actions/runs/45848970831

**Giudizio:** merge PR #247 **riuscito e verificato**.

# OMNIA — Handoff ChatGPT: B04-H2 Main Admin (post-implementazione)

**Data:** 17 novembre 2026 · ~19:50 Europe/Rome  
**Ruolo ChatGPT:** analisi conformità decisione↔codice (sola lettura). **Non** riprogettare. **Non** chiedere nuovo codice.  
**Ruolo Cursor:** implementazione già consegnata; merge **solo** su ordine Founder.  
**Founder:** dopo tua analisi, merge su `main` se OK.

---

## 0. Istruzioni operative (obbligatorie)

1. Analizza **solo** B04-H2 Main Admin residual (binding `main_admin_user_id` + transfer 48h + wallet deny-by-default + D07).
2. Fonte decisioni: `B04-H2-MAIN-ADMIN-DECISIONS-CONFORMITY.md` (D01–D12 chiusi).
3. Fonte design: `B04-H2-MAIN-ADMIN-TECHNICAL-DESIGN.md`.
4. Fonte implementazione: `B04-H2-MAIN-ADMIN-RESIDUAL-IMPLEMENTATION-REPORT.md` + questo handoff.
5. **Non** riaprire D01–D12. Se vedi gap codice↔decisione, elenca con gravità (blocker / non-blocker).
6. **Non** aprire H3, H4, legacy billing, B04-III, Stripe live, produzione.
7. Output atteso (una risposta strutturata):
   - Verdetto: `CONFORME` / `CONFORME CON RISERVE` / `NON CONFORME`
   - Tabella: `ID decisione | Evidenza codice | Esito | Nota`
   - Residui ammessi (UI Cabina, job expiry lazy) vs blocker
   - Raccomandazione merge: `SÌ` / `SÌ CON FOLLOW-UP` / `NO` + motivo in 3 righe max

---

## 1. Coordinate repo / PR

| Campo | Valore |
|---|---|
| Repo | `github.com/mcnicastro-netizen/omnia2` |
| Branch | `cursor/b04-h2-main-admin-impl-e393` |
| Commit | `bb0ef5eb4dd9b4356c7cd886c5374c938d3f697f` |
| Base | `main` @ `3b425a8e53e29a14fa209f050a58530231bd3fa8` |
| PR | https://github.com/mcnicastro-netizen/omnia2/pull/216 |
| CI GitHub Actions | **verde** — job `Backend billing / B04 unit` success (~19:44 Europe/Rome) |
| Merge | **non eseguito** — attende Founder dopo analisi ChatGPT |

---

## 2. Cosa è stato implementato (sintesi)

### Binding e audit
- Su `CommercialCustomer`: `main_admin_user_id`, `main_admin_nominated_at`, `main_admin_nominated_by`, `main_admin_events` (append-only), `main_admin_transfer` (pending/accept/cancel/expire).
- Indici: `main_admin_user_id`, `main_admin_transfer.transfer_token` (token solo hash).

### Ciclo vita
- **Nomina / revoke:** solo Ops (`POST /ops/commercial-customers/main-admin`, revoke dedicato).
- **Transfer 2 fasi:** initiate → accept/cancel; TTL **48h**; notifica Cabina + email Resend best-effort.
- **Idoneità dinamica:** assert su ruolo/account/CC operativo; perdita requisiti → deny immediato; nessuna successione automatica.

### Wallet
- Deny-by-default su admin wallet centrale se Main Admin `null` / non match / non idoneo / CC non operabile.
- `agency_admin` / `group_admin` **senza** nomina → **deny** (breaking accettata D12).
- Super Admin allocate/revoke: solo con `extraordinary_reason` (≥8 char) + audit (D07). Non diventa Main Admin.
- H1 revoke isolation (`commercial_customer_id`) preservato.

### Fuori scope (confermato non toccato)
H3, H4, migrazione legacy, B04-III, UI FE accept transfer, Stripe live, merge `main`.

### Migrazione dati
**Nessuna.** CC esistenti restano `main_admin_user_id=null` → wallet admin deny finché Ops nomina.

---

## 3. File codice rilevanti

| File | Ruolo |
|---|---|
| `backend/shared/models/commercial_customer.py` | campi Main Admin |
| `backend/shared/billing/main_admin_service.py` | ciclo vita + assert |
| `backend/shared/db/connection.py` | indici |
| `backend/apps/billing/routes.py` | wallet guards + transfer API |
| `backend/apps/immoweb/founder_ops.py` | Ops nominate/revoke |
| `backend/tests/test_b04_h2_main_admin.py` | suite H2 |
| `backend/tests/test_b04_h1_h2_wallet_authz.py` | regressione H1/H2 |
| `backend/tests/test_b04ii_wallet_ledger.py` | FakeColl.update_many |
| `backend/tests/test_b04i_foundations.py` / `test_slice1_b01_b03.py` | regressione B04-I / Slice1 |

---

## 4. Endpoint (comportamento atteso)

| Endpoint | Comportamento |
|---|---|
| `GET /billing/wallet` | Main Admin idoneo / Super Admin read |
| `POST /billing/wallet/allocate\|revoke` | Main Admin **oppure** Super Admin + `extraordinary_reason` |
| `GET /billing/wallet/organization` | invariato (org-scoped) |
| `GET /billing/commercial/main-admin` | stato binding |
| `POST .../main-admin/transfer` (+ accept/cancel) | D08–D10, TTL 48h |
| `POST /ops/commercial-customers/main-admin` | D01 nominate |
| Ops revoke Main Admin | clear binding + audit |

---

## 5. Verifica eseguita da Cursor

```
pytest tests/test_b04_h2_main_admin.py \
       tests/test_b04_h1_h2_wallet_authz.py \
       tests/test_b04ii_wallet_ledger.py \
       tests/test_b04i_foundations.py \
       tests/test_slice1_b01_b03.py
→ 50 passed
```

CI remota PR #216: **success** (2 check runs `Backend billing / B04 unit`).

---

## 6. Checklist conformità per ChatGPT (D01–D12)

| ID | Decisione (breve) | Cosa verificare nel codice |
|---|---|---|
| D01 | Solo Ops nomina; no auto/`owner_id` | Ops endpoint + service; nessun fallback euristico |
| D02 | Multi-CC per user ok | Binding per documento CC, non ruolo globale |
| D03 | Membership non obbligatoria per autorità | Assert non richiede membership CRM |
| D04 | Fine membership ≠ revoke auto; perdita idoneità = blocco | Assert dinamico su account/ruolo |
| D05 | CC ceased: no admin operativa | Deny se CC non operabile |
| D06 | `group_admin` solo con nomina | Senza `main_admin_user_id` match → deny |
| D07 | Super Admin straordinario | `extraordinary_reason` obbligatorio su allocate/revoke |
| D08 | Cabina sempre + email best-effort | Notify path; email non blocca |
| D09 | TTL 48h | `pending_until` / reject expired |
| D10 | Transfer solo dopo accept | Fino ad accept resta titolare attuale |
| D11 | Perdita requisiti → blocco; no successione auto | Assert + Ops re-nominate only |
| D12 | Deny immediato endpoint | Guard su tutte le mutate/read admin wallet centrale |

---

## 7. Residui noti (non blocker di merge, se confermati)

1. UI Cabina per accept transfer: API pronta, schermata FE fuori scope.
2. Expiry transfer: lazy on propose/accept (non cron dedicato).
3. CC senza Main Admin: deny finché Ops nomina (intenzionale, D01/D12).

---

## 8. Prompt Founder → ChatGPT (incolla così)

```
Analizza il pacchetto B04-H2 Main Admin post-implementazione.
Documenti: B04-H2-MAIN-ADMIN-HANDOFF-CHATGPT.md + DECISIONS-CONFORMITY + TECHNICAL-DESIGN + RESIDUAL-IMPLEMENTATION-REPORT.
PR: https://github.com/mcnicastro-netizen/omnia2/pull/216 @ bb0ef5eb — CI verde.
Obiettivo: verdetto conformità D01–D12 ↔ codice; raccomandazione merge SÌ/SÌ CON FOLLOW-UP/NO.
Non riaprire decisioni. Non proporre H3/H4/legacy/B04-III. Una sola risposta strutturata come da §0 handoff.
```

---

## 9. Dopo analisi ChatGPT

- Se **SÌ** / **SÌ CON FOLLOW-UP**: Founder dice `merge` a Cursor (o mergea da GitHub).
- Se **NO**: Founder inoltra i blocker a Cursor con autorizzazione fix mirata.
- Nessun merge automatico da Cursor senza frase esplicita Founder.

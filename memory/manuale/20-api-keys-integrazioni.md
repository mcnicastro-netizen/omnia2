# Capitolo 20 · API Keys e integrazioni (Track B / API Gateway)

> **Versione**: v1.0 · Feb 2026 · Onestà documentale D-051
> **Codice coperto**:
> - `frontend/src/apps/immoweb/pages/ApiKeysPage.jsx` (351 righe · UI management chiavi)
> - `backend/apps/immoweb/api_keys.py` (199 righe · router `/api/app/api-keys`)
> - `backend/apps/v1/gateway.py` (router `/api/v1/*` consumer Bearer)
> - `backend/shared/auth/api_key.py` (issuance + hash + require_api_key)
> - `backend/shared/models/api_key.py` (ApiKeyInDB/Public/Create/IssueResponse + CreditAdjustment + ApiUsageLog)

> ⚠️ **Nota D-051 chiave**: le chiavi API OMNIA sono **Track B** (D-041/D-046) — un canale separato dal Track A (piani B2B + credit packages). **Pricing differente**: Track A = **€0,05/credito**, Track B = **€0,03/credito**. Documentato onestamente.

---

## 20.1 · Cos'è "API Keys e integrazioni"

**Track B**: pilastro per **partner esterni** (web agency, portali, gestionali) che vogliono integrare feature OMNIA (Valutatore UNI 10750, Comparatore Mutui, HAL Legal, Feed immobili) nei loro widget/CRM.

**Come funziona**:
1. Titolare emette una API key `omk_live_...` dalla `ApiKeysPage`
2. Assegna crediti iniziali (top-up successivi consentiti)
3. Copia il plaintext (mostrato **una sola volta**, poi hash SHA-256 in DB)
4. Il partner usa la chiave come `Authorization: Bearer omk_live_...` su `/api/v1/*`

---

## 20.2 · Dove trovarlo

**Route frontend**: `/app/api-keys` (ApiKeysPage.jsx, 351 righe).
**Sidebar**: voce `current="api-keys"` in AgencyShell.
**Permessi**: `agency_admin`, `super_admin`, `group_admin` (group_admin vede tutte le chiavi delle branch se `group_id` popolato).

---

## 20.3 · Emissione chiave · plaintext show-once

**Endpoint**: `POST /api/app/api-keys`
**Body**: `{name (obbligatorio 1-120), initial_credits (0-1M), partner_id (opz 60ch), allowed_origins (opz list)}`

**Formato plaintext**: `omk_live_<28 base32 chars>` (`api_key.py:22`).
**Hash storato**: SHA-256 hex digest (nessun plaintext persistito).
**Prefix visibile**: primi 12 char per search/UI (`key_prefix`).

**Response**:
```json
{"key": "omk_live_ABC...", "api_key": {"id":..., "name":..., "key_prefix":..., "credits_balance": 100, ...}}
```

**UI show-once box** (`ApiKeysPage.jsx:111-151`):
- Banner emerald con font monospace
- Bottone "Copia" (usa `navigator.clipboard.writeText`)
- Bottone × per chiudere → **plaintext scompare per sempre**
- Onestà: se l'utente perde il plaintext senza copiarlo, deve emettere una nuova chiave (nessun recovery)

---

## 20.4 · Credit wallet · top-up e ledger

**Endpoint**: `POST /api/app/api-keys/{id}/credits`
**Body**: `{delta (int -1M/+1M), reason (obbligatorio 1-200)}`

**Logica**:
- delta > 0 → top-up
- delta < 0 → deduct manuale (usato per rimborsi/correzioni)
- Guard `new_balance < 0` → HTTP 400 `balance_would_go_negative`
- Ogni movimento scritto in `api_credit_ledger` (Mongo): `{api_key_id, agency_id, delta, new_balance, reason, actor_user_id, created_at}`

**⚠️ Manuale v1**: nessuna auto-ricarica Stripe. Documentato in codice: "Manual until M4/Stripe" (`api_keys.py:154`).

**UI top-up** (`ApiKeysPage.jsx:70-81`): usa `prompt()` browser nativo — nessuna modale custom. Documentato onestamente.

---

## 20.5 · Allowed origins · widget CORS security (M2.5.3)

**Endpoint**: `PATCH /api/app/api-keys/{id}/origins`
**Body**: `{allowed_origins: List[str]}`

**Semantica**:
- Lista vuota `[]` → **nessuna restrizione origin** (chiave server-side, uso in backend)
- Lista popolata → solo widget su quei domini possono usare la chiave (Origin/Referer check)
- Wildcard supportato: `https://*.agenziarossi.it` matcha subdomain

**Pulizia input**: `str(o).strip().rstrip("/")` per ogni entry.

---

## 20.6 · Revoca chiave · no undo

**Endpoint**: `POST /api/app/api-keys/{id}/revoke`
**Effetto**: `is_active=false`, `revoked_at=now`. **Non reversibile** (per "riattivare" serve emettere nuova chiave con crediti trasferiti).

**UI**: bottone "revoca" rosso in tabella, con `confirm()` browser nativo (Cap. 20 UI non usa modale custom).

---

## 20.7 · Usage log · audit billing

**Endpoint**: `GET /api/app/api-keys/{id}/usage?limit=50` (max 500).
**Collezione**: `api_usage_log` con `{api_key_id, endpoint, credits_charged, status_code, error_code, created_at}`.

**⚠️ NO UI di consultazione v1**: l'endpoint esiste ma la ApiKeysPage NON ha un pulsante "Vedi utilizzi" — la tabella mostra solo `credits_balance` e `credits_spent` cumulativi. Backlog A-026 (UI usage detail per chiave).

---

## 20.8 · API Gateway `/api/v1/*` · endpoint consumer

**Auth**: `Authorization: Bearer omk_live_...` (header obbligatorio, no cookie).
**Router**: `apps/v1/gateway.py` con prefix `/v1`.

| Endpoint | Costo (crediti) | Cosa fa |
|----------|:---------------:|---------|
| `GET /api/v1/health` | 0 (no auth) | Ping |
| `GET /api/v1/me` | 0 | Ispezione chiave + saldo |
| `POST /api/v1/valuator` | **5** | Valutazione immobile UNI 10750 |
| `POST /api/v1/mortgages/compare` | **1** | Comparatore mutui |
| `POST /api/v1/legal/ask` | **3** | HAL Legal one-shot Q&A |
| `GET /api/v1/feed/properties` | 0 | Export inventory agenzia |
| `POST /api/v1/widgets/lead` | 0 | Cattura lead da widget |
| `POST /api/v1/staging/*` | ~15 (async) | Pipeline Virtual Staging |

**Charge/log**: dopo ogni request `charge_and_log()` scala i crediti, aggiorna `credits_spent`, scrive `api_usage_log`.

---

## 20.9 · Pricing Track B · 1 credito = €0,03

**⚠️ Differenza vs Track A (Cap. 19 §19.10)**:
- **Track A** (piani B2B + credit packages BillingPage): **1 credito = €0,05** (ratio 20 cred/€, no volume discount)
- **Track B** (API Gateway ApiKeysPage): **1 credito = €0,03** (rate menzionata in `ApiKeysPage.jsx:106` e `test_credentials.md`)

**Onestà**: le due economie di credito sono **contabilmente separate** v1. La chiave API ha il proprio `credits_balance` indipendente dal wallet della subscription B2B (`sub.wallet.balance`). Un titolare che ha un piano Pro con 1200 cr/mese NON vede quei crediti sulla chiave API — deve fare `POST /credits` per top-up separato.

**Costi tipici Track B** (esempi endpoint):
- Valutatore UNI: 5 cr = €0,15
- Comparatore mutui: 1 cr = €0,03
- HAL Legal: 3 cr = €0,09
- Feed inventory + widget lead: 0 cr (freebie)

---

## 20.10 · Widget embed · loader script

**Snippet** (mostrato in ApiKeysPage `docs` box):
```html
<script src="https://{host}/api/widgets/v1/loader.js"
  data-key="omk_live_..."
  data-widget="valuator"
  data-primary="#0b1e3f"
  data-lang="it"></script>
```

**Widget disponibili v1** (dal codice `apps/v1/gateway.py` + WidgetsShowcasePage): `valuator`, `mortgages`, `lead-capture` (altri: TBD).

**Anteprima**: `/it/widgets` (WidgetsShowcasePage) — pagina demo pubblica.

---

## 20.11 · Partner ID (D-046) · white-label attribuzione

**Campo**: `api_key.partner_id` (max 60 char, opzionale).
**Uso**: identificare il partner emittente (es. `webagency_test_001` per Widget Demo Web Agency di test, cfr. `test_credentials.md`).

**D-046**: OMNIA supporta **multi-partner white-label**. Un titolare può emettere N chiavi API, ognuna per un diverso partner tech (web agency A, gestionale B, portale C), tracciando l'attribuzione via `partner_id`. Nessuna funzione di reportistica per-partner in UI v1 (backlog A-027).

---

## 20.12 · Errori comuni

- **E1 · 401 unauthorized** su `/api/v1/*`: header `Authorization: Bearer omk_...` mancante o formato errato. Fix: verifica prefix `omk_live_`.
- **E2 · 402 insufficient_credits**: saldo chiave insufficiente per l'endpoint (5cr per valuator, ecc.). Fix: `POST /api/app/api-keys/{id}/credits` con delta positivo.
- **E3 · 403 origin_not_allowed**: chiave con `allowed_origins` popolato + widget in dominio non whitelisted. Fix: aggiorna origins via `PATCH /origins` o svuota lista per uso server-side.
- **E4 · 404 api_key_not_found** su revoke/top-up: la chiave non appartiene alla tua agency (o è stata già cancellata da super_admin). Fix: verifica ownership.
- **E5 · Persa la plaintext dopo emissione**: nessun recovery. Emetti nuova chiave + `POST /credits` con delta = saldo vecchia chiave + revoca vecchia.

---

## 20.13 · Limitazioni v1 (D-051)

- ❌ NO auto-ricarica Stripe (top-up manuale via `POST /credits`)
- ❌ NO UI usage detail per chiave (endpoint `/usage` esiste, no button)
- ❌ NO reportistica per-partner (`partner_id` tracciato ma nessun rollup UI)
- ❌ NO rotazione automatica chiavi (nessun cron scadenza)
- ❌ NO scoping per endpoint (una chiave con crediti può chiamare TUTTI gli endpoint v1)
- ❌ NO rate limit per-chiave (solo controllo saldo)
- ❌ NO IP whitelist (solo Origin/Referer per widget)
- ❌ NO webhook eventi (issued/revoked/depleted)
- ❌ NO modale custom top-up/revoca (usa `prompt()`/`confirm()` browser nativi)
- ❌ Pricing Track B (€0,03) NON esposto in BillingPage (solo menzionato nel subtitle ApiKeysPage)
- ❌ Wallet Track B **contabilmente separato** dal wallet B2B piani (Cap. 19 §19.10)
- ❌ Widget disponibili v1: solo `valuator`/`mortgages`/`lead-capture`. Altri TBD.

---

## 20.14 · Collegamenti

| Cap. | Modulo | Collegamento |
|:----:|--------|--------------|
| 13 | Team & Ruoli | Solo `agency_admin` owner o super_admin emette chiavi (`require_roles`) |
| 19 | Impostazioni | Pagina separata da Settings, sidebar dedicata `/app/api-keys` |
| 10 | HAL Agent CRM | HAL Legal è esposto via `/api/v1/legal/ask` (Track B, 3cr) — distinzione D-040 |
| 11 | Mutui | `/api/v1/mortgages/compare` (1cr) — feature Cap. 11 esposta a partner |
| 6 | Publishing | `/api/v1/feed/properties` (0cr) — feed inventory analogo al feed portale pubblico |
| 18 | Notifiche | `/api/v1/widgets/lead` (0cr) → trigger email `lead_notification` (Cap. 18) |

## 20.15 · Screenshot da produrre (placeholder)

- `[SCREEN: cap20-apikeys-empty]` — ApiKeysPage stato empty (no chiavi)
- `[SCREEN: cap20-apikeys-create-form]` — form emissione (name/credits/partner_id/origins)
- `[SCREEN: cap20-apikeys-issued-box]` — box verde plaintext show-once con "Copia"
- `[SCREEN: cap20-apikeys-list]` — tabella chiavi attive con prefix/saldo/spesi/stato/azioni
- `[SCREEN: cap20-apikeys-docs]` — box grigio "Come si usa" con Authorization header + endpoint + widget snippet

Totale: **5 screenshot Cap. 20**.

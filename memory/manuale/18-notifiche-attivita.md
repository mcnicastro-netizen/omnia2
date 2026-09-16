# Capitolo 18 · Notifiche e attività

> **Versione**: v1.1 · 16-Sep-2026 · Onestà documentale D-051 · sync D-084  
> **Codice coperto**:
> - `backend/shared/email/client.py` (Resend + SUBJECTS + mock mode)
> - `backend/shared/email/templates/*.html` (7 template × lingue)
> - `backend/shared/notifications/prefs.py` + `center.py` (**A-021** preferenze · **A-017** inbox)
> - `backend/apps/core/notifications_inbox.py` — `GET/POST /api/notifications*`
> - `backend/apps/core/auth.py` (welcome + password_reset + `GET/PATCH /auth/me/notification-preferences`)
> - `backend/apps/immoweb/invites.py` (agency_invite + in-app invite_accepted)
> - `backend/apps/immocloud/public_portal.py` (lead_notification email + in-app `lead_new`)
> - `backend/apps/immocloud/saved_searches.py` (saved_search_alert + in-app `saved_search_match`)
> - `backend/apps/v1/gateway.py` (widget lead → in-app)
> - `backend/apps/immoweb/cron.py` (super_admin trigger saved-searches)
> - `backend/apps/marketing/founders.py` (founders_welcome + founders_admin_notification)
> - `frontend/src/shared/components/NotificationBell.jsx` · `NotificationPreferencesPanel.jsx`
> - `frontend/src/apps/immoweb/components/AgencyShell.jsx` · `immocloud/.../CloudTopNav.jsx`
> - `frontend/src/components/ui/sonner.jsx` (toast)

> ⚠️ **Nota D-051 (v1.1)**: OMNIA **ha** campanella + inbox in-app (**A-017**) e UI preferenze email (**A-021**).  
> **Ancora NON esiste**: activity feed dashboard (**A-018**), push/SMS/WhatsApp, SSE real-time (polling 45s), digest titolare, retry queue email, webhook Resend delivery.

---

## 18.1 · Cos'è "Notifiche e attività" in OMNIA v1.1

**Definizione operativa**: "notifiche" = **email Resend** + **inbox in-app** (campanella) + **toast sonner**. "Attività" = **audit trail Mongo** (ancora senza UI timeline centralizzata).

**È**:
- Campanella in topbar ImmoWeb (sempre) e ImmobilCloud (se loggato) con badge non-lette, dropdown, mark-as-read / mark-all
- API `/api/notifications` + collezione Mongo `notifications`
- UI preferenze: canale email on/off, tipi email toggleabili, frequenza default saved-search (B2C)
- ~7 template email multi-lingua + cron saved-searches (super_admin)
- Audit collections per debug (non timeline utente)

**Non è (ancora)**:
- una pagina dedicata "Attività" / activity feed (**A-018**)
- push web/mobile, SMS, WhatsApp
- SSE/WebSocket (la campanella fa **polling ogni 45s**)

---

## 18.2 · Dove trovarlo

**In ImmoWeb (B2B)**:
- **Campanella** in topbar AgencyShell (accanto al language switcher) — `data-testid="notification-bell"`
- **Preferenze**: Impostazioni → pannello «Preferenze notifiche» (`NotificationPreferencesPanel`)
- Toast sonner sulle azioni
- KPI Dashboard (non sono un feed attività)

**In ImmobilCloud (B2C)**:
- **Campanella** in CloudTopNav se autenticato
- **Preferenze** in Area account (`/cloud/account`)
- Email + inbox in-app su match ricerca salvata

**API**:
```
GET  /api/notifications?limit=30&unread_only=false
GET  /api/notifications/unread-count
POST /api/notifications/{id}/read
POST /api/notifications/read-all
GET  /api/auth/me/notification-preferences
PATCH /api/auth/me/notification-preferences
```

---

## 18.3 · Canali di notifica attivi v1.1

| Canale | Stato | Sorgente | Delivery |
|--------|:-----:|----------|----------|
| **Email transazionali** | ✅ | Resend (o mock) | on-event + cron saved-search |
| **Inbox in-app (Bell)** | ✅ A-017 | Mongo `notifications` | polling 45s + open dropdown |
| **Toast in-app** | ✅ | `sonner` | feedback immediato azione |
| **Preferenze email UI** | ✅ A-021 | Settings / Account | patch preferenze |
| **Push (web/mobile)** | ❌ | schema accetta `"push"` | dead code — nessun sender |
| **SMS / WhatsApp** | ❌ | — | non integrati |
| **Activity feed** | ❌ | A-018 backlog | — |

**Nota `push`**: ancora accettato in schema ma non consegnato (D-051).

---

## 18.3b · Notification center in-app (A-017)

**UI**: `NotificationBell.jsx` — icona SVG, badge (max «99+»), dropdown «Notifiche», «Segna tutte lette», click riga → mark read + navigate a `link` (`/app/...` o `/cloud/...` con prefisso lingua).

**Document schema** (`notifications`):
`id`, `user_id`, `agency_id?`, `type`, `title`, `body`, `link`, `meta`, `read`, `created_at`, `read_at`

**Tipi emitter v1.1**:
| `type` | Quando | Destinatari tipici |
|--------|--------|-------------------|
| `lead_new` | Contatto ImmobilCloud o widget v1 | listing agent + owner/admin agenzia |
| `invite_accepted` | Accept invite | inviter (`invited_by`) |
| `saved_search_match` | Cron trova match | utente B2C (anche se email off) |

**Residuale (non ancora emitter)**: match on-read CRM, import XML, social, compliance HARD, DNS verify — backlog post-A-017.

**Indipendenza da email**: l’inbox si scrive anche se l’utente ha disattivato quel tipo email (prefs A-021). Email restano gated da `user_allows_email()`.

[SCREEN: cap18-bell-dropdown]

---

## 18.4 · Email transazionali · panoramica 7 template

**Provider**: Resend (via `resend-py`, chiamata `resend.Emails.send`). Chiave in env `RESEND_API_KEY`. Sender in env `EMAIL_FROM`. Se `RESEND_API_KEY` non è configurata → **mock mode**: nessun invio, log a stdout con prefix `[EMAIL MOCK]`.

**Lingua**: derivata da user (o parametro esplicito). Default `it`. Fallback su `it` se lingua richiesta non ha template.

**Template disponibili** (`backend/shared/email/templates/`):

| Template | Trigger | Lingue disponibili | Chiamato da |
|----------|---------|:------------------:|-------------|
| `welcome` | Registrazione B2B ImmoWeb | it, en, es | `apps/core/auth.py:131` |
| `password_reset` | POST `/api/auth/forgot-password` | it, en, es | `apps/core/auth.py:273` |
| `agency_invite` | Titolare invita collaboratore | it, en, es | `apps/immoweb/invites.py:102` (Cap. 13) |
| `lead_notification` | Compilazione form contatti su portale pubblico agenzia | it, en, es | `apps/immocloud/public_portal.py:750` |
| `saved_search_alert` | Cron saved-searches trova nuovi match | it, en, es | `apps/immocloud/saved_searches.py:245` |
| `founders_welcome` | Signup Founders (marketing page) | it | `apps/marketing/founders.py:103` |
| `founders_admin_notification` | Signup Founders → notifica admin OMNIA | it | `apps/marketing/founders.py:120` |

**Totale asset HTML in `templates/`**: 17 file (5 template × 3 lingue = 15 + 2 template italiani only = 17).

**Struttura template**: HTML con placeholder `{{key}}` sostituiti da `_render(tpl, variables)`. Assets di default iniettati automaticamente: `logo_url`, `public_base` (da env `OMNIA_LOGO_URL`, `OMNIA_PUBLIC_URL`).

**Subject line**: definiti in `SUBJECTS` dict (client.py:44-70), anch'essi con placeholder resolvibili (es. `agency_invite.it`: `"Sei stato invitato a unirti a {{agency_name}} su OMNIA"`).

---

## 18.5 · Template dettaglio · welcome + password_reset (Cap. 1 auth)

**`welcome`** [SCREEN: cap18-email-welcome]

- **Quando**: subito dopo `POST /api/auth/register` (ImmoWeb B2B).
- **A chi**: email registrata dal nuovo titolare agenzia.
- **Variabili**: `user_name`.
- **Subject**: "Benvenuto in OMNIA" · "Welcome to OMNIA" · "Bienvenido a OMNIA".
- **Delivery**: fire-and-forget (errore non blocca la registrazione, viene solo loggato).

**`password_reset`**

- **Quando**: `POST /api/auth/forgot-password` con email valida (idempotente: risposta identica anche se email non esiste, per non leakare).
- **A chi**: email della richiesta (se registrata).
- **Variabili**: `user_name`, `reset_url` (link con token TTL 1h).
- **Subject**: "Reimposta la tua password OMNIA".
- **Token TTL**: 1h (index Mongo TTL su `password_reset_tokens`).

---

## 18.6 · Template dettaglio · agency_invite (Cap. 13 team)

**`agency_invite`** [SCREEN: cap18-email-agency-invite]

- **Quando**: titolare (o super_admin) invia invito da `POST /api/agencies/me/invites`.
- **A chi**: email del collaboratore invitato.
- **Variabili**: `agency_name`, `inviter_name`, `role_label`, `invite_url` (magic-link con token nel fragment, TTL 7 giorni).
- **Subject**: "Sei stato invitato a unirti a {{agency_name}} su OMNIA".
- **Cross-ref**: Cap. 13 §13.5-13.7. Il token è nel fragment URL (`#token=...`), non nella query string (best practice OWASP: no leak nei referer).

---

## 18.7 · Template dettaglio · lead_notification (portale pubblico → agente)

**`lead_notification`** [SCREEN: cap18-email-lead-notification]

- **Quando**: un visitatore del portale pubblico agenzia (`immobilcloud.it/agenzia/{slug}`) compila il form contatto su una scheda immobile.
- **A chi**: email dell'agente owner dell'immobile (o titolare se agent non ha email registrata).
- **Variabili**: `property_title`, `lead_name`, `lead_email`, `lead_phone`, `lead_message`, `property_url`.
- **Subject**: "🔔 Nuovo lead da ImmobilCloud — {{property_title}}".
- **Fallback**: se manca `to_email` (agent senza email), notifica in log come `[LEAD ORPHAN]` — nessun retry, nessuna coda.

---

## 18.8 · Template dettaglio · saved_search_alert (B2C ricerche salvate)

**`saved_search_alert`** [SCREEN: cap18-email-saved-search]

- **Quando**: cron admin-triggered esegue `run_all_active_saved_searches()` (vedi §18.9).
- **A chi**: email di ogni utente B2C con `account_type="b2c"` E `"email" in notification_channels` E ricerca salvata `is_active=true` E almeno 1 match nuovo da `last_run_at`.
- **Variabili**: `user_name`, `search_name`, `match_count`, `matches_html` (tabella HTML con max 6 righe di immobili), `search_url` (link a `/{lang}/cloud/account`).
- **Subject**: "🔔 {{match_count}} nuovi immobili per la tua ricerca "{{search_name}}"".
- **Limitazione HTML**: `matches_html` mostra solo i primi 6 match; il totale è indicato nel subject.
- **Frequenza**: opzione utente `instant | daily | weekly` (default `daily`). ⚠️ v1 **il cron admin ignora la frequenza** e processa TUTTE le active saved_searches ad ogni chiamata. La "frequenza" è solo un flag salvato, non un filtro tempo. Documentato onestamente. Backlog **A-019 Frequency-aware cron** proposto per v1.1.

---

## 18.9 · Cron saved-searches (super_admin trigger)

**Endpoint**: `POST /api/app/cron/saved-searches/run-all` (super_admin only).

**Cosa fa**:
1. Itera ogni `saved_searches` con `is_active=true`.
2. Recupera l'utente proprietario. Se `account_type != "b2c"` o `"email"` non in `notification_channels`, salta l'email (aggiorna comunque `last_run_at`).
3. Costruisce filtro Mongo su `properties` (dai `filters` salvati) con `created_at > last_run_at`.
4. Recupera fino a 20 match, ordina per `created_at desc`.
5. Se >= 1 match, chiama `_send_alert_email()` con la digest HTML (max 6 righe visibili).
6. **Sempre** avanza `last_run_at = now` (anche in caso di skip email) per evitare replay di vecchi match quando l'utente riattiva il canale.

**Response body**: `{ok: true, searches_checked: N, emails_sent: N, total_matches: N}`.

**Come lanciarlo**:
- Manuale: `curl -X POST -H "Cookie: ..." /api/app/cron/saved-searches/run-all`
- Kubernetes CronJob esterno (non deployato v1)
- GitHub Actions (non configurato v1)

**⚠️ v1 non ha uno scheduler interno**: il cron NON parte da solo. Deve essere chiamato manualmente o da uno scheduler esterno. Backlog **A-020 Internal APScheduler saved-searches** proposto.

**Nota conflitto planning**: c'è un APScheduler già attivo (`publishing_scheduler` alle 06:00 UTC) per il publishing sync. È isolato dal cron saved-searches per separazione di responsabilità.

---

## 18.10 · Preferenze utente (A-021 · UI reale)

**Schema** (`User`):
- `notification_channels`: `email` | `push` (push non consegnato)
- `notification_email_types`: sottoinsieme di `welcome`, `agency_invite`, `lead_notification`, `saved_search_alert`
- `saved_search_frequency_default`: `instant` | `daily` | `weekly` (default ricerche nuove B2C)

**Sempre on (non disattivabili)**: `password_reset` (e sicurezza account).

**UI**:
- ImmoWeb → **Impostazioni** → pannello preferenze (senza freq. saved-search di default B2B)
- ImmobilCloud → **Account** → stesso pannello + frequenza digest ricerche

**API**: `GET/PATCH /api/auth/me/notification-preferences`  
Helper: `shared/notifications/prefs.py` → `user_allows_email(user, type)` usato da invite, lead email, cron saved-search.

**Inbox vs email**: disattivare `lead_notification` ferma l’**email**, non necessariamente la riga in campanella (gli emitter in-app non rileggono i tipi email).

---

## 18.11 · Toast in-app (feedback immediato)

**Libreria**: `sonner` (React, provider in `App.js` alla root). Componente shim in `frontend/src/components/ui/sonner.jsx`.

**Uso tipico**:
```javascript
import { toast } from "sonner";

toast.success("Immobile creato ✓");
toast.error("Errore durante il salvataggio");
toast("Info generica");
```

**Dove viene usato in ImmoWeb (esempi)**:
- `BillingPage.jsx`: `toast.success("Pagamento completato ✓")`, `toast.error("Portal non disponibile")`
- Ovunque ci sia una form submit (create/update/delete di immobili, clienti, match, ecc.)
- Feedback errori server (5xx, 4xx handled)

**Durata**: ~4-5 secondi (default sonner). Nessuna persistenza. Se l'utente non vede il toast (es. era fuori dallo schermo), è perso.

**Limitazioni**:
- Nessuna coda toast persistente (Ricarichi pagina → toast pending scompare).
- Nessuna "notifica non letta" (i toast non hanno stato "letto/non letto").
- Nessuna categoria/priorità (tutti i toast hanno stesso peso visivo, tranne `.success` verde e `.error` rosso).

---

## 18.12 · Audit trail interno · collezioni Mongo (non-UI)

**Cosa sono**: append-only log di eventi tecnici in collezioni Mongo dedicate. Nessuna UI centralizzata per browsarle. Servono per:
- Debug e post-mortem (super_admin via query diretta Mongo)
- Compliance / GDPR (privacy audit)
- Rate-limit / usage tracking (HAL)
- Sync history (publishing)

**Elenco (Feb 2026)**:

| Collezione | Modulo | Cosa registra | Cap. |
|------------|--------|---------------|:----:|
| `al_audit` | HAL Agent CRM | ogni chiamata `POST /api/app/al/chat` + `improve` (session_id, tokens, cost) | 10 |
| `al_legal_audit` | HAL Legal | ogni chiamata `POST /api/app/legal/ask` (used_credits, sources_count) | — |
| `match_audit` | Match | match propositions generate | 5 |
| `calendar_events` | Visite | visite programmate/completate | — |
| `domain_vault_events` | Domain Vault | sovereignty confirm + DNS verify + connect | 17 |
| `privacy_audit_events` | Privacy L1-L4 | cambio livello privacy immobile | 3 |
| `legal_kit_events` | Legal Kit | download PDF template legale | — |
| `social_posts` | Social Publisher | ogni push canale (success/failed) | 15 |
| `hal_knowledge_sessions` | HAL Knowledge | ogni domanda RAG (question, sources, confidence, tokens) | 12 |
| `publishing_events` | Publishing | attivazione portale, sync run, errori | 6 |

**Retention**: v1 nessuna policy di retention configurata (i log crescono indefinitamente in Mongo). Backlog **A-022 Retention policy audit collections** proposto (es. archivio dopo 90 giorni).

**Come consultare (super_admin only, no UI)**: query Mongo diretta.
```javascript
db.al_audit.find({user_id: "..."}).sort({created_at: -1}).limit(50)
```

---

## 18.13 · Dashboard KPI vs activity feed (chiarimento)

**La Dashboard ImmoWeb ha KPI counters**, non un activity feed.

**Cosa è**: 6 counter numerici aggiornati on-read (nessuna cache):
- Immobili attivi (`properties.count where status IN ("published", "reserved")`)
- Lead aperti (`clients_leads.count where status = "open"`)
- Nuovi match (7gg) (`match_audit.count where created_at >= now - 7d`)
- Visite programmate (7gg) (`calendar_events.count where event_type="visit" AND event_at BETWEEN now AND now+7d`)
- Collaboratori (numero membri accepted della `agency_id`)
- Inviti pendenti (numero invites `status="pending"`)

**Cosa NON è**:
- ❌ NON è una timeline "Ultime 20 attività" (chi ha fatto cosa quando)
- ❌ NON è una lista di eventi cliccabili con drill-down
- ❌ NON mostra chi ha creato l'ultimo immobile, chi ha risposto all'ultimo lead, quale portale ha fatto l'ultima sync
- ❌ NON aggrega gli audit trail interni descritti in §18.12

**Backlog**:
- **A-018 Activity feed dashboard**: aggregare `al_audit` + `match_audit` + `publishing_events` + `social_posts` + `calendar_events` in una lista sortabile "Ultime N attività della tua agenzia".

---

## 18.14 · Errori comuni

### E1 · "Non ricevo l'email di benvenuto / password reset"
- **Causa 1**: `RESEND_API_KEY` non configurata in `.env` backend → mock mode, l'email è **solo loggata**, non spedita.
  - Fix (dev): controlla i log backend, cerca `[EMAIL MOCK]`.
  - Fix (prod): configura `RESEND_API_KEY` nel deploy env.
- **Causa 2**: email finita in spam. Fix: whitelist mittente Resend (env `EMAIL_FROM`).
- **Causa 3**: Resend rifiuta (rate limit, dominio non verificato). Fix: log backend cerca `[EMAIL ERROR]`.

### E2 · "Ho invitato un collega ma non riceve l'email"
- Vedi Cap. 13 §13.11.
- Verifica in logs: `[EMAIL OK] to=... template=agency_invite ...`.
- Se `[EMAIL MOCK]` → configura Resend.

### E3 · "La saved-search non mi invia mai email"
- **Causa 1**: nessun super_admin ha lanciato il cron. Fix: manualmente `POST /api/app/cron/saved-searches/run-all`.
- **Causa 2**: non ci sono nuovi match da `last_run_at`. Verifica su Mongo `saved_searches.find({id: sid}, {last_run_at, last_match_count})`.
- **Causa 3**: utente ha disattivato il canale email o il tipo `saved_search_alert` nelle preferenze (Impostazioni / Account). Fix: riattiva da UI. L’inbox in-app può comunque ricevere la riga `saved_search_match`.
- **Causa 4**: la `saved_search.is_active = false`. Fix: `PATCH /api/cloud/me/saved-searches/{sid}` con `is_active=true`.

### E4 · "I toast in-app spariscono troppo velocemente"
- Comportamento di default di `sonner` (~4-5s). v1 non consente configurazione per toast singolo. Backlog **A-023 Toast duration tuning**.

### E5 · "L'email arriva ma le variabili sono letterali `{{user_name}}`"
- **Causa**: chiamata `send_email` senza passare la variabile richiesta dal template.
- Fix: super_admin apri il template HTML in `backend/shared/email/templates/`, individua le `{{var}}` e verifica che vengano passate nel `variables={}` dict del caller.

### E6 · "La campanella non mostra nulla / badge non aggiorna"
- **Causa 1**: sessione scaduta (401) — riloggia.
- **Causa 2**: polling 45s — apri il dropdown per refresh immediato.
- **Causa 3**: evento non ancora cablato come emitter (es. import XML) — vedi §18.3b residuale.

---

## 18.15 · Limitazioni v1.1 (D-051)

### Cosa NON esiste ancora

**Backend**:
- ❌ Nessun router `/activity` o activity feed aggregato (**A-018**)
- ❌ Nessun push sender (schema `push` = dead code)
- ❌ Nessuna coda retry email / webhook Resend delivery
- ❌ Nessuna digest quotidiana titolare (oltre saved_search)
- ❌ Cron saved-search senza scheduler interno (trigger super_admin) — **A-020**
- ❌ Emitter residui: match on-read, import XML, social, compliance, DNS
- ❌ SSE/WebSocket (solo polling)

**Frontend**:
- ❌ Nessuna pagina full-screen «Notifiche» (solo dropdown)
- ❌ Mute/snooze, moderazione admin

**Canali**: SMS, WhatsApp, Slack/Teams — no

### Cosa ESISTE (non più «limitazione»)
- ✅ Router `/api/notifications` + collezione Mongo
- ✅ Bell + unread badge (ImmoWeb + Cloud loggato)
- ✅ Preferenze UI canale/tipo (**A-021**)
- ✅ `password_reset` sempre on

---

## 18.16 · Collegamenti agli altri capitoli

| Cap. | Modulo | Perché correlato |
|:----:|--------|------------------|
| 1 | Primo accesso | Trigger `welcome` + `password_reset` |
| 3 | Immobili | `privacy_audit_events` |
| 5 | Match | `match_audit` + KPI (emitter in-app match ancora residuale) |
| 6 | Publishing | `publishing_events` |
| 10 | HAL Agent CRM | `al_audit` |
| 12 | HAL Knowledge | `hal_knowledge_sessions` |
| 13 | Team & Ruoli | `agency_invite` + in-app `invite_accepted` |
| 15 | Social | `social_posts` (no email / no bell v1.1) |
| 17 | Domain Vault | `domain_vault_events` |
| 19 | Impostazioni | pannello preferenze notifiche |

---

## 18.17 · Onestà documentale (D-051) · sintesi Cap. 18 v1.1

- **A-017 e A-021 shippati** (15-Sep-2026): campanella + preferenze UI — capitolo allineato 16-Sep (D-084).
- **A-018 activity feed** ancora assente: dashboard = KPI, non timeline.
- **`push` schema / non implementato**.
- Cron saved-searches: frequenza ora rispettata in parte (daily/weekly gate ore); **scheduler interno assente** (A-020).
- Email fire-and-forget; no webhook Resend.
- Audit Mongo non esposto in UI.
- Sync manuale obbligatorio ad ogni ship successivo: `MANUAL_SYNC.md` · **D-084**.

Backlog residuo Cap. 18: **A-018**, **A-019** (refine freq), **A-020**, **A-022**, **A-023** + emitter residuali A-017.

---

## 18.18 · Screenshot attesi

- `[SCREEN: cap18-bell-dropdown]` — topbar con badge + dropdown Notifiche
- `[SCREEN: cap18-prefs-settings]` — pannello preferenze in Impostazioni
- `[SCREEN: cap18-email-welcome]` — email welcome
- `[SCREEN: cap18-email-agency-invite]` — email agency_invite
- `[SCREEN: cap18-email-lead-notification]` — email lead
- `[SCREEN: cap18-email-saved-search]` — email saved search
- `[SCREEN: cap18-toast-success]` — toast success
- `[SCREEN: cap18-dashboard-kpi]` — dashboard KPI (non activity feed)

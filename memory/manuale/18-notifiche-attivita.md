# Capitolo 18 · Notifiche e attività

> **Versione**: v1.0 · Feb 2026 · Onestà documentale D-051
> **Codice coperto**:
> - `backend/shared/email/client.py` (117 righe · Resend + 5 SUBJECTS + mock mode)
> - `backend/shared/email/templates/*.html` (7 template × 3 lingue = fino a 17 file HTML)
> - `backend/apps/core/auth.py` (welcome + password_reset triggers)
> - `backend/apps/immoweb/invites.py` (agency_invite trigger)
> - `backend/apps/immocloud/public_portal.py` (lead_notification trigger)
> - `backend/apps/immocloud/saved_searches.py` (saved_search_alert + cron)
> - `backend/apps/immoweb/cron.py` (super_admin trigger)
> - `backend/apps/marketing/founders.py` (founders_welcome + founders_admin_notification)
> - `backend/shared/models/user.py` (`notification_channels: [email, push]` schema)
> - `frontend/src/components/ui/sonner.jsx` (toast provider)

> ⚠️ **Nota D-051 chiave**: OMNIA v1 **NON ha un modulo "Notifiche" dedicato** né un **feed "Attività recenti"**. Questo capitolo documenta onestamente:
> 1. Cosa ESISTE (email transazionali + toast + cron saved-search + audit trail interno)
> 2. Cosa NON esiste (Bell icon, unread badge, notification center, push, SMS, digest quotidiana, preferenze utente per canale, moderazione, retry queue)

---

## 18.1 · Cos'è "Notifiche e attività" in OMNIA v1

**Definizione operativa**: in OMNIA v1 "notifiche" = **email transazionali Resend + toast in-app sonner**. "Attività" = **audit trail interno Mongo** (non esposto in UI centralizzata).

**Non è**:
- una pagina "Notifiche" con lista campanella e badge non-lette
- un feed "Ultime attività della mia agenzia" nella dashboard
- un notification center con preferenze granulari per canale

**È**:
- ~7 tipi di email transazionali multi-lingua triggerate da eventi specifici (registrazione, password reset, invito team, nuovo lead, saved-search alert, founders signup, founders admin ping)
- toast temporanei via `sonner` come feedback delle azioni utente (successo/errore)
- job cron admin-triggered per digest saved-searches (instant/daily/weekly)
- collezioni Mongo con append di eventi tecnici (`al_audit`, `match_audit`, `calendar_events`, `domain_vault_events`, `privacy_audit_events`, `legal_kit_events`, `social_posts`, `hal_knowledge_sessions`, `publishing_events`, `al_legal_audit`) — usate per debug / traceability, **non per timeline utente**

**Perché non esiste una campanella o un feed attività v1**: scelta di prodotto — priorità Founder sui moduli core (immobili, clienti, match, publishing, staging, mutui, HAL). Backlog **A-017 Notification center in-app** e **A-018 Activity feed dashboard** proposti per v1.1.

---

## 18.2 · Dove trovarlo (spoiler: nessuna pagina dedicata)

**In ImmoWeb (B2B)**: nessuna voce di menu "Notifiche" o "Attività". Le uniche esperienze notification-like sono:
- Toast in-app immediato ad ogni azione (`toast.success`, `toast.error`)
- Sidebar KPI counters della Dashboard (Immobili attivi, Lead aperti, Nuovi match 7gg, Visite 7gg, Collaboratori, Inviti pendenti)
- Email che ti arriva nella casella personale

**In ImmobilCloud (B2C)**: nessuna voce "Notifiche". L'unica esperienza notification-like è:
- Email `saved_search_alert` quando la tua ricerca salvata produce nuovi match (frequenza scelta dall'utente: instant/daily/weekly)

**Nel router backend**: nessun `APIRouter(prefix="/notifications")` né `/activity` esiste in `/app/backend/apps/`. Cerca conferma:
```
$ grep "prefix=\"/notif" /app/backend/apps/**/*.py     # zero risultati
$ grep "prefix=\"/activity" /app/backend/apps/**/*.py  # zero risultati
```

---

## 18.3 · Canali di notifica attivi v1

| Canale | Stato v1 | Sorgente | Delivery |
|--------|:--------:|----------|----------|
| **Email transazionali** | ✅ attivo | Resend API (o mock se `RESEND_API_KEY` non configurata) | on-event + saved-search cron |
| **Toast in-app** | ✅ attivo | libreria `sonner` (React) | feedback immediato azione utente |
| **Push (web/mobile)** | ❌ NON attivo | schema `notification_channels` in `user.py` accetta `"push"` ma **nessun sender push implementato** | dead code v1 |
| **SMS** | ❌ NON attivo | Nessuna integrazione Twilio | mai chiamato |
| **WhatsApp Business** | ❌ NON attivo | Nessuna integrazione | mai chiamato |
| **In-app notification center** | ❌ NON attivo | Nessuna Bell icon, unread badge | mai reso |

**Nota `push` schema-ma-non-implementato**: il modello `User` accetta `notification_channels: ["email", "push"]` (`shared/models/user.py:50`). Un utente B2C può iscriversi con `["email", "push"]` e non ricevere errore, MA nessun servizio backend legge il valore `"push"` e lo consegna. È dead code v1 documentato per trasparenza (D-051).

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

## 18.10 · Preferenze utente (schema vs realtà)

**Schema**: `User.notification_channels: List[Literal["email", "push"]]` (`shared/models/user.py:50`, default `["email"]`).

**Realtà v1**:
- Solo il valore `"email"` viene letto e usato (dal cron saved-searches, §18.9).
- Il valore `"push"` è accettato in registrazione ma **non consumato** da nessun sender → dead code trasparente.
- **Nessuna UI** per modificare `notification_channels` post-registrazione (né in ImmoWeb `SettingsPage.jsx` né in ImmobilCloud `AccountDashboard.jsx`).
- **Nessuna granularità per tipo di email**: non puoi optare-in solo per `saved_search_alert` e opt-out da `password_reset`. Le email transazionali (welcome, password_reset, agency_invite, lead_notification, founders_*) sono **sempre inviate** indipendentemente dal `notification_channels` (sono fondamentali per l'uso del prodotto).
- Backlog **A-021 UI notification preferences** proposto per v1.1 (toggle per canale + granularità per tipo).

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
- **Causa 3**: utente ha `notification_channels: ["push"]` invece di `["email"]` (default è `["email"]`, ma se in registrazione B2C ha deselezionato). Fix: aggiorna Mongo direttamente (nessuna UI).
- **Causa 4**: la `saved_search.is_active = false`. Fix: `PATCH /api/cloud/me/saved-searches/{sid}` con `is_active=true`.

### E4 · "I toast in-app spariscono troppo velocemente"
- Comportamento di default di `sonner` (~4-5s). v1 non consente configurazione per toast singolo. Backlog **A-023 Toast duration tuning**.

### E5 · "L'email arriva ma le variabili sono letterali `{{user_name}}`"
- **Causa**: chiamata `send_email` senza passare la variabile richiesta dal template.
- Fix: super_admin apri il template HTML in `backend/shared/email/templates/`, individua le `{{var}}` e verifica che vengano passate nel `variables={}` dict del caller.

---

## 18.15 · Limitazioni v1 (elenco esaustivo · D-051)

### Cosa NON esiste v1

**Backend**:
- ❌ Nessun router `/notifications` (nessun endpoint tipo `GET /me/notifications`, `PATCH /notifications/{id}/read`, `DELETE /notifications/{id}`)
- ❌ Nessun router `/activity` o `/activity-feed`
- ❌ Nessuna collezione `notifications` o `activity_feed` in Mongo
- ❌ Nessun servizio "push sender" (nonostante `notification_channels` accetti `"push"`)
- ❌ Nessuna coda retry per email fallite (fire-and-forget)
- ❌ Nessun tracking delivery status (Resend restituisce `id`, ma nessun webhook `delivered`/`bounced`/`opened` configurato v1)
- ❌ Nessuna digest email diversa da saved_search_alert (no digest quotidiana per titolare agenzia con riepilogo lead/match/sync)
- ❌ Nessun scheduler interno per saved-search (deve essere triggerato super_admin manualmente)
- ❌ Nessun rate limit su send_email (a differenza di HAL Agent 60/h). Un client malizioso potrebbe forzare massa di password_reset.

**Frontend**:
- ❌ Nessuna Bell icon nella navbar
- ❌ Nessun contatore unread
- ❌ Nessuna pagina "Notifiche" o "Attività"
- ❌ Nessuna preferenza UI per canale (email/push toggle)
- ❌ Nessuna preferenza UI per tipo (opt-in/opt-out per welcome/agency_invite/lead_notification/saved_search_alert)
- ❌ Nessuna preferenza UI per digest frequency oltre a saved-search (instant/daily/weekly)
- ❌ Nessun mute/snooze temporaneo delle notifiche
- ❌ Nessuna moderazione (super_admin non può bloccare invii per abuso)

**Delivery channels non supportati**:
- ❌ SMS (nessuna integrazione Twilio o simili)
- ❌ WhatsApp Business (nessuna integrazione Meta Business)
- ❌ Push web (Service Worker + VAPID keys non configurati)
- ❌ Push mobile (nessuna app iOS/Android)
- ❌ Slack / Teams / Discord webhook (super_admin non può ricevere alert su Slack)
- ❌ Voice call (Twilio Voice non configurato)

**Analytics notifiche**:
- ❌ Nessun tracking open rate / click-through rate
- ❌ Nessun A/B test template
- ❌ Nessun rendering preview UI per super_admin ("come apparirà questa email prima di inviarla")

**Localizzazione**:
- ❌ `founders_welcome` + `founders_admin_notification` disponibili solo in italiano (D-051: non contano per multilingua completo)

---

## 18.16 · Collegamenti agli altri capitoli

| Cap. | Modulo | Perché correlato |
|:----:|--------|------------------|
| 1 | Primo accesso | Trigger `welcome` + `password_reset` |
| 3 | Immobili | Trigger `privacy_audit_events` audit interno (Privacy L1-L4) |
| 4 | Clienti | Nessun trigger email diretto v1 (i lead sono B2C portale, non gestione clienti B2B) |
| 5 | Match | Trigger `match_audit` interno + KPI counter Dashboard |
| 6 | Publishing | Trigger `publishing_events` interno |
| 10 | HAL Agent CRM | Trigger `al_audit` interno (usage/cost tracking) |
| 12 | HAL Knowledge | Trigger `hal_knowledge_sessions` (audit domande/risposte) |
| 13 | Team & Ruoli | Trigger `agency_invite` email (magic-link) |
| 15 | Social Publisher | Trigger `social_posts` audit interno (no email v1) |
| 17 | Domain Vault | Trigger `domain_vault_events` audit interno |
| 27 | MLS Network (placeholder) | Non implementato v1 — nessun trigger email |

---

## 18.17 · Onestà documentale (D-051) · sintesi Cap. 18

- **Nessun modulo Notifiche** dedicato v1. Documentato apertamente.
- **Nessun activity feed** v1. La dashboard è **KPI counters**, non timeline.
- **`push` in schema, non implementato**: dead code trasparente.
- **`frequency` in saved_searches, non filtro tempo**: il cron ignora la frequenza e processa TUTTE le active ricerche ad ogni chiamata (bug funzionale v1, documentato).
- **Cron saved-searches NON auto-scheduled**: deve essere manualmente triggerato super_admin.
- **Email fire-and-forget**: fallimenti solo loggati, nessuna coda retry.
- **Nessun rate limit** su send_email (rischio abuso password_reset).
- **Nessun webhook Resend** per delivery status: si sa solo se la chiamata Resend ha risposto OK (`id`), non se l'email è stata realmente consegnata o aperta.
- **Audit collections** presenti ma **NON esposte in UI**: query Mongo diretta solo per super_admin.
- **`founders_*` template solo it**: non conta per copertura multilingua.

Backlog qualità prodotto proposto Cap. 18: **A-017**, **A-018**, **A-019**, **A-020**, **A-021**, **A-022**, **A-023** (vedi `ASPETTI_DA_APPROFONDIRE.md` sezione aggiornamento post-Cap. 18).

---

## 18.18 · Screenshot da produrre (placeholder)

- `[SCREEN: cap18-email-welcome]` — email welcome renderizzata (client email)
- `[SCREEN: cap18-email-agency-invite]` — email agency_invite con magic-link
- `[SCREEN: cap18-email-lead-notification]` — email lead_notification con dettagli contatto
- `[SCREEN: cap18-email-saved-search]` — email saved_search_alert con digest HTML 6 righe
- `[SCREEN: cap18-toast-success]` — esempio toast success in ImmoWeb (creato immobile)
- `[SCREEN: cap18-toast-error]` — esempio toast error in ImmoWeb (payment fallito)
- `[SCREEN: cap18-dashboard-kpi]` — dashboard KPI counters (per dimostrare che NON è activity feed)

Totale: **7 screenshot Cap. 18** da aggiungere a `screenshots-index.md`.

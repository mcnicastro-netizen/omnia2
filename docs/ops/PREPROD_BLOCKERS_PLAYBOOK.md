# Scaletta bloccanti pre-produzione — istruzioni precise

**Data**: 20 Ottobre 2026  
**SoT correlati**: `OMNIA_COERENZA_SISTEMA.md` · `OMNIA_O6_GATE_CHECKLIST.md` · `memory/STRIPE_ONBOARDING.md` · `docs/ops/RAILWAY_DEPLOY.md` · `docs/ops/RESTORE_MANUAL.md` · `docs/audit/OMNIA_S3_METER_ECONOMIA.md`  
**Regola**: un blocco = chiuso solo con **Done quando** soddisfatto (LIVE o FIRMATO). Non bastano “configurato a mente”.

---

## Ordine vincolante

| Fase | Cosa | Dipende da | Chi |
|------|------|------------|-----|
| **0** | Merge fix codice + onestà UI | — | Agent + Founder merge |
| **1** | Decisioni commerciali (listino, e-sign, OpenAPI, SSL path) | — | **Solo Founder** |
| **2** | Email produzione + bak/restore su Railway | Fase 1 path storage | Founder vault + Agent |
| **3** | Stripe Live | API `api.` OK + email + listino firmato | Founder vault + Agent smoke |
| **4** | Go-live smoke FIRMATO | Fase 0–3 | Founder + Agent |

Non invertire: **Stripe Live dopo** email e listino, altrimenti soldi veri su claim non firmati.

---

## Fase 0 — Codice / merge (1–2 ore)

### 0.1 Merge fix Clienti
1. Apri PR `#51` (`cursor/gestionale-preprod-audit-8e9b`).
2. Merge in `main` (Founder).
3. Redeploy API Railway: `bash scripts/railway-deploy.sh` (vault `RAILWAY_TOKEN`).
4. **Done quando**: `GET $OMNIA_API_PUBLIC_URL/api/app/clients` → **200** con cookie login admin demo/prod.

### 0.2 Merge mandati D-129 (se vuoi la prova mandati in prod)
1. PR `#50` (`cursor/tre-promesse-mandati-8e9b`) → merge `main`.
2. Redeploy API + rebuild FE Vercel.
3. **Done quando**: `/it/app/mandate-opportunities` carica e `GET …/proof` → 200.

### 0.3 Onestà portali (verifica, non claim)
1. Login CRM → **Pubblicità su portali**.
2. Controlla tab **In arrivo**: devono esserci Immobiliare.it, Idealista, Casa.it.
3. Controlla tab **Attivabili ora**: solo i 7 `integration_ready=true` (Subito, Wikicasa, Bakeca, Trovocasa, Kijiji, Attico, Case24).
4. Se un portale top compare come attivabile → bug UI: apri issue/agent fix (BE già 409).
5. **Done quando**: screenshot Founder delle 3 tab + nessun 409 “sorpresa” su Imm/Idealista.

---

## Fase 1 — Decisioni Founder (obbligatorie, scritte)

Compila e incolla in chat (o firma in `OMNIA_S3_METER_ECONOMIA.md` §6).

### 1.1 Listino / storage (S3.1) — BLOCCA messaging prezzi
Leggi `docs/audit/OMNIA_S3_METER_ECONOMIA.md` §0–§4.

Rispondi esplicitamente:
```
S3.1 FIRMA
Data: …
Decisione listino: FERMO (€49/€99/€299 + addon €15/100GB) | REVISIONE: …
Path storage assunto: Volume Hetzner | Cloudflare R2 | altro: …
Note: …
Firma: Founder
```
**Done quando**: testo sopra in `DECISIONS.md` o §6 del doc S3 con data.

### 1.2 E-sign — scegli UNA strada
**A — Mock onesto (prod senza firma legale)**  
- Env: `ESIGN_PROVIDER=mock`  
- UI: copy «Firma demo / non legale» in modulistica (agent se manca).  
- **Done quando**: `GET /api/app/modulistica/esign/status` → `provider=mock` e UI non dice “firma digitale legale”.

**B — Yousign (consigliato IT)**  
1. Account [Yousign](https://yousign.com) → API key (sandbox poi prod).  
2. Vault Railway + Cloud:
   ```
   ESIGN_PROVIDER=yousign
   YOUSIGN_API_KEY=…
   YOUSIGN_API_BASE=https://api-sandbox.yousign.app/v3   # poi base prod
   ```
3. Redeploy API.  
4. Smoke: genera PDF modulistica → **Invia per firma** → link Yousign reale.  
5. **Done quando**: `esign/status` → `provider=yousign` + 1 documento `sent` con `sign_url` yousign.

**C — DocuSign** (alternativa): `ESIGN_PROVIDER=docusign` + `DOCUSIGN_ACCESS_TOKEN` + `DOCUSIGN_ACCOUNT_ID` + `DOCUSIGN_BASE_URL`.

### 1.3 OpenAPI / visure
```
OPENAPI: SPEGNI claim | SANDBOX only | LIVE
```
- **SPEGNI**: Railway `OPENAPI_ENABLED=false` + UI B2C «Presto» se serve.  
- **LIVE**: contratto OpenAPI prod +  
  ```
  OPENAPI_ENABLED=true
  OPENAPI_MODE=live
  OPENAPI_EMAIL=…
  OPENAPI_API_KEY=…   # chiavi PROD, non test
  ```
- **Done quando**: una visura di prova a pagamento (o spegnimento esplicito in UI).

### 1.4 Custom domain SSL — path post-Emergent
Decidi host FE che termina SSL:
```
SSL_PATH: Vercel custom domains | Cloudflare proxy (orange cloud) | altro: …
```
Poi agent aggiorna copy in `custom_domain.py` (rimuovere “pannello Emergent”) e runbook DNS.  
**Done quando**: 1 dominio agenzia dogfood con HTTPS verde (non solo TXT verify).

---

## Fase 2 — Infra (email + backup)

### 2.1 Email Resend produzione
1. [Resend](https://resend.com) → Domains → Add `omniarealestateecosystem.it` (o sottodominio `mail.`).  
2. Aggiungi record DNS che Resend mostra (SPF/DKIM).  
3. Attendi **Verified**.  
4. Railway Variables:
   ```
   RESEND_API_KEY=re_…     # già tipicamente presente
   SENDER_EMAIL=noreply@omniarealestateecosystem.it   # dominio verificato
   ```
5. Smoke: invita un collaboratore da `/it/app/members` → email arriva (non spam-only).  
6. **Done quando**: invite ricevuto + `SENDER_EMAIL` ≠ `onboarding@resend.dev`.

### 2.2 Backup / restore su Railway (prod)
Oggi: restore FIRMATO solo **non-prod** (`RESTORE_MANUAL.md`). Prod richiede rituale su host reale.

1. Verifica volume Railway montato: `/app/.backups` (vedi `RAILWAY_DEPLOY.md` §B.5).  
2. Founder Ops (super_admin): `GET /api/app/ops/overview` → `backup.status` = OK, non stale.  
3. Copia off-box (se configurata): presente e recente.  
4. Esegui **una** restore dry-run su DB **non** di clienti paganti (clone/staging), con:
   ```bash
   # su ambiente con accesso MONGO prod-clone — NON sul DB clienti senza OK Founder
   python scripts/restore_agency_nonprod.py --agency-id <test> --out /tmp/restore_check
   ```
5. Registra run in `docs/ops/runs/restore-prod-clone-YYYY-MM-DD.log`.  
6. **Done quando**: Founder firma riga «restore su clone prod OK» + bak OK in Ops per 7 giorni consecutivi.

---

## Fase 3 — Stripe Live (soldi veri)

Prerequisiti: Fase 1.1 firmata · Fase 2.1 email OK · DNS `api.` VALID · FE Vercel up.

1. Stripe Dashboard → completa **KYC** (azienda, IBAN, documento) se incompleto.  
2. Toggle **Live** (non Test).  
3. Copia `pk_live_…` e `sk_live_…` → **solo vault** Railway (+ Cursor Environment se serve rebuild).  
   **Mai in chat / mai in git.**  
4. Webhook **Live** nuovo (non riusare Test):
   - URL: `$OMNIA_API_PUBLIC_URL/api/billing/webhook`  
   - Eventi: almeno `checkout.session.completed`, `customer.subscription.*`, `invoice.*`  
   - Copia `whsec_…` → Railway `STRIPE_WEBHOOK_SECRET`  
5. Railway:
   ```
   STRIPE_ENABLED=true
   STRIPE_MODE=live
   STRIPE_PUBLISHABLE_KEY=pk_live_…
   STRIPE_SECRET_KEY=sk_live_…
   STRIPE_WEBHOOK_SECRET=whsec_…   # del webhook LIVE
   ```
6. Redeploy API.  
7. Catalogo live (da shell con `sk_live` in env):
   ```bash
   cd backend && python -m apps.billing.setup_stripe
   ```
8. Smoke pagamento **reale minimo** (Starter mensile o credito piccolo) con carta vera Founder → poi rimborso da Dashboard.  
9. Verifica webhook Live → 200 in Stripe → Delivery.  
10. B2C: un checkout listing/boost/staging da `/cloud` con carta vera (stesso webhook).  
11. **Done quando**:
    - `STRIPE_MODE=live` su Railway  
    - 1 sub B2B + 1 one-shot B2C OK  
    - webhook Live 200  
    - Founder messaggio: `STRIPE LIVE FIRMATO YYYY-MM-DD`

Riferimento dettagliato: `memory/STRIPE_ONBOARDING.md` § Live.

---

## Fase 4 — Go-live smoke (FIRMATO)

Checklist da spuntare in chat:

```
GO-LIVE SMOKE
[ ] Login CRM prod
[ ] Lista Clienti 200
[ ] Crea immobile + foto
[ ] Pubblica su ImmobilCloud
[ ] Contatto da /cloud → lead in CRM
[ ] Match / richieste ok
[ ] Portali: solo ready attivabili
[ ] Invite email arriva
[ ] Checkout B2B live (o già fatto Fase 3)
[ ] Ops bak OK
[ ] esign status = scelta Fase 1.2
[ ] OpenAPI = scelta Fase 1.3
Firma Founder: …
```

**Done quando**: checklist completa + firma.

---

## Fuori scaletta (non bloccanti, dichiarare)

| Voce | Azione |
|------|--------|
| Idealista / Immobiliare.it integrazione | Progetto commerciale + tubo feed — **dopo** go-live |
| Academy M6 | Non claimare |
| WhatsApp CRM tipo Arcanis | Non in P0 |
| Analytics A/B | Debito |

---

## Come usare questa scaletta con l’agent

Messaggi Founder tipici (copia-incolla):

1. `fase 0: merge #51 e verifica clients 200 su api.`  
2. `fase 1: ecco firma S3.1 … / scegli e-sign B Yousign / OpenAPI SPEGNI / SSL Vercel`  
3. `fase 2: configura SENDER_EMAIL su dominio verificato e smoke invite`  
4. `fase 3: vault live pronto — procedi setup_stripe + smoke` *(solo dopo aver messo i secret in vault)*  
5. `fase 4: esegui go-live smoke e dimmi cosa manca`

L’agent **non** inventa chiavi Live: le legge solo dal vault dopo che le hai inserite tu.

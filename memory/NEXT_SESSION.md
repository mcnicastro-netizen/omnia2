# Prossima sessione — programma passi

**Aggiornato**: 15 Settembre 2026 (sera) — pausa Founder · ripresa domani  
**Stato base**: Sprint 1→4 **CONCLUSO**. Post-programma su `main` (ultimo ship: **A-017** Notification center).

---

## Ripresa domani (checklist 60 secondi)

1. `bash scripts/omnia-stack.sh ensure` (o `status`)
2. Ports Cursor → **omnia-preview :43123**
3. Smoke: login Founder · campanella Notifiche in topbar CRM
4. Questo file → Founder dice **«vai»** sull’ID

**Non ripartire da** Stripe live / webhook / Emergent / Vercel.

---

## Dove siamo (fotografia)

| Area | Stato |
|------|:-----:|
| Sprint 1→4 + conclusione formale | ✅ |
| Modulistica + Yousign (parziale) | ✅ |
| OpenAPI.it visure sandbox (Fascicolo) | ✅ |
| Visura B2C carta Stripe €4,90 | ✅ D-083 (test) |
| Preview `omnia-stack` :43123 | ✅ |
| P1 A-006 / A-007 / A-013 / A-017 / A-021 | ✅ |
| Demo prodotto self-serve | ❌ **A-025** |
| Stripe **live** + webhook + deploy | ⏸️ **DOPO Vercel** (decisione 15-Sep) |
| Emergent come host produzione | ❌ Founder non vuole più usarlo |
| Deploy target | **Vercel** (fine percorso, non ora) |
| M6 Academy / M4 MLS commerciale | ⏸️ bloccati |

---

## Decisione Stripe (15-Sep · Founder)

- KYC / 2FA Stripe affrontati; Founder ha (o sta ottenendo) chiavi **live** da tenere in password manager — **non in chat**.
- **Webhook `whsec` e config live**: rimandati a **dopo deploy Vercel**.
- Dominio target webhook a regime: `https://api.omniarealestateecosystem.it/api/billing/webhook` (oggi `api.` non up).
- Ambiente attuale resta **`STRIPE_MODE=test`** in `.env` — corretto.
- **A-014** non è il prossimo task operativo finché non c’è URL pubblico Vercel.

Dettaglio: `memory/STRIPE_ONBOARDING.md`.

---

## Ordine consigliato alla ripresa

### Backlog con «vai» (prodotto — non deploy)
| Priorità | ID | Cosa | Note |
|:-:|---|---|---|
| 1 | **A-025** | Architettura **demo prodotto** | P0 GTM · sessione dedicata |
| 2 | A-008 | Cambio ruolo membro | P2 · dopo A-007 |
| 3 | A-018 | Activity feed dashboard | P2 · riusa A-017 |
| — | A-004 | Landing `/it/agenzie` + widget | dopo/con demo |

### Solo a fine percorso (non mescolare con feature)
1. Deploy **Vercel** (+ DNS `api.` / `app.` / `cloud.`)
2. **A-014** Stripe live: env `pk_live`/`sk_live`/`whsec` + `setup_stripe` + webhook
3. OpenAPI.it prod · conferma listino visura €4,90 · Yousign key

### Blocchi strategici
- Repo GitHub privato OMNIA
- Società → M4 MLS / SISTER / QTSP
- M6 Academy

---

## Ultimo ship (ieri / oggi)

- **A-017** Notification center: `/api/notifications`, Bell CRM + Cloud, emitters lead/invite/saved-search, test ok, smoke UI ok.

---

## Comandi utili

```bash
bash scripts/omnia-stack.sh ensure|watch|status|rebuild
# Preview: http://127.0.0.1:43123
# Health:  http://127.0.0.1:43123/healthz
```

Credenziali: `memory/test_credentials.env` (gitignored).

---

## Regola di ripresa
Questo file → `ASPETTI_DA_APPROFONDIRE.md` → Founder: **«vai»** sull’ID.  
**Stripe / Vercel / webhook = capitolo a parte, a fine.**

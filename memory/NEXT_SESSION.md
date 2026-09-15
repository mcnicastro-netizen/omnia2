# Prossima sessione — programma passi

**Aggiornato**: 15 Settembre 2026 (pausa Founder)  
**Stato base**: Sprint 1→4 **CONCLUSO** (`PROGRAMMA_CONCLUSIONE.md`). Lavoro post-programma già in `main`.

---

## Dove siamo (fotografia)

| Area | Stato |
|------|:-----:|
| Sprint 1→4 + conclusione formale | ✅ |
| Modulistica + Yousign (M5.S7/S8 parziale) | ✅ |
| OpenAPI.it visure sandbox (CRM Fascicolo) | ✅ |
| Visura B2C carta Stripe €4,90 (`/cloud/visura`) | ✅ D-083 |
| Preview stabile `omnia-stack` :43123 | ✅ |
| P1 A-006 / A-007 / A-013 / A-021 | ✅ |
| Demo prodotto self-serve | ❌ A-025 (rinviata) |
| Stripe **live** + KYC Founder | ⏸️ |
| M6 Academy / M4 MLS commerciale | ⏸️ bloccati |

---

## Ordine consigliato alla ripresa

### 1) Operativo / accesso (prima di qualsiasi feature)
1. `bash scripts/omnia-stack.sh ensure` (o `status`)
2. Aprire area riservata via **Cursor Ports → omnia-preview (43123)** — non tunnel flaky
3. Smoke: login Founder + Fascicolo visura + `/it/cloud/visura` catalog

### 2) Backlog P1 rimasti (con «vai»)
| Priorità | ID | Cosa | Note |
|:-:|---|---|---|
| 1 | **A-017** | Notification center (campanella + inbox) | Effort L — alto valore CRM |
| 2 | **A-014** | Billing UI + Stripe **live** | Serve KYC + chiavi live Founder |
| — | A-008 | Cambio ruolo membro | P2, naturale dopo A-007 |

### 3 | P0 GTM (sessione dedicata, non mescolare)
| ID | Cosa |
|---|---|
| **A-025** | Architettura **demo prodotto** (cavallo di Troia) — video / `/it/demo` / guest — **prima** di cold outreach |
| A-004 | Landing `/it/agenzie` + widget (dopo o insieme alla demo) |

### 4) Integrazioni già avviate — chiusura “production ready”
1. **OpenAPI.it** — passare da sandbox a prod quando wallet/abbonamento live; ruotare API key
2. **Yousign** — verificare scadenza key; campo firma bottom-right già ok
3. **Visura B2C €4,90** — Founder conferma listino o aggiusta in `b2c_products.py` / `PRICING_B2C.md`
4. Webhook Stripe B2C in ambiente deploy (non solo test locale)

### 5) Blocchi strategici (solo dopo decisione Founder)
- Repo GitHub privato OMNIA (backup fuori Cursor)
- Società → M4 MLS commerciale / account SISTER / QTSP ISV firma a scala
- M6 Academy

---

## Comandi utili

```bash
bash scripts/omnia-stack.sh ensure|watch|status|rebuild
# Preview: http://127.0.0.1:43123  (+ Ports Cursor)
# Health:  http://127.0.0.1:43123/healthz
```

Credenziali test: `memory/test_credentials.env` (gitignored).

---

## Regola di ripresa
Non ripartire da «Sprint 2 NEXT».  
Alla ripresa: **questo file** → poi `ASPETTI_DA_APPROFONDIRE.md` → Founder dice «vai» sull’ID scelto.

# Ambiente di prova B2C — privato vende + HAL + staging + Stripe + vetrina

**Scopo**: dogfood da privato (altra email) **prima** del gestionale agenzia.  
**Stack**: Cloud Agent / `omnia-stack` · Stripe **Test** · auto-approve annunci in sandbox.

---

## 1. Avvio ambiente

```bash
bash scripts/prepare_b2c_founder_sandbox.sh
```

Output tipico: URL pubblico trycloudflare, link registrazione, `Stripe Test: True`, auto-approve ON.

Flag: `OMNIA_B2C_SANDBOX_AUTO_APPROVE=true` in `backend/.env`  
→ al **Pubblica / Invia** l’annuncio diventa subito `active` sul portale (niente coda moderazione). In produzione lasciare `false` / assente.

---

## 2. Percorso Founder (UI)

Usa un’email **diversa** da Founder/demo admin (es. Gmail personale o `tuonome+privato@…`).

| Passo | Dove | Cosa fare |
|------:|------|-----------|
| 1 | `/it/cloud/register?intent=sell` | Registrati come privato · spunta GDPR · intent «vendi» |
| 2 | `/it/cloud/account/sell` | Nuovo annuncio: titolo, città, prezzo, mq, foto (≥1), telefono/WhatsApp |
| 3 | Stesso form | **HAL** (✨) su titolo e descrizione → applica testo migliorato |
| 4 | Salva + **Pubblica** | Con auto-approve → subito live |
| 5 | Staging | Pannello Virtual Staging → paga **€0,90** (Stripe Test `4242…`) → torna su Sell → foto arredata |
| 6 | Vetrina | Boost **Vetrina 30gg €14,90** (o Premium/TOP) → carta Test |
| 7 | Portale | `/it/cloud/search` · filtra città · apri scheda · verifica badge/foto/contatto |

**Carta Stripe Test**: `4242 4242 4242 4242` · scadenza qualsiasi futura · CVC qualsiasi · 3DS: completa se richiesto.

---

## 3. Cosa stai verificando

| Area | Atteso |
|------|--------|
| Registrazione B2C | `account_type=b2c`, redirect area Vendi |
| HAL improve | Bottone ✨ → testo più lungo/pulito (Gemini) · gratis in-app |
| Foto | Upload JPEG/PNG/WebP · max 8 MB · fino a 30 |
| Virtual Staging | Checkout → job fal.ai → variante su annuncio · disclosure AI in scheda |
| Vetrina / Premium / TOP | Ranking più alto in search mentre `boost_until` è futuro |
| Scheda pubblica | Visibile in ricerca · contatti privati · no tools gestionale |

---

## 4. Listino one-shot rilevante (carta, mai crediti)

| SKU | Prezzo |
|-----|-------:|
| Virtual Staging / foto | €0,90 |
| Vetrina 30gg | €14,90 |
| Premium 30gg | €19,90 |
| TOP 30gg | €29,90 |

Vedi `memory/PRICING_B2C.md`.

---

## 5. Se qualcosa non torna

| Sintomo | Check |
|---------|--------|
| Tunnel 000 | `bash scripts/omnia-stack.sh ensure` |
| Stripe off | `STRIPE_ENABLED=true` + chiavi `sk_test` / `pk_test` |
| HAL 502/skip | `GEMINI_API_KEY` presente nel processo API |
| Staging non parte | `FAL_KEY` · annuncio con ≥1 foto · pagamento `paid` |
| Annuncio non in search | auto-approve ON? oppure Approva da `/it/app/moderation` (super_admin) |
| Redirect Stripe su localhost | apri sempre l’URL **trycloudflare** del prepare script |

---

## 6. Moderazione manuale (se auto-approve OFF)

1. Login Founder → `/it/app/moderation`  
2. Approva l’annuncio in coda  
3. Ricontrolla `/it/cloud/search`

---

## 7. Fuori scope di questo sandbox

- Gestionale agenzia (`/it/app/…` come titolare) → sessione successiva  
- Accesso atti (D-125) → ancora «Presto disponibile»  
- Stripe **Live** → solo dopo KYC

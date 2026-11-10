# Programma · martedì 10 Novembre 2026 (Europe/Rome)

**Obiettivo del giorno**: dogfood **reale** Nicastro Immobiliare → Storia verso **8**.  
Founder registra l’agenzia con **credenziali reali**, importa immobili, chiede restyling, prova i tool.  
**Freccia**: Storia + provisioning assistito (Ops). Niente Stripe self-serve B2B (O6 chiuso).

**SoT**: `PROGRAMMA_VERSO_8.md` · `NEXT_SESSION.md` · questo file.

---

## Percorso Founder (ordine consigliato)

### 0 · Prep Ops (super_admin, tu)

1. Login Founder su app → **Ops** (`/it/app/ops`).
2. Se lo slug `nicastroimmobiliare` è occupato dal seed: **Purge shell force** (pannello Dogfood).
3. Smoke: `GET $OMNIA_API_PUBLIC_URL/api/health` → ok.

### 1 · Registrazione reale

1. Esci / finestra privata → **Registrati** con email/password **reali**.
2. Completa onboarding → crea agenzia **Nicastro Immobiliare** (slug tipo `nicastroimmobiliare`).
3. Torna come **super_admin** → Ops → cerca l’agenzia → **Concedi piano Pro** + **≥2000 crediti** (nota `dogfood_nicastro_reale`).
   - Stesso pannello vale per **qualsiasi** altra agenzia (email/slug/id).
   - API: `POST /api/app/ops/grant-agency-plan` · CLI: `scripts/grant_agency_plan.py`.

### 2 · Import + sito (Blocco A/B programma Storia)

1. Import XML / inserimento immobili (quota Pro = 200 proprietà).
2. Brand Studio: scegli tema restyling (gallery 8 inclusa in Pro — niente Stripe template).
3. Opz. Cattura sito / clone da `www.nicastroimmobiliare.it` → `clone_ready`.
4. MLS on → smoke home/lista/scheda → MLS off → smoke (4 stati × temi se tempo).

### 3 · Tool marathon (online)

Prova in ordine tipico (crediti già grantati):

| Area | Cosa toccare |
|---|---|
| Immobili / Fascicolo | upload foto/docs, privacy L1–L4 |
| Staging | 1–2 job Nano/standard |
| Micro-tour / video | 1 clip (costo crediti D-147) |
| HAL | improve scheda + Guida HAL |
| Portali | preview feed / publishing se configurato |
| Domain Vault | check dominio reale |
| MLS | join/leave + box sito |
| www | Perché OMNIA paperless (D-148) — claim onesti |

### 4 · Chiusura

1. Diario `docs/audit/portale-diario/2026-11-10.md` + voto Storia.
2. Gap list onesti (cosa ha rotto / cosa manca).
3. Altre agenzie dogfood: stesso grant Ops, senza nuovo codice.

---

## DoD Storia ≈ 8 (oggi)

- [ ] Agenzia Nicastro **reale** su piano Pro assistito + crediti
- [ ] Immobili trasferiti / importati
- [ ] Restyling tema applicato (gallery 8)
- [ ] Almeno 3 tool non-trivial usati online con esito ok
- [ ] Paperless www senza claim inventati

---

## Fuori scope oggi

- Stripe entitlement template (D-151) — Pro include gallery
- Vision crawl clone millimetro
- GTM-01 · aprire self-serve O6

---

## Checklist Founder

> «Registro Nicastro con le mie credenziali → Ops mi dà Pro gratis → importo case → restyling → provo i tool online.»

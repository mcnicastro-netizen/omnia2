# Prossima sessione — programma passi

**Aggiornato**: 6 Novembre 2026 — **D-147** Kling 30 cr · **D-146** www · **D-145** Nicastro  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Environment**: omnia2 (esiste; UI Dashboard può glitchare — non Start Fresh)

**Sicurezza Railway**: runbook [`docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md`](../docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md) · stato 🟡 core done.  
Smoke: `GET $OMNIA_API_PUBLIC_URL/api/health` → ok/db=ok.  
Vault: [`memory/CLOUD_SECRETS_INVENTORY.md`](./CLOUD_SECRETS_INVENTORY.md).

---

## ⛔ Prima di andare in produzione (obbligatorio)

Founder 05-Nov-2026: **controllare i margini prima del go-live**, non dopo.

1. Riaprire [`PRICING_OMNIA.md`](./PRICING_OMNIA.md) § «Controllo perdite» + [`PRICING_B2C.md`](./PRICING_B2C.md).
2. Allineare **codice** (`CREDIT_COSTS` / checkout B2C) ↔ listino: niente SKU sotto COGS (lezione Kling @ 10 cr → **D-147** a 30 cr).
3. **Visura** e **APE**: verificare fee partner (OpenAPI / fatture) ≤ prezzo listino; se fee > prezzo → alzare prezzo o sospendere SKU.
4. Smoke Founder Ops `/app/ops` (COGS vs crediti scalati) su ambiente staging/prod controllato.
5. Solo dopo OK Founder su questa checklist → dichiarare go-live commerciale.

---

## 🎯 SoT freccia

| Ruolo | Doc |
|-------|-----|
| Freccia | [`docs/audit/OMNIA_COERENZA_SISTEMA.md`](../docs/audit/OMNIA_COERENZA_SISTEMA.md) |
| **Primo cliente B2B** | **D-145** Nicastro Immobiliare (slug `nicastro-immobiliare`) |
| **Vetrina www** | **D-146** ✅ live (Chi siamo · Perché OMNIA · no Cerca casa) |
| **Kling crediti** | **D-147** 30 cr / €1,50 · listino [`PRICING_OMNIA.md`](./PRICING_OMNIA.md) v3.2 |
| Portale | D-139…D-144 ✅ |
| Clone sito | D-023/D-130 + A-037 aperti (dopo dogfood gestionale) |

---

## Login gestionale (produzione)

| Chi | Email | Note |
|-----|-------|------|
| **Titolare Nicastro** | `titolare@nicastroimmobiliare.it` | password seed `NicastroDemo2026!` — **cambia subito** |
| Founder Ops | `ADMIN_EMAIL` (vault) | `super_admin` — dopo deploy D-145 membership → Nicastro |
| Demo GTM | ~~`demo.admin@…`~~ | **cancellato** 06-Nov · shell `demo-agency-001` da retire Ops post-deploy |

URL tipico ImmoWeb: `https://app.omniarealestateecosystem.it` (login B2B).  
Sito white-label: `/api/p/nicastro-immobiliare/`.  
Vetrina istituzionale: `https://omniarealestateecosystem.it/it` (**D-146**).

**Post-merge D-145**: Founder o agent → `POST /api/app/ops/retire-demo-agency` (cookie super_admin) per wipe shell demo + grant Pro.

---

## Filo prodotto

1. **06-Nov:** Nicastro = primo cliente reale (CRM vuoto) · demo.admin erased · codice retire demo.
2. **06-Nov:** www vetrina D-146 chiusa · audit link PASS · docs/HAL v0.53.
3. **06-Nov:** coda video/pricing chiusa — #93 persist · #94 soft mail · #95 elimina video · #96/#D-147 Kling 30 cr.
4. Dogfood gestionale ImmoWeb su Nicastro (loop mattina agente).
5. Poi: A-037 / D-130 clone sito (man mano) · gate pre-prod margini Visura/APE.

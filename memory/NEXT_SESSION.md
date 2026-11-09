# Prossima sessione — programma passi

**Aggiornato**: 9 Novembre 2026 — **closeout filo verso-8** · HAL/manuale allineati · prossimo = dogfood Storia  
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
| **Verso-8** | [`PROGRAMMA_VERSO_8.md`](./PROGRAMMA_VERSO_8.md) — Manut/SaaS/Velocità/Coerenza = **8** · Storia **~7,8** |
| **Primo cliente B2B** | **D-145** Nicastro Immobiliare (slug `nicastro-immobiliare`) |
| **Vetrina www** | **D-146** + **D-148** paperless in Perché OMNIA |
| **Kling crediti** | **D-147** 30 cr / €1,50 · listino [`PRICING_OMNIA.md`](./PRICING_OMNIA.md) v3.2 |
| Portale | D-139…D-144 ✅ |
| Migrazione sito | **D-149** casi 1–2 ✅ (#136) · clone_ready · restyling coda |
| Template pack | **D-150/D-151** gallery 8 (#137) · €99/€199 · Stripe entitlement ⏳ |
| **Prossimo** | **Dogfood Storia Nicastro** (Onda 1) — 2 temi MLS on/off + paperless |

---

## Login gestionale (produzione)

| Chi | Email | Note |
|-----|-------|------|
| **Titolare Nicastro** | `titolare@nicastroimmobiliare.it` | password seed `NicastroDemo2026!` — **cambia subito** |
| Founder Ops | `ADMIN_EMAIL` (vault) | `super_admin` — dopo deploy D-145 membership → Nicastro |
| Demo GTM | ~~`demo.admin@…`~~ | **cancellato** 06-Nov · shell `demo-agency-001` da retire Ops post-deploy |

URL tipico ImmoWeb: `https://app.omniarealestateecosystem.it` (login B2B).  
Sito white-label: `/api/p/nicastro-immobiliare/`.  
Vetrina istituzionale: `https://omniarealestateecosystem.it/it` (**D-146** + paperless **D-148**).

**Post-merge D-145**: Founder o agent → `POST /api/app/ops/retire-demo-agency` (cookie super_admin) per wipe shell demo + grant Pro.

---

## Priorità (Founder 09-Nov)

1. ✅ Filo manut+SaaS onde 2–10 + gallery 8 + D-149.
2. ✅ Closeout HAL/manuale Cap.00/08/27 + YAML + reindex.
3. **Prossimo Storia**: dogfood Nicastro (Onda 1).
4. Opz.: Stripe D-151 entitlement · clone Vision crawl · GTM-01.

## Filo prodotto

1. **09-Nov chiuso:** verso-8 Manut/SaaS · #136/#137 · docs/HAL closeout.
2. **Prossimo:** dogfood Storia · clone full polish · restyling operativo.
3. **06-Nov chiuso:** Nicastro · www · Kling · staging split.

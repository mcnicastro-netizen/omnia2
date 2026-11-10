# Prossima sessione — programma passi

**Aggiornato**: 10 Novembre 2026 — **dogfood Nicastro reale** + Ops grant piano gratis  
**Programma giorno**: [`PROGRAMMA_2026-11-10.md`](./PROGRAMMA_2026-11-10.md)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Environment**: omnia2 (esiste; UI Dashboard può glitchare — non Start Fresh)

**Sicurezza Railway**: runbook [`docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md`](../docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md) · stato 🟡 core done.  
Smoke: `GET $OMNIA_API_PUBLIC_URL/api/health` → ok/db=ok.  
Vault: [`memory/CLOUD_SECRETS_INVENTORY.md`](./CLOUD_SECRETS_INVENTORY.md).

---

## ⛔ Prima di andare in produzione (obbligatorio)

Founder 05-Nov-2026: **controllare i margini prima del go-live**, non dopo.

1. Riaprire [`PRICING_OMNIA.md`](./PRICING_OMNIA.md) § «Controllo perdite» + [`PRICING_B2C.md`](./PRICING_B2C.md).
2. Allineare **codice** (`CREDIT_COSTS` / checkout B2C) ↔ listino.
3. **Visura** e **APE**: fee partner ≤ listino.
4. Smoke Founder Ops `/app/ops`.
5. Solo dopo OK Founder → go-live commerciale.

---

## 🎯 SoT freccia

| Ruolo | Doc |
|-------|-----|
| Freccia | [`docs/audit/OMNIA_COERENZA_SISTEMA.md`](../docs/audit/OMNIA_COERENZA_SISTEMA.md) |
| **Verso-8** | [`PROGRAMMA_VERSO_8.md`](./PROGRAMMA_VERSO_8.md) — Manut/SaaS=8 · Storia dogfood oggi |
| **Primo cliente B2B** | **D-145** Nicastro Immobiliare (slug seed `nicastroimmobiliare`) |
| **Grant assistito** | Ops `POST /app/ops/grant-agency-plan` · UI `/it/app/ops` · CLI `scripts/grant_agency_plan.py` |
| **Vetrina www** | **D-146** + **D-148** paperless |
| Template / migrazione | D-149…D-151 · gallery 8 · Pro include temi |

---

## Oggi 10-Nov — dogfood reale

1. Ops: **Purge shell** se slug seed occupato → registra Nicastro con credenziali **reali**  
2. Super_admin: **Concedi Pro + ≥2000 crediti** (stesso tool per altre agenzie)  
3. Import immobili · restyling gallery 8 · clone opz. · tool marathon  
4. Paperless www · diario · voto Storia  

Self-serve Stripe B2B resta **OFF** (O6) — il grant Ops è il percorso corretto.

---

## Login

| Chi | Email | Note |
|-----|-------|------|
| Founder Ops | `ADMIN_EMAIL` (vault) | `super_admin` → pannello Ops grant |
| Seed Nicastro (vecchio) | `titolare@nicastroimmobiliare.it` | solo se non purged |
| Nicastro reale | email Founder | dopo registrazione + grant |

URL: `https://app.omniarealestateecosystem.it` · sito `/api/p/{slug}/` · www `/it`.

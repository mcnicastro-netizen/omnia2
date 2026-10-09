# Prossima sessione — programma passi

**Aggiornato**: 9 Ottobre 2026 · Onda G GREEN · P-035/P-036 CHIUSI · P-034 WONTFIX  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Branch audit**: `cursor/portale-audit-onda-d-live-4532` (PR #12) · merge su `main` solo se Founder lo chiede  
**Chat SoT**: questa run Cloud (inject Stripe test + OpenAPI)

---

## 🎯 Prossimo passo — Onda H

**SoT**: [`OMNIA_PORTALE_AUDIT_PROGRAM.md`](../docs/audit/OMNIA_PORTALE_AUDIT_PROGRAM.md) § Onda H  
Portale ↔ GDPR e AI Act (consensi, informative, diritti, sub-responsabili, trasparenza AI).  
Attende «vai» Founder.

### Aperti residui
| ID | Note |
|--|--|
| P-021 | Google OAuth opz. |
| P-024 | gemini model string docs P3 |
| P-026 | Vault `whsec` — Founder Environment |
| P-032 | alias `/cloud/valuator` (P3) |
| P-033 | Search lista L3/L4 (P2) — «dopo» |

---

## ✅ Stato catch-up

| Onda | Esito |
|--|--|
| **A** funzionamento | CHIUSA · P-001…P-008 |
| **B** codice | CHIUSA · P-009…P-017 |
| **C** secrets | CHIUSA/mitigata · boot auto |
| **D** provider live | **GREEN** · P-022/P-023 CHIUSI |
| **E** Ops telemetry | CHIUSA · P-025…P-030 CHIUSI |
| **F** bottoni CTA | ✅ **GREEN** · P-031 CHIUSO |
| **G** portale↔gestionale | ✅ **GREEN** · P-033…P-036 aperti |

**PR draft**: https://github.com/mcnicastro-netizen/omnia2/pull/12  
**Matrice G**: `docs/audit/portale-matrici/2026-10-09-onda-g.md`

---

## Calendario

| Data | Onda | Focus |
|--|--|--|
| 8 Ott | A–E | ✅ |
| 9 Ott | F + G | ✅ |
| succ. | **H** | GDPR + AI Act (dopo «vai») |
| poi | I → J | Resilienza · fascicolo |

> Regola SoT: non saltare onde. Fix P-### solo con «vai».

---

## Boot auto Cloud (invariato)

| Script | Ruolo |
|--|--|
| `stripe-vault-materialize.py` | vault → `.env` · prefer `sk_test_` |
| `sync-public-base-url.py` | FRONTEND_* = trycloudflare |
| `sync-stripe-webhook-url.py` | endpoint test → tunnel webhook |
| `omnia-stack ensure` | API+preview+tunnel · re-seed inventory se total=0 (P-031) |

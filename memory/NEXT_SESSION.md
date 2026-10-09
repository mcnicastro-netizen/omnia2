# Prossima sessione — programma passi

**Aggiornato**: 9 Ottobre 2026 · Onda F fatta · P-031 blocco inventory  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Branch audit**: `cursor/portale-audit-onda-d-live-4532` (PR #12) · merge su `main` solo se Founder lo chiede  
**Chat SoT**: questa run Cloud (inject Stripe test + OpenAPI)

---

## 🎯 Prossimo passo — sblocca F + Onda G

### Blocco attuale
| ID | Azione |
|--|--|
| **P-031 P0** | «vai P-031» → re-seed demo (`visibility=public`) · QC search total>0 · ripeti property CTA |
| P-032 P3 | alias `/cloud/valuator` (opz.) |

### Poi Onda G (portale ↔ gestionale)
**SoT**: [`OMNIA_PORTALE_AUDIT_PROGRAM.md`](../docs/audit/OMNIA_PORTALE_AUDIT_PROGRAM.md) § Onda G  
Attende «vai» Founder.

### Aperti residui
| ID | Note |
|--|--|
| P-021 | Google OAuth opz. |
| P-024 | gemini model string docs P3 |
| P-026 | Vault `whsec` — Founder Environment |
| **P-031** | inventory vuota (P-001 regressione) |
| P-032 | slug valuator EN |

---

## ✅ Stato 8 Ott (fatto oggi)

| Onda | Esito |
|--|--|
| **A** funzionamento | CHIUSA · P-001…P-008 |
| **B** codice | CHIUSA · P-009…P-017 |
| **C** secrets | CHIUSA/mitigata · boot auto |
| **D** provider live | **GREEN** · P-022/P-023 CHIUSI · Stripe test + OpenAPI D-116 |
| **E** Ops telemetry | CHIUSA · P-025…P-030 CHIUSI (vai) |
| **F** bottoni CTA | ✅ catalogo+prove · green bloccata **P-031** |

**PR draft**: https://github.com/mcnicastro-netizen/omnia2/pull/12  
**HAL**: `api.portale-audit-program` · `api.founder-ops-portale` · `api.visura-openapi-catasto` (D-116)

---

## Calendario catch-up

| Data | Onda | Focus |
|--|--|--|
| 8 Ott | A–E | ✅ |
| 9 Ott | **F** | ✅ matrice · P-031/P-032 |
| succ. | **G** | Portale ↔ gestionale (dopo «vai» / fix P-031) |
| poi | H → I → J | GDPR · resilienza · fascicolo |

> Regola SoT: non saltare onde. A–E fatte in anticipo → si avanza a F.

---

## Boot auto Cloud (invariato)

| Script | Ruolo |
|--|--|
| `stripe-vault-materialize.py` | vault → `.env` · prefer `sk_test_` |
| `sync-public-base-url.py` | FRONTEND_* = trycloudflare |
| `sync-stripe-webhook-url.py` | webhook → tunnel `/api/billing/webhook` |
| `check-secrets-presence.sh` | presence + classi Stripe |

**Founder (quando puoi)**: allinea vault `STRIPE_WEBHOOK_SECRET` all’endpoint auto-sync (P-026).

---

## HAL / manuale

Cap. 00 HAL + Cap. 19 §19.10.6 aggiornati 8-Ott sera.  
Reindex: `POST /api/app/hal/knowledge/reindex?force=true` (super_admin) dopo merge/pull.

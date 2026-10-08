# Prossima sessione — programma passi

**Aggiornato**: 8 Ottobre 2026 sera · D-118 A–E + fix P-025…P-030  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Branch audit**: `cursor/portale-audit-onda-d-live-4532` (PR #12) · merge su `main` solo se Founder lo chiede  
**Chat SoT**: questa run Cloud (inject Stripe test + OpenAPI)

---

## 🎯 Domani 9 Ottobre 2026 — Onda F (bottoni)

**Obiettivo**: matrice esaustiva di ogni CTA/controllo del portale B2C (+ Legal B2C).  
**SoT**: [`docs/audit/OMNIA_PORTALE_AUDIT_PROGRAM.md`](../docs/audit/OMNIA_PORTALE_AUDIT_PROGRAM.md) § Onda F  
**Regola**: analisi/matrici/finding `P-###` · **fix codice solo con «vai»** su ID

### Boot (obbligatorio)
1. `bash scripts/omnia-stack.sh ensure`
2. `bash scripts/check-secrets-presence.sh` → `sk_test` / `pk_test`
3. `GET /api/billing/plans` → `mode=test` `enabled=true` (se `sk_live` → STOP)
4. Rebuild FE se tocchi UI: `yarn build` + `omnia-stack restart-preview`

### Deliverable Onda F
- [ ] Estrarre FE: `<button` / `onClick` / `Link` CTA / `submit` in immocloud+legal+footer
- [ ] Matrice `docs/audit/portale-matrici/2026-10-09-onda-f.md`  
  colonne: `ID | Pagina | Label/testid | Azione attesa | Precondizione | Esito | Evidenza | Finding`
- [ ] Zone obbligatorie: TopNav (desktop+mobile), hero, search, property, account, sell, valutatore, Visura, mutui, Legal, register/login, footer, cookie/banner
- [ ] Diario `portale-diario/2026-10-09.md` · aggiornare `portale-finding.md`
- [ ] 100% catalogati · 100% provati o SKIP motivato

### Fuori scope domani
- Onda G (gestionale) / H (GDPR) — non iniziare finché F non è chiusa o Founder dice «vai» a sovrapporre
- A-038 fatture/dati fiscali (post-test)
- Push `main` senza ordine Founder

### Aperti residui (non bloccanti F)
| ID | Note |
|--|--|
| P-021 | Google OAuth opz. |
| P-024 | gemini model string docs P3 |
| P-026 | Vault `whsec` ≠ endpoint auto-sync — Founder aggiorna Environment |

---

## ✅ Stato 8 Ott (fatto oggi)

| Onda | Esito |
|--|--|
| **A** funzionamento | CHIUSA · P-001…P-008 |
| **B** codice | CHIUSA · P-009…P-017 |
| **C** secrets | CHIUSA/mitigata · boot auto |
| **D** provider live | **GREEN** · P-022/P-023 CHIUSI · Stripe test + OpenAPI D-116 |
| **E** Ops telemetry | CHIUSA · P-025…P-030 CHIUSI (vai) |

**PR draft**: https://github.com/mcnicastro-netizen/omnia2/pull/12  
**HAL**: `api.portale-audit-program` · `api.founder-ops-portale` · `api.visura-openapi-catasto` (D-116)

---

## Calendario catch-up (dopo anticipo A–E)

| Data | Onda | Focus |
|--|--|--|
| **9 Ott** | **F** | Matrice bottoni CTA |
| 10 Ott | **G** | Portale ↔ gestionale |
| 11 Ott | **H** | GDPR + AI Act portale |
| 12 Ott | **I** | Anti-crash / dati / Stripe resilienza |
| 13 Ott | **J** | Extra + fascicolo + priorità fix |

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

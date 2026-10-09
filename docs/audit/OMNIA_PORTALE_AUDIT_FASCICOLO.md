# Fascicolo Audit Portale ImmobilCloud (D-118)

**Data fascicolo**: 2026-10-09 · **residuo codice CHIUSA**  
**Repo**: `mcnicastro-netizen/omnia2` · branch `cursor/portale-audit-onda-d-live-4532` · PR #12  
**Ambiente prova**: Cloud Agent · API `43121` · preview `43123` · tunnel trycloudflare del giorno  
**Regola**: fix codice solo con «vai» Founder su `P-###` · no push `main` · Stripe solo test · O6 self-serve OFF  

---

## 1. Executive summary (Founder)

Il portale ImmobilCloud è stato percorso a onde **A–J** (analisi + evidenze live).  
**Dogfood di base regge**: search/schede, auth B2C, Visura OpenAPI sandbox, HAL Legal a pagamento (€1 B2C / 12 crediti CRM), Stripe test + webhook, Ops Founder (overview/alert/backup), GDPR gap H chiusi in codice (P-037…P-044).

**Cosa ancora rompe o indebolisce il go-live pagamenti / privacy / resilienza** (priorità):

| Priorità | ID | Perché conta |
|--|--|--|
| 1 | **P-051** | CSRF spento (`COOKIE_SECURE=false`) sul tunnel HTTPS |
| 2 | **P-049** | Se webhook Stripe muore, poll B2C resta `pending` |
| 3 | **P-046** (+P-047) | Backup/restore non coprono ledger B2C e consensi |
| 4 | **P-050** | Register / Visura checkout senza rate limit |
| 5 | **P-033** | Card L3/L4 in search anon (detail 404) — rimandato |

**Residuo codice D-118: CHIUSO** (vai 9-Ott). Nessun **P0 runtime** aperto.
Residui: **P-021** Google OAuth opz. · **P-026** vault whsec (MITIGATO, Save Founder).  
Self-serve pubblico (**O6**) resta **OFF**. Fatturazione fiscale (**A-038**) e demo da sito (**A-037**) fuori scope fix di questo programma.

---

## 2. Scorecard onde A–J

| Onda | Focus | Esito | Matrice |
|--|--|--|--|
| A | Funzionamento E2E | GREEN | `portale-matrici/2026-10-08-onda-a.md` |
| B | Codice portale | GREEN | `2026-10-08-onda-b.md` |
| C | Inventario key | GREEN | `2026-10-08-onda-c.md` |
| D | Prove live provider | GREEN | `2026-10-08-onda-d.md` |
| E | Ops / super_admin | GREEN | `2026-10-08-onda-e.md` |
| F | Matrice bottoni | GREEN | `2026-10-09-onda-f.md` |
| G | Portale ↔ CRM | GREEN | `2026-10-09-onda-g.md` |
| H | GDPR + AI Act | GREEN | `2026-10-09-onda-h.md` |
| I | Resilienza / Stripe / security | GREEN | `2026-10-09-onda-i.md` |
| J | Extra + fascicolo | GREEN | `2026-10-09-onda-j.md` |

**Diario**: `docs/audit/portale-diario/` · **Registro**: `docs/audit/portale-finding.md`

---

## 3. Registro finding — per severità (aperti / residui)

### P0
Nessuno aperto. Storici chiusi: P-001, P-009, P-022, P-031.

### P1 aperti
Nessuno — P-046 / P-049 / P-051 **CHIUSI**.


### P2 aperti
Nessuno critico — chiusi P-033/047/048/050/054/055/057.


### P3 aperti / opzionali
| ID | Titolo | Onda |
|--|--|--|
| P-021 | Google Sign-In OFF (opz.) | C |
| P-024 | Docs gemini-2.0-flash deprecato | D |
| P-026 | Vault whsec ≠ endpoint sync | D |
| P-032 | Route `/valuator` shell vuota | F |
| P-052 | UX API down globale | I |
| P-053 | Alert webhook senza dedup | I |
| **P-056** | noindex ambienti demo/tunnel | J |
| **P-058** | Runbook tunnel morto | J |

### WONTFIX / MITIGATO
| ID | Nota |
|--|--|
| P-018 | MITIGATO (vault Save + materialize) |
| P-034 | WONTFIX brand SSR by design |
| P-045 | WONTFIX no CTA contesta stima |

Chiusi in codice (selezione): P-010…P-017, P-019, P-023, P-025, P-027…P-031, P-035…P-044.

---

## 4. Matrici (indice)

Tutte sotto `docs/audit/portale-matrici/`:

- `2026-10-08-onda-a.md` … `2026-10-08-onda-e.md`
- `2026-10-09-onda-f.md` … `2026-10-09-onda-j.md`

Artefatti live tipici: `/opt/cursor/artifacts/onda-*-live.log` · `*-results.json`

---

## 5. Lista «vai» consigliati

**Coda codice D-118: VUOTA** (analisi + fix chiusi). Prossimo: `merge main` su ordine Founder.

### Storico priorità (già eseguite)

### Prima del go-live pagamenti / HTTPS pubblico
1. `vai P-051` — CSRF su tunnel HTTPS  
2. `vai P-049` — fallback Stripe su status B2C  
3. `vai P-046 P-047` — backup + restore B2C  
4. `vai P-050` — rate limit register / Visura  

### Qualità prodotto / privacy listing
5. `vai P-033` — search L3/L4  
6. `vai P-048` — soft-delete UGC  
7. `vai P-054` — i18n soldi  
8. `vai P-055` — SEO scheda  
9. `vai P-057` — notify moderazione  

### Backlog P3
`vai P-052 P-053 P-056 P-058 P-032 P-024 P-026` (o singoli)

### Non fare in questo programma
- Merge `main` senza ordine Founder  
- Abilitare O6 / Stripe live  
- Implementare A-038 fatture fiscali  
- Redesign UI “di gusto”

---

## 6. Ripresa A-037 / A-038 / O6

| Voce | Impatto audit portale | Azione |
|--|--|--|
| **A-037** Demo da sito | Fuori scope A–J | Ripresa post-fascicolo se Founder vuole |
| **A-038** Fatture fiscali | SKIP by design in E/I | Post-test commerciale |
| **O6** Self-serve | CONDITIONAL · **OFF** | Resta OFF finché O6 ≠ PASS (D-115) |
| **O3b** Restore | Collegato a P-046/P-047 | Dopo fix backup B2C |

---

## 7. Dipendenze PR (snapshot 9-Ott)

| PR | Tema | Nota |
|--|--|--|
| **#12** | Questo audit D-118 + fix H | DRAFT SoT lavoro |
| #10 | D-116 OpenAPI single key | Usato in-tree su branch audit |
| #7 | D-117 Ops finance | DRAFT; revenue path parziale via P-025 |
| #8 / #11 / #6 | Audit early / tunnel / dogfood | Storici / parziali |

---

## 8. Criteri chiusura programma (J.3)

| Criterio | Stato |
|--|--|
| Onde A–J chiuse o rimandate con nota | ✅ tutte GREEN analisi |
| Nessun P0 aperto senza finding | ✅ |
| Founder ha fascicolo + priorità | ✅ questo documento |

**Programma D-118 (analisi): CHIUSO.**  
Fix residui = coda «vai» · non riaprono le onde salvo regressione.

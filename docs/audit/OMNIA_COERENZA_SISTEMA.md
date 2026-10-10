# OMNIA — Coerenza di sistema (SoT Founder)

**Data**: 9 Ottobre 2026 · **agg. S8**: 10 Ottobre 2026  
**Repo**: `mcnicastro-netizen/omnia2` · branch di lavoro tipico = `main`  
**Scopo**: una sola freccia — *cosa è il sistema oggi, dove la logica si spezza, in che ordine chiudere prima di demo definitiva / O6 / GTM*.  
**SoT freccia (S8):** questo file + `OMNIA_O6_GATE_CHECKLIST.md` + `memory/NEXT_SESSION.md`. Registro: `OMNIA_S8_SOT_UNICO.md`.

**Scala di verità** (obbligatoria da qui in poi):

| Livello | Significa |
|---------|-----------|
| DECISO | Decisione / design scritto |
| CODICE | Comportamento in repo |
| LIVE | Prova su tunnel / non-prod con artefatto |
| FIRMATO | Founder (o run firmata) attesta l’esito |

Solo **FIRMATO** (o almeno LIVE esplicito) = “chiuso per GTM”.  
PASS su design ≠ chiuso. CHIUSO/GREEN su audit storici ≠ FIRMATO.

---

## 1. Stato reale — cosa *è* omnia2 oggi

Un monorepo **FastAPI + React + Mongo** che opera **due prodotti** sulla stessa base (`users` / `properties`):

| Pilastro | Superficie | Ruolo |
|----------|------------|--------|
| **ImmoWeb** | `/app` + `/api/app` | Gestionale B2B: clienti, match, publishing, MLS, HAL, crediti |
| **ImmobilCloud** | `/cloud` + `/api/cloud` | Portale B2C: search, schede, UGC, Visura, Stripe one-shot |
| **Academy** | `/learn` | Coming soon — **non** offerta GTM (S6) |

Più: Founder Ops, Cloud Agent (seed demo GTM + Nicastro dogfood), corpus `memory/` + audit in `docs/audit/`.

**Tesi**: ecosistema *dual-rail* tecnicamente unificato, commercialmente in modalità **assistita** (D-115: self-serve OFF finché O6 ≠ PASS / S9).  
**Demo GTM:** solo `demo-agency-001` (S7). Nicastro = dogfood Founder.

**Promessa da chiudere (una frase):**  
*Prospect apre demo → usa il gestionale → vede gli annunci sul portale → a scadenza acquista → i dati sono recuperabili → il canone regge lo storage.*

---

## 2. Cosa tiene (non buttare)

1. Un backend, due superfici (D-015).  
2. Ponte CRM ↔ portale modellato.  
3. Due binari denaro in design: subscription/crediti B2B vs carta B2C.  
4. Tenancy su `active_agency_id`.  
5. Trash come dominio in molti path.  
6. Fail-soft su AI / email / Stripe.  
7. Ops + bak health; bak O0 runtime (S2).  
8. Cloud Agent + seed dogfoodabili.  
9. O6 come cancello commerciale + hard-gate codice (S5).  
10. Memoria decisionale / HAL.

---

## 3. Contraddizioni di sistema (logica spezzata)

| # | Contraddizione | Effetto |
|---|----------------|---------|
| C1 | **Messaggio 3→2** — mitigato S6 | Pitch GTM allineato |
| C2 | **Self-serve ≠ Stripe** — S5 gate · **S9 ON** (`OMNIA_SELF_SERVE_ENABLED=true`) | Kill-switch resta; rubinetto aperto D-120 |
| C3 | **Rail monetari** — valuator onesto; Legal edge chiuso; **D-119** Legal CRM incluso | Narrativa vs wallet allineata |
| C4 | **Visibilità pubblica** — mitigato S4 | Portale/brand allineati LIVE |
| C5 | **Trash non ovunque** | Integrità dominio quasi-una (fuori freccia S* finché ripriorizzato) |
| C6 | **Bak economia** — S2 ✅ runtime 7g+hardlink; S3 numeri ✅; **S3.1 firma listino ⏳** | Economia modellata; chiusura commerciale meter aperta |
| C7 | **Restore** — S1 run firmata ✅; non = DR piattaforma | O3b pre-GTM chiuso |
| C8 | **Demo story** — mitigato S7 (`demo-agency-001`) | Una storia GTM ripetibile |
| C9 | **SoT in conflitto** — mitigato S8 (registro + frozen) | Una freccia |
| C10 | **Falsa chiusura PASS/GREEN** — mitigato S8 (scala verità + header allineati) | Solo LIVE/FIRMATO = chiuso GTM |

**Pattern:** `TROVATO → DECISO → CODICE → LIVE → FIRMATO`.

---

## 4. Sequenza di chiusura (prima di GTM)

| Step | Cosa chiudere | Contraddizioni | Done quando |
|------|---------------|----------------|-------------|
| **S1** | O3b restore firmata non-prod | C7 | ✅ **DONE 2026-10-10** |
| **S2** | Bak = O0 runtime | C6 | ✅ **DONE 2026-10-10** |
| **S3** | Meter economia (numeri) | C6 | ✅ numeri · ⏳ **S3.1 firma** |
| **S4** | Visibilità pubblica unica | C4 | ✅ **DONE 2026-10-10** |
| **S5** | Soldi onesti / hard-gate | C2, C3 | ✅ **DONE 2026-10-10** |
| **S6** | Narrativa 2 prodotti | C1 | ✅ **DONE 2026-10-10** |
| **S7** | Demo story unica | C8 | ✅ **DONE 2026-10-10** |
| **S8** | SoT unico | C9, C10 | ✅ **DONE 2026-10-10** — `OMNIA_S8_SOT_UNICO.md` |
| **S9** | O6 PASS + firma Founder self-serve | C2, C7 | ✅ **DONE 2026-10-10** — `OMNIA_S9_O6_SELF_SERVE.md` · D-120 |
| **S10** | GTM-01 smoke + percorso prospect | — | ✅ **DONE 2026-10-10** — `OMNIA_S10_GTM_01.md` · D-121 |

**Fuori sequenza senza «vai» Founder:** redesign UI, A-038 fatture, Stripe live keys, outreach di massa (gate tecnico S10 OK).

**Demo funnel (Founder 10 Ott):** richiesta → sandbox a tempo → a scadenza CTA acquista — **senza call**. Checkout B2B **aperto** (S9).

---

## 4bis. Dipendenze commerciali / SoT aperti (segnalare sempre)

| Voce | Stato | Nota |
|------|-------|------|
| **D-038 — ordine APE ufficiale** | ⏳ accordo commerciale | ≠ compliance classe APE in publishing |
| **S3.1 — firma meter** | ⏳ | Non chiudere listino senza Founder |
| **D-119 — Legal CRM incluso** | ✅ | Chiude D-075 vs P-036 |

---

## 5. Cosa *non* riesaminare da zero

- Finding D-118 già in codice su `main`: **ri-verificare LIVE**, non riscrivere.  
- O1 AuthZ / invite / agency: in gran parte CODICE vero.  
- Trash/freeze di dominio: distinto da economia bak (C6).  
- Vault Environment: presence check = rituale di boot.  
- Docs **FROZEN** (AUDIT_STATE, PROGRAMMA_PRE_ATTIVAZIONE, HANDOFF_*): memoria, non freccia — vedi `OMNIA_S8_SOT_UNICO.md`.

---

## 6. Verdetto Founder

Il repo **non** è un pasticcio casuale: è un ecosistema dual-product con spina dorsale solida.  
Il rischio di fallimento non è “manca un modulo magico”: è **raccontare o vendere una storia più chiusa** di quanto il sistema sia logicamente allineato.

**Freccia S1–S10 ✅.** Prossimo tipico: outreach solo con «vai» · oppure S3.1 / D-038.

---

## 7. Indice SoT collegati

| Documento | Uso |
|-----------|-----|
| Questo file | Freccia coerenza / sequenza |
| `OMNIA_S8_SOT_UNICO.md` | Registro LIVE vs FROZEN |
| `OMNIA_O6_GATE_CHECKLIST.md` | Cancello self-serve |
| `memory/NEXT_SESSION.md` | Puntatore sessione |
| `OMNIA_O0_BAK_MEDIA_DESIGN.md` | Modello bak target |
| `docs/ops/RESTORE_MANUAL.md` | Procedura + firma run S1 |
| `OMNIA_S3_METER_ECONOMIA.md` … `OMNIA_S7_DEMO_STORY.md` | Step S3–S7 |
| `OMNIA_PORTALE_AUDIT_FASCICOLO.md` | Audit portale D-118 (storico) |
| `memory/PRICING_OMNIA.md` / `PRICING_B2C.md` | Listino (S3.1 firma aperta) |

# OMNIA — Coerenza di sistema (SoT Founder)

**Data**: 9 Ottobre 2026 · **agg. S7**: 10 Ottobre 2026  
**Repo**: `mcnicastro-netizen/omnia2` · branch di lavoro tipico = `main`  
**Scopo**: una sola freccia — *cosa è il sistema oggi, dove la logica si spezza, in che ordine chiudere prima di demo definitiva / O6 / GTM*.  
**Non sostituisce**: fascicolo D-118, O6 checklist, O0 design, DECISIONS. Li **ordina**.

**Scala di verità** (obbligatoria da qui in poi):

| Livello | Significa |
|---------|-----------|
| DECISO | Decisione / design scritto |
| CODICE | Comportamento in repo |
| LIVE | Prova su tunnel / non-prod con artefatto |
| FIRMATO | Founder (o run firmata) attesta l’esito |

Solo **FIRMATO** (o almeno LIVE esplicito) = “chiuso per GTM”.  
PASS su design ≠ chiuso.

---

## 1. Stato reale — cosa *è* omnia2 oggi

Un monorepo **FastAPI + React + Mongo** che opera **due prodotti** sulla stessa base (`users` / `properties`):

| Pilastro | Superficie | Ruolo |
|----------|------------|--------|
| **ImmoWeb** | `/app` + `/api/app` | Gestionale B2B: clienti, match, publishing, MLS, HAL, crediti |
| **ImmobilCloud** | `/cloud` + `/api/cloud` | Portale B2C: search, schede, UGC, Visura, Stripe one-shot |
| **Academy** | `/learn` | Quasi solo vetrina / “coming soon” — **non** offerta GTM |

Più: Founder Ops, Cloud Agent riproducibile (seed demo + Nicastro), corpus `memory/` + audit in `docs/audit/`.

**Tesi**: ecosistema *dual-rail* tecnicamente unificato, commercialmente in modalità **assistita** (D-115: self-serve OFF finché O6 ≠ PASS). Non è ancora una sola storia GTM-ready; è un sistema che *sa* esserlo se si chiudono le contraddizioni sotto.

**Promessa da chiudere (una frase):**  
*Prospect apre demo → usa il gestionale → vede gli annunci sul portale → a scadenza acquista → i dati sono recuperabili → il canone regge lo storage.*

---

## 2. Cosa tiene (non buttare)

1. Un backend, due superfici (D-015) — meno drift di due repo.  
2. Ponte CRM ↔ portale modellato (listati, privacy, lead, moderazione).  
3. Due binari denaro in design: subscription/crediti B2B vs carta B2C.  
4. Tenancy su `active_agency_id` (direzione corretta).  
5. Trash come dominio in molti path (non solo UI).  
6. Fail-soft su AI / email / Stripe.  
7. Ops + bak health come superficie di verità.  
8. Cloud Agent + seed dogfoodabili.  
9. O6 dichiarato come cancello commerciale.  
10. Memoria decisionale / HAL — il prodotto *sa* perché esiste.

---

## 3. Contraddizioni di sistema (logica spezzata)

Non è una lista infinita di bug: sono **tensioni** che impediscono di firmare “sì” a demo/O6/GTM.

| # | Contraddizione | Effetto |
|---|----------------|---------|
| C1 | **Messaggio a 3 pilastri / prodotto a 2** — mitigato S6: pitch = ImmobilCloud + ImmoWeb; `/learn` solo coming soon | Pitch GTM allineato; Academy resta roadmap M6 |
| C2 | **D-115 self-serve** — mitigato S5: `OMNIA_SELF_SERVE_ENABLED` (default OFF) ≠ `STRIPE_ENABLED` | Kill-switch B2B reale; Stripe sandbox resta |
| C3 | **Rail monetari** — valuator copy onesta; Legal edge gratis **chiuso**; D-075 vs P-036 ancora aperto | Narrativa vs wallet più onesta; SoT Legal da firmare dopo |
| C4 | **Due verità pubbliche** — mitigato S4: contratto pubblico unico portale/brand | Allineato LIVE; residuali fuori S4 |
| C5 | **Trash non ovunque** — KPI / alcuni MLS senza soft-delete uniforme | Integrità dominio quasi-una |
| C6 | **O0 PASS design / bak as-is** — ancora `copytree` × retention **30** (~32× disco) | Agency ∞ economicamente finta al tetto GB |
| C7 | **Restore: docs sì, run firmata sì (S1 2026-10-10)** — ancora manuale, non RTO commerciale | Chiuso per pre-GTM O3b; non = DR piattaforma |
| C8 | **Due seed = due storie demo** — mitigato S7: GTM = solo `demo-agency-001` (Nicastro = dogfood) | Una demo story ripetibile |
| C9 | **SoT documentali in conflitto temporale** (AUDIT_STATE / GTM freeze / fascicolo / NEXT) | Founder e agent leggono più futuri |
| C10 | **CHIUSO/PASS/GREEN spesso = DECISO o CODICE**, raramente FIRMATO | Falsa chiusura (caso bak) |

**Pattern**: gli audit erano affidabili nel *vedere*; meno affidabili nel tenere la catena  
`TROVATO → DECISO → CODICE → LIVE → FIRMATO`.

---

## 4. Sequenza di chiusura (prima di GTM)

Ordine di **coerenza**, non di feature. Niente monoblocco; ogni step ha artefatto o firma.

| Step | Cosa chiudere | Contraddizioni | Done quando |
|------|---------------|----------------|-------------|
| **S1** | **O3b** — una restore firmata non-prod (agency + perimetro B2C rilevante) | C7 | ✅ **DONE 2026-10-10** — firma in `RESTORE_MANUAL` §6 + `docs/ops/runs/s1-restore-o3b-2026-10-10.log` |
| **S2** | **Bak = O0 runtime** — retention hot ≤7g e/o incrementale (come da design) | C6 | ✅ **DONE 2026-10-10** — default 7 + hardlink; `docs/ops/runs/s2-bak-o0-runtime-live.log` |
| **S3** | **Meter economia** — GB reali post-S2; conferma canoni vs Agency 300 GB + addon | C6 | ✅ numeri 10-Ott (`OMNIA_S3_METER_ECONOMIA.md`) · ⏳ **firma Founder rimandata** → S3.1 |
| **S4** | **Una regola di visibilità** — stesso contratto pubblico portale / brand site | C4 | ✅ **DONE 2026-10-10** — `public_visibility` + LIVE |
| **S5** | **Soldi onesti** — addebito reale o UI onesta; opz. hard-gate self-serve distinto da Stripe test | C2, C3 | ✅ **DONE 2026-10-10** — `OMNIA_S5_SOLDI_ONESTI.md` + LIVE |
| **S6** | **Narrativa 2 prodotti** — Academy fuori pitch finché non esiste | C1 | ✅ **DONE 2026-10-10** — `OMNIA_S6_NARRATIVA_2_PRODOTTI.md` + LIVE |
| **S7** | **Una demo story** — un seed; percorso admin→portale; giorni prova; scadenza → **Acquista pacchetto** (post-O6) | C8 | ✅ **DONE 2026-10-10** — `OMNIA_S7_DEMO_STORY.md` + LIVE ×2 |
| **S8** | **SoT unico** — questo doc + O6 + NEXT; resto frozen/archiviato | C9, C10 | Header stati allineati |
| **S9** | **O6 PASS** — checklist senza ⏳ su restore; firma Founder self-serve | C2, C7 | Rubinetto ON solo qui |
| **S10** | **GTM-01** — smoke ~20 concurrent + percorso prospect **prima** di ~5k email | — | Gate D-104 |

**Fuori sequenza finché S7 non è verde:** redesign UI, A-038 fatture, Stripe live, outreach di massa, O6 ON “perché prima o poi”.

**Demo funnel (decisione Founder in discussione):** richiesta da ads/email/reel → sandbox a tempo (gestionale + agganci portale) → a scadenza CTA acquista — **senza call**. Pitch/video = strumento pubblicitario, non sostituto della prova. Checkout acquisto solo post-**S9**.

---

## 4bis. Dipendenze commerciali aperte (segnalare sempre)

Non sono contraddizioni codice↔promessa della freccia S1–S10, ma **restano aperti** e vanno ricordati a ogni handoff:

| Voce | Stato | Nota |
|------|-------|------|
| **D-038 — ordine APE ufficiale** | ⏳ accordo commerciale | Nessun bottone “Ordina APE” finché partner (APEFACILE / Certificato-Energetico.it) non firma. D-039: niente calcolatore in-house. Compliance *classe APE* in publishing ≠ servizio certificazione. |

## 5. Cosa *non* riesaminare da zero

- Finding D-118 già in codice su `main` (CSRF, Stripe fallback, rate limit, ecc.): **ri-verificare LIVE**, non riscrivere.  
- O1 AuthZ / invite / agency: in gran parte CODICE vero.  
- Trash/freeze di dominio: distinto da economia bak (C6).  
- Vault Environment: oggi più completo; presence check = rituale di boot, non audit nuovo.

---

## 6. Verdetto Founder

Il repo **non** è un pasticcio casuale: è un ecosistema dual-product con spina dorsale solida.  
Il rischio di fallimento non è “manca un modulo magico”: è **raccontare o vendere una storia più chiusa** di quanto il sistema sia logicamente allineato (soldi, restore, storage, messaggio, una sola demo).

**Prossimo «vai» consigliato:** **S8** (SoT unico). Reminder: S3.1 firma meter; D-038 APE; S9 = `OMNIA_SELF_SERVE_ENABLED=true`.

---

## 7. Indice SoT collegati

| Documento | Uso |
|-----------|-----|
| Questo file | Freccia coerenza / sequenza |
| `OMNIA_O6_GATE_CHECKLIST.md` | Cancello self-serve |
| `OMNIA_O0_BAK_MEDIA_DESIGN.md` | Modello bak target (DECISO) |
| `docs/ops/RESTORE_MANUAL.md` | Procedura + firma run |
| `OMNIA_S5_SOLDI_ONESTI.md` | Self-serve hard-gate + copy valuator / Legal edge |
| `OMNIA_S6_NARRATIVA_2_PRODOTTI.md` | Pitch GTM = 2 prodotti; Academy fuori |
| `OMNIA_PORTALE_AUDIT_FASCICOLO.md` | Audit portale D-118 |
| `OMNIA_PROGRAMMA_PRE_ATTIVAZIONE.md` | Onde O0–O6 |
| `memory/NEXT_SESSION.md` | Puntatore sessione (punta qui) |
| `memory/PRICING_OMNIA.md` / `PRICING_B2C.md` | Listino (fermo finché S3) |

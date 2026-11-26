# AUDIT MIRATO B2C — ImmobilCloud (portale pubblico, schede, isolamento)

**Data (Europe/Rome):** 2026-11-26 16:45 CET  
**Autore:** Cursor (Cloud Agent) — solo analisi / test non distruttivi  
**Repository:** `mcnicastro-netizen/omnia2`  
**Baseline:** `main` @ `5fba9f5df0416e81b801d855da5bf79a202a6aaf` (post merge PR #247 `2dfee7f…`)  
**Working tree:** clean al momento dell’audit  
**Autorizzazione:** audit mirato — **nessuna** implementazione, deploy, merge, push, commit, mutazione DB

---

## 0. Giudizio complessivo

**Il perimetro B2C ImmobilCloud NON è dichiarabile pronto per uso commerciale reale.**

Esiste un’architettura articolata (portale React `/cloud`, API `/api/cloud/*`, sito brand HTML `/api/p/{slug}`, privacy gate L1–L4, free tier 2 annunci, matching D-126, rate-limit contatti) con test unitari di filtro S4 e publisher. Tuttavia:

1. **Verifiche dinamiche essenziali incomplete** su inventario reale (staging live: **0** listing ImmobilCloud pubblici).
2. **Gap dimostrato** tra filtro foto pubbliche e superficie pubblica SoT.
3. **Proiezione ImmobilCloud espone `agency.id`** (e in detail `agency_id`) — divergenza rispetto allo standard A4 MLS public search.
4. **Risposta contatto anonima** restituisce `lead_id` / `client_id`.
5. Suite privacy/contatto end-to-end **non eseguibile** in questo ambiente senza seed/credenziali.

**Classificazione globale:** **P1 — non GTM** sul perimetro pubblico B2C, con dipendenza da ciclo di hardening + staging-deep B2C dedicato.

---

## 1. Baseline e metodo

| Voce | Valore |
|------|--------|
| Branch | `main` |
| HEAD | `5fba9f5…` |
| Antenato merge #247 | `2dfee7f…` sì |
| Staging API interrogata (sola lettura) | `https://omnia-api-production-85845f42.up.railway.app` |
| Presunzione deploy = main | **NO** — OpenAPI staging espone path cloud; inventario pubblico `total=0` |
| Mutazioni | nessuna (no contact POST, no seed, no cleanup DB) |
| Test locali eseguiti | `test_s4_public_visibility` + publisher + MLS isolation + authz embed (19 pass) |
| Harness dinamico locale | `/opt/cursor/artifacts/b2c-audit-dynamic.log` |
| Log unit | `/opt/cursor/artifacts/b2c-audit-unit1.log`, `b2c-audit-unit2.log` |

### Flussi ricostruiti
1. Anon → `GET /api/cloud/search` → `portal_listing_filter` → `_to_card`
2. Anon → `GET /api/cloud/property/{pid}` → filter + privacy_gate → publisher
3. Anon → `POST /api/cloud/property/{pid}/contact` → lead/inquiry (codice + test esistenti; non eseguito live)
4. Brand → `GET /api/p/{slug}/` e `/{pid}` → `brand_site_filter(agency_id)`
5. Foto → `GET /api/public/property/{pid}/photo/{idx}` (filtro **più debole**)
6. Owner → `/api/cloud/me/properties` + free tier / submit
7. Matching privato → `private_listing_matching` (scope portal, fuori MLS)

---

## 2. Mappa perimetro

### 2.1 Frontend ImmobilCloud
Mount: `frontend/src/App.js` → `/:lang/cloud/*` → `ImmocloudApp.jsx`

| Route FE | Ruolo |
|----------|--------|
| `/{lang}/cloud` | Home |
| `…/search` | Ricerca |
| `…/property/:pid` | Scheda pubblica (**UUID**, non slug immobile) |
| `…/area` · `…/register` | Gate owner |
| `…/account/sell` | Vendi / gestione listing |
| `…/account/messages` | Inbox inquiry |
| valutatore / visura / mutui / checkout | Servizi B2C |

**Nota:** non esiste route React `/p/{slug}`. Il brand site è HTML SSR sotto `/api/p/{slug}/…`.

### 2.2 API ImmobilCloud (`/api/cloud`)
Search, map, facets, `property/{pid}`, `agency/{slug}`, `property/{pid}/contact`, auth register, `me/properties*`, inquiries, billing B2C correlati.

### 2.3 Sito brand `/api/p/{slug}` (`backend/apps/immoweb/site.py`)
| Path | Funzione |
|------|----------|
| `/api/p/{slug}/` | Index themed |
| `/api/p/{slug}/lista` | Lista |
| `/api/p/{slug}/{pid}` | Scheda HTML + schema.org |
| `/api/p/{slug}/sitemap.xml` | Sitemap |
| `/api/public/property/{pid}/photo/{idx}` | Binario foto |

**Slug** = **agency slug** (unicità in `agencies`), non slug listing.

---

## 3. Verifiche — pubblicazione e accesso pubblico

| ID | Verifica | Atteso | Verificato | Evidenza | Esito |
|----|----------|--------|------------|----------|-------|
| A1 | Solo listing `active`+`public`+moderation ok su portale | filtro SoT | Codice `portal_listing_filter` + unit S4 | `public_visibility.py`, 14 unit PASS | **PASS** (codice+unit) |
| A2 | Opt-out `is_listed_on_immobilcloud=false` nasconde portale non brand | delta documentato | unit S4 | `intentional_deltas` | **PASS** |
| A3 | L3/L4 esclusi dal feed portale | privacy | unit + codice | `privacy_level $nin` | **PASS** (unit); live L-gate **NOT VERIFIED** (seed login fail) |
| A4 | Detail 404 se fuori filtro | 404 | codice; live no inventory | staging `total=0` | **NOT VERIFIED** (live) / **PASS** codice |
| A5 | Trash escluso | with_not_trashed | unit | S4 | **PASS** |
| A6 | Coerenza FE UUID vs API | stesso pid | codice FE/API | `PropertyDetailPage` | **PASS** codice |
| A7 | Inventario staging utilizzabile | ≥1 listing | GET search | `total: 0` | **FAIL ambiente** (blocca deep live) |

---

## 4. Verifiche prioritarie `/p/{slug}`

| ID | Verifica | Atteso | Verificato | Evidenza | Esito |
|----|----------|--------|------------|----------|-------|
| P1 | Resolve slug agenzia attiva | 404 se assente | live `GET /api/p/does-not-exist…` → 404 | staging | **PASS** |
| P2 | Lookup immobile vincolato ad `agency_id` dello slug | cross-tenant 404 | codice `brand_site_filter(agency["id"], {id: pid})` | `site.py` 243–252 | **PASS** codice; live cross-slug **NOT VERIFIED** (no slug con listing) |
| P3 | Solo superficie pubblica brand | status/visibility/moderation | unit brand filter | S4 | **PASS** |
| P4 | Brand non richiede `is_listed_on_immobilcloud` | delta intenzionale | unit + docs | SoT | **PASS** (intenzionale) |
| P5 | HTML non espone secret interni | no password/CC | sample HTML non disponibile (0 listing); `_resolve` carica **intero** doc agency | rischio residuale | **NOT VERIFIED** HTML; **SOSPETTO** codice (`find_one` senza projection stretta) |
| P6 | Sitemap solo props filtrate | brand filter | codice | `site_sitemap` | **PASS** codice |
| P7 | MLS network box su index se `mls_enabled` | props partner + `_partner_name` | codice espone `agency_id` in query network | `site.py` 145–165 | **PASS** funzionale; vedi rischio P2 sotto |
| P8 | Cache foto | `Cache-Control: public, max-age=86400` | codice | `serve_property_photo` | **PASS** codice (rischio stale post-unpublish se CDN) |
| P9 | Enumerazione slug | 404 uniforme | live unknown 404 | staging | **PASS** (sample) |

---

## 5. Sicurezza e isolamento

### 5.1 Criticità dimostrate

#### C1 — Foto pubbliche con filtro più debole della superficie pubblica · **P1**
- **Componente:** `GET /api/public/property/{pid}/photo/{idx}` in `apps/immoweb/site.py`
- **Atteso:** allineato a `public_surface_base` / portal o brand filter
- **Effettivo:** solo `status=active` + not trashed — **manca** `visibility=public`, moderation, listing ImmobilCloud
- **Evidenza dinamica locale:** matrice accesso — listing `visibility=private` o `moderation=pending` con `status=active` → foto servibile, portale no (`b2c-audit-dynamic.log`)
- **Scenario:** chi conosce/indovina `pid`+indice può scaricare foto di annunci non pubblici (bozze pubblicate male, private, in moderazione) se lo status resta `active`
- **Impatto:** proprietari/agenzie — leakage media; piattaforma — violazione aspettativa privacy
- **Test correzione:** property `active`+`visibility=private` → photo **404**; `public`+approved → 200

#### C2 — `agency_id` / `agency.id` in risposte ImmobilCloud pubbliche · **P2** (P1 se policy = zero ID interni pubblici)
- **Componente:** `_to_card` (`portal_common.py`), `public_property_detail` (`portal_detail.py`)
- **Atteso (A4 MLS public):** niente `agency_id` in proiezione pubblica
- **Effettivo ImmobilCloud:** card espone `agency.id`; detail propaga `agency_id` dal documento + oggetto `agency` con id/email/phone
- **Evidenza:** codice + assert locale `_to_card`; test `test_immobilcloud_public` **non** asserta assenza `agency_id`
- **Scenario:** correlazione cross-listing / fingerprinting tenant; email/phone agenzia su detail sono **canali publisher** (intenzionali) ma l’UUID interno aumenta superficie
- **Classificazione decisione:** non è automaticamente violazione Founder se ImmobilCloud deve mostrare l’agenzia; è **divergenza di policy** rispetto A4 e va chiarita
- **Test correzione (se policy strip):** search/detail senza `agency_id` / `agency.id` interno

#### C3 — Contact anonimo restituisce `lead_id` e `client_id` · **P2**
- **Componente:** `public_property_contact` return `{"ok", "lead_id", "client_id"}`
- **Atteso tipico:** ack senza ID interni CRM
- **Scenario:** enumerazione/riuso ID lato client; information disclosure minore
- **Test correzione:** response solo `{ok: true}` (o token opaco)

### 5.2 Controlli con esito positivo (codice / unit)

| Controllo | Esito |
|-----------|--------|
| Brand site filtra per `agency_id` dello slug | **PASS** codice |
| Inquiry private scoped `owner_user_id` | **PASS** codice (`listing_inquiries.py`) |
| Rate limit contact 20/h IP | **PASS** codice |
| GDPR consent obbligatorio | **PASS** codice + test suite (non rieseguita live) |
| Publisher privato opt-in canali | **PASS** unit publisher |
| Privati fuori inventario MLS shareable | **PASS** unit `test_private_listing_mls_isolation` |
| `/api/media` path `omnia/private/{user}` gated P-009 | **PASS** codice |
| Fascicolo/modulistica blocked su media passthrough | **PASS** codice |

### 5.3 Sospetti non dimostrati dinamicamente

| Sospetto | Perché non PASS/FAIL |
|----------|----------------------|
| HTML brand espone campi agency sensibili | `_resolve` senza projection; nessun HTML sample con listing |
| Cache CDN foto post-withdraw | richiede timing + asset reale |
| IDOR contact verso agency sbagliata | richiede due agency + listing; non eseguito (mutativo) |
| Privacy L1–L4 end-to-end | `test_m3s9_privacy_audit` ERROR login 401 in ambiente |

---

## 6. Proprietari e annunci privati

| Verifica | Esito | Note |
|----------|-------|------|
| Free tier 2 annunci senza scadenza | **PASS** codice + allineamento `PRICING_B2C.md` / D-listino | `FREE_TIER_MAX_ACTIVE=2` |
| Dal 3° serve slot Stripe | **PASS** codice | non pay-to-unlock del matching |
| Matching privati → richieste agenzie (D-126) | **PASS** codice vs decisione | canale `portal`, fuori MLS inventory |
| Matching ≠ paywall | **PASS** vs decisione | non trovato unlock a pagamento per vedere match |
| Titolarità `owner_user_id` su CRUD/inquiry | **PASS** codice | |
| Passaggio titolarità owner→agenzia | **NOT VERIFIED** | flusso mandato/opportunities citato D-126/D-130 area; non deep-testato qui |
| Safety gate / auto-publish D-137 | **NOT VERIFIED** dinamico | codice presente; no run |

**Confronto decisioni:** free listing + matching gratuito alle agenzie = **conforme** a PRICING_B2C e D-126. Non risulta transformazione in pay-to-unlock del matching.

---

## 7. Contatti e conversione

| Verifica | Esito |
|----------|--------|
| Agency listing → client+lead su `agency_id` corretto | **PASS** codice; test `test_immobilcloud_m3s4_contact` esiste ma **non rieseguito** (DB seed) |
| Private → `listing_inquiries` owner | **PASS** codice |
| Contact su non pubblico → 404 | **PASS** codice (usa `_base_filter`) |
| Rate limit / GDPR | **PASS** codice |
| Email reali | non inviate in questo audit |
| Cross-org read lead | **PASS** codice (lead creato con agency_id; inquiry owner-scoped) — E2E **NOT VERIFIED** |

---

## 8. Esperienza, SEO, affidabilità

| Area | Stato |
|------|--------|
| Search/facets/map API | presenti; staging **0 risultati** → UX vuota **NOT VERIFIED** con dati |
| Errori 404 property | codice OK; live unknown 404 cloud **NOT VERIFIED** (no pid); brand slug 404 **PASS** |
| SEO brand | sitemap + schema.org in render property (codice); live **NOT VERIFIED** |
| SEO ImmobilCloud React | dipende da `setupProxy` OG tags; crawl JS **NOT VERIFIED** |
| Responsive / browser | **NOT VERIFIED** (no UI walkthrough autorizzato come mutativo; ambiente senza inventory) |
| Coerenza FE↔API | route UUID allineate **PASS** codice |

---

## 9. Confronto decisioni OMNIA

| Tema | Tipo | Dettaglio |
|------|------|-----------|
| Isolamento tenant brand `/p` | 3 — implementato, verifica live incompleta | filter agency OK in codice |
| Privati fuori MLS | 1 conforme | D-126 + isolation tests PASS |
| Matching privati→agenzie gratis | 1 conforme | non pay-to-unlock |
| Free 2 annunci | 1 conforme | PRICING_B2C |
| Privacy L1–L4 | 3 — implementato, **non verificato** E2E qui | test suite bloccata |
| Strip ID interni pubblici | 5 / 4 aperto | A4 strip vs ImmobilCloud agency card — **serve decisione Founder** |
| Clone sito D-130 | 2 — approvato, pipeline incompleta (nota storica DECISIONS) | fuori deep di questo audit ma blocco commerciale sito |
| D-125 atti | 2 — non shippato | box «presto disponibile» |

---

## 10. Registro problemi (priorità)

### Dimostrati
| ID | P | Problema | Fix test |
|----|---|----------|----------|
| C1 | **P1** | Photo endpoint più permissivo della superficie pubblica | private/pending `active` → photo 404 |
| C2 | **P2** | `agency.id` / `agency_id` in API ImmobilCloud pubbliche | policy + assert absence o whitelist esplicita |
| C3 | **P2** | Contact response espone `lead_id`/`client_id` | response opaca |
| E1 | **P1** | Staging senza inventory ImmobilCloud → impossibile staging-deep B2C | seed sintetico isolato + deep |

### Sospetti / incompleti
| ID | P | Problema | Serve |
|----|---|----------|-------|
| S1 | P2 | Agency doc completo in `_resolve` → HTML | projection agency + sample HTML |
| S2 | P2 | Cache lunga foto dopo unpublish | test withdraw→fetch cache |
| S3 | P1? | Privacy E2E | seed + riesecuzione `test_m3s9_privacy_audit` |
| S4 | P2 | Contact E2E cross-tenant | harness sintetico (mutativo autorizzato) |

### Miglioramenti P3
- View bump su GET detail (side-effect lettura) — accettabile prodotto, documentare
- Test FE cloud property/contact assenti
- Assert espliciti `agency_id` policy nei test pubblici ImmobilCloud

---

## 11. Copertura test esistenti vs flussi

| Flusso | Test esistenti | Adeguatezza |
|--------|----------------|-------------|
| Search/facets pubblici | `test_immobilcloud_public` | Media — richiedono API+DB seed |
| Contact | `test_immobilcloud_m3s4_contact` | Buona se DB seed |
| Visibility SoT | `test_s4_public_visibility` | Buona (unit) |
| Privacy gate | `test_m3s9_privacy_audit` | Presente; **non green** qui |
| Photo ACL vs visibility | **assente** | gap critico |
| `/p/{slug}` cross-tenant | parziale `test_themes` | insufficiente senza assert cross-slug |
| Free tier / slot | `test_m3s5_private_listings`, `test_b2c_listing_publish` | presenti |
| Matching privato | dipendenze D-126 | da rafforzare regressione isolamento |

---

## 12. Dipendenze staging / esterni

- Mongo staging con listing pubblici ImmobilCloud (**oggi 0**)
- Credenziali seed per privacy/contact tests
- Object storage per foto reali
- Resend (solo se test email — **non** in questo incarico)
- Stripe Test solo se ciclo publish a pagamento (non eseguito)
- **Non** assumere che staging = tip `main` bit-a-bit; path cloud presenti, inventory vuota

---

## 13. Decisioni funzionali indispensabili (non tecniche)

1. **Policy ID agenzia sul portale ImmobilCloud:** l’UUID agenzia deve restare pubblico (card) o va mascherato come su MLS public search?
2. **Photo ACL:** conferma che ogni media pubblico deve rispettare **esattamente** `public_surface_base` (+ regole brand se servito da `/p`)?
3. **Contact response:** OK restituire ID CRM al browser anonimo?

Tutto il resto (projection agency HTML, cache) può procedere come hardening tecnico sotto queste risposte.

---

## 14. Prossimo ciclo tecnico proposto (ordine)

1. **Seed sintetico isolato** ImmobilCloud su staging (no fixture distruzione) + conferma SHA deployato.  
2. **Fix P1 photo filter** allineato a SoT + test regressione.  
3. **Chiusura policy C2/C3** + patch + test.  
4. **Staging-deep B2C** (search, detail L1, `/p/{slug}` cross-tenant, contact su dati sintetici, owner sell free-tier, matching smoke).  
5. **Riesecuzione privacy suite** con seed.  
6. Solo dopo PASS: valutazione GTM B2C / eventuale ciclo D-130 clone.

---

## 15. Limiti di questo audit

- Nessuna implementazione / commit / push / deploy  
- Nessun contact POST / seed / delete  
- Staging inventory vuota → molte celle **NOT VERIFIED** live  
- Privacy/contact HTTP tests falliti per auth seed assente  
- Browser FE non percorso end-to-end senza dati  

---

## 16. Conclusione per il Founder

ImmobilCloud ha fondamenta coerenti con le decisioni su **free listings** e **matching non paywalled**, e un contratto di visibilità S4 chiaro tra portale e brand. **Non** è ancora un prodotto pubblico affidabile per il mercato: manca inventory di verifica, resta un **P1** sul filtro foto, restano disclosure di identificativi e un debito di test E2E.

**Raccomandazione:** autorizzare un ciclo «B2C public hardening + staging-deep» con seed sintetico, **senza** dichiarare readiness commerciale prima del PASS su C1 e sullo scenario `/p/{slug}`+contact multi-tenant.

**Stato:** fermo in attesa valutazione Founder.

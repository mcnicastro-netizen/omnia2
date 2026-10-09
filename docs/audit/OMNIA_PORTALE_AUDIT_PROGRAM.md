# OMNIA — Programma Audit Portale ImmobilCloud (passo × passo)

**Status**: ▶️ IN ESECUZIONE — Onde A–G fatte · Onda G **GREEN** (2026-10-09) · fix solo con «vai»  
**Partenza**: **8 Ottobre 2026**  
**Tunnel giorno 1**: `https://king-kai-mia-giants.trycloudflare.com` · **corrente**: vedi diario del giorno  
**Finding**: `docs/audit/portale-finding.md`  
**Owner esecuzione**: Cloud Agent + Founder (gate «vai» su fix)  
**Repo SoT**: `mcnicastro-netizen/omnia2` (GitHub)  
**Ambito**: portale B2C ImmobilCloud (`/it/cloud/*`) + superfici B2C collegate (`/it/legal`, checkout, auth cloud)  
**Fuori ambito diretto**: deep-dive gestionale CRM interno (`/it/app/*`) salvo i **punti di contatto** con il portale  
**Regole vincolanti**: D-051 onestà · D-115 no self-serve finché O6≠PASS · secret mai in git/PR · Stripe **solo `sk_test_`** in Cloud · push `main` solo su ordine Founder  

---

## 0. Scopo e regole di lavoro

### 0.1 Obiettivo
Produrre un **fascicolo audit** completo del portale: funzionamento, codice, API key, flussi verso super_admin, bottoni, rapporto gestionale, GDPR + AI Act, anti-crash / dati / Stripe — più tutto ciò che emerge come necessario.

### 0.2 Cosa NON si fa durante il programma (salvo «vai» Founder)
- Nessun redesign UI “di gusto”
- Nessun merge su `main` senza ordine
- Nessuna chiave live Stripe
- Nessuna modifica codice di prodotto **durante** le onde di analisi (solo note, matrice, report). I fix partono in onde successive con «vai» esplicito su finding numerati.

### 0.3 Deliverable obbligatori (ogni giorno)
| Artefatto | Dove |
|--|--|
| Log diario | `docs/audit/portale-diario/YYYY-MM-DD.md` |
| Matrice check (PASS/FAIL/SKIP + evidenza) | `docs/audit/portale-matrici/` |
| Finding numerati `P-###` | sezione Finding del fascicolo + aggiornamento `OMNIA_AUDIT_STATE.md` |
| Screenshot / log | `/opt/cursor/artifacts/` (Cloud) — path citati nel diario |

### 0.4 Severità finding
| Codice | Significato | Azione tipica |
|--|--|--|
| **P0** | Blocca dogfood / denaro / leak dati | Fix immediato con «vai» |
| **P1** | Funzione portale rotta o compliance grave | Fix prima go-live pagamenti |
| **P2** | UX / debito / gap documentale | Coda post-test |
| **P3** | Nice-to-have / osservazione | Backlog |

### 0.5 Ambiente di prova (ogni mattina, prima di qualsiasi check)
1. `bash scripts/omnia-stack.sh ensure` → API 43121, preview 43123, tunnel OK  
2. Mongo up (`ensure-system-deps` / mongod)  
3. `bash scripts/check-secrets-presence.sh` → solo present/missing, **mai valori**  
4. Annotare `public_url` del giorno (trycloudflare ruota)  
5. Confermare `GET /api/billing/plans` → `mode=test` (mai live)  
6. Login Founder + account dogfood B2C pronti (credenziali da `.env` / seed, non in questo file)

---

## Calendario esecutivo (partenza 8 Ott 2026)

### Piano originale

| Giorno | Data | Onda | Focus |
|--|--|--|--|
| D1 | gio 8 Ott | **Onda A** | Funzionamento end-to-end portale |
| D2 | ven 9 Ott | **Onda B** | Analisi codice **solo** portale |
| D3 | sab 10 Ott | **Onda C** | Inventario API key |
| D4 | dom 11 Ott | **Onda D** | Prova live key / provider |
| D5 | lun 12 Ott | **Onda E** | Informazioni → super_admin + Ops |
| D6 | mar 13 Ott | **Onda F** | Matrice bottoni |
| D7 | mer 14 Ott | **Onda G** | Portale ↔ gestionale |
| D8 | gio 15 Ott | **Onda H** | GDPR + AI Act |
| D9 | ven 16 Ott | **Onda I** | Anti-crash / dati / Stripe |
| D10 | sab 17 Ott | **Onda J** | Fascicolo + priorità fix |

### Catch-up reale (8 Ott sera)

| Data | Onda | Stato |
|--|--|--|
| 8 Ott | **A–E** | ✅ fatte (anticipate) · D GREEN · P-025…P-030 chiusi |
| 9 Ott | **F** | ✅ **GREEN** · P-031 CHIUSO · P-032 P3 residuo |
| 9 Ott | **G** | ✅ **GREEN** · ponti verificati · P-033…P-036 aperti |
| succ. | **H** | GDPR + AI Act — attende «vai» |
| poi | **I** | Resilienza |
| poi | **J** | Fascicolo |

> Se un giorno slitta: **non saltare onde**; si sposta in avanti. Dettaglio giornata: `memory/NEXT_SESSION.md`.

---

## Onda A — Controllo in profondità del funzionamento del portale (D1)

**Obiettivo**: ogni percorso utente B2C funziona o è documentato come FAIL con riproduzione.

### A.0 Inventario superfici (checklist path)
Barrare ogni path dopo smoke HTTP 200 + render senza errore console bloccante:

#### Nav primaria (`CloudTopNav`)
- [ ] `/{lang}/cloud` — Home  
- [ ] `/{lang}/cloud/search` — Cerca casa  
- [ ] `/{lang}/cloud/valutatore` — Valuta gratis  
- [ ] `/{lang}/cloud/mutui` — Mutui  
- [ ] `/{lang}/cloud/visura` — Visura  
- [ ] `/{lang}/cloud/register?intent=sell` — Vendi casa  
- [ ] Logo → home  
- [ ] Account / Area riservata (anon vs loggato)  
- [ ] LanguageSwitcher (almeno `it` ↔ `en` se attivo)  
- [ ] NotificationBell (solo loggato) — click, empty state, errore  

#### Auth / account
- [ ] `/{lang}/cloud/register` — registrazione nuova email  
- [ ] Registrazione email già esistente → comportamento atteso (auto-login / messaggio)  
- [ ] Login da area portale / redirect `next=`  
- [ ] `/{lang}/cloud/account` — dashboard account  
- [ ] Logout (se esposto) e sessione cookie sul tunnel HTTPS  

#### Annunci / ricerca
- [ ] Search: filtri base, risultati, empty state, paginazione/scroll  
- [ ] `/{lang}/cloud/property/:pid` — scheda pubblica L1/L2  
- [ ] Scheda L3/L4 — anonimo non vede (404 o gate)  
- [ ] Contatto annuncio / inquiry (GDPR checkbox obbligatorio)  
- [ ] Preferiti: add/remove  
- [ ] Saved search: crea / attiva / frequenza / elimina  

#### Vendi (UGC)
- [ ] `/{lang}/cloud/account/sell` — crea annuncio  
- [ ] Modifica annuncio + scroll/focus corretto  
- [ ] Upload media tmp  
- [ ] Submit moderazione  
- [ ] Delete  
- [ ] Boost checkout (sandbox)  
- [ ] Staging foto checkout (se esposto)  

#### Strumenti a pagamento / free
- [ ] Valutatore base (lead magnet)  
- [ ] Valutatore UNI + PDF paywall Stripe test  
- [ ] Visura: demo RM sandbox → Paga → webhook/sync → Scarica PDF  
- [ ] Mutui: form/simulazione, limiti, errori  
- [ ] Checkout success / cancel pages  

#### HAL Legal (superficie B2C collegata)
- [ ] `/{lang}/legal` raggiungibile da nav se presente (o deep link)  
- [ ] Paywall €1 / credito query  
- [ ] Disclaimer obbligatorio  
- [ ] Risposta + citazioni o errore onesto  

#### Footer / legali link
- [ ] Ogni link FooterB2C (privacy, cookie, termini, contatti, …) — 200 o destinazione dichiarata  
- [ ] Nessun link morto 404 silenzioso  

### A.1 Matrice persona × flusso
Per ciascuna riga: **PASS / FAIL / BLOCKED**, URL, screenshot, note.

| # | Persona | Flusso | Esito |
|--|--|--|--|
| A1 | Anonimo | Home → search → scheda → contatto | |
| A2 | Anonimo | Valutatore base | |
| A3 | Anonimo | Visura senza login → register gate | |
| A4 | Client nuovo | Register → account → preferito | |
| A5 | Client | Vendi → publish → stats | |
| A6 | Client | Visura paid → PDF | |
| A7 | Client | HAL Legal paid query | |
| A8 | Client | Boost annuncio | |
| A9 | Client EN | Nav + una pagina chiave in `en` | |

### A.2 Criteri di chiusura Onda A
- [ ] Matrice A1–A9 compilata  
- [ ] Elenco bug P0/P1 aperti  
- [ ] Diario D1 firmato  

---

## Onda B — Analisi codice solo portale (D2)

**Obiettivo**: mappa codice 1:1 superfici ↔ file, senza toccare CRM salvo import condivisi.

### B.1 Perimetro codice (whitelist)
Includere:
- `frontend/src/apps/immocloud/**`
- `frontend/src/apps/legal/**` (HAL Legal B2C)
- Route cloud in router root (mount `/cloud`)
- `backend/apps/immocloud/**`
- `backend/apps/billing/b2c_*.py`, prodotti B2C, webhook side-effects B2C
- `backend/apps/immoweb/al_legal/**` solo endpoint usati dal portale Legal  
- Shared usati dal portale: `shared/lib/api`, auth cookie, ErrorBoundary, email templates B2C  

Escludere dall’analisi “solo portale” (rimandare a G):
- `frontend/src/apps/immoweb/**` (CRM) salvo link/bridge  
- Seed CRM, sync portali Idealista, ecc. salvo impatto listing pubblici  

### B.2 Checklist analisi per modulo
Per ogni modulo (Home, Search, Property, Account, Sell, Valuator, Visura, Mutui, Legal, Auth cloud, Checkout):

1. [ ] File FE entry + componenti figli  
2. [ ] Endpoint BE chiamati (metodo + path)  
3. [ ] Collection Mongo lette/scritte  
4. [ ] Authz: anon / client / roles  
5. [ ] Side-effect denaro (Stripe product_key)  
6. [ ] Side-effect AI/provider  
7. [ ] Error path (timeout, 4xx, 5xx) e messaggio utente  
8. [ ] `data-testid` presenti / mancanti  
9. [ ] Dead code / TODO / “presto disponibile”  
10. [ ] Rischio sicurezza (IDOR, path traversal media, PII in log)  

### B.3 Deliverable Onda B
- [x] Tabella `modulo → files → endpoints → rischi` → `portale-matrici/2026-10-08-onda-b.md`  
- [x] Finding codice `P-009…P-017` → `portale-finding.md`  
- [x] Diagramma mermaid flussi soldi B2C (Visura / UNI / Legal / Boost)  

---

## Onda C — Agganci API key che riguardano il portale (D3)

**Obiettivo**: elenco esaustivo nomi secret → dove usati nel portale → obbligatorio/opzionale.

### C.1 Inventario (nomi solo — valori mai in git)
Per ogni riga: Presente in vault? Usato da path portale? Fail-soft?

| Secret | Uso portale atteso | File tipici | Obbligatorio dogfood? |
|--|--|--|--|
| `STRIPE_SECRET_KEY` (`sk_test_`) | Checkout Visura/UNI/Legal/Boost | `b2c_checkout`, `visura_b2c`, webhook | Sì |
| `STRIPE_PUBLISHABLE_KEY` | Eventuale Stripe.js FE | billing FE | Se Checkout hosted URL-only: verificare |
| `STRIPE_WEBHOOK_SECRET` | Firma webhook | `billing/routes.py` | Sì (tunnel) |
| `STRIPE_ENABLED` | Gate billing | env | Sì = true in sandbox |
| `OPENAPI_*` / chiavi Catasto | Visura fulfillment | client OpenAPI | Sì per PDF reale sandbox |
| `TAVILY_API_KEY` | HAL Legal search | `al_legal` | Consigliato |
| `GEMINI_API_KEY` (o alias) | Valutatore / Legal / improve se esposto | LLM shared | Sì se AI on |
| `FAL_KEY` | Staging B2C foto | staging jobs | Se feature on |
| `RESEND_API_KEY` | Email register, alert preferiti, inquiry | email client | Sì mail reali |
| `GOOGLE_CLIENT_ID` | Login Google B2C | auth Google | Opzionale |
| `JWT_SECRET` | Sessioni | auth | Sì |
| `FRONTEND_BASE_URL` | Link in email | saved_searches, fanout | Verificare vs tunnel |
| Altri emersi in B | … | … | … |

### C.2 Checklist agganci
- [x] Ogni `os.environ.get` nel perimetro B mappato  
- [x] Nessuna chiave hardcodata in FE build  
- [x] FE non punta a `127.0.0.1:43121` in build tunnel (same-origin `/api`)  
- [ ] Webhook Stripe endpoint = URL tunnel corrente + `/api/billing/webhook` *(verifica Dashboard → Onda D)*  
- [x] Allineamento con `memory/CLOUD_SECRETS_INVENTORY.md` (solo nomi)  

### C.3 Deliverable Onda C
- [x] Tabella secret→uso→gap → `docs/audit/portale-matrici/2026-10-08-onda-c.md`  
- [x] Lista “manca in vault” per Founder (senza valori) · finding P-018…P-021  

---

## Onda D — Controllo funzionamento delle stesse key (D4)

**Obiettivo**: prova live **sandbox** di ogni provider usato dal portale.  
**Stato**: ✅ **GREEN** 2026-10-08 (ripresa) · matrice `portale-matrici/2026-10-08-onda-d.md` · P-022/P-023 CHIUSI · gap P-025/P-026

### D.1 Protocollo prova (per provider)
1. Check presence (length > 0)  
2. Chiamata minima non distruttiva  
3. Chiamata flusso portale reale (dogfood)  
4. Esito in matrice: OK / FAIL / MOCK / SKIP  
5. Se FAIL → finding P0/P1 + log redatti  

### D.2 Matrice provider
| Provider | Smoke | Flusso portale | Esito |
|--|--|--|--|
| Stripe test | plans `enabled=true` **`mode=test`** | Checkout €1 `b2c_hal_legal_query` → paid | **OK** (P-022 CHIUSO) |
| Stripe webhook | sync endpoint tunnel · signed 200 | `checkout.session.completed` → paid | **OK** |
| OpenAPI Catasto | OAuth single-key + PDF 58KB | catalog `openapi_enabled=true` (D-116) | **OK** (P-023 CHIUSO) |
| Gemini | HAL knowledge/ask 200 | product OK | **OK** |
| Tavily | absent | — | **SKIP** |
| fal | models 200 | staging render SKIP soft | **OK** |
| Resend | domains 200 | outbound SKIP soft | **OK** |
| Google OAuth | absent | button OFF | **SKIP** |
| Mongo | health db=ok | persist | **OK** |

### D.3 Stripe — controlli speciali
- [x] Solo `sk_test_` / `pk_test_` → **OK**  
- [x] Nessun `sk_live_` attivo nel process → **OK**  
- [x] Webhook secret allineato (handler 200 in-run) → **OK** · vault Environment da aggiornare (P-026)  
- [ ] `b2c_purchases.amount_eur` popolato → **FAIL** P-025  
- [ ] Ops Founder vede incasso per voce (D-117 se merged; altrimenti annotare dipendenza PR) → deferred Onda E  

### D.4 Criteri chiusura Onda D
- [x] Matrice provider completa  
- [x] Zero P0 key “silenti” → **P-022 CHIUSO** · Onda D **GREEN**

---

## Onda E — Informazioni che devono arrivare in super_admin (D5)

**Obiettivo**: definire e verificare **cosa il Founder deve vedere** per ogni evento portale.  
**Stato**: ✅ analisi 2026-10-08 · matrice `portale-matrici/2026-10-08-onda-e.md` · finding P-027…P-030

### E.1 Catalogo eventi → destinazione Ops
Per ogni evento: oggi arriva? dove? gap?

| Evento portale | Destinazione attesa | Stato oggi |
|--|--|--|
| Registrazione client B2C | conteggio / lista? | **GAP** solo DB → P-027 |
| Inquiry su annuncio | email agenzia + audit | OK tenant CRM · UGC → **GAP** Ops P-027 |
| Annuncio UGC submit | coda moderazione CRM | **OK** `/it/app/moderation` · no nav P-030 |
| Pagamento Visura | Ops finance + ricevuta B2C | finance cieco P-025 · ricevuta **A-038** |
| Pagamento UNI PDF | Ops finance | P-025 |
| Pagamento HAL Legal | Ops finance + legal ops | finance P-025 · Legal volume OK |
| Boost / staging paid | Ops finance + listing flags | PARZIALE P-025 |
| Webhook firma fail | `ops_alerts` | **OK** |
| AI provider down | `ops_alerts` | **OK** (codice) |
| Saved-search digest inviato | log / conteggio | **GAP** P-027 |
| Errore OpenAPI Visura | order failed + alert? | order sì · alert **no** → P-027 |
| Login Google nuovo user | ? | SKIP P-021 |
| Contatto / lead mutui | ? | **GAP** `mortgage_leads` only → P-027 |

### E.2 Checklist UI super_admin
- [x] `/it/app/ops` — scheda/voci/alert OK · fatture/ricevute **assenti** · revenue B2C €0 (P-025)  
- [x] `/it/app/ops/legal` — volume Legal OK  
- [x] Coda moderazione = `/it/app/moderation` (+ API `/api/app/moderation/queue`)  
- [x] Backup health — presente in UI ma status **MISSING** (P-029)  
- [x] Alert: messaggi generici OK · Legal `top_users` *può* esporre email (n=0 in prova)

### E.3 Deliverable
- [x] Spec “telemetry minima Founder” (gap list) in matrice Onda E §E.3  
- [x] Link ad **A-038** (fattura/dati fiscali) come post-test già registrato  
- [x] Finding: P-027…P-030 (+ P-025 confermato)

---

## Onda F — Controllo di tutti i bottoni del portale (D6)

**Obiettivo**: matrice esaustiva controllo × controllo.  
**Stato**: ✅ **GREEN** 2026-10-09 · matrice `portale-matrici/2026-10-09-onda-f.md` · P-031 CHIUSO · P-032 P3

### F.1 Metodo
1. Estrarre da FE tutti i `<button`, `onClick`, `Link` CTA, `type="submit"` nel perimetro immocloud+legal+footer  
2. Per ciascuno: `data-testid` (o selettore), label, pagina, azione attesa, auth richiesta, denaro?, esito prova  
3. Prova manuale (computer use) + nota console/network  

### F.2 Template riga matrice bottoni
`ID | Pagina | Label/testid | Azione attesa | Precondizione | Esito | Evidenza | Finding`

### F.3 Zone obbligatorie
- [ ] Top nav (desktop + menu mobile se esiste)  
- [ ] Home hero CTA  
- [ ] Search filters / sort  
- [ ] Property: preferito, contatto, WhatsApp/tel, share  
- [ ] Account: saved search toggles, delete, link sell  
- [ ] Sell: salva, pubblica, elimina, boost, staging, upload  
- [ ] Valutatore: stima, paga PDF  
- [ ] Visura: demo fill, paga, scarica PDF  
- [ ] Mutui: submit  
- [ ] Legal: paga / invia domanda  
- [ ] Register/login  
- [ ] Footer  
- [ ] Cookie/banner se presente  

### F.4 Chiusura
- [ ] 100% bottoni catalogati  
- [ ] 100% provati o SKIP motivato (es. live-only)  

---

## Onda G — Rapporto portale ↔ gestionale (D7)

**Obiettivo**: ogni ponte dati/azioni tra B2C e CRM è tracciato e verificato.

### G.1 Ponti da verificare
| Ponte | Direzione | Check |
|--|--|--|
| Annuncio agenzia → scheda cloud | CRM→Portale | listing pubblico, foto, prezzo, privacy L* |
| Annuncio UGC → moderazione CRM | Portale→CRM | submit, approve/reject, visibilità |
| Inquiry portale → lead/cliente CRM | Portale→CRM | create + email + dedup |
| Privacy L1–L4 | CRM setting→Portale gate | anon vs auth |
| Crediti agenzia vs carta B2C | separazione rail | B2C mai scala crediti (D-075/listino) |
| HAL Legal in-app vs portale €1 | prodotti distinti | |
| Brand/sito agenzia vs ImmobilCloud | isolamento | |
| Notifiche saved-search | job→email B2C | |
| Domain / slug agenzia vs path cloud | no collision | |

### G.2 Checklist
- [x] Creare annuncio in CRM demo → compare in search cloud  
- [x] Privacy L3 in CRM → anon 404 in cloud  
- [x] Inquiry da cloud → record lato agenzia  
- [x] UGC approvato → live; rifiutato → non live  
- [x] Nessuna API cloud che muta dati agenzia senza authz  

### G.3 Deliverable
- [x] Diagramma ponti — `docs/audit/portale-matrici/2026-10-09-onda-g.md`  
- [x] Finding isolation / leak — P-033…P-036 

---

## Onda H — Portale ↔ GDPR e AI Act (D8)

**Obiettivo**: gap analysis normativa **applicata al portale** (onesta, non legale sostitutiva del commercialista/avvocato).

### H.1 GDPR — checklist portale
| Tema | Domanda di audit | Esito |
|--|--|--|
| Base giuridica | Consensi espliciti dove servono (inquiry, marketing)? | |
| Informativa | Link privacy accessibile e coerente? | |
| Cookie | Banner/preferenze se tracking; oggi no Analytics — confermare | |
| Diritti interessato | Export / erase B2C — esiste o gap (rif. finding G-* audit)? | |
| Minimizzazione | Campi raccolti vs necessari (Visura, register, inquiry) | |
| Conservazione | TTL `b2c_purchases`, audit, media UGC | |
| Sub-responsabili | Stripe, Resend, OpenAPI, Gemini, Tavily, fal — citati? | |
| Data breach readiness | Log PII redatti? | |
| Minori | Età / blocco? | |
| Trasferimenti extra-UE | provider AI/US — trasparenza | |

### H.2 AI Act (UE) — checklist portale
| Tema | Domanda | Esito |
|--|--|--|
| Ruolo sistema | HAL Legal / Valutatore / staging = cosa dichiariamo all’utente? | |
| Trasparenza | Utente sa che è AI? Disclaimer Legal? | |
| Divieti / alto rischio | Valutazione immobiliare automatizzata — classificazione interna onesta | |
| Human oversight | Come si contesta una stima / risposta Legal? | |
| Log & tracciabilità | `al_legal_audit`, valuator logs | |
| Dati training | Non usiamo dati cliente per train — verificabile? | |
| Deepfake / staging | Disclosure foto generate? | |
| Minori / vulnerabili | N/A o gap | |

### H.3 Deliverable
- [ ] Tabella conformità: OK / GAP / N/A  
- [ ] Priorità legali vs prodotto (nessun claim “siamo compliant” senza evidenza)  
- [ ] Eventuale voce backlog A-xxx se mancante  

---

## Onda I — Anti-crash, salvaguardia dati, Stripe, resilienza (D9)

### I.1 Anti-crash / UX failure
- [ ] `ErrorBoundary` cloud cattura crash React  
- [ ] API down → messaggio onesto, no spinner infinito  
- [ ] Timeout AI (es. improve/legal) documentati  
- [ ] Upload media fail → retry/messaggio  
- [ ] Double-submit checkout prevenuto  
- [ ] Tunnel cambio URL → cookie/login; webhook stale  

### I.2 Salvaguardia dati
- [ ] Backup health in Ops (D-105) — include collection B2C?  
- [ ] Restore procedure menziona `b2c_*` / media UGC?  
- [ ] Soft-delete vs hard-delete annunci privati  
- [ ] Indici Mongo essenziali presenti  
- [ ] Nessuna cancellazione automatica aggressiva (D-098) inattesa  

### I.3 Stripe & pagamenti
- [ ] Sandbox only in Cloud  
- [ ] Webhook idempotente  
- [ ] Sync fallback se webhook manca (Visura)  
- [ ] Alert firma non valida non ripetuti post-fix secret  
- [ ] Riconciliazione Ops vs Stripe Dashboard test  
- [ ] Nota A-038 fatture/dati fiscali = post-test, non bloccante audit  

### I.4 Sicurezza applicativa portale
- [ ] Cookie `Secure` / `SameSite` su HTTPS tunnel  
- [ ] CORS / CSRF su mutazioni  
- [ ] Rate limit register, inquiry, Legal, Visura  
- [ ] IDOR su `/cloud/me/properties/{id}`  
- [ ] Download Visura solo owner paid  
- [ ] Secrets non in bundle FE  

### I.5 Deliverable
- [ ] Checklist I firmata  
- [ ] P0 sicurezza se emergono  

---

## Onda J — Extra necessari + chiusura fascicolo (D10)

### J.1 Extra che il programma include comunque
1. **i18n** — stringhe mancanti / fallback IT su pagine soldi  
2. **Accessibilità base** — focus, contrast CTA primarie, `sr-only` titoli  
3. **Performance** — LCP home/search su tunnel; immagini  
4. **SEO tecnico** — title/meta scheda, noindex ambienti demo se serve  
5. **Moderazione UGC** — tempi, stati, notifiche utente  
6. **Email fanout** — preferiti ended / price drop (A-029/030) lato B2C  
7. **Mobile** — nav nascosta md:flex: come si naviga su telefono?  
8. **Observability** — log strutturati portale; cosa manca a Founder  
9. **Disaster tunnel** — runbook “tunnel morto / nuovo URL / aggiorna webhook”  
10. **Dipendenze PR aperte** — elenco PR che l’audit assume (es. D-117 Ops finance)  
11. **QC scripts esistenti** — `preprod_confidence_gate`, stress cloud: cosa coprono già vs gap  
12. **Confronto promise marketing vs codice** (D-051) — landing vs portale reale  

### J.2 Fascicolo finale (obbligatorio)
Documento unico: `docs/audit/OMNIA_PORTALE_AUDIT_FASCICOLO.md` con:
1. Executive summary Founder (1 pagina)  
2. Scorecard onde A–J  
3. Registro finding P-001… ordinato per severità  
4. Matrici (link)  
5. Lista «vai» consigliati (fix P0/P1) vs backlog  
6. Ripresa A-037 / A-038 / O6 se impattati  

### J.3 Criteri di chiusura programma
- [ ] Tutte le onde A–J chiuse o esplicitamente rimandate con data  
- [ ] Nessun P0 aperto senza issue/finding e proposta fix  
- [ ] Founder ha ricevuto fascicolo + priorità  

---

## Rituale giornaliero (da D1 in poi)

```
09:00  Ambiente ensure + secrets presence + URL tunnel
09:15  Ripresa finding aperti giorno prima
09:30  Esecuzione onda del giorno (checklist)
…      Evidenze in /opt/cursor/artifacts + matrici
18:00  Diario + aggiornamento finding + messaggio Founder sintetico
       STOP codice prodotto salvo P0 con «vai» esplicito
```

---

## Dipendenze e paralleli già noti

| Voce | Ruolo rispetto a questo programma |
|--|--|
| **D-117** Ops finance | E verifica segnali soldi in Onda E (se merged) |
| **A-038** Fattura + dati fiscali | Post-test; citare in E/H/I, non implementare qui |
| **A-037** Demo da sito | Fuori portale puro; non blocca A–J |
| **O6** Self-serve | Resta OFF; audit non abilita pagamenti pubblici live |
| Dogfood Visura già OK | Baseline Onda A/D — non rifare da zero, **ripetere regressione** |

---

## Esito atteso per il Founder

Al termine (target **17 Ott 2026**):  
sapere **esattamente** cosa nel portale funziona, cosa no, quali key reggono, cosa vede il super_admin, quali bottoni sono morti, come parla col gestionale, quali gap GDPR/AI Act, quanto è solido crash/dati/Stripe — e una lista ordinata di fix con priorità.

---

**Approvazione programma**: Founder 7-Ott-2026 (richiesta esplicita “crea solo programma che partirà da domani”).  
**Esecuzione**: da **8-Ott-2026**, onda A.

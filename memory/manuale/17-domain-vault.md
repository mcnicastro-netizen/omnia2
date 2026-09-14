# Capitolo 17 · Domain Vault — Sovranità digitale dell'agenzia

> **Cosa trovi in questo capitolo**
> Il **Domain Vault** è la promessa contrattuale di OMNIA sulla sovranità digitale delle agenzie: **noi non registriamo mai un dominio a nome nostro** (regola D-054). Ogni agenzia possiede il suo dominio, con i suoi contatti registrant. OMNIA offre **help-to-connect**, non transfer di ownership. Il capitolo copre: la promessa D-054 nel dettaglio, i **3 componenti reali** (Domain Vault sovereignty confirm, Custom Domain DNS verification, Domain Checker RDAP pubblico), il flusso DNS TXT + CNAME, il rate limit del checker pubblico, l'audit trail append-only, e i limiti onesti v1.

**Cosa NON è (D-051 onestà)**
- Non è un **registrar**. OMNIA **non registra** domini al posto tuo, **non paga la rinnovo**, **non gestisce** il pannello DNS al tuo posto (a meno che tu ce lo chieda esplicitamente e ne firmi mandato — flusso separato e manuale, non v1).
- Non è un **DNS provider**. Il tuo dominio resta al tuo registrar (Register, GoDaddy, Aruba, ecc.). OMNIA fornisce solo un **target CNAME/ALIAS** verso cui puntare il tuo dominio.
- Non è un **transfer di dominio**. Il flusso "help-to-connect" collega il tuo dominio esistente al sito OMNIA — **non trasferisce ownership**. Se domani lasci OMNIA, ripunti il DNS altrove e il dominio è ancora tuo.
- Non è un **WHOIS lookup**. Il checker pubblico usa **RDAP** (Registration Data Access Protocol) — il successore del WHOIS. Se il TLD del dominio non supporta ancora RDAP, il check fallisce con messaggio dedicato.

---

## 17.1 · La promessa D-054 · sovranità digitale dell'agenzia

**In una frase**
Il dominio del tuo brand è tuo. OMNIA lo tratta con la stessa serietà con cui tratta i tuoi clienti: **non lo intesta a se stessa, non lo condivide, non lo blocca**. Se decidi di lasciare OMNIA, il tuo dominio ti segue.

**La regola cardine (`domain_vault.py:3-9`)**
> *"Contractual promise: OMNIA never registers a domain on its own name. Every agency owns its domain."*

**Perché esiste**
- **Fiducia**: la maggior parte delle piattaforme SaaS del settore trattiene domini a nome loro come strumento di lock-in.
- **Portabilità**: se un domani decidi di cambiare piattaforma, il dominio è già tuo — nessuna trattativa, nessun riscatto.
- **Compliance GDPR**: il registrant deve essere identificabile (tu/la tua agenzia), non un intermediario tecnico.

**Cornice normativa (contesto, non consulenza)**
- **Regolamento ICANN** sulla registrazione domini: il registrant è il titolare legale del nome.
- **GDPR (Reg. UE 2016/679)**: dati registrant contengono dati personali → protezione applicabile.

**Documento pubblico**
`/it/domain-sovereignty-policy` (`DomainSovereigntyPolicyPage.jsx`): pagina statica che espone la promessa contrattuale a chiunque, anche non-utenti. Data-testid: `domain-sovereignty-policy-page`.

[SCREEN: domain-sovereignty-policy]

---

## 17.2 · I 3 componenti del Domain Vault

**A cosa serve capirlo**
Il "Domain Vault" nel manuale è un **concetto ombrello** che copre 3 pezzi di codice distinti nel backend. Sapere come si mappano ti aiuta a orientarti quando qualcosa non funziona.

**Le 3 API backend**

| # | File | Prefix API | Ruolo |
|:-:|------|:-:|-------|
| 1 | `domain_vault.py` (155 righe) | `/agencies` sotto `/api/app` | Registrare la conferma di sovranità + `existing_domain` opzionale |
| 2 | `custom_domain.py` (454 righe) | `/website` sotto `/api/app` | Workflow DNS verification (TXT + CNAME) per collegare il dominio |
| 3 | `domain_check.py` (359 righe) | `/domain` sotto `/api/marketing` | Checker RDAP pubblico pre-signup |

**In pratica**
- Vai in **Impostazioni → Domain Vault** → confermi la promessa D-054 → puoi dichiarare (opzionalmente) il tuo `existing_domain`. → **Componente 1.**
- Vai in **Impostazioni → Sito → Dominio personalizzato** → segui il workflow TXT + CNAME. → **Componente 2.**
- Da landing pubblica `/it/verifica-dominio` (senza login) → RDAP check → possibilità di generare lead. → **Componente 3.**

---

## 17.3 · Dove trovare il Domain Vault

**Rotta principale**: nelle Impostazioni agenzia (`/it/app/settings` → sezione **Domain Vault** o **Sovranità digitale**).

**Chi vede la voce**
Ruoli abilitati al POST: `agency_admin`, `super_admin`, `branch_admin`, `group_admin` (require_roles esplicito su `domain_vault.py:100`). Gli `agent` semplici **non vedono** la sezione (né la voce menu).

**Pagine collegate**
- `/it/domain-sovereignty-policy` (pubblica, no login).
- `/it/verifica-dominio` (pubblica, checker RDAP).
- Impostazioni → Sito → Dominio personalizzato (interno).

---

## 17.4 · Confermare la Domain Sovereignty · flusso base

**A cosa serve**
Registrare formalmente che tu (agenzia) hai letto e accettato la promessa D-054. È un check volontario ma **fortemente consigliato** — l'audit trail resta a tua difesa in caso di dispute future.

**Passi operativi**
1. Vai in **Impostazioni → Domain Vault**.
2. Leggi il testo della promessa (rimanda a `/it/domain-sovereignty-policy`).
3. Spunta il checkbox *"Confermo di aver letto la Domain Sovereignty Policy"*.
4. **Opzionale**: se hai già un dominio (`esempio.it`), scrivilo nel campo *"Il mio dominio attuale"*.
5. Clic **Conferma**.
6. Il backend chiama `POST /api/app/agencies/me/domain-sovereignty` con `{"confirmed": true, "existing_domain": "esempio.it"}`.

**Cosa salva il backend**
Sul documento `agencies`:
- `domain_sovereignty_confirmed: true`
- `domain_sovereignty_confirmed_at: <ISO 8601 UTC>` — **preservato** anche se riconfermi in seguito (primo timestamp)
- `existing_domain: "esempio.it"` — normalizzato (rimuove `http://`, `https://`, `www.`, path)

**Idempotenza (`domain_vault.py:119-127`)**
- Se `confirmed=true` la prima volta → salva timestamp
- Se `confirmed=true` di nuovo → **mantiene il primo timestamp** (non lo sovrascrive)
- Se `confirmed=false` → toglie il flag ma **preserva la riga audit** in `domain_vault_events`

**Validazione dominio**
Il campo `existing_domain` passa da `_normalize_domain()`:
- Regex `_DOMAIN_RE`: max 253 char totali, label max 63 char, TLD 2-63 char.
- Errore `400 invalid_domain_format` se non matcha (es. `esempio` senza TLD).
- Se lasci vuoto → `existing_domain: None` (permesso).

[SCREEN: domain-vault-confirm]

---

## 17.5 · Help-to-connect · NON è un transfer

**A cosa serve capirlo**
Se dichiari un `existing_domain` (es. `agenziaesempio.it`), OMNIA **non ne diventa proprietaria**. La dichiarazione serve solo perché OMNIA sa dove aiutarti a collegarlo (workflow DNS §17.6).

**Cosa succede DAVVERO al POST**
- Il campo `existing_domain` viene salvato sul documento `agencies`.
- **Nessuna chiamata al tuo registrar**. Nessuna modifica DNS. Nessun trasferimento.
- Il dominio resta nel tuo pannello registrar, con i tuoi contatti registrant, la tua carta di credito per il rinnovo.
- OMNIA **non chiede mai** le credenziali del tuo registrar.

**Cosa OMNIA fa (con il tuo consenso esplicito)**
- Ti fornisce le **istruzioni DNS** (§17.6): che TXT aggiungere, verso quale CNAME puntare.
- **Tu** applichi le modifiche nel tuo pannello registrar.
- OMNIA **verifica via DNS query** che il tuo dominio punti al target OMNIA.

**Cosa OMNIA NON fa**
- Non compra il dominio per te.
- Non paga il rinnovo.
- Non intesta il registrant a OMNIA S.r.l.
- Non blocca il dominio se lasci OMNIA.

---

## 17.6 · Custom Domain · flusso DNS verification (TXT + CNAME)

**A cosa serve**
Collegare il tuo dominio (`agenziaesempio.it`) al sito OMNIA della tua agenzia, in modo che quando un cliente digita `www.agenziaesempio.it`, arrivi sul tuo sito ospitato da OMNIA.

**Il flusso a 3 fasi (`custom_domain.py:4-14`)**

### Fase 1 — Richiesta
1. Vai in **Impostazioni → Sito → Dominio personalizzato**.
2. Scrivi il dominio (es. `agenziaesempio.it`) → clic **Richiedi collegamento**.
3. Il backend chiama `POST /api/app/website/domain/request`.
4. Il backend:
   - Normalizza il dominio (strip protocollo/www).
   - Genera un **token TXT random** univoco.
   - Salva su `agencies` in stato `pending`.
   - Notifica il super_admin OMNIA via email (per audit).
5. Ricevi in schermata le istruzioni DNS.

### Fase 2 — Tu configuri il DNS (nel tuo pannello registrar)
Aggiungi **due record**:

| Tipo | Host | Valore |
|:-:|------|--------|
| **TXT** | `_omnia-challenge.agenziaesempio.it` | `<token generato da OMNIA>` |
| **CNAME** | `www.agenziaesempio.it` | `<CNAME_TARGET OMNIA>` (es. `edge.omnia.example`) |

**Alternativa apex domain**: se vuoi che `agenziaesempio.it` (senza `www.`) punti a OMNIA, alcuni registrar non supportano CNAME su apex — usa **ALIAS/ANAME** oppure appoggia solo il `www`.

Il **CNAME_TARGET** è definito nell'env `OMNIA_CUSTOM_DOMAIN_CNAME_TARGET` (settato lato server, non modificabile lato UI).

### Fase 3 — Verifica
1. Torna in OMNIA → clic **Verifica DNS**.
2. Il backend chiama `POST /api/app/website/domain/verify`.
3. Il backend risolve:
   - `TXT _omnia-challenge.<domain>` → deve contenere il token generato.
   - `CNAME www.<domain>` → deve puntare a `CNAME_TARGET` (o A record se il registrar ha flat-CNAME).
4. Se entrambi OK → status → `verified`, dominio attivo.
5. Se KO → il pannello mostra cosa manca (TXT non trovato, CNAME sbagliato).

**Perché serve il TXT (anti-takeover)**
Solo chi ha accesso al DNS del dominio può aggiungere il record TXT. Questo previene che qualcuno "rivendichi" un dominio non suo — è il pattern standard usato da Google Search Console, Meta Business, Let's Encrypt.

[SCREEN: domain-dns-instructions]

---

## 17.7 · Domain Checker pubblico · RDAP pre-signup

**A cosa serve**
Uno strumento **pubblico** (accessibile senza login) che permette a un titolare di agenzia di verificare **prima** di iscriversi a OMNIA se il dominio della sua agenzia è correttamente intestato a lui/lei (non a un ex webmaster, non a un provider IT, non redatto/anonimo).

**Dove si trova**
- URL pubblico: `/it/verifica-dominio` (`DomainVerifyPage.jsx`).
- API: `POST /api/marketing/domain/check`.

**Come funziona (`domain_check.py`)**
1. L'utente inserisce il dominio (es. `agenziaesempio.it`) + nome agenzia (opzionale).
2. Il backend fa una **query RDAP** (successore standard del WHOIS).
3. Analizza il registrant:
   - **Corrisponde al nome agenzia?** → ok
   - **È redatto/privacy-proxy?** → warning (GDPR privacy proxy comune)
   - **È il provider IT?** → warning ("il tuo webmaster ha registrato il dominio a nome suo, non tuo")
   - **Scade fra <90 giorni?** → alert
4. L'utente riceve un report interpretato in italiano.

**Rate limit anti-abuso**
Il checker ha un rate limit per IP (`_check_rate_limit`). Se superi la soglia in poco tempo → response 429 (Too Many Requests). Non ti bannano — riprova dopo qualche minuto.

**Se il TLD non supporta RDAP**
Alcuni TLD nazionali (es. certi ccTLD) **non hanno ancora endpoint RDAP**. In quel caso il check restituisce:
> *"Il TLD non supporta ancora RDAP. Riprova più tardi o contattaci per un check manuale."*

**Lead generation opzionale**
Dopo il check, l'utente può cliccare **"Richiedi consulenza"** → `POST /api/marketing/domain/lead` crea un lead marketing nell'agenda OMNIA. Utile per catturare interesse commerciale prima del signup vero.

[SCREEN: domain-checker-pubblico]

---

## 17.8 · RDAP vs WHOIS · perché usiamo RDAP

**Contesto**
Il WHOIS è il protocollo storico (RFC 3912, 2004) per interrogare i dati di registrazione dominio. **RDAP** (Registration Data Access Protocol, RFC 7480-7484) è il suo successore standardizzato — output JSON strutturato, supporto internazionalizzazione, controllo accessi granulare.

**Perché OMNIA usa RDAP e non WHOIS**
- **JSON strutturato**: parsing affidabile (no scraping di testo libero).
- **GDPR ready**: il redacted (anonimizzazione registrant) è nativo.
- **Standard aperto**: tutti i TLD europei stanno migrando.

**Redacted registrant · perché è comune**
Post-GDPR (2018), molti registrar redigono automaticamente i dati registrant dei privati (persone fisiche). Il check RDAP restituisce campi tipo *"REDACTED FOR PRIVACY"* — è normale, non è un problema. Il checker OMNIA lo riconosce con la lista `_REDACTED_TOKENS` (`domain_check.py`).

**Registrant "provider match"**
Se il registrant è tipo *"Aruba S.p.A."* o *"OVH Hosting"*, il checker segnala che il dominio è probabilmente intestato al **provider IT**, non a te. Casi tipici: hai chiesto al webmaster di comprare il dominio e ha usato la sua carta — tecnicamente il dominio è **suo**. Va corretto (transfer registrant al tuo nome, procedura registrar-specifica).

---

## 17.9 · Audit trail · `domain_vault_events` append-only

**A cosa serve**
Ogni conferma/revoca di Domain Sovereignty **lascia una traccia storica** che nessuno può cancellare (nemmeno il super_admin dall'UI).

**Cosa viene salvato (`domain_vault.py:135-143`)**
Ad ogni `POST /agencies/me/domain-sovereignty` viene inserito un documento nella collezione `domain_vault_events`:
- `agency_id`
- `user_id` + `user_email` (chi ha cliccato)
- `confirmed`: true/false
- `existing_domain`: valore dichiarato (o null)
- `at`: timestamp ISO 8601 UTC

**Perché append-only**
Il documento **non viene mai cancellato né aggiornato**. Se sostituisci `esempio.it` con `nuovodominio.it`, resta la riga precedente + nuova riga.

**Come consultare**
Non c'è UI dedicata v1 — solo accesso via API/DB (super_admin OMNIA per dispute o audit legali).

---

## 17.10 · Errori comuni

| Errore | HTTP | Contesto | Soluzione |
|--------|:-:|----------|-----------|
| `invalid_domain_format` | 400 | Domain Vault confirm con dominio malformato | Controlla il dominio (es. deve avere TLD, no spazi) |
| `no_agency` | 404 | L'utente non è collegato ad alcuna agenzia | Verifica il tuo `agency_ids` — sei effettivamente in un'agenzia? |
| `agency_not_found` | 404 | Race condition rara | Refresh pagina |
| TXT non trovato (in verify) | — (payload) | Il record TXT non è ancora propagato o è nel host sbagliato | Attendi 5-30 minuti la propagazione DNS · verifica host = `_omnia-challenge.<domain>` esatto |
| CNAME sbagliato (in verify) | — (payload) | Il CNAME punta a un target diverso | Correggi nel pannello registrar → punta al `CNAME_TARGET` OMNIA |
| CNAME su apex fallito | — (payload) | Il tuo registrar non supporta CNAME su apex | Usa ALIAS/ANAME (Cloudflare, Route53) oppure appoggia solo `www.` |
| Rate limit 429 (domain checker) | 429 | Hai fatto troppi check RDAP dallo stesso IP | Aspetta qualche minuto e riprova |
| TLD non supporta RDAP | — (payload) | ccTLD non ancora migrato | Contatta il team OMNIA per un check manuale |
| Registrant redacted | — (payload warning) | GDPR privacy proxy attivo | Normale per registrant persona fisica — non è un problema |
| Registrant = provider | — (payload warning) | Il dominio è intestato al webmaster/provider IT | Fai un transfer registrant dal tuo registrar |

---

## 17.11 · Limiti onesti v1 (D-051)

**Cosa il Domain Vault NON fa oggi**

- ❌ **Nessuna registrazione domini** al posto tuo (**è la promessa D-054**, non un limite tecnico).
- ❌ **Nessun rinnovo automatico**. Il rinnovo del dominio è tua responsabilità.
- ❌ **Nessun DNS panel** in OMNIA. Non gestisci i record dal nostro pannello — apri il tuo registrar.
- ❌ **Nessun WHOIS query fallback**. Se il TLD non supporta RDAP, il checker non prova WHOIS legacy.
- ❌ **Nessuna UI per l'audit trail**. `domain_vault_events` esiste solo lato DB — no pagina *"Storico conferme Domain Vault"*.
- ❌ **Nessuna notifica scadenza dominio**. Il checker pubblico avvisa "scade fra 90 giorni" solo se lo lanci — non c'è cron che monitora automaticamente i domini delle agenzie iscritte.
- ❌ **Nessun supporto multi-dominio per agenzia**. Il campo `existing_domain` è **singolare** — un dominio per agenzia. Se hai `agenziaesempio.it` + `esempio-immobili.com`, ne dichiari uno solo.
- ❌ **Nessun deep-link tra i 3 componenti**. La pagina Domain Vault non ha un pulsante *"Vai al Custom Domain workflow"*. Devi navigare a mano.
- ❌ **CNAME_TARGET fisso via env**. Non è configurabile per agenzia (tutte le agenzie puntano allo stesso edge OMNIA).
- ❌ **Nessun supporto SSL configurabile**. Il certificato per il dominio custom è gestito lato OMNIA automatico (Let's Encrypt) — non hai UI per uploadare un tuo cert.
- ❌ **Rate limit non configurabile** sul checker pubblico. Se sei un partner con volumi alti, contatta il team.

**Cosa può cambiare in futuro**
Multi-dominio per agenzia, notifiche scadenza (cron), UI storico eventi, deep-link tra componenti, upload cert SSL custom, whitelist rate limit per partner.

---

## 17.12 · Cross-ref con altri capitoli

- **Cap. 6 · Portali & Publishing**: il `listing_url` degli immobili pubblicati sui portali usa il tuo dominio custom (se collegato). Se il DNS non è verificato, il fallback è il sottodominio OMNIA (`agenzia.omnia.example`).
- **Cap. 8 · Sito web agenzia**: il modulo Sito si serve del Custom Domain per rispondere sul tuo dominio. Cap. 8 documenta la parte UI/tema; Cap. 17 la parte DNS.
- **Cap. 13 · Team & Ruoli**: il POST domain-sovereignty richiede `agency_admin`+ (o rete). Un `agent` semplice non può confermare.
- **Cap. 15 · Social Publisher**: quando pubblichi immobili sui social, il `listing_url` allegato viene dal tuo dominio custom (se attivo).
- **Cap. 12 · HAL Knowledge**: puoi chiedere *"OMNIA registra il mio dominio?"* → risposta dalla voce `domain.d-054-promise`.

---

**Progressione manuale**: 17/26 capitoli (65%).
**Voci HAL totali**: **211** (Cap. 1-17, +15 nuove voci Cap. 17).
**Versione capitolo**: v1.0 (Feb 2026 · TASK N).

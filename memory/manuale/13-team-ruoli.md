# Capitolo 13 · Team & Ruoli (Collaboratori)

> **Cosa trovi in questo capitolo**
> Il modulo **Collaboratori** è il centro di controllo della tua agenzia per invitare, elencare e gestire i membri del team. In una parola: chi lavora con te dentro ImmoWeb, con quale ruolo e quali inviti sono ancora in sospeso. Il capitolo copre: dove trovarlo, i due ruoli disponibili (**titolare** e **agente**), l'invito via magic-link email con scadenza 7 giorni, la gestione degli inviti pendenti/accettati/revocati/scaduti, il flusso di accettazione da parte del collega, le differenze fra ciò che vedono i due ruoli, i limiti v1 dichiarati onestamente.

**Cosa NON è (D-051 onestà — regola cardine)**
- Non c'è un ruolo backend **"segreteria"**. Nel manuale usiamo "segreteria" come **concetto operativo** (mansione), ma nel database e nel modal di invito i ruoli assegnabili sono **solo due**: `agent` e `agency_admin`. Chi svolge segreteria oggi viene invitato come `agent`.
- Non c'è (in v1) un bottone per **rimuovere un membro** dall'agenzia. Non c'è nemmeno un modo per **cambiare il ruolo** di un membro dopo l'accettazione dell'invito.
- Non c'è una funzione **"disattiva temporaneamente"** un membro. Il campo `is_active` compare in lista, ma non esiste UI per farlo commutare.
- Non c'è **franchising / gruppo / branch** in questo capitolo. Quei ruoli (`group_admin`, `branch_admin`, `branch_agent`) sono gestiti da un flusso separato ed esplicitamente **bloccati** dal `POST /agencies` (dettagli in Cap. futuro).
- Non c'è **multi-agenzia switcher** dentro Collaboratori: se sei in più agenzie, cambi agenzia dal profilo (Cap. 1 §1.4). Qui vedi solo l'agenzia attualmente attiva.
- Non c'è **audit log visibile lato UI** di *"Chi ha invitato chi e quando"*. Il dato esiste server-side (`invited_by`, `created_at`), ma non è esposto in schermata v1.

---

## 13.1 · Cos'è il modulo Collaboratori e chi lo usa

**In una frase**
Un pannello di gestione team dove **il titolare** invita nuovi membri (agenti o altri titolari dell'agenzia) tramite un **magic link via email** e monitora lo stato degli inviti pendenti. Gli **agenti** vedono la stessa pagina in modalità sola lettura sull'elenco membri e non vedono la tab Inviti.

**Le due esperienze a colpo d'occhio**

| Cosa vede... | **Titolare** (`agency_admin` / `super_admin`) | **Agente** (`agent`) |
|--------------|:--:|:--:|
| Elenco membri agenzia | ✅ | ✅ |
| Bottone *"+ Invita membro"* | ✅ | ❌ (nascosto) |
| Tab *"Inviti"* (pending/accepted/revoked/expired) | ✅ | ❌ (nascosto) |
| Revoca di un invito pending | ✅ | ❌ |

**Perché esiste**
Un CRM condiviso senza un modo controllato per **allargare la squadra** è ingestibile: o si scambiano credenziali (rischio GDPR e sicurezza), o non si scala. Il modulo Collaboratori risolve entrambi i problemi: **credenziali individuali** per ogni membro + **audit implicito** via `invited_by`.

[SCREEN: team-members-list]

---

## 13.2 · Dove trovare Collaboratori

**Rotta**: `/it/app/members` (o `/en/app/members`, `/es/app/members`).

**Come arrivarci**
1. Fai login a ImmoWeb come `titolare` o `agente`.
2. Nella **barra a sinistra** cerca la voce **"Collaboratori"**.
3. Clicca: si apre la pagina con l'elenco membri e (se sei titolare) la tab Inviti.

**Nota redazionale**
Il codice frontend usa la chiave menu `members` (`AgencyShell`), ma in UI la label localizzata italiana è **"Collaboratori"**. Il manuale segue la label UI.

---

## 13.3 · I ruoli disponibili — `agency_admin` vs `agent`

**A cosa serve capirlo**
Ogni membro dell'agenzia ha **un solo ruolo** che determina cosa può fare in OMNIA. La scelta la fa il titolare **al momento dell'invito** e **non è modificabile** dopo l'accettazione (v1).

**I due ruoli invitabili (D-051 · esattamente questi due, niente altro)**

### `agency_admin` — Titolare / Amministratore d'agenzia
- Può **invitare** altri membri.
- Può **modificare** i dati dell'agenzia (`PATCH /agencies/me`).
- Vede la tab **Inviti** e può revocare inviti pendenti.
- Vede tutti gli immobili/clienti dell'agenzia.
- Può accedere a **Impostazioni** avanzate (Domain Vault, Billing).

### `agent` — Agente
- **Non** vede il bottone *"Invita membro"* (nascosto lato UI, bloccato lato API con 403).
- **Non** vede la tab Inviti.
- Vede l'elenco degli **altri membri** dell'agenzia (per orientarsi su chi è chi in squadra).
- Ha accesso al **suo** portafoglio operativo (immobili di cui è responsabile, i clienti che gestisce, i match). Cfr. Cap. 3-5.

### E la segreteria?
Nel manuale la trattiamo come **mansione operativa** — nel codice, chi svolge segreteria è invitato con ruolo **`agent`**. Non c'è un terzo ruolo distinto in v1. Motivo: mantenere il modello dei ruoli minimo (K.I.S.S.) finché la domanda reale di distinzione fine non emerge dal campo.

### Ruoli **non invitabili** dal modal
- `super_admin`: esiste ma è riservato al team OMNIA (auto-seedato al primo avvio, cfr. `test_credentials.md`). Non può essere assegnato via invito.
- `client`: profilo B2C anonimo (ImmobilCloud). Un utente `client` che accetta un invito **viene promosso** al ruolo dell'invito (`agent` o `agency_admin`) — vedi §13.10.
- `group_admin`, `branch_admin`, `branch_agent`: ruoli franchising, gestiti da un flusso separato (M2 Group Flow, capitolo futuro). Il `POST /agencies` **blocca** con `403 franchising_roles_use_group_flow` chi ha già uno di questi ruoli.

---

## 13.4 · Invitare un nuovo membro (magic-link email · 7 giorni)

**A cosa serve**
Aggiungere un collega senza mai condividere password: OMNIA manda un'email personale con un link unico che vale una sola volta.

**Passi operativi (solo titolare)**
1. Clicca **"+ Invita membro"** in alto a destra della pagina Collaboratori.
2. Compila il modal:
   - **Email** (obbligatorio, formato valido)
   - **Nome (suggerito)** (opzionale — appare al collega nella pagina di accettazione)
   - **Ruolo**: `Agent` o `Agency admin` (sono i due valori esatti del select — vedi §13.3)
3. Clicca **"Invia invito"**.
4. Se l'operazione riesce:
   - Il collega riceve un'email con un **link personale**.
   - Il link è del tipo `https://.../{lingua}/accept-invite#token=<32-char-token>`.
   - Il token vive **7 giorni** (`INVITE_EXPIRY_DAYS=7`).
   - Vedi un toast di conferma *"Invito inviato a <email>"*.
5. L'invito appare nella tab **Inviti** con status **pending**.

**Cosa succede se l'invito era già pending?**
Se lo stesso indirizzo email aveva già un invito con status `pending` per quest'agenzia, OMNIA **non crea un duplicato**: aggiorna l'invito esistente rigenerando **token e scadenza**. In pratica: chiedere due volte "invita marco@..." rinnova il link, non ne crea un secondo. Motivo: eliminare la confusione da inviti multipli attivi per lo stesso indirizzo.

[SCREEN: team-invite-modal]

**Cosa succede se l'utente è già membro?**
L'endpoint risponde **`400 user_already_member`** e il modal mostra l'errore in fondo. Non serve invitare qualcuno che è già dentro l'agenzia.

**Email non arrivata?**
- Chiedi al collega di controllare **spam / promozioni**.
- Verifica in tab Inviti che l'invito sia in status `pending` (se è lì, il record esiste; potrebbe essere un problema di deliverability).
- Se il collega non ritrova la mail entro 7 giorni → l'invito scade → **rilancia** l'invito con lo stesso indirizzo (il token verrà rigenerato).

---

## 13.5 · Tab Inviti — pending, accepted, revoked, expired

**A cosa serve**
Dashboard di controllo per il titolare: chi ha ricevuto un invito e come è finito.

**Colonne visibili**
- **Email**: destinatario.
- **Ruolo**: `AGENT` o `AGENCY_ADMIN` (in maiuscolo, formato badge).
- **Status**: uno dei 4 valori qui sotto.
- **Azioni**: solo per invite `pending` compare il link **Revoca** (rosso).

**I 4 stati possibili**

| Status | Colore badge | Significato |
|--------|:--:|-------------|
| **`pending`** | 🟡 ambra | Invito attivo, in attesa che il collega clicchi il link e completi la registrazione. Il titolare può revocarlo. |
| **`accepted`** | 🟢 verde | Il collega ha cliccato il link, impostato password e nome, ed è entrato in agenzia. Non c'è più nulla da fare. |
| **`revoked`** | ⚪ grigio | Il titolare ha annullato manualmente l'invito prima dell'accettazione. Il link non funziona più. |
| **`expired`** | 🔴 rosso | Sono passati più di 7 giorni dalla creazione senza accettazione. Il link non funziona più. Per invitare di nuovo, ripeti dall'inizio. |

**Come revocare un invito pendente**
1. Vai in tab **Inviti**.
2. Trova la riga desiderata (deve essere `pending`).
3. Clic su **"Revoca"** (a destra).
4. Il link inviato per email **non funziona più** (500ms dopo il click, il record cambia stato a `revoked`).
5. Se serve, puoi **rimandare** un nuovo invito allo stesso indirizzo (creando un secondo record).

**Attenzione**: la revoca **non è retroattiva** su chi ha già cliccato e completato. Se lo status è `accepted`, il collega è già dentro e la revoca dell'invito non lo rimuove dall'agenzia (v1 limitation, cfr. §13.12).

---

## 13.6 · Accettare un invito — il flusso dal punto di vista del collega

**A cosa serve capirlo**
Sapere cosa vede il tuo collega quando riceve l'email, per rassicurarlo o assisterlo se ha dubbi.

**I 4 passi che fa il collega invitato**
1. **Riceve email OMNIA** con il link `https://.../{lang}/accept-invite#token=<...>`. Il token viaggia nel **fragment** dell'URL (`#`), non nella query string, per non finire nei log server (D-051 · sicurezza L5).
2. **Clicca il link** → si apre la pagina di accettazione. OMNIA verifica il token via `GET /invites/verify` e mostra:
   - Nome agenzia che invita (es. *"Nicastro Immobiliare"*).
   - Ruolo assegnato (`agent` o `agency_admin`).
   - Email invitata (in evidenza).
3. **Compila il form**:
   - **Nome completo** (obbligatorio, autofocus).
   - **Password** (obbligatorio, **minimo 8 caratteri**, `minLength=8` lato client + hash bcrypt server).
   - Clic su **"Accetta invito"**.
4. **Auto-login e redirect**:
   - Server crea (o aggiorna) l'utente, imposta cookies `access_token` + `refresh_token` (httpOnly, secure, sameSite=none).
   - Frontend chiama `refresh()` sul contesto Auth.
   - Dopo 1,5 secondi mostra ✓ *"Invito accettato"* e reindirizza a `/{lang}/app/dashboard`.

[SCREEN: team-accept-invite]

**Errori possibili durante il verify**
- **Token invalido** (link storpiato, copia/incolla malato): pagina mostra ⚠ *"Invito non valido"*.
- **Token già usato o revocato**: stessa pagina, con dettaglio errore.
- **Token scaduto (>7gg)**: il verify aggiorna automaticamente lo status a `expired` e mostra l'errore.

**Cosa succede se il collega chiude la pagina senza completare?**
Il token resta valido: può cliccare di nuovo il link dall'email nei 7 giorni. Se sono passati più di 7 giorni, il titolare deve rilanciare l'invito.

---

## 13.7 · Elenco membri — cosa vedi

**Cosa mostra la tabella "Membri" (`GET /agencies/me/members`)**

Per ogni utente collegato alla tua agenzia (via `agency_ids`):
- **Nome**: il nome completo salvato nel profilo.
- **Email**: indirizzo di login.
- **Ruolo**: badge (`AGENT`, `AGENCY_ADMIN`, `SUPER_ADMIN` se rilevante).
- **Stato**: **Attivo** (badge verde) se `is_active=true`, altrimenti trattino grigio.

**Chi vede questa tabella**
Chiunque sia autenticato e membro dell'agenzia (`get_current_user`, nessun `require_roles`). Quindi anche un `agent` la vede. Utile per orientarsi: *"chi è la persona che ha caricato quell'immobile?"*.

**Cosa NON è mostrato in tabella (D-051 onesto)**
- Data di ingresso in agenzia (esiste `updated_at` lato DB, non esposto in colonna).
- Chi ha invitato chi (`invited_by` è nella collezione `agency_invites`, non correlato in UI).
- Ultimo login / attività recente.
- Contatore immobili/clienti gestiti per singolo membro (statistica non esposta v1).
- Foto profilo / avatar.

**Ordinamento**
Il codice restituisce fino a 200 membri **senza ordinamento esplicito**. In UI compaiono nell'ordine in cui il DB li restituisce. Su agenzie piccole (2-15 persone) l'impatto è trascurabile.

---

## 13.8 · Chi può invitare — permessi effettivi

**Regola (D-051 · 1:1 al codice)**
Solo i ruoli `agency_admin` e `super_admin` possono invitare (`Depends(require_roles("agency_admin", "super_admin"))` sui 3 endpoint `POST/GET/DELETE /agencies/me/invites`).

**In UI**
- Il bottone *"+ Invita membro"* è **condizionato** a `canInvite = user.role === 'agency_admin' || user.role === 'super_admin'` (`MembersPage.jsx:18`).
- La **tab Inviti** è nascosta agli agenti (`{canInvite && <TabBtn ...>}`).
- Se un agente tenta comunque la chiamata API (per esempio da devtools), riceve **`403 Forbidden`**.

**Super_admin del team OMNIA**
Il `super_admin` (`mcnicastro@gmail.com`) può invitare in **qualsiasi agenzia** di cui sia membro. È il ruolo di manutenzione: non è mai un cliente esterno.

---

## 13.9 · Onboarding titolare vs invito agente — due percorsi diversi

**A cosa serve capirlo**
Capire perché il **primo utente** di un'agenzia (il titolare) **non passa da un invito**.

**Percorso A · Il titolare registra la sua agenzia**
1. Signup pubblico via `/auth/register` (Cap. 1). Il register **non assegna ruoli privilegiati** (S2 · sicurezza).
2. L'utente completa l'**onboarding a 4 step** (Cap. 1 §1.5), l'ultimo dei quali chiama `POST /agencies`.
3. Il backend crea l'agenzia con `owner_id=user.id` e **promuove server-side** l'utente da `client` a `agency_admin` (`agencies.py:94-99`).
4. Da questo momento il titolare vede il menu Collaboratori e può invitare altri.

**Percorso B · Un agente entra per invito**
1. Il titolare compila il modal Invito con l'email del collega e ruolo `agent` (o `agency_admin`).
2. Il collega riceve l'email, clicca il magic-link, sceglie password, e accetta (§13.6).
3. Al momento dell'accept, se l'email **non esiste** ancora nel DB, viene creato un nuovo utente `UserInDB` con `role=<ruolo dell'invito>`, `agency_ids=[<agency_id>]`. Se l'email **esiste già**, vedi §13.10.

**Punto chiave (D-051)**
Non esiste un modo pubblico per registrarsi come `agency_admin` da zero: ti registri come `client` e diventi `agency_admin` **solo** completando l'onboarding con creazione agenzia (o accettando un invito con ruolo `agency_admin`). Questa è una decisione di sicurezza (S2 audit).

**Vincolo one-owner**
Un `agency_admin` può possedere **al massimo una** agenzia (`agency_already_exists` = 400). Se ne vuoi una seconda, ti serve un altro account (email diversa) o un flusso franchising (Cap. futuro).

---

## 13.10 · Utente già registrato che accetta un invito

**Scenario**
Marco è già cliente OMNIA (ha usato ImmobilCloud per farsi una valutazione B2C). Ora un titolare lo invita nella sua agenzia come `agent`.

**Cosa succede tecnicamente (`invites.py:238-253`)**
Il record `users` di Marco esiste già. All'`accept`:
- Il suo **agency_ids** viene esteso (`$addToSet`) con la nuova agenzia (non duplica se già presente).
- Il suo **nome** viene aggiornato a quello inserito nel form (se differente).
- La sua **password** viene sostituita con quella nuova (`password_hash = hash_password(payload.password)`).
- Il suo **ruolo**: viene aggiornato **solo se era `client`**. Se era già `agent`, resta `agent`. Se era già `agency_admin`, resta `agency_admin`. Non c'è downgrade.

**In pratica per i due casi comuni**
| Ruolo pre-invito | Ruolo dell'invito | Ruolo post-accept |
|:-:|:-:|:-:|
| `client` | `agent` | **`agent`** (promosso) |
| `client` | `agency_admin` | **`agency_admin`** (promosso) |
| `agent` | `agent` | `agent` (invariato) |
| `agent` | `agency_admin` | `agent` (invariato, **no upgrade**) |
| `agency_admin` | `agent` | `agency_admin` (invariato, no downgrade) |
| `agency_admin` | `agency_admin` | `agency_admin` (invariato) |

**Nota (D-051)**
La regola *"upgrade role solo se era client"* è **onesta e stretta**: non c'è un endpoint per cambiare ruolo dopo. Se un agente esistente deve diventare co-titolare, la strada in v1 è: cancellare l'utente e rifare invito (workaround da super_admin backend). Vedi §13.12.

---

## 13.11 · Errori comuni

| Problema | Cosa succede | Causa | Soluzione |
|----------|--------------|-------|-----------|
| *"Errore: user_already_member"* nel modal | 400 sul POST | Stai invitando un indirizzo email che è già membro della tua agenzia. | Vai in tab Membri e verifica: la persona è già dentro. Se non la vedi, refresh pagina. |
| *"Invito non valido"* sulla pagina di accept | 404 verify | Token errato o record non trovato. | Il collega deve usare **il link esatto** dell'email (cliccarlo, non copiarlo a mano). |
| *"Invito già usato o revocato"* | 400 verify | Il collega ha già accettato una prima volta, oppure il titolare ha revocato. | Fai un nuovo invito se serve. |
| *"Invito scaduto"* | 400 verify | Sono passati più di 7 giorni. | Il titolare rilancia l'invito (nuovo token, nuovi 7 giorni). |
| Email invito non arriva | Nessun errore lato UI | Deliverability, spam, indirizzo tipografato male. | Verifica invito pending in tab Inviti · chiedi al collega di controllare spam · se serve, revoca e reinvita con email corretta. |
| Bottone *"+ Invita membro"* non compare | Nessun errore | Il tuo ruolo è `agent`, non `agency_admin`. | Chiedi al titolare di fare l'invito. |
| Il collega si logga ma non vede l'agenzia | Login riuscito ma nessun contenuto | L'invito è stato **revocato** dopo l'accept oppure il record `agency_ids` non contiene l'agenzia. | Verifica in tab Membri se compare · se sì è un problema di refresh cookie (logout+login) · se no ricontatta il team OMNIA. |
| Errore *"agency_already_exists"* al POST /agencies | 400 durante onboarding | Il tuo utente ha già creato un'agenzia in passato. | Un `agency_admin` può avere una sola agenzia. Usa un secondo account per una seconda agenzia. |

---

## 13.12 · Limiti onesti v1 (D-051)

**Cosa il modulo Collaboratori NON fa oggi**

- ❌ **Nessun bottone "Rimuovi membro" in UI**. Il backend non espone un endpoint `DELETE /agencies/me/members/{user_id}`. Se un collaboratore lascia l'agenzia, in v1 va contattato il team OMNIA per la rimozione manuale.
- ❌ **Nessun cambio di ruolo post-accettazione**. Un `agent` non può essere promosso a `agency_admin` (o viceversa) tramite UI. Workaround v1: cancellare l'utente da DB e reinvitare con il ruolo giusto (operazione super_admin).
- ❌ **Nessun ruolo "segreteria" backend**. È solo un concetto operativo — chi svolge segreteria oggi viene invitato come `agent`.
- ❌ **Nessuna disattivazione temporanea** di un membro. Il campo `is_active` esiste in colonna ma non c'è UI per farlo commutare.
- ❌ **Nessun audit log visibile in UI**. Server-side sappiamo chi ha invitato chi (`invited_by`), quando (`created_at`, `updated_at`), ma non c'è schermata dedicata al log operazioni team.
- ❌ **Nessuna gestione permessi granulari** (chi può vedere quali immobili/clienti). In v1 tutti i membri autenticati vedono l'intero portafoglio dell'agenzia. I livelli di privacy L1-L4 restano sull'immobile singolo (Cap. 3 §3.4), non sul membro.
- ❌ **Nessun flusso franchising / gruppo / branch**. I ruoli `group_admin`, `branch_admin`, `branch_agent` esistono nel database ma sono gestiti da un altro flusso (M2 Group Flow, non attivo v1). Il `POST /agencies` **blocca** con 403 chi ha già uno di questi ruoli.
- ❌ **Nessun avviso in tempo reale** al titolare quando un invito viene accettato. Vedi lo status cambiare solo ricaricando la pagina Inviti.
- ❌ **Nessuna trasferimento ownership** dell'agenzia. Se il titolare vuole cedere il ruolo `owner`, oggi va gestito manualmente lato super_admin.

**Cosa può cambiare in futuro**
Se il campo esprime la necessità, in versioni successive potranno arrivare: rimozione membro, cambio ruolo, audit log, permessi granulari per membro, franchising, notifiche in tempo reale, transfer ownership.

---

## 13.13 · Cross-ref con altri capitoli

- **Cap. 1 · Primo accesso** (`01-primo-accesso.md`): flusso di signup pubblico (nessun ruolo privilegiato in signup), onboarding 4-step che crea l'agenzia e promuove a `agency_admin`, tour della barra sinistra dove trovi la voce Collaboratori.
- **Cap. 12 · HAL Knowledge**: puoi chiedere ad HAL Knowledge domande sul modulo Collaboratori (es. *"Come invito un collega?"* → risposta con fonti in `13-team-ruoli.yaml`).
- **Cap. 24 · Impostazioni** (futuro): Billing, Domain Vault, dati fiscali agenzia — spazi ulteriori riservati al `agency_admin`.
- **Cap. 3 · Immobili** § privacy: l'accesso agli immobili in L4 privacy è limitato al **team dell'agenzia**, cioè agli utenti in `agency_ids`. Il modulo Collaboratori determina implicitamente chi vede cosa.

---

**Progressione manuale**: 13/26 capitoli (50%).
**Voci HAL totali**: **155** (Cap. 1-13, +13 nuove voci Cap. 13).
**Versione capitolo**: v1.0 (Feb 2026 · TASK J).

# Dogfood Readiness — Step 1 · Runbook (FORMALE)

**Data formalizzazione:** 18 novembre 2026 · ~17:00 Europe/Rome  
**Mandato:** D-175 — Step 1 Dogfood Readiness  
**Stato documento:** **STEP 1 CHIUSO** — cinque decisioni Founder acquisite · **Step 2 non autorizzato**  
**Ruoli (D-175):** Founder decide/firma · ChatGPT gate critico · Cursor esecutore tecnico su incarico (non decide)

**Legenda**
- **[APPROVATO]** — decisione Founder  
- **[PROPOSTA CURSOR]** — ancora da ratificare o da verificare in slice successive  
- **[DA DECIDERE]** — aperto (solo H4 / elenco nominale persone prima degli smoke)

---

## 0. Premessa

**[APPROVATO]** Master Strati A+B chiuso ≠ OMNIA pronto all’uso quotidiano.  
**[APPROVATO]** Dogfood readiness ≠ produzione ≠ Stripe live (MC-049 fuori).  
**[APPROVATO]** H4 / MC-046: fuori dal perimetro definitivo ora; valutazione dopo fotografia Step 2 (non ancora avviato).  
**[APPROVATO]** Criteri usabilità a 5 livelli + condizioni di STOP.

Obiettivo: verificare se OMNIA è abbastanza stabile e sicuro per uso interno controllato, con evidenze di processo — non solo audit di codice.

---

## 1. Decisioni Founder formalizzate (5/5 + H4 rinviata)

| # | Tema | Decisione | Dettaglio |
|---|---|---|---|
| 1 | Ambiente | **[APPROVATO] C** | Locale isolato inizialmente; staging dedicato solo se necessario |
| 2 | Account reali | **[APPROVATO] B** | Nicastro **solo lettura**; **vietato** nei test distruttivi |
| 3 | Resend | **[APPROVATO] C** | **Disabilitato** durante i test; allowlist Founder solo per test email **specifici** ed espliciti |
| 4 | Snapshot Mongo | **[APPROVATO] A** | **Obbligatorio** prima dei test distruttivi; **ripristino deve essere verificato** (backup non testato ≠ garanzia) |
| 5 | Autorizzazione smoke | **[APPROVATO] C** | Elenco chiuso di **persone fisiche** nominate dal Founder (vedi §1.3) |
| 6 | H4 / MC-046 | **[APPROVATO] DOPO** | Non deciso ora; Step 2 (sola lettura) misurerà se l’assenza blocca il dogfood |

### Regola smoke — **[APPROVATO]**

- Il Founder autorizza e supervisiona gli smoke.  
- Cursor può eseguirli **solo** su incarico esplicito, entro lo scope assegnato.  
- Nessun altro soggetto può avviarli senza nuova autorizzazione Founder.  
- Cursor **non** amplia autonomamente test, ambiente o perimetro.  
- Cursor è **esecutore tecnico**, non soggetto che decide.

**[DA DECIDERE — prima degli smoke]** Nomi delle persone fisiche abilitate (elenco chiuso). Fino ad allora: nessun smoke dogfood operativo.

---

## 2. Ambiente dogfood

### 2.1 Runtime — **[APPROVATO]** con dettaglio operativo **[PROPOSTA CURSOR]**

| Voce | Valore |
|---|---|
| Primario | **Cloud Agent / stack locale** — API `http://127.0.0.1:43121`, preview `http://127.0.0.1:43123` |
| Secondario | Staging dedicato **solo se** il locale non basta (decisione Founder caso per caso) |
| Tip codice | `main` post-Master + R-02/R-03/R-04 — SHA baseline da fissare in Step 2 |
| DB | Mongo **locale** agent — non DB produzione Railway |
| Produzione Vercel/Railway | Fuori mandato |
| Tunnel pubblico | Evitare se non necessario; allo Step 1 risultava stale |

### 2.2 Stripe — **[APPROVATO]** solo test · **[PROPOSTA CURSOR]** verifiche obbligatorie prima degli smoke billing

`sk_test` **non basta da solo**. Prima degli smoke billing occorre evidenza che siano separati dall’ambiente reale:

- chiavi `sk_test` / `pk_test` (no `sk_live`)  
- webhook endpoint e secret di test (non prod)  
- Stripe account/dati di prova isolati  
- nessun routing accidentale verso customer/prod live  

Finché non verificate → billing self-serve in STOP o fuori smoke.

### 2.3 Dati — **[APPROVATO]**

| Tipo | Regola |
|---|---|
| Prova | `demo-agency-001` / utenti demo — **obbligatori** per test distruttivi (cease, sospensione, deroga) |
| Nicastro / agenzia reale | **Solo lettura** se autorizzata; **vietata** in test distruttivi |
| Seed | Solo DB locale |

### 2.4 Email (Resend) — **[APPROVATO]** + requisito tecnico

- Default smoke: Resend **disabilitato** (protezione tecnica, non solo “non mandare email”).  
- Allowlist Founder: solo per test email **esplicitamente** incaricati.  
- Implementazione del kill-switch/allowlist = slice successiva, richiede autorizzazione implementazione.

### 2.5 Snapshot e ripristino — **[APPROVATO]**

Prima di sospensione / deroga / cessazione:

1. Snapshot Mongo locale obbligatorio.  
2. **Prova di ripristino** su copia/fixture (almeno una volta documentata) prima di fidarsi del backup.  
3. Procedura di ripristino scritta e rieseguibile.  
4. Fixture usa-e-getta preferite + cleanup.

---

## 3. In-scope / Out-of-scope

### 3.1 In-scope — **[PROPOSTA CURSOR]** (ratifica implicita salvo obiezione Founder al gate; H4 esclusa)

1. Login / sessione / refresh (post R-01)  
2. Shell gestionale + Avvio  
3. Immobili / Clienti (uso base)  
4. Cabina / notifiche / Accetta transfer Main Admin (MC-040)  
5. Billing UI + plans/subscription in **test mode** (dopo check isolamento Stripe)  
6. Crediti grant/allocate/revoke (H3 + R-03)  
7. Sospensione / deroga / cease end-to-end su **dati prova**  
8. Autorizzazioni tenant (no cross-CC)  
9. Runbook + STOP + snapshot/restore  

### 3.2 Out-of-scope — **[APPROVATO]** / **[PROPOSTA]**

| Voce | Stato |
|---|---|
| Stripe live / MC-049 | **[APPROVATO]** fuori |
| H4 / MC-046 | **[APPROVATO]** fuori ora; rivalutare post-Step 2 |
| MLS pieno, B05–B07, legacy | Fuori |
| B2C vendita pubblica / portali push reali | Fuori |
| Pronto vendita / clienti paganti | Fuori |

---

## 4. Criteri di usabilità (5 livelli) — **[APPROVATO]**

| Livello | Significato |
|---|---|
| L1 UI | Schermata/route presente |
| L2 API | Endpoint corretto nel percorso |
| L3 AuthZ | Ruoli/tenant/CC corretti |
| L4 Processo | Flusso completo utente→effetto |
| L5 Errore | Fallimento gestito, no corruzione |

L1 ≠ utilizzabile. Target: **L4** sulle voci critiche; **L3+L5** obbligatori su sicurezza/crediti/lockout.  
Stati: `OK` · `PARZIALE` · `ASSENTE` · `NON VERIFICABILE`.

---

## 5. Criteri di successo dogfood — **[PROPOSTA CURSOR]**

1. Questo runbook Step 1 firmato/chiuso (qui).  
2. Step 2 fotografia completa (quando autorizzato).  
3. Smoke E2E verdi su voci L4 critiche (su incarico).  
4. Nessuno STOP aperto non mitigato.  
5. H4: non bloccante con evidenza **oppure** inclusa e verificata.  
6. Dichiarazione Founder esplicita.

---

## 6. Condizioni di STOP — **[APPROVATO]**

1. Accesso non autorizzato (cross-tenant, cease bypass, refresh post-cease, collab operativo in sospensione).  
2. Perdita/alterazione dati non prevista.  
3. Addebito reale / chiave live.  
4. Errori crediti (over-allocation, saldi incoerenti, grant su CC non operabile).  
5. Mancata applicazione blocchi.  
6. Email a destinatari esterni non autorizzati.

A STOP: evidenza documentata; nessun hotfix fuori mandato.

---

## 7. H4 / MC-046 — rinvio

**[APPROVATO]** Non nel perimetro definitivo iniziale.  
Allo **Step 2** (quando autorizzato, sola lettura) Cursor dovrà rispondere: copertura esatta, dipendenze, rischio se fuori, se blocca il dogfood concreto.

---

## 8. Prossimi passi (nessuna esecuzione senza nuovo mandato)

| Step | Contenuto | Stato |
|---|---|---|
| **1** | Runbook formale | **CHIUSO** (questo documento) |
| **2** | Fotografia gap list 5 livelli + dossier H4 | **Non autorizzato** |
| S0+ | Commit runbook in repo / smoke / fix | Solo con nuova decisione + eventuale `OMNIA — AUTORIZZAZIONE ESPLICITA ALL'IMPLEMENTAZIONE` |

---

## 9. Dichiarazione Cursor

Step 1 è **formalmente aggiornato** con le cinque decisioni Founder.  
**Non** avvio Step 2.  
**Non** eseguo smoke.  
**Non** implemento kill-switch Resend / script snapshot finché non arriva mandato esplicito.

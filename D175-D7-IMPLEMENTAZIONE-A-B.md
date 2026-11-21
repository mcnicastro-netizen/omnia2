# OMNIA D-175 — Implementazione A+B (credenziali + harness T3/T4)

**Data:** 21 novembre 2026 (Europe/Rome)  
**Autorizzazione:** Founder — pacchetti **A** e **B** soltanto  
**Non eseguito:** T3/T4, seed, cleanup, API/DB mutative, push, deploy, pacchetto C

---

## 1. Esito operazione A — credenziali temporanee

| Voce | Dettaglio |
|------|-----------|
| Path | `/tmp/d7_fixtures_secrets.json` |
| Pre-check | mode `644`, owner `ubuntu`, size 288 byte; **nessun** fd/`lsof` aperto |
| Dipendenze attive | Nessun processo con file open. Riferimenti path solo in script storici `/tmp/d7_seed_staging.py` (write) e `/tmp/d7_t3_t4_run.py` (read) — **non** in esecuzione |
| Contenuto | **Non** letto / aperto / stampato / copiato |
| Operazione 1 | `chmod 600` → mode verificata `600` |
| Operazione 2 | `rm -f` → file **assente** (`DELETE_OK`) |
| Dichiarazione | Cancellazione filesystem del path eseguita (`rm`). **Non** dichiarata «cancellazione fisica sicura» / wipe multipass |
| Altri secret/config | **Non** modificati |

**FATTO:** il file non esiste più sul path.  
**LIMITE:** residui possibili in page cache/backup VM non verificati; A9 se rieseguito ricreerebbe un file (A9 non è stato modificato in B — è storico `/tmp`).

---

## 2. Esito operazione B — harness versionabile

### 2.1 File creati

| Path | Ruolo |
|------|-------|
| `scripts/d7_e2e/__init__.py` | Package version `1.0.0` |
| `scripts/d7_e2e/__main__.py` | CLI `precheck` / `run` / `cleanup` + gate `--confirm-staging-run` |
| `scripts/d7_e2e/config.py` | Costanti staging + nota forense A6 non-SoT |
| `scripts/d7_e2e/classify.py` | PASS/FAIL/BLOCKED; **5xx → FAIL** |
| `scripts/d7_e2e/artifacts.py` | `artifacts/d7/<run_id>/` immutabile; secrets 0600 |
| `scripts/d7_e2e/http_client.py` | Client cookie/CSRF |
| `scripts/d7_e2e/mongo_util.py` | Mongo solo se project+DB staging |
| `scripts/d7_e2e/precheck.py` | Gate P1–P8 |
| `scripts/d7_e2e/seed.py` | Fixture `@example.com` + tag `d7_run_id` |
| `scripts/d7_e2e/t3.py` | Controlli T3 obbligatori |
| `scripts/d7_e2e/t4.py` | Controlli T4 obbligatori |
| `scripts/d7_e2e/README.md` | Prerequisiti, comandi, limiti, mapping forense |
| `artifacts/d7/README.md` | Policy artefatti immutabili |
| `artifacts/d7/.gitkeep` | Directory tracciata |
| `.gitignore` | Aggiunte regole `artifacts/d7/**/secrets/` |
| `D175-D7-IMPLEMENTAZIONE-A-B.md` | Questo rapporto |

### 2.2 File storici **non** modificati

A5/A6/A7 in `/opt/cursor/artifacts/`, A9/A10 in `/tmp/`, report forense/next-step preesistenti: **preservati**, non riscritti.

### 2.3 Requisiti implementati (codice + docs)

| Requisito | Dove |
|-----------|------|
| T3 collab→visit complete→mini-dossier→deal→chat→list B→iso→revoke→proposal | `t3.py` |
| T4 Main Admin, branch deny, invite, token DB, accept, membership, no email send | `t4.py` |
| Controllo esplicito per step; 5xx/inatteso/skip → FAIL/BLOCKED | `classify.py` + step files |
| Fixture isolate `d7_run_id` | `seed.py` |
| Cleanup solo per `run_id` (refuse id corto) | `seed.cleanup_run` |
| Email `@example.com` | `config.EMAIL_DOMAIN` / seed |
| Secrets non in `/tmp` 644 | `artifacts.write_secrets_file` mode 0600 |
| Artefatti immutabili per run | `artifacts.run_dir` refuse if exists |
| Gate esecuzione | `--confirm-staging-run` obbligatorio |
| Discrepanze forense documentate | `README.md`, `config.FORENSIC_A6_NOT_SOT` |

### 2.4 Verifiche fatte in A+B (non mutative staging)

| Verifica | Esito |
|----------|-------|
| `py_compile` moduli harness | OK |
| `python -m scripts.d7_e2e precheck` senza flag | exit 2, messaggio missing confirm |
| Esecuzione T3/T4 / seed / cleanup / API / DB | **NON ESEGUITI** |

---

## 3. Commit locale

| Voce | Valore |
|------|--------|
| Branch | `cursor/staging-e2e-d1d3-b894` |
| Push | **non** eseguito |
| Working tree preesistente | Numerose `??` report MD precedenti — **non** incluse nel commit |
| Commit principale A+B | `4209412f5cda651d669a6fc4aeb467546ff555db` |
| Commit docs SHA | `810255a6d699f02a997c9cc820567afb38927d26` (HEAD) |
| Messaggio principale | `feat(d7): secure staging secrets hygiene and add T3/T4 harness (A+B)` |
| Contenuto | Solo file A+B elencati in §2.1 (IDs staging in `config.py` con `pragma: allowlist secret`) |

---

## 4. Cosa resta per il Founder (non in A+B)

| Pacchetto | Contenuto |
|-----------|-----------|
| **C** | Autorizzare esecuzione: `PYTHONPATH=. python -m scripts.d7_e2e run --confirm-staging-run` |
| Review script | Eventuale revisione codice prima di C |
| Push/PR | Solo se esplicitamente richiesto |

---

## 5. Chiusura

A eseguita (chmod 600 + rm).  
B implementata (harness + docs), **non** eseguita.  
Cursor si ferma. Nessun avvio T3/T4.

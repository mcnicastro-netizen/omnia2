# O0 — Design vincolante bak/media · D-114

**Stato:** ✅ deciso (fase O0 · «vai» 30-Set-2026) · **runtime S2:** ✅ 10-Ott-2026  
**Scope O0:** numeri + modello target **scritto**.  
**Implementazione del modello:** ✅ S2 — `BACKUP_RETENTION_DAYS` default **7** + media **incrementale hardlink** (`backup_job.py`).  
**Listino:** fermo finché non si decide esplicitamente una revisione (meter → **S3**).

---

## 1. Situazione (as-is storico → runtime S2)

| Voce | Prima (as-is) | Runtime S2 (10-Ott-2026) |
|------|---------------|--------------------------|
| Media live | FS locale `LOCAL_STORAGE_ROOT` | invariato |
| Bak media | `shutil.copytree` full ogni giorno | **incrementale hardlink** da giorno precedente + full al primo giorno |
| Retention bak | default **30** | default **7** (`BACKUP_RETENTION_DAYS`) |
| Moltiplicatore disco | ~31–32× | hot ≤7g + hardlink ≈ **~1× + delta** (prova LIVE `docs/ops/runs/s2-bak-o0-runtime-live.log`) |
| Restore | procedura D-113 | S1 firmata (PR separata) + procedura |
| Quote piano (D-085) | Starter 30 / Pro 100 / Agency 300 GB | invariato · listino fermo |
| €/GB ops | non confermato | meter reale → **S3** |

### Stima ordine di grandezza (worst-case piano pieno + bak 30g)

| Piano | Live | Bak tree (~31×) | Live+bak |
|-------|------|-----------------|----------|
| Starter 30 GB | 30 | ~930 | ~960 GB |
| Pro 100 GB | 100 | ~3100 | ~3200 GB |
| Agency 300 GB | 300 | ~9300 | ~9600 GB |

A €0,04/GB/mese (ipotesi non confermata): Starter ~€38 solo disco vs canone €49 → **margine assente/negativo** se il piano è pieno. A €0,02/GB il quadro migliora ma resta fragile su Agency.

**Conclusione numerica O0:** il modello full-copy × 30 giorni **non è sostenibile** come baseline commerciale a listino corrente se i clienti riempiono la quota.

---

## 2. Modello target (to-be) — **QUESTO È IL MODELLO CHE IMPLEMENTEREMO**

### 2.1 Retention target

| Layer | Retention | Note |
|-------|-----------|------|
| Cestino operativo | 30 giorni | invariato (**D-097**) |
| Backup recovery point | **7 giorni rolling** come target V1 sostenibile | Riduce moltiplicatore da ~31× a ~8× sul media tree (ordine di grandezza) |
| Emergency / cold (opzionale V1.1) | 1 snapshot mensile trattenuto **90 giorni** | Solo se costo conferma fattibilità; non bloccante O0 |

### 2.2 Cosa entra / esce dal backup

**Entra (obbligatorio per restore agency-first):**

* Mongo per agency: agencies, users (membership), properties, clients, client_requests, activities, leads, subscriptions/wallets correlati, publishing_connections, documents metadata  
* Media **referenziati** da properties/fascicolo/modulistica di quell’agency (o tree per `agency_id` quando path lo consente)

**Esce / non in hot bak giornaliero:**

* Orphan blob già non referenziati (cleanup path **D-098**/D-102 — WHEN allineato)  
* Artefatti temporanei / cache staging  
* Dump globali non necessari al restore singola agency (ridurre scope quando si implementa extract)

**Nota as-is:** oggi mancano `client_requests` / `activities` nel dump — il modello target li **include** (allinea **D-096** criterio di successo).

### 2.3 Full vs incrementale

| Fase | Modello |
|------|---------|
| **V1 (da implementare dopo O0)** | **Incrementale giornaliero** sul media (rsync/hardlink o equivalent: solo delta + hardlink immutabili) **oppure** retention 7g full se incrementale non arriva subito — **preferenza: incrementale** |
| **Transizione** | Finché l’incrementale non è live, abbassare retention hot a **7 giorni** è il minimo vincolante per non restare a 32× |
| **Mongo** | Dump giornaliero per-collection (come oggi) → evolvere a dump filtrabile per `agency_id` in sede di restore tool |

### 2.4 Restore agency-first (**D-096** / **D-113**)

* Promessa interna: restore **singola agency** da bak valido, procedura manuale testabile (O3 / D-113).  
* Non self-service e non “garantito in brochure” finché non ci sono tempi/limiti operativi scritti.  
* Criterio successo: immobili + clienti + richieste + attività + documenti + media coerenti.

### 2.5 Costo stimato (ordine di grandezza, post-modello)

Ipotesi: retention hot 7g + incrementale ≈ **~2–4×** live (tipico), non 31×.

| Piano pieno | Live | Stima ops storage post-V1 (×3 medio) | vs ×31 as-is |
|-------------|------|--------------------------------------|--------------|
| Starter 30 GB | 30 | ~90 GB | vs ~960 |
| Pro 100 GB | 100 | ~300 GB | vs ~3200 |
| Agency 300 GB | 300 | ~900 GB | vs ~9600 |

A €0,04/GB: Starter ~€3,6/mese disco vs €49 canone → **margine disco recuperabile**. I numeri vanno **ricalibrati** dopo la prima implementazione con meter reale.

### 2.6 Decisione vincolante (frase SoT)

> **Implementeremo un backup con retention hot ≤ 7 giorni, preferenza incrementale sul media, scope allineato al restore agency-first (Mongo completo per recovery + media referenziati), e procederemo a stima costi reali post-meter prima di qualsiasi revisione listino.**

Listino €49/€99/€299 e quote GB restano **fermi** fino a decisione commerciale esplicita dopo i numeri post-implementazione.

---

## 3. Fuori da O0 / ancora aperti post-S2

* ~~Codice refactor bak~~ → **fatto in S2** (retention 7 + incrementale)  
* Cold monthly 90g (V1.1 opzionale)  
* Checksum contenuto (oggi size+mtime_ns)  
* Object storage/CDN (solo se smoke media o costi D-114 lo impongono)  
* DR piattaforma / restore self-service  
* Revisione prezzi (dopo **S3** meter) 

---

## 4. Dipendenze

* **O3 / D-113:** può testare restore sull’as-is mentre V1 bak non è live.  
* **D-098/D-102:** orphan WHEN si chiude col design sopra.  
* **O6:** non PASS senza O0 DONE (questo documento approvato in esecuzione «vai»).

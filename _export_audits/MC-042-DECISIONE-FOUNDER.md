# MC-042 — Decisione Founder (cessazione definitiva CommercialCustomer)

**Data decisione aggiornata:** 18 novembre 2026 · Europe/Rome (secondo turno)  
**ID inventario:** MC-042  
**Stato:** **DECISIONE FUNZIONALE APPROVATA DAL FOUNDER — 18/11/2026 (testo aggiornato)**  
**Implementazione codice:** vedi § Stato implementativo — **non** dichiarare chiusa senza evidenze  
**SoT piano:** `MASTER-CHIUSURA-POST-AUDIT-PIANO.md`  
**Registro:** D-176 (storico) · **D-177** (testo vincolante aggiornato)

---

## Cronologia (non cancellare)

| Versione | Data | Sintesi | Stato |
|---|---|---|---|
| v1 (mattina) | 18/11/2026 | Whitelist: sola lettura autonoma documenti **chiusura** + **fatturazione**; vietata wallet operativa | **SUPERATA** dalla v2 |
| v2 (odierna) | 18/11/2026 | **Cessazione definitiva:** nessun accesso autonomo; richieste solo via email al Super Admin; dati conservati | **VIGENTE** |

La v2 **sostituisce** l’interpretazione precedente della whitelist di accesso autonomo ai documenti di chiusura e fatturazione.

---

## Testo vincolante (Founder) — v2 vigente

Quando un CommercialCustomer **cessa definitivamente** il rapporto con OMNIA:

**Accesso**
- Login disattivato.
- Password disattivata.
- Nessun accesso autonomo alla piattaforma.
- Nessun accesso in sola lettura.
- Nessun accesso al wallet.
- Nessuna consultazione autonoma di fatture o documenti.
- Le richieste di informazioni e documenti sono indirizzate **via email al Super Admin**.
- Il Super Admin gestisce le richieste e fornisce le informazioni e i documenti dovuti.

**Conservazione (≠ accesso)**
Devono essere conservati:
- Identità.
- Nomine.
- Ledger.
- Movimenti dei crediti.
- Fatture e documenti.
- Storico commerciale e operativo.
- Documentazione di chiusura.

La cessazione dell’accesso **non** comporta cancellazione dei dati.  
**Conservazione dei dati e accesso ai dati sono due cose distinte.**

---

## Distinzione obbligatoria

| Tipo | Stato |
|---|---|
| Decisione funzionale Founder (v2) | **APPROVATA** 18/11/2026 |
| Enforcement login/password disattivati su cessazione | **DA VERIFICARE / NON DICHIARATO IMPLEMENTATO** |
| Enforcement «nessun accesso autonomo» (tutta la piattaforma) | **DA VERIFICARE / NON DICHIARATO IMPLEMENTATO** |
| Enforcement deny wallet operativo su CC ceased | **PARZIALE** — presente su `main` post PR #218 (gate wallet); non equivale a MC-042 v2 completo |
| API cliente chiusura/fatture | **ASSENTE** (e con v2 **non** è più la whitelist di accesso autonomo) |
| Canale email → Super Admin per documenti | **NON IMPLEMENTATO** come flusso prodotto (fuori scope #218) |

---

## Coerenza con decisioni già chiuse

| Riferimento | Rapporto |
|---|---|
| **D05** | MC-042 v2 **precisa e restringe** «consultazione limitata»: su cessazione definitiva **nessun** accesso autonomo. Non riapre D01–D04, D06–D12. |
| **DES-07 / DES-08** | Entitlements cessazione: allineare la lettura design a «no accesso autonomo»; area amm. post-cessazione = gestione **tramite Super Admin**, non self-serve. |
| **MC-054…059** | Sospensione / riattivazione / deroga: **distinte** da cessazione definitiva. Non confondere. |
| **PR #218** | Ha enforce deny wallet operativo + fail-open CC; **non** implementa MC-042 v2 (login off / zero accesso autonomo / canale Super Admin). |

---

## Stato implementativo (baseline `main` @ `547f67f`, post merge #218)

| Requisito MC-042 v2 | Codice | Esito |
|---|---|---|
| Login/password disattivati su cessazione | Non verificato come regola automatica di cessazione | **NON CONFORME / NON VERIFICATO** |
| Nessun accesso autonomo piattaforma | Sessioni/login non gated da «ceased» in modo documentato come chiusura totale | **NON CONFORME / GAP** |
| Nessuna read autonoma fatture/documenti | Nessuna API cliente dedicata; non c’è self-serve post-cessazione | **ALLINEATO DI FATTO all’assenza self-serve** (ma manca canale Super Admin) |
| Nessun accesso wallet | Gate `cc_is_wallet_operable` / assert su ceased + fail-open fix | **PARZIALE — wallet sì; non tutto MC-042 v2** |
| Conservazione dati | Ledger/nomine/CC restano in DB; no delete su cease | **ALLINEATO (principio)** |
| Email → Super Admin | Non presente come flusso | **MANCANTE** |

**Conclusione:** MC-042 **non** è formalmente chiusa in codice. Decisione funzionale v2 **vigente**. Enforcement completo **mancante** (salvo pezzi wallet di #218).

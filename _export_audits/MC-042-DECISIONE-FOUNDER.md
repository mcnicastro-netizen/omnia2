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
| Enforcement login/password disattivati su cessazione | **IMPLEMENTATO** 18/11 — gate login (password/Google/MFA) + session `get_current_user` su CC `ceased` (`shared/billing/commercial_access.py`) |
| Enforcement «nessun accesso autonomo» (tutta la piattaforma) | **IMPLEMENTATO** 18/11 — deny API autenticata su CC ceased (Super Admin bypass) |
| Enforcement deny wallet operativo su CC ceased | **IMPLEMENTATO** — #218 + v2 |
| API cliente chiusura/fatture | **ASSENTE** di proposito (v2: no self-serve; solo Super Admin via email) |
| Canale email → Super Admin per documenti | **FUORI SCOPE prodotto** — hint in errore 403; processo manuale email |

---

## Coerenza con decisioni già chiuse

| Riferimento | Rapporto |
|---|---|
| **D05** | MC-042 v2 **precisa e restringe** «consultazione limitata»: su cessazione definitiva **nessun** accesso autonomo. Non riapre D01–D04, D06–D12. |
| **DES-07 / DES-08** | Entitlements cessazione: allineare la lettura design a «no accesso autonomo»; area amm. post-cessazione = gestione **tramite Super Admin**, non self-serve. |
| **MC-054…059** | Sospensione / riattivazione / deroga: **distinte** da cessazione definitiva. Non confondere. |
| **PR #218** | Ha enforce deny wallet operativo + fail-open CC; **non** implementa MC-042 v2 (login off / zero accesso autonomo / canale Super Admin). |

---

## Stato implementativo (post auth Founder 18/11 — branch `cursor/mc042-v2-suspend-deroga-e393`)

| Requisito MC-042 v2 | Codice | Esito |
|---|---|---|
| Login/password disattivati su cessazione | `assert_user_login_allowed` su login / Google / MFA | **CONFORME** |
| Nessun accesso autonomo piattaforma | `enforce_commercial_access` in `get_current_user` | **CONFORME** |
| Nessuna read autonoma fatture/documenti | Nessuna API self-serve post-cessazione | **CONFORME** |
| Nessun accesso wallet | `cc_is_wallet_operable` + assert | **CONFORME** |
| Conservazione dati | Ledger/nomine/CC restano in DB; no delete su cease | **CONFORME** |
| Email → Super Admin | Processo manuale (hint 403); non UI product | **ACCETTATO** |

**Conclusione:** MC-042 v2 enforcement **implementato** con autorizzazione esplicita Founder 18/11 (insieme a MC-054 B + MC-055…059).

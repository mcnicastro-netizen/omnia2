# B04-H2 — Conformità e registro decisioni Founder (§14 chiuso)

**Aggiornato:** 17 novembre 2026 · ~19:30 Europe/Rome  
**Baseline design:** `B04-H2-MAIN-ADMIN-TECHNICAL-DESIGN.md` (stesso turno, aggiornato)  
**Stato:** **§14 CHIUSO** — decisioni Founder formalizzate.  
**Implementazione codice:** autorizzata e consegnata su branch `cursor/b04-h2-main-admin-impl-e393` (no merge finché Founder non lo chiede).

---

## Distinzione obbligatoria

| Tipo | Significato |
|---|---|
| **Decisione Founder** | Vincolante per l’implementazione futura |
| **Raccomandazione tecnica** (design) | Scelta ingegneristica subordinata alle decisioni; non governance |

---

## Registro decisioni Founder (complete)

Approvate esplicitamente dal Founder (17 nov 2026): conformità ChatGPT 1–6/8–10 + chiusura G7/G8/TTL.

| ID | Decisione Founder | Testo vincolante |
|---|---|---|
| **D01** | Nomina iniziale | Solo Super Admin Ops, procedura tracciata. Vietate auto-nomina e derivazione da `owner_id` / `agency_admin`. |
| **D02** | Multi-CC | Un User può essere Main Admin di più CommercialCustomer; ogni nomina esplicita e indipendente. |
| **D03** | Membership | Non obbligatoria per l’autorità commerciale. La nomina **non** attribuisce accesso CRM. |
| **D04** | Fine Membership | Non cancella automaticamente la nomina. La perdita di idoneità account → blocco immediato autorità wallet. |
| **D05** | CC cessato | Nessuna amministrazione operativa wallet. Conservare identità, nomine, ledger/storico. Consultazione limitata secondo B16 e DES-07/08. **Precisata da MC-042 v2 / D-177 (18 nov 2026):** su cessazione definitiva **nessun** accesso autonomo (login/password off; no sola lettura self-serve; richieste via email al Super Admin). Conservazione ≠ accesso. *(D-176 whitelist autonoma chiusura+fatturazione = **SUPERATA**.)* |
| **D06** | `group_admin` | Nessuna autorità wallet per il solo ruolo. Serve nomina esplicita Main Admin. |
| **D07 / G7** | Super Admin allocate/revoke | **Non** privilegio ordinario. Solo intervento **straordinario**, motivato, audit append-only (attore, CC, Organization, importo, operazione, esito). Nessun aggiramento isolamento CC. Non trasferisce/attribuisce titolarità Main Admin. Coerente B02 + B16. |
| **D08 / G8** | Notifica transfer | Sempre notifica in **Cabina OMNIA**. Email Resend **best-effort**; fallimento email non blocca consultazione/accettazione in Cabina. No token in chiaro nei log. Notifica ≠ privilegio. |
| **D09 / TTL** | Validità proposta | **48 ore** (design originale). Alla scadenza: invalidata, non accettabile; va riproposta. |
| **D10** | Transfer effettivo | Solo dopo accept del nuovo Main Admin con token valido. Fino ad allora resta il titolare attuale se idoneo. |
| **D11** | Perdita requisiti Main Admin | Blocco immediato wallet centrale. Nessuna successione automatica. Nuova nomina = Super Admin Ops. |
| **D12** | Deny immediato endpoint | Ogni endpoint admin wallet verifica backend: identità, idoneità, stato CC, autorità. `null` / non idoneo / non operativo → deny. Breaking change su `/wallet` per `agency_admin` **accettata**. |

### Precisazioni Founder acquisite

1. Main Admin **non** è ruolo globale: autorità per singolo CC.  
2. Transfer a due fasi **atomico**; proposta non conferisce privilegi; mai due titolari attivi.  
3. Cessazione CC ≠ perdita requisiti utente: storie e regole distinte.

---

## Matrice conformità vs §14 design (aggiornata)

| §14 originale | Decisione | Esito |
|---|---|---|
| 1 Nomina Ops | D01 | **Chiuso** |
| 2 Multi-CC | D02 | **Chiuso** |
| 3 Membership | D03 | **Chiuso** |
| 4 Fine Membership / idoneità | D04 + D11 | **Chiuso** |
| 5 CC ceased | D05 | **Chiuso** |
| 6 group_admin | D06 | **Chiuso** |
| 7 Super Admin allocate/revoke | **D07 / G7** | **Chiuso** (straordinario, non ordinario) |
| 8 Canale notifica | **D08 / G8** | **Chiuso** (Cabina sempre + email best-effort) |
| 9 TTL | **D09** | **Chiuso** (**48h**; 7 giorni **revocato**) |
| 10 Breaking `/wallet` | D12 | **Chiuso** |

**Verdetto:** §14 **completamente chiuso**. Nessuna decisione di governance lasciata a Cursor.

---

## Correzioni rispetto a bozze precedenti

| Bozza | Valore errato/provvisorio | Valore Founder definitivo |
|---|---|---|
| ChatGPT TTL | 7 giorni | **48 ore** |
| Design esecutivo (prima stesura) | Super Admin con accesso wallet “ordinario” ops | Solo **straordinario** motivato (D07) |
| Conformità precedente | Gap G7/G8 aperti | **Chiusi** |

---

## Ambiguità residue (non bloccano §14; da chiarire solo in implementazione se emergono)

| ID | Ambito | Nota | Blocca §14? |
|---|---|---|---|
| A1 | Forma esatta “motivazione obbligatoria” Super Admin straordinario | Campo `reason` obbligatorio non vuoto + eventuale ticket_id opzionale — **scelta tecnica** | No |
| A2 | UI Cabina per accept transfer | Path UX preciso sotto founder_ops — **scelta tecnica** entro D08/D10 | No |
| A3 | Job di expiry transfer | Cron/lazy-expire on read — **scelta tecnica** entro D09 | No |
| A4 | CC `ceased`: Main Admin può ancora accept transfer? | Consigliato **no** (stato non operativo) — allineato D05; da applicare in codice | No (implicito D05/D12) |
| A5 / **MC-042** | Cessazione definitiva (accesso) | **v2 APPROVATA** (D-177): no accesso autonomo; Super Admin via email. Enforcement completo **mancante**; pezzo wallet #218. | No senza mandato; firma MC-026b con riserve o impl dedicata |

Nessuna di queste riapre governance §14.

---

## Stato post-implementazione (17 nov 2026)

- Implementazione H2 consegnata su `cursor/b04-h2-main-admin-impl-e393` @ `bb0ef5eb` — PR #216 — CI verde.
- Handoff analisi ChatGPT: `B04-H2-MAIN-ADMIN-HANDOFF-CHATGPT.md`.
- **Ancora non autorizzati:** merge `main`, H3/H4/legacy/B04-III+, produzione/Stripe live.

---

## Coerenza interna verificata

- D07 non contraddice B02 (Super Admin tecnico): privilegio **non ordinario**.  
- D03+D04 rispettano B01 (autorità commerciale ≠ Membership).  
- D05 allineato DES-07/08 e B16.  
- D09=48h allineato design originale; 7g scartato.  
- D08: email non gate di accettazione → coerente con deny-by-default e Cabina.  
- H1 (isolamento CC su revoke) resta intatto e obbligatorio.

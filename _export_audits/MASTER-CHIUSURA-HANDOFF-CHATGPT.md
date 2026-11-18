# OMNIA — Handoff ChatGPT: revisione piano chiusura master post-audit

**Data:** 17 novembre 2026 · ~20:30 Europe/Rome  
**Ruolo ChatGPT:** revisore del **piano di chiusura** (sola lettura).  
**Non** riprogettare OMNIA. **Non** riaprire decisioni. **Non** chiedere nuovo codice.  
**Ruolo Cursor:** ha prodotto il piano da documenti repo + verifica CI/merge; attende esito Founder.  
**Founder:** dopo la tua revisione, decide accettazione residui / chiusura strato B / merge PR docs.

---

## 0. Istruzioni operative (obbligatorie)

1. Obiettivo: verificare se il piano è **completo, non duplicato, non confuso tra strati**, e se i criteri di chiusura sono **oggettivi e usabili**.
2. **Non** trasformare il piano in backlog di implementazione H3/H4/B04-III/B05–B07.
3. **Non** riaprire: B01–B03 DEC, B04 DES-01…10, D01–D12, B16 già approvate.
4. **Non** usare `OMNIA-HANDOFF-PER-CHATGPT.md` (14 nov) come SoT corrente — è marcato **STALE**.
5. Distingui sempre:
   - decisione Founder ≠ implementazione  
   - strato A (audit/design) ≠ strato B (impl autorizzata) ≠ strato C (readiness)
6. Se manca evidenza nei documenti allegati: scrivi `NON VERIFICABILE` — **non inventare**.
7. Una sola risposta, nel formato §8 esatto.

---

## 1. Documenti da usare (ordine)

### Primari (obbligatori)

1. `MASTER-CHIUSURA-POST-AUDIT-PIANO.md` — **oggetto della revisione**
2. `MASTER-CHIUSURA-HANDOFF-CHATGPT.md` — questo file (regole)
3. `memory/NEXT_SESSION.md` — stato operativo aggiornato 17 nov ~20:20

### Contesto minimo (se serve approfondire una riga MC)

4. `00-INDICE-AUDIT.md`
5. `CHIUSURA-VERIFICA-STATICA-BLOCCHI-0-7.md` (FASE 1)
6. `FASE-2-BACKLOG-PIANIFICAZIONE-RISANAMENTO.md` (B01–B07 pianificazione)
7. `B04-DES-REGISTRO.md` + estratti rilevanti di `B04-ANO-008-DESIGN-BILLING.md` §6 (slice I…VII)
8. `B04-H2-MAIN-ADMIN-RESIDUAL-IMPLEMENTATION-REPORT.md` (residui H2)
9. `B04-H2-MAIN-ADMIN-DECISIONS-CONFORMITY.md` (D01–D12 chiusi)
10. `B04-OPEN-FOLLOWUPS.md` (OPEN-01 repricing = fuori master B)

### Vietati come SoT corrente

- `OMNIA-HANDOFF-PER-CHATGPT.md` (14 nov, STALE)
- Memoria di chat non documentata

---

## 2. Coordinate tecniche (non contestare; verifica coerenza del piano)

| Campo | Valore |
|---|---|
| Repo | `github.com/mcnicastro-netizen/omnia2` |
| Baseline prodotto | `main` @ `c3baebc40559641590f5a1bac8705400ef992537` |
| Include fix H2 | `99a967ef05040a1b56de4836992dfd54451bcd6c` |
| PR H2 | #216 **MERGED** · CI verde pre/post-merge |
| PR piano docs | https://github.com/mcnicastro-netizen/omnia2/pull/217 · branch `cursor/master-closure-plan-e393` · CI verde su `1cdcc64` |
| Natura PR #217 | **solo documentazione** — non codice prodotto |

Slice mergiate rilevanti (per coerenza strato B): #208 Slice1 · #210 B04-I · #211 B04-II · #212 H1/H2 exact · #216 H2 Main Admin residuale.

---

## 3. Cosa deve dimostrare il piano (criteri di qualità)

Valuta il piano contro questi requisiti Founder:

1. Inventario **unico numerato**, senza duplicati sostanziali.
2. Per ogni attività: ID, descrizione, stato, evidenza, dipendenze, priorità, criterio di chiusura.
3. Distinzione chiara: già risolto / residuo accettabile / fase successiva / fuori master.
4. Nessun blocco lasciato **implicitamente** in sospeso.
5. Criteri per dichiarare chiuso lo strato (A/B/C) verificabili.
6. H3, H4, legacy, B04-III…VII, B05–B07, Stripe live **non** presentati come obbligatori per chiudere lo strato B.
7. **MC-042 v2 (18/11/2026):** cessazione definitiva = **nessun** accesso autonomo; Super Admin via email; dati conservati. D-176 whitelist **SUPERATA**. SoT: `MC-042-DECISIONE-FOUNDER.md` · D-177. PR #218 = pezzo wallet, non v2 completo.  
8. **MC-054…059:** sospensione giorno 8, riattivazione auto, deroga SA — decisioni **approvate**, codice **non** implementato. SoT: `MC-054-059-SOSPENSIONE-RIATTIVAZIONE-DEROGA.md`.

---

## 4. Aree di rischio da controllare (obbligatorie)

| Area | Domanda da rispondere |
|---|---|
| Confusione strati | Il piano permette di dichiarare «master chiuso» intendendo per errore lo strato C? |
| Completeness MC | Mancano voci evidenti rispetto a FASE2 / B04 §6 / residui H2 / igiene doc? |
| Duplicati | Stessa attività sotto due ID? |
| Stati errati | Qualche `IMPL_MERGIATO` non supportato dalle coordinate §2? Qualche `FASE_SUCCESSIVA` che invece è bloccante per B? |
| Criteri deboli | Criteri di chiusura vaghi («quando sarà ok») vs oggettivi? |
| Gate Founder | È chiaro cosa il Founder deve accettare (MC-040…043, MC-026, MC-052) prima di «STRATO B CHIUSO»? |
| Next code | È vietato avviare codice senza nuovo mandato? |

---

## 5. Residui su cui il Founder deve decidere (non reinventare)

| ID | Tema | Opzioni ammesse in output |
|---|---|---|
| MC-040 | UI Cabina accept transfer | **PENDING_FOUNDER** (non auto-approvare proposte ChatGPT) |
| MC-041 | Expiry lazy | **PENDING_FOUNDER** |
| MC-042 | Cessazione v2 | **APPROVATA** · enforcement completo NO · #218 pezzo wallet |
| MC-043 | CC senza MA → deny + runbook | **PENDING_FOUNDER** |
| MC-054…059 | Sospensione/deroga | **APPROVATE** · codice mancante/non conforme |

---

## 6. Cosa NON chiedere / NON proporre

- Nuova implementazione H3/H4/B04-III…VII/B05–B07
- Riapertura D01–D12 o DES
- Auto-nomina Main Admin / euristiche `owner_id` / `agency_admin`
- Merge di codice o deploy
- «Chiudere il master» = prodotto commerciale ready
- Nuovi audit da zero sui Blocchi 0–7

---

## 7. Prompt Founder → ChatGPT (incolla così)

```
OMNIA — REVISIONE PIANO CHIUSURA MASTER POST-AUDIT (sola lettura)

Ruolo: revisore del piano di chiusura. Non riprogrammare OMNIA. Non riaprire decisioni. Non chiedere codice.

Documenti obbligatori (in ordine):
1) MASTER-CHIUSURA-HANDOFF-CHATGPT.md
2) MASTER-CHIUSURA-POST-AUDIT-PIANO.md
3) memory/NEXT_SESSION.md

Contesto se serve: 00-INDICE-AUDIT.md, CHIUSURA-VERIFICA-STATICA-BLOCCHI-0-7.md, FASE-2-BACKLOG-PIANIFICAZIONE-RISANAMENTO.md, B04-DES-REGISTRO.md, B04-ANO-008 §6, B04-H2 residual report + DECISIONS-CONFORMITY, B04-OPEN-FOLLOWUPS.md.

Vietato come SoT: OMNIA-HANDOFF-PER-CHATGPT.md (14 nov, STALE).

Coordinate:
- main @ c3baebc (PR #216 MERGED, include 99a967e)
- PR piano docs #217 @ branch cursor/master-closure-plan-e393 — CI verde
- Slice mergiate: #208 #210 #211 #212 #216

Obiettivo: dire se il piano è idoneo come SoT di chiusura strati A/B (con C esplicitamente fuori), se l’inventario MC è completo/non duplicato, se i criteri sono oggettivi, e cosa deve firmare il Founder prima di «MASTER STRATO B CHIUSO».

Output: UNA sola risposta nel formato A–F dell’handoff §8. Niente altro.
```

---

## 8. Formato output obbligatorio (A–F)

### A) VERDETTO PIANO
Una sola etichetta:
`IDONEO` | `IDONEO CON CORREZIONI` | `NON IDONEO`

### B) VERDETTO STRATI
| Strato | Chiudibile secondo il piano? | Condizioni residue | Nota |
|---|---|---|---|
| A | SÌ / SÌ COND / NO | … | … |
| B | SÌ / SÌ COND / NO | … | … |
| C | NO (atteso) / altro | … | … |

### C) TABELLA INVENTARIO (solo scostamenti)
Elenca **solo** ID MC con problema. Se nessuno: scrivi `Nessuno scostamento rilevante`.

| ID | Problema | Tipo: manca / duplicato / stato errato / criterio debole / ambiguità | Gravità: blocker chiusura B / non-blocker / doc | Correzione proposta (max 1 riga) |
|---|---|---|---|---|

### D) RESIDUI MC-040…043
Per ciascuno: `ACCETTARE` | `DECISIONE FOUNDER RICHIESTA` | `SPOSTARE FASE SUCCESSIVA` + motivo in 1 riga.

### E) RACCOMANDAZIONE FOUNDER (una sola)
`APPROVA PIANO` | `APPROVA CON CORREZIONI DOC` | `NON APPROVARE`

Poi massimo 5 azioni numerate, ciascuna:
`cosa` | `chi (Founder/ChatGPT/Cursor)` | `serve autorizzazione codice? sì/no`

### F) DIVIETI CONFERMATI
Elenco puntato di ciò che resta vietato dopo l’approvazione del piano (almeno: niente H3/H4/III senza mandato; niente confondere B con C; niente riuso handoff 14 nov).

---

## 9. Dopo la risposta ChatGPT

- Founder applica eventuali correzioni doc (Cursor solo se autorizzato / o Founder dice «applica correzioni»).
- MC-042 **v2** e MC-054…059 già decisi (funzionali). Founder conferma ancora MC-040/041/043 e firma MC-026b + MC-052.
- Solo allora: dichiarazione `MASTER STRATO B CHIUSO` e/o merge PR #217 su ordine Founder.
- **Nessun** avvio H3/H4/B04-III / enforcement MC-042 v2 / MC-054…059 senza nuovo mandato.

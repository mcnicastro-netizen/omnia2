# Programma — 9 Ottobre 2026 (Onda F)

**Onda**: F — Controllo di tutti i bottoni del portale (D-118)  
**Mandato**: analisi + matrice · fix solo con «vai» su `P-###`  
**SoT**: `docs/audit/OMNIA_PORTALE_AUDIT_PROGRAM.md` § Onda F  
**Handoff**: `memory/NEXT_SESSION.md`

---

## Obiettivo giornata

Catalogare e provare **ogni** CTA/controllo del perimetro ImmobilCloud B2C + Legal B2C + footer/auth cloud.  
Esito per riga: OK / FAIL / SKIP (+ motivazione) · finding se FAIL.

---

## Boot

```bash
bash scripts/omnia-stack.sh ensure
bash scripts/check-secrets-presence.sh   # class=sk_test obbligatorio
curl -sS http://127.0.0.1:43121/api/billing/plans | python3 -c \
  "import sys,json;d=json.load(sys.stdin);assert d.get('mode')=='test' and d.get('enabled') is True"
```

Se `sk_live` / `mode=live` → **STOP** e segnala Founder (niente checkout).

---

## Metodo

1. Estrarre da FE: `<button`, `onClick`, `Link` CTA, `type="submit"` in `frontend/src/apps/immocloud/**`, Legal B2C, footer/auth cloud  
2. Matrice: `docs/audit/portale-matrici/2026-10-09-onda-f.md`  
   `ID | Pagina | Label/testid | Azione attesa | Precondizione | Esito | Evidenza | Finding`  
3. Prova (HTTP/API + browser se disponibile) · log in `/opt/cursor/artifacts/`  
4. Diario `2026-10-09.md` · aggiorna `portale-finding.md`

---

## Zone obbligatorie (checklist)

- [ ] Top nav desktop + menu mobile  
- [ ] Home hero CTA  
- [ ] Search filters / sort  
- [ ] Property: preferito, contatto, WhatsApp/tel, share  
- [ ] Account: saved search, delete, link sell  
- [ ] Sell: salva, pubblica, elimina, boost, staging, upload  
- [ ] Valutatore: stima, paga PDF  
- [ ] Visura: demo fill, paga, scarica PDF  
- [ ] Mutui: submit lead  
- [ ] Legal: paga / invia domanda  
- [ ] Register / login  
- [ ] Footer legal  
- [ ] Cookie/banner se presente  

---

## Criteri chiusura Onda F

- [ ] 100% bottoni catalogati  
- [ ] 100% provati o SKIP motivato  
- [ ] Matrice + diario + finding aggiornati  
- [ ] PR draft aggiornata (no push `main` senza ordine)

---

## Non fare

- Non iniziare Onda G/H senza chiusura F (o «vai» esplicito a sovrapporre)  
- Non implementare A-038  
- Non fixare P-### senza «vai» sull’ID  

## Residui noti

P-021 Google · P-024 Gemini docs · P-026 vault whsec (Founder Environment)

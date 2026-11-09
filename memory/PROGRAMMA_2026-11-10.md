# Programma · martedì 10 Novembre 2026 (Europe/Rome)

**Obiettivo del giorno**: chiudere **Onda 1 — Storia** (dogfood Nicastro) e portare la lente Storia a **8**, oppure elencare gap bloccanti con prove.

**Freccia**: un solo filo = Storia. Niente SaaS/elefante FE.  
**SoT**: `PROGRAMMA_VERSO_8.md` · `NEXT_SESSION.md` · questo file.

---

## Gate 0 — prima di toccare prodotto (15 min)

1. Merge **#148** (HAL/manuale closeout) se CI verde; altrimenti solo docs già su branch.
2. Smoke: `GET $OMNIA_API_PUBLIC_URL/api/health` → ok/db=ok.
3. Login B2B titolare Nicastro (`titolare@nicastroimmobiliare.it`) su app; verifica membership attiva (D-145).
4. Annota URL reali:
   - white-label `/api/p/nicastroimmobiliare/` (o slug SoT corrente)
   - www `/it` Perché OMNIA paperless (D-148)

**Stop** se login o health falliscono → fix ops, non inventare demo.

---

## Blocco A — Sito white-label × 2 temi × MLS on/off (cuore Onda 1)

Per **tema 1** (es. `classic` o `minimal`) e **tema 2** (es. `atelier` o `mediterranean`):

| Step | Azione | Prove |
|---|---|---|
| A1 | `POST` theme apply → tema N | Brand Studio badge attivo |
| A2 | **MLS on** (join se serve) | Home: box rete + sezione partner · screenshot |
| A3 | Smoke home / lista / scheda | 200 + look tema; no pezzi rotti |
| A4 | **MLS off** (`POST /app/mls/leave`) | Zero pezzi MLS · `mls-box` → `mls_not_enabled` |
| A5 | Ripeti A3 con MLS off | Screenshot before/after |

**DoD blocco A**: 2 temi × 2 stati MLS = 4 stati visitabili, screenshot in `/opt/cursor/artifacts/` (o allegati PR).

---

## Blocco B — Clone keep-brand Nicastro (D-149)

1. `POST /app/website/clone-capture` (build=true) su `https://www.nicastroimmobiliare.it` (o URL Founder).
2. Verifica `website.clone_ready=true` + preview home+lista+scheda.
3. Onestà: se non pixel-perfect → OK documentato; **non** promettere Vision crawl.
4. Riga CHANGELOG + nota diario se gap vs D-023 pieno.

**DoD blocco B**: percorso ripetibile URL → preview 3 pagine, senza feature nuove.

---

## Blocco C — Vetrina www paperless (D-148)

1. Apri `omniarealestateecosystem.it/it` → scroll Perché OMNIA.
2. Check 4° tratto = documenti digitali (Fascicolo / PDF / kit dominio) — **no** firma/PEC inventate.
3. Nav: niente «Cerca casa» in TopNav / CTA finale (D-146).
4. Screenshot 1 viewport Perché + 1 nav.

**DoD blocco C**: claim allineati a prodotto reale.

---

## Blocco D — Chiusura giornata (obbligatorio)

1. Aggiorna `PROGRAMMA_VERSO_8.md`: Storia **8** se A+B+C PASS, altrimenti **~7,x** + lista gap.
2. `NEXT_SESSION.md` + diario `docs/audit/portale-diario/2026-11-10.md`.
3. PR dogfood (screenshot + log) · merge solo se Founder «vai».
4. Opz. **solo se A–C verdi e tempo**: retire `demo-agency-001` Ops · **non** Stripe D-151 (coda esplicita).

---

## Fuori scope domani (vietato mischiare)

- Stripe entitlement template (D-151)
- Vision crawl / headless D-022
- GTM-01 email
- Nuovi temi oltre gallery 8
- Refactor FE/BE «già che ci siamo»

---

## Checklist Founder (1 riga)

> «Voglio vedere Nicastro con 2 temi, MLS acceso/spento, clone preview, e Perché OMNIA paperless senza bugne.»

Se sì a tutto → Storia = **8** e filo verso-8 **chiuso**.

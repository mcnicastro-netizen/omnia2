# Prossima sessione — programma passi

**Aggiornato**: 9 Ottobre 2026  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Branch**: `main`

---

## 🎯 SoT freccia (leggere prima)

**Coerenza di sistema:** [`docs/audit/OMNIA_COERENZA_SISTEMA.md`](../docs/audit/OMNIA_COERENZA_SISTEMA.md)

Scala verità: DECISO → CODICE → LIVE → FIRMATO.  
Sequenza chiusura: **S1 restore firmata → S2 bak O0 runtime → … → S9 O6 → S10 GTM-01**.

---

## Prossimo passo tipico

1. **S1** — O3b restore firmata non-prod (tabella in `docs/ops/RESTORE_MANUAL.md`)  
2. **S2** — Bak runtime = O0 (≤7g / incrementale; oggi ancora full×30)  
3. Solo dopo: demo story unica + O6 PASS + GTM-01  

**Non:** monoblocco “chiudi tutto” · self-serve ON prima di S9 · outreach ~5k email prima di GTM-01.

---

## Stato rapido

| Voce | Esito |
|--|--|
| D-118 A–J + residuo codice | su `main` — ri-verificare LIVE, non rifare |
| O6 self-serve | OFF (CONDITIONAL; manca restore firmata) |
| Bak economia | Design O0 ✅ · runtime ancora as-is (~32×) |
| Fascicolo portale | `docs/audit/OMNIA_PORTALE_AUDIT_FASCICOLO.md` |

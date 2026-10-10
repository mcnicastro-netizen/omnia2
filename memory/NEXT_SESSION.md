# Prossima sessione — programma passi

**Aggiornato**: 10 Ottobre 2026  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Branch**: `main`

---

## 🎯 SoT freccia (leggere prima)

**Coerenza di sistema:** [`docs/audit/OMNIA_COERENZA_SISTEMA.md`](../docs/audit/OMNIA_COERENZA_SISTEMA.md)

Scala verità: DECISO → CODICE → LIVE → FIRMATO.  
<<<<<<< HEAD
Sequenza: S1 (PR) → S2 ✅ → **S3 meter economia** → … → S9 O6 → S10 GTM-01.
=======
Sequenza chiusura: S1 ✅ → **S2 bak O0 runtime** → … → S9 O6 → S10 GTM-01.
>>>>>>> origin/main

---

## Prossimo passo tipico

<<<<<<< HEAD
1. **S1** — O3b restore firmata (branch/PR dedicata; non-prod)  
2. ~~**S2** — Bak runtime = O0~~ ✅ 2026-10-10 (retention 7 + media hardlink)  
3. **S3** — Meter GB reali post-S2; listino fermo o revisione esplicita  
4. Solo dopo: demo story unica + O6 PASS + GTM-01  
=======
1. ~~**S1** — O3b restore firmata non-prod~~ ✅ 2026-10-10 (`docs/ops/RESTORE_MANUAL.md` §6)  
2. **S2** — Bak runtime = O0 (≤7g / incrementale; oggi ancora full×30)  
3. Solo dopo: demo story unica + O6 PASS + GTM-01  
>>>>>>> origin/main

**Non:** monoblocco “chiudi tutto” · self-serve ON prima di S9 · outreach ~5k email prima di GTM-01.

---

## Stato rapido

| Voce | Esito |
|--|--|
| D-118 A–J + residuo codice | su `main` — ri-verificare LIVE, non rifare |
<<<<<<< HEAD
| Bak O0 runtime (S2) | ✅ default `BACKUP_RETENTION_DAYS=7` + incrementale hardlink |
| O6 self-serve | OFF (CONDITIONAL; S1 restore + S9 Founder) |
| Bak economia | Design O0 ✅ · runtime S2 ✅ · **meter → S3** |
=======
| O3b restore firmata | ✅ PASS 2026-10-10 · `demo-agency-001` · bak `2026-10-10` |
| O6 self-serve | OFF (CONDITIONAL; O3b ok — manca firma Founder S9) |
| Bak economia | Design O0 ✅ · runtime ancora as-is (~32×) → **S2** |
>>>>>>> origin/main
| Fascicolo portale | `docs/audit/OMNIA_PORTALE_AUDIT_FASCICOLO.md` |

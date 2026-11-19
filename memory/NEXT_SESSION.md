# Prossima sessione — programma passi

**Aggiornato**: 19 Novembre 2026 (~17:30 CET — Europe/Rome) · fine giornata  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**main tip**: `67b5e9216e646214e3eb21b1cb9080cf481b1081` (merge #234 C4)  
**Master A+B**: **CHIUSO**  
**D-175 C1–C4**: **CHIUSI in main**  
**C5–C8 / Dogfood E2E**: **Non autorizzati**

---

## Dove siamo

| Item | Stato |
|------|-------|
| Master A+B | **CHIUSO** |
| Dogfood Step 1 | **CHIUSO** |
| D-175 C1 Perimetro | **CHIUSO** |
| D-175 C2 Backup/restore | **CHIUSO** |
| D-175 C3 Base permanente | **CHIUSO** |
| D-175 C4 Account/org | **CHIUSO** (PR #234 @ `2ae1234` → `67b5e92`) |
| D-175 C5 Crediti/storage H4 | **Non autorizzato** |
| D-175 C6 Stripe ciclo | **Non autorizzato** |
| D-175 C7 Registro/scenari | **Non autorizzato** |
| D-175 C8 Certificazione | **Non autorizzato** |
| Dogfood E2E completo | **Dopo C5–C8** |

## Domani si riparte da qui

1. **Decisione Founder** su avvio **C5** (acquisti crediti/storage / H4) — solo con mandato esplicito.  
2. Se C5 autorizzato: usare la struttura Dogfood già pronta su `omnia_df_clean_c4` (account sintetici già inventariati; credenziali in `dogfood/c4/CREDENTIALS.local.json`).  
3. Non confondere: **stessa P.IVA + filiali** = già collaudato (C4); **affiliati network autonomi** (P.IVA distinte) = da verificare nelle fasi successive.  
4. Permanente C3: **mai** target di test funzionali.  
5. **Non** Stripe LIVE / produzione senza mandato dedicato.

## Non fare

- Avviare C5–C8 o E2E senza nuova frase di autorizzazione Founder.  
- Inventare account reali / Nicastro / email vere.  
- Scrivere sulla base permanente.  
- Dichiarare «Dogfood completo» solo perché C4 è in main.

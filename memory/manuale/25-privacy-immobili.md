# Capitolo 25 · Privacy immobili (L1–L4)

> Controlla chi vede cosa su un immobile. **D-051**: L1+L2 pubblici in vetrina; L3 lead qualificati; L4 solo team agenzia.

## 25.1 · Livelli
| Livello | Chi vede |
|---------|----------|
| L1 | Anonimo (prezzo mascherato a bucket) |
| L2 | Default portale / autenticati B2C (default listing) |
| L3 | Lead qualificati (email/GDPR) |
| L4 | Solo agenzia interna |

## 25.2 · Dove si imposta
- API: `PATCH /api/app/properties/{id}/privacy` + audit.
- UI immobile / privacy (ImmoWeb). Feed portali esclude L3/L4 a monte.

## 25.3 · Masking
- Sotto L4: strip campi sensibili.
- L1: prezzo arrotondato a bucket ~10%.
- Indirizzo completo da L3 in su.

## 25.4 · Limitazioni v1
- UI audit storico limitata (API ha eventi).
- MLS condivide solo visibility public/mls_only (Cap. 27).

## 25.5 · Collegamenti
Cap. 3 Immobili · Cap. 6 Portali · Cap. 16 Compliance.

**Versione capitolo**: v1.0 (2026-09-14 · Cursor M3).

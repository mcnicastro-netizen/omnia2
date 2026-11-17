# Prossima sessione — programma passi

**Aggiornato**: 17 Novembre 2026 (~11:00 CET — Europe/Rome)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  

---

## Dove siamo

| Item | Stato |
|------|-------|
| Verifica statica 0–7 | CHIUSA |
| B01 design | CHIUSO |
| B02 design | CHIUSO |
| B03 design | CHIUSO (DEC-01…03 / D-174) |
| B04–B07 | NON APERTI |
| Codice risanamento | NON AUTORIZZATO |

## Prossimo passo consigliato (Founder sceglie)

**Opzione A (consigliata)** — Prima esecuzione limitata:
```
Autorizzo esecuzione SOLO dello slice 1: modello dati B01 minimo
(CommercialCustomer + Organization link + Membership storica con una sola attiva)
+ B03-DEC-02 invalidazione sessioni su reset/cambio password
+ B03-DEC-01 gate email verify sulle route operative.
Niente B04 billing, niente MLS, niente migrazione produzione.
Branch feature, PR, test. Fermarsi a fine slice 1.
```

**Opzione B** — Continuare solo design:
```
Autorizzo solo design B04 (billing / ANO-008), senza codice.
Vincoli B01–B03. Non aprire B05–B07. Fermati a fine design B04.
```

SoT: `_export_audits/` · D-173 · D-174 · `RIPRENDI_2026-11-16.md`

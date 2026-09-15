# 🎯 PIANO DI ESECUZIONE — Completamento Progetto OMNIA

**Data**: 23-Feb-2026  
**Chiusura formale Sprint 1→4**: **15-Set-2026** → `PROGRAMMA_CONCLUSIONE.md`  
**Status**: ✅ **SPRINT 1–4 COMPLETATI**  
**Ambito chiuso**: M1, M2 (incl. M2.5 + M2.6), M3, M5 (S1/S2/S3/S4/S5). M4 e M6 fuori scope.

---

## ⛔ REGOLA DI DISCIPLINA (vincolante)

**Nessuna deviazione dall'ordine sotto è ammessa**, salvo:
- Bug critico bloccante segnalato dal Founder o dal cliente pilota
- Richiesta legale/GDPR urgente
- Nuova decisione strategica formalizzata in `DECISIONS.md` con firma Founder

**Ogni nuova idea che emerge durante lo sviluppo va salvata in `ASPETTI_DA_APPROFONDIRE.md` e NON implementata durante lo Sprint corrente.**

---

## 📋 ORDINE DI ESECUZIONE (tassativo)

### 🔴 SPRINT 1 — Chiusura M2.5 al 100%
**Obiettivo**: portare M2.5 White Label / Doppio Binario al 100% del programma originale.

| # | Item | Effort | Stato |
|:-:|---|:-:|---|
| 1 | **M2.5.5 Domain Vault** | ~1g | ✅ **DONE (23-Feb-2026)** — signup con garanzia contrattuale + policy pubblica + audit trail + 11/11 pytest. Vedi D-056. |
| 2 | **M2.6c Social Publisher** (FB Graph + Instagram Business + Telegram Bot APIs) | ~2g | ✅ **DONE (24-Feb-2026)** — adapter async httpx FB/IG/Telegram + credenziali cifrate AES-GCM + audit trail social_posts + 16/16 pytest. Vedi D-058. |
| 3 | **M2.6d Universal Portal Wizard** (self-service custom portali) | ~1g | ✅ **DONE (23-Feb-2026)** — 4-step wizard + tenant isolation + 13/13 pytest. Vedi D-057. |

**Sprint 1 status: 3/3 items completati ✅.** Prossimo: Sprint 2 · M5.S2 HAL Knowledge.

**Definition of Done Sprint 1**: M2.5.5 + M2.6c + M2.6d in produzione, testati con pytest e smoke E2E screenshot. Regressione totale 100% pass.

---

### 🟡 SPRINT 2 — M5.S2 HAL Knowledge
**Obiettivo**: chatbot "how-to" della piattaforma OMNIA che risponde su come usare le funzionalità.

| # | Item | Effort | Stato |
|:-:|---|:-:|---|
| 4 | **M5.S2 HAL Knowledge** — RAG + Manuale | — | ✅ **DONE** (manuale 27/27 + motore live) |

**Definition of Done Sprint 2**: ✅ raggiunto.

---

### 🟢 SPRINT 3 — Chiusura backlog M3 + M5.S4
**Obiettivo**: chiudere gli item DoD di M3 e M5 mai completati.

| # | Item | Effort | Stato |
|:-:|---|:-:|---|
| 5 | **M3.S8 Ricerca avanzata B2C** | — | ✅ DONE |
| 6 | **M3.S9 Privacy audit 4 livelli** | — | ✅ DONE |
| 7 | **M5.S4.2 Reverse Staging + varianti + CRM-aware** | — | ✅ DONE |
| 8 | **M5.S4.3 Micro-tour video** | — | ✅ DONE |
| 9 | **M5.S4.4 A/B testing portale** | — | ✅ DONE |

**Definition of Done Sprint 3**: ✅ raggiunto.

---

### 🔵 SPRINT 4 — Perf hardening + Deploy readiness
**Obiettivo**: preparare OMNIA a scalare oltre le 20 agenzie senza degradazione.

| # | Item | Effort | Stato |
|:-:|---|:-:|---|
| 10 | Async geocoding (opzione B: saltato — scelta Founder) | — | ⏭️ skipped |
| 11 | **Projection list properties** | — | ✅ DONE |
| 12 | **Stress test 5 agenti** | — | ✅ DONE (11/11) |
| 13 | **Deploy readiness + objstore foto** | — | ✅ DONE (D-067/068/069) |

**Definition of Done Sprint 4**: ✅ raggiunto (26-Feb-2026). Chiusura formale documenti: 15-Sep-2026.

---

## 🛑 FUORI SCOPE (esplicitamente rimandati)

Questi item **NON verranno affrontati** durante Sprint 1→4:

- 🛑 **M4 MLS + Stripe + Crediti** — bloccato dalla costituzione società (D-035)
- 🛑 **M5.S7 Modulistica AI** — post-società
- 🛑 **M5.S8 Firma elettronica + Visure** — post-società
- 🛑 **M6 Omnia Academy** — in coda per volere Founder
- 🛑 **Manuale Operativo cap. 3-20** — in coda per volere Founder
- 🛑 **Pre-launch commerciale** — congelato D-035 fino a M6 completo
- 🛑 **Video promo brand OMNIA** — sospeso, riprendiamo dopo Sprint 4
- 🛑 **Aspetti da approfondire A-001 (BNPL), A-002 (NVIDIA), A-003 (Creative Studio)** — restano memorizzati, non implementati
- 🛑 **APE Partnership integration** — in attesa risposte da APEFACILE + EnUp, riprende quando ci saranno info concrete
- 🛑 **Nuove landing marketing** — nessuna finché Sprint 1→4 non chiusi

---

## 📅 Timeline stimata

```
Settimana 1  →  Sprint 1 (M2.5.5 + M2.6c + M2.6d)      ~4 giorni
Settimana 2  →  Sprint 2 (M5.S2 HAL Knowledge)          ~3 giorni
Settimana 3  →  Sprint 3 (M3 backlog + M5.S4 backlog)   ~7 giorni
Settimana 4  →  Sprint 4 (Perf hardening + deploy)      ~2 giorni

TOTALE stimato: ~16 giorni di lavoro effettivo
```

Al termine di Sprint 4, lo stato del progetto sarà:

```
✅ M1 (100%)
✅ M2 core (100% DoD)
✅ M2.5 (100% incl. Domain Vault + Social Publisher + Portal Wizard)
✅ M2.6 (100% incl. Publishing + Sync + Social + Wizard)
✅ M3 (100% incl. ricerca avanzata + privacy audit)
✅ M5 core: S1 + S2 + S3 + S4 completo + S5 (S6 rimosso, S7/S8 post-società)
✅ Perf hardening completato
✅ Deploy readiness verificato

🛑 M4 → aspetta società
🛑 M6 → aspetta decisione Founder
```

**Fondamentalmente**: OMNIA sarà tecnicamente pronto per il pre-launch commerciale (subordinato a M6 Academy per D-035).

---

## 🔒 Firma di accettazione

- **Founder** (mcnicastro): approvato 23-Feb-2026 — *"ordine tassativo da rispettare, basta deviazioni, si va dritti al completamento del progetto"*
- **Main agent** (E1): committed a rispettare l'ordine sopra senza deviazioni

---

*Documento vincolante. Le priorità in `ROADMAP.md` sono subordinate a questo file finché Sprint 4 non è completato.*

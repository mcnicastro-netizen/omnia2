# 💰 OMNIA — Pricing Book (B2B agenzie)

**Versione**: 3.0 (LISTINO UFFICIALE B2B)
**Ultima revisione**: 5 Agosto 2026 — approvato dal Founder
**Stato**: 🟢 ATTIVO · sincronizzato con `backend/apps/billing/plans.py` + catalog Stripe sandbox
**Sovrascrive**: v2.0 (bozza superata) e ogni listino Founders 50 precedente

> 📎 **Per privati (portale ImmobilCloud)** → vedi **`PRICING_B2C.md`** v1.0 (rail carta one-shot, nessun credito).

---

## 🎯 Filosofia (invariata)

1. **Premium positioning**, non penetration
2. **Founders 12 mesi** con lock-in tariffario, poi passaggio automatico al listino Standard
3. **Sistema crediti** a valore unitario fisso €0,05/credito
4. **Annunci agenzia INCLUSI** senza limiti "morbidi" nei tier (Starter 30 · Pro 200 · Agency ∞)
5. **Multiposting + Portal Wizard custom** in **tutti** i piani
6. **Doppio Binario (D-041)**: ogni feature vendibile anche via widget/API
7. **Anti bait-&-switch**: il prezzo Founders resta invariato per 12 mesi

---

## 🏢 ImmoWeb — Piani abbonamento

### Fase Founders (primi 12 mesi dall'ingresso agenzia)

| Piano | Mensile | Annuale | Utenti max | Immobili max | Crediti/mese inclusi |
|-------|:-:|:-:|:-:|:-:|:-:|
| **Starter** | **€49** | **€490** (2 mesi gratis) | 3 | 30 | **120** |
| **Pro** | **€99** | **€990** | 10 | 200 | **1.200** |
| **Agency** | **€249** | **€2.490** | illimitati | illimitati | **3.600** |

### Fase Standard (dopo 12 mesi Founders)

| Piano | Mensile | Annuale |
|-------|:-:|:-:|
| Starter | €79 | €790 |
| Pro | €179 | €1.790 |
| Agency | €349 | €3.490 |

**Sconto annuale**: 2 mesi gratis (paghi 10, ricevi 12)
**Trial**: 14 giorni su tutti i piani
**Carta Stripe** obbligatoria all'onboarding

**Enterprise**: 🟡 TBD — posizionamento e Custom API pricing rivisti in sessione dedicata

---

## 💳 Sistema Crediti — €0,05 per credito

Valore unitario **fisso** e stabile. 1 credito = 5 centesimi (ratio 20 crediti/€).
I crediti inclusi nel piano si sommano ai pacchetti ricarica acquistati.

### Consumo servizi (listino Founder 5 ago 2026)

| Servizio | Crediti | Prezzo effettivo | Margine indicativo |
|----------|:-:|:-:|:-:|
| SMS notifica al cliente | 4 | €0,20 | 60% |
| Query **HAL Agents** (assistente CRM) | 4 | €0,20 | 75% |
| **Valuator base** | 6 | €0,30 | 85% |
| **Valuator UNI 10750 + PDF** | 12 | €0,60 | 82% |
| Query **HAL Legal** (con citazioni) | 12 | €0,60 | 90% |
| **Virtual Staging** (pipeline 3-stage) | 18 | €0,90 | 88% |
| **Visura catastale** | 24 | €1,20 | 40-60% (dipende dal partner) |
| **APE search** regionale | 60 | €3,00 | 30% (fee partner) |
| **Micro-tour video 10s** (Kling Pro) | 60 | €3,00 | 68% |
| **Promozione TOP** (7 giorni) | 400 | €20 | rev share |
| **Promozione Premium** (15 giorni) | 1.000 | €50 | rev share |
| **In Evidenza** (30 giorni) | 2.000 | €100 | rev share |

**❌ Rimossi dalla v1 del listino**:
- Planimetria catastale
- Ispezione ipotecaria

*(motivo: margini troppo bassi al volume attuale. Verranno riproposti quando avremo volumi >100 richieste/mese e un contratto quadro con il partner)*

### Pacchetti ricarica (Founder 5 ago 2026)

| Pacchetto | Prezzo | Crediti | Ratio |
|-----------|:-:|:-:|:-:|
| **Mini** | €20 | 400 | 20 cr/€ |
| **Small** | €50 | 1.000 | 20 cr/€ |
| **Standard** | €100 | 2.000 | 20 cr/€ |
| **Plus** | €250 | 5.000 | 20 cr/€ |
| **Power** | €500 | 10.000 | 20 cr/€ |
| **Enterprise** | €1.000 | 20.000 | 20 cr/€ |

Il ratio è **costante**: nessuno sconto volume. Semplice, prevedibile, difendibile.
Il "vantaggio" del pacchetto grande sta nell'evitare micro-transazioni ripetute e nel budget mensile lineare per l'agenzia.

---

## 📢 Multiposting & Portali

- **Multiposting standard** (Immobiliare.it, Casa.it, Idealista, Wikicasa, ecc.): **incluso in tutti i piani** — Starter, Pro, Agency, Enterprise.
- **Portal Wizard Custom** (aggiunta di un portale non standard tramite mappatura self-service): **incluso in tutti i piani**.
- **Widget Track B** (embed su sito esterno): incluso in tutti i piani con branding OMNIA visibile; per rimuoverlo servirà l'add-on White-Label (tier Pro+).

---

## 💰 Break-even e sostenibilità (aggiornato al listino 5 ago)

### Ipotesi di costo (mensili, mid-scale)
| Componente | Costo/mese |
|-----------|:-:|
| Tecnici (infra + AI) | ~€250 |
| Business/marketing | ~€300 |
| Ammortamento sviluppo | ~€100 |
| Stripe fees | ~€25 |
| **Totale** | **~€675** |

### Scenari MRR

| Scenario | Agency | MRR base | Margine netto approx. |
|----------|:-:|:-:|:-:|
| Peggiore (tutte Starter Founders) | 14 | €686 | break-even |
| **Realistico mix 60/30/10 Founders** | **10** | **€927** | **≈€250/mese** ✅ |
| Founders pieno (50 agenzie, mix reale) | 50 | ~€4.700 | ~€4.000/mese = **€48.000/anno** |
| Post 12 mesi (metà passa a Standard) | 50 | ~€6.500 | ~€5.800/mese = **€69.600/anno** |

*(Stime interne, da validare mese per mese al lancio reale)*

---

## 🚦 Trigger operativi vincolanti

| Condizione | Trigger |
|---|---|
| **Go-live commerciale** | 15 agenzie Founders firmate e paganti (Stripe attivo) |
| Soglia no-loss | 10-12 agenzie Founders attive |
| Passaggio automatico Standard | 12 mesi dall'ingresso (renewal notification 30 gg prima) |
| Algoritmo boost granulare | Attivazione a 30+ clienti (fase 2, oggi manuale) |

---

## 🔗 Sincronizzazione tecnica

Ogni modifica al listino richiede questi passi (nell'ordine):

1. **Aggiornare** `/app/backend/apps/billing/plans.py` (dizionari `LAUNCH_PLANS`, `POST_TRACTION_PLANS`, `CREDIT_PACKAGES`, `CREDIT_COSTS`).
2. **Rigenerare** il catalog Stripe con `python -m apps.billing.setup_stripe` (idempotente — deactive vecchi prezzi + crea nuovi).
3. **Verificare** via API pubblica: `GET /api/billing/plans`.
4. **Aggiornare** questo documento (`memory/PRICING_OMNIA.md`).
5. **Registrare** la modifica in `CHANGELOG.md`.

Formato lookup key Stripe: `{tier}_{cycle}` per abbonamenti (es. `pro_monthly`) · `{pkg_key}` per pacchetti (es. `pkg_2000`).

---

## 📜 Decisioni bloccate (invariate dal precedente listino)

| Topic | Decisione |
|---|---|
| Referral program | ❌ NO (valutare post-15 Founders) |
| APE come servizio nostro | ❌ Rimosso v1 (solo binario link-out a partner esterno) |
| Pricing lock-in a vita | ❌ NO (solo 12 mesi Founders) |
| Enterprise tier + Custom API | 🟡 RIMANDATO — sessione dedicata |
| Algoritmo boost granulare | 🟡 Fase 2 (post 30 clienti) |
| Sconto volume sui pacchetti crediti | ❌ NO — ratio fisso 20 cr/€ |
| Planimetria/Ipoteca come servizio v1 | ❌ Rimossi (margini) |

---

## 🗓️ Storico versioni

| Data | Versione | Note |
|------|----------|------|
| 05-Ago-2026 | **v3.0** | LISTINO UFFICIALE approvato Founder. Founders 12m €49/99/249, Standard €79/179/349, pacchetti ratio 20 cr/€, planimetria/ipoteca rimossi |
| 26-Giu-2026 | v2.0 (bozza superata) | Founders 50 24m €39/99/249 + sconto 50% a vita — non approvato |
| — | v1.x | Versioni preliminari, superate |

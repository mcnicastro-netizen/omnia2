# 📊 Dossier commerciale — Call partner APE

**Data preparazione**: 23-Feb-2026
**Uso**: 1-pager da avere davanti durante le call con APEFACILE e Certificato-Energetico.it (EnUp)
**Email inviate**: vedi `apefacile_partnership.md` + `certificato_energetico_enup_partnership.md`
**Scaletta domande**: vedi `scaletta_call_ape.md`

---

## 🎯 Pitch di apertura (60 secondi)

> *"OMNIA Real Estate Ecosystem è la prima piattaforma italiana che riunisce in un unico prodotto CRM per agenzie immobiliari, portale annunci B2C, AI generativa (valutazioni + virtual staging + assistente normativo) e ora anche compliance layer con validatore APE integrato. Siamo in preview con la nostra prima agenzia pilota a Catania e stiamo costruendo l'infrastruttura per scalare a 50+ agenzie entro 12 mesi."*
>
> *"Vi contatto perché stiamo cercando UN partner unico per integrare l'ordine dell'APE ufficiale direttamente nel flusso di lavoro dell'agente (dalla scheda immobile del CRM, in un click) e nel flusso del privato che carica un annuncio sul nostro portale B2C. Vogliamo dare al nostro utente il servizio più affidabile del mercato, senza doverci occupare noi della parte tecnica del certificato."*

---

## 📊 Volumi stimati (numeri per la trattativa)

### Anno 1 (2026) — fase pilota / lancio
| Segmento | Immobili in DB | APE stimati/anno | Note |
|---|---:|---:|---|
| Agenzie Track A (paganti) | 40 agenzie × 60 immobili = 2.400 | ~1.400 | ~60% attivi/anno |
| Agenzie Track A (Founders) | 10 agenzie × 60 = 600 | ~350 | scontate/incluse nel piano |
| Privati B2C (ImmobilCloud) | ~4.000 annunci privati | ~1.500 | conversion 35% (obbligo APE) |
| Enterprise / Franchising | 0-1 gruppo | 0-500 | non ancora firmato |
| **TOTALE Anno 1** | **~7.000 immobili** | **~3.250 APE** | equivalenti a ~€260k in ordini APE al listino (avg €80) |

### Anno 2 (2027) — scaling
| Segmento | APE stimati/anno |
|---:|---:|
| Track A B2B | ~10.000 |
| Track B (API partner web agency) | ~3.000 |
| B2C ImmobilCloud + valutatore | ~8.000 |
| **TOTALE Anno 2 target** | **~21.000 APE** |
| Fatturato APE cliente finale (@€80 avg) | ~€1.68M |

**Punto forte in trattativa**: OMNIA è **B2B + B2C simultaneamente**. Nessun altro gestionale italiano offre questo doppio canale. Il partner APE guadagna un canale ORDINI dal privato che oggi non ha (i privati non hanno un gestionale).

---

## 🎯 Cosa chiediamo al partner (checklist call)

### 🥇 Deal-breaker (senza questi 4 non se ne parla)
1. **API REST** con API key dedicata al canale partner OMNIA
   - Endpoint: `POST /ordine`, `GET /ordine/{id}`, `GET /certificato/{id}/download`
   - Autenticazione OAuth2 Client Credentials o Bearer statico
   - Documentazione completa (Swagger/OpenAPI preferibile)
2. **Listino B2B pay-per-use**
   - Nessun canone fisso mensile / annuale
   - Nessun minimo di volume (soglia zero)
   - Prezzo bloccato in contratto per almeno 12 mesi
3. **Prezzo cliente finale ≤ listino pubblico del partner**
   - Vincolo tassativo — noi rivendiamo con markup zero o minimo, l'utente non paga più che andando direttamente sul sito del partner
   - Il partner assorbe eventuali costi di integrazione B2B
4. **SLA canale partner**
   - Tempi consegna garantiti in contratto (24-48h per APEFACILE, 3-5gg per EnUp)
   - Assistenza dedicata con SLA di risposta max 24h
   - Escalation path per casi urgenti

### 🥈 Nice-to-have (aumentano il valore ma non deal-breaker)
5. **White label o co-branding** del flusso d'ordine dentro OMNIA
6. **Webhook** sugli stati (ordine ricevuto / sopralluogo fissato / certificato pronto)
7. **APE interattivo integrabile** nel nostro Fascicolo Immobile (SOLO EnUp — enHub)
8. **Fallback fisico** quando il video-rilievo non è praticabile (SOLO APEFACILE)
9. **Rev-share o commissione** riconosciuta a OMNIA (2-5% per ordine sarebbe standard)

---

## ⚖️ Matrice di confronto rapida (da tenere aperta durante entrambe le call)

| Criterio | Peso | APEFACILE | EnUp | Note |
|---|:---:|---|---|---|
| Compliance normativa APE (rilievo) | 🔴🔴🔴 | Video (con parere legale) | Solo fisico (inattaccabile) | EnUp vince per franchising risk-averse |
| API disponibili | 🔴🔴🔴 | Da chiarire | Form embeddabile, API vera? | Punto cruciale |
| Velocità consegna | 🟠🟠 | 24-48h ⭐ | 3-5gg | APEFACILE vince |
| Copertura Italia | 🟠🟠 | ? | ? Sicilia/province minori? | Da chiarire per entrambi |
| Prezzo B2B | 🟠 | ? | ? | Solo dopo NDA |
| Digitalizzazione pagamento | 🟡 | Alta | Media (contanti/bonifico) | APEFACILE meglio integrato |
| APE interattivo (enHub) | 🟢 bonus | ❌ | ✅ | Valore unico EnUp |
| Track record B2B | 🟡 | Immobiliare.it ⭐ | Programma "Collabora" | APEFACILE più maturo B2B |

---

## 💰 Struttura commerciale proposta

**Modello preferito**: **rev-share** invece di markup fisso
- OMNIA espone al cliente il prezzo pubblico del partner (nessun sovrapprezzo)
- Il partner riconosce a OMNIA una commissione X% (target: 8-12%) per ogni ordine originato
- Vantaggio partner: canale ordini gratuito, no upfront
- Vantaggio OMNIA: revenue passiva senza rischiare la relazione col cliente

**Modello di fallback** (se rev-share rifiutato):
- Listino B2B scontato (10-15% sconto sul pubblico)
- OMNIA rivende al prezzo pubblico → margine puro del 10-15%
- Rischio: partner può cambiare listino e comprimerci il margine

**Modello NO GO**:
- Canone fisso mensile / annuale
- Minimo di volume garantito
- Esclusiva unilaterale (noi legati, loro no)

---

## 🚨 Red flags (motivi per NON firmare)

- ❌ Solo form embeddabile senza API (non basta per il nostro caso d'uso)
- ❌ Nessuna documentazione tecnica
- ❌ Pretesa di esclusiva
- ❌ Prezzo cliente finale sopra il listino pubblico
- ❌ SLA "best effort" senza numeri
- ❌ Titolarità dei dati cliente non chiara (chi possiede l'anagrafica dell'acquirente APE?)
- ❌ Rifiuto di white label / co-branding minimo

---

## 📞 Prossimi passi operativi

1. **Prima delle call**: rileggere `scaletta_call_ape.md` (25 domande già preparate)
2. **Durante le call**:
   - Registrare (con consenso) o prendere note strutturate
   - Compilare la matrice sopra in tempo reale
   - Non firmare NDA in call — chiedere invio via PEC
3. **Post call (entro 24h)**:
   - Aggiornare `scaletta_call_ape.md` con le risposte
   - Redigere valutazione comparativa
   - Se un partner soddisfa i 4 deal-breaker → chiedere proposta commerciale scritta
4. **Decisione finale**: entro 2 settimane dalla seconda call
   - Loggare in `DECISIONS.md` come D-056
   - Se scelto il partner → aprire ticket M2.APE per integrazione tecnica
   - Se nessuno adeguato → valutare partner terzo (Casa Green, altri)

---

## 🎁 Bonus: leve psicologiche da usare in trattativa

- **Il nostro DB pilota**: sappiamo esattamente quanti immobili ci passano (mostra credibilità)
- **Il canale B2C è unico**: nessun competitor gestionale ha portale privati integrato (leva forte)
- **La preview è visitabile**: al termine della call proponi *"posso mostrarvi la piattaforma in 5 minuti?"*
- **Timing di lancio**: dì che stai valutando ENTRAMBI i partner in parallelo — nessuna esclusiva, nessuna pressione, ma decisione entro 30 giorni
- **Reciprocità**: proponi di menzionare il partner come "sponsor tecnologico APE" nel materiale marketing OMNIA (visibilità free per loro)

---

## 📋 Post call — cosa loggare in DECISIONS.md

Nome partner scelto · condizioni economiche finali · SLA firmato · endpoint API forniti · data attivazione test · commissione/margine · deal-breaker soddisfatti · red flag mitigati · timeline integrazione tecnica.

---

*Documento redatto da MAIN AGENT il 23-Feb-2026 su richiesta del Founder. Aggiornare dopo ogni call con risposte concrete dai partner.*

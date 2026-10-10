# S3 — Meter economia storage (post-S2)

**Data:** 10 Ottobre 2026  
**Stato:** ✅ numeri calcolati · **proposta Founder: LISTINO FERMO**  
**Dipende da:** S2 bak O0 runtime (retention 7 + hardlink) · D-085 · D-114 · O0 design  
**Artefatto live:** `docs/ops/runs/s3-meter-economia.log`  
**Script:** `scripts/meter_storage_economia.py`

---

## 1. Cosa misura S3

| Domanda | Risposta S3 |
|---------|-------------|
| Quanto disco costa un cliente a quota piena **dopo** S2? | Modello sotto (non più ×32) |
| I canoni €49/€99/€299 reggono? | Sì nello scenario mid @ €0,04/GB |
| Addon +100 GB @ €15 regge? | Sì nello stesso scenario |
| Revisione listino ora? | **No** — listino fermo (proposta) |

**Non è:** fattura cloud reale (€/GB ancora non confermato) · revisione prezzi automatica · DR.

---

## 2. Misura LIVE (Cloud Agent 10-Ott-2026)

| Voce | Valore |
|------|--------|
| `LOCAL_STORAGE_ROOT` du | **0 B** (seed demo senza media) |
| `BACKUP_ROOT` du | ~15 KB (JSONL giorno `2026-10-10`) |
| `BACKUP_RETENTION_DAYS` | **7** |
| Bak health | OK · `media_mode=full_copytree` (media vuoto) |
| Meter agenzie | `demo-agency-001` / `nicastro-agency-001` → used **0 GB** / quota 100 GB (tier pro seed) |

Prova hardlink S2 (sandbox 6 MB × 2 giorni): apparent **2,00×** · `du` reale **~1,00×** → moltiplicatore pieno non è più ×32.

---

## 3. Listino storage (invariato · D-085)

| Piano | Canone Founders | Quota inclusa |
|-------|----------------:|--------------:|
| Starter | €49 | 30 GB |
| Pro | €99 | 100 GB |
| Agency | €299 | 300 GB |
| Addon | €15/mese | +100 GB |

---

## 4. Modello ops post-S2

Con hardlink + hot 7g, il disco ops ≈ `live × moltiplicatore`:

| Scenario | × su live | Significato |
|----------|----------:|-------------|
| best_no_churn | **1,05** | file stabili (hardlink) + overhead JSONL |
| mid_churn | **2,5** | churn tipico O0 (~2–4×) |
| worst_daily_rewrite | **7,2** | riscrittura completa ogni giorno ×7 |

Sensitivity €/GB/mese ops (ipotesi, **non** bill): **0,02 / 0,04 / 0,08**.

### Tabella riferimento — mid_churn ×2,5 @ €0,04/GB

| Tier | Live | Ops ≈ | Costo disco | Canone | Disco % canone | Margine disco |
|------|-----:|------:|------------:|-------:|---------------:|--------------:|
| Starter | 30 | 75 | €3,00 | €49 | 6,1% | €46 |
| Pro | 100 | 250 | €10,00 | €99 | 10,1% | €89 |
| Agency | 300 | 750 | €30,00 | €299 | 10,0% | €269 |
| Addon +100 | 100 | 250 | €10,00 | €15 | 66,7% | €5 |

### Contrasto pre-S2 (full × ~32 @ €0,04) — perché S2 era obbligatorio

| Tier | Ops ≈ | Costo | vs canone |
|------|------:|------:|-----------|
| Starter | 960 GB | €38 | stretto / negativo se altri costi |
| Pro | 3200 GB | €128 | **> €99** |
| Agency | 9600 GB | €384 | **> €299** |

### Stress €0,08/GB · mid

Agency: 750 × 0,08 = **€60** (20% canone) — ancora sostenibile.  
Addon: 250 × 0,08 = **€20** vs €15 → **addon stretto** a €0,08 mid (monitorare; non rivedere ora).

### Stress worst ×7,2 @ €0,04

Agency: 2160 × 0,04 = **€86** (29% canone) — ok.  
@ €0,08: €173 (58% canone) — attenzione ma non rompe il canone da solo.

---

## 5. Verdetto proposto (Founder)

**LISTINO FERMO** — nessuna revisione €49/€99/€299 né quote 30/100/300 né addon €15/100 GB.

Motivi:

1. Post-S2 il modello disco torna **compatibile** coi canoni nello scenario mid @ €0,04 (ipotesi O0).  
2. Pre-S2 a ×32 i piani Pro/Agency erano **economicamente rotti** sul solo disco.  
3. €/GB **non** è ancora una fattura: ricalibrare quando c’è bill cloud reale (o meter Hetzner/AWS).  
4. Addon a €0,08 mid diventa stretto → **osservare**, non cambiare listino oggi.

**Azione successiva non-prezzo:** quando ci sarà volume reale, rieseguire `scripts/meter_storage_economia.py` e aggiornare questa nota (o S3.1).

---

## 6. Firma Founder

| Campo | Valore |
|-------|--------|
| Data | |
| Ha letto numeri §2–§4 | sì / no |
| Decisione listino | **FERMO** / revisione (specificare) |
| Note | |
| Firma | |

---

## 7. Limiti dichiarati

- Sandbox senza media → GB “reali” agenzia = 0; i numeri commerciali sono **modello** post-S2, non telemetria clienti paganti.  
- €/GB ops non confermato.  
- Non include CPU/AI/Stripe/egress — solo storage live+bak.  
- Cold monthly 90g (V1.1) escluso.

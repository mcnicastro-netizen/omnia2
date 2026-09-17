# Capitolo 23 · Micro-tour video e A/B testing

> Video promo immobili (Kling via fal.ai) e sperimentazioni A/B sul portale.  
> **D-051 / D-064 / D-065 / D-066**: Ken Burns **gratuito solo portale B2C**; nel gestionale agenzia → **501** e path ufficiale **Kling Pro a crediti**. Sora non è il path prodotto.

## 23.1 · Micro-tour video (agenzia · ImmoWeb)

- Route API gestionale: `POST /api/app/videos/kling/property/{pid}` (async **202** se crediti ok; **402** senza crediti).
- Download/status: `GET /api/app/videos/{id}`, `/download`.
- Richiede `FAL_KEY` e crediti piano (listino: tipicamente **10 crediti / 10s** Kling Pro — vedi `PRICING_OMNIA`).
- **Ken Burns gestionale** `POST /api/app/videos/kenburns/property/{pid}` → **501** (`kenburns_disabled_in_agency`). Non riaprire senza decisione Founder (A-026 / D-064).

## 23.1b · Ken Burns sul portale B2C (ImmobilCloud)

- Route: `POST /api/cloud/videos/kenburns/property/{pid}` — **ffmpeg gratuito** per arricchire le schede pubbliche / annunci privati.
- Non cannibalizza Kling: gli agenti pagano qualità AI nel CRM; il B2C usa Ken Burns free.
- Se ffmpeg manca in runtime, il job può fallire (`status=failed`).

## 23.2 · A/B testing

- `POST /api/app/analytics/ab-test` crea/registra variante.
- `GET /api/app/analytics/agency/overview` panoramica agenzia.
- Serve a confrontare creatività/annunci, non analytics social Meta.

## 23.3 · Limitazioni v1

- No scheduling social automatico del video (vedi Cap. 15).
- Costo fal.ai a consumo; test live gated.
- Overview analytics essenziale, non BI completa.
- UX del 501 Ken Burns in agenzia ancora grezza (messaggio tecnico) — backlog **A-026**.

## 23.4 · Collegamenti

Cap. 9 Virtual Staging · Cap. 15 Social · Cap. 19 Billing crediti · `ASPETTI` A-026.

**Versione capitolo**: v1.1 (17-Sep-2026 · D-084 contatto debiti + split Ken Burns).

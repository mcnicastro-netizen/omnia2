# Capitolo 23 · Micro-tour video e A/B testing

> Video promo immobili (Kling via fal.ai) e sperimentazioni A/B sul portale. **D-051**: Ken Burns endpoint 501; Sora non è il path ufficiale (D-065 Kling).

## 23.1 · Micro-tour video
- Route API: `/api/app/videos/kling/property/{pid}` (async 202).
- Download/status: `GET /api/app/videos/{id}`, `/download`.
- Richiede `FAL_KEY` e crediti piano.
- Ken Burns `POST .../kenburns/...` → **501** in v1.

## 23.2 · A/B testing
- `POST /api/app/analytics/ab-test` crea/registra variante.
- `GET /api/app/analytics/agency/overview` panoramica agenzia.
- Serve a confrontare creatività/annunci, non analytics social Meta.

## 23.3 · Limitazioni v1
- No scheduling social automatico del video (vedi Cap. 15).
- Costo fal.ai a consumo; test live gated.
- Overview analytics essenziale, non BI completa.

## 23.4 · Collegamenti
Cap. 9 Virtual Staging · Cap. 15 Social · Cap. 19 Billing crediti.

**Versione capitolo**: v1.0 (2026-09-14 · Cursor M3).

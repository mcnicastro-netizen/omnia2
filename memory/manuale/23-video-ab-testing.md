# Capitolo 23 · Micro-tour video e A/B testing

> Video promo immobili (Kling via fal.ai) e sperimentazioni A/B sul portale.  
> **D-051 / D-064 / D-065 / D-066**: Ken Burns **gratuito solo portale B2C**; nel gestionale agenzia → **501** e path ufficiale **Kling Pro a crediti**. Sora non è il path prodotto.

## 23.1 · Micro-tour video (agenzia · ImmoWeb)

- Route API gestionale: `POST /api/app/videos/kling/property/{pid}` (async **202** se crediti ok; **402** senza crediti).
- Download/status: `GET /api/app/videos/{id}`, `/download`.
- Richiede `FAL_KEY` e crediti piano (listino: tipicamente **10 crediti / 10s** Kling Pro — vedi `PRICING_OMNIA`).
- **Ken Burns gestionale** `POST /api/app/videos/kenburns/property/{pid}` → **501** (`kenburns_disabled_in_agency`). Non riaprire senza decisione Founder (A-026 / D-064).

## 23.1b · Ken Burns sul portale B2C (ImmobilCloud · D-140)

- **Dove si genera (SoT UX)**: in **Vendi**, subito dopo le foto — pannello *Video tour* (`B2CVideoTourPanel`). Endpoint owner: `POST /api/cloud/me/properties/{pid}/kenburns` + `GET .../video` (anche **bozza**, dopo almeno un salvataggio con foto).
- **Scheda pubblica**: preferisce **play** se il video è `ready`; genera residuale solo se sei il lister. Pubblico: `POST /api/cloud/videos/kenburns/property/{pid}` (solo annunci live).
- **Qualità (04-Nov)**: 1080p, CRF 18, Lanczos, preferisce foto ≥720px lato; download foto da Object Storage (`/api/media/...`) senza loopback HTTP.
- **Runtime**: `ffmpeg` installato in `Dockerfile.railway` (senza → `FileNotFoundError` / job `failed`).
- Non cannibalizza Kling: agenti = Kling a crediti in CRM; B2C = Ken Burns free.

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

**Versione capitolo**: v1.2 (04-Nov-2026 · D-140 video tour in Vendi + qualità 1080p).

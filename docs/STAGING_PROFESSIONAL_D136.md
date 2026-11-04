# Virtual Staging professionale (D-136)

## Attivazione

Default sicuro: `OMNIA_STAGING_PIPELINE=nano` (D-128 oneshot).

Per abilitare la pipeline geometrica **solo sul gestionale B2B** (ImmoWeb / crediti agenzia):

```bash
OMNIA_STAGING_PIPELINE=professional
# opzionale: pass creativo Nano Banana dopo LoRA, comunque gated
# OMNIA_STAGING_NANO_CREATIVE=true
```

ImmobilCloud B2C (anteprima / Stripe €1,49) resta su **nano** anche con il flag sopra.
Per forzare professional anche sul B2C (sconsigliato):

```bash
OMNIA_STAGING_PIPELINE_FORCE_B2C=true
```

Riavviare / redeploy API dopo il cambio env.

## Rollback

1. Impostare `OMNIA_STAGING_PIPELINE=nano` (o rimuovere la variabile).
2. Redeploy / restart API.
3. I job già creati restano leggibili; Stripe e promozione listing non cambiano contratto.

Non serve rollback codice: il path Nano Banana e legacy restano nel repo.

## Cosa cambia con `professional`

| Fase | Comportamento |
|------|----------------|
| 0 | Analisi stanza Gemini (anche su path nano) — no default `bedroom` |
| 1 | Depth map fal `imageutils/depth` + maschere esistenti Florence/EVF/SAM |
| 2 | Selective erase mascherato |
| 3 | Empty QA hard |
| 4 | Furnish LoRA / Flux inpaint + regole stile per room |
| 5 | Hard gate ACCEPT/RETRY/REJECT/MANUAL_REVIEW |
| 6 | Solo varianti ACCEPT in `variants` (reject in `variants_all`) |

Promozione / auto-save / fulfill Stripe: bloccati se nessuna variante `publishable`.

## Costi stimati (USD, ordine di grandezza)

| Path | Per run accettato (1 stile) | Note |
|------|----------------------------|------|
| nano oneshot + critic | ~0.08–0.12 | +0.08 se 1 retry |
| nano multi 4 stili | ~0.35–0.50 | hard cap agent |
| professional (erase+LoRA+gate) | ~0.15–0.45 | dipende erase engine + retry |
| professional + nano creative | +0.08 | solo se flag e gate ACCEPT |

Costo per **immagine accettata** > costo per generazione: i reject non vanno in listing.

## Limiti noti

- Depth/edge non sono ancora ControlNet hard-lock su tutti i generatori fal usati (Nano Banana edit non espone ControlNet).
- Il gate architettonico dipende da Gemini vision: se `unverifiable` → MANUAL_REVIEW, non auto-ACCEPT.
- Segmentazione aperture pixel-perfect non è garantita senza modelli dedicati; si riusano Florence/EVF/SAM già in produzione.
- A/B metriche (accept rate, costo, latenza) da raccogliere in shadow prima del default `professional`.

## Test

```bash
cd backend && python -m pytest tests/test_staging_professional_d136.py tests/test_staging_agent.py -q
```

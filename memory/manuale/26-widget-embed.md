# Capitolo 26 · Widget embeddabili

> Snippet per siti esterni (Doppio Binario Track B). **D-051**: richiedono API key `omk_live_…` e crediti Track B dove previsto.

## 26.1 · Loader
```html
<script src="https://TUO_DOMINIO/api/widgets/v1/loader.js"
  data-key="omk_live_..."
  data-widget="valuator"
  data-primary="#0b1e3f"
  data-lang="it"></script>
```

## 26.2 · Widget disponibili
`valuator` · `mortgages` · `staging` · `legal` · `domain-check`

Pagine HTML: `GET /api/widgets/v1/{widget}.html`.

## 26.3 · Showcase interno
- Route FE `/widgets` (WidgetsShowcasePage) per demo.

## 26.4 · Limitazioni v1
- Pricing Track B €0,03/cred (Cap. 20), wallet separato.
- No auto-ricarica; no rate-limit UI avanzata.
- Branding colori via `data-primary`.

## 26.5 · Collegamenti
Cap. 20 API Keys · Cap. 11 Mutui · Cap. 21 Valutatore.

**Versione capitolo**: v1.0 (2026-09-14 · Cursor M3).

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

## 26.6 · Box ricerca MLS sul sito già proprio (D-170)
Se l’agenzia **tiene il proprio sito** e aderisce alla rete, non si clona niente: si sostituisce solo il riquadro MLS.

1. Avvio → «Tengo il sito, sostituisco solo il box MLS» → adesione MLS.
2. Copia lo snippet da Avvio / Il mio sito / MLS (`GET /api/mls-box/embed-kit/{slug}`).
3. Incollalo al posto del vecchio box in home. Iframe: `/api/mls-box/search/{slug}.html`.

**Versione capitolo**: v1.1 (2026-11-12 · D-170).

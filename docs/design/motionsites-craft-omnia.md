# MotionSites craft → template siti agenzia OMNIA

Fonte: Motionsites-AI/claude-skill (`references/craft.md` + examples agency/luxury).  
Adattato allo stack **SSR** `theme_render.py` (non React/Framer runtime).

## Cosa prendere

1. **Un’idea nel first viewport** — brand + H1 + una sub + CTA + un media plane. Niente card/stat strip in hero.
2. **Media porta il design, UI quiet** — nav corta, un materiale (glass / solid / editorial rule), accent su ≤3 tipi di pezzo.
3. **Palette stretta** — 1 bg, 1 fg, 1–2 grey, ≤1 accent. Vietati purple-glow / blob / multi-shadow.
4. **Type scale** — H1 ~5–6× body; tracking stretto sul display; max 2 famiglie.
5. **Motion misurato** — entrance 0.6–1.1s, stagger 0.1–0.2s; CSS only sul sito agenzia (niente Framer in produzione template).
6. **Screenshot → fix** — ogni tema nuovo: desktop + mobile home/lista/scheda, MLS on e off.

## Cosa non portare

- Shader stacks / Three.js / scroll 900vh come default prodotto (troppo fragili in SSR white-label).
- Video hero obbligatorio su tutti i temi (ok su `cinematic`/`luxury` se CDN stabile).
- Copia letterale degli esempi MotionSites (brand, layout, assets).

## Mapping esempi → temi OMNIA

| Tema | Esempi da studiare (barra) |
|---|---|
| minimal | stillmind, equilibrium |
| classic | neo-museum |
| bold | bold-studio, modern-agency |
| luxury | velorah-hero, aethera-hero |
| atelier (planned) | modern-agency, creative-studio |
| cinematic (planned) | velorah-hero, portal-hero |
| editorial (planned) | stillmind, neo-museum |
| mediterranean (planned) | mostar-guide, immersive-ocean |

## Matrice QA

Ogni tema: preview con `mls_enabled=true` e `false` — pezzi MLS solo se on.

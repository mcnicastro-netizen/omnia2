# Template pack OMNIA — neo agenzia + restyling (D-150)

## Modello

Un solo pack template serve **due ingressi commerciali**:

| Ingresso | Contesto | Path |
|---|---|---|
| Neo agenzia / neo agente | Nessun sito (o lo vuole da zero) | D-018 → Brand Studio gallery |
| Restyling (caso 3) | Ha già un sito ma vuole look OMNIA nuovo | Stessa gallery, dopo/accanto a clone |

**Non** due cataloghi. Il look scelto è lo stesso pezzo di codice (`theme_catalog` + `theme_render`).

## Listino (D-151)

| Path | Prezzo |
|---|:-:|
| Pro / Agency | **incluso** (gallery 8) |
| Starter neo — `minimal` \| `classic` | **€99** one-shot (1 tema) |
| Starter neo — altri 6 | **€199** one-shot (1 tema) |
| **Restyling** (caso 3) | **€199** one-shot (1 tema, qualunque) |

Ordine build: prima fascia €99 (polish Minimal + Classic + slot MLS), poi i 6 da €199.

## Matrice MLS (obbligatoria)

Ogni template, live o planned, deve passare QA su entrambe le varianti:

| | `mls_enabled=true` (caso 1) | `mls_enabled=false` (caso 2) |
|---|---|---|
| Home | Box ricerca rete + sezione «Immobili dalla Rete MLS Partner» | Solo search portafoglio agenzia · zero pezzi MLS |
| Lista | Sidebar «Cerca il tuo immobile» (rete se MLS on) | Stesso UI search, senza chip/rete MLS |
| Embed `/api/mls-box/*` | OK | `mls_not_enabled` |

Join/leave MLS non cambia template_id: cambia solo i pezzi condizionali in `theme_render`.

## Live (8) — gallery completa D-151

| id | Fascia | Segmento | Craft MotionSites (ispirazione, non copia) |
|---|---|---|---|
| `minimal` | €99 | boutique / neo | stillmind, equilibrium |
| `classic` | €99 | mainstream | neo-museum |
| `bold` | €199 | volume / moderno | bold-studio, modern-agency |
| `luxury` | €199 | prestigio | velorah-hero, aethera-hero |
| `atelier` | €199 | boutique urbane | modern-agency, creative-studio |
| `cinematic` | €199 | prestigio video | velorah-hero, portal-hero |
| `editorial` | €199 | magazine / mono-quartiere | stillmind, neo-museum |
| `mediterranean` | €199 | Sud / second home | mostar-guide, immersive-ocean |

Default: `minimal`. `THEME_ROADMAP` vuoto (tetto D-019: 5–10; nuovi slot solo se Founder chiede).

## MotionSites — come lo usiamo

Repo: [Motionsites-AI/claude-skill](https://github.com/Motionsites-AI/claude-skill) · skill `motionsites-web-builder`.

- **Sì**: craft (composition, type scale, palette restraint, motion timing), spec precision, screenshot-and-fix loop, esempi agency/luxury come **barra qualità**.
- **No**: stack React+Framer Motionsites come runtime del sito agenzia (OMNIA resta SSR `theme_render` + headless API).
- **No**: copiare brand/copy/layout wholesale degli esempi (licenza sample + originalità OMNIA).
- **Adattamento Cursor**: builders.md → «edit files in existing stack»; qui lo stack è Python HTML templates, non Vite SPA.

Craft adattato: `docs/design/motionsites-craft-omnia.md`.

## Definition of Done per un nuovo tema

1. Entry in `THEME_CATALOG` con `status=live`, `mls_variants=["on","off"]`.
2. CSS/layout in `theme_render` per home + lista + scheda.
3. Test: render MLS on e off (nessun `agency-home-mls-box` se off).
4. Preview Brand Studio + `/api/p/{slug}/` smoke.
5. Nessun spill React SPA / dipendenze MotionSites in runtime.

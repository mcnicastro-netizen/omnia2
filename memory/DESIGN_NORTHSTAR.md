# 🎨 DESIGN NORTH STAR — OMNIA Real Estate Ecosystem

> **Riferimento visivo vincolante per tutto il progetto OMNIA.**
> Immagine target fornita dal Founder: `ChatGPT Image 15 apr 2026, 18_03_21.png`
> URL asset: https://customer-assets.emergentagent.com/job_audit-tool-12/artifacts/s8dap8o1_ChatGPT%20Image%2015%20apr%202026%2C%2018_03_21.png
> Data acquisizione: M1.S4 (Aprile 2026)
> Stato: ✅ CONFERMATO dal Founder

---

## 🎯 FILOSOFIA

OMNIA NON è un sito immobiliare generico. È un **ecosistema professionale verticale** composto da 3 pilastri integrati. Il design deve trasmettere:

- **Professionalità** (target B2B agenzie + Founder = agente immobiliare)
- **Sofisticazione** (premium, non low-cost)
- **Integrazione** (3 prodotti che dialogano, non silos)
- **Innovazione discreta** (AI nativa, ma non gimmick)
- **Italianità competente** (anti-idealista, anti-AI-slop, no purple gradients)

---

## 🎨 PALETTE COLORI (VINCOLANTE)

### Colori primari
```css
--omnia-navy:        #0B1E3F   /* Blu navy — brand principale, headings, CTA primarie */
--omnia-navy-deep:   #061229   /* Blu profondo — sezioni dark mode, hero override */
--omnia-cream:       #FAF7F2   /* Crema/avorio — background chiaro alternativo (NON bianco puro) */
--omnia-white:       #FFFFFF   /* Bianco — background landing pulito */
--omnia-ink:         #0E1419   /* Nero inchiostro — testo body su chiaro */
--omnia-stone-600:   #5C6470   /* Grigio caldo — testo secondario */
--omnia-stone-200:   #E5E2DC   /* Grigio caldo chiaro — bordi, divider */
```

### Colori accento per app (ognuno con la sua identità)
```css
/* IMMOBILCLOUD (B2C) — Navy profondo + accenti cielo */
--cloud-primary:   #0B1E3F   /* Navy */
--cloud-accent:    #4A90D9   /* Azzurro polvere — link, hover */

/* IMMOWEB (B2B CRM) — Teal/verde professionale */
--web-primary:     #1F6B5C   /* Verde teal scuro */
--web-accent:      #2C9783   /* Teal medio — bottoni, badge attivo */

/* OMNIA ACADEMY (LMS) — Viola profondo "graduate" */
--academy-primary: #4B3D7A   /* Viola profondo — NON purple gradient slop */
--academy-accent:  #7A6BA8   /* Viola tenue — illustrazioni */

/* Accenti trasversali */
--gold-highlight:  #C8A653   /* Oro tenue — premium badge, certificazioni, stelle */
--success:         #2C9783   /* Conferma — riuso teal */
--warning:         #E8A33B   /* Attenzione — caldo, non aggressivo */
--danger:          #B83A3A   /* Errore — rosso terra cotta, NON rosso fluo */
```

### ❌ Da EVITARE (AI-slop blacklist)
- Purple/violet gradient su bianco
- Cyan elettrico, magenta, neon
- Bianco puro #FFF in sezioni hero (usa crema #FAF7F2 o navy)
- Box shadow drop-shadow vaghi blu (`shadow-blue-500/50`)
- Gradient da angolo a angolo (`from-purple-500 via-pink-500 to-orange-500`)

---

## ✍️ TIPOGRAFIA

### Stack font (già caricato in `index.html`)
```css
font-family-display: 'Fraunces', Georgia, serif;        /* Serif moderno — H1, hero, eyebrow */
font-family-body:    'Inter', system-ui, sans-serif;    /* Sans clean — body, UI, bottoni */
font-family-mono:    'JetBrains Mono', monospace;       /* Mono — codice, ID, prezzi tecnici */
```

### Gerarchia
| Elemento | Font | Size | Weight | Tracking |
|---|---|---|---|---|
| Hero H1 | Fraunces | text-5xl → text-7xl | 500-600 | -0.02em |
| H2 sezione | Fraunces | text-3xl → text-4xl | 500 | -0.01em |
| H3 card | Inter | text-xl → text-2xl | 600 | normal |
| Eyebrow/Uppercase | Inter | text-xs | 600 | 0.15em uppercase |
| Body | Inter | text-base | 400 | normal |
| Caption/Meta | Inter | text-sm | 500 | normal |
| Button | Inter | text-sm | 600 | 0.05em uppercase |

### Regola: ZERO Roboto, ZERO Arial, ZERO Open Sans. Solo Fraunces + Inter.

---

## 📐 LAYOUT & SPAZIATURA

### Principi
- **Asimmetria intenzionale**: NO layout centrati simmetrici da landing-template-generico
- **Spaziatura generosa**: ~2-3x il default Tailwind. Usa `py-24 md:py-32` per sezioni.
- **Griglie ecosistema-like**: card collegate visualmente (linee tratteggiate, bordi sottili) — riferimento immagine target.
- **Massimo 3 livelli di profondità** (background → card → contenuto). No card-in-card-in-card.

### Container widths
```
max-w-7xl   — Layout standard pagina
max-w-5xl   — Contenuto editoriale, hero text
max-w-3xl   — Form, modali, articoli
```

---

## 🧩 COMPONENTI CHIAVE

### Card "Pillar" (per Landing + Dashboard)
- Background `--omnia-cream` su navy / `--omnia-white` su crema
- Bordo `1px solid --omnia-stone-200`
- Border-radius: `rounded-2xl` (NO sharp, NO super-rounded)
- Padding: `p-8 md:p-10`
- Hover: lift sottile (`translate-y-[-2px]`) + bordo che cambia ad accent color
- NO drop shadow pesante. Usa `shadow-sm` o nessuna.

### Bottoni
- **Primary**: bg navy, testo crema, uppercase tracking-wider, `px-8 py-4 rounded-full`
- **Secondary**: bordo navy 1px, testo navy, bg trasparente, stesso padding
- **Ghost**: testo navy + underline su hover
- Animation: `transition-colors duration-200` (mai `transition-all`)

### Icone
- **NO emoji** (🏠💡🤖). Usa `lucide-react` (già installato) o FontAwesome CDN.
- Stroke-width: 1.5 (più elegante del default 2)
- Color: ereditato dal contesto (`text-current`)

### Linee di connessione (ecosystem diagram)
Dall'immagine target, le 3 app sono collegate da linee tratteggiate sottili che indicano integrazione. Replicabile con SVG inline o `border-dashed` su pseudo-elementi.

---

## 🌅 PATTERN DI SEZIONE

### Hero Landing
- Background `--omnia-cream` o navy profondo (alternativa dark mode)
- Eyebrow piccolo uppercase + H1 grande Fraunces + sottotitolo Inter
- 1 CTA primaria + 1 link ghost
- Visualizzazione ecosistema a destra (3 pillars connessi)

### Sezione "I 3 Pilastri"
- Background contrasto (se hero crema → questa navy con cream text)
- 3 card affiancate desktop, stacked mobile
- Ogni card ha il SUO accent color (cloud=azzurro, web=teal, academy=viola)
- Bottone "Scopri" che porta a `/{lang}/cloud`, `/{lang}/app`, `/{lang}/learn`

### Footer
- Background `--omnia-navy-deep`
- 4 colonne: Brand + Tagline | ImmobilCloud | ImmoWeb | Academy
- Lingua switcher in basso a sinistra
- Copyright in basso a destra
- Stile sobrio, no social icon piazzati a caso

---

## 🎬 MICRO-INTERAZIONI

### Animation library
- React: usa **Framer Motion** se serve coreografia (non ancora installato, installa al bisogno)
- CSS-only: preferito per hover/transition semplici

### Pattern approvati
- **Stagger reveal** sezioni al primo scroll (delay 80ms tra card)
- **Number counter** su statistiche (es: "27.000+ zone OMI")
- **Hover lift** su card (translate-y -2px, transition 200ms)
- **Sottolineatura animata** su link inline (`underline-offset-4 hover:underline`)

### Da evitare
- Parallax aggressivi su tutto lo scroll
- Confetti/particle systems
- Cursor follower decorativi
- Auto-play video pesanti

---

## 📱 MOBILE-FIRST

Il Founder ha confermato che lo screenshot tool non rende mobile viewport correttamente — testare sempre da browser reale.

### Breakpoint logica
```
< 640px   — Mobile, hamburger menu attivo, stack tutto
640-1024  — Tablet, layout 2 colonne dove sensato
> 1024    — Desktop, layout completo 3 colonne
```

### Hamburger menu già presente in `MobileNav.jsx` — riutilizzare.

---

## 🌍 I18N AWARENESS

Componente `<Brand>` già esistente protegge i nomi (`OMNIA`, `ImmobilCloud`, `ImmoWeb`, `Omnia Academy`) dall'auto-translate del browser. **Usarlo sempre** quando si menzionano i brand nel JSX.

---

## ✅ CHECKLIST PRIMA DI MERGEARE UNA UI

- [ ] Palette: solo i colori in DESIGN_NORTHSTAR (no purple gradient generici)
- [ ] Font: Fraunces (display) + Inter (body), nient'altro
- [ ] No emoji come icone (lucide-react o FontAwesome)
- [ ] `data-testid` su ogni elemento interattivo (vedi regole sistema)
- [ ] `<Brand>` su nomi prodotto
- [ ] Mobile testato manualmente (non solo screenshot tool)
- [ ] Spaziatura generosa (no claustrofobia)
- [ ] Hover states definiti
- [ ] Loading states presenti per async actions

---

## 🔄 EVOLUZIONE

Questo documento è **vincolante** ma può essere esteso quando si aggiungono nuovi pattern. Modifiche sostanziali (palette, tipografia) richiedono approvazione esplicita del Founder.

---

*Fine north star. Riferirsi a questo file in ogni sessione di UI/design.*

import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

/**
 * OMNIA Brand Lab — internal repository for creative reference material.
 *
 * NOT public. Only super_admin sees the sidebar entry (see AppLayout.jsx).
 * Route: /it/app/brand-lab (any lang prefix works via <LangGate>).
 *
 * Purpose: central place where the Founder + design team collect:
 *   - The "North Star" reference image (OMNIA Real Estate Lab)
 *   - Palette + typography rules
 *   - Aesthetic commandments (do / don't)
 *   - Copy-pasteable AI prompts (video 15sec, ecc.)
 *   - Reference films / campaigns
 *
 * Design guideline aligned: navy background, emerald + gold accents,
 * Fraunces headings, editorial spacing.
 */

const NORTH_STAR_IMAGE = "https://customer-assets-eiarnc6j.emergentagent.net/job_audit-tool-12/artifacts/kivvln54_Gemini_Generated_Image_us1pucus1pucus1p.png";

const PALETTE = [
  { name: "Deep Navy",        hex: "#0B1E3F", use: "Sfondi principali, tipografia primary" },
  { name: "Emerald Signature", hex: "#1F6B5C", use: "Colore firma, fashion, UI accents, ologrammi" },
  { name: "Warm Gold",        hex: "#C8A653", use: "Highlights, luci, tipografia hero" },
  { name: "Off-White Marble", hex: "#F5F1E8", use: "Sfondi chiari, testi su navy" },
  { name: "Cyan-Teal Hologram", hex: "#4EE1D3", use: "Solo per glow ologrammi / dati live" },
];

const COMMANDMENTS_DO = [
  "Architettura parametrica (Zaha Hadid) + barocco italiano restaurato",
  "Biofilia mediterranea — palma nana, cactus, olivo giovane in ceramica bianca",
  "Luce dorata calda volumetrica (mai neon freddo)",
  "Materiali nobili — marmo lucido, vetro curvo, ottone, titanio spazzolato",
  "Silenzio compositivo — spazio negativo, quiete visiva, no clutter",
];

const COMMANDMENTS_DONT = [
  "Tetti rossi in terracotta / Toscana / Chianti",
  "Cypress rows, Bialetti, caffé napoletano cliché",
  "Handshake, diverse-team-around-laptop, corporate stock",
  "Gradient viola / violet (AI-slop signature)",
  "Neon Tron / cyberpunk freddo — solo Blade Runner 2049 warmth",
  "Skyline cinese, palme Dubai, generic-future",
  "Persone anziane con raccoglitori cartacei (contro D-035 No Paper)",
];

const REFERENCE_FILMS = [
  { title: "Neom 'The Line' launch film", year: "2022", tag: "Parametric + desert light" },
  { title: "Apple Vision Pro 'Encounter Dreams'", year: "2024", tag: "UI floating in space" },
  { title: "Blade Runner 2049 · Vegas sequence", year: "2017", tag: "Warmth dorata post-apoc" },
  { title: "Louis Vuitton 'Horizons Never End'", year: "2023", tag: "Italian luxury slowmo" },
  { title: "Zaha Hadid Foundation films", year: "—", tag: "Parametric mastery" },
  { title: "Loro Piana campaigns", year: "—", tag: "Italian editorial elegance" },
];

const NEGATIVE_PROMPT_CANONICAL = `NO red terracotta rooftops, NO Tuscan hills, NO Bialetti moka, NO cypress trees, NO Venetian blinds, NO stock office footage, NO handshakes, NO diverse-team-around-laptop tropes, NO gray suits and pastel shirts, NO purple/violet gradients, NO Tron neon, NO cold cyberpunk, NO Chinese city skyline, NO Dubai palm islands, NO elderly agents with paper binders, NO cheesy uplift music. Mediterranean-FUTURE not Generic-Future.`;

const VIDEO_PROMPT_15SEC = `Cinematic 15-second futuristic ad film for OMNIA Real Estate Ecosystem, a next-generation Italian proptech platform based in Catania, Sicily. Aesthetic reference: Zaha Hadid parametric architecture meets Blade Runner 2049 warmth meets Apple Vision Pro product film. Absolutely NO red rooftops, NO terracotta villages, NO Tuscany clichés, NO cypress trees, NO Bialetti coffee pots, NO elderly agents with binders. This is Italy in 2035, not 1995.

COLOR PALETTE (strict):
- Deep navy #0B1E3F backgrounds
- Signature emerald green #1F6B5C (fashion, holograms, UI)
- Warm gold #C8A653 accents (light-glow only)
- Off-white marble #F5F1E8
- Cyan-teal hologram glow #4EE1D3

SHOT 1 (0.0-3.0s) — ARRIVAL
Aerial descent toward a geodesic glass dome in a Catania plaza at golden hour. Baroque palazzos in background. Autonomous white shuttle-pod arrives silently. LED text "OMNIA · REAL ESTATE LAB". Palm and cactus in white ceramic planters. 24mm anamorphic.

SHOT 2 (3.0-6.5s) — WOMAN OF THE FUTURE
Slow motion: confident Italian woman 30s, dark hair, tailored EMERALD GREEN long coat, sleek boots, carries slim titanium tablet. Walks out of glass arched entrance. Behind her holograms show "RISK ANALYSIS LIVE · ASSET VALUE €1.2M" in Fraunces italic gold. Warm reflected light. Focused, not smiling for camera.

SHOT 3 (6.5-9.5s) — THE ECOSYSTEM VISUALIZED
Three floating holographic pillars around a scale-model Sicilian city built from light: "CRM · PORTALE · ACADEMY" in gold serif. Golden data streams connect them. Living plants on geodesic ribs. Text: "Un ecosistema. Non un gestionale."

SHOT 4 (9.5-12.5s) — MULTI-DEVICE
Slim floating console: iPhone-like slab and MacBook-like laptop levitating on transparent stands. Both show OMNIA UI synced (navy + emerald + gold Fraunces). One tap triggers synchronized emerald wave animation. VO Italian female calm: "OMNIA. Ecosistema immobiliare integrato."

SHOT 5 (12.5-15.0s) — LOGO CLOSE
OMNIA wordmark in gold Fraunces serif on deep navy. Below small caps: "CATANIA · MILANO · MADRID". Autonomous pod passes slowly behind logo. URL bottom in cyan-teal glow: "omniarealestateecosystem.it". Silence last 1.5s.

TECHNICAL: 24fps · anamorphic lens flares gold-emerald only · Kodak Vision3 250D grain 8% · 9:16 vertical.

STYLE: Neom 'The Line' + Apple Vision Pro + Blade Runner 2049 Vegas warmth + Louis Vuitton + Zaha Hadid.

NEGATIVE: NO red rooftops, NO Bialetti, NO cypress, NO handshakes, NO purple gradients, NO Tron neon, NO Chinese skyline. Mediterranean-FUTURE not Generic-Future.`;

export default function BrandLabPage() {
  const { i18n } = useTranslation();
  const lang = i18n.language?.slice(0, 2) || "it";
  const [copied, setCopied] = useState(null);

  const copy = async (id, text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(id);
      setTimeout(() => setCopied(null), 2000);
    } catch { /* ignore */ }
  };

  return (
    <div className="min-h-screen bg-stone-50 text-stone-900" data-testid="brand-lab-page">
      {/* ======= HERO ======= */}
      <section className="relative">
        <div className="relative h-[500px] overflow-hidden bg-slate-900">
          <img
            src={NORTH_STAR_IMAGE}
            alt="OMNIA Real Estate Lab — North Star visivo"
            className="w-full h-full object-cover"
            data-testid="brand-lab-north-star-image"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/20 to-transparent" />
          <div className="absolute bottom-0 left-0 right-0 p-10 max-w-6xl mx-auto text-white">
            <p className="text-[10px] uppercase tracking-[0.4em] text-amber-300 mb-3">Brand Lab · Interno</p>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl leading-[1.05]" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              Mediterranean Future 2035
            </h1>
            <p className="text-base sm:text-lg text-slate-200 mt-4 max-w-2xl leading-relaxed">
              Il North Star visivo di OMNIA. Ogni immagine, video, mockup e mood deve rispondere a questa direzione: Italia radicata, catapultata nel futuro. Nessun cliché toscano, nessun corporate stock.
            </p>
          </div>
        </div>
      </section>

      <div className="max-w-6xl mx-auto px-6 py-12 space-y-16">

        {/* ======= PALETTE ======= */}
        <section data-testid="brand-lab-palette">
          <SectionHeader eyebrow="01" title="Palette ufficiale" subtitle="Hex code strict — mai improvvisare colori nuovi senza approvazione." />
          <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {PALETTE.map((c) => (
              <button key={c.hex}
                onClick={() => copy(c.hex, c.hex)}
                className="group text-left border border-stone-200 rounded-lg overflow-hidden hover:shadow-md transition"
                data-testid={`palette-${c.hex.replace("#", "")}`}
              >
                <div className="h-24 flex items-end p-3" style={{ backgroundColor: c.hex }}>
                  <span className={`text-[10px] uppercase tracking-widest ${["#F5F1E8", "#C8A653", "#4EE1D3"].includes(c.hex) ? "text-stone-900" : "text-white"}`}>
                    {c.hex === copied ? "✓ copiato" : c.hex}
                  </span>
                </div>
                <div className="p-3">
                  <p className="font-medium text-sm">{c.name}</p>
                  <p className="text-xs text-stone-500 mt-1 leading-snug">{c.use}</p>
                </div>
              </button>
            ))}
          </div>
        </section>

        {/* ======= COMMANDMENTS ======= */}
        <section data-testid="brand-lab-commandments">
          <SectionHeader eyebrow="02" title="I 5 comandamenti" subtitle="Cosa fare sempre, cosa evitare come la peste." />
          <div className="grid md:grid-cols-2 gap-6">
            <div className="border-l-2 border-emerald-600 pl-5" data-testid="brand-lab-do">
              <p className="text-[10px] uppercase tracking-widest text-emerald-700 mb-3">Sempre</p>
              <ul className="space-y-3">
                {COMMANDMENTS_DO.map((c, i) => (
                  <li key={i} className="text-sm text-stone-700 leading-relaxed flex gap-3">
                    <span className="text-emerald-700 font-medium">✓</span>
                    <span>{c}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="border-l-2 border-red-500 pl-5" data-testid="brand-lab-dont">
              <p className="text-[10px] uppercase tracking-widest text-red-600 mb-3">Mai</p>
              <ul className="space-y-3">
                {COMMANDMENTS_DONT.map((c, i) => (
                  <li key={i} className="text-sm text-stone-700 leading-relaxed flex gap-3">
                    <span className="text-red-500 font-medium">✕</span>
                    <span>{c}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* ======= VIDEO PROMPT ======= */}
        <section data-testid="brand-lab-video-prompt">
          <SectionHeader
            eyebrow="03"
            title="Prompt Video 15 secondi"
            subtitle="Copia-incolla in Sora 2 / Veo 3 / Pippit. Testato: produce estetica Mediterranean Future 2035."
          />
          <div className="bg-slate-900 text-slate-100 rounded-xl overflow-hidden">
            <div className="flex justify-between items-center px-5 py-3 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <span className="text-[10px] uppercase tracking-widest text-amber-400">Prompt v2</span>
                <span className="text-xs text-slate-400">omnia_2035_15sec.txt</span>
              </div>
              <button
                onClick={() => copy("video", VIDEO_PROMPT_15SEC)}
                data-testid="brand-lab-copy-video-prompt"
                className="text-xs uppercase tracking-widest bg-amber-400 text-slate-900 px-4 py-2 rounded hover:bg-amber-300"
              >
                {copied === "video" ? "✓ Copiato" : "Copia prompt"}
              </button>
            </div>
            <pre className="p-5 text-xs leading-relaxed whitespace-pre-wrap font-mono max-h-96 overflow-y-auto text-slate-200">
              {VIDEO_PROMPT_15SEC}
            </pre>
          </div>
          <p className="text-xs text-stone-500 mt-3">
            Prompt salvato anche in <code className="bg-stone-100 px-2 py-0.5 rounded">/app/memory/creatives/omnia_2035_video_prompt.md</code> con varianti Pippit (3 clip da 5 sec) e brief musica/voice-over.
          </p>
        </section>

        {/* ======= NEGATIVE PROMPT ======= */}
        <section data-testid="brand-lab-negative-prompt">
          <SectionHeader eyebrow="04" title="Negative prompt canonico" subtitle="Da appendere a QUALSIASI prompt AI per foto o video. Impedisce il ritorno del cliché." />
          <div className="bg-red-50 border border-red-200 rounded-xl p-5">
            <div className="flex justify-between items-start mb-3">
              <p className="text-[10px] uppercase tracking-widest text-red-700">Copia-incolla</p>
              <button
                onClick={() => copy("neg", NEGATIVE_PROMPT_CANONICAL)}
                data-testid="brand-lab-copy-negative"
                className="text-xs uppercase tracking-widest border border-red-300 text-red-700 px-3 py-1 rounded hover:bg-red-100"
              >
                {copied === "neg" ? "✓ Copiato" : "Copia"}
              </button>
            </div>
            <p className="text-sm text-red-900 leading-relaxed font-mono">
              {NEGATIVE_PROMPT_CANONICAL}
            </p>
          </div>
        </section>

        {/* ======= REFERENCE FILMS ======= */}
        <section data-testid="brand-lab-references">
          <SectionHeader eyebrow="05" title="Reference films & campagne" subtitle="Da citare nei prompt AI per calibrare l'estetica al primo colpo." />
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
            {REFERENCE_FILMS.map((f, i) => (
              <div key={i} className="border border-stone-200 rounded-lg p-4 bg-white">
                <p className="text-[10px] uppercase tracking-widest text-emerald-700 mb-1">{f.year}</p>
                <p className="font-medium text-sm mb-1" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>{f.title}</p>
                <p className="text-xs text-stone-500">{f.tag}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ======= NEXT ASSETS ======= */}
        <section data-testid="brand-lab-backlog">
          <SectionHeader eyebrow="06" title="Prossimi asset da produrre" subtitle="Backlog creativo. Ogni asset seguirà i comandamenti sopra." />
          <div className="grid md:grid-cols-2 gap-3">
            {[
              "Foto agent in azione — donna emerald + tablet, ambiente Lab",
              "Foto interior Lab — 3 ologrammi CRM/PORTALE/ACADEMY",
              "Foto autonomous pod — dettaglio primo piano",
              "Video 15sec verticale — social/reels/tiktok",
              "Video 15sec orizzontale — landing/youtube/linkedin",
              "Loop animato splash — 3sec webapp loading",
              "Set icone brand — CRM · Portale · Academy · Publishing · Widget in stile ologramma",
              "Font pairing samples — Fraunces + Inter per marketing",
            ].map((task, i) => (
              <div key={i} className="flex items-start gap-3 text-sm border border-stone-200 rounded-lg p-3 bg-white">
                <input type="checkbox" disabled className="mt-1" />
                <span className="text-stone-700">{task}</span>
              </div>
            ))}
          </div>
        </section>

        <div className="border-t border-stone-200 pt-6 text-center text-xs text-stone-500">
          Pagina interna Brand Lab · super_admin only · aggiornata ad ogni nuovo asset
          <br />
          File di riferimento: <code className="text-stone-600">/app/memory/creatives/brand_lab_reference.md</code>
          {" · "}
          <Link to={`/${lang}/app`} className="text-emerald-700 hover:underline">← Torna al CRM</Link>
        </div>
      </div>
    </div>
  );
}

function SectionHeader({ eyebrow, title, subtitle }) {
  return (
    <div className="mb-6">
      <p className="text-[10px] uppercase tracking-[0.3em] text-emerald-700 mb-2">{eyebrow}</p>
      <h2 className="text-2xl sm:text-3xl mb-2" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>{title}</h2>
      {subtitle && <p className="text-sm text-stone-600 max-w-2xl">{subtitle}</p>}
    </div>
  );
}

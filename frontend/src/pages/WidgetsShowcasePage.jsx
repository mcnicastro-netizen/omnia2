import React, { useMemo, useState } from "react";
import { useAuth } from "../shared/lib/auth";
import Brand from "../shared/components/Brand";

/**
 * WidgetsShowcasePage — public gallery of Track B embeddable widgets.
 * Route: /:lang/widgets (no auth required)
 * M2.5.3 (D-041/D-049)
 */
const BACKEND = process.env.REACT_APP_BACKEND_URL || window.location.origin;
const DEMO_KEY_HINT = "omk_live_yourKeyHere...";
const curLang = () => {
  const seg = window.location.pathname.split("/")[1];
  return ["it", "en", "es"].includes(seg) ? seg : "it";
};

const WIDGETS = [
  {
    id: "valuator",
    name: "Valutatore immobili",
    tagline: "Stima istantanea UNI 10750",
    cost: "5 crediti / stima · €0,15",
    color: "#0b1e3f",
    description:
      "Form snello per far calcolare al visitatore un range €min-max sul suo immobile. Include lead capture opzionale che finisce direttamente nel tuo CRM OMNIA.",
  },
  {
    id: "mortgages",
    name: "Comparatore Mutui",
    tagline: "Top 3 offerte in tempo reale",
    cost: "1 credito / confronto · €0,03",
    color: "#0b1e3f",
    description:
      "Il visitatore inserisce prezzo, anticipo, durata e vede le 3 migliori offerte con TAEG, rata mensile e costo totale. Lead capture con contesto completo del confronto.",
  },
];

export default function WidgetsShowcasePage() {
  const { user } = useAuth();
  const [selected, setSelected] = useState("valuator");
  const [previewKey, setPreviewKey] = useState("");
  const w = WIDGETS.find((x) => x.id === selected);

  const snippet = useMemo(() => {
    const key = previewKey || DEMO_KEY_HINT;
    return `<script src="${BACKEND}/api/widgets/v1/loader.js"
  data-key="${key}"
  data-widget="${selected}"
  data-primary="${w.color}"
  data-lang="it"></script>`;
  }, [previewKey, selected, w.color]);

  const previewSrc = useMemo(() => {
    if (!previewKey) return null;
    const params = new URLSearchParams({
      key: previewKey,
      primary: w.color,
      lang: "it",
    });
    return `${BACKEND}/api/widgets/v1/${selected}.html?${params.toString()}`;
  }, [previewKey, selected, w.color]);

  const copy = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (_) {
      // clipboard not available
    }
  };

  return (
    <div
      data-testid="widgets-showcase-page"
      className="min-h-screen bg-stone-50 text-stone-900"
    >
      <header className="border-b border-stone-200 bg-white">
        <div className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between">
          <div>
            <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500">
              <Brand>OMNIA · Track B</Brand>
            </p>
            <h1
              className="text-2xl md:text-3xl mt-1"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              Widget Embeddabili
            </h1>
          </div>
          <a
            href={user ? `/${curLang()}/app/api-keys` : `/${curLang()}/login`}
            data-testid="widgets-get-key-cta"
            className="text-xs uppercase tracking-widest bg-stone-900 text-stone-50 px-4 py-2 rounded hover:bg-stone-700"
          >
            {user ? "Le mie chiavi API →" : "Accedi per emettere una chiave →"}
          </a>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10 space-y-10">
        <section className="max-w-3xl">
          <p className="text-lg text-stone-700 leading-relaxed">
            Metti le feature OMNIA (Valutatore UNI 10750, Comparatore Mutui) nel tuo sito con{" "}
            <strong>una riga di codice</strong>. Zero backend, zero manutenzione — il widget vive
            in un iframe leggero brandizzabile, chiama le API OMNIA e cattura lead direttamente
            nel tuo CRM.
          </p>
        </section>

        {/* Widget selector */}
        <section>
          <div className="flex gap-2 border-b border-stone-200 mb-6">
            {WIDGETS.map((widget) => (
              <button
                key={widget.id}
                data-testid={`widget-tab-${widget.id}`}
                onClick={() => setSelected(widget.id)}
                className={`px-4 py-2 text-xs uppercase tracking-widest border-b-2 transition ${
                  selected === widget.id
                    ? "border-stone-900 text-stone-900"
                    : "border-transparent text-stone-500 hover:text-stone-900"
                }`}
              >
                {widget.name}
              </button>
            ))}
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Description column */}
            <div className="space-y-4">
              <div>
                <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-1">
                  {w.tagline}
                </p>
                <h2
                  className="text-2xl"
                  style={{ fontFamily: "'Fraunces', Georgia, serif" }}
                >
                  {w.name}
                </h2>
                <p className="text-sm text-stone-500 mt-1">{w.cost}</p>
              </div>
              <p className="text-sm text-stone-700 leading-relaxed">{w.description}</p>

              <div className="pt-2">
                <label className="text-[10px] uppercase tracking-widest text-stone-500 block mb-2">
                  Anteprima con la tua chiave (opzionale)
                </label>
                <input
                  type="text"
                  data-testid="widgets-preview-key-input"
                  value={previewKey}
                  onChange={(e) => setPreviewKey(e.target.value.trim())}
                  placeholder={DEMO_KEY_HINT}
                  className="w-full border border-stone-300 rounded px-3 py-2 text-sm font-mono"
                />
                <p className="text-xs text-stone-500 mt-1">
                  {previewKey
                    ? "L'anteprima a destra ora chiama davvero l'API OMNIA con la tua chiave."
                    : "Inserisci una chiave `omk_live_...` per vedere l'anteprima interattiva a destra."}
                </p>
              </div>

              <div className="pt-4">
                <label className="text-[10px] uppercase tracking-widest text-stone-500 block mb-2">
                  Snippet installazione (copia e incolla nel tuo sito)
                </label>
                <div className="relative">
                  <pre
                    data-testid="widgets-snippet"
                    className="bg-stone-900 text-stone-100 p-4 rounded overflow-x-auto text-[11px] leading-relaxed"
                  >
                    {snippet}
                  </pre>
                  <button
                    onClick={() => copy(snippet)}
                    data-testid="widgets-copy-snippet"
                    className="absolute top-2 right-2 text-[10px] uppercase tracking-widest bg-stone-700 text-stone-100 px-3 py-1 rounded hover:bg-stone-600"
                  >
                    Copia
                  </button>
                </div>
              </div>
            </div>

            {/* Preview column */}
            <div className="bg-white border border-stone-200 rounded-lg overflow-hidden">
              <div className="border-b border-stone-200 bg-stone-50 px-4 py-2 text-[10px] uppercase tracking-widest text-stone-500">
                Anteprima live
              </div>
              {previewSrc ? (
                <iframe
                  data-testid="widgets-preview-iframe"
                  src={previewSrc}
                  className="w-full"
                  style={{ minHeight: 640, border: 0 }}
                  title={`OMNIA ${selected} preview`}
                />
              ) : (
                <div
                  data-testid="widgets-preview-placeholder"
                  className="p-10 text-center text-sm text-stone-500"
                >
                  <div className="mb-4">🔑</div>
                  Inserisci una chiave API a sinistra per vedere il widget dal vivo.
                  <br />
                  <a
                    href={user ? `/${curLang()}/app/api-keys` : `/${curLang()}/login`}
                    className="underline hover:no-underline mt-2 inline-block"
                  >
                    Non hai ancora una chiave? Emettila qui →
                  </a>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Feature grid */}
        <section className="bg-white border border-stone-200 rounded-lg p-6">
          <h3
            className="text-lg mb-4"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            Come funziona
          </h3>
          <div className="grid md:grid-cols-3 gap-6 text-sm text-stone-700">
            <div>
              <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-2">
                1 · Emetti la chiave
              </p>
              <p>
                Su <a href={`/${curLang()}/app/api-keys`} className="underline">/app/api-keys</a> crei una
                chiave <code>omk_live_...</code> con crediti iniziali e (opzionale)
                <em> partner_id</em> del programma Web Agency (D-046).
              </p>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-2">
                2 · Blinda gli origins
              </p>
              <p>
                Configura la <strong>whitelist di domini</strong> autorizzati (es.
                <code>https://sitodelcliente.it</code>). Solo chiamate da lì passano — le altre
                ricevono 403.
              </p>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-2">
                3 · Incolla lo snippet
              </p>
              <p>
                Il cliente Track B copia il tag <code>&lt;script&gt;</code> nel proprio sito.
                Nessun build step, nessun backend, nessuna manutenzione. Lead nel tuo CRM.
              </p>
            </div>
          </div>
        </section>

        <footer className="text-center text-xs text-stone-500 py-8">
          Powered by OMNIA · <a href="/api/v1/health" className="underline">API v1 health</a> ·{" "}
          <a href={`/${curLang()}/pricing`} className="underline">Pricing</a>
        </footer>
      </main>
    </div>
  );
}

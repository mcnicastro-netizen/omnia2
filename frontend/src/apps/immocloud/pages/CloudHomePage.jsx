import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import { PortalNewsTile } from "../components/PortalNewsBox";

const PROPERTY_TYPES = [
  { v: "", label: "Qualsiasi" },
  { v: "appartamento", label: "Appartamento" },
  { v: "villa", label: "Villa / indipendente" },
  { v: "attico", label: "Attico" },
  { v: "loft", label: "Loft" },
  { v: "monolocale", label: "Monolocale" },
];

/** Tre strumenti che NON ripetono Vendi/Valuta/Mutuo della nav + news. */
const TOOL_TILES = [
  {
    key: "scout",
    to: (lang) => `/${lang}/cloud/search`,
    img: "/cloud/scout.jpg",
    title: "Scout",
    text: "Prima della visita: completezza, prezzo in zona, domande da fare.",
    testid: "tool-scout",
  },
  {
    key: "visura",
    to: (lang) => `/${lang}/cloud/visura`,
    img: "/cloud/intent-value.jpg",
    title: "Visura",
    text: "Il foglio catastale quando ti serve, senza giri di sportello.",
    testid: "tool-visura",
  },
  {
    key: "legal",
    to: (lang) => `/${lang}/legal`,
    img: "/cloud/living.jpg",
    title: "HAL Legal",
    text: "Domande di diritto immobiliare, risposte orientative con fonti.",
    testid: "tool-legal",
  },
];

export default function CloudHomePage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const [facets, setFacets] = useState(null);
  const [pulse, setPulse] = useState(null);
  const [operation, setOperation] = useState("sale");
  const [city, setCity] = useState("");
  const [ptype, setPtype] = useState("");
  const [priceMax, setPriceMax] = useState("");
  const [roomsMin, setRoomsMin] = useState("");
  const nav = useNavigate();

  useEffect(() => {
    api.get(`/cloud/facets?operation=${operation}`).then((r) => setFacets(r.data)).catch(() => {});
  }, [operation]);

  useEffect(() => {
    const q = new URLSearchParams({ operation, days: "7" });
    if (city) q.set("city", city);
    api.get(`/cloud/pulse?${q}`)
      .then((r) => setPulse(r.data))
      .catch(() => setPulse(null));
  }, [operation, city]);

  const submit = (e) => {
    e?.preventDefault?.();
    const params = new URLSearchParams();
    params.set("operation", operation);
    if (city) params.set("city", city);
    if (ptype) params.set("property_type", ptype);
    if (priceMax) params.set("price_max", priceMax);
    if (roomsMin) params.set("rooms_min", roomsMin);
    nav(`search?${params.toString()}`);
  };

  const cityTiles = (facets?.cities?.length
    ? facets.cities.slice(0, 6)
    : [
        { city: "Milano", count: null },
        { city: "Roma", count: null },
        { city: "Napoli", count: null },
        { city: "Torino", count: null },
      ]);

  return (
    <>
      <style>{`
        @keyframes ic-rise {
          from { opacity: 0; transform: translateY(18px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes ic-ken {
          from { transform: scale(1.06); }
          to { transform: scale(1); }
        }
        .ic-rise { animation: ic-rise 0.85s ease-out both; }
        .ic-rise-delay { animation: ic-rise 0.9s ease-out 0.12s both; }
        .ic-rise-delay-2 { animation: ic-rise 0.9s ease-out 0.24s both; }
        .ic-hero-img { animation: ic-ken 14s ease-out both; }
        @media (prefers-reduced-motion: reduce) {
          .ic-rise, .ic-rise-delay, .ic-rise-delay-2, .ic-hero-img { animation: none; }
        }
      `}</style>

      {/* Full-bleed hero — brand + search + one image */}
      <section
        className="relative min-h-[88vh] flex items-end overflow-hidden"
        data-testid="cloud-hero"
      >
        <img
          src="/cloud/hero.jpg"
          alt=""
          className="ic-hero-img absolute inset-0 w-full h-full object-cover"
        />
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(180deg, rgba(11,30,63,0.35) 0%, rgba(11,30,63,0.55) 45%, rgba(11,30,63,0.88) 100%)",
          }}
        />
        <div className="relative w-full max-w-5xl mx-auto px-5 sm:px-8 pb-12 md:pb-16 pt-28">
          <p className="ic-rise text-[12px] uppercase tracking-[0.35em] text-[#E8D5B5] mb-4">
            ImmobilCloud<sup className="text-[8px]">™</sup>
          </p>
          <h1
            className="ic-rise-delay text-4xl sm:text-5xl md:text-6xl leading-[1.02] tracking-tight mb-4 font-light text-white max-w-3xl"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            La casa giusta,<br className="hidden sm:block" /> senza farsi raccontare storie.
          </h1>
          <p className="ic-rise-delay text-base md:text-lg text-white/80 max-w-xl mb-8">
            Cerca casa. Apri un annuncio. Scout — il nostro strumento sull&apos;annuncio — ti dice
            cosa manca e cosa chiedere, prima della visita.
          </p>

          <form
            onSubmit={submit}
            data-testid="cloud-search-form"
            className="ic-rise-delay-2 bg-white/95 backdrop-blur rounded-2xl p-3 md:p-4 space-y-3 shadow-2xl"
          >
            <div className="flex gap-2" role="tablist" aria-label="Operazione">
              {[
                { v: "sale", label: t("cloud.op_sale") },
                { v: "rent", label: t("cloud.op_rent") },
              ].map((o) => (
                <button
                  key={o.v}
                  type="button"
                  role="tab"
                  aria-selected={operation === o.v}
                  data-testid={`cloud-op-${o.v}`}
                  onClick={() => setOperation(o.v)}
                  className={`px-4 py-2 text-xs uppercase tracking-widest rounded-lg border transition ${
                    operation === o.v
                      ? "bg-[#0B1E3F] text-white border-[#0B1E3F]"
                      : "bg-white text-stone-600 border-stone-200 hover:border-stone-400"
                  }`}
                >
                  {o.label}
                </button>
              ))}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
              <input
                data-testid="cloud-search-city"
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="Dove vuoi vivere?"
                list="cloud-cities-suggest"
                className="px-4 py-3 text-base outline-none rounded-lg border border-stone-200 focus:border-[#0B1E3F] bg-stone-50/50"
              />
              <datalist id="cloud-cities-suggest">
                {(facets?.cities || []).map((c) => (
                  <option key={c.city} value={c.city} />
                ))}
              </datalist>
              <select
                data-testid="cloud-search-type"
                value={ptype}
                onChange={(e) => setPtype(e.target.value)}
                className="px-4 py-3 text-sm rounded-lg border border-stone-200 bg-white"
              >
                {PROPERTY_TYPES.map((p) => (
                  <option key={p.v || "any"} value={p.v}>{p.label}</option>
                ))}
              </select>
              <select
                data-testid="cloud-search-rooms"
                value={roomsMin}
                onChange={(e) => setRoomsMin(e.target.value)}
                className="px-4 py-3 text-sm rounded-lg border border-stone-200 bg-white"
              >
                <option value="">Locali</option>
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>{n}+ locali</option>
                ))}
              </select>
              <input
                data-testid="cloud-search-price"
                type="number"
                min="0"
                value={priceMax}
                onChange={(e) => setPriceMax(e.target.value)}
                placeholder={operation === "rent" ? "Canone max €" : "Budget max €"}
                className="px-4 py-3 text-sm rounded-lg border border-stone-200 bg-white"
              />
              <button
                data-testid="cloud-search-btn"
                type="submit"
                className="bg-[#C19A6B] text-white px-6 py-3 rounded-lg font-medium tracking-wide hover:bg-[#0B1E3F] transition-all"
              >
                {t("cloud.search_btn")}
              </button>
            </div>
          </form>

          <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-white/70">
            {facets && (
              <span data-testid="cloud-total">
                {facets.total_active?.toLocaleString("it-IT")} immobili da esplorare
              </span>
            )}
            {pulse && (
              <span data-testid="cloud-pulse" className="text-[#E8D5B5]">
                {pulse.label_it}
              </span>
            )}
            <Link
              to={`/${lang}/cloud/search?view=map`}
              className="text-white hover:text-[#E8D5B5] transition underline-offset-4 hover:underline"
            >
              Guarda sulla mappa →
            </Link>
          </div>
        </div>
      </section>

      {/* Quattro riquadri: Scout · Visura · HAL Legal · News a scorrimento */}
      <section className="px-5 sm:px-8 md:px-16 py-14 bg-[#f7f4ef]" data-testid="cloud-tools">
        <div className="max-w-6xl mx-auto mb-8">
          <p className="text-[11px] uppercase tracking-[0.28em] text-[#C19A6B] mb-2">
            {t("cloud.tools.eyebrow", "Strumenti")}
          </p>
          <h2
            className="text-3xl md:text-4xl font-light tracking-tight text-[#0B1E3F]"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            {t("cloud.tools.title", "Oltre la ricerca")}
          </h2>
          <p className="text-stone-600 mt-2 max-w-2xl">
            {t(
              "cloud.tools.subtitle",
              "Cosa fare sull’annuncio, sui documenti e sul diritto — più le notizie del mercato, senza rumore."
            )}
          </p>
        </div>
        <div className="max-w-6xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {TOOL_TILES.map((tile) => (
            <ToolTile
              key={tile.key}
              to={tile.to(lang)}
              img={tile.img}
              title={tile.title}
              text={tile.text}
              testid={tile.testid}
            />
          ))}
          <PortalNewsTile />
        </div>
      </section>

      {/* Quiet SEO foot — crawlable, not the star */}
      <section className="px-5 sm:px-8 md:px-16 py-12 border-t border-stone-100" data-testid="cloud-seo-density">
        <div className="max-w-5xl mx-auto">
          <h2
            className="text-xl font-light text-[#0B1E3F] mb-1"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            Vendita e affitto, città per città
          </h2>
          <p className="text-sm text-stone-500 mb-6">Entra dritto dove ti serve.</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-4">
            {cityTiles.map((c) => (
              <div key={`seo-${c.city}`} className="border-b border-stone-100 pb-3">
                <p className="text-sm font-medium text-stone-900 mb-1">{c.city}</p>
                <div className="flex gap-4 text-xs uppercase tracking-widest">
                  <Link
                    to={`search?operation=sale&city=${encodeURIComponent(c.city)}`}
                    className="text-[#0B1E3F] hover:text-[#C19A6B]"
                    data-testid={`seo-sale-${c.city}`}
                  >
                    Vendita
                  </Link>
                  <Link
                    to={`search?operation=rent&city=${encodeURIComponent(c.city)}`}
                    className="text-stone-500 hover:text-[#C19A6B]"
                    data-testid={`seo-rent-${c.city}`}
                  >
                    Affitto
                  </Link>
                  <Link
                    to={`/${lang}/cloud/search?view=map&city=${encodeURIComponent(c.city)}`}
                    className="text-stone-400 hover:text-[#C19A6B]"
                  >
                    Mappa
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}

function ToolTile({ to, img, title, text, testid }) {
  return (
    <Link
      to={to}
      data-testid={testid}
      className="group relative block min-h-[280px] sm:min-h-0 sm:aspect-[4/5] overflow-hidden rounded-2xl"
    >
      <img
        src={img}
        alt=""
        className="absolute inset-0 w-full h-full object-cover transition duration-700 group-hover:scale-105"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-[#0B1E3F]/95 via-[#0B1E3F]/45 to-transparent" />
      <div className="absolute inset-x-0 bottom-0 p-5 text-white">
        <h3
          className="text-2xl mb-2"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        >
          {title}
        </h3>
        <p className="text-sm text-white/75 leading-relaxed">{text}</p>
      </div>
    </Link>
  );
}

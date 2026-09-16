import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import PropertyCard from "../components/PropertyCard";

const PROPERTY_TYPES = [
  { v: "", label: "Qualsiasi" },
  { v: "appartamento", label: "Appartamento" },
  { v: "villa", label: "Villa / indipendente" },
  { v: "attico", label: "Attico" },
  { v: "loft", label: "Loft" },
  { v: "monolocale", label: "Monolocale" },
];

export default function CloudHomePage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const [facets, setFacets] = useState(null);
  const [featured, setFeatured] = useState([]);
  const [pulse, setPulse] = useState(null);
  const [operation, setOperation] = useState("sale");
  const [city, setCity] = useState("");
  const [ptype, setPtype] = useState("");
  const [priceMax, setPriceMax] = useState("");
  const [roomsMin, setRoomsMin] = useState("");
  const nav = useNavigate();

  useEffect(() => {
    api.get(`/cloud/facets?operation=${operation}`).then((r) => setFacets(r.data)).catch(() => {});
    api.get(`/cloud/search?operation=${operation}&page_size=6&sort=recent`)
      .then((r) => setFeatured(r.data.items || [])).catch(() => {});
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

  return (
    <>
      {/* Search-first hero — full-bleed atmosphere, utility first */}
      <section
        className="relative overflow-hidden border-b border-stone-200"
        data-testid="cloud-hero"
        style={{
          background:
            "radial-gradient(1200px 500px at 10% -10%, #e8eef8 0%, transparent 55%), radial-gradient(900px 400px at 90% 0%, #f3ebe0 0%, transparent 50%), #fbf9f5",
        }}
      >
        <div className="max-w-5xl mx-auto px-5 sm:px-8 py-12 md:py-16">
          <p className="text-[11px] uppercase tracking-[0.28em] text-stone-500 mb-3">
            ImmobilCloud<sup className="text-[8px]">™</sup>
          </p>
          <h1
            className="text-4xl md:text-5xl leading-[1.05] tracking-tight mb-3 font-light text-[#0B1E3F]"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            {t("immocloud.tagline")}
          </h1>
          <p className="text-base text-stone-600 max-w-2xl mb-8">
            {t("cloud.hero_subtitle")}
          </p>

          <form
            onSubmit={submit}
            data-testid="cloud-search-form"
            className="bg-white rounded-2xl border border-stone-200 shadow-lg p-3 md:p-4 space-y-3"
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
                placeholder={t("cloud.search_placeholder")}
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
                placeholder={operation === "rent" ? "Canone max €" : "Prezzo max €"}
                className="px-4 py-3 text-sm rounded-lg border border-stone-200 bg-white"
              />
              <button
                data-testid="cloud-search-btn"
                type="submit"
                className="bg-[#0B1E3F] text-white px-6 py-3 rounded-lg font-medium tracking-wide hover:bg-[#C19A6B] transition-all"
              >
                {t("cloud.search_btn")}
              </button>
            </div>
          </form>

          <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-stone-500">
            {facets && (
              <span data-testid="cloud-total">
                {t("cloud.total_listings", { n: facets.total_active })}
              </span>
            )}
            {pulse && (
              <span data-testid="cloud-pulse" className="text-stone-700">
                {pulse.label_it}
              </span>
            )}
            <Link
              to={`/${lang}/cloud/search?view=map`}
              className="uppercase tracking-widest text-[#0B1E3F] hover:underline"
            >
              Apri mappa →
            </Link>
          </div>
        </div>
      </section>

      {/* Scout HAL unique strip */}
      <section className="px-5 sm:px-8 md:px-16 py-8 border-b border-stone-100" data-testid="cloud-scout-strip">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <p className="text-[10px] uppercase tracking-[0.25em] text-[#C19A6B] mb-2">Solo su ImmobilCloud</p>
            <h2
              className="text-2xl md:text-3xl font-light text-[#0B1E3F]"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              Scout HAL
            </h2>
            <p className="text-sm text-stone-600 mt-2 max-w-xl">
              Su ogni annuncio: score di completezza, prezzo vs zona, ribassi recenti e le domande giuste da fare al venditore.
              Idealista e Immobiliare non ce l&apos;hanno.
            </p>
          </div>
          <Link
            to={`/${lang}/cloud/search`}
            className="inline-flex justify-center px-5 py-2.5 bg-[#0B1E3F] text-white text-xs uppercase tracking-widest rounded-lg hover:bg-[#C19A6B]"
          >
            Cerca e apri Scout
          </Link>
        </div>
      </section>

      {/* Compact secondary intents — no emoji cards */}
      <section className="px-5 sm:px-8 md:px-16 py-10" data-testid="cloud-intents">
        <div className="max-w-5xl mx-auto grid grid-cols-1 sm:grid-cols-3 gap-4">
          <IntentLink
            to={`/${lang}/cloud/register?intent=sell`}
            title="Vendi"
            text="Pubblica gratis. Boost Vetrina / Premium / TOP a carta."
            testid="intent-sell"
          />
          <IntentLink
            to={`/${lang}/cloud/valutatore`}
            title="Valuta"
            text="Stima gratis · report UNI 10750 a €2,99."
            testid="intent-valuator"
          />
          <IntentLink
            to={`/${lang}/cloud/mutui`}
            title="Mutuo"
            text="Simula la rata e confronta le offerte."
            testid="intent-mutui"
          />
        </div>
      </section>

      {facets?.cities?.length > 0 && (
        <section className="px-5 sm:px-8 md:px-16 py-6" data-testid="cloud-cities-row">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-4">
              {t("cloud.popular_cities")}
            </h2>
            <div className="flex flex-wrap gap-2">
              {facets.cities.slice(0, 12).map((c) => (
                <Link
                  key={c.city}
                  to={`search?operation=${operation}&city=${encodeURIComponent(c.city)}`}
                  data-testid={`cloud-city-pill-${c.city}`}
                  className="px-4 py-2 bg-white border border-stone-200 rounded text-sm hover:border-stone-700 transition"
                >
                  {c.city} <span className="text-stone-400 ml-1">{c.count}</span>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* SEO densità: città × operazione — crawlable without cluttering the hero */}
      <section className="px-5 sm:px-8 md:px-16 py-10 border-t border-stone-100" data-testid="cloud-seo-density">
        <div className="max-w-5xl mx-auto">
          <h2
            className="text-2xl font-light text-[#0B1E3F] mb-2"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            Case in vendita e affitto
          </h2>
          <p className="text-sm text-stone-600 mb-6 max-w-2xl">
            Entra dalla città e dall&apos;operazione: ricerca diretta, mappa e Scout HAL su ogni annuncio.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-4">
            {(facets?.cities?.length
              ? facets.cities.slice(0, 9)
              : [
                  { city: "Milano" },
                  { city: "Roma" },
                  { city: "Torino" },
                  { city: "Napoli" },
                  { city: "Bologna" },
                  { city: "Firenze" },
                ]
            ).map((c) => (
              <div key={c.city} className="border-b border-stone-100 pb-3">
                <p className="text-sm font-medium text-stone-900 mb-1">{c.city}</p>
                <div className="flex gap-4 text-xs uppercase tracking-widest">
                  <Link
                    to={`search?operation=sale&city=${encodeURIComponent(c.city)}`}
                    className="text-[#0B1E3F] hover:underline"
                    data-testid={`seo-sale-${c.city}`}
                  >
                    Vendita
                  </Link>
                  <Link
                    to={`search?operation=rent&city=${encodeURIComponent(c.city)}`}
                    className="text-stone-600 hover:underline"
                    data-testid={`seo-rent-${c.city}`}
                  >
                    Affitto
                  </Link>
                  <Link
                    to={`/${lang}/cloud/search?view=map&city=${encodeURIComponent(c.city)}`}
                    className="text-stone-500 hover:underline"
                  >
                    Mappa
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {featured.length > 0 && (
        <section className="px-5 sm:px-8 md:px-16 py-12" data-testid="cloud-featured">
          <div className="max-w-5xl mx-auto">
            <div className="flex items-baseline justify-between mb-6">
              <h2
                className="text-2xl md:text-3xl font-light tracking-tight"
                style={{ fontFamily: "'Fraunces', Georgia, serif" }}
              >
                In evidenza
              </h2>
              <Link
                to={`search?operation=${operation}`}
                className="text-xs uppercase tracking-widest text-stone-600 hover:text-stone-900"
              >
                {t("cloud.see_all")} →
              </Link>
            </div>
            <p className="text-xs text-stone-500 mb-4">
              TOP e Premium salgono in cima. Poi i più recenti.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {featured.map((p) => (
                <PropertyCard key={p.id} p={p} />
              ))}
            </div>
          </div>
        </section>
      )}
    </>
  );
}

function IntentLink({ to, title, text, testid }) {
  return (
    <Link
      to={to}
      data-testid={testid}
      className="block bg-white border border-stone-200 rounded-xl p-5 hover:border-[#0B1E3F] hover:shadow-md transition"
    >
      <h3
        className="text-lg text-[#0B1E3F] mb-1"
        style={{ fontFamily: "'Fraunces', Georgia, serif" }}
      >
        {title}
      </h3>
      <p className="text-sm text-stone-600">{text}</p>
    </Link>
  );
}

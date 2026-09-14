import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import PropertyCard from "../components/PropertyCard";

// Unsplash hero image: warm italian villa interior, free license
const HERO_IMG = "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1200&q=70&auto=format&fit=crop";

export default function CloudHomePage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const [facets, setFacets] = useState(null);
  const [featured, setFeatured] = useState([]);
  const [operation, setOperation] = useState("sale");
  const [city, setCity] = useState("");
  const nav = useNavigate();

  useEffect(() => {
    api.get(`/cloud/facets?operation=${operation}`).then((r) => setFacets(r.data)).catch(() => {});
    api.get(`/cloud/search?operation=${operation}&page_size=6&sort=recent`)
      .then((r) => setFeatured(r.data.items || [])).catch(() => {});
  }, [operation]);

  const submit = (e) => {
    e?.preventDefault?.();
    const params = new URLSearchParams();
    params.set("operation", operation);
    if (city) params.set("city", city);
    nav(`search?${params.toString()}`);
  };

  return (
    <>
      {/* ───────── Hero split-layout ───────── */}
      <section className="px-5 sm:px-8 md:px-16 py-10 md:py-16" data-testid="cloud-hero">
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-[1.1fr_1fr] gap-8 lg:gap-12 items-center">
          <div>
            <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-4">
              ImmobilCloud<sup className="text-[8px]">™</sup>
            </p>
            <h1 className="text-4xl md:text-5xl lg:text-6xl leading-[1.05] tracking-tight mb-6 font-light"
                style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              {t("immocloud.tagline")}
            </h1>
            <p className="text-base md:text-lg text-stone-600 max-w-xl mb-8">
              {t("cloud.hero_subtitle")}
            </p>
            <form onSubmit={submit} className="bg-white rounded-2xl border border-stone-200 shadow-md p-3 flex flex-col sm:flex-row gap-2">
              <input
                data-testid="cloud-search-city" type="text" value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder={t("cloud.search_placeholder")}
                list="cloud-cities-suggest"
                className="flex-1 px-4 py-3 text-base outline-none rounded-lg focus:bg-stone-50"
              />
              <datalist id="cloud-cities-suggest">
                {(facets?.cities || []).map((c) => <option key={c.city} value={c.city} />)}
              </datalist>
              <button data-testid="cloud-search-btn" type="submit"
                className="bg-[#0B1E3F] text-white px-6 py-3 rounded-lg font-medium tracking-wide hover:bg-[#C19A6B] hover:shadow-md transition-all">
                {t("cloud.search_btn")}
              </button>
            </form>
            {facets && (
              <p className="text-xs text-stone-500 mt-4" data-testid="cloud-total">
                {t("cloud.total_listings", { n: facets.total_active })}
              </p>
            )}
          </div>
          <div className="hidden lg:block">
            <div className="aspect-[4/5] rounded-2xl overflow-hidden shadow-2xl">
              <img src={HERO_IMG} alt="Interno di una casa italiana" loading="lazy" className="w-full h-full object-cover" />
            </div>
          </div>
        </div>
      </section>

      {/* ───────── 3 ACTION CARDS (Cerca · Vendi · Affitta) ───────── */}
      <section className="px-5 sm:px-8 md:px-16 py-12" data-testid="cloud-3cards">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-5">
          <ActionCard
            id="cerca" testid="card-cerca" icon="🔍"
            title={t("cloud.card_cerca_title")} text={t("cloud.card_cerca_text")}
            cta={t("cloud.card_cerca_cta")} to={`/${lang}/cloud/search?operation=sale`}
            accent="navy"
          />
          <ActionCard
            id="vendi" testid="card-vendi" icon="🏷️"
            title={t("cloud.card_vendi_title")} text={t("cloud.card_vendi_text")}
            cta={t("cloud.card_vendi_cta")} to={`/${lang}/cloud/register?intent=sell`}
            accent="gold"
          />
          <ActionCard
            id="affitta" testid="card-affitta" icon="🔑"
            title={t("cloud.card_affitta_title")} text={t("cloud.card_affitta_text")}
            cta={t("cloud.card_affitta_cta")} to={`/${lang}/cloud/register?intent=rent_out`}
            accent="navy"
          />
        </div>
        {/* Cap. 21 · Valutatore card (single row below the 3 core actions) */}
        <div className="max-w-6xl mx-auto mt-5">
          <ActionCard
            id="valutatore" testid="card-valutatore" icon="📊"
            title={t("cloud.card_valutatore_title", "Valuta il tuo immobile")}
            text={t("cloud.card_valutatore_text", "Stima rapida gratis · report UNI 10750 professionale a €2,99")}
            cta={t("cloud.card_valutatore_cta", "Apri il valutatore")}
            to={`/${lang}/cloud/valutatore`}
            accent="navy"
          />
        </div>
      </section>

      {/* ───────── Top cities ───────── */}
      {facets?.cities?.length > 0 && (
        <section className="px-5 sm:px-8 md:px-16 py-8" data-testid="cloud-cities-row">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-4">
              {t("cloud.popular_cities")}
            </h2>
            <div className="flex flex-wrap gap-2">
              {facets.cities.slice(0, 12).map((c) => (
                <Link key={c.city}
                  to={`search?operation=sale&city=${encodeURIComponent(c.city)}`}
                  data-testid={`cloud-city-pill-${c.city}`}
                  className="px-4 py-2 bg-white border border-stone-200 rounded-full text-sm hover:border-stone-700 hover:shadow-sm transition">
                  {c.city} <span className="text-stone-400 ml-1">{c.count}</span>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ───────── Featured cards ───────── */}
      {featured.length > 0 && (
        <section className="px-5 sm:px-8 md:px-16 py-12" data-testid="cloud-featured">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-baseline justify-between mb-6">
              <h2 className="text-2xl md:text-3xl font-light tracking-tight"
                  style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                {t("cloud.featured_title")}
              </h2>
              <Link to={`search?operation=${operation}`} className="text-xs uppercase tracking-widest text-stone-600 hover:text-stone-900">
                {t("cloud.see_all")} →
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {featured.map((p) => <PropertyCard key={p.id} p={p} />)}
            </div>
          </div>
        </section>
      )}
    </>
  );
}

function ActionCard({ id, testid, icon, title, text, cta, to, accent }) {
  const isGold = accent === "gold";
  return (
    <Link to={to} data-testid={testid}
      className={`group block bg-white rounded-2xl border border-stone-200 p-7 hover:shadow-xl hover:-translate-y-1 transition-all ${
        isGold ? "hover:border-[#C19A6B]" : "hover:border-[#0B1E3F]"
      }`}>
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl mb-4 ${
        isGold ? "bg-[#fef7ed] text-[#C19A6B]" : "bg-[#e7eaf2] text-[#0B1E3F]"
      }`}>{icon}</div>
      <h3 className="text-xl font-medium text-stone-900 mb-2"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}>{title}</h3>
      <p className="text-sm text-stone-600 mb-4 min-h-[3rem]">{text}</p>
      <span className={`text-xs uppercase tracking-widest font-medium ${
        isGold ? "text-[#C19A6B]" : "text-[#0B1E3F]"
      }`}>{cta} →</span>
    </Link>
  );
}

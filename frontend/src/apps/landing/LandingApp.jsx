import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import axios from "axios";
import TopNav from "../../shared/components/TopNav";
import Brand from "../../shared/components/Brand";
import OmniaLogo from "../../shared/components/OmniaLogo";
import { scrollToAnchor } from "../../shared/lib/scrollToAnchor";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const BILLING_API = `${BACKEND_URL}/api/billing/plans`;

const PLAN_FEATURES = {
  starter: [
    "Gestionale CRM + match clienti",
    "HAL AI in-app",
    "Sito agenzia + multiposting base",
    "Fino a 3 utenti · 30 immobili",
  ],
  pro: [
    "Tutto di Starter",
    "White-label sul tuo dominio",
    "Staging / tools AI avanzati",
    "Fino a 10 utenti · 200 immobili",
  ],
  agency: [
    "Tutto di Pro",
    "Limiti illimitati",
    "Multiposting esteso",
    "Supporto dedicato",
  ],
};

/**
 * OMNIA vetrina — www.omniarealestateecosystem.it
 * Lab + Ecosystem · tre anime · integrazione · prezzi.
 */
export default function LandingApp() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const [plans, setPlans] = useState([]);
  const [plansError, setPlansError] = useState(null);

  useEffect(() => {
    try {
      if ("scrollRestoration" in window.history) {
        window.history.scrollRestoration = "manual";
      }
    } catch {
      /* ignore */
    }
    const prev = document.title;
    document.title = t(
      "landing.doc_title",
      "OMNIA Real Estate Ecosystem — Sistema operativo per agenzie",
    );
    return () => {
      document.title = prev;
    };
  }, [t]);

  // Deep-link iniziale (/it#prezzi) — una sola volta, senza rivaleggiare con la nav
  useEffect(() => {
    const hash = window.location.hash || "";
    if (!hash) {
      window.scrollTo(0, 0);
      return undefined;
    }
    const t = window.setTimeout(() => {
      scrollToAnchor(hash);
    }, 60);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- solo mount
  }, []);

  useEffect(() => {
    axios
      .get(BILLING_API)
      .then((r) => {
        const list = (r.data?.plans || []).map((p) => ({
          id: p.tier,
          name: p.name,
          monthly: p.price_monthly,
          yearly: p.price_yearly ?? Math.round(p.price_monthly * 11),
          agents: p.max_agents === -1 ? "∞" : p.max_agents,
          properties: p.max_properties === -1 ? "∞" : p.max_properties,
          credits: p.credits_included_monthly,
          highlight: p.tier === "pro",
          features: PLAN_FEATURES[p.tier] || [],
        }));
        setPlans(list);
        setPlansError(null);
      })
      .catch(() => {
        setPlans([]);
        setPlansError(t("landing.pricing_unavailable"));
      });
  }, [t]);

  const pillars = [
    {
      key: "cloud",
      tag: t("landing.pillar_cloud_tag"),
      title: t("landing.pillar_cloud_title"),
      role: t("landing.pillar_cloud_role"),
      body: t("landing.pillar_cloud_body"),
      goal: t("landing.pillar_cloud_goal"),
      to: `/${lang}/cloud`,
      accent: "#C8A653",
      note: null,
    },
    {
      key: "crm",
      tag: t("landing.pillar_crm_tag"),
      title: t("landing.pillar_crm_title"),
      role: t("landing.pillar_crm_role"),
      body: t("landing.pillar_crm_body"),
      goal: t("landing.pillar_crm_goal"),
      to: `/${lang}/register`,
      accent: "#1F6B5C",
      note: null,
    },
    {
      key: "academy",
      tag: t("landing.pillar_academy_tag"),
      title: t("landing.pillar_academy_title"),
      role: t("landing.pillar_academy_role"),
      body: t("landing.pillar_academy_body"),
      goal: t("landing.pillar_academy_goal"),
      to: `/${lang}/learn`,
      accent: "#0B1E3F",
      note: t("landing.pillar_academy_note"),
    },
  ];

  const reasons = [
    { key: "one", title: t("landing.why_1_title"), body: t("landing.why_1_body") },
    { key: "two", title: t("landing.why_2_title"), body: t("landing.why_2_body") },
    { key: "three", title: t("landing.why_3_title"), body: t("landing.why_3_body") },
    { key: "four", title: t("landing.why_4_title"), body: t("landing.why_4_body") },
  ];

  const loopItems = [
    t("landing.integrate_1"),
    t("landing.integrate_2"),
    t("landing.integrate_3"),
    t("landing.integrate_4"),
  ];

  return (
    <div
      data-testid="landing-app"
      className="min-h-screen text-[#0B1E3F]"
      style={{ fontFamily: "'Fraunces', Georgia, serif" }}
    >
      {/* TopNav FUORI da overflow-x-hidden: altrimenti position:sticky si spezza e Chi siamo “atterra a metà” */}
      <TopNav current="landing" theme="light" />

      <div className="overflow-x-hidden">
      {/* HERO */}
      <section
        data-testid="landing-hero"
        className="relative min-h-[90vh] flex items-end md:items-center overflow-hidden"
      >
        <img
          src="/cloud/hero.jpg"
          alt=""
          className="absolute inset-0 h-full w-full object-cover animate-[landingKen_22s_ease-in-out_infinite_alternate]"
          loading="eager"
        />
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(115deg, rgba(11,30,63,0.94) 0%, rgba(11,30,63,0.78) 38%, rgba(11,30,63,0.4) 68%, rgba(31,107,92,0.25) 100%)",
          }}
        />
        <div className="absolute inset-0 opacity-[0.07] pointer-events-none"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, #fff 1px, transparent 0)",
            backgroundSize: "28px 28px",
          }}
        />
        <div className="relative z-10 w-full max-w-screen-2xl mx-auto px-5 sm:px-8 md:px-12 lg:px-16 py-16 md:py-24">
          <div className="max-w-3xl animate-[landingRise_0.85s_ease_both]">
            <p className="text-[#C8A653] text-sm sm:text-base tracking-[0.12em] mb-3 font-medium uppercase font-sans">
              <Brand>{t("landing.hero_eyebrow")}</Brand>
            </p>
            <h1 className="text-white text-4xl sm:text-5xl md:text-6xl leading-[1.05] tracking-tight mb-5 md:mb-6">
              {t("landing.hero_title")}
            </h1>
            <p className="text-white/85 text-base sm:text-lg md:text-xl max-w-2xl mb-6 font-sans font-light leading-relaxed">
              {t("landing.hero_subtitle")}
            </p>
            <div className="flex flex-wrap gap-2 mb-8 md:mb-10">
              <span className="font-sans text-[10px] sm:text-xs uppercase tracking-[0.22em] px-3 py-1.5 border border-[#C8A653]/50 text-[#C8A653] bg-[#C8A653]/10">
                {t("landing.hero_pill_lab")}
              </span>
              <span className="font-sans text-[10px] sm:text-xs uppercase tracking-[0.22em] px-3 py-1.5 border border-white/35 text-white/90 bg-white/5">
                {t("landing.hero_pill_eco")}
              </span>
            </div>
            <div className="flex flex-wrap gap-3 sm:gap-4">
              <Link
                to={`/${lang}/register`}
                data-testid="landing-cta-register"
                className="inline-flex items-center px-6 py-3 text-xs sm:text-sm font-sans uppercase tracking-widest bg-[#C8A653] text-[#0B1E3F] hover:bg-[#d4b56a] transition"
              >
                {t("landing.cta_start")}
              </Link>
              <a
                href="#prezzi"
                data-testid="landing-cta-pricing"
                className="inline-flex items-center px-6 py-3 text-xs sm:text-sm font-sans uppercase tracking-widest border border-white/50 text-white hover:bg-white/10 transition"
              >
                {t("landing.cta_pricing")}
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* CHI SIAMO — foto nostra + logo OMNIA + copy (no ripetizione pilastri) */}
      <section
        id="chi-siamo"
        data-testid="landing-about"
        className="scroll-mt-[72px] relative overflow-hidden bg-white min-h-[calc(100svh-4.5rem)]"
      >
        <img
          src="/cloud/hero.jpg"
          alt=""
          className="absolute inset-0 h-full w-full object-cover object-[28%_center]"
          loading="lazy"
        />
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "linear-gradient(100deg, rgba(255,255,255,0.7) 0%, rgba(255,255,255,0.35) 38%, rgba(255,255,255,0.55) 58%, #fff 78%)",
          }}
        />
        <div
          aria-hidden
          className="hidden md:block absolute top-0 bottom-0 right-0 w-[58%] bg-white"
          style={{
            /* bulbo bianco allineato in alto col copy, non a metà altezza */
            clipPath: "ellipse(92% 95% at 100% 28%)",
          }}
        />
        <div
          aria-hidden
          className="md:hidden absolute inset-x-0 bottom-0 h-[52%] bg-white rounded-t-[1.75rem]"
        />

        {/* Banner alto sotto nav, contenuto PINATO in alto (mai items-center) */}
        <div className="relative z-10 max-w-screen-2xl mx-auto min-h-[calc(100svh-4.5rem)] px-5 sm:px-8 md:px-12 lg:px-16 pt-6 pb-10 md:pt-8 md:pb-12 grid md:grid-cols-2 gap-6 md:gap-8 items-start content-start">
          <div className="flex flex-col justify-start animate-[landingRise_0.8s_ease_both]">
            <div
              data-testid="landing-about-brand"
              className="inline-flex flex-col items-start w-full max-w-sm px-4 py-5 md:px-6 md:py-6 rounded-sm"
              style={{
                background: "rgba(255,255,255,0.42)",
                backdropFilter: "blur(20px) saturate(1.15)",
                WebkitBackdropFilter: "blur(20px) saturate(1.15)",
                boxShadow: "0 16px 48px rgba(11,30,63,0.08)",
                border: "1px solid rgba(255,255,255,0.5)",
              }}
            >
              <div
                data-testid="landing-about-logo"
                className="flex flex-col items-start mb-3"
              >
                <img
                  src="/landing/omnia-mark-3x.png"
                  alt=""
                  width={768}
                  height={660}
                  className="select-none mb-2 h-[72px] md:h-[88px] w-auto"
                  draggable={false}
                />
                <p
                  className="text-xl md:text-2xl font-semibold tracking-[0.18em] text-[#0B1E3F] uppercase leading-none"
                  style={{ fontFamily: "'Montserrat', 'Inter', system-ui, sans-serif" }}
                >
                  <Brand>OMNIA</Brand>
                </p>
                <p
                  className="mt-1.5 text-[10px] md:text-[11px] font-medium tracking-[0.28em] text-[#0B1E3F]/80 uppercase"
                  style={{ fontFamily: "'Montserrat', 'Inter', system-ui, sans-serif" }}
                >
                  Real Estate Lab
                </p>
              </div>
              <div className="w-14 h-px bg-[#0B1E3F]/45 mb-3" />
              <p
                className="w-full text-[11px] sm:text-[12px] uppercase tracking-[0.16em] text-[#0B1E3F] font-semibold flex flex-wrap items-center gap-x-2 gap-y-1"
                style={{ fontFamily: "'Montserrat', 'Inter', system-ui, sans-serif" }}
              >
                {t("landing.about_tagline")
                  .split(/\s*[·•|]\s*/)
                  .filter(Boolean)
                  .map((word, i, arr) => (
                    <span key={word} className="inline-flex items-center gap-2">
                      <span className="whitespace-nowrap">{word}</span>
                      {i < arr.length - 1 ? (
                        <span className="text-[#0B1E3F]/35" aria-hidden>
                          ·
                        </span>
                      ) : null}
                    </span>
                  ))}
              </p>
            </div>
          </div>

          <div className="flex flex-col justify-start md:pl-8 lg:pl-14 xl:pl-20 pt-0.5 animate-[landingRise_0.9s_ease_both]">
            <p
              className="text-[11px] uppercase tracking-[0.28em] text-[#1F6B5C] mb-2.5 font-semibold"
              style={{ fontFamily: "'Montserrat', 'Inter', system-ui, sans-serif" }}
            >
              {t("landing.about_eyebrow")}
            </p>
            <h2
              className="text-xl sm:text-2xl lg:text-[2rem] font-semibold tracking-tight text-[#0B1E3F] leading-[1.2] mb-3 [&_strong]:font-bold"
              style={{ fontFamily: "'Montserrat', 'Inter', system-ui, sans-serif" }}
              dangerouslySetInnerHTML={{
                __html: t("landing.about_headline_html"),
              }}
            />
            <p
              className="text-[14px] sm:text-[15px] text-[#0B1E3F]/80 leading-relaxed max-w-xl [&_strong]:text-[#0B1E3F] [&_strong]:font-semibold"
              style={{ fontFamily: "'Montserrat', 'Inter', system-ui, sans-serif" }}
              dangerouslySetInnerHTML={{
                __html: t("landing.about_body_html"),
              }}
            />
          </div>
        </div>
      </section>

      {/* TRE ANIME */}
      <section
        id="offerta"
        data-testid="landing-pillars"
        className="scroll-mt-[72px] bg-[#0B1E3F] text-[#F5F1E8] px-5 sm:px-8 md:px-12 lg:px-16 py-20 md:py-28"
      >
        <div className="max-w-screen-2xl mx-auto">
          <p className="text-[10px] sm:text-xs font-sans uppercase tracking-[0.3em] text-[#C8A653] mb-3">
            {t("landing.pillars_eyebrow")}
          </p>
          <h2 className="text-3xl md:text-4xl tracking-tight mb-3 max-w-2xl">
            {t("landing.pillars_title")}
          </h2>
          <p className="font-sans text-[#F5F1E8]/70 max-w-2xl mb-12 md:mb-16 text-base md:text-lg">
            {t("landing.pillars_lead")}
          </p>

          <div className="grid md:grid-cols-3 gap-6 md:gap-8">
            {pillars.map((p, i) => (
              <Link
                key={p.key}
                to={p.to}
                data-testid={`landing-pillar-${p.key}`}
                className="group relative flex flex-col min-h-[320px] p-7 md:p-8 bg-[#132848] border border-white/10 hover:border-[#C8A653]/60 transition animate-[landingRise_0.7s_ease_both]"
                style={{ animationDelay: `${0.08 * i}s` }}
              >
                <div
                  className="absolute top-0 left-0 right-0 h-1 opacity-90"
                  style={{ background: p.accent }}
                />
                <p
                  className="text-[10px] font-sans uppercase tracking-[0.3em] mb-4"
                  style={{ color: p.accent === "#0B1E3F" ? "#C8A653" : p.accent }}
                >
                  {p.tag}
                </p>
                <h3 className="text-2xl md:text-3xl tracking-tight mb-1">
                  <Brand>{p.title}</Brand>
                </h3>
                <p className="font-sans text-sm text-[#F5F1E8]/55 mb-5 uppercase tracking-wider">
                  {p.role}
                </p>
                <p className="font-sans text-sm md:text-base text-[#F5F1E8]/80 leading-relaxed flex-1">
                  {p.body}
                </p>
                <p className="mt-5 font-sans text-xs text-[#C8A653] tracking-wide">
                  → {p.goal}
                </p>
                {p.note ? (
                  <p className="mt-4 font-sans text-[11px] leading-relaxed text-[#F5F1E8]/50 border-t border-white/10 pt-4">
                    {p.note}
                  </p>
                ) : null}
                <span className="mt-6 font-sans text-xs uppercase tracking-widest text-[#C8A653] group-hover:translate-x-1 transition-transform inline-block">
                  {t("landing.pillar_cta")} →
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* PERCHÉ OMNIA — prima del vero lavoro nello scroll */}
      <section
        id="perche"
        data-testid="landing-why"
        className="scroll-mt-[72px] bg-[#0B1E3F] text-[#F5F1E8] px-5 sm:px-8 md:px-12 lg:px-16 py-20 md:py-24"
      >
        <div className="max-w-screen-2xl mx-auto">
          <p className="text-[10px] sm:text-xs font-sans uppercase tracking-[0.3em] text-[#C8A653] mb-3">
            {t("landing.why_eyebrow")}
          </p>
          <h2 className="text-3xl md:text-4xl tracking-tight mb-12 md:mb-14 max-w-xl">
            {t("landing.why_title")}
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8 md:gap-10">
            {reasons.map((r, i) => (
              <div key={r.key} data-testid={`landing-why-${r.key}`}>
                <p className="text-[#C8A653] font-sans text-xs tracking-widest mb-3">
                  0{i + 1}
                </p>
                <h3 className="text-xl mb-3 tracking-tight">{r.title}</h3>
                <p className="font-sans text-sm text-[#F5F1E8]/70 leading-relaxed">
                  {r.body}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* IL VERO LAVORO — diagramma integrazione */}
      <section
        id="vero-lavoro"
        data-testid="landing-integrate"
        className="scroll-mt-[72px] px-5 sm:px-8 md:px-12 lg:px-16 py-20 md:py-28"
        style={{
          background:
            "linear-gradient(180deg, #eef3f1 0%, #F5F1E8 40%, #e8eef5 100%)",
        }}
      >
        <div className="max-w-screen-2xl mx-auto grid lg:grid-cols-2 gap-14 lg:gap-20 items-center">
          <div>
            <p className="text-[10px] sm:text-xs font-sans uppercase tracking-[0.3em] text-[#1F6B5C] mb-3">
              {t("landing.integrate_eyebrow")}
            </p>
            <h2 className="text-3xl md:text-4xl tracking-tight mb-4 max-w-lg">
              {t("landing.integrate_title")}
            </h2>
            <p className="font-sans text-[#0B1E3F]/70 text-base md:text-lg leading-relaxed mb-8 max-w-xl">
              {t("landing.integrate_lead")}
            </p>
            <ol className="space-y-4 font-sans">
              {loopItems.map((item, idx) => (
                <li key={idx} className="flex gap-4 items-start">
                  <span className="shrink-0 w-8 h-8 flex items-center justify-center text-xs tracking-widest text-[#C8A653] border border-[#C8A653]/40 bg-white/60">
                    0{idx + 1}
                  </span>
                  <span className="text-sm md:text-base text-[#0B1E3F]/80 pt-1.5 leading-relaxed">
                    {item}
                  </span>
                </li>
              ))}
            </ol>
          </div>

          {/* Diagramma ecosistema */}
          <div
            data-testid="landing-ecosystem-diagram"
            className="relative mx-auto w-full max-w-md aspect-square"
          >
            <div
              className="absolute inset-[12%] rounded-full border border-[#0B1E3F]/15 animate-[landingPulse_6s_ease-in-out_infinite]"
              style={{
                background:
                  "radial-gradient(circle at 50% 50%, rgba(200,166,83,0.2), transparent 65%)",
              }}
            />
            <div className="absolute inset-[28%] rounded-full bg-[#0B1E3F] text-[#F5F1E8] flex items-center justify-center text-center shadow-[0_20px_60px_rgba(11,30,63,0.25)] animate-[landingRise_1s_ease_both]">
              <p className="font-sans text-[10px] sm:text-xs uppercase tracking-[0.25em] leading-relaxed px-4 whitespace-pre-line">
                {t("landing.integrate_diagram_center")}
              </p>
            </div>
            {[
              {
                label: t("landing.integrate_diagram_market"),
                sub: "ImmobilCloud",
                pos: "top-0 left-1/2 -translate-x-1/2",
                color: "#C8A653",
              },
              {
                label: t("landing.integrate_diagram_ops"),
                sub: "ImmoWeb",
                pos: "bottom-[8%] left-0",
                color: "#1F6B5C",
              },
              {
                label: t("landing.integrate_diagram_skills"),
                sub: "Academy",
                pos: "bottom-[8%] right-0",
                color: "#0B1E3F",
              },
            ].map((node) => (
              <div
                key={node.sub}
                className={`absolute ${node.pos} w-[42%] sm:w-[38%] bg-white/95 border border-[#0B1E3F]/10 px-4 py-3 shadow-[0_12px_40px_rgba(11,30,63,0.08)]`}
                style={{ borderTop: `3px solid ${node.color}` }}
              >
                <p className="font-sans text-[10px] uppercase tracking-[0.25em] text-[#0B1E3F]/50 mb-1">
                  {node.label}
                </p>
                <p className="text-sm sm:text-base tracking-tight">
                  <Brand>{node.sub}</Brand>
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PREZZI */}
      <section
        id="prezzi"
        data-testid="landing-pricing"
        className="scroll-mt-[72px] px-5 sm:px-8 md:px-12 lg:px-16 py-20 md:py-28 border-t border-[#0B1E3F]/10"
        style={{
          background:
            "linear-gradient(180deg, #F5F1E8 0%, #eef3f1 55%, #F5F1E8 100%)",
        }}
      >
        <div className="max-w-screen-2xl mx-auto">
          <p className="text-[10px] sm:text-xs font-sans uppercase tracking-[0.3em] text-[#1F6B5C] mb-3 text-center">
            {t("landing.pricing_eyebrow")}
          </p>
          <h2 className="text-3xl md:text-4xl tracking-tight text-center mb-3">
            {t("landing.pricing_title")}
          </h2>
          <p className="font-sans text-center text-[#0B1E3F]/65 max-w-xl mx-auto mb-12 md:mb-16">
            {t("landing.pricing_lead")}
          </p>

          {plansError ? (
            <p
              className="text-center font-sans text-sm text-stone-500"
              data-testid="landing-pricing-error"
            >
              {plansError}
            </p>
          ) : (
            <div
              className="grid md:grid-cols-3 gap-6 md:gap-8 max-w-5xl mx-auto"
              data-testid="landing-pricing-grid"
            >
              {plans.map((p) => (
                <div
                  key={p.id}
                  data-testid={`landing-plan-${p.id}`}
                  className={`relative flex flex-col p-7 md:p-8 border ${
                    p.highlight
                      ? "border-[#C8A653] bg-white shadow-[0_20px_50px_rgba(11,30,63,0.1)]"
                      : "border-[#0B1E3F]/15 bg-[#F5F1E8]/90"
                  }`}
                >
                  {p.highlight ? (
                    <p className="absolute -top-3 left-6 text-[10px] font-sans uppercase tracking-widest bg-[#C8A653] text-[#0B1E3F] px-3 py-1">
                      {t("landing.pricing_popular")}
                    </p>
                  ) : null}
                  <h3 className="text-2xl mb-1 tracking-tight">{p.name}</h3>
                  <p className="font-sans text-xs text-[#0B1E3F]/50 mb-6 uppercase tracking-wider">
                    {p.agents} {t("landing.pricing_agents")} · {p.properties}{" "}
                    {t("landing.pricing_listings")}
                  </p>
                  <p className="mb-1">
                    <span className="text-4xl tracking-tight">€{p.monthly}</span>
                    <span className="font-sans text-sm text-[#0B1E3F]/55 ml-1">
                      /{t("landing.pricing_month")}
                    </span>
                  </p>
                  <p className="font-sans text-sm text-[#0B1E3F]/55 mb-6">
                    {t("landing.pricing_or_year")} <strong>€{p.yearly}</strong>
                  </p>
                  <ul className="font-sans text-sm text-[#0B1E3F]/75 space-y-2 mb-8 flex-1">
                    {p.features.map((f) => (
                      <li key={f} className="flex gap-2">
                        <span className="text-[#1F6B5C]" aria-hidden>
                          —
                        </span>
                        <span>{f}</span>
                      </li>
                    ))}
                    <li className="flex gap-2">
                      <span className="text-[#1F6B5C]" aria-hidden>
                        —
                      </span>
                      <span>
                        {p.credits} {t("landing.pricing_credits")}
                      </span>
                    </li>
                  </ul>
                  <Link
                    to={`/${lang}/register?plan=${p.id}`}
                    data-testid={`landing-plan-cta-${p.id}`}
                    className={`text-center text-xs font-sans uppercase tracking-widest px-4 py-3 transition ${
                      p.highlight
                        ? "bg-[#0B1E3F] text-[#F5F1E8] hover:bg-[#1a3358]"
                        : "border border-[#0B1E3F] text-[#0B1E3F] hover:bg-[#0B1E3F] hover:text-[#F5F1E8]"
                    }`}
                  >
                    {t("landing.cta_choose_plan")}
                  </Link>
                </div>
              ))}
            </div>
          )}

          <p className="mt-10 text-center font-sans text-xs text-[#0B1E3F]/50 max-w-lg mx-auto">
            {t("landing.pricing_footnote")}
          </p>
        </div>
      </section>

      {/* CTA FINALE */}
      <section
        data-testid="landing-final-cta"
        className="px-5 sm:px-8 md:px-12 lg:px-16 py-16 md:py-20 bg-[#0B1E3F] text-center relative overflow-hidden"
      >
        <div
          className="absolute inset-0 opacity-30 pointer-events-none"
          style={{
            background:
              "radial-gradient(600px 200px at 50% 100%, rgba(200,166,83,0.35), transparent 70%)",
          }}
        />
        <div className="relative">
          <h2 className="text-[#F5F1E8] text-2xl md:text-3xl tracking-tight mb-4">
            {t("landing.final_title")}
          </h2>
          <p className="font-sans text-[#F5F1E8]/70 mb-8 max-w-lg mx-auto">
            {t("landing.final_lead")}
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link
              to={`/${lang}/register`}
              className="inline-flex px-6 py-3 text-xs font-sans uppercase tracking-widest bg-[#C8A653] text-[#0B1E3F] hover:bg-[#d4b56a] transition"
            >
              {t("landing.cta_start")}
            </Link>
            <Link
              to={`/${lang}/cloud`}
              className="inline-flex px-6 py-3 text-xs font-sans uppercase tracking-widest border border-[#F5F1E8]/40 text-[#F5F1E8] hover:bg-white/10 transition"
            >
              {t("landing.cta_cloud")}
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-[#0B1E3F]/10 bg-[#0B1E3F] text-[#F5F1E8]">
        <div className="max-w-screen-2xl mx-auto px-5 sm:px-8 md:px-12 lg:px-16 py-6 md:py-8 text-[10px] sm:text-xs font-sans uppercase tracking-widest text-[#F5F1E8]/70 flex flex-col sm:flex-row gap-3 sm:gap-6 sm:justify-between sm:items-center">
          <span className="flex items-center gap-2 text-[#F5F1E8]">
            <OmniaLogo variant="mark" size="sm" inverted />
            © 2026 <Brand>OMNIA Real Estate Lab</Brand>
          </span>
          <div className="flex flex-wrap gap-4 sm:gap-6">
            <Link
              to={`/${lang}/domain-sovereignty-policy`}
              className="hover:text-[#C8A653] transition"
            >
              {t("domain_vault.policy_link")}
            </Link>
            <Link
              to={`/${lang}/verifica-dominio`}
              className="hover:text-[#C8A653] transition"
            >
              {t("domain_vault.existing_domain_verify_cta")}
            </Link>
            <Link
              to={`/${lang}/agenzie`}
              className="hover:text-[#C8A653] transition"
            >
              {t("landing.nav_founders")}
            </Link>
          </div>
          <Brand className="truncate text-[#C8A653]/90">
            omniarealestateecosystem.it
          </Brand>
        </div>
      </footer>

      <style>{`
        @keyframes landingRise {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: none; }
        }
        @keyframes landingKen {
          from { transform: scale(1); }
          to { transform: scale(1.06); }
        }
        @keyframes landingPulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.03); opacity: 0.85; }
        }
      `}</style>
      </div>
    </div>
  );
}

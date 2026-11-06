import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import axios from "axios";
import TopNav from "../../shared/components/TopNav";
import Brand from "../../shared/components/Brand";
import OmniaLogo from "../../shared/components/OmniaLogo";

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
 * Chi siamo · progetto · perché sceglierci · cosa vendiamo · prezzi.
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
      "OMNIA — Ecosistema immobiliare per agenzie",
    );
    const hash = (window.location.hash || "").replace(/^#/, "");
    if (hash) {
      // Nav anchor (#chi-siamo / #prezzi…): after paint, non azzerare lo scroll
      requestAnimationFrame(() => {
        document.getElementById(hash)?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    } else {
      window.scrollTo(0, 0);
    }
    return () => {
      document.title = prev;
    };
  }, [t]);

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

  const reasons = [
    {
      key: "one",
      title: t("landing.why_1_title"),
      body: t("landing.why_1_body"),
    },
    {
      key: "two",
      title: t("landing.why_2_title"),
      body: t("landing.why_2_body"),
    },
    {
      key: "three",
      title: t("landing.why_3_title"),
      body: t("landing.why_3_body"),
    },
  ];

  const products = [
    {
      key: "immoweb",
      tag: "B2B",
      title: t("landing.product_crm_title"),
      body: t("landing.product_crm_body"),
      to: `/${lang}/register`,
    },
    {
      key: "cloud",
      tag: "B2C",
      title: t("landing.product_cloud_title"),
      body: t("landing.product_cloud_body"),
      to: `/${lang}/cloud`,
    },
    {
      key: "academy",
      tag: "Academy",
      title: t("landing.product_academy_title"),
      body: t("landing.product_academy_body"),
      to: `/${lang}/learn`,
    },
  ];

  return (
    <div
      data-testid="landing-app"
      className="min-h-screen overflow-x-hidden text-[#0B1E3F]"
      style={{ fontFamily: "'Fraunces', Georgia, serif" }}
    >
      <TopNav current="landing" theme="light" />

      {/* HERO — full-bleed vetrina */}
      <section
        data-testid="landing-hero"
        className="relative min-h-[88vh] flex items-end md:items-center overflow-hidden"
      >
        <img
          src="/cloud/hero.jpg"
          alt=""
          className="absolute inset-0 h-full w-full object-cover animate-[landingKen_18s_ease-in-out_infinite_alternate]"
          loading="eager"
        />
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(105deg, rgba(11,30,63,0.92) 0%, rgba(11,30,63,0.72) 42%, rgba(11,30,63,0.35) 70%, rgba(11,30,63,0.2) 100%)",
          }}
        />
        <div className="relative z-10 w-full max-w-screen-2xl mx-auto px-5 sm:px-8 md:px-12 lg:px-16 py-16 md:py-24">
          <div className="max-w-2xl animate-[landingRise_0.8s_ease_both]">
            <p className="text-[#C8A653] text-sm sm:text-base md:text-lg tracking-[0.08em] mb-4 md:mb-5 font-medium">
              <Brand>OMNIA Real Estate Ecosystem</Brand>
            </p>
            <h1 className="text-white text-4xl sm:text-5xl md:text-6xl leading-[1.05] tracking-tight mb-5 md:mb-6">
              {t("landing.hero_title")}
            </h1>
            <p
              className="text-white/85 text-base sm:text-lg md:text-xl max-w-xl mb-8 md:mb-10 font-sans font-light leading-relaxed"
            >
              {t("landing.hero_subtitle")}
            </p>
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

      {/* CHI SIAMO */}
      <section
        id="chi-siamo"
        data-testid="landing-about"
        className="scroll-mt-28 px-5 sm:px-8 md:px-12 lg:px-16 py-20 md:py-28 max-w-screen-2xl mx-auto"
        style={{
          background:
            "radial-gradient(900px 400px at 0% 0%, rgba(31,107,92,0.08), transparent 60%), #F5F1E8",
        }}
      >
        <div className="grid md:grid-cols-12 gap-10 md:gap-16 items-start">
          <div className="md:col-span-4">
            <p className="text-[10px] sm:text-xs font-sans uppercase tracking-[0.3em] text-[#1F6B5C] mb-3">
              {t("landing.about_eyebrow")}
            </p>
            <h2 className="text-3xl md:text-4xl tracking-tight text-[#0B1E3F]">
              {t("landing.about_title")}
            </h2>
          </div>
          <div className="md:col-span-8 space-y-5 font-sans text-[#0B1E3F]/80 text-base md:text-lg leading-relaxed">
            <p>{t("landing.about_p1")}</p>
            <p>{t("landing.about_p2")}</p>
          </div>
        </div>
      </section>

      {/* PERCHÉ SCEGLIERCI */}
      <section
        id="perche"
        data-testid="landing-why"
        className="scroll-mt-28 bg-[#0B1E3F] text-[#F5F1E8] px-5 sm:px-8 md:px-12 lg:px-16 py-20 md:py-28"
      >
        <div className="max-w-screen-2xl mx-auto">
          <p className="text-[10px] sm:text-xs font-sans uppercase tracking-[0.3em] text-[#C8A653] mb-3">
            {t("landing.why_eyebrow")}
          </p>
          <h2 className="text-3xl md:text-4xl tracking-tight mb-12 md:mb-16 max-w-xl">
            {t("landing.why_title")}
          </h2>
          <div className="grid md:grid-cols-3 gap-10 md:gap-12">
            {reasons.map((r, i) => (
              <div
                key={r.key}
                data-testid={`landing-why-${r.key}`}
                className="animate-[landingRise_0.7s_ease_both]"
                style={{ animationDelay: `${0.1 * i}s` }}
              >
                <p className="text-[#C8A653] font-sans text-xs tracking-widest mb-4">
                  0{i + 1}
                </p>
                <h3 className="text-xl md:text-2xl mb-3 tracking-tight">{r.title}</h3>
                <p className="font-sans text-sm md:text-base text-[#F5F1E8]/75 leading-relaxed">
                  {r.body}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* COSA VENDIAMO */}
      <section
        id="offerta"
        data-testid="landing-offer"
        className="scroll-mt-28 px-5 sm:px-8 md:px-12 lg:px-16 py-20 md:py-28 max-w-screen-2xl mx-auto bg-[#F5F1E8]"
      >
        <p className="text-[10px] sm:text-xs font-sans uppercase tracking-[0.3em] text-[#1F6B5C] mb-3">
          {t("landing.offer_eyebrow")}
        </p>
        <h2 className="text-3xl md:text-4xl tracking-tight mb-4 max-w-2xl">
          {t("landing.offer_title")}
        </h2>
        <p className="font-sans text-[#0B1E3F]/70 max-w-2xl mb-12 md:mb-16 text-base md:text-lg">
          {t("landing.offer_lead")}
        </p>
        <div className="grid md:grid-cols-3 gap-8 md:gap-10">
          {products.map((p) => (
            <Link
              key={p.key}
              to={p.to}
              data-testid={`landing-product-${p.key}`}
              className="group block border-t border-[#0B1E3F]/20 pt-6 hover:border-[#C8A653] transition"
            >
              <p className="text-[10px] font-sans uppercase tracking-[0.3em] text-[#1F6B5C] mb-3">
                {p.tag}
              </p>
              <h3 className="text-2xl mb-3 tracking-tight group-hover:translate-x-1 transition-transform">
                <Brand>{p.title}</Brand>
              </h3>
              <p className="font-sans text-sm text-[#0B1E3F]/70 leading-relaxed mb-5">
                {p.body}
              </p>
              <span className="font-sans text-xs uppercase tracking-widest text-[#C8A653]">
                {t("common.next")} →
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* PREZZI */}
      <section
        id="prezzi"
        data-testid="landing-pricing"
        className="scroll-mt-28 px-5 sm:px-8 md:px-12 lg:px-16 py-20 md:py-28 border-t border-[#0B1E3F]/10"
        style={{
          background:
            "linear-gradient(180deg, #eef3f1 0%, #F5F1E8 55%, #e8eef5 100%)",
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
        className="px-5 sm:px-8 md:px-12 lg:px-16 py-16 md:py-20 bg-[#0B1E3F] text-center"
      >
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
      `}</style>
    </div>
  );
}

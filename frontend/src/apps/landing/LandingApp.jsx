import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import TopNav from "../../shared/components/TopNav";
import Brand from "../../shared/components/Brand";
import OmniaLogo from "../../shared/components/OmniaLogo";

/**
 * OMNIA Landing — Brand Lab palette (Mediterranean Future).
 */
export default function LandingApp() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);

  const pillars = [
    {
      key: "cloud",
      title: t("landing.pillar_cloud_title"),
      desc: t("landing.pillar_cloud_desc"),
      to: `/${lang}/cloud`,
      tag: "B2C",
      accent: "#1F6B5C",
    },
    {
      key: "app",
      title: t("landing.pillar_app_title"),
      desc: t("landing.pillar_app_desc"),
      to: `/${lang}/app`,
      tag: "B2B",
      accent: "#C8A653",
    },
    {
      key: "academy",
      title: t("landing.pillar_learn_title"),
      desc: t("landing.pillar_learn_desc"),
      to: null, // destinazione da definire
      tag: "Academy",
      accent: "#0B1E3F",
    },
  ];

  return (
    <div
      data-testid="landing-app"
      className="min-h-screen overflow-x-hidden text-[#0B1E3F]"
      style={{
        fontFamily: "'Fraunces', Georgia, serif",
        background:
          "radial-gradient(1200px 560px at 8% -8%, rgba(31,107,92,0.14), transparent 55%)," +
          "radial-gradient(900px 480px at 100% 0%, rgba(200,166,83,0.16), transparent 50%)," +
          "linear-gradient(180deg, #F5F1E8 0%, #eef3f1 45%, #e8eef5 100%)",
      }}
    >
      <TopNav current="landing" theme="light" />

      <section className="px-5 sm:px-8 md:px-12 lg:px-16 py-14 md:py-18 lg:py-20 max-w-screen-2xl mx-auto grid md:grid-cols-12 gap-10 md:gap-12 items-center">
        <div className="md:col-span-6 min-w-0 animate-[landingRise_0.7s_ease_both]">
          <p
            className="text-[10px] sm:text-xs font-sans uppercase tracking-[0.3em] mb-4 md:mb-6"
            style={{ color: "#1F6B5C" }}
          >
            <Brand>Real estate · Ecosystem · 2026</Brand>
          </p>
          <h1 className="text-4xl sm:text-5xl md:text-5xl lg:text-6xl leading-[1.05] tracking-tight mb-6 md:mb-8 break-words text-[#0B1E3F]">
            {t("landing.hero_title")}
          </h1>
          <p className="text-lg sm:text-xl md:text-xl font-light text-[#0B1E3F]/75 mb-8 md:mb-10 max-w-xl font-sans">
            {t("landing.hero_subtitle")}
          </p>
          <a
            data-testid="landing-cta"
            href={`/${lang}/cloud`}
            className="inline-block px-6 md:px-8 py-3 md:py-4 text-xs sm:text-sm font-sans uppercase tracking-widest text-[#0B1E3F] transition hover:brightness-105"
            style={{
              background: "linear-gradient(180deg, #d4b56a, #C8A653)",
              boxShadow: "0 14px 36px rgba(200,166,83,0.35)",
            }}
          >
            {t("landing.hero_cta")} →
          </a>
        </div>

        <aside className="md:col-span-6 min-w-0 animate-[landingRise_0.85s_ease_both]">
          <div
            data-testid="landing-hero-visual"
            className="relative overflow-hidden rounded-3xl border border-[#C8A653]/35 shadow-[0_24px_60px_rgba(11,30,63,0.18)] aspect-[4/3] md:aspect-[5/4] group"
          >
            <img
              src="/cloud/hero.jpg"
              alt="Immobile residenziale — OMNIA Real Estate Lab"
              className="absolute inset-0 h-full w-full object-cover transition duration-700 group-hover:scale-[1.03]"
              loading="eager"
            />
            <div
              className="absolute inset-0"
              style={{
                background:
                  "linear-gradient(180deg, rgba(11,30,63,0.1) 0%, rgba(11,30,63,0.35) 45%, rgba(11,30,63,0.88) 100%)",
              }}
            />
            <div className="absolute bottom-0 left-0 right-0 p-6 sm:p-8 text-center">
              <p
                className="text-white text-3xl sm:text-4xl md:text-5xl leading-[1.05] mb-3"
                style={{
                  fontFamily: "'Cormorant Garamond', 'Times New Roman', serif",
                  fontStyle: "italic",
                  fontWeight: 600,
                  textShadow: "0 2px 22px rgba(0,0,0,0.8)",
                }}
              >
                Omnia Real Estate Lab
              </p>
              <p
                className="text-white/95 text-base sm:text-lg md:text-xl leading-snug"
                style={{
                  fontFamily: "'Cormorant Garamond', 'Times New Roman', serif",
                  fontStyle: "italic",
                  fontWeight: 500,
                  letterSpacing: "0.02em",
                  textShadow: "0 2px 16px rgba(0,0,0,0.75)",
                }}
              >
                Vivi il Futuro
              </p>
            </div>
          </div>
        </aside>
      </section>

      <section className="px-5 sm:px-8 md:px-12 lg:px-16 pb-16 md:pb-20 lg:pb-24 max-w-screen-2xl mx-auto grid sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-5 lg:gap-6">
        {pillars.map((p) => {
          const className =
            "group block p-5 md:p-6 rounded-2xl border bg-[#F5F1E8]/80 backdrop-blur transition hover:-translate-y-0.5 hover:shadow-[0_18px_40px_rgba(11,30,63,0.12)] h-full";
          const style = { borderColor: `${p.accent}55` };
          const body = (
            <>
              <p
                className="text-[10px] sm:text-xs font-sans uppercase tracking-[0.3em] mb-2.5 md:mb-3"
                style={{ color: p.accent }}
              >
                <Brand>{p.tag}</Brand>
              </p>
              <h2 className="text-xl md:text-2xl tracking-tight mb-2 text-[#0B1E3F] group-hover:translate-x-1 transition-transform">
                <Brand>{p.title}</Brand>
              </h2>
              <p className="text-[#0B1E3F]/70 leading-relaxed font-sans text-sm">
                {p.desc}
              </p>
              {p.to ? (
                <span
                  className="inline-block mt-4 md:mt-5 text-[10px] sm:text-xs font-sans uppercase tracking-widest"
                  style={{ color: p.accent }}
                >
                  {t("common.next")} →
                </span>
              ) : null}
            </>
          );
          if (p.to) {
            return (
              <Link
                key={p.key}
                to={p.to}
                data-testid={`pillar-${p.key}`}
                className={className}
                style={style}
              >
                {body}
              </Link>
            );
          }
          return (
            <div
              key={p.key}
              data-testid={`pillar-${p.key}`}
              className={className}
              style={style}
            >
              {body}
            </div>
          );
        })}
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
              data-testid="footer-domain-sovereignty-link"
            >
              {t("domain_vault.policy_link")}
            </Link>
            <Link
              to={`/${lang}/verifica-dominio`}
              className="hover:text-[#C8A653] transition"
            >
              {t("domain_vault.existing_domain_verify_cta")}
            </Link>
          </div>
          <Brand className="truncate text-[#C8A653]/90">omniarealestateecosystem.it</Brand>
        </div>
      </footer>

      <style>{`
        @keyframes landingRise {
          from { opacity: 0; transform: translateY(14px); }
          to { opacity: 1; transform: none; }
        }
      `}</style>
    </div>
  );
}

import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import TopNav from "../../shared/components/TopNav";
import Brand from "../../shared/components/Brand";
import OmniaLogo from "../../shared/components/OmniaLogo";

/**
 * Omnia Academy — pagina destinazione (bozza).
 * Linea guida: professionalità + onestà intellettuale (non abilitante oggi).
 */
export default function AcademyApp() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);

  const pillars = t("academy.offer_items", { returnObjects: true });
  const pathSteps = t("academy.path_steps", { returnObjects: true });
  const legalTopics = t("academy.program_legal", { returnObjects: true });
  const techTopics = t("academy.program_tech", { returnObjects: true });
  const offerList = Array.isArray(pillars) ? pillars : [];
  const steps = Array.isArray(pathSteps) ? pathSteps : [];
  const legal = Array.isArray(legalTopics) ? legalTopics : [];
  const tech = Array.isArray(techTopics) ? techTopics : [];

  const mailto = `mailto:academy@omniarealestateecosystem.it?subject=${encodeURIComponent(
    "Info Omnia Academy"
  )}`;

  return (
    <div
      data-testid="academy-app"
      className="min-h-screen overflow-x-hidden text-[#0B1E3F]"
      style={{
        fontFamily: "'Fraunces', Georgia, serif",
        background:
          "radial-gradient(1100px 520px at 0% -10%, rgba(31,107,92,0.12), transparent 55%)," +
          "radial-gradient(900px 480px at 100% 0%, rgba(200,166,83,0.12), transparent 50%)," +
          "linear-gradient(180deg, #F5F1E8 0%, #eef3f1 50%, #e8eef5 100%)",
      }}
    >
      <TopNav current="academy" theme="light" />

      {/* Hero */}
      <section className="px-5 sm:px-8 md:px-12 lg:px-16 pt-14 md:pt-18 pb-10 md:pb-14 max-w-screen-2xl mx-auto grid md:grid-cols-12 gap-10 md:gap-12 items-center">
        <div className="md:col-span-6 min-w-0 animate-[academyRise_0.7s_ease_both]">
          <p
            className="text-[10px] sm:text-xs font-sans uppercase tracking-[0.3em] mb-4 md:mb-5"
            style={{ color: "#1F6B5C" }}
            data-testid="academy-eyebrow"
          >
            <Brand>{t("academy.eyebrow")}</Brand>
          </p>
          <h1
            className="text-4xl sm:text-5xl md:text-5xl lg:text-[3.35rem] leading-[1.06] tracking-tight mb-5 md:mb-6 text-[#0B1E3F]"
            data-testid="academy-title"
          >
            {t("academy.hero_title")}
          </h1>
          <p
            className="text-lg sm:text-xl font-light text-[#0B1E3F]/75 max-w-2xl font-sans leading-relaxed mb-8"
            data-testid="academy-desc"
          >
            {t("academy.hero_lead")}
          </p>
          <div className="flex flex-wrap gap-3 md:gap-4">
            <a
              href={mailto}
              data-testid="academy-cta-info"
              className="inline-block px-6 py-3 text-xs sm:text-sm font-sans uppercase tracking-widest text-[#0B1E3F] transition hover:brightness-105"
              style={{
                background: "linear-gradient(180deg, #d4b56a, #C8A653)",
                boxShadow: "0 14px 36px rgba(200,166,83,0.35)",
              }}
            >
              {t("academy.cta_info")} →
            </a>
            <a
              href="#academy-honesty"
              className="inline-block px-6 py-3 text-xs sm:text-sm font-sans uppercase tracking-widest border border-[#0B1E3F]/20 text-[#0B1E3F]/80 hover:border-[#0B1E3F]/45 transition"
            >
              {t("academy.cta_honesty")}
            </a>
          </div>
        </div>

        <aside className="md:col-span-6 min-w-0 animate-[academyRise_0.85s_ease_both]">
          <div
            data-testid="academy-hero-visual"
            className="relative overflow-hidden rounded-3xl border border-[#C8A653]/35 shadow-[0_24px_60px_rgba(11,30,63,0.18)] aspect-[4/3] md:aspect-[5/4] group"
          >
            <img
              src="/cloud/living.jpg"
              alt={t("academy.img_hero_alt")}
              className="absolute inset-0 h-full w-full object-cover transition duration-700 group-hover:scale-[1.03]"
              loading="eager"
            />
            <div
              className="absolute inset-0"
              style={{
                background:
                  "linear-gradient(180deg, rgba(11,30,63,0.05) 0%, rgba(11,30,63,0.2) 55%, rgba(11,30,63,0.55) 100%)",
              }}
            />
            <p
              className="absolute bottom-0 left-0 right-0 p-5 sm:p-6 text-center text-white text-xl sm:text-2xl md:text-3xl leading-tight"
              style={{
                fontFamily: "'Cormorant Garamond', Georgia, serif",
                fontStyle: "italic",
                fontWeight: 600,
                textShadow: "0 2px 18px rgba(0,0,0,0.75)",
              }}
            >
              {t("academy.img_hero_caption")}
            </p>
          </div>
        </aside>
      </section>

      {/* Onestà — banner chiaro */}
      <section
        id="academy-honesty"
        data-testid="academy-honesty"
        className="px-5 sm:px-8 md:px-12 lg:px-16 pb-12 md:pb-16 max-w-screen-2xl mx-auto animate-[academyRise_0.9s_ease_both]"
      >
        <div
          className="relative overflow-hidden rounded-3xl px-6 py-7 md:px-10 md:py-9 text-[#F5F1E8]"
          style={{
            background:
              "linear-gradient(135deg, #0B1E3F 0%, #123056 55%, #1F6B5C 140%)",
          }}
        >
          <p className="text-[10px] font-sans uppercase tracking-[0.28em] text-[#C8A653] mb-3">
            {t("academy.honesty_badge")}
          </p>
          <h2 className="text-2xl md:text-3xl tracking-tight mb-4 max-w-2xl">
            {t("academy.honesty_title")}
          </h2>
          <p className="font-sans text-sm md:text-base leading-relaxed text-[#F5F1E8]/88 max-w-3xl">
            {t("academy.honesty_body")}
          </p>
        </div>
      </section>

      {/* Problema + visual */}
      <section className="px-5 sm:px-8 md:px-12 lg:px-16 pb-14 md:pb-18 max-w-screen-2xl mx-auto grid md:grid-cols-12 gap-8 md:gap-12 items-center">
        <div className="md:col-span-5 order-2 md:order-1">
          <div className="relative overflow-hidden rounded-3xl border border-[#1F6B5C]/25 shadow-[0_18px_44px_rgba(11,30,63,0.12)] aspect-[4/5] max-h-[520px] group">
            <img
              src="/cloud/scout.jpg"
              alt={t("academy.img_problem_alt")}
              className="absolute inset-0 h-full w-full object-cover transition duration-700 group-hover:scale-[1.03]"
              loading="lazy"
            />
            <div
              className="absolute inset-0"
              style={{
                background:
                  "linear-gradient(180deg, transparent 40%, rgba(11,30,63,0.55) 100%)",
              }}
            />
          </div>
        </div>
        <div className="md:col-span-7 order-1 md:order-2 space-y-6">
          <div>
            <h2 className="text-2xl md:text-3xl tracking-tight mb-3">
              {t("academy.problem_title")}
            </h2>
            <p className="font-sans text-[#0B1E3F]/70 leading-relaxed text-sm md:text-base">
              {t("academy.problem_body")}
            </p>
          </div>
          <div className="space-y-5 md:space-y-6">
            {offerList.map((item, idx) => (
              <div
                key={idx}
                className="border-l-2 pl-5 md:pl-6"
                style={{ borderColor: idx === 0 ? "#1F6B5C" : "#C8A653" }}
              >
                <h3 className="text-lg md:text-xl tracking-tight mb-1.5">{item.title}</h3>
                <p className="font-sans text-sm text-[#0B1E3F]/70 leading-relaxed">
                  {item.body}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Metodo */}
      <section className="px-5 sm:px-8 md:px-12 lg:px-16 pb-14 md:pb-18 max-w-screen-2xl mx-auto">
        <div className="max-w-3xl mb-8 md:mb-10">
          <h2 className="text-2xl md:text-3xl tracking-tight mb-3">
            {t("academy.method_title")}
          </h2>
          <p className="font-sans text-[#0B1E3F]/70 leading-relaxed text-sm md:text-base">
            {t("academy.method_body")}
          </p>
        </div>
        <div className="grid sm:grid-cols-2 gap-6 md:gap-8">
          <div>
            <p
              className="text-[10px] font-sans uppercase tracking-[0.28em] mb-2"
              style={{ color: "#1F6B5C" }}
            >
              {t("academy.method_texts_label")}
            </p>
            <p className="font-sans text-sm md:text-base text-[#0B1E3F]/80 leading-relaxed">
              {t("academy.method_texts")}
            </p>
          </div>
          <div>
            <p
              className="text-[10px] font-sans uppercase tracking-[0.28em] mb-2"
              style={{ color: "#C8A653" }}
            >
              {t("academy.method_exams_label")}
            </p>
            <p className="font-sans text-sm md:text-base text-[#0B1E3F]/80 leading-relaxed">
              {t("academy.method_exams")}
            </p>
          </div>
        </div>
      </section>

      {/* Fascia atmosfera città */}
      <section
        className="relative mb-14 md:mb-18 overflow-hidden"
        aria-hidden="true"
      >
        <div className="grid grid-cols-2 md:grid-cols-4 min-h-[160px] md:min-h-[220px]">
          {[
            "/cloud/city-milano.jpg",
            "/cloud/city-roma.jpg",
            "/cloud/city-torino.jpg",
            "/cloud/city-napoli.jpg",
          ].map((src) => (
            <div key={src} className="relative overflow-hidden">
              <img
                src={src}
                alt=""
                className="absolute inset-0 h-full w-full object-cover"
                loading="lazy"
              />
            </div>
          ))}
        </div>
        <div
          className="absolute inset-0 flex items-center justify-center px-6"
          style={{
            background:
              "linear-gradient(90deg, rgba(11,30,63,0.72) 0%, rgba(11,30,63,0.45) 50%, rgba(31,107,92,0.55) 100%)",
          }}
        >
          <p
            className="text-center text-white text-2xl sm:text-3xl md:text-4xl leading-tight"
            style={{
              fontFamily: "'Cormorant Garamond', Georgia, serif",
              fontStyle: "italic",
              fontWeight: 600,
              textShadow: "0 2px 20px rgba(0,0,0,0.55)",
            }}
          >
            {t("academy.img_strip_caption")}
          </p>
        </div>
      </section>

      {/* Percorso ufficiale (educativo) */}
      <section className="px-5 sm:px-8 md:px-12 lg:px-16 pb-14 md:pb-18 max-w-screen-2xl mx-auto">
        <div className="max-w-3xl mb-8">
          <h2 className="text-2xl md:text-3xl tracking-tight mb-3">
            {t("academy.path_title")}
          </h2>
          <p className="font-sans text-sm text-[#0B1E3F]/65 leading-relaxed mb-2">
            {t("academy.path_intro")}
          </p>
          <p className="font-sans text-xs uppercase tracking-wider text-[#1F6B5C]">
            {t("academy.path_note")}
          </p>
        </div>
        <ol className="grid md:grid-cols-3 gap-6 md:gap-8 list-none p-0 m-0">
          {steps.map((step, idx) => (
            <li key={idx} className="relative">
              <span
                className="block text-4xl md:text-5xl font-light mb-3"
                style={{
                  fontFamily: "'Cormorant Garamond', Georgia, serif",
                  fontStyle: "italic",
                  color: "#C8A653",
                }}
              >
                {String(idx + 1).padStart(2, "0")}
              </span>
              <h3 className="text-lg tracking-tight mb-2">{step.title}</h3>
              <p className="font-sans text-sm text-[#0B1E3F]/70 leading-relaxed">
                {step.body}
              </p>
            </li>
          ))}
        </ol>
      </section>

      {/* Programma */}
      <section className="px-5 sm:px-8 md:px-12 lg:px-16 pb-14 md:pb-18 max-w-screen-2xl mx-auto">
        <div className="max-w-3xl mb-8">
          <h2 className="text-2xl md:text-3xl tracking-tight mb-3">
            {t("academy.program_title")}
          </h2>
          <p className="font-sans text-sm md:text-base text-[#0B1E3F]/70 leading-relaxed">
            {t("academy.program_intro")}
          </p>
        </div>
        <div className="grid md:grid-cols-2 gap-10 md:gap-14">
          <div>
            <h3
              className="text-xs font-sans uppercase tracking-[0.28em] mb-4"
              style={{ color: "#1F6B5C" }}
            >
              {t("academy.program_legal_title")}
            </h3>
            <ul className="space-y-2 font-sans text-sm text-[#0B1E3F]/80">
              {legal.map((topic) => (
                <li key={topic} className="flex gap-2">
                  <span className="text-[#C8A653] shrink-0">·</span>
                  <span>{topic}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3
              className="text-xs font-sans uppercase tracking-[0.28em] mb-4"
              style={{ color: "#C8A653" }}
            >
              {t("academy.program_tech_title")}
            </h3>
            <ul className="space-y-2 font-sans text-sm text-[#0B1E3F]/80">
              {tech.map((topic) => (
                <li key={topic} className="flex gap-2">
                  <span className="text-[#1F6B5C] shrink-0">·</span>
                  <span>{topic}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* HAL Legal */}
      <section
        data-testid="academy-hal-legal"
        className="px-5 sm:px-8 md:px-12 lg:px-16 pb-14 md:pb-18 max-w-screen-2xl mx-auto"
      >
        <div className="border-t border-[#0B1E3F]/10 pt-10 md:pt-12 grid md:grid-cols-12 gap-8 items-end">
          <div className="md:col-span-8 max-w-2xl">
            <p
              className="text-[10px] font-sans uppercase tracking-[0.28em] mb-3"
              style={{ color: "#1F6B5C" }}
            >
              <Brand>HAL Legal</Brand>
            </p>
            <h2 className="text-2xl md:text-3xl tracking-tight mb-3">
              {t("academy.hal_title")}
            </h2>
            <p className="font-sans text-sm md:text-base text-[#0B1E3F]/70 leading-relaxed mb-3">
              {t("academy.hal_body")}
            </p>
            <p className="font-sans text-xs text-[#0B1E3F]/55 leading-relaxed">
              {t("academy.hal_disclaimer")}
            </p>
          </div>
          <div className="md:col-span-4 md:text-right">
            <Link
              to={`/${lang}/legal`}
              data-testid="academy-cta-legal"
              className="inline-block px-5 py-3 text-xs font-sans uppercase tracking-widest border border-[#0B1E3F]/25 hover:border-[#0B1E3F]/50 transition"
            >
              {t("academy.cta_legal")} →
            </Link>
          </div>
        </div>
      </section>

      {/* CTA finale con foto */}
      <section className="px-5 sm:px-8 md:px-12 lg:px-16 pb-16 md:pb-20 max-w-screen-2xl mx-auto">
        <div className="relative overflow-hidden rounded-3xl border border-[#C8A653]/35 min-h-[280px] md:min-h-[320px] flex items-center justify-center text-center">
          <img
            src="/cloud/hero.jpg"
            alt={t("academy.img_closing_alt")}
            className="absolute inset-0 h-full w-full object-cover"
            loading="lazy"
          />
          <div
            className="absolute inset-0"
            style={{
              background:
                "linear-gradient(180deg, rgba(11,30,63,0.55) 0%, rgba(11,30,63,0.78) 100%)",
            }}
          />
          <div className="relative z-10 px-6 py-10 md:px-10 md:py-12 max-w-xl">
            <h2 className="text-2xl md:text-3xl tracking-tight mb-3 text-white">
              {t("academy.closing_title")}
            </h2>
            <p className="font-sans text-sm md:text-base text-white/85 mx-auto mb-6 leading-relaxed">
              {t("academy.closing_body")}
            </p>
            <a
              href={mailto}
              data-testid="academy-cta-closing"
              className="inline-block px-6 py-3 text-xs sm:text-sm font-sans uppercase tracking-widest text-[#0B1E3F] transition hover:brightness-105"
              style={{
                background: "linear-gradient(180deg, #d4b56a, #C8A653)",
                boxShadow: "0 14px 36px rgba(200,166,83,0.3)",
              }}
            >
              {t("academy.cta_info")} →
            </a>
          </div>
        </div>
      </section>

      <footer className="border-t border-[#0B1E3F]/10 bg-[#0B1E3F] text-[#F5F1E8]">
        <div
          className="max-w-screen-2xl mx-auto px-5 sm:px-8 md:px-12 lg:px-16 py-6 md:py-8 text-[10px] sm:text-xs font-sans uppercase tracking-widest text-[#F5F1E8]/70 flex flex-col sm:flex-row gap-3 sm:gap-6 sm:justify-between sm:items-center"
          data-testid="academy-footer"
        >
          <span className="flex items-center gap-2 text-[#F5F1E8]">
            <OmniaLogo variant="mark" size="sm" inverted />
            © 2026 <Brand>Omnia Academy</Brand>
          </span>
          <p className="normal-case tracking-normal text-[#F5F1E8]/55 max-w-md leading-relaxed">
            {t("academy.footer_note")}
          </p>
          <Link to={`/${lang}`} className="hover:text-[#C8A653] transition">
            {t("nav.back_to_home")}
          </Link>
        </div>
      </footer>

      <style>{`
        @keyframes academyRise {
          from { opacity: 0; transform: translateY(14px); }
          to { opacity: 1; transform: none; }
        }
      `}</style>
    </div>
  );
}

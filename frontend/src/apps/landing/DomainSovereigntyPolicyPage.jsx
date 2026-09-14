import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import LanguageSwitcher from "@/shared/components/LanguageSwitcher";
import Brand from "@/shared/components/Brand";

/**
 * M2.5.5 — Domain Sovereignty Policy (public).
 *
 * Contractual promise (D-051/D-054): OMNIA never registers a customer's
 * domain in its own name. This page is linked from:
 *   - Signup form (Domain Vault checkbox)
 *   - Landing footer (both LandingApp and AgenziesLandingPage)
 *   - Legal Kit / Domain Verify pages
 */
export default function DomainSovereigntyPolicyPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);

  const sections = ["p1", "p2", "p3", "p4", "p5", "p6"].map((k) => ({
    title: t(`domain_vault.policy_${k}_title`),
    text: t(`domain_vault.policy_${k}_text`),
  }));

  return (
    <div
      data-testid="domain-sovereignty-policy-page"
      className="min-h-screen bg-[#F5F1E8] text-[#0B1E3F]"
      style={{ fontFamily: "'Fraunces', Georgia, serif" }}
    >
      {/* Header */}
      <header className="border-b border-[#0B1E3F]/10 bg-[#F5F1E8]/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-5 sm:px-8 py-5 flex items-center justify-between">
          <Link to={`/${lang}`} className="text-lg tracking-tight">
            <Brand>OMNIA</Brand>
          </Link>
          <LanguageSwitcher />
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-3xl mx-auto px-5 sm:px-8 pt-16 pb-10">
        <p className="text-xs font-sans uppercase tracking-[0.3em] text-[#1F6B5C] mb-4">
          <Brand>Domain Vault</Brand> · M2.5.5
        </p>
        <h1
          data-testid="policy-title"
          className="text-4xl sm:text-5xl lg:text-6xl tracking-tight leading-[1.05] mb-5"
        >
          {t("domain_vault.policy_title")}
        </h1>
        <p className="text-base sm:text-lg font-sans text-[#0B1E3F]/70 leading-relaxed max-w-2xl">
          {t("domain_vault.policy_subtitle")}
        </p>
      </section>

      {/* Intro card */}
      <section className="max-w-3xl mx-auto px-5 sm:px-8 mb-10">
        <div
          className="bg-white border border-[#0B1E3F]/10 p-6 sm:p-8"
          style={{ borderLeftWidth: "3px", borderLeftColor: "#C8A653" }}
        >
          <p
            data-testid="policy-intro"
            className="text-sm sm:text-base font-sans text-[#0B1E3F]/85 leading-relaxed"
          >
            {t("domain_vault.policy_intro")}
          </p>
        </div>
      </section>

      {/* Sections */}
      <section
        data-testid="policy-sections"
        className="max-w-3xl mx-auto px-5 sm:px-8 pb-16 space-y-8"
      >
        {sections.map((s, idx) => (
          <article
            key={idx}
            data-testid={`policy-section-${idx + 1}`}
            className="bg-white border border-[#0B1E3F]/10 p-6 sm:p-8 hover:border-[#1F6B5C]/60 transition"
          >
            <h2 className="text-xl sm:text-2xl tracking-tight mb-3 text-[#0B1E3F]">
              {s.title}
            </h2>
            <p className="text-sm sm:text-base font-sans text-[#0B1E3F]/80 leading-relaxed">
              {s.text}
            </p>
          </article>
        ))}
      </section>

      {/* Footer */}
      <footer className="border-t border-[#0B1E3F]/10 bg-white/50">
        <div className="max-w-3xl mx-auto px-5 sm:px-8 py-8 text-xs sm:text-sm font-sans text-[#0B1E3F]/60 space-y-4">
          <p data-testid="policy-footer-text">{t("domain_vault.policy_footer")}</p>
          <div className="flex gap-6 pt-2 border-t border-[#0B1E3F]/10">
            <Link
              to={`/${lang}/verifica-dominio`}
              className="uppercase tracking-widest underline hover:text-[#1F6B5C]"
              data-testid="policy-footer-verify-link"
            >
              {t("domain_vault.existing_domain_verify_cta")} →
            </Link>
            <Link
              to={`/${lang}`}
              className="uppercase tracking-widest underline hover:text-[#1F6B5C]"
            >
              ← <Brand>OMNIA</Brand>
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

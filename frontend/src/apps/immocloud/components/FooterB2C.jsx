import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

export default function FooterB2C() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const links = [
    { to: `/${lang}/privacy`, label: t("cloud.footer_privacy"), testid: "footer-privacy" },
    { to: `/${lang}/cookie`, label: t("cloud.footer_cookie"), testid: "footer-cookie" },
    { to: `/${lang}/termini`, label: t("cloud.footer_terms"), testid: "footer-terms" },
  ];
  return (
    <footer className="mt-16 bg-[#0B1E3F] text-white">
      <div className="max-w-6xl mx-auto px-5 sm:px-8 md:px-16 py-10 flex flex-wrap items-end justify-between gap-6">
        <div>
          <p
            className="text-xl tracking-tight"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            ImmobilCloud<sup className="text-[9px] text-[#C19A6B] ml-0.5">™</sup>
          </p>
          <p className="text-sm text-white/60 mt-2 max-w-sm">{t("cloud.footer_tagline")}</p>
          <nav className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-xs uppercase tracking-[0.16em] text-white/70" aria-label="Legal">
            {links.map((l) => (
              <Link key={l.to} to={l.to} data-testid={l.testid} className="hover:text-[#C19A6B] transition">
                {l.label}
              </Link>
            ))}
          </nav>
        </div>
        <p className="text-xs text-white/40">© 2026 OMNIA Real Estate Ecosystem</p>
      </div>
    </footer>
  );
}

import React from "react";
import { useTranslation } from "react-i18next";

export default function FooterB2C() {
  const { t } = useTranslation();
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
        </div>
        <p className="text-xs text-white/40">© 2026 OMNIA Real Estate Ecosystem</p>
      </div>
    </footer>
  );
}

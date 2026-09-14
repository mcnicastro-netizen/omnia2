import React from "react";
import { useTranslation } from "react-i18next";

export default function FooterB2C() {
  const { t } = useTranslation();
  return (
    <footer className="border-t border-stone-200 mt-16">
      <div className="max-w-6xl mx-auto px-5 sm:px-8 md:px-16 py-8 text-xs text-stone-500 flex flex-wrap items-center justify-between gap-3">
        <span>© 2026 OMNIA Real Estate Ecosystem</span>
        <span>{t("cloud.footer_tagline")}</span>
      </div>
    </footer>
  );
}

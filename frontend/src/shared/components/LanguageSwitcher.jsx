import React from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";
import { SUPPORTED_LANGS } from "../i18n/config";
import { switchLangInPath } from "../lib/navigation";

const LANG_LABELS = {
  it: "Italiano",
  en: "English",
  es: "Español",
};

/**
 * Minimal language switcher: dropdown with native language names.
 * Uses translate="no" to prevent Chrome/Edge auto-translate hijacking labels.
 */
export default function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const current = (i18n.language || "it").slice(0, 2);

  const change = (e) => {
    const next = e.target.value;
    i18n.changeLanguage(next);
    // M1 — go through the router so LangSync & components stay in sync
    navigate(switchLangInPath(location.pathname, next) + location.search, { replace: true });
  };

  return (
    <select
      data-testid="lang-switcher"
      value={current}
      onChange={change}
      translate="no"
      className="notranslate bg-transparent border border-stone-400 rounded px-2 py-1 text-sm font-medium tracking-wider cursor-pointer hover:bg-stone-100 transition"
      aria-label="Language selector"
    >
      {SUPPORTED_LANGS.map((l) => (
        <option key={l} value={l} translate="no" className="notranslate">
          {LANG_LABELS[l]}
        </option>
      ))}
    </select>
  );
}

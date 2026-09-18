import React from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

/**
 * Pulsante "Indietro" → pagina precedente nella history in-app.
 * Se non c'è history (deep link diretto), fallback alla dashboard.
 */
export default function BackButton({
  className = "",
  fallbackTo = null,
  testId = "app-back-button",
}) {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();
  const fallback = fallbackTo || `/${lang}/app/dashboard`;

  const onBack = () => {
    const idx = window.history.state?.idx;
    if (typeof idx === "number" && idx > 0) {
      nav(-1);
      return;
    }
    nav(fallback);
  };

  return (
    <button
      type="button"
      data-testid={testId}
      onClick={onBack}
      className={`inline-flex items-center gap-1.5 text-xs uppercase tracking-widest text-stone-500 hover:text-stone-900 transition ${className}`}
      aria-label={t("common.back")}
    >
      <span aria-hidden="true">←</span>
      {t("common.back")}
    </button>
  );
}

/** True solo sulla dashboard CRM (nessun Indietro). */
export function isCrmDashboardPath(pathname = "") {
  return /\/app\/dashboard\/?$/.test(pathname);
}

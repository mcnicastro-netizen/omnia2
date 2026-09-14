import React from "react";
import { useTranslation } from "react-i18next";

/**
 * KPICard — single metric tile for the dashboard.
 * Shows label, value, optional icon, and a "coming soon" hint if locked.
 */
export default function KPICard({ kpi }) {
  const { t } = useTranslation();
  const { key, label, value, locked, icon } = kpi;

  return (
    <div
      data-testid={`kpi-${key}`}
      className={`relative p-5 md:p-6 rounded-xl border transition ${
        locked
          ? "bg-stone-100 border-stone-200 text-stone-400"
          : "bg-white border-stone-200 text-stone-900 hover:border-stone-300"
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <p className={`text-[11px] uppercase tracking-widest font-medium ${locked ? "text-stone-400" : "text-stone-500"}`}>
          {label}
        </p>
        {icon && (
          <span
            className={`text-xs ${locked ? "text-stone-300" : "text-stone-400"}`}
            aria-hidden="true"
          >
            ●
          </span>
        )}
      </div>
      <p
        className={`text-3xl md:text-4xl font-semibold tabular-nums ${locked ? "text-stone-300" : "text-stone-900"}`}
        style={{ fontFamily: "'Fraunces', Georgia, serif" }}
      >
        {locked ? "—" : value}
      </p>
      {locked && (
        <span
          data-testid={`kpi-${key}-locked`}
          className="mt-2 inline-block text-[9px] uppercase tracking-widest text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full"
        >
          {t("dashboard.kpi_coming_soon")}
        </span>
      )}
    </div>
  );
}

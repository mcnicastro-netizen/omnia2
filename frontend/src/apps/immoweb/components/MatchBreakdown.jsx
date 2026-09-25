/** A-028b — Match score breakdown (14 criteri / 100 pt). */
import React from "react";

export const CRITERION_LABELS = {
  operation: "Operazione",
  property_type: "Tipologia",
  city: "Città",
  zone: "Zona",
  price: "Prezzo",
  surface: "Superficie",
  rooms: "Locali",
  bedrooms: "Camere",
  bathrooms: "Bagni",
  conditions: "Stato",
  floor: "Piano",
  energy: "Energia",
  features: "Dotazioni",
  multimedia: "Media",
};

export function MatchBreakdownBars({ breakdown, compact = false }) {
  if (!breakdown || typeof breakdown !== "object") return null;
  const entries = Object.entries(breakdown);
  if (!entries.length) return null;
  return (
    <div
      data-testid="match-breakdown"
      className={compact ? "space-y-1" : "space-y-1.5"}
    >
      {entries.map(([key, val]) => {
        const got = Number(val?.got ?? 0);
        const max = Math.max(1, Number(val?.max ?? 1));
        const pct = Math.round((100 * got) / max);
        return (
          <div key={key} className="flex items-center gap-2 text-[10px]">
            <span className="w-20 shrink-0 text-stone-500 truncate">
              {CRITERION_LABELS[key] || key}
            </span>
            <div className="flex-1 h-1.5 bg-stone-100 rounded overflow-hidden">
              <div
                className={`h-full rounded ${got === 0 ? "bg-rose-300" : got >= max ? "bg-emerald-600" : "bg-[#0B1E3F]"}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="w-10 text-right text-stone-600 tabular-nums">
              {got}/{max}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function ScoreExplainPopover({ score, open, onClose, children }) {
  if (!open) return null;
  return (
    <div
      data-testid="score-explain-popover"
      className="absolute z-30 left-0 top-full mt-1 w-64 bg-white border border-stone-200 shadow-lg rounded-lg p-3 text-left"
      onClick={(e) => e.stopPropagation()}
    >
      <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-2">
        Cosa significa {score ?? "—"}
      </p>
      <ul className="text-[11px] text-stone-600 space-y-1 mb-2">
        <li><strong className="text-stone-900">85–100</strong> Rovente — chiama oggi</li>
        <li><strong className="text-stone-900">65–84</strong> Caldo — proponi in giornata</li>
        <li><strong className="text-stone-900">40–64</strong> Tiepido — aggiorna le preferenze</li>
        <li><strong className="text-stone-900">0–39</strong> Freddo — da riqualificare</li>
      </ul>
      {children}
      <button
        type="button"
        className="mt-2 text-[10px] uppercase tracking-widest text-stone-500 hover:text-stone-800"
        onClick={onClose}
      >
        Chiudi
      </button>
    </div>
  );
}

import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api } from "../../../shared/lib/api";

function colorForScore(score) {
  if (score >= 85) return "bg-rose-50 text-rose-700 border-rose-200";
  if (score >= 65) return "bg-orange-50 text-orange-700 border-orange-200";
  if (score >= 40) return "bg-amber-50 text-amber-700 border-amber-200";
  return "bg-stone-100 text-stone-600 border-stone-200";
}

/**
 * Compact preview of the top 3 matching CLIENTS for a given property.
 * Renders only in edit mode (when propertyId is known).
 */
export default function PropertyMatchesPreview({ propertyId, lang }) {
  const { t } = useTranslation();
  const [data, setData] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!propertyId) return;
    api.get(`/app/matches/property/${propertyId}?min_score=40&limit=3`)
      .then((r) => setData(r.data))
      .catch(() => setError(true));
  }, [propertyId]);

  if (!propertyId || error) return null;
  if (!data) return null;
  if ((data.items || []).length === 0) {
    return (
      <div data-testid="prop-matches-empty" className="bg-stone-50 border border-stone-200 rounded-md px-4 py-3 text-xs text-stone-500">
        {t("matches.no_matches_for_property") || "Nessun cliente compatibile al momento. Aggiungi clienti con preferenze coerenti per vedere i match qui."}
      </div>
    );
  }

  return (
    <div data-testid="prop-matches-preview" className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-widest text-stone-500">
          {t("matches.top_clients_for_property") || "Top clienti compatibili"}
        </span>
        <Link
          to={`/${lang}/app/matches`}
          className="text-[10px] uppercase tracking-widest text-stone-500 hover:text-stone-900"
        >
          {t("matches.see_all") || "Vedi tutti"} →
        </Link>
      </div>
      <ul className="space-y-2">
        {data.items.map((m) => (
          <li key={m.client.id}>
            <Link
              to={`/${lang}/app/matches/lead?p=${propertyId}&c=${m.client.id}`}
              data-testid={`prop-match-${m.client.id}`}
              className="flex items-center gap-3 px-3 py-2 border border-stone-200 rounded-md hover:border-stone-400 hover:bg-stone-50 transition"
            >
              <div className={`text-xs font-semibold px-2 py-1 rounded border ${colorForScore(m.score)}`}>
                {m.score}<span className="opacity-50">/100</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-stone-900 truncate">
                  {m.client.name} {m.client.surname || ""}
                </div>
                <div className="text-xs text-stone-500 truncate">
                  {t(`clients.type_${m.client.client_type}`)} · {t(`clients.status_${m.client.status}`)}
                  {m.missing && m.missing.length > 0 ? ` · mancano: ${m.missing.length}` : " · match perfetto"}
                </div>
              </div>
              <span className="text-[10px] uppercase tracking-widest text-stone-400">✨ AI</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

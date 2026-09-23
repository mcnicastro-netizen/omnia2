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
 * Match inverso (D-090): top clienti (preferenze) + richieste CRM / MLS shared.
 */
export default function PropertyMatchesPreview({ propertyId, lang }) {
  const { t } = useTranslation();
  const [data, setData] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!propertyId) return;
    api.get(`/app/matches/property/${propertyId}?min_score=40&limit=5`)
      .then((r) => setData(r.data))
      .catch(() => setError(true));
  }, [propertyId]);

  if (!propertyId || error) return null;
  if (!data) return null;

  const clients = data.items || [];
  const requests = data.requests || [];
  if (clients.length === 0 && requests.length === 0) {
    return (
      <div data-testid="prop-matches-empty" className="bg-stone-50 border border-stone-200 rounded-md px-4 py-3 text-xs text-stone-500">
        {t("matches.no_matches_for_property")}
      </div>
    );
  }

  return (
    <div data-testid="prop-matches-preview" className="space-y-4">
      {clients.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase tracking-widest text-stone-500">
              {t("matches.top_clients_for_property")}
            </span>
            <Link to={`/${lang}/app/matches`} className="text-[10px] uppercase tracking-widest text-stone-500 hover:text-stone-900">
              {t("matches.see_all")} →
            </Link>
          </div>
          <ul className="space-y-2">
            {clients.map((m) => (
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
                    </div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      {requests.length > 0 && (
        <div className="space-y-2" data-testid="prop-request-matches">
          <span className="text-xs uppercase tracking-widest text-stone-500">
            {t("matches.top_requests_for_property") || "Richieste compatibili"}
          </span>
          <ul className="space-y-2">
            {requests.map((m) => (
              <li key={m.request_id}>
                <Link
                  to={m.scope === "portfolio" ? `/${lang}/app/requests/${m.request_id}` : `/${lang}/app/requests`}
                  data-testid={`prop-request-match-${m.request_id}`}
                  className="flex items-center gap-3 px-3 py-2 border border-stone-200 rounded-md hover:border-stone-400 hover:bg-stone-50 transition"
                >
                  <div className={`text-xs font-semibold px-2 py-1 rounded border ${colorForScore(m.score)}`}>
                    {m.score}<span className="opacity-50">/100</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-stone-900 truncate">
                      {m.title || (m.client?.name ? `${m.client.name} ${m.client.surname || ""}` : m.request_id)}
                    </div>
                    <div className="text-[10px] uppercase tracking-widest text-stone-500 truncate">
                      {t(`requests.type_${m.request_type}`)} · {m.scope === "mls" ? t("requests.scope_mls") : t("requests.scope_portfolio")}
                      {m.source ? ` · ${m.source}` : ""}
                    </div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

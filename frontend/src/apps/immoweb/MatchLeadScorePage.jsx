import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams, Link } from "react-router-dom";
import AgencyShell from "./components/AgencyShell";
import { api } from "../../shared/lib/api";

function tempStyles(temp) {
  switch ((temp || "").toLowerCase()) {
    case "rovente": return { tone: "bg-rose-50 text-rose-700 border-rose-200", icon: "🔥", title: "ROVENTE" };
    case "caldo": return { tone: "bg-orange-50 text-orange-700 border-orange-200", icon: "🌶️", title: "CALDO" };
    case "tiepido": return { tone: "bg-amber-50 text-amber-700 border-amber-200", icon: "☀️", title: "TIEPIDO" };
    default: return { tone: "bg-stone-100 text-stone-600 border-stone-200", icon: "❄️", title: "FREDDO" };
  }
}

export default function MatchLeadScorePage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const [sp] = useSearchParams();
  const pid = sp.get("p");
  const cid = sp.get("c");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!pid || !cid) return;
    setData(null);
    setError("");
    api.post(`/app/matches/lead-score?property_id=${pid}&client_id=${cid}`)
      .then((r) => setData(r.data))
      .catch((e) => setError(e?.response?.data?.detail || "Errore nel calcolo del Lead Score"));
  }, [pid, cid]);

  return (
    <AgencyShell current="matches">
      <section data-testid="lead-score-page" className="max-w-3xl space-y-6">
        <div>
          <Link to={`/${lang}/app/matches`} className="text-xs uppercase tracking-widest text-stone-500 hover:text-stone-900">
            ← {t("matches.back_to_list") || "Torna ai match"}
          </Link>
          <h1
            className="text-3xl md:text-4xl tracking-tight mt-2"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            ✨ Lead Score AI
          </h1>
        </div>

        {error && (
          <p data-testid="leadscore-error" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">{String(error)}</p>
        )}

        {!data && !error && (
          <div data-testid="leadscore-loading" className="bg-white border border-stone-200 rounded-lg p-8 text-center">
            <div className="inline-block animate-pulse text-stone-500">L'AI sta valutando il lead…</div>
            <p className="text-xs text-stone-400 mt-2">Gemini-3 Flash · ~3-5 secondi</p>
          </div>
        )}

        {data && (
          <>
            {/* Score banner */}
            {(() => {
              const ts = tempStyles(data.lead_score.temperature);
              return (
                <div data-testid="leadscore-banner" className={`rounded-lg p-6 border ${ts.tone}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="text-5xl">{ts.icon}</div>
                      <div>
                        <div className="text-xs uppercase tracking-widest opacity-70">{t("matches.lead_temp") || "Temperatura lead"}</div>
                        <div className="text-2xl font-semibold">{ts.title}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-5xl font-bold" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                        {data.lead_score.score}
                        <span className="text-2xl opacity-50">/100</span>
                      </div>
                      <div className="text-[10px] uppercase tracking-widest opacity-60 mt-1">
                        engine: {data.lead_score.engine}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* Action hint */}
            {data.lead_score.action_hint && (
              <div data-testid="leadscore-action" className="bg-stone-900 text-stone-50 rounded-lg p-5">
                <div className="text-[10px] uppercase tracking-widest opacity-60 mb-1">{t("matches.next_action") || "Azione consigliata"}</div>
                <p className="text-base leading-snug">{data.lead_score.action_hint}</p>
              </div>
            )}

            {/* Reasons */}
            <div className="bg-white border border-stone-200 rounded-lg p-5">
              <div className="text-xs uppercase tracking-widest text-stone-500 mb-3">{t("matches.why") || "Perché"}</div>
              <ul className="space-y-2">
                {(data.lead_score.reasons || []).map((r, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-stone-800">
                    <span className="text-emerald-700 mt-0.5">✓</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Refs */}
            <div className="grid sm:grid-cols-2 gap-4">
              <Link
                to={`/${lang}/app/properties/${data.property.id}`}
                className="bg-white border border-stone-200 rounded-lg p-4 hover:border-stone-400"
              >
                <div className="text-[10px] uppercase tracking-widest text-stone-500 mb-1">{t("matches.property") || "Immobile"}</div>
                <div className="font-semibold text-stone-900">{data.property.title}</div>
                <div className="text-xs text-stone-500 mt-1">
                  {data.property.city} · {data.property.surface_sqm} m² · {data.property.rooms} loc.
                </div>
                <div className="text-sm font-medium text-stone-900 mt-2" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                  {data.property.price ? new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(data.property.price) : (data.property.rent_monthly ? `${new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(data.property.rent_monthly)}/mese` : "—")}
                </div>
              </Link>
              <Link
                to={`/${lang}/app/clients/${data.client.id}`}
                className="bg-white border border-stone-200 rounded-lg p-4 hover:border-stone-400"
              >
                <div className="text-[10px] uppercase tracking-widest text-stone-500 mb-1">{t("matches.client") || "Cliente"}</div>
                <div className="font-semibold text-stone-900">{data.client.name} {data.client.surname || ""}</div>
                <div className="text-xs text-stone-500 mt-1">
                  {t(`clients.type_${data.client.client_type}`)} · {t(`clients.status_${data.client.status}`)}
                </div>
                <div className="text-xs text-stone-500 mt-2">
                  {data.client.email}{data.client.phone ? ` · ${data.client.phone}` : ""}
                </div>
              </Link>
            </div>

            {/* Deterministic breakdown */}
            <details className="bg-white border border-stone-200 rounded-lg p-4">
              <summary className="cursor-pointer text-xs uppercase tracking-widest text-stone-500">
                {t("matches.match_detail") || "Dettaglio match deterministico"} ({data.match.score}/100)
              </summary>
              <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                {Object.entries(data.match.breakdown || {}).map(([k, v]) => (
                  <div key={k} className={`flex items-center justify-between px-2 py-1.5 rounded ${v.got === v.max ? "bg-emerald-50" : v.got === 0 ? "bg-red-50" : "bg-amber-50"}`}>
                    <span className="text-stone-700">{k}</span>
                    <span className="font-medium">{v.got}/{v.max}</span>
                  </div>
                ))}
              </div>
            </details>
          </>
        )}
      </section>
    </AgencyShell>
  );
}

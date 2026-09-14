import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, Link } from "react-router-dom";
import AgencyShell from "./components/AgencyShell";
import { api } from "../../shared/lib/api";

function formatPrice(v) {
  if (v == null) return "—";
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(v);
}

function scoreColors(score) {
  if (score >= 85) return { bg: "bg-rose-50", text: "text-rose-700", border: "border-rose-200", label: "ROVENTE" };
  if (score >= 65) return { bg: "bg-orange-50", text: "text-orange-700", border: "border-orange-200", label: "CALDO" };
  if (score >= 40) return { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200", label: "TIEPIDO" };
  return { bg: "bg-stone-100", text: "text-stone-500", border: "border-stone-200", label: "FREDDO" };
}

export default function MatchesPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();
  const [data, setData] = useState({ items: [], total: 0, min_score: 50 });
  const [loading, setLoading] = useState(true);
  const [minScore, setMinScore] = useState(50);

  const load = async (score = minScore) => {
    setLoading(true);
    try {
      const { data } = await api.get(`/app/matches?min_score=${score}&limit=100`);
      setData(data);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    load(minScore);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <AgencyShell current="matches">
      <section data-testid="matches-page" className="space-y-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1
              className="text-3xl md:text-4xl tracking-tight"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {t("matches.title") || "Match"}
            </h1>
            <p className="text-stone-600 mt-1">{t("matches.subtitle") || "Cross-reference automatico tra i tuoi immobili e i tuoi clienti."}</p>
          </div>
          <div className="flex items-center gap-3">
            <label className="text-xs uppercase tracking-widest text-stone-500">
              {t("matches.min_score") || "Score minimo"}
            </label>
            <select
              data-testid="min-score-filter"
              value={minScore}
              onChange={(e) => { const v = parseInt(e.target.value, 10); setMinScore(v); load(v); }}
              className="px-3 py-2 border border-stone-300 rounded-md text-sm"
            >
              <option value={40}>{`40+ ${t("matches.warm") || "tiepidi"}`}</option>
              <option value={50}>{`50+ ${t("matches.good") || "buoni"}`}</option>
              <option value={65}>{`65+ ${t("matches.hot") || "caldi"}`}</option>
              <option value={85}>{`85+ ${t("matches.blazing") || "roventi"}`}</option>
            </select>
          </div>
        </div>

        {loading ? (
          <p className="text-stone-500 text-sm">{t("common.loading")}</p>
        ) : data.items.length === 0 ? (
          <div data-testid="matches-empty" className="bg-white border border-stone-200 rounded-lg p-12 text-center">
            <p
              className="text-2xl mb-2"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {t("matches.empty_title") || "Nessun match al momento"}
            </p>
            <p className="text-stone-500 max-w-md mx-auto">
              {t("matches.empty_subtitle") || "Aggiungi più immobili e clienti — i match si calcolano automaticamente."}
            </p>
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.items.map((m) => {
              const sc = scoreColors(m.score);
              const p = m.property;
              const c = m.client;
              return (
                <div
                  key={`${p.id}-${c.id}`}
                  data-testid={`match-card-${p.id}-${c.id}`}
                  className="bg-white border border-stone-200 rounded-lg overflow-hidden hover:border-stone-400 transition"
                >
                  <div className={`flex items-center justify-between px-4 py-2 border-b ${sc.bg} ${sc.border}`}>
                    <span className={`text-xs uppercase tracking-widest font-semibold ${sc.text}`}>
                      {sc.label}
                    </span>
                    <span className={`text-2xl font-bold ${sc.text}`} style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                      {m.score}<span className="text-sm">/100</span>
                    </span>
                  </div>
                  <div className="p-4">
                    <Link
                      to={`/${lang}/app/properties/${p.id}`}
                      className="block mb-3 hover:bg-stone-50 -mx-2 -my-1 px-2 py-1 rounded"
                    >
                      <div className="text-[10px] uppercase tracking-widest text-stone-500 mb-0.5">{t("matches.property") || "Immobile"}</div>
                      <div className="font-semibold text-stone-900 line-clamp-1">{p.title}</div>
                      <div className="text-xs text-stone-500">{p.city} · {formatPrice(p.price || p.rent_monthly)} · {p.surface_sqm ? `${p.surface_sqm} m²` : "—"}</div>
                    </Link>
                    <div className="border-t border-stone-100 pt-3">
                      <Link
                        to={`/${lang}/app/clients/${c.id}`}
                        className="block hover:bg-stone-50 -mx-2 -my-1 px-2 py-1 rounded"
                      >
                        <div className="text-[10px] uppercase tracking-widest text-stone-500 mb-0.5">{t("matches.client") || "Cliente"}</div>
                        <div className="font-medium text-stone-900">{c.name} {c.surname || ""}</div>
                        <div className="text-xs text-stone-500">{c.email || c.phone || "—"} · {t(`clients.type_${c.client_type}`)} · {t(`clients.status_${c.status}`)}</div>
                      </Link>
                    </div>
                    {m.missing && m.missing.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-stone-100">
                        <div className="text-[10px] uppercase tracking-widest text-stone-500 mb-1">{t("matches.missing") || "Mancano"}</div>
                        <div className="flex flex-wrap gap-1">
                          {m.missing.slice(0, 4).map((mi) => (
                            <span key={mi} className="text-[10px] px-2 py-0.5 rounded bg-stone-100 text-stone-600">
                              {mi.split(":")[0]}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    <button
                      type="button"
                      data-testid={`leadscore-btn-${p.id}-${c.id}`}
                      onClick={() => nav(`/${lang}/app/matches/lead?p=${p.id}&c=${c.id}`)}
                      className="mt-4 w-full text-xs uppercase tracking-widest font-medium border border-stone-300 rounded-md py-2 hover:bg-stone-50"
                    >
                      ✨ {t("matches.ai_score_btn") || "Calcola Lead Score AI"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </AgencyShell>
  );
}

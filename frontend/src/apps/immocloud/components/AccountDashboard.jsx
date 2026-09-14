/* OMNIA — B2C Account Dashboard (M3.S7)
 *
 * Authenticated B2C user dashboard. Tabs:
 *   1. Ricerche salvate — manage saved searches + see last match count
 *   2. (future) Annunci pubblicati, Notifiche, Profilo
 *
 * Path: /it/cloud/account
 */
import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import { useAuth, formatApiErrorDetail } from "../../../shared/lib/auth";

const FREQ_OPTIONS = [
  { v: "instant", k: "cloud.account.freq_instant" },
  { v: "daily", k: "cloud.account.freq_daily" },
  { v: "weekly", k: "cloud.account.freq_weekly" },
];

export default function AccountDashboard() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();
  const { user } = useAuth();
  const [searches, setSearches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user === null) return;
    if (!user || user.account_type !== "b2c") {
      nav(`/${lang}/cloud/register`, { replace: true });
      return;
    }
    api.get("/cloud/me/saved-searches")
      .then((r) => setSearches(r.data.items || []))
      .catch((e) => setError(formatApiErrorDetail(e?.response?.data?.detail)))
      .finally(() => setLoading(false));
  }, [user, lang, nav]);

  const toggleActive = async (sid, active) => {
    try {
      await api.patch(`/cloud/me/saved-searches/${sid}`, { is_active: active });
      setSearches((arr) => arr.map((s) => s.id === sid ? { ...s, is_active: active } : s));
    } catch (e) {
      setError(formatApiErrorDetail(e?.response?.data?.detail));
    }
  };

  const changeFreq = async (sid, frequency) => {
    try {
      await api.patch(`/cloud/me/saved-searches/${sid}`, { frequency });
      setSearches((arr) => arr.map((s) => s.id === sid ? { ...s, frequency } : s));
    } catch (e) {
      setError(formatApiErrorDetail(e?.response?.data?.detail));
    }
  };

  const remove = async (sid) => {
    if (!window.confirm(t("cloud.account.confirm_delete"))) return;
    try {
      await api.delete(`/cloud/me/saved-searches/${sid}`);
      setSearches((arr) => arr.filter((s) => s.id !== sid));
    } catch (e) {
      setError(formatApiErrorDetail(e?.response?.data?.detail));
    }
  };

  if (user === null || loading) {
    return <div className="max-w-4xl mx-auto p-6 text-stone-500 text-sm">{t("common.loading")}</div>;
  }

  return (
    <div data-testid="account-dashboard" className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      <header className="mb-8">
        <p className="text-xs uppercase tracking-widest text-[#C19A6B] font-semibold mb-2">
          {t("cloud.account.eyebrow")}
        </p>
        <h1 className="text-3xl md:text-5xl font-light tracking-tight" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
          {t("cloud.account.title", { name: user.name || "" })}
        </h1>
        <p className="text-stone-600 text-base mt-2">{t("cloud.account.subtitle")}</p>
      </header>

      {error && (
        <div data-testid="account-error" className="mb-4 text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded px-3 py-2">
          {error}
        </div>
      )}

      <section data-testid="saved-searches-section">
        <div className="flex items-baseline justify-between mb-4">
          <h2 className="text-xl font-light tracking-tight" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            {t("cloud.account.saved_searches_title")}
          </h2>
          <Link to={`/${lang}/cloud/search`} className="text-xs uppercase tracking-widest text-[#0B1E3F] hover:text-[#C19A6B]">
            + {t("cloud.account.new_search")}
          </Link>
        </div>

        {searches.length === 0 ? (
          <div data-testid="ss-empty" className="bg-white border border-stone-200 rounded-lg p-8 text-center">
            <p className="text-stone-500 text-sm mb-4">{t("cloud.account.ss_empty_desc")}</p>
            <Link
              to={`/${lang}/cloud/search`}
              data-testid="ss-empty-cta"
              className="inline-block px-6 py-2.5 bg-[#0B1E3F] text-white text-sm uppercase tracking-widest rounded hover:bg-[#C19A6B] transition"
            >
              {t("cloud.account.ss_empty_cta")}
            </Link>
          </div>
        ) : (
          <ul className="space-y-3">
            {searches.map((s) => (
              <li
                key={s.id}
                data-testid={`ss-row-${s.id}`}
                className="bg-white border border-stone-200 rounded-lg p-5 flex items-start justify-between gap-4 flex-wrap"
              >
                <div className="min-w-0 flex-1">
                  <h3 className="text-base font-medium text-stone-900 mb-1">{s.name}</h3>
                  <p className="text-xs text-stone-600 mb-2">
                    {Object.entries(s.filters).map(([k, v]) => (
                      <span key={k} className="inline-block mr-2 mb-1 px-2 py-0.5 bg-stone-100 rounded text-[10px] uppercase tracking-wider">
                        {k}: <strong>{String(v)}</strong>
                      </span>
                    ))}
                  </p>
                  {s.last_match_count !== undefined && s.last_run_at && (
                    <p className="text-[11px] text-stone-500">
                      {t("cloud.account.last_matches", { count: s.last_match_count })}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <select
                    data-testid={`ss-freq-${s.id}`}
                    value={s.frequency}
                    onChange={(e) => changeFreq(s.id, e.target.value)}
                    className="text-[11px] uppercase tracking-widest border border-stone-300 rounded px-2 py-1.5"
                  >
                    {FREQ_OPTIONS.map((o) => (
                      <option key={o.v} value={o.v}>{t(o.k)}</option>
                    ))}
                  </select>
                  <label className="inline-flex items-center gap-1.5 text-[11px] uppercase tracking-widest text-stone-600 cursor-pointer">
                    <input
                      type="checkbox"
                      data-testid={`ss-toggle-${s.id}`}
                      checked={!!s.is_active}
                      onChange={(e) => toggleActive(s.id, e.target.checked)}
                    />
                    {t("cloud.account.active")}
                  </label>
                  <button
                    data-testid={`ss-delete-${s.id}`}
                    onClick={() => remove(s.id)}
                    className="text-[11px] uppercase tracking-widest text-rose-700 border border-rose-200 rounded px-3 py-1.5 hover:bg-rose-50"
                  >
                    {t("common.delete")}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

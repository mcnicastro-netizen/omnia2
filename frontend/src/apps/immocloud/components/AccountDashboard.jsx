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
import NotificationPreferencesPanel from "../../../shared/components/NotificationPreferencesPanel";
import SecuritySettingsPanel from "../../../shared/components/SecuritySettingsPanel";
import CloudPageHero from "./CloudPageHero";

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
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user === null) return;
    if (!user || user.account_type !== "b2c") {
      nav(`/${lang}/cloud/register`, { replace: true });
      return;
    }
    Promise.all([
      api.get("/cloud/me/saved-searches").then((r) => setSearches(r.data.items || [])),
      api.get("/cloud/me/favorites").then((r) => setFavorites(r.data.items || [])).catch(() => setFavorites([])),
    ])
      .catch((e) => setError(formatApiErrorDetail(e?.response?.data?.detail)))
      .finally(() => setLoading(false));
  }, [user, lang, nav]);

  const toggleActive = async (sid, active) => {
    try {
      await api.patch(`/cloud/me/saved-searches/${sid}`, { is_active: active });
      setSearches((arr) => arr.map((s) => (s.id === sid ? { ...s, is_active: active } : s)));
    } catch (e) {
      setError(formatApiErrorDetail(e?.response?.data?.detail));
    }
  };

  const changeFreq = async (sid, frequency) => {
    try {
      await api.patch(`/cloud/me/saved-searches/${sid}`, { frequency });
      setSearches((arr) => arr.map((s) => (s.id === sid ? { ...s, frequency } : s)));
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
    return (
      <div className="max-w-4xl mx-auto px-5 py-16">
        <div className="rounded-2xl bg-[#f7f4ef] border border-stone-200 px-6 py-12 text-center text-stone-500 text-sm">
          {t("common.loading")}
        </div>
      </div>
    );
  }

  return (
    <div data-testid="account-dashboard">
      <CloudPageHero
        eyebrow={t("cloud.account.eyebrow")}
        title={t("cloud.account.title", { name: user.name || "" })}
        subtitle={t("cloud.account.subtitle")}
        image="/cloud/scout.jpg"
        compact
      />

      <div className="max-w-5xl mx-auto px-5 sm:px-8 md:px-16 py-10">
        {error && (
          <div data-testid="account-error" className="mb-6 text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-xl px-4 py-3">
            {error}
          </div>
        )}

        <section data-testid="saved-searches-section">
          <div className="flex items-baseline justify-between mb-5">
            <h2
              className="text-2xl font-light tracking-tight text-[#0B1E3F]"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {t("cloud.account.saved_searches_title")}
            </h2>
            <Link
              to={`/${lang}/cloud/search`}
              className="text-xs uppercase tracking-widest text-[#0B1E3F] hover:text-[#C19A6B]"
            >
              + {t("cloud.account.new_search")}
            </Link>
          </div>

          {searches.length === 0 ? (
            <div data-testid="ss-empty" className="bg-[#f7f4ef] border border-stone-200 rounded-2xl p-10 text-center">
              <p className="text-stone-600 text-sm mb-5">{t("cloud.account.ss_empty_desc")}</p>
              <Link
                to={`/${lang}/cloud/search`}
                data-testid="ss-empty-cta"
                className="inline-block px-6 py-2.5 bg-[#0B1E3F] text-white text-sm uppercase tracking-widest rounded-lg hover:bg-[#C19A6B] transition"
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
                  className="bg-white border border-stone-200 rounded-2xl p-5 flex items-start justify-between gap-4 flex-wrap"
                >
                  <div className="min-w-0 flex-1">
                    <h3 className="text-base font-medium text-stone-900 mb-1">{s.name}</h3>
                    <p className="text-xs text-stone-600 mb-2">
                      {Object.entries(s.filters).map(([k, v]) => (
                        <span
                          key={k}
                          className="inline-block mr-2 mb-1 px-2 py-0.5 bg-[#f7f4ef] rounded text-[10px] uppercase tracking-wider"
                        >
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
                      className="text-[11px] uppercase tracking-widest border border-stone-200 rounded-lg px-2 py-1.5"
                    >
                      {FREQ_OPTIONS.map((o) => (
                        <option key={o.v} value={o.v}>
                          {t(o.k)}
                        </option>
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
                      className="text-[11px] uppercase tracking-widest text-rose-700 border border-rose-200 rounded-lg px-3 py-1.5 hover:bg-rose-50"
                    >
                      {t("common.delete")}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section data-testid="favorites-section" className="mt-12">
          <h2
            className="text-2xl font-light tracking-tight mb-5 text-[#0B1E3F]"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            Preferiti
          </h2>
          {favorites.length === 0 ? (
            <p className="text-sm text-stone-500 rounded-2xl bg-[#f7f4ef] border border-stone-200 px-5 py-8">
              Nessun immobile nei preferiti. Aprine uno e clicca ★ Salva.
            </p>
          ) : (
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {favorites.map((p) => (
                <li key={p.id} className="border border-stone-200 rounded-2xl p-5 bg-white">
                  <div className="flex items-start justify-between gap-2">
                    <Link
                      to={`/${lang}/cloud/property/${p.id}`}
                      className="font-medium text-[#0B1E3F] hover:text-[#C19A6B]"
                    >
                      {p.title || p.property_type}
                    </Link>
                    {p.listing_ended && (
                      <span
                        data-testid={`fav-ended-${p.id}`}
                        className="shrink-0 text-[10px] uppercase tracking-widest px-2 py-0.5 rounded border border-stone-300 text-stone-600 bg-stone-50"
                      >
                        {p.listing_end_status === "sold"
                          ? "Venduto"
                          : p.listing_end_status === "rented"
                            ? "Affittato"
                            : "Ritirato"}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-stone-500 mt-1">
                    {p.city}
                    {p.price ? ` · € ${Number(p.price).toLocaleString("it-IT")}` : ""}
                  </p>
                  <button
                    type="button"
                    className="mt-3 text-[11px] uppercase tracking-widest text-rose-700"
                    onClick={async () => {
                      await api.delete(`/cloud/me/favorites/${p.id}`);
                      setFavorites((arr) => arr.filter((x) => x.id !== p.id));
                    }}
                  >
                    Rimuovi
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section
          data-testid="account-notifications"
          className="mt-12 border border-stone-200 bg-white rounded-2xl p-6 md:p-8 space-y-3"
        >
          <h2
            className="text-2xl font-light tracking-tight text-[#0B1E3F]"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            Notifiche
          </h2>
          <p className="text-sm text-stone-600">
            Scegli come e quando ricevere aggiornamenti su ImmobilCloud.
          </p>
          <NotificationPreferencesPanel showSavedSearchFreq />
        </section>

        <div className="mt-10">
          <SecuritySettingsPanel variant="cloud" />
        </div>
      </div>
    </div>
  );
}

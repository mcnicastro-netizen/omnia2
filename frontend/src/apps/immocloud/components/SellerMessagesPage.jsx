/* OMNIA — B2C seller inquiry inbox (D-138 Idealista+)
 * Path: /it/cloud/account/messages
 */
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import { useAuth, formatApiErrorDetail } from "../../../shared/lib/auth";
import CloudPageHero from "./CloudPageHero";

const FILTERS = ["open", "unread", "visits", "archived", "all"];

function waHref(raw) {
  const digits = String(raw || "").replace(/\D/g, "");
  if (!digits) return null;
  const withCc = digits.startsWith("39") || digits.length > 10 ? digits : `39${digits}`;
  return `https://wa.me/${withCc}`;
}

function mailtoHref(email, title, lang) {
  if (!email) return null;
  const subject = encodeURIComponent(
    lang === "en" ? `Re: ${title || "your inquiry"}` : `Re: ${title || "la tua richiesta"}`,
  );
  return `mailto:${email}?subject=${subject}`;
}

export default function SellerMessagesPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const filter = FILTERS.includes(params.get("filter")) ? params.get("filter") : "open";
  const focusId = params.get("id") || "";

  const [items, setItems] = useState([]);
  const [summary, setSummary] = useState({ unread: 0, visits_pending: 0, open: 0, total: 0 });
  const [selectedId, setSelectedId] = useState(focusId);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState("");
  const [noteDraft, setNoteDraft] = useState("");

  useEffect(() => {
    if (user === null) return;
    if (!user || user.account_type !== "b2c") {
      nav(`/${lang}/cloud/area?next=${encodeURIComponent(`/${lang}/cloud/account/messages`)}`, {
        replace: true,
      });
    }
  }, [user, lang, nav]);

  const load = useCallback(async () => {
    setError("");
    try {
      const [listRes, sumRes] = await Promise.all([
        api.get("/cloud/me/inquiries", { params: { filter, limit: 80 } }),
        api.get("/cloud/me/inquiries/summary"),
      ]);
      setItems(listRes.data.items || []);
      setSummary(sumRes.data || {});
    } catch (e) {
      setError(formatApiErrorDetail(e?.response?.data?.detail) || t("cloud.messages.err_load"));
    } finally {
      setLoading(false);
    }
  }, [filter, t]);

  useEffect(() => {
    if (!user || user.account_type !== "b2c") return;
    setLoading(true);
    load();
  }, [user, load]);

  useEffect(() => {
    if (focusId) setSelectedId(focusId);
  }, [focusId]);

  const selected = useMemo(
    () => items.find((it) => it.id === selectedId) || items[0] || null,
    [items, selectedId],
  );

  useEffect(() => {
    if (selected) setNoteDraft(selected.seller_note || "");
  }, [selected?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!selected || selected.is_read) return undefined;
    let cancelled = false;
    (async () => {
      try {
        const { data } = await api.patch(`/cloud/me/inquiries/${selected.id}`, { read: true });
        if (cancelled) return;
        const item = data.item;
        setItems((arr) => arr.map((x) => (x.id === item.id ? item : x)));
        setSummary((s) => ({ ...s, unread: Math.max(0, (s.unread || 0) - 1) }));
      } catch {
        /* non-blocking */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [selected?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const setFilter = (f) => {
    const next = new URLSearchParams(params);
    next.set("filter", f);
    next.delete("id");
    setParams(next, { replace: true });
    setSelectedId("");
  };

  const patch = async (id, body) => {
    setBusyId(id);
    setError("");
    try {
      const { data } = await api.patch(`/cloud/me/inquiries/${id}`, body);
      const item = data.item;
      setItems((arr) => {
        if (filter === "open" && item.archived) return arr.filter((x) => x.id !== id);
        if (filter === "unread" && item.is_read) return arr.filter((x) => x.id !== id);
        if (filter === "archived" && !item.archived) return arr.filter((x) => x.id !== id);
        return arr.map((x) => (x.id === id ? item : x));
      });
      await api.get("/cloud/me/inquiries/summary").then((r) => setSummary(r.data || {}));
      return item;
    } catch (e) {
      setError(formatApiErrorDetail(e?.response?.data?.detail) || t("cloud.messages.err_save"));
      return null;
    } finally {
      setBusyId("");
    }
  };

  if (user === null || (loading && !items.length)) {
    return (
      <div className="max-w-4xl mx-auto px-5 py-16 text-center text-stone-500 text-sm">
        {t("common.loading")}
      </div>
    );
  }

  return (
    <div data-testid="seller-messages-page">
      <CloudPageHero
        eyebrow={t("cloud.messages.eyebrow")}
        title={t("cloud.messages.title")}
        subtitle={t("cloud.messages.subtitle")}
        image="/cloud/scout.jpg"
        compact
      />

      <div className="max-w-6xl mx-auto px-5 sm:px-8 md:px-12 py-8">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
          <div className="flex flex-wrap gap-2 text-[11px] uppercase tracking-widest">
            <Link
              to={`/${lang}/cloud/account`}
              className="px-3 py-2 border border-stone-300 rounded-lg text-stone-600 hover:border-[#0B1E3F]"
            >
              {t("cloud.messages.back_account")}
            </Link>
            <Link
              to={`/${lang}/cloud/account/sell`}
              className="px-3 py-2 border border-stone-300 rounded-lg text-stone-600 hover:border-[#0B1E3F]"
            >
              {t("cloud.messages.back_sell")}
            </Link>
          </div>
          <div className="flex flex-wrap gap-3 text-xs text-stone-600" data-testid="messages-summary">
            <span>{t("cloud.messages.sum_unread", { n: summary.unread || 0 })}</span>
            <span>·</span>
            <span>{t("cloud.messages.sum_visits", { n: summary.visits_pending || 0 })}</span>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mb-5" data-testid="messages-filters">
          {FILTERS.map((f) => (
            <button
              key={f}
              type="button"
              data-testid={`messages-filter-${f}`}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 text-[11px] uppercase tracking-widest rounded-lg border transition ${
                filter === f
                  ? "bg-[#0B1E3F] text-white border-[#0B1E3F]"
                  : "border-stone-300 text-stone-600 hover:border-[#0B1E3F]"
              }`}
            >
              {t(`cloud.messages.filter_${f}`)}
            </button>
          ))}
        </div>

        {error && (
          <div className="mb-4 text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-xl px-4 py-3">
            {error}
          </div>
        )}

        {!items.length ? (
          <div
            data-testid="messages-empty"
            className="rounded-2xl border border-stone-200 bg-white px-6 py-14 text-center"
          >
            <p className="text-sm text-stone-600 mb-4">{t("cloud.messages.empty")}</p>
            <Link
              to={`/${lang}/cloud/account/sell`}
              className="inline-block px-5 py-2.5 bg-[#0B1E3F] text-white text-xs uppercase tracking-widest rounded-lg"
            >
              {t("cloud.messages.empty_cta")}
            </Link>
          </div>
        ) : (
          <div className="grid lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)] gap-4">
            <ul
              data-testid="messages-list"
              className="border border-stone-200 rounded-2xl bg-white divide-y divide-stone-100 overflow-hidden max-h-[70vh] overflow-y-auto"
            >
              {items.map((it) => {
                const active = selected?.id === it.id;
                return (
                  <li key={it.id}>
                    <button
                      type="button"
                      data-testid={`messages-item-${it.id}`}
                      onClick={() => {
                        setSelectedId(it.id);
                        const next = new URLSearchParams(params);
                        next.set("id", it.id);
                        setParams(next, { replace: true });
                      }}
                      className={`w-full text-left px-4 py-3 transition ${
                        active ? "bg-[#f7f4ef]" : "hover:bg-stone-50"
                      } ${!it.is_read ? "border-l-2 border-l-[#C19A6B]" : "border-l-2 border-l-transparent"}`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className={`text-sm ${it.is_read ? "text-stone-700" : "text-[#0B1E3F] font-medium"}`}>
                          {[it.name, it.surname].filter(Boolean).join(" ") || it.email}
                        </p>
                        <time className="text-[10px] text-stone-400 shrink-0">
                          {it.created_at
                            ? new Date(it.created_at).toLocaleDateString(lang, {
                                day: "2-digit",
                                month: "short",
                              })
                            : ""}
                        </time>
                      </div>
                      <p className="text-[11px] text-stone-500 mt-0.5 truncate">
                        {it.property_title}
                        {it.property_city ? ` · ${it.property_city}` : ""}
                      </p>
                      <p className="text-xs text-stone-600 mt-1 line-clamp-2">{it.message}</p>
                      {it.visit_requested && (
                        <span className="inline-block mt-2 text-[10px] uppercase tracking-widest text-amber-800 bg-amber-50 border border-amber-200 rounded px-2 py-0.5">
                          {t(`cloud.messages.visit_${it.visit_status || "requested"}`)}
                        </span>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>

            {selected && (
              <article
                data-testid="messages-detail"
                className="border border-stone-200 rounded-2xl bg-white p-5 sm:p-6 space-y-5"
              >
                <header>
                  <p className="text-[10px] uppercase tracking-widest text-[#C19A6B] mb-1">
                    {selected.listing_code || selected.property_id?.slice(0, 8)}
                  </p>
                  <h2
                    className="text-xl font-light text-[#0B1E3F] tracking-tight"
                    style={{ fontFamily: "'Fraunces', Georgia, serif" }}
                  >
                    {[selected.name, selected.surname].filter(Boolean).join(" ")}
                  </h2>
                  <p className="text-sm text-stone-500 mt-1">
                    {selected.property_title}
                    {selected.property_city ? ` · ${selected.property_city}` : ""}
                  </p>
                </header>

                <div className="rounded-xl bg-[#f7f4ef] border border-stone-200 px-4 py-3 text-sm text-stone-800 whitespace-pre-wrap">
                  {selected.message}
                </div>

                <div className="flex flex-wrap gap-2 text-[11px] uppercase tracking-widest">
                  {selected.email && (
                    <a
                      data-testid="messages-reply-email"
                      href={mailtoHref(selected.email, selected.property_title, lang)}
                      className="px-3 py-2 bg-[#0B1E3F] text-white rounded-lg hover:bg-[#C19A6B]"
                    >
                      {t("cloud.messages.reply_email")}
                    </a>
                  )}
                  {selected.phone && (
                    <a
                      data-testid="messages-reply-phone"
                      href={`tel:${selected.phone}`}
                      className="px-3 py-2 border border-stone-300 rounded-lg text-stone-700 hover:border-[#0B1E3F]"
                    >
                      {t("cloud.messages.reply_phone")}
                    </a>
                  )}
                  {selected.phone && waHref(selected.phone) && (
                    <a
                      data-testid="messages-reply-wa"
                      href={waHref(selected.phone)}
                      target="_blank"
                      rel="noreferrer"
                      className="px-3 py-2 border border-stone-300 rounded-lg text-stone-700 hover:border-[#0B1E3F]"
                    >
                      {t("cloud.messages.reply_wa")}
                    </a>
                  )}
                </div>

                <div className="text-sm text-stone-600 space-y-1">
                  <p>
                    <span className="text-[10px] uppercase tracking-widest text-stone-400 mr-2">Email</span>
                    {selected.email || "—"}
                  </p>
                  <p>
                    <span className="text-[10px] uppercase tracking-widest text-stone-400 mr-2">Tel</span>
                    {selected.phone || "—"}
                  </p>
                </div>

                {selected.visit_requested && (
                  <section data-testid="messages-visit-actions" className="space-y-2">
                    <h3 className="text-[10px] uppercase tracking-widest text-stone-500">
                      {t("cloud.messages.visit_manage")}
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {["accepted", "declined", "completed"].map((st) => (
                        <button
                          key={st}
                          type="button"
                          disabled={busyId === selected.id}
                          data-testid={`messages-visit-${st}`}
                          onClick={() => patch(selected.id, { visit_status: st })}
                          className={`px-3 py-1.5 text-[11px] uppercase tracking-widest rounded-lg border ${
                            selected.visit_status === st
                              ? "bg-[#0B1E3F] text-white border-[#0B1E3F]"
                              : "border-stone-300 text-stone-700 hover:border-[#0B1E3F]"
                          } disabled:opacity-50`}
                        >
                          {t(`cloud.messages.visit_btn_${st}`)}
                        </button>
                      ))}
                    </div>
                  </section>
                )}

                <section className="space-y-2">
                  <label className="block">
                    <span className="text-[10px] uppercase tracking-widest text-stone-500">
                      {t("cloud.messages.seller_note")}
                    </span>
                    <textarea
                      data-testid="messages-seller-note"
                      rows={3}
                      value={noteDraft}
                      onChange={(e) => setNoteDraft(e.target.value)}
                      className="mt-1 w-full px-3 py-2 border border-stone-200 rounded-lg text-sm"
                      placeholder={t("cloud.messages.seller_note_ph")}
                    />
                  </label>
                  <button
                    type="button"
                    data-testid="messages-save-note"
                    disabled={busyId === selected.id}
                    onClick={() => patch(selected.id, { seller_note: noteDraft })}
                    className="px-4 py-2 text-[11px] uppercase tracking-widest border border-stone-300 rounded-lg hover:border-[#0B1E3F] disabled:opacity-50"
                  >
                    {t("cloud.messages.save_note")}
                  </button>
                </section>

                <div className="flex flex-wrap gap-2 pt-2 border-t border-stone-100">
                  <button
                    type="button"
                    data-testid="messages-toggle-archive"
                    disabled={busyId === selected.id}
                    onClick={() => patch(selected.id, { archived: !selected.archived })}
                    className="px-3 py-2 text-[11px] uppercase tracking-widest border border-stone-300 rounded-lg text-stone-700 disabled:opacity-50"
                  >
                    {selected.archived
                      ? t("cloud.messages.unarchive")
                      : t("cloud.messages.archive")}
                  </button>
                </div>
              </article>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

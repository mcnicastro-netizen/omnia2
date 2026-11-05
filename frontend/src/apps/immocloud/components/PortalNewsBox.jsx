/* OMNIA — ImmobilCloud news (D-139)
 * variant=page: lista con filtri (account)
 * variant=tile: riquadro a scorrimento nella griglia home
 */
import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";

const CAT_LABEL = {
  immobiliare: "Immobiliare",
  mutui: "Mutui",
  arredo: "Arredo",
};

function formatWhen(iso) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "";
    return d.toLocaleDateString("it-IT", { day: "numeric", month: "short" });
  } catch {
    return "";
  }
}

function useNewsFeed({ limit = 8, category = "" } = {}) {
  const [items, setItems] = useState([]);
  const [enabled, setEnabled] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const q = new URLSearchParams({ limit: String(limit) });
    if (category) q.set("category", category);
    api
      .get(`/cloud/news?${q}`)
      .then((r) => {
        if (cancelled) return;
        setEnabled(r.data?.enabled !== false);
        setItems(Array.isArray(r.data?.items) ? r.data.items : []);
      })
      .catch(() => {
        if (!cancelled) {
          setEnabled(false);
          setItems([]);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [limit, category]);

  return { items, enabled, loading };
}

/** Tile home: titoli in scorrimento verticale continuo, pausa al hover. */
export function PortalNewsTile() {
  const { t } = useTranslation();
  const { items, enabled, loading } = useNewsFeed({ limit: 8 });
  const [paused, setPaused] = useState(false);

  if (!enabled) return null;

  const loop = items.length ? [...items, ...items] : [];

  return (
    <div
      data-testid="portal-news-tile"
      className="group relative flex flex-col overflow-hidden rounded-2xl bg-[#0B1E3F] text-white min-h-[280px] sm:min-h-0 sm:aspect-[4/5]"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
    >
      <style>{`
        @keyframes ic-news-scroll {
          from { transform: translateY(0); }
          to { transform: translateY(-50%); }
        }
        .ic-news-track {
          animation: ic-news-scroll 28s linear infinite;
        }
        .ic-news-track.paused { animation-play-state: paused; }
        @media (prefers-reduced-motion: reduce) {
          .ic-news-track { animation: none; }
        }
      `}</style>

      <div className="relative z-10 px-5 pt-5 pb-3 border-b border-white/10">
        <p className="text-[10px] uppercase tracking-[0.28em] text-[#C19A6B] mb-1">
          {t("cloud.news.eyebrow", "Dal mercato")}
        </p>
        <h3
          className="text-xl font-light"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        >
          {t("cloud.news.tile_title", "Notizie")}
        </h3>
      </div>

      <div className="relative flex-1 overflow-hidden px-5 py-3">
        {loading ? (
          <p className="text-sm text-white/50" data-testid="portal-news-loading">
            {t("common.loading")}
          </p>
        ) : items.length === 0 ? (
          <p className="text-sm text-white/50" data-testid="portal-news-empty">
            {t("cloud.news.empty", "Nessuna notizia al momento.")}
          </p>
        ) : (
          <div
            className={`ic-news-track space-y-4 ${paused ? "paused" : ""}`}
            data-testid="portal-news-scroll"
          >
            {loop.map((it, idx) => (
              <a
                key={`${it.id || it.url}-${idx}`}
                href={it.url}
                target="_blank"
                rel="noopener noreferrer"
                data-testid="portal-news-item"
                className="block group/item"
              >
                <p className="text-[10px] uppercase tracking-widest text-[#C19A6B]/90 mb-1">
                  {CAT_LABEL[it.category] || it.category}
                  {it.published_at ? ` · ${formatWhen(it.published_at)}` : ""}
                </p>
                <p
                  className="text-sm leading-snug text-white/90 group-hover/item:text-[#E8D5B5] transition"
                  style={{ fontFamily: "'Fraunces', Georgia, serif" }}
                >
                  {it.title}
                </p>
                <p className="text-[11px] text-white/40 mt-1">{it.source}</p>
              </a>
            ))}
          </div>
        )}
        <div
          className="pointer-events-none absolute inset-x-0 bottom-0 h-12"
          style={{ background: "linear-gradient(180deg, transparent, #0B1E3F)" }}
        />
      </div>

      <p className="relative z-10 px-5 pb-4 text-[10px] text-white/35">
        {t("cloud.news.tile_hint", "Scorri · clic per aprire la fonte")}
      </p>
    </div>
  );
}

export default function PortalNewsBox({ compact = false }) {
  const { t } = useTranslation();
  const [filter, setFilter] = useState("");
  const { items, enabled, loading } = useNewsFeed({
    limit: compact ? 5 : 8,
    category: filter,
  });

  if (!enabled) return null;
  if (!loading && items.length === 0 && !filter) return null;

  return (
    <section
      className={compact ? "mt-10" : "px-5 sm:px-8 md:px-16 py-14 bg-white"}
      data-testid="portal-news-box"
      aria-labelledby="portal-news-heading"
    >
      <div className={compact ? "" : "max-w-5xl mx-auto"}>
        <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
          <div>
            <p className="text-[11px] uppercase tracking-[0.28em] text-[#C19A6B] mb-2">
              {t("cloud.news.eyebrow", "Dal mercato")}
            </p>
            <h2
              id="portal-news-heading"
              className={`${compact ? "text-2xl" : "text-3xl md:text-4xl"} font-light tracking-tight text-[#0B1E3F]`}
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {t("cloud.news.title", "Notizie utili, senza rumore")}
            </h2>
          </div>
          {!compact && (
            <div className="flex flex-wrap gap-2" role="tablist" aria-label={t("cloud.news.filter_label", "Categorie")}>
              {[
                { v: "", label: t("cloud.news.filter_all", "Tutte") },
                { v: "immobiliare", label: t("cloud.news.cat_immobiliare", "Immobiliare") },
                { v: "mutui", label: t("cloud.news.cat_mutui", "Mutui") },
                { v: "arredo", label: t("cloud.news.cat_arredo", "Arredo") },
              ].map((o) => (
                <button
                  key={o.v || "all"}
                  type="button"
                  role="tab"
                  aria-selected={filter === o.v}
                  data-testid={`portal-news-filter-${o.v || "all"}`}
                  onClick={() => setFilter(o.v)}
                  className={`px-3 py-1.5 text-[11px] uppercase tracking-widest border transition ${
                    filter === o.v
                      ? "bg-[#0B1E3F] text-white border-[#0B1E3F]"
                      : "bg-transparent text-stone-600 border-stone-200 hover:border-stone-400"
                  }`}
                >
                  {o.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {loading ? (
          <p className="text-sm text-stone-400" data-testid="portal-news-loading">
            {t("common.loading")}
          </p>
        ) : items.length === 0 ? (
          <p className="text-sm text-stone-500" data-testid="portal-news-empty">
            {t("cloud.news.empty", "Nessuna notizia in questa categoria al momento.")}
          </p>
        ) : (
          <ul className="divide-y divide-stone-100 border-t border-b border-stone-200" data-testid="portal-news-list">
            {items.map((it) => {
              const when = formatWhen(it.published_at);
              const cat = CAT_LABEL[it.category] || it.category;
              return (
                <li key={it.id || it.url}>
                  <a
                    href={it.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    data-testid="portal-news-item"
                    className="group flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4 py-4 hover:bg-[#f7f4ef]/60 transition px-1 -mx-1"
                  >
                    <div className="sm:w-36 shrink-0 flex items-center gap-2 text-[11px] uppercase tracking-widest text-stone-400">
                      <span className="text-[#C19A6B]">{cat}</span>
                      {when ? <span>· {when}</span> : null}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p
                        className="text-[#0B1E3F] text-base md:text-lg font-light group-hover:text-[#C19A6B] transition"
                        style={{ fontFamily: "'Fraunces', Georgia, serif" }}
                      >
                        {it.title}
                      </p>
                      <p className="text-xs text-stone-500 mt-1">{it.source}</p>
                    </div>
                  </a>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}

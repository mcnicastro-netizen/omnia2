/* OMNIA — ImmobilCloud news box (D-139)
 * Aggregato RSS server-side: immobiliare / mutui / arredo. Link esterni.
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

export default function PortalNewsBox({ compact = false }) {
  const { t } = useTranslation();
  const [items, setItems] = useState([]);
  const [enabled, setEnabled] = useState(true);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const q = new URLSearchParams({ limit: compact ? "5" : "8" });
    if (filter) q.set("category", filter);
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
  }, [compact, filter]);

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
            {!compact && (
              <p className="text-stone-600 mt-2 max-w-xl text-sm md:text-base">
                {t(
                  "cloud.news.subtitle",
                  "Casa, mutui e arredo da fonti aperte. Apri l’articolo sul sito originale."
                )}
              </p>
            )}
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
                      <p className="text-xs text-stone-500 mt-1">
                        {it.source}
                        <span className="ml-2 opacity-0 group-hover:opacity-100 transition text-[#C19A6B]">
                          {t("cloud.news.open_external", "Apri ↗")}
                        </span>
                      </p>
                    </div>
                  </a>
                </li>
              );
            })}
          </ul>
        )}

        <p className="mt-4 text-[11px] text-stone-400">
          {t(
            "cloud.news.disclaimer",
            "Fonti terze · i contenuti restano dei rispettivi editori. OMNIA non ne modifica il testo."
          )}
        </p>
      </div>
    </section>
  );
}

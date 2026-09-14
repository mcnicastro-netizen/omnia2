/* OMNIA — HAL Improve Button (inline AI suggestion for title/description)
 *
 * Reusable component shown next to title/description fields in:
 *  - ImmoWeb PropertyFormPage (agents)
 *  - ImmobilCloud SellPage (B2C private owners)
 *
 * Click ✨ → POST /api/app/al/improve with current value + all form data.
 * Modal shows side-by-side Original vs Suggested + IT/EN/ES lang tabs +
 * Apply / Regenerate / Close actions.
 */
import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../lib/api";

const LANGS = [
  { code: "it", label: "IT" },
  { code: "en", label: "EN" },
  { code: "es", label: "ES" },
];

export default function AlImproveButton({
  field,            // "title" | "description"
  value,            // current text
  propertyData,     // entire form snapshot
  onApply,          // (newText) => void
  testId,           // base test id prefix
}) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [lang, setLang] = useState("it");
  const [loading, setLoading] = useState(false);
  const [suggestion, setSuggestion] = useState("");
  const [error, setError] = useState(null);

  const tid = testId || `al-improve-${field}`;

  const generate = async (targetLang = lang) => {
    setLoading(true);
    setError(null);
    setSuggestion("");
    try {
      const r = await api.post("/app/al/improve", {
        field,
        current_text: value || "",
        property_data: propertyData || {},
        target_lang: targetLang,
        tone: "standard",
      });
      setSuggestion(r.data.improved || "");
    } catch (e) {
      const d = e?.response?.data?.detail;
      setError(
        d === "llm_budget_exceeded" || d === "llm_unavailable"
          ? t("al.err_budget")
          : d === "rate_limit_exceeded"
          ? t("al.err_rate_limit")
          : t("al.err_generic")
      );
    } finally {
      setLoading(false);
    }
  };

  const openModal = () => {
    setOpen(true);
    setSuggestion("");
    setError(null);
    setLang("it");
    generate("it");
  };

  const switchLang = (code) => {
    setLang(code);
    generate(code);
  };

  const apply = () => {
    if (suggestion) onApply(suggestion);
    setOpen(false);
  };

  return (
    <>
      <button
        type="button"
        data-testid={`${tid}-trigger`}
        onClick={openModal}
        className="inline-flex items-center gap-1.5 text-[11px] uppercase tracking-widest text-[#C19A6B] hover:text-[#0B1E3F] font-medium border border-[#C19A6B]/40 hover:border-[#0B1E3F] px-2.5 py-1 rounded transition"
        title={t("al_improve.tooltip")}
      >
        <span aria-hidden>✨</span>
        {t("al_improve.button")}
      </button>

      {open && (
        <div
          data-testid={`${tid}-modal`}
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 p-4"
          onClick={() => setOpen(false)}
        >
          <div
            className="bg-white rounded-lg shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <header className="px-6 py-4 border-b border-stone-200 flex items-center justify-between">
              <div>
                <h2
                  className="text-lg font-light"
                  style={{ fontFamily: "'Fraunces', Georgia, serif" }}
                >
                  ✨ {t(`al_improve.title_${field}`)}
                </h2>
                <p className="text-[10px] uppercase tracking-widest text-stone-500 mt-0.5">
                  {t("al_improve.subtitle")}
                </p>
              </div>
              <button
                data-testid={`${tid}-close`}
                onClick={() => setOpen(false)}
                className="text-2xl leading-none text-stone-400 hover:text-stone-900"
              >
                ×
              </button>
            </header>

            {/* Lang tabs */}
            <div className="px-6 pt-4 flex gap-2">
              {LANGS.map((l) => (
                <button
                  key={l.code}
                  data-testid={`${tid}-lang-${l.code}`}
                  onClick={() => switchLang(l.code)}
                  disabled={loading}
                  className={`text-[11px] uppercase tracking-widest px-3 py-1.5 rounded border transition ${
                    lang === l.code
                      ? "bg-[#0B1E3F] text-white border-[#0B1E3F]"
                      : "bg-white text-stone-600 border-stone-300 hover:border-[#0B1E3F]"
                  } disabled:opacity-50`}
                >
                  {l.label}
                </button>
              ))}
            </div>

            {/* Body: original | suggested */}
            <div className="flex-1 overflow-y-auto p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="text-[10px] uppercase tracking-widest text-stone-500 mb-2">
                  {t("al_improve.original")}
                </h3>
                <div
                  data-testid={`${tid}-original`}
                  className="text-sm whitespace-pre-wrap text-stone-700 bg-stone-50 border border-stone-200 rounded p-3 min-h-[160px]"
                >
                  {value || (
                    <em className="text-stone-400">{t("al_improve.empty_original")}</em>
                  )}
                </div>
              </div>
              <div>
                <h3 className="text-[10px] uppercase tracking-widest text-[#C19A6B] mb-2">
                  {t("al_improve.suggested")}
                </h3>
                <div
                  data-testid={`${tid}-suggested`}
                  className="text-sm whitespace-pre-wrap text-stone-900 bg-[#FAF7F2] border border-[#C19A6B]/40 rounded p-3 min-h-[160px]"
                >
                  {loading ? (
                    <em className="text-stone-400">{t("al_improve.generating")}</em>
                  ) : error ? (
                    <span className="text-red-600">{error}</span>
                  ) : suggestion ? (
                    suggestion
                  ) : (
                    <em className="text-stone-400">{t("al_improve.empty_suggested")}</em>
                  )}
                </div>
              </div>
            </div>

            {/* Footer */}
            <footer className="px-6 py-4 border-t border-stone-200 flex items-center justify-between">
              <button
                data-testid={`${tid}-regenerate`}
                onClick={() => generate(lang)}
                disabled={loading}
                className="text-xs uppercase tracking-widest text-stone-600 hover:text-[#0B1E3F] disabled:opacity-50"
              >
                ↻ {t("al_improve.regenerate")}
              </button>
              <div className="flex gap-3">
                <button
                  data-testid={`${tid}-cancel`}
                  onClick={() => setOpen(false)}
                  className="text-xs uppercase tracking-widest text-stone-500 hover:text-stone-900 px-3 py-2"
                >
                  {t("al_improve.cancel")}
                </button>
                <button
                  data-testid={`${tid}-apply`}
                  onClick={apply}
                  disabled={!suggestion || loading}
                  className="text-xs uppercase tracking-widest bg-[#0B1E3F] text-white px-5 py-2 rounded hover:bg-[#C19A6B] disabled:opacity-40"
                >
                  {t("al_improve.apply")}
                </button>
              </div>
            </footer>
          </div>
        </div>
      )}
    </>
  );
}

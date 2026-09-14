import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api } from "../../shared/lib/api";
import { formatApiErrorDetail } from "../../shared/lib/auth";
import LanguageSwitcher from "../../shared/components/LanguageSwitcher";
import Brand from "../../shared/components/Brand";
import OmniaLogo from "../../shared/components/OmniaLogo";

export default function ForgotPasswordPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.post("/auth/forgot-password", { email });
      setSent(true);
    } catch (err) {
      setError(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      data-testid="forgot-page"
      className="min-h-screen bg-stone-100 text-stone-900 flex flex-col"
      style={{ fontFamily: "'Fraunces', Georgia, serif" }}
    >
      <header className="flex items-center justify-between px-5 sm:px-8 md:px-12 py-5 border-b border-stone-300 bg-white">
        <Link to={`/${lang}`} className="flex items-center gap-3 text-xl md:text-2xl tracking-tight font-medium">
          <OmniaLogo variant="mark" size="md" />
          <span><Brand>OMNIA</Brand><span className="text-stone-400">·</span>
          <Brand className="font-light">app</Brand></span>
        </Link>
        <LanguageSwitcher />
      </header>

      <main className="flex-1 flex items-center justify-center px-5 py-12">
        <form
          onSubmit={submit}
          className="w-full max-w-md bg-white border border-stone-300 p-8 md:p-10"
        >
          <h1 className="text-3xl md:text-4xl tracking-tight mb-4">{t("auth.forgot_title")}</h1>
          <p className="text-stone-600 font-sans text-sm mb-8">{t("auth.forgot_subtitle")}</p>

          {sent ? (
            <div data-testid="forgot-success" className="p-4 border border-emerald-300 bg-emerald-50 text-emerald-800 text-sm font-sans">
              {t("auth.reset_link_sent")}
            </div>
          ) : (
            <>
              <label className="block mb-6">
                <span className="block text-xs font-sans uppercase tracking-widest text-stone-500 mb-2">
                  {t("auth.email")}
                </span>
                <input
                  data-testid="forgot-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 border border-stone-300 bg-stone-50 font-sans text-base focus:outline-none focus:border-stone-900"
                />
              </label>

              {error && (
                <div className="mb-5 p-3 border border-red-300 bg-red-50 text-red-700 text-sm font-sans">
                  {error}
                </div>
              )}

              <button
                data-testid="forgot-submit"
                type="submit"
                disabled={loading}
                className="w-full bg-stone-900 text-stone-50 px-6 py-4 text-xs sm:text-sm font-sans uppercase tracking-widest hover:bg-stone-700 transition disabled:opacity-50"
              >
                {loading ? t("common.loading") : t("auth.send_reset_link")} →
              </button>
            </>
          )}

          <p className="mt-8 pt-6 border-t border-stone-200 text-sm font-sans text-stone-600">
            <Link to={`/${lang}/login`} className="text-stone-900 underline">
              ← {t("common.back")}
            </Link>
          </p>
        </form>
      </main>
    </div>
  );
}

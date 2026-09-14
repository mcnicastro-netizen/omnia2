import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../../shared/lib/api";
import { formatApiErrorDetail } from "../../shared/lib/auth";
import LanguageSwitcher from "../../shared/components/LanguageSwitcher";
import Brand from "../../shared/components/Brand";
import OmniaLogo from "../../shared/components/OmniaLogo";

export default function ResetPasswordPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();
  const [params] = useSearchParams();
  const token = params.get("token") || "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (password !== confirm) {
      setError(t("auth.passwords_mismatch"));
      return;
    }
    setLoading(true);
    try {
      await api.post("/auth/reset-password", { token, new_password: password });
      setDone(true);
      setTimeout(() => nav(`/${lang}/login`, { replace: true }), 2500);
    } catch (err) {
      setError(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      data-testid="reset-password-page"
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
        <form onSubmit={submit} className="w-full max-w-md bg-white border border-stone-300 p-8 md:p-10">
          <h1 className="text-3xl md:text-4xl tracking-tight mb-4">{t("auth.reset_title")}</h1>

          {!token && (
            <div data-testid="reset-no-token" className="p-4 border border-red-300 bg-red-50 text-red-700 text-sm font-sans">
              {t("auth.invalid_reset_link")}{" "}
              <Link to={`/${lang}/forgot-password`} className="underline">
                {t("auth.forgot_password")} →
              </Link>
            </div>
          )}

          {token && done && (
            <div data-testid="reset-success" className="p-4 border border-emerald-300 bg-emerald-50 text-emerald-800 text-sm font-sans">
              {t("auth.password_updated")}{" "}
              <Link to={`/${lang}/login`} className="underline">{t("auth.login_now")} →</Link>
            </div>
          )}

          {token && !done && (
            <>
              <label className="block mb-5">
                <span className="block text-xs font-sans uppercase tracking-widest text-stone-500 mb-2">
                  {t("auth.new_password")}
                </span>
                <input
                  data-testid="reset-password-input"
                  type="password"
                  required
                  minLength={8}
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 border border-stone-300 bg-stone-50 font-sans text-base focus:outline-none focus:border-stone-900"
                />
              </label>
              <label className="block mb-6">
                <span className="block text-xs font-sans uppercase tracking-widest text-stone-500 mb-2">
                  {t("auth.confirm_password")}
                </span>
                <input
                  data-testid="reset-confirm-input"
                  type="password"
                  required
                  minLength={8}
                  autoComplete="new-password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  className="w-full px-4 py-3 border border-stone-300 bg-stone-50 font-sans text-base focus:outline-none focus:border-stone-900"
                />
              </label>

              {error && (
                <div data-testid="reset-error" className="mb-5 p-3 border border-red-300 bg-red-50 text-red-700 text-sm font-sans">
                  {error}
                </div>
              )}

              <button
                data-testid="reset-submit"
                type="submit"
                disabled={loading}
                className="w-full bg-stone-900 text-stone-50 px-6 py-4 text-xs sm:text-sm font-sans uppercase tracking-widest hover:bg-stone-700 transition disabled:opacity-50"
              >
                {loading ? t("common.loading") : t("auth.reset_cta")} →
              </button>
            </>
          )}

          <p className="mt-8 pt-6 border-t border-stone-200 text-sm font-sans text-stone-600">
            <Link to={`/${lang}/login`} className="text-stone-900 underline">
              ← {t("auth.login_now")}
            </Link>
          </p>
        </form>
      </main>
    </div>
  );
}

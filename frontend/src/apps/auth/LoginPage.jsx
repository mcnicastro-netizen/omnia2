import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth, formatApiErrorDetail } from "../../shared/lib/auth";
import { sanitizeNextParam } from "../../shared/lib/navigation";
import LanguageSwitcher from "../../shared/components/LanguageSwitcher";
import Brand from "../../shared/components/Brand";
import OmniaLogo from "../../shared/components/OmniaLogo";

export default function LoginPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const { login } = useAuth();
  const nav = useNavigate();
  const location = useLocation();
  // C3 — anti open-redirect (logica pura testata in shared/lib/navigation.ts)
  const next = sanitizeNextParam(
    new URLSearchParams(location.search).get("next"),
    `/${lang}/app/dashboard`
  );

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(email, password);
      nav(next, { replace: true });
    } catch (err) {
      setError(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      data-testid="login-page"
      className="min-h-screen bg-stone-100 text-stone-900 flex flex-col"
      style={{ fontFamily: "'Fraunces', Georgia, serif" }}
    >
      <header className="flex items-center justify-between px-5 sm:px-8 md:px-12 py-5 border-b border-stone-300 bg-white">
        <Link to={`/${lang}`} className="flex items-center gap-3 text-xl md:text-2xl tracking-tight font-medium">
          <OmniaLogo variant="mark" size="md" data-testid="login-logo" />
          <span><Brand>OMNIA</Brand><span className="text-stone-400">·</span>
          <Brand className="font-light">app</Brand></span>
        </Link>
        <LanguageSwitcher />
      </header>

      <main className="flex-1 flex items-center justify-center px-5 py-12">
        <form
          onSubmit={submit}
          data-testid="login-form"
          className="w-full max-w-md bg-white border border-stone-300 p-8 md:p-10"
        >
          <p className="text-xs font-sans uppercase tracking-[0.3em] text-amber-700 mb-3">
            <Brand>ImmoWeb — Agency CRM</Brand>
          </p>
          <h1 className="text-3xl md:text-4xl tracking-tight mb-8">{t("auth.login_title")}</h1>

          <label className="block mb-5">
            <span className="block text-xs font-sans uppercase tracking-widest text-stone-500 mb-2">
              {t("auth.email")}
            </span>
            <input
              data-testid="login-email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-stone-300 bg-stone-50 font-sans text-base focus:outline-none focus:border-stone-900"
            />
          </label>

          <label className="block mb-3">
            <span className="block text-xs font-sans uppercase tracking-widest text-stone-500 mb-2">
              {t("auth.password")}
            </span>
            <input
              data-testid="login-password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border border-stone-300 bg-stone-50 font-sans text-base focus:outline-none focus:border-stone-900"
            />
          </label>

          <Link
            to={`/${lang}/forgot-password`}
            className="block text-xs font-sans text-stone-500 hover:text-stone-900 mb-6"
          >
            {t("auth.forgot_password")} →
          </Link>

          {error && (
            <div
              data-testid="login-error"
              className="mb-5 p-3 border border-red-300 bg-red-50 text-red-700 text-sm font-sans"
            >
              {error}
            </div>
          )}

          <button
            data-testid="login-submit"
            type="submit"
            disabled={loading}
            className="w-full bg-stone-900 text-stone-50 px-6 py-4 text-xs sm:text-sm font-sans uppercase tracking-widest hover:bg-stone-700 transition disabled:opacity-50"
          >
            {loading ? t("common.loading") : t("auth.login_cta")} →
          </button>

          <p className="mt-8 pt-6 border-t border-stone-200 text-sm font-sans text-stone-600">
            {t("auth.no_account")}{" "}
            <Link to={`/${lang}/register`} className="text-stone-900 underline">
              {t("auth.register_now")}
            </Link>
          </p>
        </form>
      </main>
    </div>
  );
}

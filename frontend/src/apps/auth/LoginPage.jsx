import React, { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth, formatApiErrorDetail } from "../../shared/lib/auth";
import { sanitizeNextParam } from "../../shared/lib/navigation";
import LanguageSwitcher from "../../shared/components/LanguageSwitcher";
import Brand from "../../shared/components/Brand";
import OmniaLogo from "../../shared/components/OmniaLogo";
import GoogleSignInButton from "../../shared/components/GoogleSignInButton";

function EyeIcon({ open }) {
  // Minimal inline icons — no extra icon dependency
  if (open) {
    return (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" stroke="currentColor" strokeWidth="1.6" />
        <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.6" />
      </svg>
    );
  }
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.6" />
      <path d="M4 4l16 16" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

export default function LoginPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const { login, loginWithGoogle, verifyMfa } = useAuth();
  const nav = useNavigate();
  const location = useLocation();
  const next = sanitizeNextParam(
    new URLSearchParams(location.search).get("next"),
    `/${lang}/app/dashboard`
  );

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [passwordFieldKey, setPasswordFieldKey] = useState(0);
  const [mfaToken, setMfaToken] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const passwordRef = useRef(null);
  const mfaCodeRef = useRef(null);
  const focusPasswordAfterClear = useRef(false);
  const clearMfaOnError = useRef(false);

  useEffect(() => {
    if (focusPasswordAfterClear.current) {
      focusPasswordAfterClear.current = false;
      // Remounted input — focus after paint; also wipe any late browser autofill
      const el = passwordRef.current;
      if (el) {
        el.value = "";
        el.focus();
      }
    }
  }, [passwordFieldKey]);

  useEffect(() => {
    if (clearMfaOnError.current) {
      clearMfaOnError.current = false;
      mfaCodeRef.current?.focus();
    }
  }, [mfaCode, error]);

  const wipePassword = () => {
    setPassword("");
    setShowPassword(false);
    focusPasswordAfterClear.current = true;
    // Remount defeats Chrome/Firefox password-manager re-fill after failed login
    setPasswordFieldKey((k) => k + 1);
  };

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await login(email, password);
      if (data?.mfa_required) {
        setMfaToken(data.mfa_token);
        return;
      }
      nav(next, { replace: true });
    } catch (err) {
      const detail = err.response?.data?.detail;
      wipePassword();
      setError(
        detail === "use_google_sign_in"
          ? t("auth.use_google")
          : formatApiErrorDetail(detail) || err.message
      );
    } finally {
      setLoading(false);
    }
  };

  const submitMfa = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await verifyMfa(mfaToken, mfaCode);
      nav(next, { replace: true });
    } catch (err) {
      clearMfaOnError.current = true;
      setMfaCode("");
      setError(formatApiErrorDetail(err.response?.data?.detail) || t("auth.mfa_invalid"));
    } finally {
      setLoading(false);
    }
  };

  const onGoogle = async (credential) => {
    setError("");
    try {
      const data = await loginWithGoogle(credential);
      if (data?.mfa_required) {
        setMfaToken(data.mfa_token);
        return;
      }
      nav(next, { replace: true });
    } catch (err) {
      setError(formatApiErrorDetail(err?.response?.data?.detail) || err.message);
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
        {mfaToken ? (
          <form
            onSubmit={submitMfa}
            data-testid="mfa-form"
            className="w-full max-w-md bg-white border border-stone-300 p-8 md:p-10"
          >
            <p className="text-xs font-sans uppercase tracking-[0.3em] text-amber-700 mb-3">
              {t("auth.mfa_eyebrow")}
            </p>
            <h1 className="text-3xl md:text-4xl tracking-tight mb-4">{t("auth.mfa_title")}</h1>
            <p className="text-sm font-sans text-stone-600 mb-6">{t("auth.mfa_hint")}</p>
            <label className="block mb-5">
              <span className="block text-xs font-sans uppercase tracking-widest text-stone-500 mb-2">
                {t("auth.mfa_code")}
              </span>
              <input
                data-testid="mfa-code"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                required
                value={mfaCode}
                onChange={(e) => setMfaCode(e.target.value)}
                ref={mfaCodeRef}
                className="w-full px-4 py-3 border border-stone-300 bg-stone-50 font-sans text-base focus:outline-none focus:border-stone-900"
              />
            </label>
            {error && (
              <div data-testid="login-error" className="mb-5 p-3 border border-red-300 bg-red-50 text-red-700 text-sm font-sans">
                {error}
              </div>
            )}
            <button
              type="submit"
              disabled={loading}
              data-testid="mfa-submit"
              className="w-full py-3 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest font-sans hover:bg-stone-700 disabled:opacity-50"
            >
              {loading ? t("common.loading") : t("auth.mfa_cta")}
            </button>
            <button
              type="button"
              className="mt-4 w-full text-xs font-sans text-stone-500 hover:text-stone-900"
              onClick={() => { setMfaToken(""); setMfaCode(""); setError(""); }}
            >
              ← {t("auth.mfa_back")}
            </button>
          </form>
        ) : (
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
              <div className="relative">
                <input
                  key={passwordFieldKey}
                  data-testid="login-password"
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  ref={passwordRef}
                  className="w-full px-4 py-3 pr-12 border border-stone-300 bg-stone-50 font-sans text-base focus:outline-none focus:border-stone-900"
                />
                <button
                  type="button"
                  data-testid="login-password-toggle"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-stone-500 hover:text-stone-900"
                  aria-label={
                    showPassword
                      ? t("auth.hide_password", "Nascondi password")
                      : t("auth.show_password", "Mostra password")
                  }
                  title={
                    showPassword
                      ? t("auth.hide_password", "Nascondi password")
                      : t("auth.show_password", "Mostra password")
                  }
                >
                  <EyeIcon open={showPassword} />
                </button>
              </div>
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
              type="submit"
              disabled={loading}
              data-testid="login-submit"
              className="w-full py-3 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest font-sans hover:bg-stone-700 disabled:opacity-50"
            >
              {loading ? t("common.loading") : t("auth.login_cta")}
            </button>

            <div className="my-6">
              <GoogleSignInButton onSuccess={onGoogle} onError={(m) => setError(m)} />
            </div>

            <p className="text-sm font-sans text-stone-500 text-center">
              {t("auth.no_account")}{" "}
              <Link to={`/${lang}/register`} className="text-stone-900 underline">
                {t("auth.register_now")}
              </Link>
            </p>
          </form>
        )}
      </main>
    </div>
  );
}

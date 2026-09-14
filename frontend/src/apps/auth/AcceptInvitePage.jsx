import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams, useNavigate } from "react-router-dom";
import { api } from "../../shared/lib/api";
import { useAuth } from "../../shared/lib/auth";
import { formatApiErrorDetail } from "../../shared/lib/auth";
import Brand from "../../shared/components/Brand";
import OmniaLogo from "../../shared/components/OmniaLogo";
import LanguageSwitcher from "../../shared/components/LanguageSwitcher";

export default function AcceptInvitePage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const [params] = useSearchParams();
  // L5 — il token arriva nel fragment (#token=...) per non finire nei log server;
  // fallback su query string per compatibilità con email già inviate.
  const hashToken = new URLSearchParams(window.location.hash.replace(/^#/, "")).get("token");
  const token = hashToken || params.get("token");
  const nav = useNavigate();
  const { refresh } = useAuth();

  const [verifying, setVerifying] = useState(true);
  const [invite, setInvite] = useState(null);
  const [verifyError, setVerifyError] = useState("");

  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!token) {
      setVerifyError(t("accept_invite.invalid"));
      setVerifying(false);
      return;
    }
    api
      .get(`/app/invites/verify?token=${encodeURIComponent(token)}`)
      .then((r) => setInvite(r.data))
      .catch(() => setVerifyError(t("accept_invite.invalid")))
      .finally(() => setVerifying(false));
  }, [token, t]);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await api.post("/app/invites/accept", { token, name: name.trim(), password });
      await refresh();
      setSuccess(true);
      setTimeout(() => nav(`/${lang}/app/dashboard`, { replace: true }), 1500);
    } catch (err) {
      setError(formatApiErrorDetail(err?.response?.data?.detail) || t("common.error"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      data-testid="accept-invite-page"
      className="min-h-screen bg-stone-50 text-stone-900"
      style={{ fontFamily: "'Inter', system-ui, sans-serif" }}
    >
      <header className="border-b border-stone-200">
        <div className="max-w-5xl mx-auto px-5 sm:px-8 py-5 flex items-center justify-between">
          <span
            className="flex items-center gap-3 text-xl tracking-tight font-medium text-stone-900"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            <OmniaLogo variant="mark" size="md" />
            <Brand>OMNIA</Brand>
          </span>
          <LanguageSwitcher />
        </div>
      </header>

      <main className="max-w-md mx-auto px-5 sm:px-8 py-12 md:py-20">
        {verifying && (
          <p data-testid="verifying" className="text-sm text-stone-500 uppercase tracking-widest">
            {t("accept_invite.loading")}
          </p>
        )}

        {!verifying && verifyError && (
          <div data-testid="invite-invalid" className="text-center py-12">
            <div className="text-5xl mb-4 text-red-600">⚠</div>
            <h1
              className="text-2xl tracking-tight mb-3"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {t("accept_invite.invalid")}
            </h1>
            <a
              href={`/${lang}/login`}
              className="inline-block mt-4 text-sm uppercase tracking-widest text-stone-600 hover:text-stone-900"
            >
              ← {t("nav.login")}
            </a>
          </div>
        )}

        {!verifying && invite && !success && (
          <div>
            <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-3">
              <Brand>ImmoWeb · Invito</Brand>
            </p>
            <h1
              className="text-3xl tracking-tight mb-2"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {t("accept_invite.title")}
            </h1>
            <p className="text-stone-600 mb-2">
              {t("accept_invite.subtitle", { agency_name: invite.agency_name, role: invite.role })}
            </p>
            <p className="text-sm text-stone-500 mb-8">
              <strong>{invite.email}</strong>
            </p>

            <form onSubmit={submit} className="space-y-4">
              <div>
                <label className="block text-xs uppercase tracking-widest text-stone-600 mb-1.5">
                  {t("accept_invite.name")}
                </label>
                <input
                  required
                  autoFocus
                  data-testid="accept-name-input"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2.5 bg-white border border-stone-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-stone-900/10 focus:border-stone-900"
                />
              </div>
              <div>
                <label className="block text-xs uppercase tracking-widest text-stone-600 mb-1.5">
                  {t("accept_invite.password")}
                </label>
                <input
                  required
                  type="password"
                  minLength={8}
                  data-testid="accept-password-input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-2.5 bg-white border border-stone-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-stone-900/10 focus:border-stone-900"
                />
                <p className="text-xs text-stone-400 mt-1">{t("accept_invite.password_hint")}</p>
              </div>

              {error && (
                <p data-testid="accept-error" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={submitting}
                data-testid="accept-submit-btn"
                className="w-full px-6 py-3 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest font-medium rounded-md hover:bg-stone-700 disabled:opacity-50 transition"
              >
                {submitting ? t("common.loading") : t("accept_invite.accept")}
              </button>
            </form>
          </div>
        )}

        {success && (
          <div data-testid="accept-success" className="text-center py-12">
            <div className="text-5xl mb-4 text-emerald-600">✓</div>
            <p
              className="text-xl tracking-tight"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {t("accept_invite.success")}
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

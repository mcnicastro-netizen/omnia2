import React, { useEffect, useMemo, useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth, formatApiErrorDetail, isEmailAlreadyRegistered } from "../../shared/lib/auth";
import { api } from "../../shared/lib/api";
import LanguageSwitcher from "../../shared/components/LanguageSwitcher";
import Brand from "../../shared/components/Brand";
import OmniaLogo from "../../shared/components/OmniaLogo";
import GoogleSignInButton from "../../shared/components/GoogleSignInButton";
import PasswordField from "../../shared/components/PasswordField";

const PREFERRED_PLAN_KEY = "omnia_preferred_plan";
const ALLOWED_PLANS = new Set(["starter", "pro", "agency"]);

const PLAN_FEATURES = {
  starter: [
    "Gestionale CRM + match clienti",
    "HAL AI in-app",
    "Sito agenzia + multiposting base",
    "Fino a 3 utenti · 30 immobili",
  ],
  pro: [
    "Tutto di Starter",
    "White-label sul tuo dominio",
    "Staging / tools AI avanzati",
    "Fino a 10 utenti · 200 immobili",
  ],
  agency: [
    "Tutto di Pro",
    "Limiti illimitati",
    "Multiposting esteso",
    "Supporto dedicato",
  ],
};

const FALLBACK_PLANS = [
  { tier: "starter", name: "Starter", price_monthly: 49, price_yearly: 539, max_agents: 3, max_properties: 30, credits_included_monthly: 120 },
  { tier: "pro", name: "Pro", price_monthly: 99, price_yearly: 1089, max_agents: 10, max_properties: 200, credits_included_monthly: 1200 },
  { tier: "agency", name: "Agency", price_monthly: 299, price_yearly: 3289, max_agents: -1, max_properties: -1, credits_included_monthly: 3600 },
];

function fmtLimit(n) {
  return n === -1 || n == null ? "∞" : String(n);
}

export default function RegisterPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const { register, loginWithGoogle } = useAuth();
  const nav = useNavigate();
  const [searchParams] = useSearchParams();

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    account_type: "agency",
    existing_domain: "",
  });
  const [policyAccepted, setPolicyAccepted] = useState(false);
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const [error, setError] = useState("");
  const [dupEmail, setDupEmail] = useState(false);
  const [loading, setLoading] = useState(false);
  const [preferredPlan, setPreferredPlan] = useState("");
  const [planCatalog, setPlanCatalog] = useState([]);
  const [choosingPlan, setChoosingPlan] = useState(true);
  const loginHref = `/${lang}/login?from=app&next=${encodeURIComponent(`/${lang}/app/dashboard`)}`;

  useEffect(() => {
    const raw = (searchParams.get("plan") || "").toLowerCase().trim();
    let initial = ALLOWED_PLANS.has(raw) ? raw : "";
    if (!initial) {
      try {
        const stored = (sessionStorage.getItem(PREFERRED_PLAN_KEY) || "").toLowerCase();
        if (ALLOWED_PLANS.has(stored)) initial = stored;
      } catch {
        /* ignore */
      }
    }
    if (initial) {
      try {
        sessionStorage.setItem(PREFERRED_PLAN_KEY, initial);
      } catch {
        /* ignore */
      }
      setPreferredPlan(initial);
      // Da landing (?plan=) o ripresa: form subito. Altrimenti restano i box.
      if (ALLOWED_PLANS.has(raw)) setChoosingPlan(false);
    }
  }, [searchParams]);

  useEffect(() => {
    let mounted = true;
    api
      .get("/billing/plans")
      .then((r) => {
        if (!mounted) return;
        setPlanCatalog(r.data?.plans || []);
      })
      .catch(() => {
        if (mounted) setPlanCatalog([]);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const plans = useMemo(() => {
    const src = planCatalog.length ? planCatalog : FALLBACK_PLANS;
    return src
      .map((p) => {
        const tier = (p.tier || "").toLowerCase();
        if (!ALLOWED_PLANS.has(tier)) return null;
        return {
          tier,
          name: p.name || tier,
          monthly: Math.round(p.price_monthly),
          yearly: Math.round(p.price_yearly ?? p.price_monthly * 11),
          agents: fmtLimit(p.max_agents),
          properties: fmtLimit(p.max_properties),
          credits: p.credits_included_monthly || 0,
          highlight: tier === "pro",
          features: PLAN_FEATURES[tier] || [],
        };
      })
      .filter(Boolean);
  }, [planCatalog]);

  const selectedPlan = plans.find((p) => p.tier === preferredPlan) || null;

  const pickPlan = (tier) => {
    if (!ALLOWED_PLANS.has(tier)) return;
    setPreferredPlan(tier);
    setChoosingPlan(false);
    setError("");
    try {
      sessionStorage.setItem(PREFERRED_PLAN_KEY, tier);
    } catch {
      /* ignore */
    }
    // URL sync senza reload
    try {
      const url = new URL(window.location.href);
      url.searchParams.set("plan", tier);
      window.history.replaceState({}, "", url.pathname + url.search);
    } catch {
      /* ignore */
    }
  };

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const isAgencyRole = form.account_type === "agency";
  const showPlanBoxes = isAgencyRole && (choosingPlan || !preferredPlan);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setDupEmail(false);
    if (!privacyAccepted) {
      setError(t("auth.privacy_required_error"));
      return;
    }
    if (isAgencyRole && !policyAccepted) {
      setError(t("domain_vault.policy_required_error"));
      return;
    }
    if (isAgencyRole && !preferredPlan) {
      setError(t("auth.plan_required_error", "Scegli il pacchetto prima di registrarti."));
      setChoosingPlan(true);
      return;
    }
    if (!form.password || form.password.length < 8) {
      setError(
        t("auth.password_required", "Scegli una password (minimo 8 caratteri).")
      );
      return;
    }
    setLoading(true);
    try {
      const payload = {
        name: form.name,
        email: form.email,
        role: form.account_type === "student" ? "student" : "client",
        lang,
        password: form.password,
      };
      if (isAgencyRole) {
        payload.domain_sovereignty_confirmed = policyAccepted;
        if (form.existing_domain.trim()) {
          payload.existing_domain = form.existing_domain.trim();
          try {
            sessionStorage.setItem("omnia_existing_domain", form.existing_domain.trim());
          } catch {
            /* ignore */
          }
        }
        if (preferredPlan) payload.preferred_plan = preferredPlan;
      }
      await register(payload);
      if (isAgencyRole) {
        nav(`/${lang}/app/onboarding`, { replace: true });
      } else if (form.account_type === "student") {
        nav(`/${lang}/academy`, { replace: true });
      } else {
        nav(`/${lang}/cloud/account`, { replace: true });
      }
    } catch (err) {
      if (isEmailAlreadyRegistered(err)) {
        setDupEmail(true);
        setError(t("auth.email_already_registered"));
      } else {
        setError(formatApiErrorDetail(err.response?.data?.detail) || err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const onGoogle = async (credential) => {
    setError("");
    if (!privacyAccepted) {
      setError(t("auth.privacy_required_error"));
      throw new Error("privacy");
    }
    if (isAgencyRole && !policyAccepted) {
      setError(t("domain_vault.policy_required_error"));
      throw new Error("policy");
    }
    const user = await loginWithGoogle(credential);
    if (!(user?.agency_ids || []).length) {
      nav(`/${lang}/app/onboarding`, { replace: true });
    } else {
      nav(`/${lang}/app/dashboard`, { replace: true });
    }
  };

  return (
    <div
      data-testid="register-page"
      className="min-h-screen bg-stone-100 text-stone-900 flex flex-col"
      style={{ fontFamily: "'Fraunces', Georgia, serif" }}
    >
      <header className="flex items-center justify-between px-5 sm:px-8 md:px-12 py-5 border-b border-stone-300 bg-white">
        <Link to={`/${lang}`} className="flex items-center gap-3 text-xl md:text-2xl tracking-tight font-medium">
          <OmniaLogo variant="mark" size="md" data-testid="register-logo" />
          <span>
            <Brand>OMNIA</Brand>
            <span className="text-stone-400">·</span>
            <Brand className="font-light">app</Brand>
          </span>
        </Link>
        <LanguageSwitcher />
      </header>

      <main className="flex-1 flex items-start justify-center px-5 py-10 md:py-14">
        {showPlanBoxes ? (
          <div className="w-full max-w-5xl" data-testid="register-plan-chooser">
            <div className="text-center mb-10">
              <p className="text-xs font-sans uppercase tracking-[0.3em] text-amber-700 mb-3">
                <Brand>{t("auth.register_eyebrow")}</Brand>
              </p>
              <h1 className="text-3xl md:text-4xl tracking-tight mb-3">
                {t("auth.choose_plan", "Scegli il pacchetto")}
              </h1>
              <p className="font-sans text-sm text-stone-600 max-w-xl mx-auto mb-6">
                {t(
                  "auth.choose_plan_hint",
                  "Tre offerte Founders. Clicca un box: si apre il form di registrazione. Paghi dopo documenti e verifica."
                )}
              </p>
              <label className="inline-block text-left max-w-sm w-full">
                <span className="block text-xs font-sans uppercase tracking-widest text-stone-500 mb-2 text-center">
                  {t("auth.account_type")}
                </span>
                <select
                  data-testid="register-account-type-chooser"
                  value={form.account_type}
                  onChange={(e) => {
                    const v = e.target.value;
                    setForm((f) => ({ ...f, account_type: v }));
                    if (v !== "agency") setChoosingPlan(false);
                  }}
                  className="w-full px-4 py-3 border border-stone-300 bg-white font-sans text-base focus:outline-none focus:border-stone-900"
                >
                  <option value="agency">{t("auth.acct_agency")}</option>
                  <option value="private">{t("auth.acct_private")}</option>
                  <option value="student">{t("auth.acct_student")}</option>
                </select>
              </label>
            </div>

            <div className="grid md:grid-cols-3 gap-5 md:gap-6" data-testid="register-plan-grid">
              {plans.map((p) => (
                <button
                  key={p.tier}
                  type="button"
                  data-testid={`register-plan-${p.tier}`}
                  onClick={() => pickPlan(p.tier)}
                  className={`relative text-left flex flex-col p-6 md:p-7 border transition ${
                    p.highlight
                      ? "border-[#C8A653] bg-white shadow-[0_16px_40px_rgba(11,30,63,0.08)]"
                      : "border-stone-300 bg-white hover:border-[#0B1E3F]"
                  }`}
                >
                  {p.highlight ? (
                    <span className="absolute -top-3 left-5 text-[10px] font-sans uppercase tracking-widest bg-[#C8A653] text-[#0B1E3F] px-3 py-1">
                      {t("landing.pricing_popular", "Consigliato")}
                    </span>
                  ) : null}
                  <h2 className="text-2xl tracking-tight mb-1">{p.name}</h2>
                  <p className="font-sans text-xs text-stone-500 mb-5 uppercase tracking-wider">
                    {p.agents} {t("landing.pricing_agents", "utenti")} · {p.properties}{" "}
                    {t("landing.pricing_listings", "immobili")}
                  </p>
                  <p className="mb-1">
                    <span className="text-4xl tracking-tight">€{p.monthly}</span>
                    <span className="font-sans text-sm text-stone-500 ml-1">
                      /{t("landing.pricing_month", "mese")}
                    </span>
                  </p>
                  <p className="font-sans text-sm text-stone-500 mb-5">
                    {t("landing.pricing_or_year", "oppure")} <strong>€{p.yearly}</strong>
                    {t("auth.per_year", "/anno")}
                  </p>
                  <ul className="font-sans text-sm text-stone-700 space-y-2 mb-6 flex-1">
                    {p.features.map((f) => (
                      <li key={f} className="flex gap-2">
                        <span className="text-[#1F6B5C]" aria-hidden>
                          —
                        </span>
                        <span>{f}</span>
                      </li>
                    ))}
                    <li className="flex gap-2">
                      <span className="text-[#1F6B5C]" aria-hidden>
                        —
                      </span>
                      <span>
                        {p.credits} {t("landing.pricing_credits", "crediti AI / mese")}
                      </span>
                    </li>
                  </ul>
                  <span
                    className={`mt-auto text-center text-xs font-sans uppercase tracking-widest px-4 py-3 ${
                      p.highlight
                        ? "bg-[#0B1E3F] text-[#F5F1E8]"
                        : "border border-[#0B1E3F] text-[#0B1E3F]"
                    }`}
                  >
                    {t("auth.plan_cta", "Scegli e registrati")} →
                  </span>
                </button>
              ))}
            </div>

            <p className="mt-8 text-center font-sans text-sm text-stone-600">
              {t("auth.have_account")}{" "}
              <Link to={loginHref} className="text-stone-900 underline">
                {t("auth.login_now")}
              </Link>
            </p>
          </div>
        ) : (
          <form
            onSubmit={submit}
            data-testid="register-form"
            className="w-full max-w-md bg-white border border-stone-300 p-8 md:p-10"
          >
            <p className="text-xs font-sans uppercase tracking-[0.3em] text-amber-700 mb-3">
              <Brand>{t("auth.register_eyebrow")}</Brand>
            </p>
            <h1 className="text-3xl md:text-4xl tracking-tight mb-3">{t("auth.register_title")}</h1>
            <p className="mb-6 font-sans text-sm text-stone-600">{t("auth.register_lead")}</p>

            {isAgencyRole && selectedPlan ? (
              <div
                className="mb-6 border border-[#0B1E3F]/20 bg-[#0B1E3F]/[0.03] px-4 py-3"
                data-testid="register-selected-plan"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-[10px] font-sans uppercase tracking-widest text-stone-500 mb-1">
                      {t("auth.plan_selected", "Pacchetto scelto")}
                    </p>
                    <p className="text-lg tracking-tight">
                      {selectedPlan.name}{" "}
                      <span className="font-sans text-sm text-stone-600">
                        · €{selectedPlan.monthly}
                        {t("auth.per_month", "/mese")}
                      </span>
                    </p>
                  </div>
                  <button
                    type="button"
                    data-testid="register-change-plan"
                    onClick={() => setChoosingPlan(true)}
                    className="shrink-0 text-xs font-sans uppercase tracking-widest text-[#1F6B5C] underline"
                  >
                    {t("auth.change_plan", "Cambia")}
                  </button>
                </div>
              </div>
            ) : null}

            <label className="block mb-6">
              <span className="block text-xs font-sans uppercase tracking-widest text-stone-500 mb-2">
                {t("auth.account_type")}
              </span>
              <select
                data-testid="register-account-type"
                value={form.account_type}
                onChange={(e) => {
                  const v = e.target.value;
                  setForm((f) => ({ ...f, account_type: v }));
                  if (v === "agency" && !preferredPlan) setChoosingPlan(true);
                }}
                className="w-full px-4 py-3 border border-stone-300 bg-stone-50 font-sans text-base focus:outline-none focus:border-stone-900"
              >
                <option value="agency">{t("auth.acct_agency")}</option>
                <option value="private">{t("auth.acct_private")}</option>
                <option value="student">{t("auth.acct_student")}</option>
              </select>
              {isAgencyRole ? (
                <span className="mt-2 block text-xs font-sans text-stone-500">
                  {t("auth.acct_agency_hint")}
                </span>
              ) : null}
            </label>

            {["name", "email"].map((f) => (
              <label key={f} className="block mb-5">
                <span className="block text-xs font-sans uppercase tracking-widest text-stone-500 mb-2">
                  {t(`auth.${f}`)}
                </span>
                <input
                  data-testid={`register-${f}`}
                  type={f === "email" ? "email" : "text"}
                  required
                  value={form[f]}
                  onChange={set(f)}
                  className="w-full px-4 py-3 border border-stone-300 bg-stone-50 font-sans text-base focus:outline-none focus:border-stone-900"
                />
              </label>
            ))}

            <label className="block mb-5">
              <span className="block text-xs font-sans uppercase tracking-widest text-stone-500 mb-2">
                {t("auth.password")}
              </span>
              <PasswordField
                data-testid="register-password"
                required
                minLength={8}
                value={form.password}
                onChange={set("password")}
                autoComplete="new-password"
                className="w-full px-4 py-3 pr-12 border border-stone-300 bg-stone-50 font-sans text-base focus:outline-none focus:border-stone-900"
              />
              {isAgencyRole ? (
                <p
                  data-testid="register-password-hint"
                  className="mt-2 font-sans text-xs text-stone-600"
                >
                  {t(
                    "auth.agency_password_hint",
                    "Dopo la verifica riceverai la password per accedere al gestionale."
                  )}
                </p>
              ) : null}
            </label>

            <label
              className="flex items-start gap-3 mb-6 cursor-pointer"
              data-testid="register-privacy-label"
            >
              <input
                type="checkbox"
                data-testid="register-privacy-checkbox"
                checked={privacyAccepted}
                onChange={(e) => setPrivacyAccepted(e.target.checked)}
                className="mt-1 w-4 h-4 accent-[#1F6B5C]"
              />
              <span className="text-xs font-sans text-stone-700 leading-relaxed">
                <Trans
                  i18nKey="auth.privacy_checkbox"
                  components={{
                    privacy: (
                      <Link
                        to={`/${lang}/privacy`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="underline text-[#0B1E3F] hover:text-[#1F6B5C]"
                        data-testid="register-privacy-link"
                      />
                    ),
                  }}
                />
              </span>
            </label>

            {isAgencyRole ? (
              <div
                data-testid="domain-vault-block"
                className="mb-6 border border-emerald-800/30 bg-emerald-50/60 p-5"
                style={{ borderLeftWidth: "3px", borderLeftColor: "#1F6B5C" }}
              >
                <div className="flex items-start gap-3 mb-4">
                  <span
                    aria-hidden="true"
                    className="mt-0.5 inline-flex items-center justify-center w-8 h-8 rounded-full bg-[#1F6B5C] text-white text-sm shrink-0"
                  >
                    🛡️
                  </span>
                  <div>
                    <p className="text-sm md:text-base font-medium tracking-tight text-[#0B1E3F]">
                      {t("domain_vault.badge")}
                    </p>
                    <p className="text-xs font-sans text-stone-600 mt-1">
                      {t("domain_vault.badge_subtitle")}
                    </p>
                  </div>
                </div>

                <label className="block mb-3">
                  <span className="block text-xs font-sans uppercase tracking-widest text-stone-500 mb-2">
                    {t("domain_vault.existing_domain_label")}
                  </span>
                  <input
                    data-testid="register-existing-domain"
                    type="text"
                    value={form.existing_domain}
                    onChange={set("existing_domain")}
                    placeholder={t("domain_vault.existing_domain_placeholder")}
                    className="w-full px-4 py-3 border border-stone-300 bg-white font-sans text-base focus:outline-none focus:border-stone-900"
                  />
                  <span className="mt-2 block text-xs font-sans text-stone-500">
                    {t("domain_vault.existing_domain_help")}{" "}
                    <Link
                      to={`/${lang}/verifica-dominio`}
                      className="underline text-[#1F6B5C] hover:text-[#0B1E3F]"
                      data-testid="domain-vault-verify-link"
                    >
                      {t("domain_vault.existing_domain_verify_cta")} →
                    </Link>
                  </span>
                </label>

                <label
                  className="flex items-start gap-3 mt-4 cursor-pointer"
                  data-testid="domain-vault-policy-label"
                >
                  <input
                    type="checkbox"
                    data-testid="register-policy-checkbox"
                    checked={policyAccepted}
                    onChange={(e) => setPolicyAccepted(e.target.checked)}
                    className="mt-1 w-4 h-4 accent-[#1F6B5C]"
                  />
                  <span className="text-xs font-sans text-stone-700 leading-relaxed">
                    <Trans
                      i18nKey="domain_vault.policy_checkbox"
                      components={{
                        policy: (
                          <Link
                            to={`/${lang}/domain-sovereignty-policy`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="underline text-[#0B1E3F] hover:text-[#1F6B5C]"
                            data-testid="domain-vault-policy-link"
                          />
                        ),
                      }}
                    />
                  </span>
                </label>
              </div>
            ) : null}

            {error ? (
              <div
                data-testid="register-error"
                className="mb-5 p-3 border border-red-300 bg-red-50 text-red-700 text-sm font-sans"
              >
                <p>{error}</p>
                {dupEmail ? (
                  <p className="mt-2">
                    <Link
                      to={loginHref}
                      data-testid="register-login-link"
                      className="underline font-medium text-stone-900"
                    >
                      {t("auth.login_now")} →
                    </Link>
                  </p>
                ) : null}
              </div>
            ) : null}

            <button
              data-testid="register-submit"
              type="submit"
              disabled={loading}
              className="w-full bg-stone-900 text-stone-50 px-6 py-4 text-xs sm:text-sm font-sans uppercase tracking-widest hover:bg-stone-700 transition disabled:opacity-50"
            >
              {loading ? t("common.loading") : t("auth.register_cta")} →
            </button>

            <GoogleSignInButton
              onSuccess={onGoogle}
              onError={(msg) => setError(msg)}
              disabled={loading}
              label={t("auth.continue_google")}
            />

            <p className="mt-8 pt-6 border-t border-stone-200 text-sm font-sans text-stone-600">
              {t("auth.have_account")}{" "}
              <Link
                to={loginHref}
                data-testid="register-have-account-login"
                className="text-stone-900 underline"
              >
                {t("auth.login_now")}
              </Link>
            </p>
          </form>
        )}
      </main>
    </div>
  );
}

import React, { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { api } from "../../shared/lib/api";
import { useAuth, formatApiErrorDetail } from "../../shared/lib/auth";
import { validateItalianVat, validateFiscalCodeSoft } from "../../shared/lib/italianFiscal";
import Brand from "../../shared/components/Brand";
import OmniaLogo from "../../shared/components/OmniaLogo";
import LanguageSwitcher from "../../shared/components/LanguageSwitcher";
import AddressAutocomplete from "../immocloud/components/AddressAutocomplete";

const STEPS = ["identity", "fiscal", "branding", "done"];
const PREFERRED_PLAN_KEY = "omnia_preferred_plan";

export default function OnboardingWizard() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();
  const { refresh } = useAuth();
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [vatHint, setVatHint] = useState("");
  const [cfHint, setCfHint] = useState("");
  const [logoUploading, setLogoUploading] = useState(false);
  const [logoName, setLogoName] = useState("");
  const logoInputRef = useRef(null);

  const preferredPlan = (() => {
    try {
      const p = (sessionStorage.getItem(PREFERRED_PLAN_KEY) || "").toLowerCase();
      return ["starter", "pro", "agency"].includes(p) ? p : "";
    } catch {
      return "";
    }
  })();

  const [form, setForm] = useState({
    display_name: "",
    fiscal: {
      legal_name: "",
      vat_number: "",
      fiscal_code: "",
      rea: "",
    },
    address: {
      street: "",
      city: "",
      province: "",
      postal_code: "",
      country: "IT",
    },
    contact: {
      email: "",
      phone: "",
      website: "",
      pec: "",
    },
    branding: {
      logo_url: "",
      primary_color: "#0B1E3F",
      accent_color: "#1F6B5C",
      tagline: "",
    },
  });

  const update = (group, key, value) => {
    if (group === null) {
      setForm({ ...form, [key]: value });
    } else {
      setForm({ ...form, [group]: { ...form[group], [key]: value } });
    }
  };

  const onAddressSelect = (rec) => {
    if (!rec) return;
    setForm((prev) => ({
      ...prev,
      address: {
        ...prev.address,
        street: rec.normalized || prev.address.street,
        city: rec.comune || prev.address.city,
        province: (rec.provincia_sigla || prev.address.province || "").toUpperCase().slice(0, 2),
        postal_code: rec.cap || prev.address.postal_code,
        country: "IT",
      },
    }));
  };

  const canContinue = () => {
    if (step === 0) return form.display_name.trim().length >= 2;
    if (step === 1) return form.fiscal.legal_name.trim().length >= 2;
    return true;
  };

  const validateFiscalStep = () => {
    setVatHint("");
    setCfHint("");
    const vat = validateItalianVat(form.fiscal.vat_number);
    if (!vat.ok) {
      setVatHint(t("onboarding.vat_soft_error"));
      return false;
    }
    const cf = validateFiscalCodeSoft(form.fiscal.fiscal_code);
    if (!cf.ok) {
      setCfHint(t("onboarding.cf_soft_error"));
      return false;
    }
    return true;
  };

  const goNext = () => {
    if (step === 1 && !validateFiscalStep()) return;
    setStep(step + 1);
  };

  const submitFinal = async () => {
    setError("");
    if (!validateFiscalStep()) {
      setStep(1);
      return;
    }
    if (!(form.branding.logo_url || "").trim()) {
      setError(t("onboarding.logo_required", "Carica il file del marchio/logo prima di continuare."));
      return;
    }
    setSubmitting(true);
    try {
      const cleanGroup = (obj) => {
        const out = {};
        for (const [k, v] of Object.entries(obj || {})) {
          if (typeof v === "string" && v.trim() === "") continue;
          out[k] = v;
        }
        return out;
      };
      const payload = {
        display_name: form.display_name.trim(),
        fiscal: cleanGroup(form.fiscal),
        address: cleanGroup(form.address),
        contact: cleanGroup(form.contact),
        branding: cleanGroup(form.branding),
      };
      if (preferredPlan) payload.preferred_plan_tier = preferredPlan;
      await api.post("/app/agencies", payload);
      // Critico: refresh sessione → ruolo agency_admin (altrimenti dashboard = 403 FE)
      if (typeof refresh === "function") {
        await refresh();
      }
      setStep(3);
      // CRM locked until Ops activate — sala d'attesa, non dashboard
      setTimeout(() => nav(`/${lang}/app/waiting-activation`, { replace: true }), 1200);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (detail === "agency_already_exists") {
        setError(t("onboarding.error_already_exists"));
      } else if (err?.response?.status === 403) {
        setError(t("onboarding.error_forbidden"));
      } else {
        setError(formatApiErrorDetail(detail) || t("common.error"));
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      data-testid="onboarding-wizard"
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
            <span>
              <Brand>OMNIA</Brand>
              <span className="text-stone-400">·</span>
              <Brand className="font-light text-stone-500">app</Brand>
            </span>
          </span>
          <LanguageSwitcher />
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-5 sm:px-8 py-10 md:py-16">
        <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-3">
          <Brand>{t("onboarding.eyebrow")}</Brand>
        </p>
        <h1
          className="text-3xl sm:text-4xl md:text-5xl tracking-tight mb-3"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        >
          {t("onboarding.title")}
        </h1>
        <p className="text-stone-600 mb-10 max-w-xl">{t("onboarding.subtitle")}</p>

        <ol className="flex items-center gap-2 mb-10 text-xs uppercase tracking-widest text-stone-500">
          {STEPS.map((s, i) => (
            <li key={s} className="flex items-center gap-2" data-testid={`step-indicator-${s}`}>
              <span
                className={`w-7 h-7 inline-flex items-center justify-center rounded-full border ${
                  i <= step
                    ? "bg-stone-900 text-stone-50 border-stone-900"
                    : "border-stone-300 text-stone-400"
                }`}
              >
                {i + 1}
              </span>
              <span className={i === step ? "text-stone-900 font-semibold" : ""}>
                {t(`onboarding.step_${s}`)}
              </span>
              {i < STEPS.length - 1 && <span className="text-stone-300">·</span>}
            </li>
          ))}
        </ol>

        {step === 0 && (
          <div data-testid="step-identity" className="space-y-5">
            <Field label={t("onboarding.display_name")} hint={t("onboarding.display_name_hint")} required>
              <input
                data-testid="onb-display-name"
                value={form.display_name}
                onChange={(e) => update(null, "display_name", e.target.value)}
                className="form-input"
                autoFocus
              />
            </Field>
          </div>
        )}

        {step === 1 && (
          <div data-testid="step-fiscal" className="space-y-5">
            <p className="text-sm text-stone-600 bg-white border border-stone-200 rounded-md px-3 py-2">
              {t("onboarding.data_honesty")}
            </p>
            <Field label={t("onboarding.legal_name")} hint={t("onboarding.legal_name_hint")} required>
              <input
                data-testid="onb-legal-name"
                value={form.fiscal.legal_name}
                onChange={(e) => update("fiscal", "legal_name", e.target.value)}
                className="form-input"
              />
            </Field>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Field label={t("onboarding.vat_number")} hint={vatHint || t("onboarding.vat_hint")}>
                <input
                  data-testid="onb-vat"
                  value={form.fiscal.vat_number}
                  onChange={(e) => update("fiscal", "vat_number", e.target.value)}
                  className="form-input"
                  placeholder="11 cifre"
                />
              </Field>
              <Field label={t("onboarding.fiscal_code")} hint={cfHint || undefined}>
                <input
                  data-testid="onb-fiscal-code"
                  value={form.fiscal.fiscal_code}
                  onChange={(e) => update("fiscal", "fiscal_code", e.target.value)}
                  className="form-input"
                />
              </Field>
              <Field label={t("onboarding.rea")}>
                <input
                  data-testid="onb-rea"
                  value={form.fiscal.rea}
                  onChange={(e) => update("fiscal", "rea", e.target.value)}
                  className="form-input"
                />
              </Field>
            </div>
            <hr className="border-stone-200 my-2" />
            <Field label={t("onboarding.address_street")} hint={t("onboarding.address_hint")}>
              <AddressAutocomplete
                value={form.address.street}
                onChange={(text) => update("address", "street", text)}
                onSelect={onAddressSelect}
                placeholder={t("onboarding.address_placeholder")}
                testid="onb-street"
                inputClassName="form-input"
                className="w-full"
              />
            </Field>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Field label={t("onboarding.address_city")}>
                <input
                  data-testid="onb-city"
                  value={form.address.city}
                  onChange={(e) => update("address", "city", e.target.value)}
                  className="form-input"
                />
              </Field>
              <Field label={t("onboarding.address_province")}>
                <input
                  data-testid="onb-province"
                  value={form.address.province}
                  maxLength={2}
                  onChange={(e) => update("address", "province", e.target.value.toUpperCase())}
                  className="form-input"
                />
              </Field>
              <Field label={t("onboarding.address_postal_code")}>
                <input
                  data-testid="onb-postal"
                  value={form.address.postal_code}
                  onChange={(e) => update("address", "postal_code", e.target.value)}
                  className="form-input"
                />
              </Field>
            </div>
            <hr className="border-stone-200 my-2" />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Field label={t("onboarding.contact_email")}>
                <input
                  type="email"
                  data-testid="onb-contact-email"
                  value={form.contact.email}
                  onChange={(e) => update("contact", "email", e.target.value)}
                  className="form-input"
                />
              </Field>
              <Field label={t("onboarding.contact_phone")}>
                <input
                  data-testid="onb-phone"
                  value={form.contact.phone}
                  onChange={(e) => update("contact", "phone", e.target.value)}
                  className="form-input"
                />
              </Field>
            </div>
            <Field
              label={t("onboarding.contact_pec", "PEC")}
              hint={t("onboarding.pec_hint", "Serve all’identificazione clientela (GDPR).")}
            >
              <input
                type="email"
                data-testid="onb-pec"
                value={form.contact.pec}
                onChange={(e) => update("contact", "pec", e.target.value)}
                className="form-input"
                placeholder="pec@agenzia.it"
              />
            </Field>
            <Field label={t("onboarding.contact_website")}>
              <input
                data-testid="onb-website"
                value={form.contact.website}
                onChange={(e) => update("contact", "website", e.target.value)}
                className="form-input"
                placeholder="https://"
              />
            </Field>
          </div>
        )}

        {step === 2 && (
          <div data-testid="step-branding" className="space-y-5">
            {preferredPlan ? (
              <p className="text-sm text-stone-600 bg-white border border-stone-200 rounded-md px-3 py-2">
                {t("onboarding.preferred_plan", "Piano scelto")}:{" "}
                <span className="font-medium uppercase">{preferredPlan}</span>
              </p>
            ) : null}
            <Field
              label={t("onboarding.logo_file", "Marchio / logo")}
              hint={t(
                "onboarding.logo_hint",
                "Carica il file del logo (PNG/JPG/WebP/SVG, max 2 MB). Lo usiamo per sito e materiali."
              )}
            >
              <input
                ref={logoInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp,image/svg+xml"
                data-testid="onb-logo-file"
                className="block w-full text-sm text-stone-600"
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  setLogoUploading(true);
                  setError("");
                  try {
                    const fd = new FormData();
                    fd.append("file", file, file.name);
                    const r = await api.post("/app/agencies/onboarding/logo", fd, {
                      timeout: 60000,
                    });
                    update("branding", "logo_url", r.data.url);
                    setLogoName(file.name);
                  } catch (err) {
                    setError(
                      formatApiErrorDetail(err?.response?.data?.detail) ||
                        t("onboarding.logo_upload_error", "Upload logo non riuscito.")
                    );
                  } finally {
                    setLogoUploading(false);
                  }
                }}
              />
              {logoUploading ? (
                <p className="text-xs text-stone-500 mt-1">{t("common.loading")}</p>
              ) : null}
              {form.branding.logo_url ? (
                <div className="mt-3 flex items-center gap-3">
                  <img
                    src={form.branding.logo_url}
                    alt=""
                    className="h-12 w-12 object-contain border border-stone-200 bg-white rounded"
                  />
                  <span className="text-xs text-stone-600">{logoName || "logo"}</span>
                </div>
              ) : null}
            </Field>
            <Field label={t("onboarding.tagline")} hint={t("onboarding.tagline_hint")}>
              <input
                data-testid="onb-tagline"
                value={form.branding.tagline}
                onChange={(e) => update("branding", "tagline", e.target.value)}
                className="form-input"
                placeholder={t("onboarding.tagline_placeholder")}
              />
            </Field>
            <div className="grid grid-cols-2 gap-4">
              <Field label={t("onboarding.primary_color")}>
                <div className="flex gap-2">
                  <input
                    type="color"
                    data-testid="onb-primary-color"
                    value={form.branding.primary_color}
                    onChange={(e) => update("branding", "primary_color", e.target.value)}
                    className="h-10 w-14 cursor-pointer border border-stone-300 rounded"
                  />
                  <input
                    value={form.branding.primary_color}
                    onChange={(e) => update("branding", "primary_color", e.target.value)}
                    className="form-input flex-1"
                  />
                </div>
              </Field>
              <Field label={t("onboarding.accent_color")}>
                <div className="flex gap-2">
                  <input
                    type="color"
                    data-testid="onb-accent-color"
                    value={form.branding.accent_color}
                    onChange={(e) => update("branding", "accent_color", e.target.value)}
                    className="h-10 w-14 cursor-pointer border border-stone-300 rounded"
                  />
                  <input
                    value={form.branding.accent_color}
                    onChange={(e) => update("branding", "accent_color", e.target.value)}
                    className="form-input flex-1"
                  />
                </div>
              </Field>
            </div>

            <div className="mt-6 p-5 bg-white border border-stone-200 rounded-lg">
              <p className="text-xs uppercase tracking-widest text-stone-500 mb-3">
                {t("onboarding.review_title")}
              </p>
              <h3
                className="text-2xl mb-1"
                style={{ fontFamily: "'Fraunces', Georgia, serif", color: form.branding.primary_color }}
              >
                {form.display_name || "—"}
              </h3>
              <p className="text-sm text-stone-600">{form.branding.tagline || form.fiscal.legal_name}</p>
              <div className="mt-3 flex gap-2">
                <span
                  className="inline-block w-6 h-6 rounded border border-stone-300"
                  style={{ background: form.branding.primary_color }}
                  title="Primary"
                />
                <span
                  className="inline-block w-6 h-6 rounded border border-stone-300"
                  style={{ background: form.branding.accent_color }}
                  title="Accent"
                />
              </div>
            </div>
            <p className="text-sm text-stone-500">{t("onboarding.review_subtitle")}</p>
          </div>
        )}

        {step === 3 && (
          <div data-testid="step-done" className="text-center py-12">
            <div className="text-5xl mb-4">✓</div>
            <h2
              className="text-3xl tracking-tight mb-2"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {t("onboarding.success_title")}
            </h2>
            <p className="text-stone-600">{t("onboarding.success_subtitle")}</p>
          </div>
        )}

        {error && (
          <p data-testid="onb-error" className="mt-6 text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">
            {error}
          </p>
        )}

        {step < 3 && (
          <div className="flex items-center justify-between mt-10 pt-6 border-t border-stone-200">
            <button
              data-testid="onb-back-btn"
              type="button"
              onClick={() => setStep(Math.max(0, step - 1))}
              disabled={step === 0 || submitting}
              className="px-4 py-2 text-sm text-stone-600 hover:text-stone-900 disabled:opacity-30"
            >
              ← {t("onboarding.back")}
            </button>
            {step < 2 ? (
              <button
                data-testid="onb-next-btn"
                type="button"
                onClick={goNext}
                disabled={!canContinue() || submitting}
                className="px-6 py-3 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest font-medium rounded-md hover:bg-stone-700 disabled:opacity-50 transition"
              >
                {t("onboarding.next")} →
              </button>
            ) : (
              <button
                data-testid="onb-create-btn"
                type="button"
                onClick={submitFinal}
                disabled={submitting}
                className="px-6 py-3 bg-emerald-700 text-stone-50 text-xs uppercase tracking-widest font-medium rounded-md hover:bg-emerald-800 disabled:opacity-50 transition"
              >
                {submitting ? t("onboarding.creating") : t("onboarding.create")} →
              </button>
            )}
          </div>
        )}
      </main>

      <style>{`
        .form-input {
          width: 100%;
          padding: 0.625rem 0.75rem;
          background: white;
          border: 1px solid #d6d3d1;
          border-radius: 6px;
          font-size: 0.875rem;
          color: #1c1917;
          transition: border-color 0.15s, box-shadow 0.15s;
        }
        .form-input:focus {
          outline: none;
          border-color: #1c1917;
          box-shadow: 0 0 0 3px rgba(28,25,23,0.06);
        }
      `}</style>
    </div>
  );
}

function Field({ label, hint, required, children }) {
  return (
    <div>
      <label className="block text-xs uppercase tracking-widest text-stone-600 mb-1.5">
        {label}
        {required && <span className="text-red-600 ml-1">*</span>}
      </label>
      {children}
      {hint && <p className="text-xs text-stone-400 mt-1">{hint}</p>}
    </div>
  );
}

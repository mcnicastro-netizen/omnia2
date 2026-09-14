import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { api } from "../../shared/lib/api";
import { formatApiErrorDetail } from "../../shared/lib/auth";
import Brand from "../../shared/components/Brand";
import OmniaLogo from "../../shared/components/OmniaLogo";
import LanguageSwitcher from "../../shared/components/LanguageSwitcher";

const STEPS = ["identity", "fiscal", "branding", "done"];

export default function OnboardingWizard() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    display_name: "",
    fiscal: {
      legal_name: "",
      vat_number: "",
      fiscal_code: "",
      rea: "",
      fiaip_code: "",
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

  const canContinue = () => {
    if (step === 0) return form.display_name.trim().length >= 2;
    if (step === 1) return form.fiscal.legal_name.trim().length >= 2;
    return true;
  };

  const submitFinal = async () => {
    setError("");
    setSubmitting(true);
    try {
      // Strip empty strings from optional groups so Pydantic Optional[EmailStr] etc. accept them
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
      await api.post("/app/agencies", payload);
      // mark onboarding completed
      await api.patch("/app/agencies/me", { onboarding_completed: true });
      setStep(3);
      setTimeout(() => nav(`/${lang}/app/dashboard`, { replace: true }), 1500);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (detail === "agency_already_exists") {
        setError(t("onboarding.error_already_exists"));
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
          <Brand>ImmoWeb · Onboarding</Brand>
        </p>
        <h1
          className="text-3xl sm:text-4xl md:text-5xl tracking-tight mb-3"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        >
          {t("onboarding.title")}
        </h1>
        <p className="text-stone-600 mb-10 max-w-xl">{t("onboarding.subtitle")}</p>

        {/* Progress */}
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

        {/* STEP 0 — Identity */}
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

        {/* STEP 1 — Fiscal */}
        {step === 1 && (
          <div data-testid="step-fiscal" className="space-y-5">
            <Field label={t("onboarding.legal_name")} hint={t("onboarding.legal_name_hint")} required>
              <input
                data-testid="onb-legal-name"
                value={form.fiscal.legal_name}
                onChange={(e) => update("fiscal", "legal_name", e.target.value)}
                className="form-input"
              />
            </Field>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Field label={t("onboarding.vat_number")}>
                <input
                  data-testid="onb-vat"
                  value={form.fiscal.vat_number}
                  onChange={(e) => update("fiscal", "vat_number", e.target.value)}
                  className="form-input"
                />
              </Field>
              <Field label={t("onboarding.fiscal_code")}>
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
              <Field label={t("onboarding.fiaip_code")}>
                <input
                  data-testid="onb-fiaip"
                  value={form.fiscal.fiaip_code}
                  onChange={(e) => update("fiscal", "fiaip_code", e.target.value)}
                  className="form-input"
                />
              </Field>
            </div>
            <hr className="border-stone-200 my-2" />
            <Field label={t("onboarding.address_street")}>
              <input
                data-testid="onb-street"
                value={form.address.street}
                onChange={(e) => update("address", "street", e.target.value)}
                className="form-input"
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

        {/* STEP 2 — Branding */}
        {step === 2 && (
          <div data-testid="step-branding" className="space-y-5">
            <Field label={t("onboarding.logo_url")}>
              <input
                data-testid="onb-logo"
                value={form.branding.logo_url}
                onChange={(e) => update("branding", "logo_url", e.target.value)}
                className="form-input"
                placeholder="https://..."
              />
            </Field>
            <Field label={t("onboarding.tagline")}>
              <input
                data-testid="onb-tagline"
                value={form.branding.tagline}
                onChange={(e) => update("branding", "tagline", e.target.value)}
                className="form-input"
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

            {/* Review summary */}
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

        {/* STEP 3 — Done */}
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

        {/* Actions */}
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
                onClick={() => setStep(step + 1)}
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

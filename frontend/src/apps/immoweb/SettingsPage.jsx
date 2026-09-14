import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import AgencyShell from "./components/AgencyShell";
import { api } from "../../shared/lib/api";
import { formatApiErrorDetail } from "../../shared/lib/auth";

export default function SettingsPage() {
  const { t } = useTranslation();
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  useEffect(() => {
    api
      .get("/app/agencies/me")
      .then((r) => setForm(r.data))
      .catch(() =>
        setForm({
          display_name: "",
          fiscal: {},
          contact: {},
          address: {},
          branding: {},
          website: { mode: null, external_url: "", template_id: "" },
        }),
      );
  }, []);

  if (!form) {
    return (
      <AgencyShell current="settings">
        <p className="text-sm text-stone-500">{t("common.loading")}</p>
      </AgencyShell>
    );
  }

  const update = (group, key, value) => {
    if (group === null) setForm({ ...form, [key]: value });
    else setForm({ ...form, [group]: { ...form[group], [key]: value } });
  };

  const setWebsiteMode = (mode) => {
    // toggle off if clicked again
    const next = form.website?.mode === mode ? null : mode;
    setForm({ ...form, website: { ...(form.website || {}), mode: next } });
  };

  const save = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const cleanGroup = (obj) => {
        const out = {};
        for (const [k, v] of Object.entries(obj || {})) {
          if (typeof v === "string" && v.trim() === "") continue;
          if (v === null || v === undefined) continue;
          out[k] = v;
        }
        return out;
      };
      const website = { ...(form.website || {}) };
      // strip empty
      const websiteClean = cleanGroup(website);
      // keep `mode` even when null? It must be explicit so backend can save null.
      if (website.mode === null || website.mode === undefined) {
        websiteClean.mode = null;
      } else {
        websiteClean.mode = website.mode;
      }
      const payload = {
        display_name: form.display_name,
        fiscal: cleanGroup(form.fiscal),
        address: cleanGroup(form.address),
        contact: cleanGroup(form.contact),
        branding: cleanGroup(form.branding),
        website: websiteClean,
      };
      const { data } = await api.patch("/app/agencies/me", payload);
      setForm(data);
      setToast(t("settings.saved"));
      setTimeout(() => setToast(""), 2500);
    } catch (err) {
      setError(formatApiErrorDetail(err?.response?.data?.detail) || t("settings.save_error"));
    } finally {
      setSaving(false);
    }
  };

  const websiteMode = form.website?.mode || null;

  return (
    <AgencyShell current="settings">
      <section data-testid="settings-page" className="max-w-3xl space-y-6">
        <div>
          <h1
            className="text-3xl md:text-4xl tracking-tight"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            {t("settings.title")}
          </h1>
          <p className="text-stone-600 mt-1">{t("settings.subtitle")}</p>
        </div>

        <form onSubmit={save} className="space-y-8">
          <Section label={t("onboarding.step_identity")}>
            <FieldRow label={t("onboarding.display_name")}>
              <input
                data-testid="settings-display-name"
                value={form.display_name || ""}
                onChange={(e) => update(null, "display_name", e.target.value)}
                className="form-input"
              />
            </FieldRow>
            <FieldRow label={t("settings.tagline")}>
              <input
                data-testid="settings-tagline"
                value={form.branding?.tagline || ""}
                onChange={(e) => update("branding", "tagline", e.target.value)}
                className="form-input"
                placeholder={t("settings.tagline_placeholder")}
              />
            </FieldRow>
          </Section>

          <Section label={t("onboarding.step_fiscal")}>
            <FieldRow label={t("onboarding.legal_name")}>
              <input
                data-testid="settings-legal-name"
                value={form.fiscal?.legal_name || ""}
                onChange={(e) => update("fiscal", "legal_name", e.target.value)}
                className="form-input"
              />
            </FieldRow>
            <div className="grid grid-cols-2 gap-4">
              <FieldRow label={t("onboarding.vat_number")}>
                <input
                  value={form.fiscal?.vat_number || ""}
                  onChange={(e) => update("fiscal", "vat_number", e.target.value)}
                  className="form-input"
                />
              </FieldRow>
              <FieldRow label={t("onboarding.fiscal_code")}>
                <input
                  value={form.fiscal?.fiscal_code || ""}
                  onChange={(e) => update("fiscal", "fiscal_code", e.target.value)}
                  className="form-input"
                />
              </FieldRow>
            </div>
            <FieldRow label={t("onboarding.address_street")}>
              <input
                value={form.address?.street || ""}
                onChange={(e) => update("address", "street", e.target.value)}
                className="form-input"
              />
            </FieldRow>
            <div className="grid grid-cols-3 gap-4">
              <FieldRow label={t("onboarding.address_city")}>
                <input
                  value={form.address?.city || ""}
                  onChange={(e) => update("address", "city", e.target.value)}
                  className="form-input"
                />
              </FieldRow>
              <FieldRow label={t("onboarding.address_province")}>
                <input
                  value={form.address?.province || ""}
                  maxLength={2}
                  onChange={(e) => update("address", "province", e.target.value.toUpperCase())}
                  className="form-input"
                />
              </FieldRow>
              <FieldRow label={t("onboarding.address_postal_code")}>
                <input
                  value={form.address?.postal_code || ""}
                  onChange={(e) => update("address", "postal_code", e.target.value)}
                  className="form-input"
                />
              </FieldRow>
            </div>
          </Section>

          <Section label={t("settings.contact_label")}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FieldRow label={t("onboarding.contact_email")}>
                <input
                  type="email"
                  value={form.contact?.email || ""}
                  onChange={(e) => update("contact", "email", e.target.value)}
                  className="form-input"
                />
              </FieldRow>
              <FieldRow label={t("onboarding.contact_phone")}>
                <input
                  value={form.contact?.phone || ""}
                  onChange={(e) => update("contact", "phone", e.target.value)}
                  className="form-input"
                />
              </FieldRow>
            </div>
          </Section>

          {/* WEBSITE — the new simplified section */}
          <Section label={t("settings.website_label")}>
            <p className="text-sm text-stone-600 mb-4">
              {t("settings.website_intro")}
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                type="button"
                data-testid="website-mode-external"
                onClick={() => setWebsiteMode("external")}
                className={`text-left p-5 border rounded-lg transition ${
                  websiteMode === "external"
                    ? "border-emerald-700 bg-emerald-50/60 ring-2 ring-emerald-100"
                    : "border-stone-300 bg-white hover:border-stone-500"
                }`}
              >
                <p className="text-xs uppercase tracking-widest text-stone-500 mb-1">
                  {t("settings.website_external_tag")}
                </p>
                <p className="font-semibold text-stone-900 mb-1">
                  {t("settings.website_external_title")}
                </p>
                <p className="text-sm text-stone-600">
                  {t("settings.website_external_desc")}
                </p>
              </button>

              <button
                type="button"
                data-testid="website-mode-template"
                onClick={() => setWebsiteMode("omnia_template")}
                className={`text-left p-5 border rounded-lg transition ${
                  websiteMode === "omnia_template"
                    ? "border-emerald-700 bg-emerald-50/60 ring-2 ring-emerald-100"
                    : "border-stone-300 bg-white hover:border-stone-500"
                }`}
              >
                <p className="text-xs uppercase tracking-widest text-stone-500 mb-1">
                  {t("settings.website_template_tag")}
                </p>
                <p className="font-semibold text-stone-900 mb-1">
                  {t("settings.website_template_title")}
                </p>
                <p className="text-sm text-stone-600">
                  {t("settings.website_template_desc")}
                </p>
              </button>
            </div>

            {websiteMode === "external" && (
              <div data-testid="website-external-pane" className="mt-5 space-y-3 bg-stone-50 border border-stone-200 rounded-lg p-5">
                <FieldRow label={t("settings.website_external_url_label")}>
                  <input
                    data-testid="website-external-url"
                    type="url"
                    value={form.website?.external_url || ""}
                    onChange={(e) => update("website", "external_url", e.target.value)}
                    placeholder="https://www.tuoagenzia.it"
                    className="form-input"
                  />
                </FieldRow>
                <p className="text-xs text-stone-600">
                  {t("settings.website_external_feed_hint")}
                </p>
              </div>
            )}

            {websiteMode === "omnia_template" && (
              <div data-testid="website-template-pane" className="mt-5 space-y-3 bg-stone-50 border border-stone-200 rounded-lg p-5">
                <p className="text-sm text-stone-700">
                  {t("settings.website_template_pane_text")}
                </p>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-3">
                  {["minimal", "elegant", "bold"].map((tpl) => (
                    <div
                      key={tpl}
                      className="aspect-[4/3] border border-stone-300 rounded-md bg-white flex items-center justify-center text-xs uppercase tracking-widest text-stone-400"
                    >
                      {tpl}
                      <span className="ml-2 text-[9px] text-amber-700">{t("settings.website_template_soon")}</span>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-stone-500 mt-2">
                  {t("settings.website_template_soon_full")}
                </p>
              </div>
            )}
          </Section>

          {error && (
            <p data-testid="settings-error" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">
              {error}
            </p>
          )}

          {toast && (
            <p data-testid="settings-toast" className="text-sm text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-md px-3 py-2">
              ✓ {toast}
            </p>
          )}

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={saving}
              data-testid="settings-save-btn"
              className="px-6 py-3 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest font-medium rounded-md hover:bg-stone-700 disabled:opacity-50 transition"
            >
              {saving ? t("common.loading") : t("settings.save")}
            </button>
          </div>
        </form>
      </section>

      <style>{`
        .form-input {
          width: 100%;
          padding: 0.625rem 0.75rem;
          background: white;
          border: 1px solid #d6d3d1;
          border-radius: 6px;
          font-size: 0.875rem;
          color: #1c1917;
        }
        .form-input:focus {
          outline: none;
          border-color: #1c1917;
          box-shadow: 0 0 0 3px rgba(28,25,23,0.06);
        }
      `}</style>
    </AgencyShell>
  );
}

function Section({ label, children }) {
  return (
    <fieldset className="space-y-4">
      <legend className="text-xs uppercase tracking-widest text-stone-500 mb-2">{label}</legend>
      {children}
    </fieldset>
  );
}

function FieldRow({ label, children }) {
  return (
    <div>
      <label className="block text-xs uppercase tracking-widest text-stone-600 mb-1.5">{label}</label>
      {children}
    </div>
  );
}

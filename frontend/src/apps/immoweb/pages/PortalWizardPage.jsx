import React, { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import AgencyShell from "../components/AgencyShell";
import Brand from "../../../shared/components/Brand";

/**
 * M2.6d — Universal Portal Wizard.
 *
 * Self-service configurazione di un portale "custom" (regionale, di franchising,
 * di nicchia) non presente nel catalogo OMNIA. 4 step, feed_pull mode only:
 *  1. Identità (nome + slug + sito + categoria)
 *  2. Formato (dialect + integration mode)
 *  3. Endpoint (URL dove il portale scarica il feed — informativo per il pilot)
 *  4. Conferma + copia feed URL + salva
 *
 * Il salvataggio crea sia il PortalCatalog entry (tenant-owned) sia la
 * connection attiva. Poi si torna a /it/app/publishing.
 */
const STEPS = ["identita", "formato", "endpoint", "conferma"];

const DIALECTS = [
  { code: "osf_federata", label_key: "portal_wizard.dialect_osf_federata" },
  { code: "generic_rss", label_key: "portal_wizard.dialect_generic_rss" },
];

const CATEGORIES = ["gratuito", "freemium", "premium"];
const SCOPES = ["local", "regional", "national"];

export default function PortalWizardPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();

  const [step, setStep] = useState(0);
  const [form, setForm] = useState({
    name: "",
    slug: "",
    site_url: "",
    category: "freemium",
    geographic_scope: "regional",
    dialect: "osf_federata",
    integration_type: "feed_pull",
    endpoint_url: "",
    notes: "",
  });
  const [feedInfo, setFeedInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const autoSlug = useMemo(() => {
    return form.name
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 40);
  }, [form.name]);

  // Auto-fill slug from name unless user typed one manually
  useEffect(() => {
    if (form.slug === "" || form.slug === autoSlug) {
      setForm((f) => ({ ...f, slug: autoSlug }));
    }
  }, [autoSlug, form.slug]);

  // Preload feed info on step 4 (confirmation)
  useEffect(() => {
    if (step === 3 && !feedInfo) {
      api
        .get(`/app/publishing/custom-portals/feed-info?dialect=${form.dialect}`)
        .then((r) => setFeedInfo(r.data))
        .catch((e) => setError(e?.response?.data?.detail || "load_error"));
    }
  }, [step, form.dialect, feedInfo]);

  const canProceed = () => {
    if (step === 0) return form.name.trim().length >= 2 && form.slug.length >= 2;
    if (step === 1) return DIALECTS.some((d) => d.code === form.dialect);
    if (step === 2) return true;
    return true;
  };

  const goNext = () => {
    setError("");
    if (!canProceed()) return;
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  };
  const goBack = () => {
    setError("");
    setStep((s) => Math.max(s - 1, 0));
  };

  const submit = async () => {
    setLoading(true);
    setError("");
    try {
      await api.post("/app/publishing/custom-portals", {
        name: form.name.trim(),
        slug: form.slug,
        dialect: form.dialect,
        integration_type: form.integration_type,
        category: form.category,
        geographic_scope: form.geographic_scope,
        site_url: form.site_url.trim() || null,
        endpoint_url: form.endpoint_url.trim() || null,
        notes: form.notes.trim() || null,
      });
      nav(`/${lang}/app/publishing`, { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || "save_error");
    } finally {
      setLoading(false);
    }
  };

  const copyFeed = async () => {
    if (!feedInfo?.primary) return;
    try {
      await navigator.clipboard.writeText(feedInfo.primary);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore
    }
  };

  return (
    <AgencyShell current="publishing">
      <section
        data-testid="portal-wizard-page"
        className="max-w-3xl mx-auto space-y-8"
      >
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-2">
            <Brand>ImmoWeb · Publishing · Wizard</Brand>
          </p>
          <h1
            className="text-3xl md:text-4xl tracking-tight"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            data-testid="wizard-title"
          >
            {t("portal_wizard.title")}
          </h1>
          <p className="text-sm text-stone-600 mt-2 max-w-2xl">
            {t("portal_wizard.subtitle")}
          </p>
        </div>

        {/* Stepper */}
        <div
          className="flex items-center gap-2"
          data-testid="wizard-stepper"
        >
          {STEPS.map((s, idx) => (
            <div key={s} className="flex-1 flex items-center gap-2">
              <div
                data-testid={`wizard-step-${idx}`}
                className={`w-7 h-7 flex items-center justify-center rounded-full text-xs font-semibold transition ${
                  idx <= step
                    ? "bg-[#0B1E3F] text-white"
                    : "bg-stone-200 text-stone-500"
                }`}
              >
                {idx + 1}
              </div>
              <span
                className={`text-[10px] uppercase tracking-widest ${
                  idx === step ? "text-[#0B1E3F] font-semibold" : "text-stone-400"
                }`}
              >
                {t(`portal_wizard.step_${s}`)}
              </span>
              {idx < STEPS.length - 1 && (
                <div
                  className={`flex-1 h-px ${
                    idx < step ? "bg-[#0B1E3F]" : "bg-stone-200"
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {error && (
          <div
            data-testid="wizard-error"
            className="text-sm text-red-700 bg-red-50 border border-red-300 rounded p-3"
          >
            {error}
          </div>
        )}

        {/* Step content */}
        <div className="bg-white border border-stone-200 p-6 md:p-8 space-y-5">
          {step === 0 && (
            <div data-testid="wizard-step-0-content" className="space-y-5">
              <FieldLabel required>{t("portal_wizard.field_name")}</FieldLabel>
              <input
                data-testid="wizard-name"
                value={form.name}
                onChange={set("name")}
                placeholder={t("portal_wizard.name_placeholder")}
                className={inputClass}
              />
              <p className="text-xs text-stone-500 -mt-2">
                {t("portal_wizard.name_help")}
              </p>

              <FieldLabel required>{t("portal_wizard.field_slug")}</FieldLabel>
              <input
                data-testid="wizard-slug"
                value={form.slug}
                onChange={set("slug")}
                placeholder="es. immo-veneto"
                className={inputClass}
              />
              <p className="text-xs text-stone-500 -mt-2">
                {t("portal_wizard.slug_help")}
              </p>

              <FieldLabel>{t("portal_wizard.field_site_url")}</FieldLabel>
              <input
                data-testid="wizard-site-url"
                type="url"
                value={form.site_url}
                onChange={set("site_url")}
                placeholder="https://portale.esempio.it"
                className={inputClass}
              />

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <FieldLabel>{t("portal_wizard.field_category")}</FieldLabel>
                  <select
                    data-testid="wizard-category"
                    value={form.category}
                    onChange={set("category")}
                    className={inputClass}
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c} value={c}>
                        {t(`portal_wizard.category_${c}`)}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <FieldLabel>{t("portal_wizard.field_scope")}</FieldLabel>
                  <select
                    data-testid="wizard-scope"
                    value={form.geographic_scope}
                    onChange={set("geographic_scope")}
                    className={inputClass}
                  >
                    {SCOPES.map((s) => (
                      <option key={s} value={s}>
                        {t(`portal_wizard.scope_${s}`)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {step === 1 && (
            <div data-testid="wizard-step-1-content" className="space-y-5">
              <FieldLabel required>{t("portal_wizard.field_dialect")}</FieldLabel>
              <div className="grid gap-3">
                {DIALECTS.map((d) => (
                  <label
                    key={d.code}
                    data-testid={`wizard-dialect-${d.code}`}
                    className={`block border p-4 cursor-pointer transition ${
                      form.dialect === d.code
                        ? "border-[#0B1E3F] bg-stone-50"
                        : "border-stone-200 hover:border-stone-400"
                    }`}
                  >
                    <input
                      type="radio"
                      name="dialect"
                      value={d.code}
                      checked={form.dialect === d.code}
                      onChange={set("dialect")}
                      className="mr-3"
                    />
                    <span className="font-medium">
                      {t(`${d.label_key}_title`)}
                    </span>
                    <p className="text-xs text-stone-500 ml-6 mt-1">
                      {t(`${d.label_key}_desc`)}
                    </p>
                  </label>
                ))}
              </div>

              <div
                className="border border-amber-200 bg-amber-50 text-xs text-amber-900 p-3"
                data-testid="wizard-integration-notice"
              >
                {t("portal_wizard.integration_note")}
              </div>
            </div>
          )}

          {step === 2 && (
            <div data-testid="wizard-step-2-content" className="space-y-5">
              <FieldLabel>{t("portal_wizard.field_endpoint_url")}</FieldLabel>
              <input
                data-testid="wizard-endpoint-url"
                type="url"
                value={form.endpoint_url}
                onChange={set("endpoint_url")}
                placeholder="https://portale.esempio.it/import"
                className={inputClass}
              />
              <p className="text-xs text-stone-500 -mt-2">
                {t("portal_wizard.endpoint_help")}
              </p>

              <FieldLabel>{t("portal_wizard.field_notes")}</FieldLabel>
              <textarea
                data-testid="wizard-notes"
                value={form.notes}
                onChange={set("notes")}
                rows={3}
                placeholder={t("portal_wizard.notes_placeholder")}
                className={inputClass}
              />
            </div>
          )}

          {step === 3 && (
            <div data-testid="wizard-step-3-content" className="space-y-6">
              <div
                className="border border-emerald-800/30 bg-emerald-50/60 p-5"
                style={{ borderLeftWidth: "3px", borderLeftColor: "#1F6B5C" }}
              >
                <p className="text-sm font-medium mb-1 text-[#0B1E3F]">
                  🎯 {t("portal_wizard.review_title")}
                </p>
                <ul className="text-xs text-stone-700 space-y-1 mt-2">
                  <li>
                    <strong>{t("portal_wizard.field_name")}:</strong> {form.name}
                  </li>
                  <li>
                    <strong>{t("portal_wizard.field_slug")}:</strong> {form.slug}
                  </li>
                  <li>
                    <strong>{t("portal_wizard.field_dialect")}:</strong>{" "}
                    {form.dialect}
                  </li>
                  {form.site_url && (
                    <li>
                      <strong>{t("portal_wizard.field_site_url")}:</strong>{" "}
                      {form.site_url}
                    </li>
                  )}
                  {form.endpoint_url && (
                    <li>
                      <strong>{t("portal_wizard.field_endpoint_url")}:</strong>{" "}
                      {form.endpoint_url}
                    </li>
                  )}
                </ul>
              </div>

              {feedInfo && (
                <div className="space-y-3">
                  <p className="text-sm font-medium text-[#0B1E3F]">
                    📡 {t("portal_wizard.feed_ready_title")}
                  </p>
                  <p className="text-xs text-stone-600">
                    {t("portal_wizard.feed_ready_help")}
                  </p>
                  <div className="flex gap-2">
                    <code
                      data-testid="wizard-feed-url"
                      className="flex-1 bg-stone-100 border border-stone-200 px-3 py-2 text-xs font-mono text-stone-800 break-all"
                    >
                      {feedInfo.primary}
                    </code>
                    <button
                      data-testid="wizard-feed-copy"
                      onClick={copyFeed}
                      className="px-4 text-xs uppercase tracking-widest bg-stone-900 text-white hover:bg-stone-700"
                    >
                      {copied ? "✓ " + t("portal_wizard.copied") : t("portal_wizard.copy")}
                    </button>
                  </div>
                </div>
              )}

              <p className="text-xs text-stone-500">
                {t("portal_wizard.confirm_hint")}
              </p>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="flex justify-between items-center">
          <button
            data-testid="wizard-back"
            onClick={goBack}
            disabled={step === 0 || loading}
            className="px-6 py-3 text-xs uppercase tracking-widest text-stone-600 hover:text-stone-900 disabled:opacity-30"
          >
            ← {t("common.back")}
          </button>
          <button
            data-testid="wizard-cancel"
            onClick={() => nav(`/${lang}/app/publishing`)}
            className="px-6 py-3 text-xs uppercase tracking-widest text-stone-500 hover:text-stone-800"
          >
            {t("common.cancel")}
          </button>
          {step < STEPS.length - 1 ? (
            <button
              data-testid="wizard-next"
              onClick={goNext}
              disabled={!canProceed()}
              className="px-6 py-3 text-xs uppercase tracking-widest bg-stone-900 text-white hover:bg-stone-700 disabled:opacity-30"
            >
              {t("common.next")} →
            </button>
          ) : (
            <button
              data-testid="wizard-submit"
              onClick={submit}
              disabled={loading}
              className="px-6 py-3 text-xs uppercase tracking-widest bg-[#1F6B5C] text-white hover:bg-[#0B1E3F] disabled:opacity-40"
            >
              {loading ? t("common.saving") : t("portal_wizard.finish_cta")}
            </button>
          )}
        </div>
      </section>
    </AgencyShell>
  );
}

const inputClass =
  "w-full px-4 py-3 border border-stone-300 bg-white font-sans text-base focus:outline-none focus:border-stone-900";

function FieldLabel({ children, required }) {
  return (
    <label className="block text-xs uppercase tracking-widest text-stone-500 mb-2">
      {children}
      {required && <span className="text-red-600 ml-1">*</span>}
    </label>
  );
}

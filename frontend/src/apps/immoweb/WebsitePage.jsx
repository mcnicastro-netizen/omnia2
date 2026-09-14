import React, { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import AgencyShell from "./components/AgencyShell";
import { api } from "../../shared/lib/api";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * M2.S5 Layer D - Website / Brand Studio.
 *
 * Three sections:
 *   1. Brand Extractor (POST /app/website/extract-from-url) - Phase 1
 *   2. Theme Picker (GET /themes, POST /theme/apply, POST /theme/auto-configure) - Phase 2
 *   3. Live preview iframe of /api/p/{slug}/ or /app/website/preview/{theme_id}
 */
export default function WebsitePage() {
  const { t } = useTranslation();
  const [themes, setThemes] = useState([]);
  const [current, setCurrent] = useState(null); // GET /theme response
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  // Brand extractor state
  const [extractUrl, setExtractUrl] = useState("");
  const [extracting, setExtracting] = useState(false);
  const [extractResult, setExtractResult] = useState(null);

  // Picker state
  const [selectedTheme, setSelectedTheme] = useState(null);
  const [applying, setApplying] = useState(false);

  const iframeRef = useRef(null);

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(""), 4500); };

  const loadAll = async () => {
    setLoading(true);
    try {
      const [r1, r2] = await Promise.all([
        api.get("/app/website/themes"),
        api.get("/app/website/theme"),
      ]);
      setThemes(r1.data.themes || []);
      setCurrent(r2.data);
      setSelectedTheme(r2.data?.resolved?.theme_id || r1.data.default_theme_id || "minimal");
    } catch (e) {
      setError(String(e?.response?.data?.detail || e.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAll(); }, []);

  const refreshIframe = () => {
    if (iframeRef.current) {
      // bust cache so preview reloads
      const src = iframeRef.current.src.split("?")[0];
      iframeRef.current.src = `${src}?t=${Date.now()}`;
    }
  };

  const extractBrand = async (e) => {
    e?.preventDefault?.();
    if (!extractUrl) return;
    setExtracting(true); setError(""); setExtractResult(null);
    try {
      const { data } = await api.post("/app/website/extract-from-url", { url: extractUrl });
      setExtractResult(data);
      // refresh `current` so extracted_profile is up-to-date
      const r2 = await api.get("/app/website/theme");
      setCurrent(r2.data);
      showToast(t("website.extract_success"));
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message));
    } finally {
      setExtracting(false);
    }
  };

  const autoConfigure = async () => {
    setApplying(true); setError("");
    try {
      const { data } = await api.post("/app/website/theme/auto-configure");
      setSelectedTheme(data.theme_id);
      const r2 = await api.get("/app/website/theme");
      setCurrent(r2.data);
      showToast(t("website.auto_success", { theme: data.theme_id }));
      refreshIframe();
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message));
    } finally {
      setApplying(false);
    }
  };

  const applyTheme = async (themeId) => {
    setApplying(true); setError("");
    try {
      // preserve any extracted palette/logo from current extracted_profile
      const bp = current?.extracted_profile?.brand_profile || {};
      const palette = bp.palette || {};
      const logo = current?.extracted_profile?.logo_hint?.url;
      const tagline = bp.voice?.tagline_guess;
      await api.post("/app/website/theme/apply", {
        theme_id: themeId,
        palette: {
          primary: palette.primary || undefined,
          accent: palette.accent || undefined,
          neutral_dark: palette.neutral_dark || undefined,
          neutral_light: palette.neutral_light || undefined,
        },
        logo_url: logo || undefined,
        tagline: tagline || undefined,
      });
      setSelectedTheme(themeId);
      const r2 = await api.get("/app/website/theme");
      setCurrent(r2.data);
      showToast(t("website.apply_success", { theme: themeId }));
      refreshIframe();
    } catch (err) {
      setError(String(err?.response?.data?.detail || err.message));
    } finally {
      setApplying(false);
    }
  };

  if (loading) {
    return (
      <AgencyShell current="website">
        <p className="text-sm text-stone-500" data-testid="website-loading">{t("common.loading")}</p>
      </AgencyShell>
    );
  }

  const extracted = current?.extracted_profile;
  const resolved = current?.resolved;
  const publicUrl = current?.public_url
    ? `${BACKEND_URL}${current.public_url}`
    : null;
  const previewSrc = publicUrl
    ? `${publicUrl}?t=${Date.now()}`
    : "about:blank";

  return (
    <AgencyShell current="website">
      <section data-testid="website-page" className="max-w-6xl space-y-10">
        <div>
          <h1 className="text-3xl md:text-4xl tracking-tight" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            {t("website.title")}
          </h1>
          <p className="text-stone-600 mt-1">{t("website.subtitle")}</p>
        </div>

        {error && (
          <p data-testid="website-error" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">
            {error}
          </p>
        )}
        {toast && (
          <p data-testid="website-toast" className="text-sm text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-md px-3 py-2">
            ✓ {toast}
          </p>
        )}

        {/* ============ 1. BRAND EXTRACTOR ============ */}
        <section className="space-y-4">
          <div>
            <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-2">
              {t("website.section_extractor")}
            </h2>
            <p className="text-sm text-stone-600">
              {t("website.extractor_intro")}
            </p>
          </div>
          <form onSubmit={extractBrand} className="flex flex-col md:flex-row gap-3">
            <input
              data-testid="website-extract-url"
              type="url"
              value={extractUrl}
              onChange={(e) => setExtractUrl(e.target.value)}
              placeholder="https://www.tuoagenzia.it"
              className="flex-1 px-3 py-2.5 bg-white border border-stone-300 rounded-md text-sm focus:outline-none focus:border-stone-900 focus:ring-2 focus:ring-stone-900/10"
            />
            <button
              type="submit"
              disabled={extracting || !extractUrl}
              data-testid="website-extract-btn"
              className="px-5 py-2.5 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest font-medium rounded-md hover:bg-stone-700 disabled:opacity-50 transition"
            >
              {extracting ? t("website.extracting") : t("website.extract_btn")}
            </button>
          </form>

          {(extractResult || extracted) && (
            <div data-testid="website-extracted-summary" className="bg-stone-50 border border-stone-200 rounded-lg p-5">
              <ExtractedSummary
                data={extractResult || extracted}
                onAutoConfigure={autoConfigure}
                autoBtnDisabled={applying}
                t={t}
              />
            </div>
          )}
        </section>

        {/* ============ 2. THEME PICKER ============ */}
        <section className="space-y-4">
          <div>
            <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-2">
              {t("website.section_theme")}
            </h2>
            <p className="text-sm text-stone-600">
              {t("website.theme_intro")}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {themes.map((th) => {
              const isActive = selectedTheme === th.id;
              return (
                <button
                  key={th.id}
                  type="button"
                  data-testid={`theme-card-${th.id}`}
                  onClick={() => applyTheme(th.id)}
                  disabled={applying}
                  className={`text-left p-5 border rounded-lg transition disabled:opacity-60 ${
                    isActive
                      ? "border-emerald-700 bg-emerald-50/60 ring-2 ring-emerald-100"
                      : "border-stone-300 bg-white hover:border-stone-500"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <p className="font-semibold text-stone-900">{th.name}</p>
                    {isActive && (
                      <span className="text-[10px] uppercase tracking-widest text-emerald-700">
                        ✓ {t("website.active")}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mb-3">
                    {Object.values(th.preview_palette || {}).map((c, i) => (
                      <span key={i}
                        className="inline-block w-6 h-6 rounded-full border border-stone-200"
                        style={{ background: c }} />
                    ))}
                  </div>
                  <p className="text-sm text-stone-600">{th.description}</p>
                </button>
              );
            })}
          </div>
        </section>

        {/* ============ 3. LIVE PREVIEW ============ */}
        <section className="space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-2">
                {t("website.section_preview")}
              </h2>
              <p className="text-sm text-stone-600">
                {t("website.preview_intro")}
              </p>
            </div>
            <div className="flex gap-2 items-center">
              <button
                type="button"
                onClick={refreshIframe}
                data-testid="website-refresh-preview"
                className="px-3 py-2 text-xs uppercase tracking-widest text-stone-700 border border-stone-300 rounded-md hover:bg-stone-100 transition"
              >
                ↻ {t("website.refresh")}
              </button>
              {publicUrl && (
                <a
                  href={publicUrl}
                  target="_blank"
                  rel="noreferrer"
                  data-testid="website-open-public"
                  className="px-3 py-2 text-xs uppercase tracking-widest text-stone-700 border border-stone-300 rounded-md hover:bg-stone-100 transition"
                >
                  {t("website.open_public")} ↗
                </a>
              )}
            </div>
          </div>

          <div className="border border-stone-300 rounded-md overflow-hidden bg-stone-50"
               style={{ height: "640px" }}>
            <iframe
              ref={iframeRef}
              data-testid="website-preview-iframe"
              src={previewSrc}
              title="Site preview"
              className="w-full h-full bg-white"
              sandbox="allow-same-origin allow-scripts"
            />
          </div>

          {resolved && (
            <details className="text-xs text-stone-500" data-testid="website-resolved-debug">
              <summary className="cursor-pointer hover:text-stone-700">
                {t("website.show_resolved")}
              </summary>
              <pre className="mt-2 p-3 bg-stone-100 rounded text-stone-700 overflow-x-auto">
{JSON.stringify(resolved, null, 2)}
              </pre>
            </details>
          )}
        </section>

        {/* ============ 4. CUSTOM DOMAIN (M2.S6) ============ */}
        <CustomDomainSection t={t} />
      </section>
    </AgencyShell>
  );
}

function CustomDomainSection({ t }) {
  const [state, setState] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [domain, setDomain] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState("");

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/app/website/domain");
      setState(data);
    } catch (e) {
      setErr(String(e?.response?.data?.detail || e.message));
    } finally { setLoading(false); }
  }, []);
  React.useEffect(() => { load(); }, [load]);

  const submit = async (e) => {
    e?.preventDefault?.();
    if (!domain) return;
    setBusy(true); setErr("");
    try {
      const { data } = await api.post("/app/website/domain/request", { domain });
      setState(data); setDomain("");
    } catch (e) {
      setErr(String(e?.response?.data?.detail || e.message));
    } finally { setBusy(false); }
  };

  const verify = async () => {
    setBusy(true); setErr("");
    try {
      const { data } = await api.post("/app/website/domain/verify");
      setState({ ...state, status: data.status, last_error: data.last_error,
                 verified_at: data.verified_at });
    } catch (e) {
      setErr(String(e?.response?.data?.detail || e.message));
    } finally { setBusy(false); }
  };

  const remove = async () => {
    if (!window.confirm(t("website.cd_confirm_delete"))) return;
    setBusy(true); setErr("");
    try {
      await api.delete("/app/website/domain");
      await load();
    } catch (e) {
      setErr(String(e?.response?.data?.detail || e.message));
    } finally { setBusy(false); }
  };

  const copy = (txt) => navigator.clipboard?.writeText(txt);

  if (loading) return <p className="text-sm text-stone-500">{t("common.loading")}</p>;

  const hasDomain = !!state?.domain;
  const status = state?.status;
  const dns = state?.dns_instructions;

  return (
    <section className="space-y-4" data-testid="custom-domain-section">
      <div>
        <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-2">
          {t("website.section_cd")}
        </h2>
        <p className="text-sm text-stone-600">{t("website.cd_intro")}</p>
      </div>

      {err && <p data-testid="cd-error" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">{err}</p>}

      {!hasDomain && (
        <form onSubmit={submit} className="flex gap-3 flex-wrap">
          <input
            data-testid="cd-domain-input" value={domain}
            onChange={(e) => setDomain(e.target.value)}
            placeholder="www.tuaagenzia.it"
            className="flex-1 min-w-[220px] px-3 py-2.5 bg-white border border-stone-300 rounded-md text-sm focus:outline-none focus:border-stone-900"
          />
          <button
            type="submit" disabled={busy || !domain}
            data-testid="cd-request-btn"
            className="px-5 py-2.5 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest font-medium rounded-md hover:bg-stone-700 disabled:opacity-50"
          >
            {t("website.cd_request_btn")}
          </button>
        </form>
      )}

      {hasDomain && (
        <div className="bg-white border border-stone-200 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div>
              <div className="font-medium text-stone-900 text-base">{state.domain}</div>
              <div className="text-xs text-stone-500 mt-0.5">
                {t("website.cd_requested_at", { d: (state.requested_at || "").slice(0, 16).replace("T", " ") })}
              </div>
            </div>
            <StatusBadge status={status} t={t} />
          </div>

          {status === "error" && state.last_error && (
            <p className="text-xs text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">
              {state.last_error}
            </p>
          )}

          {dns && (
            <div className="bg-stone-50 border border-stone-200 rounded-md p-4 space-y-3">
              <p className="text-xs uppercase tracking-widest text-stone-500">{t("website.cd_dns_instructions")}</p>
              <DNSRow label="TXT" host={dns.txt_record.host} value={dns.txt_record.value} onCopy={copy} />
              <DNSRow label="CNAME" host={dns.cname_record.host} value={dns.cname_record.value} onCopy={copy} />
              <p className="text-xs text-stone-500 italic">{dns.apex_alternative}</p>
            </div>
          )}

          <div className="flex gap-2 flex-wrap">
            <button
              type="button" onClick={verify} disabled={busy}
              data-testid="cd-verify-btn"
              className="px-4 py-2 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest rounded-md hover:bg-stone-700 disabled:opacity-50"
            >
              {busy ? t("website.cd_verifying") : t("website.cd_verify_btn")}
            </button>
            <button
              type="button" onClick={remove} disabled={busy}
              data-testid="cd-delete-btn"
              className="px-4 py-2 bg-white border border-red-200 text-red-700 text-xs uppercase tracking-widest rounded-md hover:bg-red-50 disabled:opacity-50"
            >
              {t("website.cd_delete_btn")}
            </button>
          </div>

          {status === "verified" && (
            <p className="text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 rounded px-3 py-2">
              ✓ {t("website.cd_admin_will_activate_ssl")}
            </p>
          )}
        </div>
      )}
    </section>
  );
}

function StatusBadge({ status, t }) {
  const map = {
    pending: { txt: t("website.cd_status_pending"), cls: "text-amber-800 bg-amber-50 border-amber-200" },
    verified: { txt: t("website.cd_status_verified"), cls: "text-emerald-800 bg-emerald-50 border-emerald-200" },
    error: { txt: t("website.cd_status_error"), cls: "text-red-700 bg-red-50 border-red-200" },
  };
  const m = map[status] || { txt: "—", cls: "text-stone-600 bg-stone-100 border-stone-200" };
  return (
    <span data-testid={`cd-status-${status}`}
          className={`text-[10px] uppercase tracking-widest px-2.5 py-1 rounded-md border ${m.cls}`}>
      {m.txt}
    </span>
  );
}

function DNSRow({ label, host, value, onCopy }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-[60px_1fr_auto] gap-2 items-start">
      <span className="text-[10px] uppercase tracking-widest text-stone-500 mt-1">{label}</span>
      <div className="font-mono text-xs space-y-1">
        <div className="text-stone-500">Host: <span className="text-stone-900">{host}</span></div>
        <div className="text-stone-500">Valore: <span className="text-stone-900 break-all">{value}</span></div>
      </div>
      <button type="button" onClick={() => onCopy(value)}
              className="text-[10px] uppercase tracking-widest text-stone-600 border border-stone-300 rounded px-2 py-1 hover:bg-stone-100">
        Copia
      </button>
    </div>
  );
}


function ExtractedSummary({ data, onAutoConfigure, autoBtnDisabled, t }) {
  const bp = data?.brand_profile || data?.extracted_profile?.brand_profile || {};
  const logoHint = data?.summary?.logo_found ? "✓" : (data?.logo_hint?.url ? "✓" : "—");
  const palette = bp.palette || {};
  const voice = bp.voice || {};
  const structure = bp.structure || {};
  const confidence = bp.confidence ?? 0;
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <span className="text-xs uppercase tracking-widest text-stone-500">
          {t("website.extracted_confidence")}:
        </span>
        <span className={`text-sm font-semibold ${confidence >= 70 ? "text-emerald-700" : confidence >= 40 ? "text-amber-700" : "text-red-700"}`}>
          {confidence}/100
        </span>
        <span className="text-xs text-stone-400">·</span>
        <span className="text-xs text-stone-500">{t("website.extracted_logo")}: {logoHint}</span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {["primary", "accent", "neutral_dark", "neutral_light"].map((k) => (
          <div key={k} className="bg-white rounded-md p-3 border border-stone-200">
            <div className="text-[10px] uppercase tracking-widest text-stone-500 mb-2">{k}</div>
            <div className="flex items-center gap-2">
              <span className="inline-block w-7 h-7 rounded border border-stone-300"
                    style={{ background: palette[k] || "transparent" }} />
              <span className="text-xs font-mono text-stone-700">{palette[k] || "—"}</span>
            </div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
        <Pill label={t("website.field_tone")} value={voice.tone} />
        <Pill label={t("website.field_header")} value={structure.header_style} />
        <Pill label={t("website.field_card")} value={structure.card_style} />
      </div>
      <button
        type="button"
        onClick={onAutoConfigure}
        disabled={autoBtnDisabled}
        data-testid="website-auto-configure-btn"
        className="px-5 py-2.5 bg-emerald-700 text-white text-xs uppercase tracking-widest font-medium rounded-md hover:bg-emerald-800 disabled:opacity-50 transition"
      >
        ⚡ {t("website.auto_configure_btn")}
      </button>
    </div>
  );
}

function Pill({ label, value }) {
  return (
    <div className="bg-white border border-stone-200 rounded px-3 py-2">
      <div className="text-[10px] uppercase tracking-widest text-stone-500 mb-0.5">{label}</div>
      <div className="text-stone-800">{value || "—"}</div>
    </div>
  );
}

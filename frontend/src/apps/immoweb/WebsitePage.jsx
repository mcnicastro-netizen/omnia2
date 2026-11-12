import React, { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import AgencyShell from "./components/AgencyShell";
import MlsEmbedKit from "./components/MlsEmbedKit";
import { api } from "../../shared/lib/api";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

/**
 * Il mio sito
 * A) Ho già un sito → solo URL
 * B) Restyling / sito OMNIA → subito i template → scelgo → modifico logo/slogan → anteprima
 * Extract/palette: VIA
 */
export default function WebsitePage() {
  const { t } = useTranslation();
  const { lang } = useParams();
  const l = (lang || "it").slice(0, 2);
  const [searchParams, setSearchParams] = useSearchParams();

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  const [current, setCurrent] = useState(null);
  const [agency, setAgency] = useState(null);
  const [themes, setThemes] = useState([]);
  const [siteUrl, setSiteUrl] = useState("");
  const [path, setPath] = useState(null); // external | omnia | null
  const [selectedTheme, setSelectedTheme] = useState("classic");
  const [previewHtml, setPreviewHtml] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewMls, setPreviewMls] = useState(false); // anteprima con/senza box rete

  const [editName, setEditName] = useState("");
  const [editTagline, setEditTagline] = useState("");
  const [editLogo, setEditLogo] = useState("");
  const [agencyMls, setAgencyMls] = useState(false);
  const [embedKit, setEmbedKit] = useState(null);

  const templatesRef = useRef(null);

  const flash = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(""), 4000);
  };

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [th, cur, me] = await Promise.all([
        api.get("/app/website/themes"),
        api.get("/app/website/theme"),
        api.get("/app/agencies/me").catch(() => ({ data: null })),
      ]);
      setThemes(th.data.themes || []);
      setCurrent(cur.data);
      setAgency(me.data);
      const mlsLive = !!me.data?.mls_enabled;
      setAgencyMls(mlsLive);
      setPreviewMls(mlsLive);
      const slug = me.data?.slug;
      if (mlsLive && slug) {
        try {
          const kit = await api.get(`/mls-box/embed-kit/${slug}`);
          setEmbedKit(kit.data);
        } catch {
          setEmbedKit(null);
        }
      } else {
        setEmbedKit(null);
      }
      const url =
        cur.data?.declared_url ||
        cur.data?.external_url ||
        (cur.data?.existing_domain ? `https://${cur.data.existing_domain}` : "") ||
        "";
      setSiteUrl(url);
      const mode = cur.data?.website_mode;
      if (mode === "external") setPath("external");
      else if (mode === "omnia_template") setPath("omnia");
      else setPath(null);
      const tid = cur.data?.resolved?.theme_id || th.data.default_theme_id || "classic";
      setSelectedTheme(tid);
      setEditName(me.data?.display_name || me.data?.name || "");
      setEditTagline(
        me.data?.branding?.tagline ||
          cur.data?.resolved?.tagline ||
          cur.data?.saved_theme_config?.tagline ||
          ""
      );
      setEditLogo(
        me.data?.branding?.logo_url ||
          cur.data?.resolved?.logo_url ||
          cur.data?.saved_theme_config?.logo_url ||
          ""
      );
    } catch (e) {
      const d = e?.response?.data?.detail;
      setError(typeof d === "string" ? d : d?.hint || e.message || "Errore di caricamento");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Deep-link restyle=1 → apri subito i template
  useEffect(() => {
    if (loading) return;
    if (searchParams.get("restyle") === "1" || searchParams.get("omnia") === "1") {
      openRestyle();
      const next = new URLSearchParams(searchParams);
      next.delete("restyle");
      next.delete("omnia");
      setSearchParams(next, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading]);

  const publicBase = current?.public_url ? `${BACKEND_URL}${current.public_url}` : null;

  const loadPreview = useCallback(async () => {
    if (path !== "omnia" || !selectedTheme) {
      setPreviewHtml("");
      return;
    }
    setPreviewLoading(true);
    try {
      // Stesso template, con o senza box rete (non salva l’adesione MLS)
      const r = await api.get(`/app/website/preview/${selectedTheme}`, {
        params: { mls: previewMls ? "true" : "false", t: Date.now() },
        responseType: "text",
        transformResponse: [(d) => d],
      });
      setPreviewHtml(typeof r.data === "string" ? r.data : String(r.data || ""));
    } catch (e) {
      setPreviewHtml(
        `<!doctype html><html><body style="font-family:system-ui;padding:2rem;color:#444">`
          + `<p>Anteprima non disponibile.</p>`
          + (publicBase
            ? `<p><a href="${publicBase}" target="_blank" rel="noreferrer">Apri sito pubblico</a></p>`
            : "")
          + `</body></html>`
      );
    } finally {
      setPreviewLoading(false);
    }
  }, [path, selectedTheme, previewMls, publicBase]);

  useEffect(() => {
    if (loading || path !== "omnia") return;
    loadPreview();
  }, [loading, loadPreview, selectedTheme, previewMls, path]);

  const saveExternal = async () => {
    setBusy(true);
    setError("");
    try {
      await api.post("/app/website/presence", {
        mode: "external",
        external_url: siteUrl.trim(),
      });
      setPath("external");
      flash("Ok: il tuo sito resta com’è.");
      await load();
    } catch (e) {
      const d = e?.response?.data?.detail;
      setError(
        (typeof d === "object" && (d.hint || d.error)) ||
          (typeof d === "string" ? d : null) ||
          "Non sono riuscito a salvare l’indirizzo"
      );
    } finally {
      setBusy(false);
    }
  };

  const openRestyle = async () => {
    setPath("omnia");
    setError("");
    setTimeout(() => {
      templatesRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
    setBusy(true);
    try {
      await api.post("/app/website/presence", {
        mode: "omnia_template",
        external_url: siteUrl.trim() || undefined,
      });
      await load();
    } catch (e) {
      const d = e?.response?.data?.detail;
      setError(typeof d === "string" ? d : d?.hint || e.message || "Errore");
    } finally {
      setBusy(false);
    }
  };

  const applyTheme = async (themeId) => {
    setBusy(true);
    setError("");
    try {
      await api.post("/app/website/theme/apply", {
        theme_id: themeId,
        logo_url: editLogo || undefined,
        tagline: editTagline || undefined,
      });
      setSelectedTheme(themeId);
      flash(`Template «${themeId}» applicato. Ora puoi ritoccare logo e slogan.`);
      const r = await api.get("/app/website/theme");
      setCurrent(r.data);
    } catch (e) {
      const d = e?.response?.data?.detail;
      setError(typeof d === "string" ? d : e.message || "Errore tema");
    } finally {
      setBusy(false);
    }
  };

  const saveSiteTexts = async () => {
    setBusy(true);
    setError("");
    try {
      await api.patch("/app/agencies/me", {
        display_name: editName,
        branding: {
          ...(agency?.branding || {}),
          tagline: editTagline,
          logo_url: editLogo,
        },
      });
      await api.post("/app/website/theme/apply", {
        theme_id: selectedTheme,
        logo_url: editLogo || undefined,
        tagline: editTagline || undefined,
      });
      flash("Modifiche salvate. Guarda l’anteprima.");
      await load();
    } catch (e) {
      const d = e?.response?.data?.detail;
      setError(typeof d === "string" ? d : d?.hint || e.message || "Salvataggio non riuscito");
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <AgencyShell current="website">
        <p className="text-sm text-stone-500" data-testid="website-loading">
          {t("common.loading")}
        </p>
      </AgencyShell>
    );
  }

  const statusLine =
    path === "external"
      ? `Usi il tuo sito: ${current?.external_url || siteUrl || "—"}`
      : path === "omnia"
        ? `Sito OMNIA · template ${selectedTheme}`
        : "Scegli: tieni il sito che hai, oppure fai un restyling con un template OMNIA.";

  return (
    <AgencyShell current="website">
      <section data-testid="website-page" className="max-w-3xl space-y-8">
        <header>
          <h1
            className="text-3xl md:text-4xl tracking-tight text-stone-900"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            Il mio sito
          </h1>
          <p className="mt-2 text-sm font-sans text-stone-600">
            O tieni quello che hai già, o scegli un template OMNIA e lo personalizzi.
          </p>
          <p
            className="mt-3 text-sm font-sans text-stone-800 border border-stone-200 bg-stone-50 px-3 py-2"
            data-testid="website-status"
          >
            {statusLine}
          </p>
        </header>

        {error ? (
          <p data-testid="website-error" className="text-sm text-red-800 bg-red-50 border border-red-200 px-3 py-2">
            {error}
          </p>
        ) : null}
        {toast ? (
          <p data-testid="website-toast" className="text-sm text-emerald-900 bg-emerald-50 border border-emerald-200 px-3 py-2">
            {toast}
          </p>
        ) : null}

        <div className="grid sm:grid-cols-2 gap-4" data-testid="website-choice-grid">
          <div
            className={`border px-4 py-4 space-y-3 ${
              path === "external" ? "border-stone-900 bg-white" : "border-stone-200 bg-stone-50/80"
            }`}
          >
            <p className="text-base font-medium text-stone-900" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              Ho già un sito
            </p>
            <p className="text-sm text-stone-600 font-sans">
              Resta dove sta. Non lo sostituiamo. Salviamo solo l’indirizzo.
            </p>
            <label className="block text-xs uppercase tracking-widest text-stone-500 font-sans">
              Indirizzo
              <input
                data-testid="website-url-input"
                type="url"
                value={siteUrl}
                onChange={(e) => setSiteUrl(e.target.value)}
                placeholder="https://www.tuaagenzia.it"
                className="mt-1 w-full px-3 py-2.5 border border-stone-300 bg-white text-sm text-stone-900 normal-case tracking-normal"
              />
            </label>
            <button
              type="button"
              disabled={busy || !siteUrl.trim()}
              onClick={saveExternal}
              data-testid="website-save-external"
              className="w-full px-3 py-2.5 text-[11px] uppercase tracking-widest bg-stone-900 text-white disabled:opacity-40"
            >
              Salva: lascio il sito com’è
            </button>
          </div>

          <div
            className={`border px-4 py-4 space-y-3 ${
              path === "omnia" ? "border-stone-900 bg-white" : "border-stone-200 bg-stone-50/80"
            }`}
          >
            <p className="text-base font-medium text-stone-900" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              Restyling / sito OMNIA
            </p>
            <p className="text-sm text-stone-600 font-sans">
              Clicca e vedi i template. Ne scegli uno, poi ritocchi nome, slogan e logo.
              Gli annunci arrivano da Immobili.
            </p>
            <button
              type="button"
              disabled={busy}
              onClick={openRestyle}
              data-testid="website-choose-omnia"
              className="w-full px-3 py-2.5 text-[11px] uppercase tracking-widest border border-stone-900 text-stone-900 disabled:opacity-40"
            >
              Mostra i template →
            </button>
          </div>
        </div>

        {path === "omnia" ? (
          <div className="space-y-8" data-testid="website-omnia-panel">
            <section ref={templatesRef} className="space-y-4" data-testid="website-templates">
              <h2 className="text-xl text-stone-900" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                1. Scegli un template
              </h2>
              <p className="text-sm text-stone-600 font-sans">
                Sono modelli di sito pronti. Tocca l’immagine per applicarlo. Ogni
                template funziona con o senza box rete OMNIA — lo vedi in anteprima
                sotto, senza cambiare modello.
              </p>
              <div className="grid sm:grid-cols-2 gap-4">
                {themes.map((th) => {
                  const active = selectedTheme === th.id;
                  const img = th.hero_image || th.preview_image || null;
                  return (
                    <button
                      key={th.id}
                      type="button"
                      disabled={busy}
                      onClick={() => applyTheme(th.id)}
                      data-testid={`theme-card-${th.id}`}
                      className={`text-left overflow-hidden border bg-white transition disabled:opacity-50 ${
                        active
                          ? "border-stone-900 ring-2 ring-stone-900"
                          : "border-stone-200 hover:border-stone-500"
                      }`}
                    >
                      <div className="relative aspect-[16/10] bg-stone-200 overflow-hidden">
                        {img ? (
                          <img
                            src={img}
                            alt=""
                            className="absolute inset-0 w-full h-full object-cover"
                            loading="lazy"
                          />
                        ) : (
                          <div
                            className="absolute inset-0"
                            style={{
                              background: `linear-gradient(135deg, ${
                                (th.preview_palette || {}).primary || "#0B1E3F"
                              }, ${(th.preview_palette || {}).accent || "#78716c"})`,
                            }}
                          />
                        )}
                        {active ? (
                          <span className="absolute top-2 right-2 text-[10px] uppercase tracking-widest bg-white text-stone-900 px-2 py-1">
                            scelto
                          </span>
                        ) : null}
                      </div>
                      <div className="px-3 py-3">
                        <p className="font-medium text-stone-900 text-base">{th.name}</p>
                        <p className="mt-1 text-xs text-stone-500 font-sans">{th.description}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </section>

            <section className="space-y-4 border border-stone-200 px-4 py-4" data-testid="website-edit-panel">
              <h2 className="text-xl text-stone-900" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                2. Modifica cosa si vede
              </h2>
              <p className="text-sm text-stone-600 font-sans">
                Nome, slogan e logo sul sito. Per telefono e indirizzo usa Impostazioni.
                Per gli annunci usa Immobili.
              </p>
              <label className="block text-xs uppercase tracking-widest text-stone-500">
                Nome agenzia
                <input
                  data-testid="website-edit-name"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="mt-1 w-full px-3 py-2 border border-stone-300 text-sm normal-case tracking-normal"
                />
              </label>
              <label className="block text-xs uppercase tracking-widest text-stone-500">
                Slogan (sotto il nome, se il template lo mostra)
                <input
                  data-testid="website-edit-tagline"
                  value={editTagline}
                  onChange={(e) => setEditTagline(e.target.value)}
                  className="mt-1 w-full px-3 py-2 border border-stone-300 text-sm normal-case tracking-normal"
                  placeholder="Es. La casa giusta, senza stress"
                />
              </label>
              <label className="block text-xs uppercase tracking-widest text-stone-500">
                Indirizzo del logo (foto online)
                <input
                  data-testid="website-edit-logo"
                  value={editLogo}
                  onChange={(e) => setEditLogo(e.target.value)}
                  className="mt-1 w-full px-3 py-2 border border-stone-300 text-sm normal-case tracking-normal"
                  placeholder="https://…"
                />
              </label>
              {editLogo ? (
                <img src={editLogo} alt="Logo" className="h-12 object-contain" data-testid="website-logo-preview" />
              ) : null}
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={busy}
                  onClick={saveSiteTexts}
                  data-testid="website-save-edits"
                  className="px-4 py-2.5 text-[11px] uppercase tracking-widest bg-stone-900 text-white disabled:opacity-40"
                >
                  Salva modifiche
                </button>
                <Link
                  to={`/${l}/app/settings`}
                  className="px-4 py-2.5 text-[11px] uppercase tracking-widest border border-stone-300"
                >
                  Contatti / indirizzo
                </Link>
                <Link
                  to={`/${l}/app/properties`}
                  className="px-4 py-2.5 text-[11px] uppercase tracking-widest border border-stone-300"
                >
                  Immobili (annunci)
                </Link>
              </div>
            </section>

            <section className="space-y-3" data-testid="website-preview-section">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="text-xl text-stone-900" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                  3. Anteprima
                </h2>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => setPreviewMls(false)}
                    data-testid="website-preview-no-mls"
                    className={`px-3 py-1.5 text-[11px] uppercase tracking-widest border ${
                      !previewMls ? "border-stone-900 bg-white" : "border-stone-300"
                    }`}
                  >
                    Solo i tuoi immobili
                  </button>
                  <button
                    type="button"
                    onClick={() => setPreviewMls(true)}
                    data-testid="website-preview-with-mls"
                    className={`px-3 py-1.5 text-[11px] uppercase tracking-widest border ${
                      previewMls ? "border-stone-900 bg-white" : "border-stone-300"
                    }`}
                  >
                    Con box rete OMNIA
                  </button>
                  <button
                    type="button"
                    onClick={loadPreview}
                    data-testid="website-refresh-preview"
                    className="px-3 py-1.5 text-[11px] uppercase tracking-widest border border-stone-300"
                  >
                    Aggiorna
                  </button>
                  {publicBase ? (
                    <a
                      href={publicBase}
                      target="_blank"
                      rel="noreferrer"
                      data-testid="website-open-public"
                      className="px-3 py-1.5 text-[11px] uppercase tracking-widest border border-stone-300"
                    >
                      Sito live →
                    </a>
                  ) : null}
                </div>
              </div>
              <p className="text-sm text-stone-600 font-sans" data-testid="website-mls-preview-hint">
                Stesso template, due viste: con o senza ricerca sulla rete. L’adesione alla rete
                si attiva dal percorso MLS (oggi:{" "}
                <strong>{agencyMls ? "rete attiva sul sito live" : "rete non attiva sul sito live"}</strong>
                ). Qui cambi solo l’anteprima.
              </p>
              <div className="border border-stone-300 bg-stone-50 relative overflow-hidden" style={{ height: 520 }}>
                {previewLoading ? (
                  <p className="absolute top-0 inset-x-0 text-xs text-stone-500 bg-stone-100 px-3 py-1 z-10">
                    Carico…
                  </p>
                ) : null}
                <iframe
                  data-testid="website-preview-iframe"
                  title="Anteprima sito"
                  srcDoc={previewHtml || undefined}
                  className="w-full h-full bg-white"
                  sandbox="allow-same-origin allow-scripts"
                />
              </div>
            </section>

            <details className="border border-stone-200 px-3 py-3" data-testid="website-domain-details">
              <summary className="cursor-pointer text-sm font-medium text-stone-800">
                Voglio il mio indirizzo (www…) su questo sito OMNIA
              </summary>
              <div className="mt-3">
                <CustomDomainSection />
              </div>
            </details>
          </div>
        ) : null}

        {path === "external" && (current?.external_url || siteUrl) ? (
          <div className="space-y-4" data-testid="website-external-done">
            <p className="text-sm text-stone-600 font-sans">
              Indirizzo salvato:{" "}
              <a className="underline break-all" href={current?.external_url || siteUrl} target="_blank" rel="noreferrer">
                {current?.external_url || siteUrl}
              </a>
              . Il sito resta il tuo. Se un giorno vuoi il restyling, clicca «Mostra i template».
            </p>
            {agencyMls && embedKit ? (
              <MlsEmbedKit kit={embedKit} />
            ) : (
              <p className="text-sm text-stone-600 font-sans" data-testid="website-external-mls-hint">
                Quando aderisci alla rete MLS ti diamo un codice da incollare al posto del solo box
                ricerca rete. Il resto del sito non si tocca.
              </p>
            )}
          </div>
        ) : null}
      </section>
    </AgencyShell>
  );
}

function CustomDomainSection() {
  const [state, setState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [domain, setDomain] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/app/website/domain");
      setState(data);
    } catch (e) {
      setErr(String(e?.response?.data?.detail || e.message));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const submit = async (e) => {
    e?.preventDefault?.();
    if (!domain) return;
    setBusy(true);
    setErr("");
    try {
      const { data } = await api.post("/app/website/domain/request", { domain });
      setState(data);
      setDomain("");
    } catch (e2) {
      setErr(String(e2?.response?.data?.detail || e2.message));
    } finally {
      setBusy(false);
    }
  };

  const verify = async () => {
    setBusy(true);
    setErr("");
    try {
      const { data } = await api.post("/app/website/domain/verify");
      setState((s) => ({
        ...s,
        status: data.status,
        last_error: data.last_error,
        verified_at: data.verified_at,
      }));
    } catch (e2) {
      setErr(String(e2?.response?.data?.detail || e2.message));
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    if (!window.confirm("Rimuovere questo indirizzo personalizzato?")) return;
    setBusy(true);
    setErr("");
    try {
      await api.delete("/app/website/domain");
      await load();
    } catch (e2) {
      setErr(String(e2?.response?.data?.detail || e2.message));
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <p className="text-sm text-stone-500">Carico…</p>;

  const hasDomain = !!state?.domain;
  const dns = state?.dns_instructions;

  return (
    <div className="space-y-3 text-sm font-sans" data-testid="custom-domain-section">
      <p className="text-stone-600">
        Di solito lo fa chi gestisce il dominio: due record, poi Verifica.
      </p>
      {err ? (
        <p data-testid="cd-error" className="text-red-800 bg-red-50 border border-red-200 px-3 py-2">
          {err}
        </p>
      ) : null}
      {!hasDomain ? (
        <form onSubmit={submit} className="flex flex-wrap gap-2">
          <input
            data-testid="cd-domain-input"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            placeholder="www.tuaagenzia.it"
            className="flex-1 min-w-[200px] px-3 py-2 border border-stone-300"
          />
          <button
            type="submit"
            disabled={busy || !domain}
            data-testid="cd-request-btn"
            className="px-4 py-2 text-[11px] uppercase tracking-widest bg-stone-900 text-white disabled:opacity-40"
          >
            Continua
          </button>
        </form>
      ) : (
        <div className="border border-stone-200 px-3 py-3 space-y-3">
          <p className="font-medium text-stone-900">{state.domain}</p>
          <p className="text-xs text-stone-500">
            Stato:{" "}
            {state.status === "verified"
              ? "ok, in attesa di attivazione sicura"
              : state.status === "error"
                ? "errore — controlla i record"
                : "in attesa dei record"}
          </p>
          {dns ? (
            <div className="bg-stone-50 border border-stone-200 px-3 py-2 space-y-2 text-xs">
              <p>
                TXT — host <code>{dns.txt_record.host}</code> · valore{" "}
                <code className="break-all">{dns.txt_record.value}</code>
              </p>
              <p>
                CNAME — host <code>{dns.cname_record.host}</code> · valore{" "}
                <code>{dns.cname_record.value}</code>
              </p>
            </div>
          ) : null}
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={verify}
              disabled={busy}
              data-testid="cd-verify-btn"
              className="px-3 py-2 text-[11px] uppercase tracking-widest bg-stone-900 text-white disabled:opacity-40"
            >
              Verifica
            </button>
            <button
              type="button"
              onClick={remove}
              disabled={busy}
              data-testid="cd-delete-btn"
              className="px-3 py-2 text-[11px] uppercase tracking-widest border border-red-300 text-red-800"
            >
              Rimuovi
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

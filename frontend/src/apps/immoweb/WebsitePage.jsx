import React, { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import AgencyShell from "./components/AgencyShell";
import { api } from "../../shared/lib/api";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

/**
 * Il mio sito — scelta chiara per agency_admin.
 * 1) Ho già un sito → salva URL, fine.
 * 2) Voglio un sito su OMNIA → scegli aspetto + anteprima.
 * Niente clone, estrattori, JSON, roadmap.
 */
export default function WebsitePage() {
  const { t } = useTranslation();
  const { lang } = useParams();
  const l = (lang || "it").slice(0, 2);

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  const [current, setCurrent] = useState(null);
  const [themes, setThemes] = useState([]);
  const [siteUrl, setSiteUrl] = useState("");
  const [path, setPath] = useState(null); // "external" | "omnia" | null
  const [selectedTheme, setSelectedTheme] = useState("classic");
  const [previewHtml, setPreviewHtml] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);

  const flash = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(""), 4000);
  };

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [th, cur] = await Promise.all([
        api.get("/app/website/themes"),
        api.get("/app/website/theme"),
      ]);
      setThemes(th.data.themes || []);
      setCurrent(cur.data);
      const mode = cur.data?.website_mode;
      const url =
        cur.data?.declared_url ||
        cur.data?.external_url ||
        (cur.data?.existing_domain ? `https://${cur.data.existing_domain}` : "") ||
        "";
      setSiteUrl(url);
      if (mode === "external") setPath("external");
      else if (mode === "omnia_template") setPath("omnia");
      else setPath(null);
      setSelectedTheme(cur.data?.resolved?.theme_id || th.data.default_theme_id || "classic");
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

  const publicPath = current?.public_url ? `${BACKEND_URL}${current.public_url}` : null;

  const loadPreview = useCallback(async () => {
    if (!publicPath || path !== "omnia") {
      setPreviewHtml("");
      return;
    }
    setPreviewLoading(true);
    try {
      const r = await fetch(
        `${publicPath}${publicPath.includes("?") ? "&" : "?"}t=${Date.now()}`,
        { credentials: "same-origin", headers: { Accept: "text/html" } }
      );
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setPreviewHtml(await r.text());
    } catch (e) {
      setPreviewHtml(
        `<!doctype html><html><body style="font-family:system-ui;padding:2rem;color:#444">`
          + `<p>Anteprima non disponibile.</p>`
          + (publicPath
            ? `<p><a href="${publicPath}" target="_blank" rel="noreferrer">Apri in una nuova scheda</a></p>`
            : "")
          + `</body></html>`
      );
    } finally {
      setPreviewLoading(false);
    }
  }, [publicPath, path]);

  useEffect(() => {
    if (loading) return;
    loadPreview();
  }, [loading, loadPreview, selectedTheme]);

  const saveExternal = async () => {
    setBusy(true);
    setError("");
    try {
      await api.post("/app/website/presence", {
        mode: "external",
        external_url: siteUrl.trim(),
      });
      setPath("external");
      flash("Ok: il tuo sito resta com’è. Abbiamo salvato l’indirizzo.");
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

  const chooseOmnia = async () => {
    setBusy(true);
    setError("");
    try {
      await api.post("/app/website/presence", {
        mode: "omnia_template",
        external_url: siteUrl.trim() || undefined,
      });
      setPath("omnia");
      flash("Ok: userai un sito OMNIA. Scegli l’aspetto qui sotto.");
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
      await api.post("/app/website/theme/apply", { theme_id: themeId });
      setSelectedTheme(themeId);
      flash("Aspetto aggiornato.");
      const r = await api.get("/app/website/theme");
      setCurrent(r.data);
    } catch (e) {
      const d = e?.response?.data?.detail;
      setError(typeof d === "string" ? d : e.message || "Errore tema");
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
        ? "Usi un sito preparato da OMNIA (i visitatori lo vedono con i tuoi annunci)."
        : "Non hai ancora scelto. Dimmi cosa preferisci.";

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
            Due possibilità. Niente termini tecnici.
          </p>
          <p
            className="mt-3 text-sm font-sans text-stone-800 border border-stone-200 bg-stone-50 px-3 py-2"
            data-testid="website-status"
          >
            {statusLine}
          </p>
        </header>

        {error ? (
          <p
            data-testid="website-error"
            className="text-sm text-red-800 bg-red-50 border border-red-200 px-3 py-2"
          >
            {error}
          </p>
        ) : null}
        {toast ? (
          <p
            data-testid="website-toast"
            className="text-sm text-emerald-900 bg-emerald-50 border border-emerald-200 px-3 py-2"
          >
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
              1. Ho già un sito
            </p>
            <p className="text-sm text-stone-600 font-sans">
              Resta online dove sta oggi. OMNIA non lo sostituisce e non lo “clona”.
              Serve solo l’indirizzo (per contatti e riferimenti).
            </p>
            <label className="block text-xs uppercase tracking-widest text-stone-500 font-sans">
              Indirizzo del sito
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
              2. Voglio un sito su OMNIA
            </p>
            <p className="text-sm text-stone-600 font-sans">
              Una vetrina nuova gestita qui, con i tuoi immobili. Utile se vuoi mostrare la rete MLS
              sul sito pubblico. Il sito vecchio resta fino a quando non cambi l’indirizzo DNS
              (te lo spieghiamo se serve).
            </p>
            <button
              type="button"
              disabled={busy}
              onClick={chooseOmnia}
              data-testid="website-choose-omnia"
              className="w-full px-3 py-2.5 text-[11px] uppercase tracking-widest border border-stone-900 text-stone-900 disabled:opacity-40"
            >
              Usa un sito OMNIA
            </button>
            <p className="text-xs text-stone-500 font-sans">
              Poi scegli l’aspetto e guarda l’anteprima qui sotto.
            </p>
          </div>
        </div>

        {path === "omnia" ? (
          <section className="space-y-4" data-testid="website-omnia-panel">
            <h2
              className="text-xl text-stone-900"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              Aspetto del sito
            </h2>
            <p className="text-sm text-stone-600 font-sans">
              Tocca un aspetto per applicarlo subito.
            </p>
            <div className="grid sm:grid-cols-2 gap-3">
              {themes.map((th) => {
                const active = selectedTheme === th.id;
                return (
                  <button
                    key={th.id}
                    type="button"
                    disabled={busy}
                    onClick={() => applyTheme(th.id)}
                    data-testid={`theme-card-${th.id}`}
                    className={`text-left px-4 py-3 border transition disabled:opacity-50 ${
                      active
                        ? "border-stone-900 bg-white"
                        : "border-stone-200 bg-stone-50 hover:border-stone-400"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-medium text-stone-900">{th.name}</span>
                      {active ? (
                        <span className="text-[10px] uppercase tracking-widest text-stone-500">attivo</span>
                      ) : null}
                    </div>
                    <div className="flex gap-1.5 mt-2">
                      {Object.values(th.preview_palette || {})
                        .slice(0, 4)
                        .map((c, i) => (
                          <span
                            key={i}
                            className="w-5 h-5 border border-stone-200"
                            style={{ background: c }}
                          />
                        ))}
                    </div>
                    <p className="mt-2 text-xs text-stone-500 font-sans line-clamp-2">{th.description}</p>
                  </button>
                );
              })}
            </div>

            <div className="flex flex-wrap gap-2 items-center">
              <button
                type="button"
                onClick={loadPreview}
                data-testid="website-refresh-preview"
                className="px-3 py-2 text-[11px] uppercase tracking-widest border border-stone-300"
              >
                Aggiorna anteprima
              </button>
              {publicPath ? (
                <a
                  href={publicPath}
                  target="_blank"
                  rel="noreferrer"
                  data-testid="website-open-public"
                  className="px-3 py-2 text-[11px] uppercase tracking-widest border border-stone-300"
                >
                  Apri sito →
                </a>
              ) : null}
              <Link
                to={`/${l}/app/mls`}
                className="px-3 py-2 text-[11px] uppercase tracking-widest border border-stone-300 text-stone-700"
              >
                Rete MLS
              </Link>
            </div>

            <div
              className="border border-stone-300 bg-stone-50 relative overflow-hidden"
              style={{ height: 520 }}
            >
              {previewLoading ? (
                <p className="absolute top-0 inset-x-0 text-xs text-stone-500 bg-stone-100 px-3 py-1 z-10">
                  Carico anteprima…
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

            <details className="border border-stone-200 px-3 py-3" data-testid="website-domain-details">
              <summary className="cursor-pointer text-sm font-medium text-stone-800">
                Voglio usare il mio indirizzo (es. www.agenzia.it) sul sito OMNIA
              </summary>
              <div className="mt-3">
                <CustomDomainSection />
              </div>
            </details>
          </section>
        ) : null}

        {path === "external" && (current?.external_url || siteUrl) ? (
          <p className="text-sm text-stone-600 font-sans" data-testid="website-external-done">
            Indirizzo salvato:{" "}
            <a
              className="underline break-all"
              href={current?.external_url || siteUrl}
              target="_blank"
              rel="noreferrer"
            >
              {current?.external_url || siteUrl}
            </a>
            . Gli immobili e i clienti li gestisci qui in OMNIA; il sito pubblico resta il tuo.
          </p>
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
        Passo per chi vuole che il sito OMNIA risponda al proprio indirizzo (www…).
        Di solito lo fa il tecnico del dominio: aggiungi due record e premi Verifica.
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
                : "in attesa dei record DNS"}
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

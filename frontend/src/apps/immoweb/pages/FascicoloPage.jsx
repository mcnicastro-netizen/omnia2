/*
 * OMNIA — Fascicolo Immobile AI (precursore paperless del Santo Graal)
 *
 * Vista unica: dati immobile + valutazione AI + checklist documentale rogito
 * con upload/download + analisi HAL dei documenti mancanti + render staging.
 */
import React, { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import AgencyShell from "../components/AgencyShell";

const fmt = (n) => (n || n === 0 ? `€ ${Math.round(n).toLocaleString("it-IT")}` : "—");

function priceVsValuation(price, valuation) {
  if (!price || !valuation?.estimated_value) return null;
  const { min, max } = valuation.estimated_value;
  if (price < min) return { label: "Sotto la stima AI", cls: "bg-emerald-100 text-emerald-800 border-emerald-300" };
  if (price > max) return { label: "Sopra la stima AI", cls: "bg-amber-100 text-amber-800 border-amber-300" };
  return { label: "In linea con la stima AI", cls: "bg-sky-100 text-sky-800 border-sky-300" };
}

function ChecklistItem({ item, propertyId, onChanged }) {
  const inputRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const upload = async (file) => {
    if (!file) return;
    setErr("");
    if (file.size > 8 * 1024 * 1024) {
      setErr("Max 8 MB");
      return;
    }
    setBusy(true);
    try {
      // M24 — multipart verso Object Storage (niente più base64 nel body JSON)
      const fd = new FormData();
      fd.append("file", file, file.name);
      fd.append("doc_type", item.key);
      await api.post(`/app/fascicolo/${propertyId}/documents/upload`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 60000,
      });
      onChanged();
    } catch (e) {
      setErr(e.response?.data?.detail || "Upload fallito");
    } finally {
      setBusy(false);
    }
  };

  const removeDoc = async (docId) => {
    try {
      await api.delete(`/app/fascicolo/${propertyId}/documents/${docId}`);
      onChanged();
    } catch (e) {
      setErr("Eliminazione fallita");
    }
  };

  const download = async (docId, name) => {
    try {
      const r = await api.get(`/app/fascicolo/${propertyId}/documents/${docId}/download`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([r.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", name);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch {
      setErr("Download fallito");
    }
  };

  return (
    <div
      data-testid={`fascicolo-doc-${item.key}`}
      className={`border p-4 ${item.present ? "border-emerald-200 bg-emerald-50/40" : item.required ? "border-red-200 bg-red-50/30" : "border-stone-200 bg-white"}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <p className="text-sm text-stone-800 flex items-center gap-2">
            <span>{item.present ? "✅" : item.required ? "🔴" : "⚪"}</span>
            <span>{item.label}</span>
          </p>
          <p className="text-[11px] text-stone-500 mt-0.5 ml-6">
            {item.required ? "Obbligatorio per il rogito" : "Consigliato"}
            {item.note && <span className="text-amber-700"> · {item.note}</span>}
          </p>
          {item.documents.map((d) => (
            <div key={d.id} className="ml-6 mt-1.5 flex items-center gap-2 text-xs text-stone-600">
              <button onClick={() => download(d.id, d.name)} data-testid={`doc-download-${d.id}`} className="underline hover:text-stone-900 truncate max-w-[200px]">
                📎 {d.name}
              </button>
              <button onClick={() => removeDoc(d.id)} data-testid={`doc-delete-${d.id}`} className="text-red-500 hover:text-red-700" title="Elimina">
                ✕
              </button>
            </div>
          ))}
          {err && <p className="ml-6 mt-1 text-[11px] text-red-600">{err}</p>}
        </div>
        <div>
          <input ref={inputRef} type="file" className="hidden" onChange={(e) => upload(e.target.files?.[0])} data-testid={`doc-upload-input-${item.key}`} />
          <button
            onClick={() => inputRef.current?.click()}
            disabled={busy}
            data-testid={`doc-upload-btn-${item.key}`}
            className="text-[11px] uppercase tracking-widest border border-stone-300 hover:border-stone-500 px-3 py-1.5 text-stone-600 whitespace-nowrap"
          >
            {busy ? "..." : "⬆ Carica"}
          </button>
        </div>
      </div>
    </div>
  );
}

function VisuraOpenApiPanel({ propertyId, onAttached }) {
  const [enabled, setEnabled] = useState(false);
  const [form, setForm] = useState({
    provincia: "RM",
    comune: "",
    foglio: "",
    particella: "",
    subalterno: "",
    tipo_catasto: "F",
  });
  const [jobs, setJobs] = useState([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const refresh = useCallback(async () => {
    try {
      const [st, list] = await Promise.all([
        api.get("/docs/status"),
        api.get(`/docs/visura?property_id=${encodeURIComponent(propertyId)}`),
      ]);
      setEnabled(Boolean(st.data?.openapi_visure_enabled));
      setJobs(list.data?.items || []);
    } catch {
      /* panel stays quiet if status fails */
    }
  }, [propertyId]);

  useEffect(() => { refresh(); }, [refresh]);

  const setField = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const requestVisura = async (e) => {
    e.preventDefault();
    setErr("");
    setMsg("");
    if (!form.comune.trim() || !form.foglio.trim() || !form.particella.trim()) {
      setErr("Compila comune, foglio e particella");
      return;
    }
    setBusy(true);
    try {
      const r = await api.post("/docs/visura/request", {
        property_id: propertyId,
        provincia: form.provincia.trim().toUpperCase().slice(0, 2),
        comune: form.comune.trim(),
        foglio: form.foglio.trim(),
        particella: form.particella.trim(),
        subalterno: form.subalterno.trim() || null,
        tipo_catasto: form.tipo_catasto,
        tipo_visura: "ordinaria",
      });
      setMsg(`Richiesta inviata · stato ${r.data.status}${r.data.external_id ? ` · id ${r.data.external_id.slice(0, 8)}` : ""}`);
      await refresh();
    } catch (ex) {
      const d = ex.response?.data?.detail;
      setErr(typeof d === "string" ? d : d?.message || "Richiesta visura fallita");
    } finally {
      setBusy(false);
    }
  };

  const pollJob = async (jobId) => {
    setErr("");
    setBusy(true);
    try {
      const r = await api.get(`/docs/visura/${jobId}`);
      setMsg(`Stato aggiornato: ${r.data.status}`);
      await refresh();
    } catch (ex) {
      setErr(ex.response?.data?.detail || "Aggiornamento stato fallito");
    } finally {
      setBusy(false);
    }
  };

  const attachJob = async (jobId) => {
    setErr("");
    setBusy(true);
    try {
      await api.post(`/docs/visura/${jobId}/attach`);
      setMsg("PDF allegato al Fascicolo come visura catastale");
      await refresh();
      onAttached?.();
    } catch (ex) {
      setErr(ex.response?.data?.detail || "Allegato fallito");
    } finally {
      setBusy(false);
    }
  };

  if (!enabled) {
    return (
      <div className="bg-white border border-stone-200 p-6" data-testid="fascicolo-visura-disabled">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-stone-700">Visura catastale (OpenAPI.it)</h2>
        <p className="text-xs text-stone-500 mt-2">
          Integrazione non attiva su questo ambiente. Contatta il Founder per abilitare sandbox/produzione.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-stone-200 p-6 space-y-4" data-testid="fascicolo-visura-panel">
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-widest text-stone-700">Visura catastale (OpenAPI.it)</h2>
        <p className="text-xs text-stone-500 mt-1">
          Richiedi la visura ufficiale da foglio/particella e allegala al checklist del Fascicolo.
        </p>
      </div>
      <form onSubmit={requestVisura} className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <label className="text-xs text-stone-600 space-y-1">
          <span>Provincia</span>
          <input
            data-testid="visura-provincia"
            className="w-full border border-stone-200 px-2 py-1.5 text-sm"
            value={form.provincia}
            onChange={(e) => setField("provincia", e.target.value)}
            maxLength={2}
          />
        </label>
        <label className="text-xs text-stone-600 space-y-1 col-span-2 sm:col-span-1">
          <span>Comune</span>
          <input
            data-testid="visura-comune"
            className="w-full border border-stone-200 px-2 py-1.5 text-sm"
            value={form.comune}
            onChange={(e) => setField("comune", e.target.value)}
            placeholder="Roma"
          />
        </label>
        <label className="text-xs text-stone-600 space-y-1">
          <span>Foglio</span>
          <input
            data-testid="visura-foglio"
            className="w-full border border-stone-200 px-2 py-1.5 text-sm"
            value={form.foglio}
            onChange={(e) => setField("foglio", e.target.value)}
          />
        </label>
        <label className="text-xs text-stone-600 space-y-1">
          <span>Particella</span>
          <input
            data-testid="visura-particella"
            className="w-full border border-stone-200 px-2 py-1.5 text-sm"
            value={form.particella}
            onChange={(e) => setField("particella", e.target.value)}
          />
        </label>
        <label className="text-xs text-stone-600 space-y-1">
          <span>Subalterno</span>
          <input
            data-testid="visura-subalterno"
            className="w-full border border-stone-200 px-2 py-1.5 text-sm"
            value={form.subalterno}
            onChange={(e) => setField("subalterno", e.target.value)}
          />
        </label>
        <label className="text-xs text-stone-600 space-y-1">
          <span>Catasto</span>
          <select
            data-testid="visura-tipo"
            className="w-full border border-stone-200 px-2 py-1.5 text-sm bg-white"
            value={form.tipo_catasto}
            onChange={(e) => setField("tipo_catasto", e.target.value)}
          >
            <option value="F">Fabbricati</option>
            <option value="T">Terreni</option>
          </select>
        </label>
        <div className="col-span-2 sm:col-span-3">
          <button
            type="submit"
            disabled={busy}
            data-testid="visura-request-btn"
            className="bg-[#0B1E3F] hover:bg-[#16305a] disabled:bg-stone-300 text-white text-xs uppercase tracking-widest px-4 py-2"
          >
            {busy ? "Invio..." : "Richiedi visura"}
          </button>
        </div>
      </form>
      {msg && <p className="text-xs text-emerald-700" data-testid="visura-msg">{msg}</p>}
      {err && <p className="text-xs text-red-700" data-testid="visura-err">{err}</p>}
      {jobs.length > 0 && (
        <ul className="space-y-2 border-t border-stone-100 pt-3">
          {jobs.map((j) => (
            <li key={j.id} className="flex flex-wrap items-center justify-between gap-2 text-xs text-stone-700" data-testid={`visura-job-${j.id}`}>
              <span>
                {j.status} · {j.request?.comune} fg.{j.request?.foglio}/{j.request?.particella}
                {j.external_id ? ` · ${j.external_id.slice(0, 8)}` : ""}
              </span>
              <span className="flex gap-2">
                <button type="button" disabled={busy} onClick={() => pollJob(j.id)} className="underline">
                  Aggiorna
                </button>
                {(j.status === "ready" || j.status === "processing") && (
                  <button type="button" disabled={busy} onClick={() => attachJob(j.id)} className="underline font-medium">
                    Allega PDF
                  </button>
                )}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function FascicoloPage() {
  const { id } = useParams();
  const { i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [analyzing, setAnalyzing] = useState(false);

  const load = useCallback(async () => {
    try {
      const r = await api.get(`/app/fascicolo/${id}`);
      setData(r.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Errore di caricamento");
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const analyze = async () => {
    setAnalyzing(true);
    try {
      const r = await api.post(`/app/fascicolo/${id}/analyze`);
      setData((d) => ({ ...d, last_analysis: r.data.analysis }));
    } catch {
      setError("Analisi HAL non riuscita, riprova");
    } finally {
      setAnalyzing(false);
    }
  };

  if (error) {
    return (
      <AgencyShell current="properties">
        <div data-testid="fascicolo-error" className="p-8 text-sm text-red-700">{error}</div>
      </AgencyShell>
    );
  }
  if (!data) {
    return (
      <AgencyShell current="properties">
        <div className="p-8 text-sm text-stone-500">Caricamento fascicolo...</div>
      </AgencyShell>
    );
  }

  const { property: prop, checklist, progress, staging_jobs, valuation, last_analysis } = data;
  const badge = priceVsValuation(prop.price, valuation);
  const pct = progress.required_total ? Math.round((progress.required_done / progress.required_total) * 100) : 0;

  return (
    <AgencyShell current="properties">
      <section data-testid="fascicolo-page" className="max-w-5xl space-y-6">
        <div>
          <Link to={`/${lang}/app/properties/${id}`} className="text-xs uppercase tracking-widest text-stone-500 hover:text-stone-900">
            ← Torna all'immobile
          </Link>
          <div className="flex items-start justify-between flex-wrap gap-4 mt-2">
            <div>
              <p className="text-[10px] uppercase tracking-[0.3em] text-amber-700 mb-1">OMNIA · Fascicolo Immobile AI</p>
              <h1 className="text-3xl md:text-4xl tracking-tight" style={{ fontFamily: "'Fraunces', Georgia, serif" }} data-testid="fascicolo-title">
                {prop.title || "Immobile"}
              </h1>
              <p className="text-sm text-stone-500 mt-1">
                {prop.city}{prop.zone ? ` · ${prop.zone}` : ""} · {prop.property_type} · {prop.surface_sqm ? `${prop.surface_sqm} m²` : "—"}
              </p>
            </div>
            {prop.cover_url && (
              <img src={prop.cover_url} alt="" className="w-32 h-24 object-cover border border-stone-200" />
            )}
          </div>
        </div>

        {/* Price vs AI valuation */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white border border-stone-200 p-5">
            <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-1">Prezzo annuncio</p>
            <p className="text-2xl text-stone-900" data-testid="fascicolo-price">{fmt(prop.price)}</p>
          </div>
          <div className="bg-white border border-stone-200 p-5">
            <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-1">Stima AI (UNI 10750)</p>
            {valuation ? (
              <>
                <p className="text-2xl text-stone-900" data-testid="fascicolo-valuation">{fmt(valuation.estimated_value?.avg)}</p>
                <p className="text-[11px] text-stone-500">{fmt(valuation.estimated_value?.min)} — {fmt(valuation.estimated_value?.max)}</p>
              </>
            ) : (
              <p className="text-sm text-stone-400">Servono città e superficie</p>
            )}
          </div>
          <div className="bg-white border border-stone-200 p-5 flex flex-col justify-center">
            {badge ? (
              <span data-testid="fascicolo-price-badge" className={`text-xs uppercase tracking-widest px-3 py-2 border text-center ${badge.cls}`}>
                {badge.label}
              </span>
            ) : (
              <span className="text-sm text-stone-400 text-center">—</span>
            )}
          </div>
        </div>

        {/* Checklist */}
        <div className="bg-white border border-stone-200 p-6">
          <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
            <h2 className="text-sm font-semibold uppercase tracking-widest text-stone-700">
              Checklist documentale rogito
            </h2>
            <div className="flex items-center gap-3">
              <div className="w-36 h-2 bg-stone-100 overflow-hidden">
                <div className={`h-full ${pct === 100 ? "bg-emerald-600" : "bg-amber-600"}`} style={{ width: `${pct}%` }} />
              </div>
              <span className="text-xs text-stone-600" data-testid="fascicolo-progress">
                {progress.required_done}/{progress.required_total} obbligatori
              </span>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {checklist.map((item) => (
              <ChecklistItem key={item.key} item={item} propertyId={id} onChanged={load} />
            ))}
          </div>
        </div>

        <VisuraOpenApiPanel propertyId={id} onAttached={load} />

        {/* HAL analysis */}
        <div className="bg-white border border-stone-200 p-6">
          <div className="flex items-center justify-between flex-wrap gap-3 mb-3">
            <h2 className="text-sm font-semibold uppercase tracking-widest text-stone-700">Analisi HAL — prontezza al rogito</h2>
            <button
              onClick={analyze}
              disabled={analyzing}
              data-testid="fascicolo-analyze-btn"
              className="bg-stone-900 hover:bg-stone-700 disabled:bg-stone-300 text-white text-xs uppercase tracking-widest px-4 py-2"
            >
              {analyzing ? "HAL sta analizzando..." : "🤖 Analizza con HAL"}
            </button>
          </div>
          {last_analysis ? (
            <div data-testid="fascicolo-analysis" className="text-sm text-stone-700 whitespace-pre-wrap bg-stone-50 border border-stone-100 p-4">
              {last_analysis.text}
              <p className="text-[10px] text-stone-400 mt-3">
                {last_analysis.source === "al" ? "Analisi HAL (Gemini)" : "Analisi automatica"} · {new Date(last_analysis.at).toLocaleString("it-IT")}
              </p>
            </div>
          ) : (
            <p className="text-sm text-stone-400">Nessuna analisi eseguita. Clicca "Analizza con HAL" per un report sulla prontezza al rogito.</p>
          )}
        </div>

        {/* Staging renders */}
        {staging_jobs.length > 0 && (
          <div className="bg-white border border-stone-200 p-6">
            <h2 className="text-sm font-semibold uppercase tracking-widest text-stone-700 mb-4">
              Render Virtual Staging ({staging_jobs.length})
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {staging_jobs.map((j) => (
                <div key={j.id} className="border border-stone-100">
                  {j.variant_url && <img src={j.variant_url} alt={j.style} className="w-full h-28 object-cover" />}
                  <p className="p-2 text-[11px] text-stone-500">{j.style} · {j.room_type}{j.mode === "reverse" ? " · 🔄" : ""}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="bg-white border border-stone-200 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-widest text-stone-700">Modulistica</h2>
            <p className="text-xs text-stone-500 mt-1">Genera mandati, proposte e preliminari brandizzati dall&apos;agenzia.</p>
          </div>
          <Link
            to={`/${lang}/app/modulistica?property_id=${id}`}
            data-testid="fascicolo-modulistica-link"
            className="text-xs uppercase tracking-widest bg-[#0B1E3F] text-white px-4 py-2 text-center"
          >
            Apri modulistica
          </Link>
        </div>
      </section>
    </AgencyShell>
  );
}

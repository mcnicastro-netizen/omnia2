import React, { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import AgencyShell from "../components/AgencyShell";
import Brand from "../../../shared/components/Brand";

/**
 * ImportXmlPage — M2.5.4a Universal XML Importer.
 * Two-phase flow: upload → preview report → confirm commit.
 * Copy: intentionally generic ("il tuo attuale gestionale"). No competitor names.
 */
export default function ImportXmlPage() {
  const { t } = useTranslation();
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [preview, setPreview] = useState(null); // {session_id, report}
  const [commitResult, setCommitResult] = useState(null);
  const [skipDup, setSkipDup] = useState(true);

  const onFile = useCallback((f) => {
    setError(null);
    setCommitResult(null);
    setPreview(null);
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".xml")) {
      setError(t("import.err_not_xml") || "Il file deve avere estensione .xml");
      return;
    }
    if (f.size > 50 * 1024 * 1024) {
      setError(t("import.err_too_big") || "File troppo grande (max 50MB)");
      return;
    }
    setFile(f);
  }, [t]);

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    onFile(e.dataTransfer.files?.[0]);
  };

  const uploadPreview = async () => {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const r = await api.post("/app/import/xml/preview", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setPreview(r.data);
    } catch (e) {
      setError(e?.response?.data?.detail || "upload_error");
    } finally {
      setBusy(false);
    }
  };

  const doCommit = async (dryRun) => {
    if (!preview) return;
    setBusy(true);
    setError(null);
    try {
      const r = await api.post("/app/import/xml/commit", {
        session_id: preview.session_id,
        dry_run: dryRun,
        skip_duplicates_by_ref: skipDup,
      });
      setCommitResult({ ...r.data, dry_run: dryRun });
      if (!dryRun) {
        setPreview(null); // session consumed
      }
    } catch (e) {
      setError(e?.response?.data?.detail || "commit_error");
    } finally {
      setBusy(false);
    }
  };

  const report = preview?.report;

  return (
    <AgencyShell current="import">
      <section data-testid="import-page" className="space-y-8 max-w-4xl">
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-2">
            <Brand>ImmoWeb · Migrazione</Brand>
          </p>
          <h1
            className="text-3xl md:text-4xl tracking-tight"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            {t("import.title") || "Importa da altro gestionale"}
          </h1>
          <p className="text-sm text-stone-600 mt-2 max-w-2xl">
            {t("import.subtitle") ||
              "Carica il file XML esportato dal tuo attuale gestionale. Vediamo insieme cosa contiene, poi confermi l'import in OMNIA. Nessuna modifica alla tua fonte originale."}
          </p>
        </div>

        {/* STEP 1 — Upload */}
        {!preview && (
          <div
            data-testid="import-dropzone"
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            className={`border-2 border-dashed rounded-lg p-10 text-center transition-colors ${
              dragOver ? "border-stone-900 bg-stone-50" : "border-stone-300 bg-white"
            }`}
          >
            <p className="text-lg mb-2" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              {file ? file.name : (t("import.drop_hint") || "Trascina qui il tuo file XML")}
            </p>
            <p className="text-xs text-stone-500 mb-4">
              {file
                ? `${(file.size / 1024).toFixed(0)} KB`
                : (t("import.drop_or") || "o seleziona dal disco")}
            </p>
            <label className="inline-block cursor-pointer bg-stone-900 text-stone-50 px-5 py-2 rounded text-xs uppercase tracking-widest hover:bg-stone-700">
              <input
                data-testid="import-file-input"
                type="file"
                accept=".xml,text/xml,application/xml"
                onChange={(e) => onFile(e.target.files?.[0])}
                className="hidden"
              />
              {t("import.choose_file") || "Scegli file"}
            </label>
            {file && (
              <div className="mt-6">
                <button
                  onClick={uploadPreview}
                  disabled={busy}
                  data-testid="import-analyze-btn"
                  className="bg-emerald-700 text-white px-6 py-2.5 rounded text-xs uppercase tracking-widest hover:bg-emerald-800 disabled:opacity-40"
                >
                  {busy ? "…" : (t("import.analyze") || "Analizza contenuto")}
                </button>
              </div>
            )}
          </div>
        )}

        {error && (
          <div
            data-testid="import-error"
            className="border border-red-300 bg-red-50 text-red-700 text-sm px-4 py-3 rounded"
          >
            {error}
          </div>
        )}

        {/* STEP 2 — Preview report */}
        {preview && report && (
          <div className="space-y-6" data-testid="import-preview">
            <div className="bg-emerald-50 border border-emerald-300 rounded-lg p-4">
              <p className="text-[10px] uppercase tracking-widest text-emerald-800 font-semibold">
                {t("import.parsed_title") || "Analisi completata"}
              </p>
              <p className="text-3xl mt-1 text-emerald-900" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                {report.parsed_ok} / {report.total_found} <span className="text-sm text-emerald-700">immobili leggibili</span>
              </p>
              {report.skipped > 0 && (
                <p className="text-xs text-amber-700 mt-1">
                  {report.skipped} {t("import.skipped") || "record scartati (dati incompleti)"}
                </p>
              )}
            </div>

            {/* Aggregations */}
            <div className="grid md:grid-cols-3 gap-4">
              <StatCard label={t("import.by_type") || "Per tipologia"} data={report.by_type} testid="stat-type" />
              <StatCard label={t("import.by_operation") || "Per contratto"} data={report.by_operation} testid="stat-op" />
              <StatCard label={t("import.by_city") || "Per città"} data={report.by_city} testid="stat-city" />
            </div>

            {(report.without_photos > 0 || report.without_price > 0) && (
              <div className="bg-amber-50 border border-amber-300 rounded-lg p-4 text-sm text-amber-900" data-testid="import-warnings">
                {report.without_photos > 0 && <p>⚠️ {report.without_photos} {t("import.warn_photos") || "immobili senza foto"}</p>}
                {report.without_price > 0 && <p>⚠️ {report.without_price} {t("import.warn_price") || "immobili senza prezzo/canone"}</p>}
              </div>
            )}

            {/* Samples */}
            <div>
              <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-3">
                {t("import.samples") || "Anteprima primi 5 immobili"}
              </p>
              <div className="border border-stone-200 rounded-lg overflow-hidden bg-white">
                <table className="w-full text-sm">
                  <thead className="bg-stone-50 text-[10px] uppercase tracking-widest text-stone-500">
                    <tr>
                      <th className="text-left px-3 py-2">Ref</th>
                      <th className="text-left px-3 py-2">Titolo</th>
                      <th className="text-left px-3 py-2">Città</th>
                      <th className="text-left px-3 py-2">Tipo</th>
                      <th className="text-left px-3 py-2">Contratto</th>
                      <th className="text-right px-3 py-2">Prezzo</th>
                      <th className="text-right px-3 py-2">MQ</th>
                      <th className="text-right px-3 py-2">📷</th>
                    </tr>
                  </thead>
                  <tbody data-testid="import-samples-table">
                    {report.samples.map((s, i) => (
                      <tr key={i} className="border-t border-stone-200">
                        <td className="px-3 py-2 font-mono text-xs text-stone-500">{s.reference_code || "—"}</td>
                        <td className="px-3 py-2 text-stone-900 truncate max-w-xs">{s.title}</td>
                        <td className="px-3 py-2 text-stone-600">{s.city}</td>
                        <td className="px-3 py-2 text-stone-600 text-xs">{s.property_type}</td>
                        <td className="px-3 py-2 text-stone-600 text-xs">{s.operation}</td>
                        <td className="px-3 py-2 text-right tabular-nums text-stone-900">
                          {s.price ? `€${s.price.toLocaleString("it-IT")}` : s.rent_monthly ? `€${s.rent_monthly}/mese` : "—"}
                        </td>
                        <td className="px-3 py-2 text-right tabular-nums text-stone-500">{s.surface_sqm || "—"}</td>
                        <td className="px-3 py-2 text-right tabular-nums text-stone-500">{s.photos_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Divergences */}
            {report.divergences.length > 0 && (
              <details className="bg-stone-50 border border-stone-200 rounded p-3 text-xs" data-testid="import-divergences">
                <summary className="cursor-pointer text-stone-700">
                  {t("import.divergences") || "Divergenze rilevate"} ({report.divergences.length})
                </summary>
                <ul className="mt-2 space-y-1 font-mono text-stone-600">
                  {report.divergences.map((d, i) => (<li key={i}>· {d}</li>))}
                </ul>
              </details>
            )}

            {/* Options + commit */}
            <div className="bg-white border border-stone-200 rounded-lg p-5 space-y-3">
              <label className="flex items-start gap-2 text-sm text-stone-700">
                <input
                  type="checkbox"
                  checked={skipDup}
                  onChange={(e) => setSkipDup(e.target.checked)}
                  data-testid="import-skip-dup-checkbox"
                  className="mt-1"
                />
                <span>
                  <strong>{t("import.dedupe") || "Salta immobili già presenti"}</strong>{" "}
                  <span className="text-stone-500">
                    {t("import.dedupe_hint") || "(match per codice riferimento — consigliato per non duplicare)"}
                  </span>
                </span>
              </label>
              <div className="flex gap-2 pt-2">
                <button
                  onClick={() => doCommit(true)}
                  disabled={busy}
                  data-testid="import-dry-btn"
                  className="text-xs uppercase tracking-widest border border-stone-300 text-stone-700 px-4 py-2 rounded hover:bg-stone-50 disabled:opacity-40"
                >
                  {t("import.simulate") || "Simulazione (nessuna scrittura)"}
                </button>
                <button
                  onClick={() => doCommit(false)}
                  disabled={busy}
                  data-testid="import-commit-btn"
                  className="text-xs uppercase tracking-widest bg-emerald-700 text-white px-5 py-2 rounded hover:bg-emerald-800 disabled:opacity-40"
                >
                  {busy ? "…" : (t("import.confirm") || "Importa in OMNIA")}
                </button>
                <button
                  onClick={() => { setPreview(null); setFile(null); setCommitResult(null); }}
                  data-testid="import-reset-btn"
                  className="text-xs uppercase tracking-widest text-stone-500 hover:text-stone-800 ml-auto"
                >
                  {t("import.cancel") || "Annulla"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* STEP 3 — Commit result */}
        {commitResult && (
          <div
            className={`border rounded-lg p-4 ${
              commitResult.inserted > 0
                ? "bg-emerald-50 border-emerald-400 text-emerald-900"
                : "bg-stone-50 border-stone-300 text-stone-700"
            }`}
            data-testid="import-commit-result"
          >
            {commitResult.dry_run ? (
              <>
                <p className="font-semibold">🧪 {t("import.simulation_done") || "Simulazione completata"}</p>
                <p className="text-sm mt-1">
                  In caso di import reale sarebbero stati inseriti <strong>{commitResult.inserted}</strong> immobili,{" "}
                  <strong>{commitResult.skipped_by_reference}</strong> saltati per duplicato.
                </p>
              </>
            ) : commitResult.inserted > 0 ? (
              <>
                <p className="font-semibold">✅ {t("import.done") || "Import completato"}</p>
                <p className="text-sm mt-1">
                  <strong>{commitResult.inserted}</strong> immobili importati con successo,{" "}
                  <strong>{commitResult.skipped_by_reference}</strong> saltati (già presenti).
                </p>
              </>
            ) : (
              <>
                <p className="font-semibold">ℹ️ {t("import.nothing_new") || "Nessun immobile nuovo importato"}</p>
                <p className="text-sm mt-1">
                  Tutti i <strong>{commitResult.skipped_by_reference}</strong> immobili erano già presenti (dedupe attivo).
                </p>
              </>
            )}
          </div>
        )}
      </section>
    </AgencyShell>
  );
}

function StatCard({ label, data, testid }) {
  const entries = Object.entries(data || {}).sort((a, b) => b[1] - a[1]);
  return (
    <div className="bg-white border border-stone-200 rounded-lg p-4" data-testid={testid}>
      <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-2">{label}</p>
      <ul className="space-y-1">
        {entries.slice(0, 6).map(([k, v]) => (
          <li key={k} className="flex justify-between text-sm">
            <span className="text-stone-700 truncate mr-2">{k}</span>
            <span className="text-stone-900 tabular-nums font-medium">{v}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

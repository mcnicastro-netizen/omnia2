import React, { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import AgencyShell from "./components/AgencyShell";
import { api, API_BASE } from "../../shared/lib/api";
import { formatApiErrorDetail } from "../../shared/lib/auth";

/** Client Import — dual mode page.
 *
 *  Tab A "Standard CSV": legacy template-based flow (preserved as advanced mode).
 *  Tab B "⚡ AI Smart Import" (D-FUTURE-07): upload any messy file → Gemini parses
 *  → confidence-scored preview → inline edits → commit.
 */
export default function ClientImportPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const [tab, setTab] = useState("ai");   // "ai" | "csv"
  return (
    <AgencyShell current="clients">
      <section data-testid="client-import-page" className="max-w-5xl space-y-6">
        <div>
          <Link to={`/${lang}/app/clients`} className="text-xs uppercase tracking-widest text-stone-500 hover:text-stone-900">
            ← {t("client_import.back_to_clients")}
          </Link>
          <h1 className="text-3xl md:text-4xl tracking-tight mt-2" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            {t("client_import.title")}
          </h1>
          <p className="text-stone-600 mt-1">{t("client_import.subtitle")}</p>
        </div>

        {/* Tab switcher */}
        <div className="flex gap-2 border-b border-stone-200" data-testid="import-tabs">
          <TabBtn id="ai" active={tab === "ai"} onClick={() => setTab("ai")}
                  label={t("client_import.tab_ai")} sub={t("client_import.tab_ai_sub")} highlight />
          <TabBtn id="csv" active={tab === "csv"} onClick={() => setTab("csv")}
                  label={t("client_import.tab_csv")} sub={t("client_import.tab_csv_sub")} />
        </div>

        {tab === "ai" ? <AISmartImport t={t} lang={lang} /> : <StandardCSVImport t={t} lang={lang} />}
      </section>
    </AgencyShell>
  );
}

function TabBtn({ id, active, onClick, label, sub, highlight }) {
  return (
    <button
      type="button"
      data-testid={`tab-${id}`}
      onClick={onClick}
      className={`px-5 py-3 text-left border-b-2 transition ${
        active
          ? "border-stone-900"
          : "border-transparent hover:border-stone-300"
      }`}
    >
      <span className={`block text-sm font-semibold ${active ? "text-stone-900" : "text-stone-500"}`}>
        {label}{highlight && !active && <span className="ml-1.5 text-[9px] uppercase tracking-widest text-emerald-700">novità</span>}
      </span>
      <span className="block text-xs text-stone-500 mt-0.5">{sub}</span>
    </button>
  );
}

/* ============================================================================
 *  TAB B — AI Smart Import (D-FUTURE-07)
 * ============================================================================ */
function AISmartImport({ t, lang }) {
  const nav = useNavigate();
  const fileInput = useRef(null);
  const [phase, setPhase] = useState("idle");  // idle | uploading | preview | committing | done
  const [error, setError] = useState("");
  const [draft, setDraft] = useState(null);
  const [filename, setFilename] = useState("");
  const [minConf, setMinConf] = useState(50);
  const [gdpr, setGdpr] = useState(false);
  const [commitResult, setCommitResult] = useState(null);

  const onPick = (f) => {
    if (!f) return;
    setError(""); setDraft(null); setCommitResult(null);
    setFilename(f.name); setPhase("uploading");
    const form = new FormData();
    form.append("file", f);
    api.post("/app/clients/import/ai", form, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    })
      .then(({ data }) => { setDraft(data); setPhase("preview"); })
      .catch((err) => {
        setError(formatApiErrorDetail(err?.response?.data?.detail) || err.message || "error");
        setPhase("idle");
      });
  };

  const onDrop = (e) => { e.preventDefault(); const f = e.dataTransfer.files?.[0]; if (f) onPick(f); };

  const patchRow = async (idx, patch) => {
    try {
      const { data } = await api.patch(`/app/clients/import/ai/draft/${draft.draft_id}/row/${idx}`, patch);
      const rows = [...draft.rows];
      rows[idx] = data.row;
      setDraft({ ...draft, rows });
    } catch (err) {
      setError(formatApiErrorDetail(err?.response?.data?.detail) || err.message);
    }
  };

  const dropRow = (idx) => patchRow(idx, { drop: true });
  const undropRow = (idx) => patchRow(idx, { drop: false });

  const commit = async () => {
    setPhase("committing"); setError("");
    try {
      const { data } = await api.post(`/app/clients/import/ai/draft/${draft.draft_id}/commit`, {
        min_confidence: minConf,
        default_gdpr_consent: gdpr,
      });
      setCommitResult(data); setPhase("done");
    } catch (err) {
      setError(formatApiErrorDetail(err?.response?.data?.detail) || err.message);
      setPhase("preview");
    }
  };

  if (phase === "done" && commitResult) {
    return (
      <div data-testid="ai-import-done" className="bg-white border border-stone-300 rounded-lg p-6">
        <h3 className="font-semibold text-stone-900 text-lg mb-2">
          ✓ {t("client_import.done_title")}
        </h3>
        <p className="text-stone-700 mb-2">
          {t("client_import.ai_done_imported", { imported: commitResult.imported, total: commitResult.total_rows })}
        </p>
        {commitResult.skipped > 0 && (
          <p className="text-stone-500 text-sm">
            {t("client_import.ai_done_skipped", { n: commitResult.skipped })}
          </p>
        )}
        <button
          onClick={() => nav(`/${lang}/app/clients`)}
          className="mt-4 px-5 py-2.5 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest rounded-md hover:bg-stone-700"
        >
          {t("client_import.go_to_list")}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-stone-100 border border-stone-200 rounded-lg p-5 flex gap-3 items-start text-sm text-stone-700">
        <span className="text-base leading-none mt-0.5">◆</span>
        <div>
          <p className="font-medium mb-1">{t("client_import.ai_intro_title")}</p>
          <p>{t("client_import.ai_intro_text")}</p>
        </div>
      </div>

      {error && (
        <p data-testid="ai-import-error" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">
          {error}
        </p>
      )}

      {phase === "idle" && (
        <div
          data-testid="ai-dropzone"
          onClick={() => fileInput.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={onDrop}
          className="border-2 border-dashed border-stone-300 rounded-lg p-12 text-center cursor-pointer hover:border-stone-700 hover:bg-stone-50 transition"
        >
          <p className="text-lg text-stone-800 font-medium" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            {t("client_import.ai_drop_here")}
          </p>
          <p className="text-sm text-stone-500 mt-2">{t("client_import.ai_formats")}</p>
          <p className="text-xs text-stone-400 mt-1">{t("client_import.ai_max_size")}</p>
        </div>
      )}
      <input
        ref={fileInput} type="file"
        accept=".csv,.xlsx,.vcf,.txt,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/vcard,text/plain"
        data-testid="ai-file-input"
        onChange={(e) => e.target.files?.[0] && onPick(e.target.files[0])}
        className="hidden"
      />

      {phase === "uploading" && (
        <div data-testid="ai-loading" className="bg-white border border-stone-200 rounded-lg p-12 text-center">
          <p className="text-stone-700 font-medium animate-pulse">{t("client_import.ai_parsing", { file: filename })}</p>
          <p className="text-xs text-stone-500 mt-2">{t("client_import.ai_parsing_hint")}</p>
        </div>
      )}

      {phase === "preview" && draft && (
        <AIPreview
          t={t} draft={draft} onPatchRow={patchRow}
          onDropRow={dropRow} onUndropRow={undropRow}
          minConf={minConf} setMinConf={setMinConf}
          gdpr={gdpr} setGdpr={setGdpr}
          onCommit={commit} onReset={() => { setDraft(null); setPhase("idle"); }}
        />
      )}

      {phase === "committing" && (
        <div className="bg-white border border-stone-200 rounded-lg p-8 text-center">
          <p className="text-stone-700 animate-pulse">{t("client_import.ai_committing")}</p>
        </div>
      )}
    </div>
  );
}

function AIPreview({ t, draft, onPatchRow, onDropRow, onUndropRow, minConf, setMinConf, gdpr, setGdpr, onCommit, onReset }) {
  const eligible = (draft.rows || []).filter((r) => !r._drop && (r.confidence ?? 0) >= minConf);
  return (
    <div className="space-y-4" data-testid="ai-preview">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <p className="text-stone-700 font-medium">
            {t("client_import.ai_preview_title", { n: draft.total_rows, file: draft.source_filename })}
          </p>
          <p className="text-xs text-stone-500 mt-1">
            {t("client_import.ai_buckets", {
              high: draft.confidence_buckets.high,
              medium: draft.confidence_buckets.medium,
              low: draft.confidence_buckets.low,
            })}
          </p>
        </div>
        <button onClick={onReset} className="text-xs uppercase tracking-widest text-stone-500 hover:text-stone-900 underline">
          {t("client_import.ai_change_file")}
        </button>
      </div>

      <div className="border border-stone-200 rounded-lg overflow-hidden bg-white" data-testid="ai-rows-list">
        {(draft.rows || []).map((r) => (
          <AIRowItem key={r.idx} row={r} t={t}
                     onPatchRow={onPatchRow} onDrop={onDropRow} onUndrop={onUndropRow}
                     belowMin={(r.confidence ?? 0) < minConf} />
        ))}
      </div>

      <div className="bg-stone-50 border border-stone-200 rounded-lg p-5 space-y-3">
        <div>
          <label className="block text-xs uppercase tracking-widest text-stone-500 mb-1">
            {t("client_import.ai_min_conf", { v: minConf })}
          </label>
          <input
            type="range" min="0" max="100" step="5" value={minConf}
            data-testid="ai-min-conf-slider"
            onChange={(e) => setMinConf(parseInt(e.target.value))}
            className="w-full"
          />
          <p className="text-xs text-stone-500 mt-1">
            {t("client_import.ai_will_import", { n: eligible.length, total: draft.total_rows })}
          </p>
        </div>
        <label className="flex items-center gap-2 text-sm text-stone-700">
          <input type="checkbox" checked={gdpr} onChange={(e) => setGdpr(e.target.checked)}
                 data-testid="ai-gdpr-checkbox" className="rounded" />
          {t("client_import.ai_gdpr_default")}
        </label>
        <button
          onClick={onCommit}
          disabled={eligible.length === 0}
          data-testid="ai-commit-btn"
          className="px-6 py-3 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest font-medium rounded-md hover:bg-stone-700 disabled:opacity-40"
        >
          ⚡ {t("client_import.ai_commit_btn", { n: eligible.length })}
        </button>
      </div>
    </div>
  );
}

function ConfBadge({ value }) {
  if (value >= 80) {
    return <span className="text-[10px] uppercase tracking-widest px-2 py-0.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded">★ {value}</span>;
  }
  if (value >= 50) {
    return <span className="text-[10px] uppercase tracking-widest px-2 py-0.5 bg-amber-50 border border-amber-200 text-amber-800 rounded">⚠ {value}</span>;
  }
  return <span className="text-[10px] uppercase tracking-widest px-2 py-0.5 bg-red-50 border border-red-200 text-red-700 rounded">! {value}</span>;
}

function AIRowItem({ row, t, onPatchRow, onDrop, onUndrop, belowMin }) {
  const [expanded, setExpanded] = useState(false);
  const dropped = row._drop;
  const prefs = row.preferences || {};
  const prefBits = [];
  if (prefs.operation) prefBits.push(prefs.operation);
  if ((prefs.cities || []).length) prefBits.push(prefs.cities.join(", "));
  if (prefs.price_max) prefBits.push(`max ${prefs.price_max.toLocaleString("it-IT")}€`);
  if (prefs.rooms_min) prefBits.push(`${prefs.rooms_min}+ stanze`);
  return (
    <div
      data-testid={`ai-row-${row.idx}`}
      className={`px-4 py-3 border-b border-stone-100 last:border-0 ${dropped ? "opacity-40 bg-stone-50 line-through" : belowMin ? "bg-amber-50/30" : ""}`}
    >
      <div className="flex items-start gap-3 flex-wrap">
        <ConfBadge value={row.confidence ?? 0} />
        <div className="flex-1 min-w-[200px]">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-stone-900">{row.name} {row.surname || ""}</span>
            <span className="text-[10px] uppercase tracking-widest text-stone-400">{row.client_type}</span>
          </div>
          <div className="text-xs text-stone-600 mt-0.5">
            {[row.email, row.phone].filter(Boolean).join(" · ") || <span className="italic">{t("client_import.ai_no_contact")}</span>}
          </div>
          {prefBits.length > 0 && (
            <div className="text-xs text-stone-500 mt-0.5">↳ {prefBits.join(" · ")}</div>
          )}
          {(row.warnings || []).length > 0 && (
            <div className="text-xs text-amber-700 mt-1">⚠ {(row.warnings || []).join(" · ")}</div>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            type="button"
            data-testid={`ai-row-expand-${row.idx}`}
            onClick={() => setExpanded(!expanded)}
            className="text-xs px-2 py-1 text-stone-500 hover:text-stone-900"
          >
            {expanded ? t("client_import.ai_collapse") : t("client_import.ai_edit")}
          </button>
          {dropped ? (
            <button
              type="button"
              data-testid={`ai-row-undrop-${row.idx}`}
              onClick={() => onUndrop(row.idx)}
              className="text-xs px-2 py-1 text-stone-700 hover:text-stone-900"
            >
              ↺ {t("client_import.ai_restore")}
            </button>
          ) : (
            <button
              type="button"
              data-testid={`ai-row-drop-${row.idx}`}
              onClick={() => onDrop(row.idx)}
              className="text-xs px-2 py-1 text-red-700 hover:bg-red-50 rounded"
            >
              ✕ {t("client_import.ai_drop")}
            </button>
          )}
        </div>
      </div>

      {expanded && !dropped && (
        <div className="mt-3 pt-3 border-t border-stone-100 grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
          <EditableField label={t("client_import.ai_field_name")} value={row.name} onSave={(v) => onPatchRow(row.idx, { name: v })} />
          <EditableField label={t("client_import.ai_field_surname")} value={row.surname || ""} onSave={(v) => onPatchRow(row.idx, { surname: v })} />
          <EditableField label="Email" value={row.email || ""} onSave={(v) => onPatchRow(row.idx, { email: v })} />
          <EditableField label={t("client_import.ai_field_phone")} value={row.phone || ""} onSave={(v) => onPatchRow(row.idx, { phone: v })} />
          <SelectField label={t("client_import.ai_field_type")} value={row.client_type}
            options={["buyer", "seller", "tenant", "landlord", "investor"]}
            onSave={(v) => onPatchRow(row.idx, { client_type: v })} />
          {row.source_excerpt && (
            <div className="md:col-span-3 text-stone-400 italic text-[11px] mt-1 truncate">
              {t("client_import.ai_excerpt")}: {row.source_excerpt}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function EditableField({ label, value, onSave }) {
  const [v, setV] = useState(value || "");
  return (
    <label className="block">
      <span className="block text-stone-500 mb-0.5">{label}</span>
      <input
        value={v} onChange={(e) => setV(e.target.value)}
        onBlur={() => v !== value && onSave(v)}
        className="w-full px-2 py-1 border border-stone-300 rounded text-stone-900"
      />
    </label>
  );
}

function SelectField({ label, value, options, onSave }) {
  return (
    <label className="block">
      <span className="block text-stone-500 mb-0.5">{label}</span>
      <select value={value || ""} onChange={(e) => onSave(e.target.value)}
        className="w-full px-2 py-1 border border-stone-300 rounded text-stone-900 bg-white">
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </label>
  );
}

/* ============================================================================
 *  TAB A — Standard CSV (legacy template flow, preserved)
 * ============================================================================ */
function parseCSV(text) {
  const lines = text.replace(/\r\n/g, "\n").split("\n").filter((l) => l.trim().length > 0);
  if (lines.length === 0) return { headers: [], rows: [] };
  const sep = (lines[0].match(/;/g) || []).length > (lines[0].match(/,/g) || []).length ? ";" : ",";
  const headers = lines[0].split(sep).map((h) => h.trim().replace(/^\ufeff/, "").replace(/^"|"$/g, ""));
  const rows = lines.slice(1).map((line) => {
    const values = line.split(sep).map((v) => v.trim().replace(/^"|"$/g, ""));
    const obj = {};
    headers.forEach((h, i) => (obj[h] = values[i] ?? ""));
    return obj;
  });
  return { headers, rows };
}

function StandardCSVImport({ t, lang }) {
  const nav = useNavigate();
  const fileInput = useRef(null);
  const [headers, setHeaders] = useState([]);
  const [rows, setRows] = useState([]);
  const [filename, setFilename] = useState("");
  const [result, setResult] = useState(null);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState("");

  const downloadTemplate = async () => {
    const url = `${API_BASE}/app/clients/_template/csv`;
    const resp = await fetch(url, { credentials: "include" });
    const blob = await resp.blob();
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "omnia-clienti-template.csv";
    link.click();
  };

  const handleFile = (file) => {
    setError(""); setResult(null); setFilename(file.name);
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const { headers, rows } = parseCSV(e.target.result);
        setHeaders(headers); setRows(rows);
      } catch (err) {
        setError(t("client_import.parse_error", { msg: err.message }));
      }
    };
    reader.readAsText(file, "utf-8");
  };

  const onDrop = (e) => { e.preventDefault(); const f = e.dataTransfer.files?.[0]; if (f) handleFile(f); };

  const doImport = async () => {
    setImporting(true); setError("");
    try {
      const { data } = await api.post("/app/clients/import/csv", { rows, filename });
      setResult(data);
    } catch (err) {
      setError(formatApiErrorDetail(err?.response?.data?.detail) || t("common.error"));
    } finally {
      setImporting(false);
    }
  };

  if (result) {
    return (
      <div data-testid="client-csv-result" className="bg-white border border-stone-300 rounded-lg p-6">
        <h3 className="font-semibold text-stone-900 text-lg mb-2">✓ {t("client_import.done_title")}</h3>
        <p className="text-stone-700 mb-2">
          {t("client_import.done_imported", { imported: result.imported, total: result.total_rows })}
        </p>
        {result.errors?.length > 0 && (
          <details className="text-sm text-stone-700 mt-2">
            <summary className="cursor-pointer font-medium">⚠ {t("client_import.done_errors", { count: result.errors.length })}</summary>
            <ul className="mt-2 ml-4 list-disc">
              {result.errors.slice(0, 10).map((e, i) => (
                <li key={i}>{t("client_import.error_row", { row: e.row, message: e.message })}</li>
              ))}
            </ul>
          </details>
        )}
        <button onClick={() => nav(`/${lang}/app/clients`)} className="mt-4 px-5 py-2.5 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest rounded-md hover:bg-stone-700">
          {t("client_import.go_to_list")}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <Step num="1" title={t("client_import.step1_title")} text={t("client_import.step1_text")}>
        <button data-testid="client-csv-template-btn" onClick={downloadTemplate}
          className="px-5 py-2.5 border border-stone-300 bg-white text-xs uppercase tracking-widest rounded-md hover:bg-stone-50">
          {t("client_import.template_btn")}
        </button>
        <p className="text-xs text-stone-500 mt-2">{t("client_import.separator_hint")}</p>
      </Step>

      <Step num="2" title={t("client_import.step2_title")} text={t("client_import.step2_text")}>
        <div data-testid="client-csv-dropzone" onClick={() => fileInput.current?.click()}
          onDragOver={(e) => e.preventDefault()} onDrop={onDrop}
          className="border-2 border-dashed border-stone-300 rounded-lg p-8 text-center cursor-pointer hover:border-stone-500 hover:bg-stone-50 transition">
          <p className="text-stone-700 font-medium">{t("client_import.drop_here")}</p>
          <p className="text-xs text-stone-500 mt-1">{t("client_import.or_click")}</p>
        </div>
        <input ref={fileInput} type="file" accept=".csv,text/csv" data-testid="client-csv-file-input"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} className="hidden" />
        {filename && <p className="text-xs text-stone-600 mt-2">📄 {filename} · {rows.length} righe</p>}
        {error && <p data-testid="client-csv-error" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2 mt-3">{error}</p>}
      </Step>

      {rows.length > 0 && (
        <Step num="3" title={t("client_import.step3_title")} text="">
          <div className="bg-white border border-stone-200 rounded-lg p-4 mb-4">
            <p className="text-xs uppercase tracking-widest text-stone-500 mb-2">
              {t("client_import.preview_title", { count: rows.length })}
            </p>
            <div className="overflow-auto max-h-64">
              <table className="text-xs w-full" data-testid="client-csv-preview-table">
                <thead className="bg-stone-50 sticky top-0">
                  <tr>
                    {headers.slice(0, 6).map((h) => <th key={h} className="text-left px-2 py-1.5 font-medium text-stone-600">{h}</th>)}
                    {headers.length > 6 && <th className="text-left px-2 py-1.5 text-stone-400">…</th>}
                  </tr>
                </thead>
                <tbody>
                  {rows.slice(0, 5).map((row, i) => (
                    <tr key={i} className="border-t border-stone-100">
                      {headers.slice(0, 6).map((h) => <td key={h} className="px-2 py-1.5 text-stone-700 truncate max-w-[150px]">{row[h]}</td>)}
                      {headers.length > 6 && <td className="px-2 py-1.5 text-stone-400">…</td>}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <button data-testid="client-csv-import-btn" onClick={doImport} disabled={importing}
            className="px-6 py-3 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest font-medium rounded-md hover:bg-stone-700 disabled:opacity-50">
            {importing ? t("client_import.importing") : t("client_import.import_btn", { count: rows.length })}
          </button>
        </Step>
      )}
    </div>
  );
}

function Step({ num, title, text, children }) {
  return (
    <div className="bg-white border border-stone-200 rounded-lg p-6">
      <div className="flex items-start gap-4">
        <span className="flex-shrink-0 w-8 h-8 rounded-full bg-stone-900 text-stone-50 flex items-center justify-center font-semibold text-sm">
          {num}
        </span>
        <div className="flex-1">
          <h3 className="font-semibold text-stone-900 mb-1">{title}</h3>
          {text && <p className="text-sm text-stone-600 mb-3">{text}</p>}
          {children}
        </div>
      </div>
    </div>
  );
}

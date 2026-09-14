import React, { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import AgencyShell from "./components/AgencyShell";
import { api, API_BASE } from "../../shared/lib/api";
import { formatApiErrorDetail } from "../../shared/lib/auth";

function parseCSV(text) {
  // M14 — RFC-4180-aware parser: supporta campi quotati con separatori/righe interne
  // e doppi apici escaped (""). Auto-rileva ; o , come separatore.
  const clean = text.replace(/^\ufeff/, "").replace(/\r\n/g, "\n");
  const firstLine = clean.split("\n", 1)[0] || "";
  const sep = (firstLine.match(/;/g) || []).length > (firstLine.match(/,/g) || []).length ? ";" : ",";

  const records = [];
  let field = "";
  let record = [];
  let inQuotes = false;
  for (let i = 0; i < clean.length; i++) {
    const c = clean[i];
    if (inQuotes) {
      if (c === '"') {
        if (clean[i + 1] === '"') { field += '"'; i++; }
        else inQuotes = false;
      } else field += c;
    } else if (c === '"') {
      inQuotes = true;
    } else if (c === sep) {
      record.push(field); field = "";
    } else if (c === "\n") {
      record.push(field); field = "";
      if (record.some((v) => v.trim() !== "")) records.push(record);
      record = [];
    } else field += c;
  }
  record.push(field);
  if (record.some((v) => v.trim() !== "")) records.push(record);

  if (records.length === 0) return { headers: [], rows: [] };
  const headers = records[0].map((h) => h.trim());
  const rows = records.slice(1).map((values) => {
    const obj = {};
    headers.forEach((h, i) => (obj[h] = (values[i] ?? "").trim()));
    return obj;
  });
  return { headers, rows };
}

export default function PropertyImportPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();
  const [tab, setTab] = useState("csv");
  const fileInput = useRef(null);

  // CSV state
  const [csvHeaders, setCsvHeaders] = useState([]);
  const [csvRows, setCsvRows] = useState([]);
  const [csvFilename, setCsvFilename] = useState("");
  const [csvResult, setCsvResult] = useState(null);
  const [csvImporting, setCsvImporting] = useState(false);
  const [csvError, setCsvError] = useState("");

  // XML state
  const [xmlMode, setXmlMode] = useState("url"); // "url" or "paste"
  const [xmlUrl, setXmlUrl] = useState("");
  const [xmlContent, setXmlContent] = useState("");
  const [xmlImporting, setXmlImporting] = useState(false);
  const [xmlResult, setXmlResult] = useState(null);
  const [xmlError, setXmlError] = useState("");

  const downloadTemplate = async () => {
    const url = `${API_BASE}/app/properties/_template/csv`;
    const resp = await fetch(url, { credentials: "include" });
    const blob = await resp.blob();
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "omnia-immobili-template.csv";
    link.click();
  };

  const handleFile = (file) => {
    setCsvError("");
    setCsvResult(null);
    setCsvFilename(file.name);
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const { headers, rows } = parseCSV(e.target.result);
        setCsvHeaders(headers);
        setCsvRows(rows);
      } catch (err) {
        setCsvError("File CSV non valido: " + err.message);
      }
    };
    reader.readAsText(file, "utf-8");
  };

  const onDrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) handleFile(f);
  };

  const importCsv = async () => {
    setCsvImporting(true);
    setCsvError("");
    try {
      const { data } = await api.post("/app/properties/import/csv", { rows: csvRows, filename: csvFilename });
      setCsvResult(data);
    } catch (err) {
      setCsvError(formatApiErrorDetail(err?.response?.data?.detail) || t("common.error"));
    } finally {
      setCsvImporting(false);
    }
  };

  const importXml = async () => {
    setXmlImporting(true);
    setXmlError("");
    try {
      const payload = xmlMode === "url"
        ? { feed_url: xmlUrl.trim() }
        : { xml_content: xmlContent };
      const { data } = await api.post("/app/properties/import/xml", payload);
      if (data.async && data.job_id) {
        // M23 — import URL in background: polling dello stato job ogni 2s (max 5 min)
        for (let i = 0; i < 150; i++) {
          await new Promise((r) => setTimeout(r, 2000));
          const { data: job } = await api.get(`/app/properties/import/jobs/${data.job_id}`);
          if (["completed", "completed_with_errors", "failed"].includes(job.status)) {
            setXmlResult({
              job_id: job.id,
              imported: job.imported_count,
              total_rows: job.total_rows,
              errors: job.errors || [],
              status: job.status,
            });
            return;
          }
        }
        setXmlError("Import ancora in corso — controlla lo storico import tra qualche minuto.");
      } else {
        setXmlResult(data);
      }
    } catch (err) {
      setXmlError(formatApiErrorDetail(err?.response?.data?.detail) || t("common.error"));
    } finally {
      setXmlImporting(false);
    }
  };

  return (
    <AgencyShell current="properties">
      <section data-testid="property-import-page" className="max-w-4xl space-y-6">
        <div>
          <Link to={`/${lang}/app/properties`} className="text-xs uppercase tracking-widest text-stone-500 hover:text-stone-900">
            {t("properties.back_to_list")}
          </Link>
          <h1 className="text-3xl md:text-4xl tracking-tight mt-2" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            {t("import.page_title")}
          </h1>
          <p className="text-stone-600 mt-1">{t("import.page_subtitle")}</p>
        </div>

        <div className="flex border-b border-stone-200">
          <TabBtn active={tab === "csv"} onClick={() => setTab("csv")} testid="tab-csv">
            {t("import.tab_csv")}
          </TabBtn>
          <TabBtn active={tab === "xml"} onClick={() => setTab("xml")} testid="tab-xml">
            {t("import.tab_xml")}
          </TabBtn>
        </div>

        {/* CSV TAB */}
        {tab === "csv" && (
          <div className="space-y-6">
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-5">
              <h2 className="font-semibold text-amber-900 mb-1">{t("import.csv_intro_title")}</h2>
              <p className="text-sm text-amber-800">{t("import.csv_intro_text")}</p>
            </div>

            <Step num="1" title={t("import.csv_step1_title")} text={t("import.csv_step1_text")}>
              <button data-testid="csv-template-btn" onClick={downloadTemplate} className="px-5 py-2.5 border border-stone-300 bg-white text-xs uppercase tracking-widest rounded-md hover:bg-stone-50">
                {t("import.csv_template_btn")}
              </button>
              <p className="text-xs text-stone-500 mt-2">{t("import.csv_separator_hint")}</p>
            </Step>

            <Step num="2" title={t("import.csv_step2_title")} text={t("import.csv_step2_text")}>
              <div
                data-testid="csv-dropzone"
                onClick={() => fileInput.current?.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={onDrop}
                className="border-2 border-dashed border-stone-300 rounded-lg p-8 text-center cursor-pointer hover:border-stone-500 hover:bg-stone-50 transition"
              >
                <p className="text-stone-700 font-medium">{t("import.csv_drop_here")}</p>
                <p className="text-xs text-stone-500 mt-1">{t("import.csv_or_click")}</p>
              </div>
              <input
                ref={fileInput}
                type="file"
                accept=".csv,text/csv"
                data-testid="csv-file-input"
                onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                className="hidden"
              />
              {csvFilename && <p className="text-xs text-stone-600 mt-2">📄 {csvFilename}</p>}
              {csvError && <p className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2 mt-3">{csvError}</p>}
            </Step>

            {csvRows.length > 0 && !csvResult && (
              <Step num="3" title={t("import.csv_step3_title")} text="">
                <div className="bg-white border border-stone-200 rounded-lg p-4 mb-4">
                  <p className="text-xs uppercase tracking-widest text-stone-500 mb-2">
                    {t("import.csv_preview_title", { count: csvRows.length })}
                  </p>
                  <div className="overflow-auto max-h-64">
                    <table className="text-xs w-full">
                      <thead className="bg-stone-50 sticky top-0">
                        <tr>
                          {csvHeaders.slice(0, 6).map((h) => <th key={h} className="text-left px-2 py-1.5 font-medium text-stone-600">{h}</th>)}
                          {csvHeaders.length > 6 && <th className="text-left px-2 py-1.5 text-stone-400">…</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {csvRows.slice(0, 5).map((row, i) => (
                          <tr key={i} className="border-t border-stone-100">
                            {csvHeaders.slice(0, 6).map((h) => <td key={h} className="px-2 py-1.5 text-stone-700 truncate max-w-[150px]">{row[h]}</td>)}
                            {csvHeaders.length > 6 && <td className="px-2 py-1.5 text-stone-400">…</td>}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                <button data-testid="csv-import-btn" onClick={importCsv} disabled={csvImporting} className="px-6 py-3 bg-emerald-700 text-stone-50 text-xs uppercase tracking-widest font-medium rounded-md hover:bg-emerald-800 disabled:opacity-50">
                  {csvImporting ? t("import.csv_importing") : t("import.csv_import_btn")}
                </button>
              </Step>
            )}

            {csvResult && (
              <div data-testid="csv-result" className="bg-emerald-50 border border-emerald-200 rounded-lg p-5">
                <h3 className="font-semibold text-emerald-900 text-lg mb-2">✓ {t("import.csv_done_title")}</h3>
                <p className="text-sm text-emerald-800 mb-2">
                  {t("import.csv_done_imported", { imported: csvResult.imported })}
                </p>
                {csvResult.errors?.length > 0 && (
                  <details className="text-sm text-amber-900 mt-2">
                    <summary className="cursor-pointer font-medium">
                      ⚠ {t("import.csv_done_errors", { count: csvResult.errors.length })}
                    </summary>
                    <ul className="mt-2 ml-4 list-disc">
                      {csvResult.errors.slice(0, 10).map((e, i) => (
                        <li key={i}>{t("import.csv_error_row", { row: e.row, message: e.message })}</li>
                      ))}
                    </ul>
                  </details>
                )}
                <button onClick={() => nav(`/${lang}/app/properties`)} className="mt-4 px-5 py-2.5 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest rounded-md hover:bg-stone-700">
                  {t("import.go_to_list")}
                </button>
              </div>
            )}
          </div>
        )}

        {/* XML TAB */}
        {tab === "xml" && (
          <div className="space-y-6">
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-5">
              <h2 className="font-semibold text-amber-900 mb-1">{t("import.xml_intro_title")}</h2>
              <p className="text-sm text-amber-800">{t("import.xml_intro_text")}</p>
              <p className="text-xs text-amber-900 mt-2">
                ✨ <strong>Formato Agestanet riconosciuto automaticamente.</strong> Se il tuo XML proviene da Agestanet, i 51 codici tipologia, le classi energetiche e i campi di sistema saranno mappati senza intervento.
              </p>
            </div>

            {/* Sub-mode toggle */}
            <div className="inline-flex border border-stone-300 rounded-md overflow-hidden text-xs uppercase tracking-widest">
              <button
                data-testid="xml-mode-url"
                onClick={() => setXmlMode("url")}
                className={`px-4 py-2 ${xmlMode === "url" ? "bg-stone-900 text-stone-50" : "bg-white text-stone-600 hover:bg-stone-50"}`}
              >
                URL feed
              </button>
              <button
                data-testid="xml-mode-paste"
                onClick={() => setXmlMode("paste")}
                className={`px-4 py-2 border-l border-stone-300 ${xmlMode === "paste" ? "bg-stone-900 text-stone-50" : "bg-white text-stone-600 hover:bg-stone-50"}`}
              >
                Incolla XML
              </button>
            </div>

            {xmlMode === "url" && (
              <div className="space-y-3">
                <label className="block text-xs uppercase tracking-widest text-stone-600">{t("import.xml_url_label")}</label>
                <input
                  data-testid="xml-url-input"
                  value={xmlUrl}
                  onChange={(e) => setXmlUrl(e.target.value)}
                  placeholder={t("import.xml_url_placeholder")}
                  className="w-full px-3 py-2.5 border border-stone-300 rounded-md text-sm focus:outline-none focus:border-stone-900"
                />
                <p className="text-xs text-stone-500">{t("import.xml_url_hint")}</p>
              </div>
            )}

            {xmlMode === "paste" && (
              <div className="space-y-3">
                <label className="block text-xs uppercase tracking-widest text-stone-600">
                  Contenuto XML
                </label>
                <textarea
                  data-testid="xml-content-input"
                  value={xmlContent}
                  onChange={(e) => setXmlContent(e.target.value)}
                  placeholder={"<?xml version='1.0'?>\n<immobili>\n  <immobile>\n    <rif>...</rif>\n    ...\n  </immobile>\n</immobili>"}
                  className="w-full px-3 py-3 border border-stone-300 rounded-md text-xs font-mono h-64 focus:outline-none focus:border-stone-900"
                />
                <p className="text-xs text-stone-500">
                  Apri il file XML in un editor di testo (Blocco note, TextEdit), copia <strong>tutto il contenuto</strong> e incollalo qui sopra. Riconosciamo automaticamente il formato Agestanet.
                </p>
              </div>
            )}

            {xmlError && <p className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">{xmlError}</p>}

            <button
              data-testid="xml-import-btn"
              onClick={importXml}
              disabled={xmlImporting || (xmlMode === "url" ? !xmlUrl : !xmlContent)}
              className="px-6 py-3 bg-emerald-700 text-stone-50 text-xs uppercase tracking-widest font-medium rounded-md hover:bg-emerald-800 disabled:opacity-50"
            >
              {xmlImporting ? t("import.csv_importing") : t("import.xml_import_btn")}
            </button>

            {xmlResult && (
              <div data-testid="xml-result" className="bg-emerald-50 border border-emerald-200 rounded-lg p-5">
                <h3 className="font-semibold text-emerald-900 mb-2">
                  ✓ {t("import.csv_done_title")}
                  {xmlResult.format_detected === "agestanet" && (
                    <span className="ml-2 text-xs uppercase tracking-widest bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded">
                      Agestanet
                    </span>
                  )}
                </h3>
                <p className="text-sm text-emerald-800">
                  {t("import.csv_done_imported", { imported: xmlResult.imported })}
                </p>
                {xmlResult.errors?.length > 0 && (
                  <details className="text-sm text-amber-900 mt-2">
                    <summary className="cursor-pointer font-medium">⚠ {t("import.csv_done_errors", { count: xmlResult.errors.length })}</summary>
                    <ul className="mt-2 ml-4 list-disc">
                      {xmlResult.errors.slice(0, 10).map((e, i) => (
                        <li key={i}>{t("import.csv_error_row", { row: e.row, message: e.message })}</li>
                      ))}
                    </ul>
                  </details>
                )}
                <button onClick={() => nav(`/${lang}/app/properties`)} className="mt-4 px-5 py-2.5 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest rounded-md hover:bg-stone-700">
                  {t("import.go_to_list")}
                </button>
              </div>
            )}
          </div>
        )}
      </section>
    </AgencyShell>
  );
}

function TabBtn({ active, onClick, testid, children }) {
  return (
    <button
      onClick={onClick}
      data-testid={testid}
      className={`px-4 py-2.5 text-xs uppercase tracking-widest font-medium transition border-b-2 -mb-px ${
        active ? "border-stone-900 text-stone-900" : "border-transparent text-stone-500 hover:text-stone-900"
      }`}
    >
      {children}
    </button>
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

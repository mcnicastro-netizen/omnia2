/* OMNIA — HAL Legal page
 *
 * Standalone full-page legal assistant. Available to all authenticated users
 * (agents + B2C). Includes:
 *   - Disclaimer modal first visit (L.247/2012)
 *   - Tab: Chat (with sources panel + confidence indicator)
 *   - Tab: Analizza PDF (dropzone + question + structured analysis)
 */
import React, { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api } from "../../shared/lib/api";

const SUB_AGENT_BADGE = {
  general: "bg-stone-100 text-stone-700",
  proposta: "bg-amber-100 text-amber-900",
  locazioni: "bg-emerald-100 text-emerald-900",
  catasto: "bg-sky-100 text-sky-900",
  urbanistica: "bg-violet-100 text-violet-900",
  pdf_analysis: "bg-rose-100 text-rose-900",
};

const ACCEPT_KEY = "omnia_legal_disclaimer_v1";

function DisclaimerModal({ onAccept }) {
  const { t } = useTranslation();
  const [checked, setChecked] = useState(false);
  return (
    <div
      data-testid="legal-disclaimer-modal"
      className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
    >
      <div className="bg-white rounded-lg shadow-2xl max-w-lg w-full p-6">
        <h2
          className="text-xl font-light mb-3 text-[#0B1E3F]"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        >
          ⚖️ {t("legal.disclaimer_title")}
        </h2>
        <p className="text-sm text-stone-700 leading-relaxed mb-5">
          {t("legal.disclaimer_body")}
        </p>
        <label className="flex items-start gap-3 text-sm text-stone-800 cursor-pointer mb-5">
          <input
            data-testid="legal-disclaimer-checkbox"
            type="checkbox"
            checked={checked}
            onChange={(e) => setChecked(e.target.checked)}
            className="mt-1"
          />
          <span>{t("legal.accept_terms")}</span>
        </label>
        <button
          data-testid="legal-disclaimer-accept"
          disabled={!checked}
          onClick={onAccept}
          className="w-full bg-[#0B1E3F] text-white text-xs uppercase tracking-widest py-3 rounded hover:bg-[#C19A6B] disabled:opacity-40"
        >
          {t("legal.start")}
        </button>
      </div>
    </div>
  );
}

function ConfidencePill({ confidence, lowConfidence }) {
  const pct = Math.round((confidence || 0) * 100);
  const color = lowConfidence
    ? "bg-amber-100 text-amber-900"
    : "bg-emerald-100 text-emerald-900";
  return (
    <span
      data-testid="legal-confidence"
      className={`inline-flex items-center gap-1 text-[10px] uppercase tracking-widest px-2 py-1 rounded ${color}`}
    >
      ◈ {pct}%
    </span>
  );
}

function SourcesPanel({ citations }) {
  const { t } = useTranslation();
  if (!citations || citations.length === 0) {
    return (
      <p data-testid="legal-no-sources" className="text-xs text-stone-500 italic">
        {t("legal.no_sources")}
      </p>
    );
  }
  return (
    <ol className="space-y-3" data-testid="legal-sources-list">
      {citations.map((c, i) => (
        <li key={i} className="text-xs">
          <a
            href={c.url}
            target="_blank"
            rel="noopener noreferrer nofollow"
            className="text-[#0B1E3F] hover:text-[#C19A6B] font-medium underline underline-offset-2"
          >
            [{i + 1}] {c.title}
          </a>
          <p className="text-stone-600 mt-1 line-clamp-3">{c.snippet}</p>
        </li>
      ))}
    </ol>
  );
}

function ChatTab() {
  const { t } = useTranslation();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [sid, setSid] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, busy]);

  const send = async (e) => {
    e?.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    setBusy(true);
    setMessages((m) => [...m, { role: "user", content: text }]);
    setInput("");
    try {
      const r = await api.post("/app/legal/chat",
        { session_id: sid, message: text },
        { timeout: 90000 }
      );
      if (!sid) setSid(r.data.session_id);
      setMessages((m) => [...m, {
        role: "assistant",
        content: r.data.reply,
        sub_agent: r.data.sub_agent,
        citations: r.data.citations,
        confidence: r.data.confidence,
        low_confidence: r.data.low_confidence,
      }]);
    } catch (err) {
      const d = err?.response?.data?.detail;
      const msg = d === "rate_limit_exceeded"
        ? t("legal.err_rate_limit")
        : t("legal.err_generic");
      setMessages((m) => [...m, { role: "assistant", content: msg, error: true }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-280px)] min-h-[480px]">
      {/* Conversation column */}
      <div className="lg:col-span-2 bg-white border border-stone-200 rounded-lg flex flex-col">
        <div ref={scrollRef} data-testid="legal-messages" className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-stone-500 text-sm py-12">
              <p className="mb-3">{t("legal.page_subtitle")}</p>
              <ul className="text-left text-xs space-y-1.5 max-w-md mx-auto">
                <li>· &ldquo;Differenza tra caparra confirmatoria e penitenziale&rdquo;</li>
                <li>· &ldquo;Posso recedere da una proposta d&rsquo;acquisto firmata?&rdquo;</li>
                <li>· &ldquo;Cedolare secca 21% o 10%: quale conviene?&rdquo;</li>
                <li>· &ldquo;Cos&rsquo;è la conformità urbanistica?&rdquo;</li>
              </ul>
            </div>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              data-testid={`legal-msg-${m.role}`}
              className={`text-sm leading-relaxed ${
                m.role === "user"
                  ? "bg-stone-100 ml-6 p-4 rounded-lg whitespace-pre-wrap"
                  : "bg-[#FAF7F2] mr-6 p-4 rounded-lg border border-stone-200"
              }`}
            >
              {m.role === "assistant" && m.sub_agent && (
                <div className="mb-2 flex items-center gap-2 flex-wrap">
                  <span
                    className={`text-[10px] uppercase tracking-widest px-2 py-1 rounded ${
                      SUB_AGENT_BADGE[m.sub_agent] || "bg-stone-100 text-stone-700"
                    }`}
                  >
                    {t(`legal.agent_${m.sub_agent}`)}
                  </span>
                  {typeof m.confidence === "number" && (
                    <ConfidencePill confidence={m.confidence} lowConfidence={m.low_confidence} />
                  )}
                </div>
              )}
              <div className="whitespace-pre-wrap">{m.content}</div>
            </div>
          ))}
          {busy && (
            <div data-testid="legal-thinking" className="bg-[#FAF7F2] mr-6 p-4 rounded-lg border border-stone-200">
              <span className="italic text-stone-400 text-sm">{t("legal.thinking")}</span>
            </div>
          )}
        </div>
        <form onSubmit={send} className="border-t border-stone-200 p-4 flex gap-3">
          <input
            data-testid="legal-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t("legal.input_placeholder")}
            maxLength={2000}
            disabled={busy}
            className="flex-1 px-4 py-2 text-sm border border-stone-300 rounded focus:outline-none focus:border-[#0B1E3F]"
          />
          <button
            data-testid="legal-send"
            type="submit"
            disabled={busy || !input.trim()}
            className="px-5 py-2 bg-[#0B1E3F] text-white text-xs uppercase tracking-widest rounded hover:bg-[#C19A6B] disabled:opacity-40"
          >
            {t("legal.send")}
          </button>
        </form>
      </div>

      {/* Sources column */}
      <aside className="bg-white border border-stone-200 rounded-lg p-5 overflow-y-auto">
        <h3 className="text-[10px] uppercase tracking-widest text-stone-500 mb-3">
          {t("legal.sources")}
        </h3>
        {(() => {
          const last = [...messages].reverse().find((m) => m.role === "assistant");
          if (!last) {
            return (
              <p className="text-xs text-stone-400 italic">
                Le fonti normative consultate appariranno qui dopo la prima risposta.
              </p>
            );
          }
          return (
            <>
              {last.low_confidence && (
                <div
                  data-testid="legal-low-confidence-cta"
                  className="bg-amber-50 border border-amber-200 rounded p-3 mb-4 text-xs text-amber-900"
                >
                  <p className="font-medium mb-1">⚠️ {t("legal.low_confidence_warning")}</p>
                  <a
                    href="https://www.notariato.it/it/utilita/trova-notaio/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block mt-1 text-amber-900 underline font-semibold"
                  >
                    {t("legal.cta_notary")} →
                  </a>
                </div>
              )}
              <SourcesPanel citations={last.citations} />
            </>
          );
        })()}
      </aside>
    </div>
  );
}

function PdfTab() {
  const { t } = useTranslation();
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState(
    "Analizza questo documento immobiliare e segnala criticità, clausole atipiche e verifiche da fare prima della firma."
  );
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const onPick = (e) => {
    const f = e.target.files?.[0];
    if (f) setFile(f);
  };
  const onDrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) setFile(f);
  };

  const analyze = async () => {
    if (!file) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("question", question);
      const r = await api.post("/app/legal/analyze-pdf", fd, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000,
      });
      setResult(r.data);
    } catch (err) {
      const d = err?.response?.data?.detail;
      const m = {
        file_too_large: t("legal.pdf_too_large"),
        invalid_pdf: t("legal.pdf_invalid"),
        encrypted_pdf: t("legal.pdf_encrypted"),
        no_text_extracted: t("legal.pdf_scanned"),
        only_pdf_allowed: t("legal.pdf_invalid"),
        rate_limit_exceeded: t("legal.err_rate_limit"),
      }[d] || t("legal.err_generic");
      setError(m);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-white border border-stone-200 rounded-lg p-6 space-y-5">
        <div
          data-testid="legal-pdf-dropzone"
          onDrop={onDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-stone-300 rounded-lg p-10 text-center cursor-pointer hover:border-[#0B1E3F] hover:bg-stone-50 transition"
        >
          <input
            ref={fileInputRef}
            data-testid="legal-pdf-input"
            type="file"
            accept="application/pdf"
            onChange={onPick}
            className="hidden"
          />
          <p className="text-sm text-stone-600">
            {file ? `📎 ${file.name} (${Math.round(file.size / 1024)} KB)` : t("legal.pdf_dropzone")}
          </p>
        </div>

        <div>
          <label className="block text-[10px] uppercase tracking-widest text-stone-500 mb-2">
            {t("legal.pdf_question_label")}
          </label>
          <textarea
            data-testid="legal-pdf-question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={t("legal.pdf_question_placeholder")}
            rows={3}
            className="w-full px-3 py-2 text-sm border border-stone-300 rounded focus:outline-none focus:border-[#0B1E3F]"
          />
        </div>

        <button
          data-testid="legal-pdf-analyze"
          onClick={analyze}
          disabled={!file || busy}
          className="w-full px-5 py-3 bg-[#0B1E3F] text-white text-xs uppercase tracking-widest rounded hover:bg-[#C19A6B] disabled:opacity-40"
        >
          {busy ? t("legal.pdf_uploading") : t("legal.pdf_analyze")}
        </button>

        {error && (
          <p data-testid="legal-pdf-error" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-3">
            {error}
          </p>
        )}
      </div>

      <div className="bg-[#FAF7F2] border border-stone-200 rounded-lg p-6">
        {busy && (
          <p data-testid="legal-pdf-analyzing" className="italic text-stone-500 text-sm">
            {t("legal.thinking")}
          </p>
        )}
        {result && (
          <div data-testid="legal-pdf-result" className="space-y-4">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`text-[10px] uppercase tracking-widest px-2 py-1 rounded ${SUB_AGENT_BADGE.pdf_analysis}`}>
                {t("legal.agent_pdf_analysis")}
              </span>
              <ConfidencePill confidence={result.confidence} lowConfidence={result.low_confidence} />
              <span className="text-[10px] uppercase tracking-widest text-stone-500">
                {result.page_count} pp · {result.extracted_chars} car.
              </span>
            </div>
            <div className="text-sm leading-relaxed whitespace-pre-wrap text-stone-900">
              {result.reply}
            </div>
            <div className="border-t border-stone-200 pt-4">
              <h3 className="text-[10px] uppercase tracking-widest text-stone-500 mb-3">
                {t("legal.sources")}
              </h3>
              <SourcesPanel citations={result.citations} />
            </div>
            {result.low_confidence && (
              <div
                data-testid="legal-pdf-low-confidence"
                className="bg-amber-50 border border-amber-200 rounded p-3 text-xs text-amber-900"
              >
                <p className="font-medium mb-1">⚠️ {t("legal.low_confidence_warning")}</p>
                <a
                  href="https://www.notariato.it/it/utilita/trova-notaio/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block mt-1 underline font-semibold"
                >
                  {t("legal.cta_notary")} →
                </a>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function LegalApp() {
  const { t } = useTranslation();
  const [accepted, setAccepted] = useState(
    typeof window !== "undefined" && localStorage.getItem(ACCEPT_KEY) === "1"
  );
  const [tab, setTab] = useState("chat");

  const accept = () => {
    localStorage.setItem(ACCEPT_KEY, "1");
    setAccepted(true);
  };

  return (
    <div className="min-h-screen bg-[#F5F2EC]" data-testid="legal-app">
      {!accepted && <DisclaimerModal onAccept={accept} />}

      <header className="bg-white border-b border-stone-200">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1
              className="text-3xl font-light text-[#0B1E3F]"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              ⚖️ HAL <span className="text-[#C19A6B]">Legal</span>
            </h1>
            <p className="text-xs uppercase tracking-widest text-stone-500 mt-1">
              {t("legal.page_subtitle")}
            </p>
          </div>
          <Link
            data-testid="legal-nav-back"
            to={`/${document.documentElement.lang || "it"}/app/dashboard`}
            className="text-[10px] uppercase tracking-widest text-stone-600 hover:text-[#0B1E3F]"
          >
            ← {t("legal.nav_back")}
          </Link>
        </div>
        <nav className="max-w-7xl mx-auto px-6 flex gap-1 border-t border-stone-100">
          <button
            data-testid="legal-tab-chat"
            onClick={() => setTab("chat")}
            className={`px-5 py-3 text-xs uppercase tracking-widest border-b-2 transition ${
              tab === "chat"
                ? "border-[#0B1E3F] text-[#0B1E3F]"
                : "border-transparent text-stone-500 hover:text-[#0B1E3F]"
            }`}
          >
            {t("legal.tab_chat")}
          </button>
          <button
            data-testid="legal-tab-pdf"
            onClick={() => setTab("pdf")}
            className={`px-5 py-3 text-xs uppercase tracking-widest border-b-2 transition ${
              tab === "pdf"
                ? "border-[#0B1E3F] text-[#0B1E3F]"
                : "border-transparent text-stone-500 hover:text-[#0B1E3F]"
            }`}
          >
            {t("legal.tab_pdf")}
          </button>
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        {tab === "chat" ? <ChatTab /> : <PdfTab />}
      </main>

      <footer className="max-w-7xl mx-auto px-6 py-4 text-[10px] text-stone-500 italic">
        {t("legal.disclaimer_body")}
      </footer>
    </div>
  );
}

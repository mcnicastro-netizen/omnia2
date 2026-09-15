import React, { useEffect, useRef, useState } from "react";
import { api } from "../../../shared/lib/api";
import AgencyShell from "../components/AgencyShell";
import Brand from "../../../shared/components/Brand";

/**
 * HAL Knowledge — risposte su come usare OMNIA (guida operativa).
 * Tono destinato ad agenti immobiliari, non a tecnici.
 */
const SAMPLE_QUESTIONS = [
  "Come entro nel network MLS?",
  "Quali immobili si vedono in MLS?",
  "Come pubblico un immobile sui portali?",
  "Come inserisco un nuovo immobile?",
  "Come gestisco i partner MLS?",
];

export default function HalKnowledgePage() {
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [answer, setAnswer] = useState(null);
  const [history, setHistory] = useState([]);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  const loadStatus = async () => {
    try {
      const r = await api.get("/app/hal/knowledge/status");
      setStatus(r.data);
    } catch (e) {
      // silently ignore
    }
  };

  const loadHistory = async () => {
    try {
      const r = await api.get("/app/hal/knowledge/history?limit=15");
      setHistory(r.data.items || []);
    } catch (e) {
      // silently ignore
    }
  };

  useEffect(() => {
    loadStatus();
    loadHistory();
    inputRef.current?.focus();
  }, []);

  const submit = async (e, override) => {
    if (e) e.preventDefault();
    const q = (override ?? question).trim();
    if (!q || busy) return;
    setBusy(true);
    setError(null);
    setAnswer(null);
    try {
      const r = await api.post("/app/hal/knowledge/ask", { question: q });
      setAnswer(r.data);
      await loadHistory();
    } catch (e) {
      setError("Non sono riuscito a rispondere adesso. Riprova tra un momento.");
    } finally {
      setBusy(false);
    }
  };

  const askSample = (q) => {
    setQuestion(q);
    submit(null, q);
  };

  const restoreFromHistory = (h) => {
    setQuestion(h.question);
    setAnswer({
      answer: h.answer,
      sources: h.sources || [],
      confidence: h.confidence,
      status: h.status,
    });
    inputRef.current?.focus();
  };

  const guideReady = status && (status.manual_hal_indexed ?? 0) > 0;

  return (
    <AgencyShell current="hal-knowledge">
      <section data-testid="hal-knowledge-page" className="space-y-8">
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-2">
            <Brand>HAL · Guida OMNIA</Brand>
          </p>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <h1
              className="text-3xl md:text-4xl tracking-tight"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              Guida OMNIA
            </h1>
            {status && (
              <div
                data-testid="hal-status-badge"
                className="text-[10px] uppercase tracking-widest text-stone-600 bg-stone-100 px-3 py-1.5 rounded"
              >
                {guideReady ? "Guida operativa attiva" : "Guida in aggiornamento"}
              </div>
            )}
          </div>
          <p className="text-sm text-stone-600 mt-2 max-w-3xl">
            Qui HAL ti spiega <strong>come usare OMNIA</strong> (menu, passi, MLS, immobili…).
            Per domande sul tuo lavoro quotidiano — immobili, clienti, lead — usa il pulsante HAL
            in basso a destra nelle altre pagine.
          </p>
        </div>

        {status && (status.manual_hal_indexed ?? 0) === 0 && (
          <div
            data-testid="hal-manual-indexing-banner"
            className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
          >
            <strong>Guida in aggiornamento</strong> — tra poco HAL avrà tutte le voci del manuale operativo.
            Puoi già fare domande su Immobili, MLS e le funzioni principali.
          </div>
        )}

        <form onSubmit={submit} className="bg-white border border-stone-200 rounded-lg p-4 space-y-3">
          <label className="text-xs uppercase tracking-widest text-stone-500 block">La tua domanda</label>
          <textarea
            ref={inputRef}
            data-testid="hal-question-input"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Es. Come entro nel network MLS? Come pubblico un immobile?"
            maxLength={1000}
            rows={3}
            className="w-full border border-stone-300 rounded px-3 py-2 text-sm resize-y focus:outline-none focus:ring-2 focus:ring-[#1F6B5C]/30 focus:border-[#1F6B5C]"
            disabled={busy}
          />
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-[11px] text-stone-500">{question.length}/1000</p>
            <button
              type="submit"
              data-testid="hal-ask-submit"
              disabled={busy || !question.trim()}
              className="text-xs uppercase tracking-widest bg-[#1F6B5C] text-white px-5 py-2 rounded hover:bg-[#0B1E3F] transition disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {busy ? "Attendi…" : "Chiedi sulla guida"}
            </button>
          </div>
        </form>

        {!answer && (
          <div>
            <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-2">Prova con una di queste</h2>
            <div className="flex flex-wrap gap-2">
              {SAMPLE_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  data-testid={`hal-sample-${i}`}
                  onClick={() => askSample(q)}
                  disabled={busy}
                  className="text-xs text-stone-700 border border-stone-300 px-3 py-1.5 rounded-full hover:bg-stone-100 transition disabled:opacity-40"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div data-testid="hal-error" className="text-sm text-red-700 bg-red-50 border border-red-300 rounded p-3">
            {String(error)}
          </div>
        )}

        {answer && (
          <div data-testid="hal-answer" className="bg-white border border-stone-200 rounded-lg overflow-hidden">
            <div className="px-5 py-3 border-b border-stone-200 flex items-center justify-between bg-stone-50">
              <div className="flex items-center gap-2">
                <span className="text-lg" aria-hidden>✦</span>
                <span className="text-xs uppercase tracking-widest text-stone-500">Risposta HAL</span>
              </div>
              <ConfidenceBadge status={answer.status} />
            </div>
            <div className="p-5">
              {answer.status === "insufficient_context" ? (
                <div className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded p-3">
                  <strong>Non ho trovato abbastanza indicazioni.</strong>
                  <div className="mt-1">{answer.answer}</div>
                </div>
              ) : (
                <div
                  className="text-sm text-stone-800 leading-relaxed whitespace-pre-wrap"
                  dangerouslySetInnerHTML={{ __html: renderMarkdownLite(answer.answer || "") }}
                />
              )}
            </div>
          </div>
        )}

        {history.length > 0 && (
          <div>
            <h2 className="text-lg mb-3" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              Domande recenti
            </h2>
            <div className="bg-white border border-stone-200 rounded-lg divide-y divide-stone-200" data-testid="hal-history">
              {history.slice(0, 8).map((h) => (
                <button
                  key={h.id}
                  onClick={() => restoreFromHistory(h)}
                  className="w-full text-left px-4 py-3 hover:bg-stone-50 transition"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-sm text-stone-800 truncate flex-1">{h.question}</span>
                    <ConfidenceBadge status={h.status} small />
                  </div>
                  <p className="text-[10px] text-stone-500 mt-1">
                    {new Date(h.created_at).toLocaleString("it-IT")}
                  </p>
                </button>
              ))}
            </div>
          </div>
        )}
      </section>
    </AgencyShell>
  );
}

function ConfidenceBadge({ status, small = false }) {
  const styles = {
    high: "bg-emerald-100 text-emerald-800",
    medium: "bg-amber-100 text-amber-800",
    insufficient_context: "bg-red-100 text-red-800",
  };
  const labels = {
    high: "Chiara",
    medium: "Utile",
    insufficient_context: "Incompleta",
  };
  const tips = {
    high: "Risposta chiara: HAL ha trovato indicazioni solide nella guida (confidence alta).",
    medium: "Risposta utile: indicazioni trovate, ma potresti riformulare per più precisione.",
    insufficient_context: "Risposta incompleta: nella guida non c’è abbastanza contesto. Prova a essere più specifico.",
  };
  const size = small ? "text-[9px] px-1.5 py-0.5" : "text-[10px] px-2 py-1";
  const tip = tips[status] || "Livello di affidabilità della risposta HAL rispetto alla guida OMNIA.";
  return (
    <span
      title={tip}
      aria-label={tip}
      data-testid="hal-confidence-badge"
      data-confidence={status || "medium"}
      className={`group relative inline-flex items-center ${styles[status] || styles.medium} ${size} uppercase tracking-widest rounded whitespace-nowrap cursor-help`}
    >
      {labels[status] || "Risposta"}
      <span
        role="tooltip"
        className="pointer-events-none absolute right-0 top-full z-20 mt-1 hidden w-56 rounded bg-stone-900 px-2 py-1.5 text-[10px] normal-case tracking-normal font-normal leading-snug text-white shadow-lg group-hover:block group-focus-visible:block"
      >
        {tip}
      </span>
    </span>
  );
}

/** Very small markdown → HTML converter (bold, code, line breaks). No external dep. */
function renderMarkdownLite(md) {
  return String(md)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, '<span class="font-medium">$1</span>')
    .replace(/\[FONTE (\d+)\]/g, "")
    .replace(/\n\n+/g, "</p><p>")
    .replace(/\n/g, "<br/>")
    .replace(/^/, "<p>").concat("</p>");
}

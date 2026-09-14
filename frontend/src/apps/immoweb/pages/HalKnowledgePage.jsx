import React, { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import AgencyShell from "../components/AgencyShell";
import Brand from "../../../shared/components/Brand";

/**
 * M5.S2 · HAL Knowledge (RAG on OMNIA docs).
 *
 * Third HAL bot (D-040 · 3 physical buttons, no LLM router):
 *   - AL for Agents (M5.S1)
 *   - HAL Legal (M5.S3)
 *   - HAL Knowledge (M5.S2, this page)
 *
 * Answers questions about how the OMNIA platform works using RAG on the
 * documentation corpus (PRD, ROADMAP, DECISIONS, AUDIT_M2, etc.).
 */
const SAMPLE_QUESTIONS = [
  "Come pubblico un immobile su tutti i portali?",
  "Cos'è il Domain Vault e come funziona?",
  "Come faccio a configurare un canale social?",
  "Cosa può fare HAL Legal? Quali fonti usa?",
  "Cosa cambia tra Track A e Track B (Doppio Binario)?",
];

export default function HalKnowledgePage() {
  const { i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);

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
      const detail = e?.response?.data?.detail || "ask_error";
      setError(typeof detail === "string" ? detail : JSON.stringify(detail));
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

  return (
    <AgencyShell current="hal-knowledge">
      <section data-testid="hal-knowledge-page" className="space-y-8">
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-2">
            <Brand>HAL · Knowledge Base</Brand>
          </p>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <h1
              className="text-3xl md:text-4xl tracking-tight"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              Chiedi ad HAL
            </h1>
            {status && (
              <div
                data-testid="hal-status-badge"
                className="text-[10px] uppercase tracking-widest text-stone-600 bg-stone-100 px-3 py-1.5 rounded"
              >
                📚 {status.chunks_indexed} chunk · {status.index?.vocab_size || 0} termini
                <span className="mx-2 text-stone-300">|</span>
                🤖 {status.model?.name}
              </div>
            )}
          </div>
          <p className="text-sm text-stone-600 mt-2 max-w-3xl">
            HAL Knowledge risponde su come funziona OMNIA usando la documentazione ufficiale (PRD, roadmap, decisioni, audit). Ogni risposta cita le fonti utilizzate — se HAL non ha abbastanza contesto, te lo dice invece di inventare.
          </p>
        </div>

        {/* Corpus manuale in indicizzazione: mostra il banner finché
            non ci sono chunk YAML del manuale nell'indice */}
        {status && (status.manual_hal_indexed ?? 0) === 0 && (
          <div
            data-testid="hal-manual-indexing-banner"
            className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
          >
            📖 <strong>Corpus manuale in indicizzazione</strong> — Le 56 voci del Manuale Operativo (Cap. 1-5) saranno disponibili a breve.
            Nel frattempo HAL Knowledge risponde già su PRD, ROADMAP, DECISIONS e altri documenti tecnici.
          </div>
        )}

        {/* Question form */}
        <form onSubmit={submit} className="bg-white border border-stone-200 rounded-lg p-4 space-y-3">
          <label className="text-xs uppercase tracking-widest text-stone-500 block">La tua domanda</label>
          <textarea
            ref={inputRef}
            data-testid="hal-question-input"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Es. Come si attivano i portali di pubblicazione? Come funziona il Domain Vault?"
            maxLength={1000}
            rows={3}
            className="w-full border border-stone-300 rounded px-3 py-2 text-sm resize-y focus:outline-none focus:ring-2 focus:ring-[#1F6B5C]/30 focus:border-[#1F6B5C]"
            disabled={busy}
          />
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-[11px] text-stone-500">{question.length}/1000 · <em>enter con shift = a capo · enter = invia</em></p>
            <button
              type="submit"
              data-testid="hal-ask-submit"
              disabled={busy || !question.trim()}
              className="text-xs uppercase tracking-widest bg-[#1F6B5C] text-white px-5 py-2 rounded hover:bg-[#0B1E3F] transition disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {busy ? "Attendi…" : "Chiedi ad HAL"}
            </button>
          </div>
        </form>

        {/* Sample questions */}
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
            Errore: {String(error)}
          </div>
        )}

        {/* Answer */}
        {answer && (
          <div data-testid="hal-answer" className="bg-white border border-stone-200 rounded-lg overflow-hidden">
            <div className="px-5 py-3 border-b border-stone-200 flex items-center justify-between bg-stone-50">
              <div className="flex items-center gap-2">
                <span className="text-lg">🤖</span>
                <span className="text-xs uppercase tracking-widest text-stone-500">Risposta HAL</span>
              </div>
              <ConfidenceBadge status={answer.status} confidence={answer.confidence} />
            </div>
            <div className="p-5">
              {answer.status === "insufficient_context" ? (
                <div className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded p-3">
                  <strong>⚠️ Contesto insufficiente.</strong>
                  <div className="mt-1">{answer.answer}</div>
                  <div className="text-[11px] text-amber-700 mt-2">
                    Similarity: {(answer.confidence * 100).toFixed(1)}% — sotto la soglia minima del 8%.
                  </div>
                </div>
              ) : (
                <>
                  <div
                    className="text-sm text-stone-800 leading-relaxed whitespace-pre-wrap"
                    style={{ fontFamily: "-apple-system, BlinkMacSystemFont, sans-serif" }}
                    dangerouslySetInnerHTML={{ __html: renderMarkdownLite(answer.answer || "") }}
                  />
                  {answer.sources && answer.sources.length > 0 && (
                    <div className="mt-5 pt-4 border-t border-stone-200">
                      <h3 className="text-[10px] uppercase tracking-widest text-stone-500 mb-2">Fonti citate</h3>
                      <div className="space-y-1.5" data-testid="hal-sources">
                        {answer.sources.map((s, i) => (
                          <div key={i} className="text-xs text-stone-600 flex items-start gap-2">
                            <span className="text-emerald-700 font-mono">[{i + 1}]</span>
                            <div className="flex-1 min-w-0">
                              <div className="font-mono text-stone-800 truncate" title={`${s.file} · ${s.section}`}>
                                {s.file}
                              </div>
                              {s.section && (
                                <div className="text-[10px] text-stone-500 truncate">↳ {s.section}</div>
                              )}
                            </div>
                            <span className="text-[10px] text-stone-400 font-mono">{(s.similarity * 100).toFixed(1)}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}

        {/* History */}
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
                    <ConfidenceBadge status={h.status} confidence={h.confidence} small />
                  </div>
                  <p className="text-[10px] text-stone-500 mt-1">
                    {new Date(h.created_at).toLocaleString("it-IT")}
                    {h.sources?.length > 0 && ` · ${h.sources.length} fonti`}
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

function ConfidenceBadge({ status, confidence, small = false }) {
  const styles = {
    high: "bg-emerald-100 text-emerald-800",
    medium: "bg-amber-100 text-amber-800",
    insufficient_context: "bg-red-100 text-red-800",
  };
  const labels = {
    high: "Alta confidence",
    medium: "Media confidence",
    insufficient_context: "Insufficiente",
  };
  const size = small ? "text-[9px] px-1.5 py-0.5" : "text-[10px] px-2 py-1";
  return (
    <span className={`${styles[status] || styles.medium} ${size} uppercase tracking-widest rounded whitespace-nowrap`}>
      {labels[status] || status} · {((confidence || 0) * 100).toFixed(0)}%
    </span>
  );
}

/** Very small markdown → HTML converter (bold, code, line breaks). No external dep. */
function renderMarkdownLite(md) {
  return String(md)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, '<code class="text-[13px] bg-stone-100 px-1 py-0.5 rounded">$1</code>')
    .replace(/\[FONTE (\d+)\]/g, '<sup class="text-emerald-700 font-mono text-[10px]">[$1]</sup>')
    .replace(/\n\n+/g, "</p><p>")
    .replace(/\n/g, "<br/>")
    .replace(/^/, "<p>").concat("</p>");
}

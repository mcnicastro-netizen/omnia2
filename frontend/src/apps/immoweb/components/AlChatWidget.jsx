/* OMNIA — Al Chat Widget (M5.S1 + Streaming)
 * Floating Action Button bottom-right. Espande pannello chat.
 * Streaming SSE token-by-token via fetch + ReadableStream.
 */
import React, { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { API_BASE } from "../../../shared/lib/api";

export default function AlChatWidget() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [sid, setSid] = useState(null);
  const scrollRef = useRef(null);
  const abortRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, busy]);

  // Cleanup on unmount
  useEffect(() => () => abortRef.current?.abort(), []);

  const updateLast = (patch) => {
    setMessages((m) => {
      const out = [...m];
      const last = out[out.length - 1];
      if (last && last.role === "assistant") out[out.length - 1] = { ...last, ...patch };
      return out;
    });
  };

  const appendToLast = (chunk) => {
    setMessages((m) => {
      const out = [...m];
      const last = out[out.length - 1];
      if (last && last.role === "assistant") {
        out[out.length - 1] = { ...last, content: (last.content || "") + chunk };
      }
      return out;
    });
  };

  const send = async (e) => {
    e?.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    setBusy(true);
    setMessages((m) => [
      ...m,
      { role: "user", content: text },
      { role: "assistant", content: "", tool: null, thinking: false },
    ]);
    setInput("");

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      const resp = await fetch(`${API_BASE}/app/al/chat/stream`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "Accept-Language": (typeof navigator !== "undefined" ? navigator.language : "it") || "it",
        },
        body: JSON.stringify({ session_id: sid, message: text }),
        signal: ctrl.signal,
      });

      if (!resp.ok) {
        let detail = null;
        try { detail = (await resp.json())?.detail; } catch { /* noop */ }
        const msg =
          detail === "rate_limit_exceeded" ? t("al.err_rate_limit")
            : (detail === "llm_budget_exceeded" || detail === "llm_unavailable") ? t("al.err_budget")
            : t("al.err_generic");
        updateLast({ content: msg });
        return;
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        // Parse SSE frames (separated by blank line)
        const frames = buffer.split("\n\n");
        buffer = frames.pop() || ""; // last (possibly partial) frame kept in buffer
        for (const frame of frames) {
          const line = frame.split("\n").find((l) => l.startsWith("data:"));
          if (!line) continue;
          let evt;
          try { evt = JSON.parse(line.slice(5).trim()); } catch { continue; }

          switch (evt.type) {
            case "session":
              if (!sid) setSid(evt.session_id);
              break;
            case "thinking":
              updateLast({ thinking: true });
              break;
            case "tool":
              updateLast({ tool: evt.name, thinking: false });
              break;
            case "token":
              if (evt.content) appendToLast(evt.content);
              break;
            case "done":
              updateLast({ thinking: false });
              break;
            case "error": {
              const m =
                evt.detail === "llm_budget_exceeded" || evt.detail === "llm_unavailable"
                  ? t("al.err_budget")
                  : t("al.err_generic");
              updateLast({ content: m, thinking: false });
              break;
            }
            default:
              break;
          }
        }
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        updateLast({ content: t("al.err_generic"), thinking: false });
      }
    } finally {
      setBusy(false);
      abortRef.current = null;
    }
  };

  const stop = () => {
    abortRef.current?.abort();
  };

  const newSession = () => {
    abortRef.current?.abort();
    setSid(null);
    setMessages([]);
    setInput("");
  };

  if (!open) {
    return (
      <button
        data-testid="al-fab"
        onClick={() => setOpen(true)}
        className="fixed bottom-24 right-6 z-50 w-14 h-14 bg-[#0B1E3F] text-white rounded-full shadow-xl hover:bg-[#C19A6B] transition flex items-center justify-center text-xl font-light"
        style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        title={t("al.open_chat")}
      >
        HAL
      </button>
    );
  }

  return (
    <div
      data-testid="al-widget"
      className="fixed bottom-24 right-6 z-50 w-[360px] max-w-[calc(100vw-32px)] h-[520px] max-h-[calc(100vh-140px)] bg-white border border-stone-200 rounded-lg shadow-2xl flex flex-col"
    >
      <header className="px-4 py-3 border-b border-stone-200 flex items-center justify-between bg-[#0B1E3F] text-white rounded-t-lg">
        <div>
          <h3 className="font-light text-base" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>HAL</h3>
          <p className="text-[10px] uppercase tracking-widest text-stone-300">{t("al.subtitle")}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            data-testid="al-new-session"
            onClick={newSession}
            className="text-[10px] uppercase tracking-widest opacity-70 hover:opacity-100"
            title={t("al.new")}
          >
            ↻
          </button>
          <button
            data-testid="al-close"
            onClick={() => setOpen(false)}
            className="text-lg leading-none opacity-70 hover:opacity-100"
            title={t("al.close")}
          >
            ×
          </button>
        </div>
      </header>

      <div ref={scrollRef} data-testid="al-messages" className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div className="text-center text-stone-500 text-xs py-8">
            <p className="mb-3">{t("al.welcome")}</p>
            <ul className="text-left space-y-1.5 text-[11px] text-stone-600 max-w-[260px] mx-auto">
              <li>· &ldquo;{t("al.suggest_1")}&rdquo;</li>
              <li>· &ldquo;{t("al.suggest_2")}&rdquo;</li>
              <li>· &ldquo;{t("al.suggest_3")}&rdquo;</li>
              <li>· &ldquo;{t("al.suggest_4")}&rdquo;</li>
            </ul>
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            data-testid={`al-msg-${m.role}`}
            className={`text-sm leading-relaxed whitespace-pre-wrap ${
              m.role === "user"
                ? "bg-stone-100 ml-6 p-3 rounded-lg"
                : "bg-[#FAF7F2] mr-6 p-3 rounded-lg border border-stone-200"
            }`}
          >
            {m.content || (m.thinking ? <span className="italic text-stone-400">{t("al.thinking")}</span> : "")}
            {busy && m.role === "assistant" && i === messages.length - 1 && m.content && (
              <span className="inline-block w-1.5 h-3.5 bg-[#0B1E3F] align-middle ml-0.5 animate-pulse" />
            )}
            {m.tool && (
              <span className="block mt-1.5 text-[10px] uppercase tracking-widest text-[#C19A6B]">
                via {m.tool}
              </span>
            )}
          </div>
        ))}
      </div>

      <form onSubmit={send} className="border-t border-stone-200 p-3 flex gap-2">
        <input
          data-testid="al-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t("al.placeholder")}
          maxLength={2000}
          className="flex-1 px-3 py-2 text-sm border border-stone-300 rounded focus:outline-none focus:border-[#0B1E3F]"
          disabled={busy}
        />
        {busy ? (
          <button
            type="button"
            data-testid="al-stop"
            onClick={stop}
            className="px-4 py-2 bg-stone-700 text-white text-xs uppercase tracking-widest rounded hover:bg-stone-900"
          >
            {t("al.stop")}
          </button>
        ) : (
          <button
            type="submit"
            data-testid="al-send"
            disabled={!input.trim()}
            className="px-4 py-2 bg-[#0B1E3F] text-white text-xs uppercase tracking-widest rounded hover:bg-[#C19A6B] disabled:opacity-50"
          >
            {t("al.send")}
          </button>
        )}
      </form>
    </div>
  );
}

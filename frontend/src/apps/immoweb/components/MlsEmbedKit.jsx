import React, { useState } from "react";

/**
 * Codice iframe per sostituire solo il box MLS sul sito già proprio (D-170).
 */
export default function MlsEmbedKit({ kit, compact = false }) {
  const [copied, setCopied] = useState(false);
  if (!kit) return null;
  const ready = kit.ready !== false && !!kit.iframe_html;
  const copy = async () => {
    if (!kit.iframe_html) return;
    try {
      await navigator.clipboard.writeText(kit.iframe_html);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      setCopied(false);
    }
  };
  return (
    <div
      data-testid="mls-embed-kit"
      className={`border border-stone-900 bg-white space-y-3 ${compact ? "px-3 py-3" : "px-4 py-4"}`}
    >
      <p className="text-sm font-sans text-stone-800">
        Il tuo sito resta dov’è. Sostituisci <strong>solo</strong> il riquadro di ricerca della rete
        MLS con questo codice. Vetrina, menu, contatti: non si toccano.
      </p>
      {!ready ? (
        <p className="text-xs font-sans text-amber-800" data-testid="mls-embed-wait">
          Il codice si attiva quando aderisci alla rete MLS (passo successivo).
        </p>
      ) : null}
      <ol className="text-xs font-sans text-stone-600 space-y-1 list-decimal pl-4">
        {(kit.how_to || []).map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>
      <pre
        data-testid="mls-embed-snippet"
        className="text-[11px] font-mono bg-stone-50 border border-stone-200 p-2 overflow-x-auto whitespace-pre-wrap break-all"
      >
        {kit.iframe_html || "—"}
      </pre>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={!ready}
          onClick={copy}
          data-testid="mls-embed-copy"
          className="px-3 py-2 text-[11px] uppercase tracking-widest bg-stone-900 text-white disabled:opacity-40"
        >
          {copied ? "Copiato" : "Copia il codice"}
        </button>
        {ready && kit.search_url ? (
          <a
            href={kit.search_url}
            target="_blank"
            rel="noreferrer"
            data-testid="mls-embed-preview-link"
            className="px-3 py-2 text-[11px] uppercase tracking-widest border border-stone-400"
          >
            Anteprima box →
          </a>
        ) : null}
      </div>
      {ready && kit.search_url ? (
        <iframe
          title="Anteprima box MLS"
          src={kit.search_url}
          data-testid="mls-embed-preview"
          className="w-full border border-stone-200 bg-white"
          style={{ minHeight: 420 }}
        />
      ) : null}
    </div>
  );
}

import React, { useEffect, useState } from "react";
import { api } from "../../../shared/lib/api";

/**
 * Ricerca contestuale cliente/immobile (CMJ-01).
 * Conserva gli ID tecnici internamente; mostra solo etichette leggibili.
 */
export default function EntitySearch({
  kind,
  value,
  onChange,
  testId,
  placeholder,
  label,
  initialLabel = "",
  required = false,
  disabled = false,
}) {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState([]);
  const [selectedLabel, setSelectedLabel] = useState(initialLabel || "");
  const [loading, setLoading] = useState(false);
  const [searchErr, setSearchErr] = useState("");

  useEffect(() => {
    if (!value) {
      setSelectedLabel("");
      return;
    }
    if (initialLabel) {
      setSelectedLabel(initialLabel);
    }
    const url = kind === "client" ? `/app/clients/${value}` : `/app/properties/${value}`;
    let cancelled = false;
    api
      .get(url)
      .then((r) => {
        if (cancelled) return;
        const d = r.data || {};
        setSelectedLabel(
          kind === "client"
            ? `${d.name || ""} ${d.surname || ""}`.trim() || d.email || initialLabel || "Selezionato"
            : d.title ||
                d.reference_code ||
                [d.address, d.city].filter(Boolean).join(", ") ||
                initialLabel ||
                "Selezionato"
        );
      })
      .catch(() => {
        if (!cancelled) setSelectedLabel(initialLabel || "Immobile condiviso (MLS)");
      });
    return () => {
      cancelled = true;
    };
  }, [kind, value, initialLabel]);

  const search = async (text) => {
    setQ(text);
    setSearchErr("");
    if (!text || text.length < 2) {
      setHits([]);
      return;
    }
    setLoading(true);
    try {
      const url = kind === "client" ? "/app/clients" : "/app/properties";
      const { data } = await api.get(url, { params: { q: text, page_size: 8, limit: 8 } });
      setHits(data.items || []);
      if (!(data.items || []).length) setSearchErr("Nessun risultato");
    } catch {
      setHits([]);
      setSearchErr("Ricerca non riuscita");
    } finally {
      setLoading(false);
    }
  };

  const pick = (item) => {
    onChange(item.id, item);
    setSelectedLabel(
      kind === "client"
        ? `${item.name || ""} ${item.surname || ""}`.trim() || item.email || "Selezionato"
        : item.title ||
            item.reference_code ||
            [item.address, item.city].filter(Boolean).join(", ") ||
            "Selezionato"
    );
    setQ("");
    setHits([]);
    setSearchErr("");
  };

  const clear = () => {
    onChange("", null);
    setSelectedLabel("");
    setQ("");
    setHits([]);
    setSearchErr("");
  };

  const fieldLabel =
    label || (kind === "client" ? "Cliente" : "Immobile") + (required ? "" : " (opzionale)");

  return (
    <div className="relative min-w-[140px] flex-1" data-testid={testId ? `${testId}-wrap` : undefined}>
      <span className="text-[10px] uppercase tracking-widest text-crm-muted">{fieldLabel}</span>
      {value ? (
        <div
          className="mt-1 flex items-center gap-2 border border-crm-line rounded-md px-3 py-2 text-sm bg-white"
          data-testid={testId ? `${testId}-selected` : undefined}
        >
          <span className="truncate flex-1 text-crm-navy">{selectedLabel || "Selezionato"}</span>
          {!disabled ? (
            <button
              type="button"
              className="text-[10px] uppercase tracking-widest text-crm-muted"
              onClick={clear}
              data-testid={testId ? `${testId}-clear` : undefined}
            >
              Cambia
            </button>
          ) : null}
        </div>
      ) : (
        <input
          data-testid={testId}
          value={q}
          onChange={(e) => search(e.target.value)}
          placeholder={placeholder || (kind === "client" ? "Cerca cliente…" : "Cerca immobile…")}
          className="crm-input mt-1 w-full px-3 py-2 border border-crm-line rounded-md text-sm"
          autoComplete="off"
          disabled={disabled}
          required={required && !value}
        />
      )}
      {loading ? <p className="text-[10px] text-crm-muted mt-1">Ricerca…</p> : null}
      {searchErr && !hits.length ? (
        <p className="text-[10px] text-rose-700 mt-1" data-testid={testId ? `${testId}-empty` : undefined}>
          {searchErr}
        </p>
      ) : null}
      {hits.length > 0 ? (
        <ul
          className="absolute z-20 mt-1 w-full bg-white border border-crm-line max-h-48 overflow-auto text-sm shadow-sm"
          data-testid={testId ? `${testId}-hits` : undefined}
        >
          {hits.map((h) => (
            <li key={h.id}>
              <button
                type="button"
                className="w-full text-left px-3 py-2 hover:bg-crm-mist"
                onClick={() => pick(h)}
                data-testid={testId ? `${testId}-hit-${h.id}` : undefined}
              >
                {kind === "client"
                  ? `${h.name || ""} ${h.surname || ""}`.trim() || h.email
                  : h.title ||
                    h.reference_code ||
                    [h.address, h.city].filter(Boolean).join(", ")}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

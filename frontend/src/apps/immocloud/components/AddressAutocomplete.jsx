/* OMNIA — AddressAutocomplete
 *
 * Live autocomplete for Italian addresses, powered by ANNCSU (ISTAT ArcGIS)
 * with graceful fallback to Nominatim OSM (server-side in /api/cloud/anncsu/suggest).
 *
 * UX pattern: identical to Idealista / Immobiliare.it
 *  - User types → debounced API call (350ms, min 3 chars)
 *  - Dropdown of candidates with comune / cap / regione metadata
 *  - Keyboard navigable (↑ ↓ Enter Esc)
 *  - On select: parent receives full record { normalized, comune, provincia_sigla,
 *    regione, cap, lat, lon, source }
 *
 * Props:
 *  - value: string (controlled)
 *  - onChange(text): typed-in text (free editing)
 *  - onSelect(record): user picked a candidate
 *  - placeholder, className, testid (for input)
 */
import React, { useEffect, useRef, useState } from "react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api/cloud/anncsu/suggest`;
const DEBOUNCE_MS = 350;
const MIN_CHARS = 3;

export default function AddressAutocomplete({
  value,
  onChange,
  onSelect,
  placeholder = "",
  className = "",
  testid = "address-autocomplete",
  inputClassName = "",
}) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [candidates, setCandidates] = useState([]);
  const [activeIdx, setActiveIdx] = useState(-1);
  const [selected, setSelected] = useState(null); // last picked record
  const wrapRef = useRef(null);
  const abortRef = useRef(null);
  const debounceRef = useRef(null);

  // Close on outside click
  useEffect(() => {
    const onDoc = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  // Debounced fetch
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!value || value.trim().length < MIN_CHARS) {
      setCandidates([]);
      setOpen(false);
      return;
    }
    // If user edits after a selection, invalidate the validated badge
    if (selected && selected.normalized !== value) {
      setSelected(null);
    }
    debounceRef.current = setTimeout(async () => {
      if (abortRef.current) abortRef.current.abort();
      const ctl = new AbortController();
      abortRef.current = ctl;
      setLoading(true);
      try {
        const r = await fetch(
          `${API}?q=${encodeURIComponent(value)}&limit=6`,
          { signal: ctl.signal },
        );
        const d = await r.json();
        const cands = Array.isArray(d.candidates) ? d.candidates : [];
        setCandidates(cands);
        setActiveIdx(-1);
        setOpen(cands.length > 0);
      } catch (e) {
        if (e.name !== "AbortError") {
          setCandidates([]);
          setOpen(false);
        }
      } finally {
        setLoading(false);
      }
    }, DEBOUNCE_MS);
    return () => clearTimeout(debounceRef.current);
  }, [value]);

  const pick = (idx) => {
    const c = candidates[idx];
    if (!c) return;
    setSelected(c);
    setOpen(false);
    setCandidates([]);
    onChange(c.normalized);
    if (typeof onSelect === "function") onSelect(c);
  };

  const onKeyDown = (e) => {
    if (!open || candidates.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((i) => Math.min(i + 1, candidates.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      if (activeIdx >= 0) {
        e.preventDefault();
        pick(activeIdx);
      }
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  return (
    <div ref={wrapRef} className={`relative ${className}`}>
      <input
        type="text"
        data-testid={testid}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => candidates.length > 0 && setOpen(true)}
        onKeyDown={onKeyDown}
        placeholder={placeholder}
        autoComplete="off"
        className={inputClassName}
      />
      {loading && (
        <div className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-stone-400 pointer-events-none">
          …
        </div>
      )}
      {open && candidates.length > 0 && (
        <ul
          data-testid={`${testid}-dropdown`}
          className="absolute z-30 mt-1 w-full bg-white border border-stone-200 rounded-md shadow-lg max-h-72 overflow-y-auto"
          role="listbox"
        >
          {candidates.map((c, i) => (
            <li
              key={`${c.normalized}-${i}`}
              data-testid={`${testid}-opt-${i}`}
              role="option"
              aria-selected={i === activeIdx}
              onMouseDown={(e) => {
                e.preventDefault();
                pick(i);
              }}
              onMouseEnter={() => setActiveIdx(i)}
              className={`px-3 py-2 cursor-pointer text-sm border-b last:border-b-0 border-stone-100 ${
                i === activeIdx ? "bg-stone-100" : "hover:bg-stone-50"
              }`}
            >
              <div className="text-stone-900 leading-snug line-clamp-2">
                {c.normalized}
              </div>
              <div className="text-[11px] text-stone-500 mt-0.5 flex flex-wrap gap-x-2">
                {c.comune && <span>{c.comune}</span>}
                {c.provincia_sigla && <span>({c.provincia_sigla})</span>}
                {c.cap && <span>· {c.cap}</span>}
                <span className="ml-auto uppercase tracking-wider opacity-60">
                  {c.source === "anncsu" ? "ANNCSU" : "OSM"}
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
      {selected && (
        <div
          data-testid={`${testid}-validated`}
          className="mt-1.5 inline-flex items-center gap-1.5 text-[11px] text-emerald-700 bg-emerald-50 border border-emerald-200 rounded px-2 py-0.5"
        >
          <span>✓</span>
          <span>
            {selected.comune}
            {selected.provincia_sigla ? ` (${selected.provincia_sigla})` : ""}
            {selected.cap ? ` · ${selected.cap}` : ""}
            {selected.regione ? ` · ${selected.regione}` : ""}
          </span>
        </div>
      )}
    </div>
  );
}

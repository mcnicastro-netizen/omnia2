/**
 * A-017 — In-app notification bell (CRM topbar + ImmobilCloud when logged in).
 * Polls /notifications every 45s; dropdown with mark-read + mark-all.
 */
import React, { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../lib/api";

function relativeTime(iso, lang) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    const diff = (Date.now() - d.getTime()) / 1000;
    const rtf = new Intl.RelativeTimeFormat(lang || "it", { numeric: "auto" });
    if (diff < 60) return rtf.format(-Math.floor(diff), "second");
    if (diff < 3600) return rtf.format(-Math.floor(diff / 60), "minute");
    if (diff < 86400) return rtf.format(-Math.floor(diff / 3600), "hour");
    return rtf.format(-Math.floor(diff / 86400), "day");
  } catch {
    return "";
  }
}

export default function NotificationBell({ pollMs = 45000 }) {
  const { i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(false);
  const rootRef = useRef(null);

  const load = useCallback(async () => {
    try {
      const r = await api.get("/notifications", { params: { limit: 20 } });
      setItems(r.data.items || []);
      setUnread(r.data.unread_count || 0);
    } catch {
      // silent — user may not be fully ready
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, pollMs);
    return () => clearInterval(t);
  }, [load, pollMs]);

  useEffect(() => {
    if (!open) return undefined;
    const onDoc = (e) => {
      if (rootRef.current && !rootRef.current.contains(e.target)) setOpen(false);
    };
    const onKey = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const toggle = async () => {
    const next = !open;
    setOpen(next);
    if (next) {
      setLoading(true);
      await load();
      setLoading(false);
    }
  };

  const markOne = async (n) => {
    try {
      if (!n.read) {
        const r = await api.post(`/notifications/${n.id}/read`);
        setUnread(r.data.unread_count ?? Math.max(0, unread - 1));
        setItems((arr) => arr.map((x) => (x.id === n.id ? { ...x, read: true } : x)));
      }
      if (n.link) {
        setOpen(false);
        const path = n.link.startsWith("/") ? `/${lang}${n.link}` : n.link;
        // link stored as /app/... or /cloud/... without lang prefix
        if (n.link.startsWith("/app") || n.link.startsWith("/cloud")) {
          nav(`/${lang}${n.link}`);
        } else {
          nav(path);
        }
      }
    } catch {
      // noop
    }
  };

  const markAll = async () => {
    try {
      await api.post("/notifications/read-all");
      setUnread(0);
      setItems((arr) => arr.map((x) => ({ ...x, read: true })));
    } catch {
      // noop
    }
  };

  const badge = unread > 99 ? "99+" : unread > 0 ? String(unread) : null;

  return (
    <div className="relative" ref={rootRef} data-testid="notification-bell">
      <button
        type="button"
        onClick={toggle}
        aria-label="Notifiche"
        aria-expanded={open}
        data-testid="notification-bell-btn"
        className="relative inline-flex items-center justify-center w-9 h-9 rounded-md text-stone-700 hover:bg-stone-200/70 transition"
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
          <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
        </svg>
        {badge && (
          <span
            data-testid="notification-unread-badge"
            className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 px-1 rounded-full bg-[#C19A6B] text-[9px] font-semibold text-white flex items-center justify-center leading-none"
          >
            {badge}
          </span>
        )}
      </button>

      {open && (
        <div
          data-testid="notification-dropdown"
          className="absolute right-0 mt-2 w-[min(100vw-2rem,22rem)] bg-white border border-stone-200 shadow-lg z-50 overflow-hidden"
          style={{ borderRadius: 6 }}
        >
          <div className="flex items-center justify-between px-3 py-2.5 border-b border-stone-100">
            <p className="text-xs uppercase tracking-widest text-stone-500 font-semibold">
              Notifiche
            </p>
            {unread > 0 && (
              <button
                type="button"
                onClick={markAll}
                data-testid="notification-mark-all"
                className="text-[11px] text-[#0B1E3F] hover:underline"
              >
                Segna tutte lette
              </button>
            )}
          </div>
          <ul className="max-h-80 overflow-y-auto divide-y divide-stone-100">
            {loading && items.length === 0 && (
              <li className="px-3 py-6 text-sm text-stone-400 text-center">Caricamento…</li>
            )}
            {!loading && items.length === 0 && (
              <li
                className="px-3 py-8 text-sm text-stone-400 text-center"
                data-testid="notification-empty"
              >
                Nessuna notifica
              </li>
            )}
            {items.map((n) => (
              <li key={n.id}>
                <button
                  type="button"
                  onClick={() => markOne(n)}
                  data-testid={`notification-item-${n.id}`}
                  className={`w-full text-left px-3 py-3 hover:bg-stone-50 transition ${
                    n.read ? "bg-white" : "bg-amber-50/40"
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {!n.read && (
                      <span
                        className="mt-1.5 w-1.5 h-1.5 rounded-full bg-[#C19A6B] shrink-0"
                        aria-hidden="true"
                      />
                    )}
                    <div className={`min-w-0 flex-1 ${n.read ? "pl-3.5" : ""}`}>
                      <p className="text-sm text-stone-900 font-medium leading-snug truncate">
                        {n.title}
                      </p>
                      {n.body ? (
                        <p className="text-xs text-stone-500 mt-0.5 line-clamp-2">{n.body}</p>
                      ) : null}
                      <p className="text-[10px] uppercase tracking-wider text-stone-400 mt-1">
                        {relativeTime(n.created_at, lang)}
                      </p>
                    </div>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

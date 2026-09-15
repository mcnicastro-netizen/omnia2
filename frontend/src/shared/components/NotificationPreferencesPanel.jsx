/**
 * A-021 — Notification preferences panel (shared B2B Settings + B2C Account).
 * Channels: email / push (push disabled v1). Email types toggles. B2C digest default.
 */
import React, { useEffect, useState } from "react";
import { api } from "../lib/api";

const EMAIL_TYPES = [
  { key: "welcome", label: "Email di benvenuto" },
  { key: "agency_invite", label: "Inviti agenzia" },
  { key: "lead_notification", label: "Nuovi lead / contatti" },
  { key: "saved_search_alert", label: "Alert ricerche salvate" },
];

const FREQ = [
  { v: "instant", label: "Immediato" },
  { v: "daily", label: "Digest giornaliero" },
  { v: "weekly", label: "Digest settimanale" },
];

export default function NotificationPreferencesPanel({ showSavedSearchFreq = false }) {
  const [prefs, setPrefs] = useState(null);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get("/auth/me/notification-preferences")
      .then((r) => setPrefs(r.data))
      .catch(() => setErr("Impossibile caricare le preferenze"));
  }, []);

  const toggleChannel = (ch) => {
    if (ch === "push") return; // v1 disabled
    setPrefs((p) => {
      const set = new Set(p.notification_channels || []);
      if (set.has(ch)) set.delete(ch);
      else set.add(ch);
      return { ...p, notification_channels: [...set] };
    });
  };

  const toggleType = (key) => {
    setPrefs((p) => {
      const set = new Set(p.notification_email_types || []);
      if (set.has(key)) set.delete(key);
      else set.add(key);
      return { ...p, notification_email_types: [...set] };
    });
  };

  const save = async () => {
    if (!prefs) return;
    setSaving(true);
    setErr("");
    setMsg("");
    try {
      const body = {
        notification_channels: prefs.notification_channels,
        notification_email_types: prefs.notification_email_types,
      };
      if (showSavedSearchFreq) {
        body.saved_search_frequency_default = prefs.saved_search_frequency_default;
      }
      const r = await api.patch("/auth/me/notification-preferences", body);
      setPrefs(r.data);
      setMsg("Preferenze salvate");
      setTimeout(() => setMsg(""), 2500);
    } catch (e) {
      setErr(e.response?.data?.detail || "Salvataggio non riuscito");
    } finally {
      setSaving(false);
    }
  };

  if (!prefs && !err) {
    return <p className="text-sm text-stone-500">Caricamento preferenze…</p>;
  }
  if (!prefs) {
    return <p className="text-sm text-red-700">{err}</p>;
  }

  const emailOn = (prefs.notification_channels || []).includes("email");

  return (
    <div data-testid="notification-prefs-panel" className="space-y-5">
      <div>
        <p className="text-xs uppercase tracking-widest text-stone-500 mb-2">Canali</p>
        <div className="flex flex-wrap gap-4">
          <label className="inline-flex items-center gap-2 text-sm text-stone-800 cursor-pointer">
            <input
              type="checkbox"
              data-testid="pref-channel-email"
              checked={emailOn}
              onChange={() => toggleChannel("email")}
            />
            Email
          </label>
          <label
            className="inline-flex items-center gap-2 text-sm text-stone-400 cursor-not-allowed"
            title="Push in arrivo in v1.1"
          >
            <input type="checkbox" disabled checked={false} data-testid="pref-channel-push" />
            Push <span className="text-[10px] uppercase tracking-widest">(in arrivo v1.1)</span>
          </label>
        </div>
      </div>

      <div className={!emailOn ? "opacity-50 pointer-events-none" : ""}>
        <p className="text-xs uppercase tracking-widest text-stone-500 mb-2">Tipi di email</p>
        <ul className="space-y-2">
          {EMAIL_TYPES.map((t) => (
            <li key={t.key}>
              <label className="inline-flex items-center gap-2 text-sm text-stone-800 cursor-pointer">
                <input
                  type="checkbox"
                  data-testid={`pref-type-${t.key}`}
                  checked={(prefs.notification_email_types || []).includes(t.key)}
                  onChange={() => toggleType(t.key)}
                />
                {t.label}
              </label>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-[11px] text-stone-500">
          Le email di reset password sono sempre inviate per sicurezza account.
        </p>
      </div>

      {showSavedSearchFreq && (
        <div>
          <p className="text-xs uppercase tracking-widest text-stone-500 mb-2">
            Frequenza default alert ricerche
          </p>
          <select
            data-testid="pref-ss-freq"
            className="border border-stone-300 rounded px-3 py-2 text-sm bg-white"
            value={prefs.saved_search_frequency_default || "instant"}
            onChange={(e) =>
              setPrefs((p) => ({ ...p, saved_search_frequency_default: e.target.value }))
            }
          >
            {FREQ.map((f) => (
              <option key={f.v} value={f.v}>{f.label}</option>
            ))}
          </select>
          <p className="mt-1 text-[11px] text-stone-500">
            Si applica come preferenza account; ogni ricerca salvata può avere una frequenza propria.
          </p>
        </div>
      )}

      <div className="flex items-center gap-3">
        <button
          type="button"
          data-testid="pref-save-btn"
          disabled={saving}
          onClick={save}
          className="px-4 py-2 bg-stone-900 text-white text-xs uppercase tracking-widest rounded disabled:opacity-50"
        >
          {saving ? "Salvataggio…" : "Salva preferenze"}
        </button>
        {msg && <span className="text-xs text-emerald-700" data-testid="pref-saved">{msg}</span>}
        {err && <span className="text-xs text-red-700">{err}</span>}
      </div>
    </div>
  );
}

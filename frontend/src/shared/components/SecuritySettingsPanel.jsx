import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { formatApiErrorDetail, useAuth } from "../lib/auth";

/**
 * Shared security panel: MFA setup + GDPR erase.
 * Used in CRM Settings and B2C Account.
 */
export default function SecuritySettingsPanel({ variant = "crm" }) {
  const { user, logout, refresh } = useAuth();
  const [status, setStatus] = useState(null);
  const [setup, setSetup] = useState(null);
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [backupCodes, setBackupCodes] = useState(null);
  const [eraseConfirm, setEraseConfirm] = useState("");
  const [erasePassword, setErasePassword] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    try {
      const { data } = await api.get("/auth/mfa/status");
      setStatus(data);
    } catch (e) {
      setErr(formatApiErrorDetail(e?.response?.data?.detail));
    }
  };

  useEffect(() => {
    load();
  }, []);

  const startSetup = async () => {
    setErr("");
    setBusy(true);
    try {
      const { data } = await api.post("/auth/mfa/setup");
      setSetup(data);
      setBackupCodes(null);
    } catch (e) {
      setErr(formatApiErrorDetail(e?.response?.data?.detail));
    } finally {
      setBusy(false);
    }
  };

  const enable = async () => {
    setErr("");
    setBusy(true);
    try {
      const { data } = await api.post("/auth/mfa/enable", { code });
      setBackupCodes(data.backup_codes || []);
      setSetup(null);
      setCode("");
      setMsg("Autenticazione a due fattori attiva.");
      await load();
      await refresh();
    } catch (e) {
      setErr(formatApiErrorDetail(e?.response?.data?.detail) || "Codice non valido");
    } finally {
      setBusy(false);
    }
  };

  const disable = async () => {
    setErr("");
    setBusy(true);
    try {
      await api.post("/auth/mfa/disable", { code, password: password || undefined });
      setMsg("MFA disattivata.");
      setCode("");
      setPassword("");
      await load();
      await refresh();
    } catch (e) {
      setErr(formatApiErrorDetail(e?.response?.data?.detail) || "Impossibile disattivare");
    } finally {
      setBusy(false);
    }
  };

  const erase = async () => {
    if (eraseConfirm.trim().toUpperCase() !== "DELETE") {
      setErr('Scrivi DELETE per confermare.');
      return;
    }
    if (!window.confirm("Confermi la cancellazione definitiva di account e dati personali?")) return;
    setErr("");
    setBusy(true);
    try {
      await api.post("/auth/me/erase", {
        confirm: "DELETE",
        password: erasePassword || undefined,
      });
      await logout();
      window.location.href = "/";
    } catch (e) {
      setErr(formatApiErrorDetail(e?.response?.data?.detail) || "Cancellazione non riuscita");
      setBusy(false);
    }
  };

  const enabled = Boolean(status?.enabled ?? user?.mfa_enabled);

  return (
    <section
      data-testid={`security-panel-${variant}`}
      className="border border-stone-200 bg-white rounded-lg p-6 space-y-6"
    >
      <div>
        <h2 className="text-xs uppercase tracking-widest text-stone-500">Sicurezza & privacy</h2>
        <p className="text-sm text-stone-600 mt-1">
          Login a due fattori e cancellazione dei tuoi dati personali (GDPR).
        </p>
      </div>

      {err && (
        <p data-testid="security-error" className="text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded px-3 py-2">
          {err}
        </p>
      )}
      {msg && (
        <p data-testid="security-msg" className="text-sm text-emerald-800 bg-emerald-50 border border-emerald-200 rounded px-3 py-2">
          {msg}
        </p>
      )}

      <div className="space-y-3" data-testid="mfa-block">
        <h3 className="text-sm font-medium text-stone-900">Autenticazione a due fattori (app Authenticator)</h3>
        <p className="text-xs text-stone-500">
          Stato: {enabled ? "attiva" : "disattiva"}
          {enabled && status?.backup_codes_remaining != null
            ? ` · codici di recupero rimasti: ${status.backup_codes_remaining}`
            : ""}
        </p>

        {!enabled && !setup && (
          <button
            type="button"
            data-testid="mfa-setup-btn"
            disabled={busy}
            onClick={startSetup}
            className="px-4 py-2 bg-stone-900 text-white text-xs uppercase tracking-widest rounded-md hover:bg-stone-700 disabled:opacity-50"
          >
            Attiva MFA
          </button>
        )}

        {setup && (
          <div className="space-y-3 border border-stone-200 rounded-md p-4 bg-stone-50">
            <p className="text-sm text-stone-700">Scansiona il QR con Google Authenticator / Authy, oppure inserisci il codice manuale:</p>
            {setup.qr_data_uri && (
              <img src={setup.qr_data_uri} alt="QR MFA" className="w-40 h-40 bg-white border border-stone-200" data-testid="mfa-qr" />
            )}
            <code className="block text-xs break-all bg-white border border-stone-200 p-2" data-testid="mfa-secret">
              {setup.secret}
            </code>
            <label className="block">
              <span className="text-xs uppercase tracking-widest text-stone-500">Codice a 6 cifre</span>
              <input
                data-testid="mfa-enable-code"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="mt-1 w-full max-w-xs px-3 py-2 border border-stone-300 rounded-md text-sm"
                inputMode="numeric"
                autoComplete="one-time-code"
              />
            </label>
            <button
              type="button"
              data-testid="mfa-enable-btn"
              disabled={busy || code.length < 6}
              onClick={enable}
              className="px-4 py-2 bg-stone-900 text-white text-xs uppercase tracking-widest rounded-md disabled:opacity-50"
            >
              Conferma e attiva
            </button>
          </div>
        )}

        {backupCodes && (
          <div className="border border-amber-200 bg-amber-50 rounded-md p-4" data-testid="mfa-backup-codes">
            <p className="text-sm font-medium text-amber-900 mb-2">Salva questi codici di recupero (una sola volta):</p>
            <ul className="grid grid-cols-2 gap-1 font-mono text-xs">
              {backupCodes.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
          </div>
        )}

        {enabled && (
          <div className="space-y-2 border border-stone-200 rounded-md p-4">
            <p className="text-xs text-stone-500">Per disattivare: codice MFA (o backup) + password (se account email).</p>
            <input
              data-testid="mfa-disable-code"
              placeholder="Codice MFA"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full max-w-xs px-3 py-2 border border-stone-300 rounded-md text-sm"
            />
            <input
              data-testid="mfa-disable-password"
              type="password"
              placeholder="Password (se usi email/password)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full max-w-xs px-3 py-2 border border-stone-300 rounded-md text-sm"
            />
            <button
              type="button"
              data-testid="mfa-disable-btn"
              disabled={busy}
              onClick={disable}
              className="px-4 py-2 border border-stone-300 text-xs uppercase tracking-widest rounded-md hover:bg-stone-50"
            >
              Disattiva MFA
            </button>
          </div>
        )}
      </div>

      <div className="space-y-3 border-t border-stone-200 pt-6" data-testid="erase-block">
        <h3 className="text-sm font-medium text-rose-800">Cancella i miei dati</h3>
        <p className="text-xs text-stone-600">
          Elimina account, preferiti, ricerche salvate, lead personali e anonimizza i tuoi dati.
          Scrivi <strong>DELETE</strong> per confermare.
        </p>
        <input
          data-testid="erase-confirm"
          value={eraseConfirm}
          onChange={(e) => setEraseConfirm(e.target.value)}
          placeholder="DELETE"
          className="w-full max-w-xs px-3 py-2 border border-rose-200 rounded-md text-sm"
        />
        <input
          data-testid="erase-password"
          type="password"
          value={erasePassword}
          onChange={(e) => setErasePassword(e.target.value)}
          placeholder="Password (se account email/password)"
          className="w-full max-w-xs px-3 py-2 border border-stone-300 rounded-md text-sm"
        />
        <button
          type="button"
          data-testid="erase-btn"
          disabled={busy}
          onClick={erase}
          className="px-4 py-2 bg-rose-800 text-white text-xs uppercase tracking-widest rounded-md hover:bg-rose-700 disabled:opacity-50"
        >
          Cancella definitivamente
        </button>
      </div>
    </section>
  );
}

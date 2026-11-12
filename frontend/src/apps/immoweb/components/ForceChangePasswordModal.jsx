import React, { useState } from "react";
import { api } from "../../../shared/lib/api";
import { useAuth, formatApiErrorDetail } from "../../../shared/lib/auth";

/**
 * D-160 — blocco primo ingresso dopo Attiva (API key = password iniziale).
 * Obbliga a scegliere una password personale; la chiave API resta valida per integrazioni.
 */
export default function ForceChangePasswordModal() {
  const { user, refresh } = useAuth();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [copied, setCopied] = useState(false);

  if (!user || !user.must_change_password) return null;

  const copyHint = async () => {
    const tip =
      "Incolla qui la chiave ricevuta via email (password iniziale), poi scegli la nuova password.";
    try {
      await navigator.clipboard.writeText(tip);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* ignore */
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    setErr(null);
    if (next.length < 8) {
      setErr("La nuova password deve avere almeno 8 caratteri.");
      return;
    }
    if (next !== confirm) {
      setErr("Le due password non coincidono.");
      return;
    }
    setBusy(true);
    try {
      await api.post("/auth/me/change-password", {
        current_password: current,
        new_password: next,
      });
      await refresh();
    } catch (ex) {
      const d = ex?.response?.data?.detail;
      if (d === "current_password_wrong") {
        setErr("Password attuale non corretta. Usa il codice ricevuto via email.");
      } else {
        setErr(formatApiErrorDetail(d) || "Cambio password non riuscito");
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      data-testid="force-change-password"
      className="fixed inset-0 z-[80] bg-stone-900/50 flex items-center justify-center p-4"
    >
      <form
        onSubmit={submit}
        className="w-full max-w-md bg-white border border-stone-200 rounded-lg shadow-lg p-6 space-y-4"
      >
        <h2
          className="text-2xl text-[#0B1E3F] tracking-tight"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        >
          Scegli la tua password
        </h2>
        <p className="text-sm text-stone-600">
          Al primo accesso usa il <strong>codice ricevuto via email</strong> come
          password temporanea, poi scegline una tua. Potrai continuare subito nel
          gestionale.
        </p>
        <label className="block text-xs uppercase tracking-widest text-stone-500">
          Password attuale (codice dall’email)
          <input
            type="password"
            autoComplete="current-password"
            data-testid="force-pw-current"
            className="mt-1 w-full border border-stone-300 rounded-md px-3 py-2 text-sm font-mono normal-case tracking-normal"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            required
          />
        </label>
        <p className="text-[11px] text-stone-500">
          Nell’email: seleziona il codice e copia (Ctrl+C / tieni premuto su
          mobile).{" "}
          <button
            type="button"
            onClick={copyHint}
            className="underline text-[#0B1E3F]"
          >
            {copied ? "Ok" : "Promemoria"}
          </button>
        </p>
        <label className="block text-xs uppercase tracking-widest text-stone-500">
          Nuova password
          <input
            type="password"
            autoComplete="new-password"
            data-testid="force-pw-new"
            className="mt-1 w-full border border-stone-300 rounded-md px-3 py-2 text-sm normal-case tracking-normal"
            value={next}
            onChange={(e) => setNext(e.target.value)}
            minLength={8}
            required
          />
        </label>
        <label className="block text-xs uppercase tracking-widest text-stone-500">
          Conferma nuova password
          <input
            type="password"
            autoComplete="new-password"
            data-testid="force-pw-confirm"
            className="mt-1 w-full border border-stone-300 rounded-md px-3 py-2 text-sm normal-case tracking-normal"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            minLength={8}
            required
          />
        </label>
        {err ? (
          <p className="text-sm text-rose-800 bg-rose-50 border border-rose-200 rounded px-3 py-2">
            {err}
          </p>
        ) : null}
        <button
          type="submit"
          disabled={busy}
          data-testid="force-pw-submit"
          className="w-full text-xs uppercase tracking-widest px-4 py-3 rounded bg-[#0B1E3F] text-white disabled:opacity-40"
        >
          {busy ? "Salvataggio…" : "Salva e continua"}
        </button>
      </form>
    </div>
  );
}

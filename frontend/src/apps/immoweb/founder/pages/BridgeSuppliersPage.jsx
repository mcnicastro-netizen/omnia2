import React, { useEffect, useState } from "react";
import { api } from "../../../../shared/lib/api";

export default function BridgeSuppliersPage() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [msg, setMsg] = useState(null);
  const [busyId, setBusyId] = useState(null);

  const load = async () => {
    try {
      const r = await api.get("/app/ops/bridge/providers");
      setData(r.data);
    } catch {
      setErr("Impossibile caricare i fornitori.");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const kill = async (id, revive) => {
    const note = window.prompt(
      revive
        ? `Riattivare ${id}? Nota opzionale:`
        : `SPEGNERE ${id} (kill-switch)? Nota obbligatoria consigliata:`
    );
    if (note === null) return;
    if (
      !revive &&
      !window.confirm(`Confermi kill-switch su «${id}»? I servizi collegati falliranno soft.`)
    ) {
      return;
    }
    setBusyId(id);
    setMsg(null);
    try {
      await api.post(
        `/app/ops/bridge/providers/${id}/${revive ? "revive" : "kill"}`,
        { note: note || "" }
      );
      setMsg(revive ? `${id} riattivato` : `${id} spento`);
      await load();
    } catch {
      setMsg("Operazione non riuscita.");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div data-testid="bridge-suppliers" className="space-y-8">
      <header>
        <h1
          className="text-3xl text-[#0B1E3F] tracking-tight"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        >
          Fornitori
        </h1>
        <p className="mt-2 text-sm text-stone-600 max-w-2xl">
          Presenza chiave, circuit breaker e kill-switch di emergenza. Mai il valore del secret.
        </p>
      </header>

      {err ? <p className="text-sm text-red-700">{err}</p> : null}
      {msg ? <p className="text-sm text-[#0B1E3F]">{msg}</p> : null}

      {data ? (
        <div className="text-xs text-stone-500 uppercase tracking-widest">
          Stripe {data.stripe_enabled ? "ON" : "OFF"} · mode {data.stripe_mode}
        </div>
      ) : null}

      <ul className="grid md:grid-cols-2 gap-3" data-testid="bridge-providers-list">
        {(data?.items || []).map((p) => (
          <li
            key={p.id}
            className={`bg-white border rounded-lg px-4 py-4 space-y-2 ${
              p.killed ? "border-rose-300" : "border-stone-200"
            }`}
            data-testid={`bridge-provider-${p.id}`}
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-medium text-[#0B1E3F]">{p.label}</p>
                <p className="text-[10px] uppercase tracking-widest text-stone-400 mt-1">
                  {p.env}
                </p>
              </div>
              <span
                className={`text-[10px] uppercase tracking-widest px-2 py-1 rounded ${
                  p.killed
                    ? "bg-rose-100 text-rose-900"
                    : p.configured
                      ? "bg-emerald-50 text-emerald-800"
                      : "bg-rose-50 text-rose-800"
                }`}
              >
                {p.killed ? "KILL" : p.configured ? "configurato" : "manca"}
              </span>
            </div>
            <p className="text-xs text-stone-500 font-mono">{p.hint}</p>
            {p.circuit_open || p.held ? (
              <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-2 py-1">
                Circuit {p.held ? "HOLD" : "APERTO"} · fail={p.circuit_failures}
                {p.last_error ? ` · ${p.last_error}` : ""}
              </p>
            ) : p.configured ? (
              <p className="text-xs text-stone-500">Circuit ok</p>
            ) : null}
            {p.kill_note ? (
              <p className="text-xs text-stone-500">Nota: {p.kill_note}</p>
            ) : null}
            <div className="pt-1">
              {p.killed ? (
                <button
                  type="button"
                  disabled={busyId === p.id}
                  onClick={() => kill(p.id, true)}
                  className="text-[10px] uppercase tracking-widest px-3 py-1.5 rounded border border-emerald-400 text-emerald-900"
                  data-testid={`bridge-revive-${p.id}`}
                >
                  Riattiva
                </button>
              ) : (
                <button
                  type="button"
                  disabled={busyId === p.id || p.id === "mongodb"}
                  onClick={() => kill(p.id, false)}
                  className="text-[10px] uppercase tracking-widest px-3 py-1.5 rounded border border-rose-300 text-rose-800 disabled:opacity-40"
                  data-testid={`bridge-kill-${p.id}`}
                  title={p.id === "mongodb" ? "Mongo non spegnibile da UI" : ""}
                >
                  Kill-switch
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>

      {!data && !err ? <p className="text-sm text-stone-500">Caricamento…</p> : null}
    </div>
  );
}

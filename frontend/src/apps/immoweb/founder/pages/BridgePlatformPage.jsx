import React, { useEffect, useState } from "react";
import { api } from "../../../../shared/lib/api";

export default function BridgePlatformPage() {
  const [preflight, setPreflight] = useState(null);
  const [overview, setOverview] = useState(null);
  const [msg, setMsg] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    try {
      const [p, o] = await Promise.all([
        api.get("/app/ops/preflight"),
        api.get("/app/ops/overview?days=7"),
      ]);
      setPreflight(p.data);
      setOverview(o.data);
    } catch {
      setPreflight(null);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const runBackup = async () => {
    setBusy(true);
    setMsg(null);
    try {
      await api.post("/app/ops/backup/run");
      setMsg("Backup avviato.");
      await load();
    } catch {
      setMsg("Backup non riuscito.");
    } finally {
      setBusy(false);
    }
  };

  const ackAll = async () => {
    try {
      await api.post("/app/ops/alerts/ack-all");
      await load();
    } catch {
      /* ignore */
    }
  };

  const checks = preflight?.checks || {};

  return (
    <div data-testid="bridge-platform" className="space-y-8">
      <header>
        <h1
          className="text-3xl text-[#0B1E3F] tracking-tight"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        >
          Piattaforma
        </h1>
        <p className="mt-2 text-sm text-stone-600 max-w-2xl">
          Preflight, backup, alert operativi. Azioni distruttive (blank-slate) restano via API
          script — non in UI.
        </p>
      </header>

      {msg ? <p className="text-sm text-[#0B1E3F]">{msg}</p> : null}

      <section className="bg-white border border-stone-200 rounded-lg px-5 py-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-xs uppercase tracking-widest text-stone-500">Preflight</h2>
          <span
            className={`text-xs uppercase tracking-widest px-2 py-1 rounded ${
              preflight?.esito === "PASS"
                ? "bg-emerald-50 text-emerald-800"
                : "bg-amber-50 text-amber-900"
            }`}
            data-testid="bridge-preflight-esito"
          >
            {preflight?.esito || "—"}
          </span>
        </div>
        <ul className="grid sm:grid-cols-2 gap-2 text-sm">
          {Object.entries(checks).map(([k, v]) => (
            <li key={k} className="flex justify-between gap-2 border border-stone-100 rounded px-3 py-2">
              <span className="text-stone-600 font-mono text-xs">{k}</span>
              <span className={v ? "text-emerald-700" : "text-rose-700"}>{v ? "ok" : "fail"}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="bg-white border border-stone-200 rounded-lg px-5 py-5 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-xs uppercase tracking-widest text-stone-500">Backup</h2>
          <button
            type="button"
            disabled={busy}
            onClick={runBackup}
            className="text-[10px] uppercase tracking-widest px-3 py-1.5 rounded border border-stone-300 hover:bg-stone-50 disabled:opacity-50"
          >
            Esegui ora
          </button>
        </div>
        <p className="text-sm">
          Stato: <strong>{overview?.backup?.status || preflight?.backup?.status || "—"}</strong>
          {" · "}
          {(overview?.backup?.created_at || preflight?.backup?.created_at || "").slice(0, 19) ||
            "nessun run"}
        </p>
      </section>

      <section className="bg-white border border-stone-200 rounded-lg px-5 py-5 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-xs uppercase tracking-widest text-stone-500">
            Alert ({overview?.alerts?.unacked ?? preflight?.alerts_unacked ?? 0} aperti)
          </h2>
          {(overview?.alerts?.unacked || 0) > 0 ? (
            <button
              type="button"
              onClick={ackAll}
              className="text-[10px] uppercase tracking-widest px-3 py-1.5 rounded border border-amber-300 text-amber-900"
            >
              Segna tutti visti
            </button>
          ) : null}
        </div>
        <ul className="space-y-2 text-sm">
          {(overview?.alerts?.recent || []).slice(0, 12).map((a) => (
            <li key={a.id} className="flex gap-2 border-b border-stone-100 pb-2">
              <span className="text-[10px] uppercase tracking-widest text-stone-400 w-16 shrink-0">
                {a.severity}
              </span>
              <span className="flex-1">{a.message}</span>
            </li>
          ))}
          {!overview?.alerts?.recent?.length ? (
            <li className="text-stone-500">Nessun alert recente.</li>
          ) : null}
        </ul>
      </section>
    </div>
  );
}

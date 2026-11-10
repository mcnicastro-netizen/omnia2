import React, { useEffect, useState } from "react";
import { api } from "../../../../shared/lib/api";

export default function BridgeSuppliersPage() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    api
      .get("/app/ops/bridge/providers")
      .then((r) => setData(r.data))
      .catch(() => setErr("Impossibile caricare i fornitori."));
  }, []);

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
          Servizi esterni collegati a OMNIA. Vedi solo se la chiave è presente e lo stato del
          circuit breaker — mai il valore del secret.
        </p>
      </header>

      {err ? <p className="text-sm text-red-700">{err}</p> : null}

      {data ? (
        <div className="text-xs text-stone-500 uppercase tracking-widest">
          Stripe {data.stripe_enabled ? "ON" : "OFF"} · mode {data.stripe_mode}
        </div>
      ) : null}

      <ul className="grid md:grid-cols-2 gap-3" data-testid="bridge-providers-list">
        {(data?.items || []).map((p) => (
          <li
            key={p.id}
            className="bg-white border border-stone-200 rounded-lg px-4 py-4 space-y-2"
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
                  p.configured
                    ? "bg-emerald-50 text-emerald-800"
                    : "bg-rose-50 text-rose-800"
                }`}
              >
                {p.configured ? "configurato" : "manca"}
              </span>
            </div>
            <p className="text-xs text-stone-500 font-mono">{p.hint}</p>
            {p.circuit_open ? (
              <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-2 py-1">
                Circuit APERTO · fail={p.circuit_failures}
                {p.last_error ? ` · ${p.last_error}` : ""}
              </p>
            ) : p.configured ? (
              <p className="text-xs text-stone-500">Circuit ok</p>
            ) : null}
          </li>
        ))}
      </ul>

      {!data && !err ? <p className="text-sm text-stone-500">Caricamento…</p> : null}
    </div>
  );
}

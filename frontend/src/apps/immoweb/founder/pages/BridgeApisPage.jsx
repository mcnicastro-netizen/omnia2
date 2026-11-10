import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../../../../shared/lib/api";

export default function BridgeApisPage() {
  const [sp] = useSearchParams();
  const [q, setQ] = useState(sp.get("q") || "");
  const [items, setItems] = useState([]);
  const [busy, setBusy] = useState(true);
  const [msg, setMsg] = useState(null);
  const [plain, setPlain] = useState(null);

  const load = async () => {
    setBusy(true);
    try {
      const r = await api.get("/app/ops/bridge/api-keys", {
        params: { q, limit: 200 },
      });
      setItems(r.data?.items || []);
    } catch {
      setItems([]);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const revoke = async (id) => {
    if (!window.confirm("Bloccare (revocare) questa API key? Irreversibile.")) return;
    setMsg(null);
    setPlain(null);
    try {
      await api.post(`/app/ops/bridge/api-keys/${id}/revoke`);
      setMsg("Chiave revocata.");
      await load();
    } catch {
      setMsg("Revoca non riuscita.");
    }
  };

  const rotate = async (id) => {
    if (!window.confirm("Rigenerare la chiave? La vecchia smette di funzionare subito.")) return;
    setMsg(null);
    setPlain(null);
    try {
      const r = await api.post(`/app/ops/bridge/api-keys/${id}/rotate`);
      setPlain(r.data?.key || null);
      setMsg("Nuova chiave emessa — copiala ora, non sarà più mostrata.");
      await load();
    } catch {
      setMsg("Rotazione non riuscita.");
    }
  };

  return (
    <div data-testid="bridge-apis" className="space-y-8">
      <header>
        <h1
          className="text-3xl text-[#0B1E3F] tracking-tight"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        >
          API clienti
        </h1>
        <p className="mt-2 text-sm text-stone-600 max-w-2xl">
          Tutte le chiavi Track B delle agenzie. Puoi bloccarle o rigenerarle. Il secret in chiaro
          appare solo al momento della rotazione.
        </p>
      </header>

      <form
        className="flex gap-2 flex-wrap"
        onSubmit={(e) => {
          e.preventDefault();
          load();
        }}
      >
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Agenzia, prefisso, nome…"
          className="flex-1 min-w-[200px] border border-stone-300 rounded-md px-3 py-2 text-sm bg-white"
          data-testid="bridge-apis-q"
        />
        <button
          type="submit"
          className="text-xs uppercase tracking-widest px-4 py-2 rounded bg-[#0B1E3F] text-white"
        >
          Filtra
        </button>
      </form>

      {msg ? (
        <div className="text-sm bg-stone-50 border border-stone-200 rounded-lg px-4 py-3 space-y-2">
          <p>{msg}</p>
          {plain ? (
            <code
              data-testid="bridge-api-plaintext"
              className="block text-xs break-all font-mono bg-white border border-stone-200 rounded px-2 py-2"
            >
              {plain}
            </code>
          ) : null}
        </div>
      ) : null}

      {busy ? (
        <p className="text-sm text-stone-500">Caricamento…</p>
      ) : (
        <div className="overflow-x-auto border border-stone-200 rounded-lg bg-white" data-testid="bridge-apis-table">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-stone-200 text-[10px] uppercase tracking-widest text-stone-500 text-left">
                <th className="px-3 py-2">Agenzia</th>
                <th className="px-3 py-2">Nome</th>
                <th className="px-3 py-2">Prefisso</th>
                <th className="px-3 py-2">Stato</th>
                <th className="px-3 py-2">Crediti</th>
                <th className="px-3 py-2">Azioni</th>
              </tr>
            </thead>
            <tbody>
              {items.map((k) => (
                <tr key={k.id} className="border-b border-stone-100 last:border-0">
                  <td className="px-3 py-2">{k.agency_name}</td>
                  <td className="px-3 py-2">{k.name}</td>
                  <td className="px-3 py-2 font-mono text-xs">{k.key_prefix}</td>
                  <td className="px-3 py-2">
                    {k.is_active ? (
                      <span className="text-emerald-700">attiva</span>
                    ) : (
                      <span className="text-stone-400">revocata</span>
                    )}
                  </td>
                  <td className="px-3 py-2">{k.credits_balance ?? "—"}</td>
                  <td className="px-3 py-2 space-x-2 whitespace-nowrap">
                    {k.is_active ? (
                      <>
                        <button
                          type="button"
                          onClick={() => revoke(k.id)}
                          className="text-[10px] uppercase tracking-widest text-rose-700 hover:underline"
                        >
                          Blocca
                        </button>
                        <button
                          type="button"
                          onClick={() => rotate(k.id)}
                          className="text-[10px] uppercase tracking-widest text-[#0B1E3F] hover:underline"
                        >
                          Rigenera
                        </button>
                      </>
                    ) : (
                      <span className="text-stone-400 text-[10px] uppercase tracking-widest">—</span>
                    )}
                  </td>
                </tr>
              ))}
              {!items.length ? (
                <tr>
                  <td colSpan={6} className="px-3 py-8 text-center text-stone-500">
                    Nessuna chiave.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

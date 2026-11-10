import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api } from "../../../../shared/lib/api";

export default function BridgeClientsPage() {
  const { lang: langParam } = useParams();
  const lang = langParam || "it";
  const base = `/${lang}/app/ops`;
  const [sp, setSp] = useSearchParams();
  const tab = sp.get("tab") === "b2c" ? "b2c" : "agenzie";
  const status = sp.get("status") || "";
  const [q, setQ] = useState(sp.get("q") || "");
  const [items, setItems] = useState([]);
  const [busy, setBusy] = useState(true);
  const [err, setErr] = useState(null);

  const load = async () => {
    setBusy(true);
    setErr(null);
    try {
      if (tab === "b2c") {
        const r = await api.get(`/app/ops/bridge/b2c-users`, { params: { q, limit: 80 } });
        setItems(r.data?.items || []);
      } else {
        const r = await api.get(`/app/ops/bridge/tenants`, {
          params: { q, status, limit: 80 },
        });
        setItems(r.data?.items || []);
      }
    } catch (e) {
      setErr("Caricamento non riuscito.");
      setItems([]);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, status]);

  const setTab = (t) => {
    const next = new URLSearchParams(sp);
    if (t === "b2c") next.set("tab", "b2c");
    else next.delete("tab");
    setSp(next);
  };

  const title = useMemo(
    () => (tab === "b2c" ? "Archivio utenti B2C" : "Archivio agenzie"),
    [tab]
  );

  return (
    <div data-testid="bridge-clients" className="space-y-8">
      <header>
        <h1
          className="text-3xl text-[#0B1E3F] tracking-tight"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        >
          Clienti
        </h1>
        <p className="mt-2 text-sm text-stone-600 max-w-2xl">
          Archivi piattaforma: agenzie (con titolare, piano, conteggi) e account ImmobilCloud.
        </p>
      </header>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          data-testid="bridge-tab-agenzie"
          onClick={() => setTab("agenzie")}
          className={`text-xs uppercase tracking-widest px-3 py-2 rounded border ${
            tab === "agenzie" ? "bg-[#0B1E3F] text-white border-[#0B1E3F]" : "border-stone-300"
          }`}
        >
          Agenzie
        </button>
        <button
          type="button"
          data-testid="bridge-tab-b2c"
          onClick={() => setTab("b2c")}
          className={`text-xs uppercase tracking-widest px-3 py-2 rounded border ${
            tab === "b2c" ? "bg-[#0B1E3F] text-white border-[#0B1E3F]" : "border-stone-300"
          }`}
        >
          B2C
        </button>
        {tab === "agenzie" ? (
          <>
            {["", "pending", "active", "suspended"].map((s) => (
              <button
                key={s || "all"}
                type="button"
                onClick={() => {
                  const next = new URLSearchParams(sp);
                  if (s) next.set("status", s);
                  else next.delete("status");
                  setSp(next);
                }}
                className={`text-[10px] uppercase tracking-widest px-2.5 py-1.5 rounded border ${
                  status === s ? "border-[#0B1E3F] text-[#0B1E3F]" : "border-stone-200 text-stone-500"
                }`}
              >
                {s || "tutte"}
              </button>
            ))}
          </>
        ) : null}
      </div>

      <form
        className="flex flex-wrap gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          load();
        }}
      >
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={tab === "b2c" ? "Email, nome, codice…" : "Nome, slug…"}
          className="flex-1 min-w-[200px] border border-stone-300 rounded-md px-3 py-2 text-sm bg-white"
          data-testid="bridge-clients-q"
        />
        <button
          type="submit"
          className="text-xs uppercase tracking-widest px-4 py-2 rounded bg-[#0B1E3F] text-white"
        >
          Cerca
        </button>
      </form>

      <h2 className="text-xs uppercase tracking-widest text-stone-500">{title}</h2>
      {err ? <p className="text-sm text-red-700">{err}</p> : null}
      {busy ? (
        <p className="text-sm text-stone-500">Caricamento…</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-stone-500 border border-dashed border-stone-300 rounded-lg px-4 py-8 text-center">
          Nessun risultato.
        </p>
      ) : tab === "b2c" ? (
        <ul className="bg-white border border-stone-200 rounded-lg divide-y divide-stone-100" data-testid="bridge-b2c-list">
          {items.map((u) => (
            <li key={u.id} className="px-4 py-3 flex flex-wrap gap-3 justify-between">
              <div>
                <p className="font-medium text-stone-900">{u.name || u.email}</p>
                <p className="text-sm text-stone-600">{u.email}</p>
              </div>
              <div className="text-right text-xs text-stone-500">
                {u.client_code ? (
                  <span className="font-mono text-stone-700 block">{u.client_code}</span>
                ) : null}
                <span>{(u.created_at || "").slice(0, 10)}</span>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <ul className="bg-white border border-stone-200 rounded-lg divide-y divide-stone-100" data-testid="bridge-tenants-list">
          {items.map((a) => (
            <li key={a.id}>
              <Link
                to={`${base}/clienti/${a.id}`}
                className="px-4 py-3 flex flex-wrap gap-3 justify-between hover:bg-stone-50 transition"
                data-testid={`bridge-tenant-${a.id}`}
              >
                <div className="min-w-0">
                  <p className="font-medium text-[#0B1E3F] truncate">{a.display_name}</p>
                  <p className="text-sm text-stone-600 truncate">
                    {a.owner_email || "—"} · {a.slug}
                  </p>
                </div>
                <div className="text-right text-xs text-stone-500 space-y-1">
                  <span
                    className={`inline-block uppercase tracking-widest px-2 py-0.5 rounded ${
                      a.activation_status === "pending"
                        ? "bg-amber-50 text-amber-800"
                        : a.activation_status === "suspended"
                          ? "bg-rose-50 text-rose-800"
                          : "bg-emerald-50 text-emerald-800"
                    }`}
                  >
                    {a.activation_status}
                  </span>
                  <p>
                    {a.counts?.clients ?? 0} clienti · {a.counts?.properties ?? 0} immobili ·{" "}
                    {a.counts?.api_keys_active ?? 0} API
                  </p>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

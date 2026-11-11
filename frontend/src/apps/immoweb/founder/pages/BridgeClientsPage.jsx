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
          Archivi piattaforma: agenzie (titolare, P.IVA, PEC, KYC, piano) e account
          ImmobilCloud — base per identificare la clientela (GDPR / obblighi
          contrattuali).
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
        {tab === "agenzie" && items.length > 0 ? (
          <button
            type="button"
            data-testid="bridge-clients-export-csv"
            className="text-xs uppercase tracking-widest px-4 py-2 rounded border border-stone-300 bg-white"
            onClick={() => {
              const cols = [
                "id",
                "display_name",
                "slug",
                "activation_status",
                "plan",
                "owner_name",
                "owner_email",
                "owner_phone",
                "vat_number",
                "fiscal_code",
                "pec",
                "website",
                "city",
                "province",
                "zip",
                "kyc_status",
                "created_at",
              ];
              const esc = (v) => {
                const s = v == null ? "" : String(v);
                return `"${s.replace(/"/g, '""')}"`;
              };
              const rows = items.map((a) =>
                [
                  a.id,
                  a.display_name,
                  a.slug,
                  a.activation_status,
                  a.plan,
                  a.owner_name,
                  a.owner_email,
                  a.owner_phone,
                  a.fiscal?.vat_number,
                  a.fiscal?.fiscal_code,
                  a.pec || a.contact?.pec,
                  a.website || a.contact?.website,
                  a.address?.city,
                  a.address?.province,
                  a.address?.zip,
                  a.kyc_status,
                  (a.created_at || "").slice(0, 10),
                ]
                  .map(esc)
                  .join(",")
              );
              const csv = [cols.join(","), ...rows].join("\n");
              const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
              const url = URL.createObjectURL(blob);
              const link = document.createElement("a");
              link.href = url;
              link.download = `omnia-elenco-clienti-${new Date()
                .toISOString()
                .slice(0, 10)}.csv`;
              document.body.appendChild(link);
              link.click();
              link.parentNode.removeChild(link);
              URL.revokeObjectURL(url);
            }}
          >
            Esporta elenco CSV
          </button>
        ) : null}
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
            <li key={u.id} className="px-4 py-3 flex flex-wrap gap-3 justify-between items-center">
              <div>
                <p className="font-medium text-stone-900">{u.name || u.email}</p>
                <p className="text-sm text-stone-600">{u.email}</p>
              </div>
              <div className="text-right text-xs text-stone-500 space-y-1">
                {u.client_code ? (
                  <span className="font-mono text-stone-700 block">{u.client_code}</span>
                ) : null}
                <span className="block">{(u.created_at || "").slice(0, 10)}</span>
                {u.erased_at || String(u.email || "").includes("@erased.") ? (
                  <span className="text-stone-400 uppercase tracking-widest">già erased</span>
                ) : (
                  <button
                    type="button"
                    className="text-[10px] uppercase tracking-widest text-rose-700 hover:underline"
                    data-testid={`bridge-erase-b2c-${u.id}`}
                    onClick={async () => {
                      const conf = window.prompt(
                        `Anonimizzare ${u.email}? Digita CANCELLA_UTENTE`
                      );
                      if (conf !== "CANCELLA_UTENTE") return;
                      try {
                        await api.post(`/app/ops/bridge/users/${u.id}/erase`, {
                          confirm: "CANCELLA_UTENTE",
                        });
                        await load();
                      } catch {
                        setErr("Erase non riuscito.");
                      }
                    }}
                  >
                    GDPR erase
                  </button>
                )}
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

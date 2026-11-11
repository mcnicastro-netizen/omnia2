import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../../../shared/lib/api";
import Brand from "../../../../shared/components/Brand";

function Kpi({ label, value, to, warn }) {
  const body = (
    <div
      className={`rounded-lg border bg-white px-4 py-4 ${
        warn ? "border-amber-300" : "border-stone-200"
      }`}
    >
      <p className="text-[10px] uppercase tracking-widest text-stone-500">{label}</p>
      <p
        className="mt-2 text-3xl text-[#0B1E3F] font-light"
        style={{ fontFamily: "'Fraunces', Georgia, serif" }}
      >
        {value ?? "—"}
      </p>
    </div>
  );
  return to ? (
    <Link to={to} className="block hover:shadow-sm transition">
      {body}
    </Link>
  ) : (
    body
  );
}

export default function BridgeHomePage() {
  const { lang: langParam } = useParams();
  const lang = langParam || "it";
  const base = `/${lang}/app/ops`;
  const [summary, setSummary] = useState(null);
  const [queue, setQueue] = useState([]);
  const [busy, setBusy] = useState(true);
  const [attivaId, setAttivaId] = useState(null);
  const [msg, setMsg] = useState(null);

  const load = async () => {
    setBusy(true);
    try {
      const [s, q] = await Promise.all([
        api.get("/app/ops/bridge/summary"),
        api.get("/app/ops/activation-queue"),
      ]);
      setSummary(s.data);
      setQueue(q.data?.items || []);
    } catch {
      setSummary(null);
      setQueue([]);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const attiva = async (row) => {
    if (!row?.agency_id) return;
    if (
      !window.confirm(
        `Attivare «${row.display_name || row.slug}»?\n${row.owner_email || ""}\nSblocca CRM, Pro, email.`
      )
    ) {
      return;
    }
    setAttivaId(row.agency_id);
    setMsg(null);
    try {
      const r = await api.post("/app/ops/activate-agency", {
        agency_id: row.agency_id,
        grant_plan: true,
        credits: 2000,
        send_email: true,
        wipe_crm: true,
        note: "cabina_ingresso",
        require_kyc_verified: true,
        require_payment: true,
        issue_login_credential: false,
      });
      setMsg(`Attivata · ${r.data?.display_name || row.display_name}`);
      await load();
    } catch (e) {
      const d = e?.response?.data?.detail;
      setMsg(
        (typeof d === "object" && (d.hint || d.error)) ||
          d ||
          "Errore — apri scheda: KYC + pagamento"
      );
    } finally {
      setAttivaId(null);
    }
  };

  return (
    <div data-testid="bridge-home" className="space-y-10">
      <header>
        <p className="text-[10px] uppercase tracking-[0.3em] text-[#C19A6B] mb-2">
          <Brand>Founder</Brand>
        </p>
        <h1
          className="text-3xl md:text-4xl text-[#0B1E3F] tracking-tight"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        >
          Ingresso
        </h1>
        <p className="mt-2 text-stone-600 max-w-2xl text-sm">
          Prima le richieste di attivazione. Poi lo stato della piattaforma.
        </p>
      </header>

      {busy && !summary ? (
        <p className="text-sm text-stone-500 uppercase tracking-widest">Caricamento…</p>
      ) : null}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="bridge-home-kpis">
        <Kpi
          label="In coda"
          value={summary?.activation_pending}
          to={`${base}/clienti?status=pending`}
          warn={(summary?.activation_pending || 0) > 0}
        />
        <Kpi label="Agenzie" value={summary?.agencies_total} to={`${base}/clienti`} />
        <Kpi label="Utenti B2C" value={summary?.b2c_users} to={`${base}/clienti?tab=b2c`} />
        <Kpi
          label="API attive"
          value={summary?.api_keys_active}
          to={`${base}/api`}
        />
        <Kpi
          label="Alert aperti"
          value={summary?.alerts_unacked}
          to={`${base}/piattaforma`}
          warn={(summary?.alerts_unacked || 0) > 0}
        />
        <Kpi
          label="Backup"
          value={summary?.backup?.status || "—"}
          to={`${base}/piattaforma`}
          warn={summary?.backup?.status && summary.backup.status !== "OK"}
        />
      </div>

      <section
        className="rounded-xl border border-[#0B1E3F]/20 bg-white px-5 py-6 space-y-4"
        data-testid="bridge-activation-queue"
      >
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-xs uppercase tracking-widest text-[#C19A6B]">
              Richieste di attivazione
            </h2>
            <p className="text-sm text-stone-600 mt-1">
              Onboarding completato — email titolare in elenco.
            </p>
          </div>
          <button
            type="button"
            onClick={load}
            className="text-xs uppercase tracking-widest px-3 py-2 rounded border border-stone-300 hover:bg-stone-50"
          >
            Aggiorna
          </button>
        </div>

        {queue.length === 0 ? (
          <p className="text-sm text-stone-500 bg-stone-50 border border-stone-100 rounded px-3 py-3">
            Nessuna richiesta in coda.
          </p>
        ) : (
          <ul className="divide-y divide-stone-100 border border-stone-200 rounded-lg overflow-hidden">
            {queue.map((row) => (
              <li
                key={row.agency_id}
                className="px-4 py-3 flex flex-wrap items-center justify-between gap-3 bg-white"
              >
                <div className="min-w-0">
                  <p className="font-medium text-[#0B1E3F] truncate">
                    {row.display_name || row.slug}
                  </p>
                  <p className="text-sm text-stone-600 truncate">
                    {row.owner_email || "—"}
                    {row.owner_name ? ` · ${row.owner_name}` : ""}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Link
                    to={`${base}/clienti/${row.agency_id}`}
                    className="text-xs uppercase tracking-widest text-stone-500 hover:text-stone-800"
                  >
                    Scheda
                  </Link>
                  <button
                    type="button"
                    disabled={attivaId === row.agency_id}
                    onClick={() => attiva(row)}
                    className="text-sm uppercase tracking-widest px-4 py-2 rounded bg-[#0B1E3F] text-white disabled:opacity-50"
                  >
                    {attivaId === row.agency_id ? "…" : "Attiva"}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
        {msg ? <p className="text-sm text-[#0B1E3F]">{msg}</p> : null}
      </section>
    </div>
  );
}

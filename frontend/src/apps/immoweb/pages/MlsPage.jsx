import React, { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import AgencyShell from "../components/AgencyShell";
import { api } from "../../../shared/lib/api";

/**
 * MLS Network CRM — struttura Agesta (mio / locale / Italia + collaborazioni),
 * look OMNIA (Mediterranean Future).
 */
export default function MlsPage() {
  const { i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const [dash, setDash] = useState(null);
  const [scope, setScope] = useState("mine");
  const [inventory, setInventory] = useState({ items: [], total: 0 });
  const [partners, setPartners] = useState([]);
  const [offers, setOffers] = useState([]);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setErr("");
    try {
      const [d, inv, p, o] = await Promise.all([
        api.get("/app/mls/dashboard"),
        api.get(`/app/mls/inventory?scope=${scope}&limit=24`),
        api.get("/app/mls/partners"),
        api.get("/app/mls/offers?direction=all"),
      ]);
      setDash(d.data);
      setInventory(inv.data);
      setPartners(p.data.items || []);
      setOffers(o.data.items || []);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Impossibile caricare MLS");
    }
  }, [scope]);

  useEffect(() => {
    load();
  }, [load]);

  const join = async () => {
    setBusy(true);
    try {
      await api.post("/app/mls/join", { accept_terms: true });
      await load();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Join fallito");
    } finally {
      setBusy(false);
    }
  };

  const respondOffer = async (id, action) => {
    try {
      await api.post(`/app/mls/offers/${id}/respond`, { action });
      await load();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Azione offerta fallita");
    }
  };

  const respondPartner = async (id, action) => {
    try {
      await api.post(`/app/mls/partners/${id}/respond`, { action });
      await load();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Azione partner fallita");
    }
  };

  return (
    <AgencyShell current="mls">
      <div className="max-w-6xl mx-auto px-4 py-6 space-y-6" data-testid="mls-page">
        <header className="space-y-2">
          <p className="text-xs uppercase tracking-[0.2em] text-sky-800/70">OMNIA Network</p>
          <h1 className="text-3xl font-semibold text-slate-900" style={{ fontFamily: "Georgia, serif" }}>
            MLS
          </h1>
          <p className="text-slate-600 max-w-2xl">
            Collabora con altre agenzie: il tuo inventario condiviso, il network provinciale e nazionale,
            offerte e partnership — anche a volume di rete in crescita.
          </p>
        </header>

        {err ? (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-rose-800 text-sm">{String(err)}</div>
        ) : null}

        {dash && !dash.mls_enabled ? (
          <section className="rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-sky-50 p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h2 className="text-lg font-medium text-slate-900">Attiva OMNIA MLS</h2>
              <p className="text-sm text-slate-600 mt-1">
                Entri nel network multi-agenzia. Potrai condividere gli immobili impostati come pubblici o «solo MLS».
              </p>
            </div>
            <button
              type="button"
              disabled={busy}
              onClick={join}
              className="px-5 py-2.5 rounded-md bg-slate-900 text-white text-sm hover:bg-slate-800 disabled:opacity-50"
              data-testid="mls-join"
            >
              {busy ? "Attivazione…" : "Entra nel network"}
            </button>
          </section>
        ) : null}

        {dash ? (
          <>
            <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <StatCard
                title="Il mio MLS"
                lines={[
                  `${dash.mine.shared} immobili condivisi`,
                  `${dash.mine.exclusive} esclusivi`,
                  `${dash.mine.with_photos} con foto`,
                ]}
              />
              <StatCard
                title={dash.network.label_local}
                lines={[
                  `${dash.network.local_listings} annunci rete locale`,
                  `${dash.network.agencies} agenzie in network`,
                ]}
              />
              <StatCard
                title={dash.network.label_national}
                lines={[
                  `${dash.network.national_listings} annunci Italia`,
                  `${dash.collaborations.partners} partner attivi`,
                ]}
              />
            </section>

            <section className="rounded-xl border border-slate-200 bg-white p-4">
              <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                <h2 className="text-lg font-medium text-slate-900">Collaborazioni</h2>
                <div className="text-sm text-slate-600">
                  {dash.collaborations.invites_pending} inviti · {dash.collaborations.offers_incoming} offerte in arrivo ·{" "}
                  {dash.collaborations.offers_outgoing} inviate
                </div>
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <h3 className="text-sm font-medium text-slate-700 mb-2">Partner</h3>
                  <ul className="space-y-2">
                    {partners.length === 0 ? (
                      <li className="text-sm text-slate-500">Nessun partner ancora.</li>
                    ) : (
                      partners.slice(0, 8).map((p) => (
                        <li key={p.id} className="flex items-center justify-between gap-2 text-sm border border-slate-100 rounded-md px-3 py-2">
                          <span>
                            {p.counterpart?.name || p.counterpart_id}{" "}
                            <span className="text-slate-400">· {p.status}</span>
                          </span>
                          {p.status === "pending" && p.direction === "incoming" ? (
                            <span className="flex gap-1">
                              <button type="button" className="text-emerald-700" onClick={() => respondPartner(p.id, "accept")}>
                                Accetta
                              </button>
                              <button type="button" className="text-rose-700" onClick={() => respondPartner(p.id, "reject")}>
                                Rifiuta
                              </button>
                            </span>
                          ) : null}
                        </li>
                      ))
                    )}
                  </ul>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-slate-700 mb-2">Offerte</h3>
                  <ul className="space-y-2">
                    {offers.length === 0 ? (
                      <li className="text-sm text-slate-500">Nessuna offerta.</li>
                    ) : (
                      offers.slice(0, 8).map((o) => (
                        <li key={o.id} className="flex items-center justify-between gap-2 text-sm border border-slate-100 rounded-md px-3 py-2">
                          <span>
                            {o.property_title || o.property_id}{" "}
                            <span className="text-slate-400">· {o.status}</span>
                          </span>
                          {o.status === "pending" && o.to_agency_id ? (
                            <span className="flex gap-1">
                              <button type="button" className="text-emerald-700" onClick={() => respondOffer(o.id, "accept")}>
                                Accetta
                              </button>
                              <button type="button" className="text-rose-700" onClick={() => respondOffer(o.id, "reject")}>
                                Rifiuta
                              </button>
                            </span>
                          ) : null}
                        </li>
                      ))
                    )}
                  </ul>
                </div>
              </div>
            </section>

            <section className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {[
                  { id: "mine", label: "Il mio MLS" },
                  { id: "local", label: dash.network.label_local },
                  { id: "national", label: "MLS Italia" },
                ].map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setScope(t.id)}
                    className={`px-3 py-1.5 rounded-md text-sm border ${
                      scope === t.id ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-200"
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
                <span className="text-sm text-slate-500 self-center ml-auto">{inventory.total} risultati</span>
              </div>
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {(inventory.items || []).map((item) => (
                  <article key={item.id} className="border border-slate-200 rounded-lg overflow-hidden bg-white">
                    <div
                      className="h-36 bg-slate-100 bg-cover bg-center"
                      style={item.cover_url ? { backgroundImage: `url(${item.cover_url})` } : undefined}
                    />
                    <div className="p-3 space-y-1">
                      <div className="text-xs text-slate-500 uppercase tracking-wide">{item.operation || "—"}</div>
                      <h3 className="font-medium text-slate-900 line-clamp-2">{item.title}</h3>
                      <p className="text-sm text-slate-600">
                        {item.city}
                        {item.province_sigla ? ` (${item.province_sigla})` : ""}
                      </p>
                      <p className="text-sm font-semibold text-slate-900">
                        {item.price != null ? `€ ${Number(item.price).toLocaleString(lang)}` : "Prezzo n.d."}
                      </p>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          </>
        ) : (
          <p className="text-slate-500 text-sm">Caricamento MLS…</p>
        )}
      </div>
    </AgencyShell>
  );
}

function StatCard({ title, lines }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="text-sm uppercase tracking-wide text-slate-500 mb-2">{title}</h2>
      <ul className="space-y-1">
        {lines.map((l) => (
          <li key={l} className="text-slate-900 font-medium">
            {l}
          </li>
        ))}
      </ul>
    </div>
  );
}

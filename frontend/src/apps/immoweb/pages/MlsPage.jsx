import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import AgencyShell from "../components/AgencyShell";
import MlsEmbedKit from "../components/MlsEmbedKit";
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
  const [embedKit, setEmbedKit] = useState(null);
  const [siteMode, setSiteMode] = useState(null);

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
      try {
        const me = await api.get("/app/agencies/me");
        const mode = me.data?.website?.mode;
        setSiteMode(mode || null);
        const slug = me.data?.slug;
        if (d.data?.mls_enabled && slug && (mode === "external" || mode === "keep_brand")) {
          const kit = await api.get(`/mls-box/embed-kit/${slug}`);
          setEmbedKit(kit.data);
        } else {
          setEmbedKit(null);
        }
      } catch {
        setEmbedKit(null);
      }
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

  const leave = async () => {
    if (!window.confirm("Esci dalla rete MLS? Il sito resta su OMNIA ma senza box MLS.")) {
      return;
    }
    setBusy(true);
    try {
      await api.post("/app/mls/leave");
      await load();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Uscita MLS fallita");
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
      <div className="crm-desk max-w-6xl mx-auto space-y-6" data-testid="mls-page">
        <header className="space-y-2">
          <p className="crm-eyebrow" data-testid="mls-crm-eyebrow">
            OMNIA Network
          </p>
          <h1 className="crm-title text-3xl md:text-4xl">MLS</h1>
          <p className="text-crm-muted max-w-2xl text-sm">
            Collabora con altre agenzie: inventario condiviso, rete locale e Italia, offerte e partnership.
          </p>
        </header>

        {err ? (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-rose-800 text-sm">
            {String(err)}
          </div>
        ) : null}

        {dash && !dash.mls_enabled ? (
          <section className="crm-panel p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-crm-mist/60">
            <div>
              <h2 className="text-lg font-medium text-crm-navy">Attiva OMNIA MLS</h2>
              <p className="text-sm text-crm-muted mt-1">
                Entri nel network multi-agenzia. Potrai condividere gli immobili impostati come pubblici o «solo MLS».
              </p>
            </div>
            <button
              type="button"
              disabled={busy}
              onClick={join}
              className="crm-btn-primary px-5 py-2.5 rounded-md text-sm disabled:opacity-50"
              data-testid="mls-join"
            >
              {busy ? "Attivazione…" : "Entra nel network"}
            </button>
          </section>
        ) : null}

        {dash && dash.mls_enabled ? (
          <>
            <div
              data-testid="mls-next-share"
              className="crm-panel px-4 py-3 flex flex-wrap items-center justify-between gap-3 border-crm-navy"
            >
              <p className="text-sm text-crm-navy">
                Rete attiva. Prossimo passo: apri gli immobili e condividili (visibilità rete / pubblici).
              </p>
              <Link
                to={`/${lang}/app/properties`}
                className="crm-btn-ghost px-4 py-2 text-[11px] uppercase tracking-widest rounded-md"
              >
                Vai agli immobili →
              </Link>
            </div>
            <div className="crm-panel flex flex-wrap items-center justify-between gap-3 px-4 py-3">
              <p className="text-sm text-crm-muted">
                {siteMode === "external"
                  ? "Rete attiva. Sul tuo sito: sostituisci solo il box ricerca MLS (codice sotto). Il resto resta com’è."
                  : "Rete attiva: sul sito OMNIA compare il box. Puoi uscire e restare senza rete."}
              </p>
              <button
                type="button"
                disabled={busy}
                onClick={leave}
                className="crm-btn-ghost px-4 py-2 rounded-md text-sm disabled:opacity-50"
                data-testid="mls-leave"
              >
                {busy ? "Uscita…" : "Esci dalla rete MLS"}
              </button>
            </div>
            {embedKit ? <MlsEmbedKit kit={embedKit} /> : null}
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

            <section className="crm-panel p-4">
              <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                <h2 className="text-lg font-medium text-crm-navy">Collaborazioni</h2>
                <div className="text-sm text-crm-muted">
                  {dash.collaborations.invites_pending} inviti · {dash.collaborations.offers_incoming} offerte in
                  arrivo · {dash.collaborations.offers_outgoing} inviate
                </div>
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <h3 className="text-sm font-medium text-crm-navy mb-2">Partner</h3>
                  <ul className="space-y-2">
                    {partners.length === 0 ? (
                      <li className="text-sm text-crm-muted">Nessun partner ancora.</li>
                    ) : (
                      partners.slice(0, 8).map((p) => (
                        <li
                          key={p.id}
                          className="flex items-center justify-between gap-2 text-sm border border-crm-line rounded-md px-3 py-2"
                        >
                          <span>
                            {p.counterpart?.name || p.counterpart_id}{" "}
                            <span className="text-crm-muted">· {p.status}</span>
                          </span>
                          {p.status === "pending" && p.direction === "incoming" ? (
                            <span className="flex gap-1">
                              <button
                                type="button"
                                className="text-crm-navy underline"
                                onClick={() => respondPartner(p.id, "accept")}
                              >
                                Accetta
                              </button>
                              <button
                                type="button"
                                className="text-rose-700"
                                onClick={() => respondPartner(p.id, "reject")}
                              >
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
                  <h3 className="text-sm font-medium text-crm-navy mb-2">Offerte</h3>
                  <ul className="space-y-2">
                    {offers.length === 0 ? (
                      <li className="text-sm text-crm-muted">Nessuna offerta.</li>
                    ) : (
                      offers.slice(0, 8).map((o) => (
                        <li
                          key={o.id}
                          className="flex items-center justify-between gap-2 text-sm border border-crm-line rounded-md px-3 py-2"
                        >
                          <span>
                            {o.property_title || o.property_id}{" "}
                            <span className="text-crm-muted">· {o.status}</span>
                          </span>
                          {o.status === "pending" && o.to_agency_id ? (
                            <span className="flex gap-1">
                              <button
                                type="button"
                                className="text-crm-navy underline"
                                onClick={() => respondOffer(o.id, "accept")}
                              >
                                Accetta
                              </button>
                              <button
                                type="button"
                                className="text-rose-700"
                                onClick={() => respondOffer(o.id, "reject")}
                              >
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
                      scope === t.id ? "crm-btn-primary border-crm-navy" : "crm-btn-ghost"
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
                <span className="text-sm text-crm-muted self-center ml-auto">{inventory.total} risultati</span>
              </div>
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {(inventory.items || []).map((item) => {
                  const href =
                    scope === "mine"
                      ? `/${lang}/app/properties/${item.id}`
                      : `/${lang}/cloud/property/${item.id}`;
                  return (
                    <Link
                      key={item.id}
                      to={href}
                      data-testid={`mls-inventory-card-${item.id}`}
                      className="crm-panel overflow-hidden block hover:border-crm-navy/40 transition-colors"
                    >
                      <div
                        className="h-36 bg-crm-mist bg-cover bg-center"
                        style={item.cover_url ? { backgroundImage: `url(${item.cover_url})` } : undefined}
                      />
                      <div className="p-3 space-y-1">
                        <div className="text-xs text-crm-gold uppercase tracking-wide">
                          {item.operation || "—"}
                        </div>
                        <h3 className="font-medium text-crm-navy line-clamp-2">{item.title}</h3>
                        <p className="text-sm text-crm-muted">
                          {item.city}
                          {item.province_sigla ? ` (${item.province_sigla})` : ""}
                        </p>
                        <p className="text-sm font-semibold text-crm-navy">
                          {item.price != null ? `€ ${Number(item.price).toLocaleString(lang)}` : "Prezzo n.d."}
                        </p>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </section>
          </>
        ) : null}

        {!dash ? <p className="text-crm-muted text-sm">Caricamento MLS…</p> : null}
      </div>
    </AgencyShell>
  );
}

function StatCard({ title, lines }) {
  return (
    <div className="crm-panel p-4">
      <h2 className="crm-eyebrow mb-2">{title}</h2>
      <ul className="space-y-1">
        {lines.map((l) => (
          <li key={l} className="text-crm-navy font-medium text-sm">
            {l}
          </li>
        ))}
      </ul>
    </div>
  );
}

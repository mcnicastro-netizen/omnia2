import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api } from "../../../shared/lib/api";
import AgencyShell from "../components/AgencyShell";
import Brand from "../../../shared/components/Brand";

/**
 * PortalsPage — M2.6a Publishing Center (D-052).
 * Dashboard 2-tab: Attivi (with connection status) · Disponibili (from catalog).
 * Activation: 1-click for portals without credentials, modal form otherwise.
 */
export default function PortalsPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const [catalog, setCatalog] = useState([]);
  const [connections, setConnections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("active");
  const [modal, setModal] = useState(null); // {portal, creds:{}}
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [complianceModal, setComplianceModal] = useState(null); // {connection, data}
  const [syncing, setSyncing] = useState(null); // connection id currently syncing
  const [syncResult, setSyncResult] = useState(null); // last sync result banner

  const load = async () => {
    setLoading(true);
    try {
      const [cat, conn] = await Promise.all([
        api.get("/app/publishing/catalog"),
        api.get("/app/publishing/connections"),
      ]);
      setCatalog(cat.data.items || []);
      setConnections(conn.data.items || []);
    } catch (e) {
      setError(e?.response?.data?.detail || "load_error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const activePortalSlugs = new Set(connections.map((c) => c.portal_slug));
  const available = catalog.filter((p) => !activePortalSlugs.has(p.slug));
  const portalMap = Object.fromEntries(catalog.map((p) => [p.slug, p]));

  const openActivate = (portal) => {
    const creds = {};
    (portal.credential_fields || []).forEach((f) => { creds[f.name] = ""; });
    setModal({ portal, creds });
    setError(null);
  };

  const submitActivate = async () => {
    if (!modal) return;
    setBusy(true); setError(null);
    try {
      await api.post("/app/publishing/connections", {
        portal_slug: modal.portal.slug,
        credentials: modal.creds,
      });
      setModal(null);
      await load();
    } catch (e) {
      setError(e?.response?.data?.detail || "activate_error");
    } finally { setBusy(false); }
  };

  const deactivate = async (id) => {
    if (!confirm(t("portals.confirm_deactivate") || "Disattivare questo portale?")) return;
    try {
      await api.delete(`/app/publishing/connections/${id}`);
      await load();
    } catch (e) { setError(e?.response?.data?.detail || "delete_error"); }
  };

  const syncNow = async (conn) => {
    setSyncing(conn.id);
    setError(null);
    setSyncResult(null);
    try {
      const r = await api.post(`/app/publishing/connections/${conn.id}/sync-now`);
      setSyncResult({ portal: conn.portal_slug, ...r.data });
      await load();
    } catch (e) {
      setError(e?.response?.data?.detail || "sync_error");
    } finally { setSyncing(null); }
  };

  const openCompliance = async (conn) => {
    setError(null);
    try {
      const r = await api.get(`/app/publishing/connections/${conn.id}/compliance`);
      setComplianceModal({ connection: conn, data: r.data });
    } catch (e) {
      setError(e?.response?.data?.detail || "compliance_error");
    }
  };

  return (
    <AgencyShell current="publishing">
      <section data-testid="portals-page" className="space-y-8">
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-2">
            <Brand>ImmoWeb · Publishing Center</Brand>
          </p>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <h1 className="text-3xl md:text-4xl tracking-tight" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              {t("portals.title") || "Portali Immobiliari"}
            </h1>
            <div className="flex gap-2 flex-wrap">
              <Link
                to={`/${lang}/app/publishing/social`}
                data-testid="open-social-publisher-btn"
                className="px-4 py-2 text-xs uppercase tracking-widest border border-[#1F6B5C] text-[#1F6B5C] hover:bg-[#1F6B5C] hover:text-white transition"
              >
                Canali social
              </Link>
              <Link
                to={`/${lang}/app/publishing/wizard`}
                data-testid="add-custom-portal-btn"
                className="px-4 py-2 text-xs uppercase tracking-widest bg-[#1F6B5C] text-white hover:bg-[#0B1E3F] transition"
              >
                {t("portal_wizard.add_custom_portal_cta")}
              </Link>
            </div>
          </div>
          <p className="text-sm text-stone-600 mt-2 max-w-2xl">
            {t("portals.subtitle") ||
              "Attiva i portali su cui vuoi pubblicare gli annunci. OMNIA genera un feed XML aggiornato in tempo reale — ogni portale scarica autonomamente ogni notte."}
          </p>
          <div className="mt-3 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-3 py-2 max-w-2xl">
            ⚠️ <strong>Compliance HARD attiva + Sync automatico</strong>: solo gli annunci con prezzo, superficie, indirizzo, classe energetica valida e almeno 3 foto vengono pubblicati. Il sync gira automaticamente ogni notte alle 06:00 UTC su tutti i portali attivi. Clicca "Compliance" per vedere quali immobili sono bloccati e perché.
          </div>
        </div>

        {/* Metrics header */}
        <div className="grid grid-cols-3 gap-4 max-w-2xl">
          <MetricBox label={t("portals.total_active") || "Portali attivi"} value={connections.filter((c) => c.status === "active").length} testid="metric-active" />
          <MetricBox label={t("portals.available") || "Disponibili"} value={available.length} testid="metric-available" />
          <MetricBox label={t("portals.catalog_total") || "Catalogo totale"} value={catalog.length} testid="metric-catalog" />
        </div>

        {error && <div data-testid="portals-error" className="text-sm text-red-700 bg-red-50 border border-red-300 rounded p-3">{error}</div>}

        {syncResult && (
          <div data-testid="sync-result-banner" className={`text-sm border rounded p-3 flex items-start gap-3 ${syncResult.ok ? "text-emerald-800 bg-emerald-50 border-emerald-200" : "text-amber-800 bg-amber-50 border-amber-200"}`}>
            <div className="flex-1">
              <strong>Sync {syncResult.portal}</strong> — {syncResult.publishable ?? 0} immobili pubblicabili, {syncResult.blocked ?? 0} bloccati dal validatore compliance.
              {syncResult.log?.error_message && <div className="text-xs mt-1 text-stone-600">{syncResult.log.error_message}</div>}
              {syncResult.integration_type === "api_push" && <div className="text-xs mt-1 text-stone-600">ℹ️ Portale push: integrazione reale in arrivo con M2.6c/d — per ora simulata.</div>}
            </div>
            <button onClick={() => setSyncResult(null)} className="text-xs text-stone-500 hover:text-stone-800">✕</button>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-6 border-b border-stone-200">
          {["active", "available"].map((k) => (
            <button
              key={k}
              onClick={() => setTab(k)}
              data-testid={`portals-tab-${k}`}
              className={`pb-3 text-xs uppercase tracking-widest border-b-2 -mb-px transition ${
                tab === k ? "border-stone-900 text-stone-900" : "border-transparent text-stone-500 hover:text-stone-800"
              }`}
            >
              {k === "active" ? `${t("portals.active") || "Attivi"} (${connections.length})` : `${t("portals.disponibili") || "Disponibili"} (${available.length})`}
            </button>
          ))}
        </div>

        {/* Table */}
        <div className="bg-white border border-stone-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-stone-50 text-[10px] uppercase tracking-widest text-stone-500">
              <tr>
                <th className="text-left px-4 py-3">Portale</th>
                <th className="text-left px-4 py-3">Categoria</th>
                <th className="text-left px-4 py-3">Modalità</th>
                <th className="text-left px-4 py-3">Traffico</th>
                <th className="text-left px-4 py-3">Stato</th>
                <th className="text-right px-4 py-3">Azioni</th>
              </tr>
            </thead>
            <tbody data-testid="portals-table-body">
              {loading ? (
                <tr><td colSpan={6} className="px-4 py-6 text-stone-500 text-center">…</td></tr>
              ) : tab === "active" ? (
                connections.length === 0 ? (
                  <tr><td colSpan={6} className="px-4 py-6 text-stone-500 text-center" data-testid="portals-empty-active">
                    Nessun portale attivo. Vai alla tab "Disponibili" per attivarne uno.
                  </td></tr>
                ) : connections.map((c) => {
                  const p = portalMap[c.portal_slug] || {};
                  const lastSync = c.last_sync_at ? new Date(c.last_sync_at).toLocaleString("it-IT") : "mai";
                  return (
                    <tr key={c.id} data-testid={`portal-conn-${c.portal_slug}`} className="border-t border-stone-200 hover:bg-stone-50">
                      <td className="px-4 py-3">
                        <div className="font-medium">{p.name || c.portal_slug}</div>
                        <div className="text-[10px] text-stone-500 mt-0.5" data-testid={`portal-lastsync-${c.portal_slug}`}>
                          Ultimo sync: {lastSync}
                          {c.items_published > 0 && ` · ${c.items_published} pubblicati`}
                          {c.items_failed > 0 && ` · ${c.items_failed} bloccati`}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-stone-600 text-xs">{p.category || "—"}</td>
                      <td className="px-4 py-3 text-stone-600 text-xs">{p.integration_type || "—"}</td>
                      <td className="px-4 py-3 text-stone-600">{"★".repeat(p.traffic_score || 0)}</td>
                      <td className="px-4 py-3">
                        <StatusBadge status={c.status} />
                        {c.last_error && (
                          <div className="text-[10px] text-red-600 mt-1 max-w-[180px] truncate" title={c.last_error} data-testid={`portal-lasterror-${c.portal_slug}`}>
                            ⚠ {c.last_error}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex justify-end gap-2 items-center">
                          <button
                            onClick={() => syncNow(c)}
                            disabled={syncing === c.id || c.status === "disabled"}
                            data-testid={`portal-sync-${c.portal_slug}`}
                            className="text-[10px] uppercase tracking-widest bg-stone-800 text-white px-2 py-1 rounded hover:bg-stone-900 disabled:opacity-40"
                          >
                            {syncing === c.id ? "…" : "Sync"}
                          </button>
                          <button
                            onClick={() => openCompliance(c)}
                            data-testid={`portal-compliance-${c.portal_slug}`}
                            className="text-[10px] uppercase tracking-widest border border-stone-300 text-stone-700 px-2 py-1 rounded hover:bg-stone-100"
                          >
                            Compliance
                          </button>
                          <button
                            onClick={() => deactivate(c.id)}
                            data-testid={`portal-deactivate-${c.portal_slug}`}
                            className="text-[10px] uppercase tracking-widest text-red-600 hover:text-red-800"
                          >
                            Disattiva
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                available.length === 0 ? (
                  <tr><td colSpan={6} className="px-4 py-6 text-stone-500 text-center">Tutti i portali del catalogo sono già attivi.</td></tr>
                ) : available.map((p) => (
                  <tr key={p.slug} data-testid={`portal-catalog-${p.slug}`} className="border-t border-stone-200 hover:bg-stone-50">
                    <td className="px-4 py-3 font-medium">{p.name}</td>
                    <td className="px-4 py-3 text-stone-600 text-xs">{p.category}</td>
                    <td className="px-4 py-3 text-stone-600 text-xs">{p.integration_type}</td>
                    <td className="px-4 py-3 text-stone-600">{"★".repeat(p.traffic_score || 0)}</td>
                    <td className="px-4 py-3 text-stone-500 text-xs">{p.notes?.substring(0, 40) || "—"}</td>
                    <td className="px-4 py-3 text-right">
                      <button onClick={() => openActivate(p)} data-testid={`portal-activate-${p.slug}`} className="text-xs uppercase tracking-widest bg-emerald-700 text-white px-3 py-1.5 rounded hover:bg-emerald-800">Attiva</button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <details className="text-xs text-stone-600 max-w-2xl">
          <summary className="cursor-pointer">Come funziona</summary>
          <div className="mt-2 space-y-1 bg-stone-50 border border-stone-200 rounded p-3">
            <p>1. Attivi un portale qui e (se richiesto) inserisci le credenziali del tuo account presso quel portale</p>
            <p>2. OMNIA genera automaticamente un feed XML alla tua URL agenzia (per portali "pull") o pubblica via API (per portali "push")</p>
            <p>3. Il <strong>sync automatico</strong> gira ogni notte alle 06:00 UTC e sincronizza tutti i portali attivi. Puoi anche forzare un sync manuale con il pulsante "Sync"</p>
            <p>4. Il validatore <strong>Compliance</strong> controlla ogni immobile prima della pubblicazione: se manca prezzo, superficie, APE, indirizzo o 3+ foto viene escluso automaticamente (regola HARD, obbligo D.Lgs 192/2005 + AGCM)</p>
            <p>5. Clicca "Compliance" su un portale attivo per vedere il dettaglio degli immobili bloccati e i motivi</p>
          </div>
        </details>

        {/* Compliance dashboard modal (M2.6b) */}
        {complianceModal && (
          <div data-testid="portal-compliance-modal" className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={() => setComplianceModal(null)}>
            <div className="bg-white rounded-lg max-w-2xl w-full p-6 max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
              <div className="flex justify-between items-start mb-4">
                <div>
                  <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-1">Compliance</p>
                  <h3 className="text-xl" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                    {portalMap[complianceModal.connection.portal_slug]?.name || complianceModal.connection.portal_slug}
                  </h3>
                </div>
                <button onClick={() => setComplianceModal(null)} className="text-stone-500 hover:text-stone-800">✕</button>
              </div>

              <div className="grid grid-cols-4 gap-3 mb-6" data-testid="compliance-metrics">
                <MetricBox label="Totale" value={complianceModal.data.summary.total} testid="compliance-total" />
                <MetricBox label="Pubblicabili" value={complianceModal.data.summary.publishable} testid="compliance-publishable" />
                <MetricBox label="Bloccati" value={complianceModal.data.summary.blocked} testid="compliance-blocked" />
                <MetricBox label="Con warning" value={complianceModal.data.summary.with_warnings} testid="compliance-warnings" />
              </div>

              {complianceModal.data.summary.top_hard_reasons?.length > 0 && (
                <div className="mb-6">
                  <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-2">Motivi blocco più frequenti</p>
                  <div className="space-y-1">
                    {complianceModal.data.summary.top_hard_reasons.map(([reason, count]) => (
                      <div key={reason} className="flex justify-between text-xs bg-red-50 border border-red-200 rounded px-3 py-1.5">
                        <span className="font-medium">{REASON_LABELS[reason] || reason}</span>
                        <span className="text-red-700">{count} immobili</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {complianceModal.data.blocked_details?.length > 0 && (
                <div>
                  <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-2">
                    Immobili bloccati (primi {complianceModal.data.blocked_details.length})
                  </p>
                  <div className="space-y-1" data-testid="compliance-blocked-list">
                    {complianceModal.data.blocked_details.map((b) => (
                      <div key={b.id} className="text-xs border border-stone-200 rounded px-3 py-2">
                        <div className="flex justify-between">
                          <span className="font-medium truncate">{b.title || b.reference || b.id}</span>
                          <a href={`/${document.documentElement.lang || "it"}/app/properties/${b.id}`} className="text-emerald-700 hover:underline ml-2 shrink-0">Correggi →</a>
                        </div>
                        <div className="text-stone-500 mt-1">
                          {b.reasons.map((r) => REASON_LABELS[r] || r).join(" · ")}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {complianceModal.data.summary.publishable === complianceModal.data.summary.total && complianceModal.data.summary.total > 0 && (
                <p className="text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded p-3">
                  ✅ Tutti gli immobili attivi sono conformi e pubblicabili.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Activation modal */}
        {modal && (
          <div data-testid="portal-activate-modal" className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={() => setModal(null)}>
            <div className="bg-white rounded-lg max-w-md w-full p-6" onClick={(e) => e.stopPropagation()}>
              <h3 className="text-lg mb-1" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>Attiva {modal.portal.name}</h3>
              <p className="text-xs text-stone-500 mb-4">{modal.portal.notes}</p>
              {(modal.portal.credential_fields || []).length === 0 ? (
                <p className="text-sm text-stone-600 mb-4">Nessuna credenziale richiesta — attivazione immediata.</p>
              ) : (
                <div className="space-y-3 mb-4">
                  {modal.portal.credential_fields.map((f) => (
                    <div key={f.name}>
                      <label className="text-xs text-stone-500 block mb-1">{f.label}</label>
                      <input
                        type={f.type === "email" ? "email" : "text"}
                        data-testid={`portal-cred-${f.name}`}
                        value={modal.creds[f.name] || ""}
                        onChange={(e) => setModal({ ...modal, creds: { ...modal.creds, [f.name]: e.target.value } })}
                        className="w-full border border-stone-300 rounded px-3 py-2 text-sm"
                      />
                    </div>
                  ))}
                </div>
              )}
              <div className="flex justify-end gap-2">
                <button onClick={() => setModal(null)} className="text-xs uppercase tracking-widest text-stone-500 hover:text-stone-800 px-3 py-2">Annulla</button>
                <button onClick={submitActivate} disabled={busy} data-testid="portal-modal-confirm" className="text-xs uppercase tracking-widest bg-emerald-700 text-white px-4 py-2 rounded hover:bg-emerald-800 disabled:opacity-40">
                  {busy ? "…" : "Attiva portale"}
                </button>
              </div>
            </div>
          </div>
        )}
      </section>
    </AgencyShell>
  );
}

function MetricBox({ label, value, testid }) {
  return (
    <div className="bg-white border border-stone-200 rounded-lg px-4 py-3" data-testid={testid}>
      <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-1">{label}</p>
      <p className="text-2xl font-medium" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>{value}</p>
    </div>
  );
}

function StatusBadge({ status }) {
  const styles = {
    active: "bg-emerald-100 text-emerald-800",
    pending: "bg-amber-100 text-amber-800",
    error: "bg-red-100 text-red-800",
    disabled: "bg-stone-200 text-stone-600",
  };
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-[10px] uppercase tracking-widest ${styles[status] || styles.disabled}`}>
      {status}
    </span>
  );
}

// M2.6b — human-readable labels for compliance reasons.
// Kept in Italian; i18n keys can wrap these later if EN/ES are needed.
const REASON_LABELS = {
  missing_price: "Prezzo mancante",
  missing_rent: "Canone mensile mancante",
  missing_surface: "Superficie (mq) mancante",
  missing_energy_class: "Classe energetica APE mancante",
  invalid_energy_class: "Classe energetica non valida",
  less_than_3_photos: "Meno di 3 foto",
  no_valid_photo_url: "Foto senza URL valido",
  missing_address: "Indirizzo incompleto (città/provincia)",
  title_too_short: "Titolo troppo corto (<10 caratteri)",
  description_too_short: "Descrizione troppo corta (<50 caratteri)",
  rooms_not_specified: "Numero locali non indicato",
  ipe_missing: "IPE (indice prestazione) non indicato",
};

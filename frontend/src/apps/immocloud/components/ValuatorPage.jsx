/* OMNIA — ImmobilCloud Valuator (dual-tier · task B2C-VAL-01)
 *
 * Path: /it/cloud/valutatore
 *
 * TIER BASE (lead magnet): stima rapida GRATIS · 1×/12 mesi · richiede login + email verificata · NO PDF · NO merito UNI
 * TIER UNI 10750 + PDF: €2,99 one-shot Stripe · include superficie commerciale + coefficienti di merito + report PDF
 *
 * Agenti B2B (con agency_id): pass-through — copy "Usa crediti agenzia" invece di €2,99.
 *
 * Query params pre-fill supportati: ?tier=base|uni&city=...&property_type=...&surface_sqm=...
 */
import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import AddressAutocomplete from "./AddressAutocomplete";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api/cloud/valuator`;
const AUTH_ME = `${BACKEND_URL}/api/auth/me`;
const STATUS_URL = `${BACKEND_URL}/api/billing/b2c/valuator-status`;
const CHECKOUT_URL = `${BACKEND_URL}/api/billing/b2c/checkout`;
const PDF_URL = `${BACKEND_URL}/api/cloud/valuator/report-pdf`;

const PROPERTY_TYPES = ["appartamento", "attico", "loft", "villa", "monolocale", "rustico_casale", "ufficio", "negozio", "garage_box"];
const CONDITIONS = ["nuovo", "ristrutturato", "ottimo", "buono", "abitabile", "da_ristrutturare", "ruderi_da_demolire"];
const ENERGY_CLASSES = ["A4", "A3", "A2", "A1", "A", "B", "C", "D", "E", "F", "G"];
const FLOOR_CLASSES = ["seminterrato", "piano_terra", "piano_1", "piano_intermedio", "ultimo_no_asc", "ultimo_con_asc", "attico_panoramico"];
const EXPOSURES = ["sud", "sud_est", "sud_ovest", "est", "ovest", "nord_est", "nord_ovest", "nord", "cieca", "doppia_esp"];
const VIEWS = ["interno", "cortile", "strada", "verde", "panoramico", "mare", "lago_montagna"];
const HEATINGS = ["autonomo", "centralizzato", "pompa_calore", "assente"];
const ELEVATORS = ["presente", "presente_piano_alto", "assente_piano_basso", "assente_piano_alto"];

const emptyForm = { city: "", zone: "", address: "", property_type: "appartamento", surface_sqm: "", condition: "buono", energy_class: "", floor: "" };
const emptyPro = {
  veranda_mq: "", terrazzo_mq: "", balcone_mq: "", cantina_mq: "", soffitta_mq: "",
  box_auto_mq: "", posto_auto_scoperto_mq: "", giardino_villa_mq: "", giardino_condom_mq: "",
  taverna_mq: "", mansarda_abitabile_mq: "",
  floor_class: "", exposure: "", view: "", heating: "", elevator: "", year_built: "",
  vincolo_storico: false, vincolo_paesag: false, locazione_libera_breve: false, locazione_lunga: false, nuda_proprieta: false,
};

function useQuery() {
  const { search } = useLocation();
  return useMemo(() => Object.fromEntries(new URLSearchParams(search)), [search]);
}

async function fetchJson(url, opts = {}) {
  const r = await fetch(url, { credentials: "include", ...opts, headers: { "Content-Type": "application/json", ...(opts.headers || {}) } });
  const text = await r.text();
  let body = null;
  try { body = text ? JSON.parse(text) : null; } catch { body = { raw: text }; }
  return { ok: r.ok, status: r.status, body, response: r };
}

export default function ValuatorPage() {
  const { t } = useTranslation();
  const query = useQuery();

  const [tier, setTier] = useState(query.tier === "uni" ? "uni" : "base");
  const [form, setForm] = useState({ ...emptyForm, ...pickPrefill(query) });
  const [pro, setPro] = useState(emptyPro);
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(false);
  const [pdfBusy, setPdfBusy] = useState(false);
  const [checkoutBusy, setCheckoutBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [payloadHash, setPayloadHash] = useState(null);
  const [error, setError] = useState(null);
  const resultRef = useRef(null);

  // Load user + billing status
  useEffect(() => {
    (async () => {
      const me = await fetchJson(AUTH_ME);
      if (me.ok) setUser(me.body);
      if (me.ok) {
        const st = await fetchJson(STATUS_URL);
        if (st.ok) setStatus(st.body);
      }
    })();
  }, []);

  const isAgent = !!(user && (user.agency_id || (user.agency_ids && user.agency_ids.length)));
  const isB2C = !!(user && !isAgent);
  const priceLabel = isAgent ? t("valuator.tier_uni_price_agent", "12 crediti agenzia") : (t("valuator.tier_uni_price", "€2,99 · report professionale"));

  function pickPrefill(q) {
    const p = {};
    if (q.city) p.city = q.city;
    if (q.property_type) p.property_type = q.property_type;
    if (q.surface_sqm) p.surface_sqm = q.surface_sqm;
    return p;
  }

  function buildPayload(includePro) {
    const p = {
      city: form.city, property_type: form.property_type,
      surface_sqm: Number(form.surface_sqm),
    };
    if (form.zone) p.zone = form.zone;
    if (form.address) p.address = form.address;
    if (form.condition) p.condition = form.condition;
    if (form.energy_class) p.energy_class = form.energy_class;
    if (form.floor !== "" && form.floor !== null) p.floor = Number(form.floor);
    if (includePro) {
      const cs = {};
      ["veranda_mq", "terrazzo_mq", "balcone_mq", "cantina_mq", "soffitta_mq", "box_auto_mq", "posto_auto_scoperto_mq", "giardino_villa_mq", "giardino_condom_mq", "taverna_mq", "mansarda_abitabile_mq"].forEach(k => {
        if (pro[k] && Number(pro[k]) > 0) cs[k] = Number(pro[k]);
      });
      if (Object.keys(cs).length) p.commercial_surfaces = cs;
      const merit = {};
      ["floor_class", "exposure", "view", "heating", "elevator"].forEach(k => { if (pro[k]) merit[k] = pro[k]; });
      if (pro.year_built && Number(pro.year_built) > 1700) merit.year_built = Number(pro.year_built);
      ["vincolo_storico", "vincolo_paesag", "locazione_libera_breve", "locazione_lunga", "nuda_proprieta"].forEach(k => { if (pro[k]) merit[k] = true; });
      if (Object.keys(merit).length) p.merit = merit;
    }
    return p;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!user) {
      setError({ code: "login_required", message: t("valuator.login_required", "Accedi o registrati per usare il valutatore") });
      return;
    }
    if (isB2C && !user.email_verified) {
      setError({ code: "email_verification_required", message: t("valuator.email_verify_required", "Verifica l'email per usare la stima gratuita") });
      return;
    }
    setBusy(true); setError(null); setResult(null); setPayloadHash(null);
    const includePro = tier === "uni";
    const payload = buildPayload(includePro);
    const r = await fetchJson(API, { method: "POST", body: JSON.stringify(payload) });
    setBusy(false);
    if (r.ok) {
      setResult({ ...r.body, _tier: tier });
      if (r.body && r.body.payload_hash) setPayloadHash(r.body.payload_hash);
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    } else {
      const d = r.body?.detail || {};
      if (r.status === 402 && d.product_key) setPayloadHash(d.payload_hash || null);
      setError({ code: d.code || `http_${r.status}`, message: d.message || t("valuator.error_generic", "Errore durante la stima"), reset_at: d.reset_at, product_key: d.product_key, price_eur: d.price_eur, upsell_product_key: d.upsell_product_key });
    }
  }

  async function handleCheckout(kind) {
    // kind: 'uni' (form submit fallback) or 'upsell' (from base result)
    if (!user) {
      window.location.href = `/it/cloud/login?next=${encodeURIComponent(window.location.pathname + window.location.search)}`;
      return;
    }
    setCheckoutBusy(true);
    const payload = buildPayload(true);
    // If no pro data was filled (e.g. upsell from base), send minimal UNI hint (still needs merit at min)
    if (!payload.merit && !payload.commercial_surfaces) {
      // For upsell without pro fields, still send valid data — user will complete on the UNI tab
      setTier("uni");
      setCheckoutBusy(false);
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    // Compute payload_hash server-side by attempting the estimate → 402 returns hash
    const preflight = await fetchJson(API, { method: "POST", body: JSON.stringify(payload) });
    let ph = payloadHash;
    if (!ph && preflight.status === 402) ph = preflight.body?.detail?.payload_hash;
    const success = `${window.location.origin}/it/cloud/checkout/success`;
    const cancel = `${window.location.origin}/it/cloud/checkout/cancel`;
    const r = await fetchJson(CHECKOUT_URL, {
      method: "POST",
      body: JSON.stringify({ product_key: "b2c_valuator_uni_pdf", success_url: success, cancel_url: cancel, payload_hash: ph }),
    });
    setCheckoutBusy(false);
    if (r.ok && r.body?.checkout_url) {
      // Save form state to sessionStorage for post-checkout resume
      sessionStorage.setItem("omnia_valuator_pending", JSON.stringify({ form, pro, tier: "uni", ph }));
      window.location.href = r.body.checkout_url;
    } else {
      setError({ code: r.body?.detail?.code || "checkout_error", message: r.body?.detail?.message || t("valuator.checkout_error", "Impossibile avviare il pagamento") });
    }
  }

  async function handleDownloadPdf() {
    if (pdfBusy || !result) return;
    setPdfBusy(true);
    const payload = buildPayload(true);
    const r = await fetch(PDF_URL, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    if (r.ok) {
      const blob = await r.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `valutazione-${(form.city || "immobile").toLowerCase().replace(/\s+/g, "-")}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } else {
      const b = await r.json().catch(() => ({}));
      if (r.status === 402) {
        setError({ code: "payment_required", message: t("valuator.pdf_paywall", "Il PDF richiede il pagamento €2,99"), price_eur: 2.99 });
      } else {
        setError({ code: b?.detail?.code || "pdf_error", message: b?.detail?.message || t("valuator.pdf_error", "Errore download PDF") });
      }
    }
    setPdfBusy(false);
  }

  const canSubmit = form.city && form.surface_sqm && Number(form.surface_sqm) >= 10;

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="mb-6">
          <Link to="/it/cloud" className="text-sm text-stone-600 hover:text-stone-900" data-testid="valuator-back">← {t("common.back", "Torna al portale")}</Link>
          <h1 className="mt-2 text-3xl font-serif text-stone-900" data-testid="valuator-title">{t("valuator.page_title", "Valutatore immobiliare")}</h1>
          <p className="mt-2 text-stone-600 max-w-2xl">{t("valuator.page_subtitle", "Scegli fra stima rapida gratuita o valutazione professionale UNI 10750 con report PDF.")}</p>
        </div>

        {!user && (
          <div className="mb-6 p-4 rounded-lg border border-amber-300 bg-amber-50 text-amber-900" data-testid="valuator-anon-banner">
            {t("valuator.anon_banner", "Per usare il valutatore devi essere registrato su ImmobilCloud.")}
            <Link to="/it/cloud/login" className="ml-2 underline font-medium">{t("common.login", "Accedi")}</Link>
            <span> · </span>
            <Link to="/it/cloud/register" className="underline font-medium">{t("common.register", "Registrati")}</Link>
          </div>
        )}

        {/* Tier tabs */}
        <div className="grid md:grid-cols-2 gap-4 mb-6" data-testid="valuator-tier-cards">
          <TierCard
            testid="tier-base-card"
            active={tier === "base"}
            title={t("valuator.tier_base_title", "Stima rapida")}
            subtitle={t("valuator.tier_base_subtitle", "1 valutazione gratuita ogni 12 mesi")}
            price={t("valuator.tier_base_price", "GRATIS")}
            onClick={() => setTier("base")}
            note={status?.base_remaining === 0 ? t("valuator.base_limit_reached_short", "Limite raggiunto — riprova più avanti") : null}
          />
          <TierCard
            testid="tier-uni-card"
            active={tier === "uni"}
            title={t("valuator.tier_uni_title", "UNI 10750 + PDF")}
            subtitle={t("valuator.tier_uni_subtitle", "Superficie commerciale · merito · report brandizzato")}
            price={priceLabel}
            onClick={() => setTier("uni")}
            highlight
          />
        </div>

        <form onSubmit={handleSubmit} className="grid md:grid-cols-2 gap-6 bg-white border border-stone-200 rounded-lg p-6" data-testid="valuator-form">
          {/* Left: base fields */}
          <div className="space-y-4">
            <h3 className="font-serif text-lg text-stone-800">{t("valuator.section_location", "Ubicazione")}</h3>
            <AddressAutocomplete
              value={form.address}
              onSelect={({ address, city, zone }) => setForm(f => ({ ...f, address: address || "", city: city || f.city, zone: zone || f.zone }))}
              placeholder={t("valuator.address_placeholder", "Indirizzo o via")}
              data-testid="valuator-address"
            />
            <input className="w-full border rounded p-2" placeholder={t("valuator.city", "Città")} value={form.city} onChange={e => setForm(f => ({ ...f, city: e.target.value }))} data-testid="valuator-city" />
            <input className="w-full border rounded p-2" placeholder={t("valuator.zone", "Zona")} value={form.zone} onChange={e => setForm(f => ({ ...f, zone: e.target.value }))} data-testid="valuator-zone" />
          </div>
          <div className="space-y-4">
            <h3 className="font-serif text-lg text-stone-800">{t("valuator.section_property", "Immobile")}</h3>
            <select className="w-full border rounded p-2" value={form.property_type} onChange={e => setForm(f => ({ ...f, property_type: e.target.value }))} data-testid="valuator-property-type">
              {PROPERTY_TYPES.map(o => <option key={o} value={o}>{o}</option>)}
            </select>
            <input type="number" min="10" max="10000" className="w-full border rounded p-2" placeholder={t("valuator.surface", "Superficie calpestabile m²")} value={form.surface_sqm} onChange={e => setForm(f => ({ ...f, surface_sqm: e.target.value }))} data-testid="valuator-surface" />
            <select className="w-full border rounded p-2" value={form.condition} onChange={e => setForm(f => ({ ...f, condition: e.target.value }))} data-testid="valuator-condition">
              {CONDITIONS.map(o => <option key={o} value={o}>{o}</option>)}
            </select>
            <select className="w-full border rounded p-2" value={form.energy_class} onChange={e => setForm(f => ({ ...f, energy_class: e.target.value }))} data-testid="valuator-energy">
              <option value="">{t("valuator.energy_none", "Classe energetica (opzionale)")}</option>
              {ENERGY_CLASSES.map(o => <option key={o} value={o}>{o}</option>)}
            </select>
            <input type="number" min="-2" max="80" className="w-full border rounded p-2" placeholder={t("valuator.floor", "Piano (opzionale)")} value={form.floor} onChange={e => setForm(f => ({ ...f, floor: e.target.value }))} data-testid="valuator-floor" />
          </div>

          {/* Pro section — only UNI tier */}
          {tier === "uni" && (
            <div className="md:col-span-2 border-t pt-4 mt-2" data-testid="valuator-pro-section">
              <h3 className="font-serif text-lg text-stone-800 mb-3">{t("valuator.pro_surfaces_title", "Superfici commerciali UNI 10750")}</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                {["veranda_mq", "terrazzo_mq", "balcone_mq", "cantina_mq", "soffitta_mq", "box_auto_mq", "posto_auto_scoperto_mq", "giardino_villa_mq", "giardino_condom_mq", "taverna_mq", "mansarda_abitabile_mq"].map(k => (
                  <input key={k} type="number" min="0" className="border rounded p-2" placeholder={k.replace(/_mq$/, "").replace(/_/g, " ")} value={pro[k]} onChange={e => setPro(p => ({ ...p, [k]: e.target.value }))} data-testid={`pro-${k}`} />
                ))}
              </div>
              <h3 className="font-serif text-lg text-stone-800 mt-6 mb-3">{t("valuator.pro_merit_title", "Coefficienti di merito")}</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                <Sel label="Piano" opts={FLOOR_CLASSES} v={pro.floor_class} on={v => setPro(p => ({ ...p, floor_class: v }))} tid="pro-floor-class" />
                <Sel label="Esposizione" opts={EXPOSURES} v={pro.exposure} on={v => setPro(p => ({ ...p, exposure: v }))} tid="pro-exposure" />
                <Sel label="Vista" opts={VIEWS} v={pro.view} on={v => setPro(p => ({ ...p, view: v }))} tid="pro-view" />
                <Sel label="Riscaldamento" opts={HEATINGS} v={pro.heating} on={v => setPro(p => ({ ...p, heating: v }))} tid="pro-heating" />
                <Sel label="Ascensore" opts={ELEVATORS} v={pro.elevator} on={v => setPro(p => ({ ...p, elevator: v }))} tid="pro-elevator" />
                <input type="number" min="1700" max="2030" className="border rounded p-2" placeholder="Anno costruzione" value={pro.year_built} onChange={e => setPro(p => ({ ...p, year_built: e.target.value }))} data-testid="pro-year-built" />
              </div>
            </div>
          )}

          <div className="md:col-span-2 flex items-center justify-between pt-4 border-t">
            {tier === "base" ? (
              <button type="submit" disabled={!canSubmit || busy} className="px-6 py-3 bg-stone-900 text-white rounded-lg disabled:opacity-40" data-testid="valuator-submit-base">
                {busy ? "..." : t("valuator.submit_base", "Ottieni la stima gratuita")}
              </button>
            ) : (
              <button type="submit" disabled={!canSubmit || busy} className="px-6 py-3 bg-emerald-700 text-white rounded-lg disabled:opacity-40" data-testid="valuator-submit-uni">
                {busy ? "..." : (isAgent ? t("valuator.submit_uni_agent", "Calcola UNI (crediti agenzia)") : t("valuator.submit_uni_b2c", "Calcola UNI · €2,99"))}
              </button>
            )}
            {tier === "base" && (
              <span className="text-xs text-stone-500">{t("valuator.tier_base_limit", "1 valutazione ogni 12 mesi · nessun PDF")}</span>
            )}
            {tier === "uni" && !isAgent && (
              <span className="text-xs text-stone-500">{t("valuator.tier_uni_hint", "Il pagamento sblocca calcolo + PDF per 24h")}</span>
            )}
          </div>
        </form>

        {/* Errors + upsell */}
        {error && (
          <div className="mt-6 p-5 rounded-lg border border-red-300 bg-red-50 text-red-900" data-testid="valuator-error">
            <div className="font-medium">{error.message}</div>
            {error.reset_at && (
              <div className="text-sm mt-1">{t("valuator.reset_at", "Riprova dopo il")}: {new Date(error.reset_at).toLocaleDateString()}</div>
            )}
            {(error.code === "payment_required" || error.upsell_product_key) && (
              <button onClick={() => handleCheckout("upsell")} disabled={checkoutBusy} className="mt-3 px-4 py-2 bg-emerald-700 text-white rounded" data-testid="valuator-checkout-cta">
                {checkoutBusy ? "..." : (isAgent ? t("valuator.use_agency_credits", "Usa crediti agenzia") : t("valuator.pay_and_unlock", "Paga €2,99 e sblocca"))}
              </button>
            )}
          </div>
        )}

        {/* Result */}
        {result && (
          <div ref={resultRef} className="mt-6 space-y-4">
            <div className="bg-white border border-stone-200 rounded-lg p-6" data-testid="valuator-result">
              <div className="text-sm text-stone-500 uppercase tracking-wide">{t("valuator.result_value", "Valore stimato")}</div>
              <div className="text-3xl font-serif text-stone-900" data-testid="r-value">€ {Number(result.estimated_value || result.value_avg || 0).toLocaleString("it-IT")}</div>
              {result.value_range && (
                <div className="text-sm text-stone-600 mt-1">
                  Range: € {Number(result.value_range.min).toLocaleString("it-IT")} – € {Number(result.value_range.max).toLocaleString("it-IT")}
                </div>
              )}
              {result.price_per_sqm && (
                <div className="text-sm text-stone-600">€/m²: {Number(result.price_per_sqm).toLocaleString("it-IT")}</div>
              )}
              {result.confidence && (
                <div className="text-xs text-stone-500 mt-2">{t("valuator.confidence", "Affidabilità")}: {result.confidence}</div>
              )}
            </div>

            {result._tier === "base" && (
              <div className="p-5 rounded-lg border border-emerald-300 bg-emerald-50" data-testid="valuator-upsell">
                <div className="font-medium text-emerald-900">{t("valuator.upsell_uni_cta", "Vuoi una valutazione UNI 10750 con report PDF professionale?")}</div>
                <div className="text-sm text-emerald-800 mt-1">{t("valuator.upsell_uni_details", "Superficie commerciale ponderata + coefficienti di merito + PDF brandizzato scaricabile.")}</div>
                <button onClick={() => { setTier("uni"); window.scrollTo({ top: 0, behavior: "smooth" }); }} className="mt-3 px-4 py-2 bg-emerald-700 text-white rounded" data-testid="upsell-goto-uni">
                  {isAgent ? t("valuator.upsell_agent_cta", "Passa a UNI (crediti agenzia)") : t("valuator.upsell_b2c_cta", "Passa a UNI · €2,99")}
                </button>
              </div>
            )}

            {result._tier === "uni" && (
              <button onClick={handleDownloadPdf} disabled={pdfBusy} className="w-full md:w-auto px-6 py-3 bg-stone-900 text-white rounded-lg disabled:opacity-40" data-testid="r-download-pdf">
                {pdfBusy ? "..." : `📄 ${t("valuator.r_pdf_btn", "Scarica report PDF")}`}
              </button>
            )}
          </div>
        )}

        <div className="mt-10 text-xs text-stone-500 text-center">
          {t("valuator.disclaimer", "Stima algoritmica basata su dati OMI 2025 + coefficienti UNI 10750. Non sostituisce una perizia professionale.")}
        </div>
      </div>
    </div>
  );
}

function TierCard({ active, title, subtitle, price, onClick, note, highlight, testid }) {
  return (
    <button type="button" onClick={onClick} data-testid={testid}
      className={`text-left p-5 rounded-lg border transition ${active ? (highlight ? "border-emerald-500 bg-emerald-50 ring-2 ring-emerald-300" : "border-stone-900 bg-stone-50 ring-2 ring-stone-300") : "border-stone-200 bg-white hover:border-stone-400"}`}>
      <div className="flex items-baseline justify-between">
        <div className="font-serif text-lg text-stone-900">{title}</div>
        <div className={`text-sm font-medium ${highlight ? "text-emerald-700" : "text-stone-700"}`}>{price}</div>
      </div>
      <div className="text-sm text-stone-600 mt-1">{subtitle}</div>
      {note && <div className="text-xs text-amber-700 mt-2">{note}</div>}
    </button>
  );
}

function Sel({ label, opts, v, on, tid }) {
  return (
    <select className="border rounded p-2 w-full" value={v} onChange={e => on(e.target.value)} data-testid={tid}>
      <option value="">{label}</option>
      {opts.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  );
}

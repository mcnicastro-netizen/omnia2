/* OMNIA — Public Property Detail Page (M3.S4)
 *
 * Public landing page for a single property listed on ImmobilCloud.
 * Path: /it/cloud/property/:pid
 *
 * Sections:
 *  1. Hero with title, price, city, share buttons
 *  2. Photo gallery (cover + thumbnails)
 *  3. Key info (surface, rooms, bedrooms, bathrooms, energy class)
 *  4. Description + features list
 *  5. Mini map (Leaflet) if lat/lng available
 *  6. Agency card + contact form → POST /api/cloud/property/:pid/contact
 *  7. Schema.org RealEstateListing JSON-LD for SEO
 *
 * Lead is auto-created in the agency's CRM with source="ImmobilCloud".
 */
import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { MapContainer, TileLayer, Marker } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { api } from "../../../shared/lib/api";
import { useAuth } from "../../../shared/lib/auth";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api/cloud`;

function formatPrice(p) {
  if (!p) return "";
  const v = p.operation === "rent" ? p.rent_monthly : p.price;
  if (!v) return "";
  return p.operation === "rent"
    ? `€ ${Number(v).toLocaleString("it-IT")}/mese`
    : `€ ${Number(v).toLocaleString("it-IT")}`;
}

// Stima rapida rata: mutuo 25 anni, LTV 80%, TAN indicativo 3.6% (allineato al comparatore)
function estimateInstallment(price) {
  const loan = price * 0.8;
  const i = 0.036 / 12;
  const n = 300;
  return (loan * i) / (1 - Math.pow(1 + i, -n));
}

export default function PropertyDetailPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const { pid } = useParams();
  const [prop, setProp] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activePhoto, setActivePhoto] = useState(0);
  const [fav, setFav] = useState(false);
  const [videoUrl, setVideoUrl] = useState(null);
  const [videoBusy, setVideoBusy] = useState(false);
  const [scout, setScout] = useState(null);
  const [scoutBusy, setScoutBusy] = useState(false);
  const [scoutErr, setScoutErr] = useState("");
  const { user } = useAuth();
  const isB2c = Boolean(user && user.account_type === "b2c");
  const isLister = Boolean(prop?.viewer_is_lister);

  const runScout = async () => {
    if (!pid || scoutBusy) return;
    setScoutBusy(true);
    setScoutErr("");
    try {
      const { data } = await api.post(`/cloud/property/${pid}/scout`, { lang });
      setScout(data);
    } catch (e) {
      setScoutErr(e?.response?.data?.detail || "Scout non disponibile. Riprova.");
    } finally {
      setScoutBusy(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    setScout(null);
    setScoutErr("");
    api.get(`/cloud/property/${pid}`)
      .then((r) => setProp(r.data))
      .catch((e) => setError(e?.response?.status === 404 ? "not_found" : "fetch_error"))
      .finally(() => setLoading(false));
  }, [pid]);

  useEffect(() => {
    if (!pid) return;
    api.get(`/cloud/videos/by-property/${pid}`)
      .then((r) => {
        if (r.data?.id) {
          setVideoUrl(`${BACKEND_URL}/api/app/videos/${r.data.id}/download`);
        }
      })
      .catch(() => {});
    if (isB2c) {
      api.get("/cloud/me/favorites/ids")
        .then((r) => setFav((r.data.ids || []).includes(pid)))
        .catch(() => {});
    }
  }, [pid, isB2c]);

  const toggleFav = async () => {
    if (!isB2c) return;
    try {
      if (fav) {
        await api.delete(`/cloud/me/favorites/${pid}`);
        setFav(false);
      } else {
        await api.post(`/cloud/me/favorites/${pid}`);
        setFav(true);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const generateVideo = async () => {
    setVideoBusy(true);
    try {
      const { data } = await api.post(`/cloud/videos/kenburns/property/${pid}`, { duration_s: 15 });
      const poll = async (n = 0) => {
        if (n > 40) return;
        const st = await api.get(`/cloud/videos/${data.video_id}`);
        if (st.data.status === "ready") {
          setVideoUrl(`${BACKEND_URL}/api/app/videos/${data.video_id}/download`);
          return;
        }
        if (st.data.status === "failed") return;
        await new Promise((r) => setTimeout(r, 1500));
        return poll(n + 1);
      };
      await poll();
    } catch (e) {
      console.error(e);
    } finally {
      setVideoBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-5 sm:px-8 py-20" data-testid="property-detail-loading">
        <div className="rounded-2xl bg-[#f7f4ef] border border-stone-200 px-6 py-16 text-center">
          <p className="text-stone-500 text-sm">{t("common.loading")}</p>
        </div>
      </div>
    );
  }
  if (error === "not_found" || !prop) {
    return (
      <div className="max-w-5xl mx-auto px-5 sm:px-8 py-20 text-center" data-testid="property-detail-notfound">
        <p className="text-[11px] uppercase tracking-[0.28em] text-[#C19A6B] mb-3">ImmobilCloud</p>
        <h1 className="text-3xl md:text-4xl font-light mb-3 text-[#0B1E3F]" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
          {t("cloud.detail_not_found_title")}
        </h1>
        <p className="text-stone-600 mb-8 max-w-md mx-auto">{t("cloud.detail_not_found_desc")}</p>
        <Link
          to={`/${lang}/cloud/search`}
          className="inline-flex px-5 py-2.5 text-xs uppercase tracking-widest bg-[#0B1E3F] text-white rounded-lg hover:bg-[#C19A6B] transition"
        >
          ← {t("cloud.back_to_search")}
        </Link>
      </div>
    );
  }

  const photos = prop.photos || [];
  const cover = photos[activePhoto];
  const publicUrl = `${window.location.origin}/${lang}/cloud/property/${pid}`;

  const energy = prop.energy?.energy_class || "—";
  const features = Object.entries(prop.features || {}).filter(([_, v]) => v).map(([k]) => k);

  return (
    <div data-testid="property-detail-page">
      <SchemaOrgJsonLd prop={prop} publicUrl={publicUrl} />

      {/* Dominant gallery plane */}
      <section className="relative bg-[#0B1E3F]">
        {photos.length > 0 ? (
          <div data-testid="detail-gallery" className="relative">
            <div className="aspect-[16/10] md:aspect-[21/9] max-h-[70vh] overflow-hidden bg-stone-900">
              <img
                src={`${BACKEND_URL}${cover.url}`}
                alt={cover.caption || prop.title}
                className="w-full h-full object-cover"
              />
              <div
                className="absolute inset-0 pointer-events-none"
                style={{
                  background:
                    "linear-gradient(180deg, rgba(11,30,63,0.15) 0%, rgba(11,30,63,0.05) 40%, rgba(11,30,63,0.75) 100%)",
                }}
              />
            </div>
            {photos.length > 1 && (
              <div className="absolute bottom-4 left-0 right-0 px-5 sm:px-8 md:px-16">
                <div className="max-w-6xl mx-auto flex gap-2 overflow-x-auto pb-1">
                  {photos.map((ph, i) => (
                    <button
                      key={i}
                      data-testid={`detail-thumb-${i}`}
                      onClick={() => setActivePhoto(i)}
                      className={`shrink-0 w-16 h-16 md:w-20 md:h-20 rounded-lg overflow-hidden border-2 transition ${
                        i === activePhoto ? "border-white" : "border-white/30 opacity-80 hover:opacity-100"
                      }`}
                    >
                      <img src={`${BACKEND_URL}${ph.url}`} alt="" className="w-full h-full object-cover" />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="aspect-[21/9] max-h-[40vh] flex items-center justify-center text-white/50 text-sm bg-[#0B1E3F]">
            {t("cloud.no_photos")}
          </div>
        )}
      </section>

      <div className="max-w-6xl mx-auto px-5 sm:px-8 md:px-16 py-8">
        {/* Breadcrumb */}
        <nav className="text-xs text-stone-500 mb-5">
          <Link to={`/${lang}/cloud`} className="hover:text-[#0B1E3F]">{t("cloud.b2c_home_short")}</Link>
          <span className="mx-2">·</span>
          <Link to={`/${lang}/cloud/search`} className="hover:text-[#0B1E3F]">{t("cloud.search_label")}</Link>
          <span className="mx-2">·</span>
          <span className="text-stone-800">{prop.city}</span>
        </nav>

        {/* Title + price */}
        <div className="flex flex-wrap items-end justify-between gap-4 mb-8 pb-8 border-b border-stone-200">
          <div className="min-w-0 flex-1">
            {prop.operation && (
              <p className="text-[11px] uppercase tracking-[0.28em] text-[#C19A6B] mb-2">
                {prop.operation === "rent" ? t("cloud.op_rent") : t("cloud.op_sale")}
              </p>
            )}
            <h1
              data-testid="detail-title"
              className="text-3xl md:text-4xl lg:text-5xl font-light tracking-tight text-[#0B1E3F] leading-[1.05]"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {prop.title || prop.property_type}
            </h1>
            <p className="text-stone-600 text-sm mt-2">
              {prop.city}{prop.zone ? ` · ${prop.zone}` : ""}{prop.property_type ? ` · ${prop.property_type}` : ""}
            </p>
            <ShareBar title={prop.title || prop.property_type} publicUrl={publicUrl} />
          </div>
          <div className="text-left sm:text-right shrink-0">
            <div data-testid="detail-price" className="text-2xl md:text-3xl font-semibold text-[#0B1E3F]" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              {formatPrice(prop) || t("cloud.price_on_request")}
            </div>
            {isB2c && (
              <button
                type="button"
                data-testid="detail-favorite-btn"
                onClick={toggleFav}
                className={`mt-3 text-xs uppercase tracking-widest px-4 py-2 border rounded-lg transition ${
                  fav
                    ? "bg-[#0B1E3F] text-white border-[#0B1E3F]"
                    : "border-stone-300 text-stone-700 hover:border-[#0B1E3F]"
                }`}
              >
                {fav ? "★ Nei preferiti" : "☆ Salva nei preferiti"}
              </button>
            )}
            {prop.operation !== "rent" && prop.price > 20000 && (
              <Link
                to={`/${lang}/cloud/mutui?price=${prop.price}`}
                data-testid="detail-mortgage-box"
                className="mt-3 flex items-center gap-2 sm:justify-end text-sm text-stone-600 hover:text-[#0B1E3F] group"
                title={t("mutui.detail_box_note")}
              >
                <span>
                  {t("mutui.detail_box_title")} {t("mutui.detail_box_from")}{" "}
                  <strong className="text-[#0B1E3F]">
                    € {Math.round(estimateInstallment(prop.price)).toLocaleString("it-IT")}/{t("mutui.month")}
                  </strong>
                </span>
                <span className="text-[11px] uppercase tracking-widest text-[#C19A6B] group-hover:underline">
                  {t("mutui.detail_box_cta")} →
                </span>
              </Link>
            )}
            <div className="mt-3 flex flex-col sm:flex-row gap-2 sm:justify-end items-stretch sm:items-center text-sm" data-testid="detail-valuator-box">
              <span className="text-stone-600">{t("valuator.detail_box_title", "Quanto vale questo immobile?")}</span>
              <Link
                to={`/${lang}/cloud/valutatore?tier=base&city=${encodeURIComponent(prop.city || "")}&property_type=${encodeURIComponent(prop.property_type || "appartamento")}&surface_sqm=${prop.surface_sqm || ""}`}
                data-testid="detail-valuator-base-cta"
                className="px-3 py-1.5 border border-stone-300 rounded-lg text-stone-700 hover:bg-[#f7f4ef] text-center"
              >
                {t("valuator.detail_box_base_cta", "Stima gratuita")}
              </Link>
              <Link
                to={`/${lang}/cloud/valutatore?tier=uni&city=${encodeURIComponent(prop.city || "")}&property_type=${encodeURIComponent(prop.property_type || "appartamento")}&surface_sqm=${prop.surface_sqm || ""}`}
                data-testid="detail-valuator-uni-cta"
                className="px-3 py-1.5 bg-[#0B1E3F] text-white rounded-lg hover:bg-[#C19A6B] text-center transition"
              >
                {t("valuator.detail_box_uni_cta", "Report UNI · €2,99")}
              </Link>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* LEFT COLUMN */}
          <div className="lg:col-span-2 space-y-8">
            {/* Scout — buyer trust voice OR constructive lister mirror */}
            <section
              data-testid="scout-hal-panel"
              data-scout-voice={isLister ? "lister" : "buyer"}
              className="overflow-hidden rounded-2xl border border-stone-200 bg-[#f7f4ef] shadow-sm"
            >
              <div className="grid grid-cols-1 sm:grid-cols-[140px_1fr]">
                <div className="hidden sm:block relative min-h-[140px]">
                  <img
                    src="/cloud/living.jpg"
                    alt=""
                    className="absolute inset-0 w-full h-full object-cover"
                  />
                </div>
                <div className="p-5 sm:p-6 bg-[#f7f4ef] text-[#0B1E3F]">
                  <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.25em] text-[#C19A6B]">Scout</p>
                      <h2
                        className="text-xl font-light text-[#0B1E3F]"
                        style={{ fontFamily: "'Fraunces', Georgia, serif" }}
                      >
                        {isLister
                          ? "Come ti vede chi valuta casa"
                          : "Un'occhiata furba, prima della visita"}
                      </h2>
                      <p className="text-sm text-stone-600 mt-1">
                        {isLister
                          ? "Stesso sguardo di un acquirente — ma qui ti dice cosa rafforzare, non quanto dubitare di te."
                          : "Ti dice se l'annuncio è completo, se il prezzo ha senso e cosa chiedere."}
                      </p>
                    </div>
                    {!scout && (
                      <button
                        type="button"
                        data-testid="scout-hal-run"
                        onClick={runScout}
                        disabled={scoutBusy}
                        className="px-4 py-2 text-xs uppercase tracking-widest bg-[#0B1E3F] text-white rounded-lg hover:bg-[#C19A6B] disabled:opacity-50 transition"
                      >
                        {scoutBusy
                          ? "Un attimo…"
                          : isLister
                            ? "Guarda con gli occhi di Scout"
                            : "Chiedi a Scout"}
                      </button>
                    )}
                  </div>
                  {scoutErr && (
                    <p className="text-sm text-rose-700" data-testid="scout-hal-error">{String(scoutErr)}</p>
                  )}
                  {scout && (
                    <div className="space-y-4" data-testid="scout-hal-result">
                      <p className="text-sm text-stone-800 border-l-2 border-[#C19A6B] pl-3 leading-relaxed">
                        {isLister
                          ? (scout.completeness?.score < 60
                              ? "Con i dati attuali Scout ha poco da raccontare a chi valuta casa. Qui sotto c'è cosa aggiungere — non è un voto sul tuo lavoro."
                              : "Ecco come un acquirente legge il tuo annuncio oggi. La fascia prezzo è un indizio di zona, non un giudizio sul tuo chiesto.")
                          : scout.insight}
                      </p>
                      <div className="space-y-3">
                        <div
                          className="inline-block px-3 py-2 rounded-lg bg-white border border-stone-200"
                          data-testid="scout-completeness"
                        >
                          <span className="text-[10px] uppercase tracking-widest text-stone-500">
                            {isLister ? "Completezza vista dall'acquirente" : "Quanto è completo"}
                          </span>
                          <div className="text-lg font-medium text-[#0B1E3F]">
                            {scout.completeness?.score}/100 · {scout.completeness?.grade}
                          </div>
                        </div>
                        {scout.price_vs_zone?.available && (
                          <div className="space-y-3" data-testid="scout-price-zone">
                            <div className="px-3 py-3 rounded-lg bg-white border border-stone-200">
                              <span className="text-[10px] uppercase tracking-widest text-stone-500">
                                Fascia di prezzo stimata
                              </span>
                              <div className="text-lg font-medium text-[#0B1E3F] mt-0.5">
                                {scout.price_vs_zone.label_it}
                              </div>
                              {scout.price_vs_zone.estimated_band_eur && (
                                <p className="text-sm text-stone-700 mt-1" data-testid="scout-price-band">
                                  Per questi mq: circa{" "}
                                  <strong>
                                    € {Number(scout.price_vs_zone.estimated_band_eur.min).toLocaleString("it-IT")}
                                    {" – "}
                                    {Number(scout.price_vs_zone.estimated_band_eur.max).toLocaleString("it-IT")}
                                  </strong>
                                  <span className="text-stone-500">
                                    {" "}(€{scout.price_vs_zone.zone_eur_mq_min}–{scout.price_vs_zone.zone_eur_mq_max}/m²)
                                  </span>
                                </p>
                              )}
                              <p className="text-xs text-stone-500 mt-1">
                                Richiesta ~€{scout.price_vs_zone.asking_eur_mq}/m²
                                {scout.price_vs_zone.asking_eur
                                  ? ` · € ${Number(scout.price_vs_zone.asking_eur).toLocaleString("it-IT")}`
                                  : ""}
                              </p>
                            </div>

                            {/* Buyer: confidence + limits. Lister: constructive “what Scout can use” — no inquisitorial grade */}
                            {isLister ? (
                              <div
                                className="px-3 py-3 rounded-lg bg-white border border-stone-200"
                                data-testid="scout-lister-signal"
                              >
                                <span className="text-[10px] uppercase tracking-widest text-stone-500">
                                  Cosa Scout può usare oggi
                                </span>
                                <p className="text-sm text-[#0B1E3F] mt-1 leading-relaxed">
                                  {scout.completeness?.score >= 70
                                    ? "Hai già abbastanza campi perché Scout dia un primo sguardo utile. Continua a curare foto e documenti."
                                    : "Mancano ancora pezzi che un acquirente si aspetta: completa quelli sotto e il segnale prezzo diventa più chiaro per tutti."}
                                </p>
                                {isB2c && (
                                  <Link
                                    to={`/${lang}/cloud/account/sell`}
                                    className="inline-block mt-3 text-xs uppercase tracking-widest text-[#C19A6B] hover:text-[#0B1E3F]"
                                    data-testid="scout-lister-edit-cta"
                                  >
                                    Modifica il tuo annuncio →
                                  </Link>
                                )}
                              </div>
                            ) : (
                              scout.price_vs_zone.confidence && (
                                <div
                                  className="px-3 py-3 rounded-lg bg-white border border-stone-200"
                                  data-testid="scout-confidence"
                                >
                                  <span className="text-[10px] uppercase tracking-widest text-stone-500">
                                    Quanto ci fidiamo
                                  </span>
                                  <div className="flex flex-wrap items-baseline gap-2 mt-0.5">
                                    <span className="text-sm font-medium text-[#0B1E3F]">
                                      {scout.price_vs_zone.confidence.label_it}
                                    </span>
                                    <span className="text-[10px] uppercase tracking-widest text-[#C19A6B]">
                                      {scout.price_vs_zone.confidence.level}
                                      {scout.price_vs_zone.confidence.comparables_n != null
                                        ? ` · ${scout.price_vs_zone.confidence.comparables_n} annunci in città`
                                        : ""}
                                    </span>
                                  </div>
                                  {scout.price_vs_zone.confidence.limits_it?.length > 0 && (
                                    <ul className="mt-2 text-xs text-stone-600 space-y-1 list-disc pl-4" data-testid="scout-confidence-limits">
                                      {scout.price_vs_zone.confidence.limits_it.map((lim, i) => (
                                        <li key={i}>{lim}</li>
                                      ))}
                                    </ul>
                                  )}
                                </div>
                              )
                            )}

                            {scout.price_vs_zone.why?.length > 0 && (
                              <div data-testid="scout-price-why">
                                <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-1">
                                  {isLister ? "Come si colloca il chiesto" : "Perché lo diciamo"}
                                </p>
                                <ul className="text-sm text-stone-800 space-y-1.5 list-disc pl-4 leading-relaxed">
                                  {scout.price_vs_zone.why.map((w) => (
                                    <li key={w.key || w.label_it}>{w.label_it}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        )}
                        {prop.last_price_drop?.drop_pct && (
                          <div className="px-3 py-2 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm">
                            Ribasso recente −{prop.last_price_drop.drop_pct}%
                          </div>
                        )}
                      </div>
                      {!isLister && scout.red_flags?.length > 0 && (
                        <div>
                          <p className="text-[10px] uppercase tracking-widest text-rose-700 mb-1">Occhio a</p>
                          <ul className="text-sm text-stone-800 space-y-1 list-disc pl-4 leading-relaxed">
                            {scout.red_flags.map((f, i) => <li key={i}>{f}</li>)}
                          </ul>
                        </div>
                      )}
                      {isLister && scout.red_flags?.length > 0 && (
                        <div data-testid="scout-lister-friction">
                          <p className="text-[10px] uppercase tracking-widest text-amber-800 mb-1">
                            Dove un acquirente potrebbe frenare
                          </p>
                          <ul className="text-sm text-stone-800 space-y-1 list-disc pl-4 leading-relaxed">
                            {scout.red_flags.map((f, i) => <li key={i}>{f}</li>)}
                          </ul>
                        </div>
                      )}
                      {scout.questions_for_seller?.length > 0 && (
                        <div>
                          <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-1">
                            {isLister ? "Domande che ti faranno" : "Da chiedere al telefono"}
                          </p>
                          <ol className="text-sm text-stone-800 space-y-1 list-decimal pl-4 leading-relaxed">
                            {scout.questions_for_seller.map((q, i) => <li key={i}>{q}</li>)}
                          </ol>
                        </div>
                      )}

                      {scout.visit_checklist?.length > 0 && (
                        <div data-testid="scout-visit-checklist">
                          <p className="text-[10px] uppercase tracking-widest text-[#C19A6B] mb-1">
                            {isLister ? "Cosa controlleranno in visita" : "In visita — porta questa lista"}
                          </p>
                          <ol className="text-sm text-stone-800 space-y-1.5 list-decimal pl-4 leading-relaxed">
                            {scout.visit_checklist.map((it) => (
                              <li key={it.key}>{it.label_it}</li>
                            ))}
                          </ol>
                        </div>
                      )}

                      {scout.documents_before_offer?.length > 0 && (
                        <div data-testid="scout-documents">
                          <p className="text-[10px] uppercase tracking-widest text-[#C19A6B] mb-1">
                            {isLister
                              ? "Documenti che ti chiederanno prima dell'offerta"
                              : "Prima di un'offerta — documenti da avere"}
                          </p>
                          <ul className="text-sm text-stone-800 space-y-2 list-disc pl-4 leading-relaxed">
                            {scout.documents_before_offer.map((d) => (
                              <li key={d.key}>
                                <span className="font-medium text-[#0B1E3F]">{d.label_it}</span>
                                {d.why_it && (
                                  <span className="block text-xs text-stone-500 mt-0.5">{d.why_it}</span>
                                )}
                              </li>
                            ))}
                          </ul>
                          {!isLister && prop.operation !== "rent" && (
                            <div className="mt-3 flex flex-wrap gap-3 text-xs uppercase tracking-widest">
                              <Link
                                to={`/${lang}/cloud/visura`}
                                className="text-[#0B1E3F] hover:text-[#C19A6B]"
                                data-testid="scout-doc-visura-cta"
                              >
                                Visura sul portale →
                              </Link>
                              <Link
                                to={`/${lang}/cloud/valutatore?tier=base&city=${encodeURIComponent(prop.city || "")}&property_type=${encodeURIComponent(prop.property_type || "appartamento")}&surface_sqm=${prop.surface_sqm || ""}`}
                                className="text-stone-500 hover:text-[#C19A6B]"
                                data-testid="scout-doc-valuator-cta"
                              >
                                Stima ImmobilCloud →
                              </Link>
                            </div>
                          )}
                        </div>
                      )}

                      {isLister && scout.seller_gaps?.length > 0 && (
                        <div data-testid="scout-seller-gaps">
                          <p className="text-[10px] uppercase tracking-widest text-amber-800 mb-1">
                            Cosa aggiungere all&apos;annuncio
                          </p>
                          <ul className="text-sm text-stone-800 space-y-1 list-disc pl-4 leading-relaxed">
                            {scout.seller_gaps.map((g, i) => (
                              <li key={g.key || i}>{g.label_it}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      <p className="text-[11px] text-stone-500 leading-relaxed">
                        {isLister
                          ? "Scout ti mostra lo stesso segnale che vede chi sta cercando casa. Usalo per migliorare l'annuncio — non come voto."
                          : scout.disclaimer_it}
                      </p>
                      <button
                        type="button"
                        onClick={runScout}
                        disabled={scoutBusy}
                        className="text-[11px] uppercase tracking-widest text-stone-500 hover:text-[#0B1E3F]"
                      >
                        Aggiorna Scout
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </section>

            {/* Micro-tour Ken Burns */}
            <div data-testid="detail-micro-tour" className="border border-stone-200 rounded-2xl p-5 bg-white">
              <div className="flex items-center justify-between gap-3 mb-3">
                <h2 className="text-[11px] uppercase tracking-[0.28em] text-[#C19A6B]">Micro-tour</h2>
                {!videoUrl && photos.length > 0 && (
                  <button
                    type="button"
                    data-testid="detail-generate-video"
                    disabled={videoBusy}
                    onClick={generateVideo}
                    className="text-xs uppercase tracking-widest px-3 py-1.5 border border-stone-300 rounded-lg hover:border-[#0B1E3F] disabled:opacity-50"
                  >
                    {videoBusy ? "Generazione…" : "Genera video 15s"}
                  </button>
                )}
              </div>
              {videoUrl ? (
                <video
                  data-testid="detail-video-player"
                  src={videoUrl}
                  controls
                  className="w-full rounded-xl aspect-video bg-stone-900"
                />
              ) : (
                <p className="text-sm text-stone-500">Nessun video ancora. Generane uno dalle foto dell&apos;annuncio.</p>
              )}
            </div>

            {/* Key info grid */}
            <div data-testid="detail-key-info" className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-[#f7f4ef] border border-stone-200 rounded-2xl p-5">
              <InfoCell label={t("cloud.info_surface")} value={prop.surface_sqm ? `${prop.surface_sqm} m²` : "—"} testid="info-surface" />
              <InfoCell label={t("cloud.info_rooms")} value={prop.rooms || "—"} testid="info-rooms" />
              <InfoCell label={t("cloud.info_bedrooms")} value={prop.bedrooms || "—"} testid="info-bedrooms" />
              <InfoCell label={t("cloud.info_bathrooms")} value={prop.bathrooms || "—"} testid="info-bathrooms" />
              <InfoCell label={t("cloud.info_floor")} value={prop.floor != null ? `${prop.floor}/${prop.total_floors || "—"}` : "—"} testid="info-floor" />
              <InfoCell label={t("cloud.info_year")} value={prop.year_built || "—"} testid="info-year" />
              <InfoCell label={t("cloud.info_energy")} value={energy} testid="info-energy" />
              <InfoCell label={t("cloud.info_ref")} value={prop.reference_code || "—"} testid="info-ref" />
            </div>

            {/* Description */}
            {prop.description && (
              <section data-testid="detail-description">
                <h2 className="text-2xl font-light mb-3 text-[#0B1E3F]" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                  {t("cloud.detail_description")}
                </h2>
                <p className="text-stone-700 text-sm leading-relaxed whitespace-pre-line">
                  {prop.description}
                </p>
              </section>
            )}

            {/* Features */}
            {features.length > 0 && (
              <section data-testid="detail-features">
                <h2 className="text-2xl font-light mb-3 text-[#0B1E3F]" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                  {t("cloud.detail_features")}
                </h2>
                <ul className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm text-stone-700">
                  {features.map((f) => (
                    <li key={f} className="flex items-center gap-2 before:content-['✓'] before:text-[#C19A6B] before:font-bold">
                      <span>{t(`features.${f}`, { defaultValue: f.replace(/_/g, " ") })}</span>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {/* Mini map */}
            {prop.lat && prop.lng && (
              <section data-testid="detail-map">
                <h2 className="text-2xl font-light mb-3 text-[#0B1E3F]" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                  {t("cloud.detail_location")}
                </h2>
                <div className="h-72 rounded-2xl overflow-hidden border border-stone-200">
                  <MapContainer center={[prop.lat, prop.lng]} zoom={14} scrollWheelZoom={false} className="h-full w-full">
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    <Marker position={[prop.lat, prop.lng]} />
                  </MapContainer>
                </div>
              </section>
            )}
          </div>

          {/* RIGHT COLUMN — contact composition */}
          <aside className="lg:col-span-1 lg:sticky lg:top-24 lg:self-start">
            {isLister ? (
              <div
                data-testid="contact-own-listing"
                className="relative overflow-hidden rounded-2xl border border-stone-200/80 bg-gradient-to-br from-[#f7f4ef] via-white to-[#f3eee6] p-6"
              >
                <div className="absolute -right-8 -top-8 h-28 w-28 rounded-full bg-[#C19A6B]/10" aria-hidden />
                <p className="text-[10px] uppercase tracking-[0.28em] text-[#C19A6B] mb-2">ImmobilCloud</p>
                <p className="text-sm text-[#0B1E3F] leading-relaxed" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                  {t("cloud.contact_own_listing")}
                </p>
              </div>
            ) : (
              <ContactPanel
                pid={pid}
                propertyTitle={prop.title}
                publisher={prop.publisher}
                agency={prop.agency}
              />
            )}
          </aside>
        </div>
      </div>
    </div>
  );
}

/* Share bar: WhatsApp, Facebook, X, email, copy link (+ native share on mobile) */
function ShareBar({ title, publicUrl }) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const shareText = t("cloud.share_text", { title });
  const enc = encodeURIComponent;

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(publicUrl);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = publicUrl;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const nativeShare = () => navigator.share({ title, text: shareText, url: publicUrl }).catch(() => {});

  const btnCls = "w-8 h-8 rounded-full border border-stone-200 bg-white flex items-center justify-center text-stone-600 hover:text-white transition";

  return (
    <div data-testid="detail-share-bar" className="flex items-center gap-2 mt-3">
      <span className="text-[11px] uppercase tracking-widest text-stone-500 mr-1">{t("cloud.share_label")}</span>
      <a
        data-testid="share-whatsapp" title={t("cloud.share_whatsapp")} aria-label={t("cloud.share_whatsapp")}
        href={`https://wa.me/?text=${enc(`${shareText}\n${publicUrl}`)}`}
        target="_blank" rel="noopener noreferrer"
        className={`${btnCls} hover:bg-[#25D366] hover:border-[#25D366]`}
      >
        <svg viewBox="0 0 24 24" className="w-4 h-4" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
      </a>
      <a
        data-testid="share-facebook" title={t("cloud.share_facebook")} aria-label={t("cloud.share_facebook")}
        href={`https://www.facebook.com/sharer/sharer.php?u=${enc(publicUrl)}`}
        target="_blank" rel="noopener noreferrer"
        className={`${btnCls} hover:bg-[#1877F2] hover:border-[#1877F2]`}
      >
        <svg viewBox="0 0 24 24" className="w-4 h-4" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
      </a>
      <a
        data-testid="share-x" title={t("cloud.share_x")} aria-label={t("cloud.share_x")}
        href={`https://twitter.com/intent/tweet?text=${enc(shareText)}&url=${enc(publicUrl)}`}
        target="_blank" rel="noopener noreferrer"
        className={`${btnCls} hover:bg-black hover:border-black`}
      >
        <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
      </a>
      <a
        data-testid="share-email" title={t("cloud.share_email")} aria-label={t("cloud.share_email")}
        href={`mailto:?subject=${enc(title || "")}&body=${enc(`${shareText}\n\n${publicUrl}`)}`}
        className={`${btnCls} hover:bg-[#0B1E3F] hover:border-[#0B1E3F]`}
      >
        <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 7L2 7"/></svg>
      </a>
      <button
        data-testid="share-copy" type="button" title={t("cloud.share_copy")} aria-label={t("cloud.share_copy")}
        onClick={copyLink}
        className={`${btnCls} hover:bg-[#C19A6B] hover:border-[#C19A6B]`}
      >
        <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
      </button>
      {typeof navigator !== "undefined" && navigator.share && (
        <button
          data-testid="share-native" type="button" title={t("cloud.share_native")} aria-label={t("cloud.share_native")}
          onClick={nativeShare}
          className={`${btnCls} hover:bg-stone-700 hover:border-stone-700`}
        >
          <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.59 13.51 6.83 3.98m-.01-10.98-6.82 3.98"/></svg>
        </button>
      )}
      {copied && (
        <span data-testid="share-copied-toast" className="text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded px-2 py-0.5">
          {t("cloud.share_copied")}
        </span>
      )}
    </div>
  );
}

function InfoCell({ label, value, testid }) {
  return (
    <div data-testid={testid}>
      <div className="text-[11px] uppercase tracking-widest text-stone-500">{label}</div>
      <div className="text-sm font-medium text-stone-900 mt-0.5">{value}</div>
    </div>
  );
}

function waHref(raw) {
  const digits = String(raw || "").replace(/[^\d]/g, "");
  return digits ? `https://wa.me/${digits}` : null;
}

function IconMail({ className = "w-4 h-4" }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m3 7 9 6 9-6" />
    </svg>
  );
}

function IconPhone({ className = "w-4 h-4" }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
      <path d="M6.5 3.5 9 6l-1.8 1.8a12 12 0 0 0 6.5 6.5L15.5 13l2.5 2.5c.4.4.5 1 .2 1.5A15 15 0 0 1 5 5.3c.5-.3 1.1-.2 1.5.2Z" />
    </svg>
  );
}

function IconWhatsApp({ className = "w-4 h-4" }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor" aria-hidden>
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
    </svg>
  );
}

function ChannelLink({ testid, href, icon, label, external }) {
  return (
    <a
      data-testid={testid}
      href={href}
      {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
      className="group flex items-center gap-3 rounded-xl border border-stone-200/90 bg-white/70 px-3 py-2.5 text-sm text-[#0B1E3F] transition duration-200 hover:-translate-y-0.5 hover:border-[#C19A6B]/60 hover:bg-white hover:shadow-[0_8px_24px_-12px_rgba(11,30,63,0.25)]"
    >
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#0B1E3F]/[0.06] text-[#0B1E3F] transition group-hover:bg-[#C19A6B]/15 group-hover:text-[#8a6a45]">
        {icon}
      </span>
      <span className="min-w-0 flex-1 truncate font-medium tracking-tight">{label}</span>
      <span className="text-[10px] uppercase tracking-[0.2em] text-stone-400 transition group-hover:text-[#C19A6B]">→</span>
    </a>
  );
}

function ContactPanel({ pid, propertyTitle, publisher, agency }) {
  const { t } = useTranslation();
  const kind = publisher?.kind || (agency ? "agency" : "private");
  const isPrivate = kind === "private";
  const channels = publisher?.channels || {};
  const name =
    publisher?.display_name ||
    agency?.display_name ||
    (isPrivate ? t("cloud.publisher_private") : t("cloud.publisher_agency"));
  const city = agency?.city;
  const logo = agency?.logo_url;
  const initial = (name || "P").trim().charAt(0).toUpperCase();
  const email = isPrivate ? channels.email : (channels.email || agency?.email);
  const phone = isPrivate ? channels.phone : (channels.phone || agency?.phone);
  const whatsapp = isPrivate ? channels.whatsapp : channels.whatsapp;
  const wa = whatsapp ? waHref(whatsapp) : null;
  const acceptsMessages = publisher?.accepts_messages !== false;

  const [form, setForm] = useState({
    name: "", surname: "", email: "", phone: "",
    message: t("cloud.contact_default_message", { title: propertyTitle || "" }),
    visit_requested: false,
    gdpr_consent: false,
  });
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!form.gdpr_consent) {
      setError(t("cloud.contact_err_gdpr"));
      return;
    }
    setBusy(true);
    setError("");
    try {
      const r = await fetch(`${API}/property/${pid}/contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const d = await r.json();
      if (!r.ok) {
        setError(d.detail || t("cloud.contact_err_generic"));
      } else {
        setDone(true);
      }
    } catch {
      setError(t("cloud.contact_err_generic"));
    } finally {
      setBusy(false);
    }
  };

  const fieldCls =
    "w-full rounded-xl border border-stone-200/90 bg-white/80 px-3.5 py-2.5 text-sm text-stone-900 outline-none transition placeholder:text-stone-400 focus:border-[#0B1E3F] focus:bg-white focus:ring-2 focus:ring-[#0B1E3F]/10";

  return (
    <div
      data-testid={isPrivate ? "private-publisher-card" : "detail-agency-card"}
      className="relative overflow-hidden rounded-2xl border border-stone-200/80 bg-gradient-to-b from-[#fbf8f3] to-white shadow-[0_20px_50px_-28px_rgba(11,30,63,0.35)] animate-[contactIn_480ms_ease-out]"
    >
      <style>{`
        @keyframes contactIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      {/* Header identity */}
      <div className="relative border-b border-stone-200/70 bg-[#0B1E3F] px-5 pb-5 pt-5 text-white">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(193,154,107,0.28),transparent_55%)]" aria-hidden />
        <p className="relative text-[10px] uppercase tracking-[0.3em] text-[#E8D5B5]/90 mb-3">
          {isPrivate ? t("cloud.publisher_private") : t("cloud.detail_agency_label")}
        </p>
        <div className="relative flex items-center gap-3.5">
          {logo ? (
            <img
              src={logo}
              alt={name}
              className="h-14 w-14 rounded-xl object-contain bg-white/95 border border-white/20 p-1"
            />
          ) : (
            <div
              className="flex h-14 w-14 items-center justify-center rounded-xl bg-white/10 text-2xl font-light text-[#E8D5B5] ring-1 ring-white/20"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {initial}
            </div>
          )}
          <div className="min-w-0">
            <h3
              className="truncate text-xl font-medium leading-tight text-white"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {name}
            </h3>
            {city && <p className="mt-0.5 truncate text-xs text-white/65">{city}</p>}
          </div>
        </div>
      </div>

      <div className="space-y-5 p-5">
        {(email || phone || wa) && (
          <div className="space-y-2" data-testid="publisher-channels">
            {email && (
              <ChannelLink
                testid={isPrivate ? "publisher-email" : "agency-email"}
                href={`mailto:${email}`}
                icon={<IconMail />}
                label={email}
              />
            )}
            {phone && (
              <ChannelLink
                testid={isPrivate ? "publisher-phone" : "agency-phone"}
                href={`tel:${phone}`}
                icon={<IconPhone />}
                label={phone}
              />
            )}
            {wa && (
              <ChannelLink
                testid="publisher-whatsapp"
                href={wa}
                icon={<IconWhatsApp className="w-4 h-4 text-[#1f6b45]" />}
                label="WhatsApp"
                external
              />
            )}
          </div>
        )}

        {acceptsMessages && (
          done ? (
            <div data-testid="contact-done" className="rounded-xl bg-[#f7f4ef] px-4 py-6 text-center">
              <p className="text-[10px] uppercase tracking-[0.28em] text-[#C19A6B] mb-2">ImmobilCloud</p>
              <h4
                className="text-lg text-[#0B1E3F] mb-1"
                style={{ fontFamily: "'Fraunces', Georgia, serif" }}
              >
                {t("cloud.contact_done_title")}
              </h4>
              <p className="text-xs leading-relaxed text-stone-600">
                {isPrivate ? t("cloud.contact_done_desc_private") : t("cloud.contact_done_desc")}
              </p>
            </div>
          ) : (
            <form data-testid="contact-form" onSubmit={onSubmit} className="space-y-3">
              {(email || phone || wa) && (
                <div className="flex items-center gap-3 py-1">
                  <div className="h-px flex-1 bg-gradient-to-r from-transparent via-stone-200 to-transparent" />
                  <span className="text-[10px] uppercase tracking-[0.22em] text-stone-400">
                    {t("cloud.contact_or_message")}
                  </span>
                  <div className="h-px flex-1 bg-gradient-to-r from-transparent via-stone-200 to-transparent" />
                </div>
              )}
              <div>
                <h4
                  className="text-base text-[#0B1E3F]"
                  style={{ fontFamily: "'Fraunces', Georgia, serif" }}
                >
                  {isPrivate ? t("cloud.contact_title_private") : t("cloud.contact_title")}
                </h4>
                <p className="mt-1 text-xs leading-relaxed text-stone-500">
                  {isPrivate ? t("cloud.contact_desc_private") : t("cloud.contact_desc")}
                </p>
              </div>

              <input
                data-testid="contact-name"
                placeholder={t("cloud.contact_name")}
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className={fieldCls}
              />
              <input
                data-testid="contact-email"
                type="email"
                placeholder={t("cloud.contact_email")}
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className={fieldCls}
              />
              <input
                data-testid="contact-phone"
                placeholder={t("cloud.contact_phone")}
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                className={fieldCls}
              />
              <textarea
                data-testid="contact-message"
                rows={4}
                required
                minLength={10}
                placeholder={t("cloud.contact_message")}
                value={form.message}
                onChange={(e) => setForm({ ...form, message: e.target.value })}
                className={`${fieldCls} resize-y min-h-[96px]`}
              />

              <label className="flex items-center gap-2.5 text-xs text-stone-700 cursor-pointer select-none">
                <input
                  type="checkbox"
                  data-testid="contact-visit"
                  checked={form.visit_requested}
                  onChange={(e) => setForm({ ...form, visit_requested: e.target.checked })}
                  className="h-4 w-4 rounded border-stone-300 text-[#0B1E3F] focus:ring-[#C19A6B]"
                />
                {t("cloud.contact_visit")}
              </label>

              <label className="flex items-start gap-2.5 text-xs leading-relaxed text-stone-600 cursor-pointer select-none">
                <input
                  type="checkbox"
                  data-testid="contact-gdpr"
                  required
                  checked={form.gdpr_consent}
                  onChange={(e) => setForm({ ...form, gdpr_consent: e.target.checked })}
                  className="mt-0.5 h-4 w-4 rounded border-stone-300 text-[#0B1E3F] focus:ring-[#C19A6B]"
                />
                <span>{t("cloud.contact_gdpr")}</span>
              </label>

              {error && (
                <p data-testid="contact-error" className="text-xs text-rose-700 bg-rose-50 border border-rose-200/80 rounded-xl px-3 py-2">
                  {error}
                </p>
              )}

              <button
                type="submit"
                data-testid="contact-submit"
                disabled={busy}
                className="w-full rounded-xl bg-[#0B1E3F] py-3 text-xs font-medium uppercase tracking-[0.2em] text-white transition duration-200 hover:bg-[#C19A6B] hover:shadow-[0_12px_28px_-14px_rgba(193,154,107,0.9)] disabled:opacity-50"
              >
                {busy ? t("cloud.contact_submitting") : t("cloud.contact_submit")}
              </button>
            </form>
          )
        )}
      </div>
    </div>
  );
}

/* Schema.org RealEstateListing JSON-LD for SEO + sharing rich previews */
function SchemaOrgJsonLd({ prop, publicUrl }) {
  const data = {
    "@context": "https://schema.org",
    "@type": "RealEstateListing",
    name: prop.title,
    description: prop.description,
    url: publicUrl,
    address: {
      "@type": "PostalAddress",
      addressLocality: prop.city,
      addressRegion: prop.province,
      postalCode: prop.postal_code,
      addressCountry: "IT",
    },
    ...(prop.lat && prop.lng ? {
      geo: { "@type": "GeoCoordinates", latitude: prop.lat, longitude: prop.lng }
    } : {}),
    ...(prop.price ? {
      offers: { "@type": "Offer", price: prop.price, priceCurrency: "EUR" }
    } : {}),
    ...(prop.surface_sqm ? {
      floorSize: { "@type": "QuantitativeValue", value: prop.surface_sqm, unitCode: "MTK" }
    } : {}),
  };
  return (
    <script
      type="application/ld+json"
      data-testid="schema-jsonld"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, "\\u003c") }}
    />
  );
}

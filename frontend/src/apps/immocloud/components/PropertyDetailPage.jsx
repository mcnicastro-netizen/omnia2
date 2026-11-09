/* OMNIA — Public Property Detail Page (M3.S4)
 *
 * Public landing page for a single property listed on ImmobilCloud.
 * Path: /it/cloud/property/:pid
 *
 * MOVE-ONLY split: propertyDetailUtils · ShareBar · InfoCell · Contact · Schema.
 */
import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { MapContainer, TileLayer, Marker } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { api } from "../../../shared/lib/api";
import { useAuth } from "../../../shared/lib/auth";
import { energyClassLabel } from "../../../shared/lib/energyClasses";
import ContactPanel from "./PropertyDetailContact";
import { InfoCell } from "./PropertyDetailInfoCell";
import SchemaOrgJsonLd from "./PropertyDetailSchema";
import ShareBar from "./PropertyDetailShareBar";
import {
  BACKEND_URL,
  estimateInstallment,
  formatPrice,
} from "./propertyDetailUtils";

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
  const [videoErr, setVideoErr] = useState("");
  const [scout, setScout] = useState(null);
  const [scoutBusy, setScoutBusy] = useState(false);
  const [scoutErr, setScoutErr] = useState("");
  const { user } = useAuth();
  const isB2c = Boolean(user && user.account_type === "b2c");
  const isLister = Boolean(prop?.viewer_is_lister);

  const scoutGradeLabel = (grade) =>
    ({ A: "Ottima", B: "Buona", C: "Sufficiente", D: "Da completare" }[grade] || "");

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
    setActivePhoto(0);
    api.get(`/cloud/property/${pid}`)
      .then((r) => {
        const data = r.data;
        setProp(data);
        // Hero = cover scelta dal venditore (anche render). Evitare di forzare
        // la prima foto «reale»: spesso è uno scatto basso (~600px) che in header
        // full-bleed diventa sfocato; il render cover è tipicamente più definito.
        const ph = data?.photos || [];
        const coverIdx = ph.findIndex((p) => p?.is_cover);
        setActivePhoto(coverIdx >= 0 ? coverIdx : 0);
      })
      .catch((e) => setError(e?.response?.status === 404 ? "not_found" : "fetch_error"))
      .finally(() => setLoading(false));
  }, [pid]);

  // P-055 — tab title per-property (SSR/OG handled in preview-server)
  useEffect(() => {
    if (!prop) return;
    const prev = document.title;
    const title = (prop.title || prop.city || "Immobile").toString().slice(0, 80);
    document.title = `${title} · ImmobilCloud`;
    return () => { document.title = prev; };
  }, [prop]);

  const resolveVideoPlayUrl = (data) => {
    if (!data?.id) return null;
    const rel =
      (data.download_url && String(data.download_url)) ||
      `/api/app/videos/${data.id}/download`;
    if (rel.startsWith("http://") || rel.startsWith("https://")) return rel;
    return `${BACKEND_URL}${rel.startsWith("/") ? rel : `/${rel}`}`;
  };

  useEffect(() => {
    if (!pid) return;
    api.get(`/cloud/videos/by-property/${pid}`)
      .then((r) => {
        if (r.data?.status === "ready" && r.data?.id) {
          setVideoUrl(resolveVideoPlayUrl(r.data));
        } else {
          setVideoUrl(null);
        }
      })
      .catch(() => setVideoUrl(null));
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
    setVideoErr("");
    try {
      const { data } = await api.post(`/cloud/videos/kenburns/property/${pid}`, { duration_s: 15 });
      const poll = async (n = 0) => {
        if (n > 40) {
          setVideoErr("Generazione troppo lenta. Riprova tra un minuto.");
          return;
        }
        const st = await api.get(`/cloud/videos/${data.video_id}`);
        if (st.data.status === "ready") {
          setVideoUrl(resolveVideoPlayUrl(st.data));
          return;
        }
        if (st.data.status === "failed") {
          const detail = st.data.error || "generation_failed";
          setVideoErr(
            detail === "no_photos_downloaded"
              ? "Non siamo riusciti a leggere le foto per il video. Riprova o ricarica le immagini."
              : detail === "video_expired"
                ? "Il video precedente non è più disponibile. Rigeneralo."
                : `Video non generato (${detail}). Riprova.`
          );
          return;
        }
        await new Promise((r) => setTimeout(r, 1500));
        return poll(n + 1);
      };
      await poll();
    } catch (e) {
      console.error(e);
      setVideoErr(e?.response?.data?.detail || "Video tour non disponibile. Riprova.");
    } finally {
      setVideoBusy(false);
    }
  };

  const deleteVideo = async () => {
    if (!pid || videoBusy) return;
    const ok = window.confirm(
      t(
        "cloud.sell.video_delete_confirm",
        "Eliminare il video tour da questo annuncio? La scheda pubblica non lo mostrerà più. Potrai generarne uno nuovo quando vuoi."
      )
    );
    if (!ok) return;
    setVideoBusy(true);
    setVideoErr("");
    try {
      await api.delete(`/cloud/me/properties/${pid}/video`);
      setVideoUrl(null);
    } catch (e) {
      setVideoErr(
        e?.response?.data?.detail ||
          t("cloud.sell.video_delete_failed", "Non siamo riusciti a eliminare il video. Riprova.")
      );
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

  const energy = prop.energy?.energy_class
    ? energyClassLabel(prop.energy.energy_class)
    : "—";
  const features = Object.entries(prop.features || {}).filter(([_, v]) => v).map(([k]) => k);

  return (
    <div data-testid="property-detail-page">
      <SchemaOrgJsonLd prop={prop} publicUrl={publicUrl} />

      {/* Dominant gallery plane */}
      <section className="relative bg-[#0B1E3F]">
        {photos.length > 0 ? (
          <div data-testid="detail-gallery" className="relative">
            <div className="aspect-[16/10] md:aspect-[21/9] max-h-[70vh] overflow-hidden bg-stone-900 flex items-center justify-center">
              <img
                src={`${BACKEND_URL}${cover.url}`}
                alt={cover.caption || prop.title}
                className="w-full h-full object-cover object-center"
                decoding="async"
              />
              <div
                className="absolute inset-0 pointer-events-none"
                style={{
                  background:
                    "linear-gradient(180deg, rgba(11,30,63,0.15) 0%, rgba(11,30,63,0.05) 40%, rgba(11,30,63,0.75) 100%)",
                }}
              />
              {cover?.is_virtual_staging && (
                <p
                  data-testid="staging-disclosure"
                  className="absolute top-4 left-4 md:left-8 z-10 max-w-sm text-[11px] uppercase tracking-widest text-white bg-black/60 px-3 py-1.5 rounded"
                >
                  {t(
                    "cloud.staging_disclosure",
                    "Render virtuale — immagine generata, non fotografia reale"
                  )}
                </p>
              )}
            </div>
            {photos.length > 1 && (
              <div className="absolute bottom-4 left-0 right-0 px-5 sm:px-8 md:px-16">
                <div className="max-w-6xl mx-auto flex gap-2 overflow-x-auto pb-1 justify-center sm:justify-start">
                  {photos.map((ph, i) => (
                    <button
                      key={i}
                      data-testid={`detail-thumb-${i}`}
                      onClick={() => setActivePhoto(i)}
                      className={`relative shrink-0 w-16 h-16 md:w-20 md:h-20 rounded-lg overflow-hidden border-2 transition ${
                        i === activePhoto ? "border-white" : "border-white/30 opacity-80 hover:opacity-100"
                      }`}
                    >
                      <img src={`${BACKEND_URL}${ph.url}`} alt="" className="w-full h-full object-cover" />
                      {ph?.is_virtual_staging && (
                        <span className="absolute bottom-0 inset-x-0 text-[8px] uppercase tracking-wider text-white bg-black/65 text-center py-0.5">
                          Render
                        </span>
                      )}
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
                              : "Ecco come un acquirente legge il tuo annuncio oggi. La fascia prezzo è un indizio di zona, non un giudizio sulla tua richiesta.")
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
                            {(scout.completeness?.grade_label_it || scoutGradeLabel(scout.completeness?.grade)) && (
                              <span className="text-sm font-normal text-stone-600">
                                {" "}· {scout.completeness?.grade_label_it || scoutGradeLabel(scout.completeness?.grade)}
                              </span>
                            )}
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
                                  {isLister ? "Come si colloca la richiesta" : "Perché lo diciamo"}
                                </p>
                                <ul className="text-sm text-stone-800 space-y-1.5 list-disc pl-4 leading-relaxed">
                                  {scout.price_vs_zone.why
                                    .filter((w) => w?.key !== "source" && !String(w?.label_it || "").toLowerCase().startsWith("fonte zona"))
                                    .map((w) => (
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

            {/* Micro-tour — play pubblico; genera soprattutto da Vendi (proprietario) */}
            {(videoUrl || isLister) && (
            <div data-testid="detail-micro-tour" className="border border-stone-200 rounded-2xl p-5 bg-white">
              <div className="flex items-center justify-between gap-3 mb-3">
                <div>
                  <h2 className="text-[11px] uppercase tracking-[0.28em] text-[#C19A6B]">Micro-tour</h2>
                  {isLister && !videoUrl && (
                    <p className="text-xs text-stone-500 mt-1">
                      Genera il video da Area riservata → Vendi, subito dopo le foto.
                    </p>
                  )}
                </div>
                {isLister && !videoUrl && photos.length > 0 && (
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
              {videoErr && (
                <p className="text-sm text-rose-700 mb-2" data-testid="detail-video-error">{String(videoErr)}</p>
              )}
              {videoUrl ? (
                <div className="space-y-2">
                  <div className="mx-auto w-full max-w-3xl rounded-xl overflow-hidden bg-stone-900">
                    <video
                      data-testid="detail-video-player"
                      src={videoUrl}
                      controls
                      playsInline
                      preload="metadata"
                      onError={() => {
                        setVideoUrl(null);
                        setVideoErr(
                          isLister
                            ? "Il video non si riproduce. Rigeneralo da Vendi o qui sotto."
                            : "Video temporaneamente non disponibile."
                        );
                      }}
                      className="block w-full aspect-video object-contain object-center bg-stone-900"
                    />
                  </div>
                  {isLister && (
                    <button
                      type="button"
                      data-testid="detail-delete-video"
                      disabled={videoBusy}
                      onClick={deleteVideo}
                      className="text-xs uppercase tracking-widest text-rose-700 hover:text-rose-900 disabled:opacity-50"
                    >
                      {t("cloud.sell.video_delete", "Elimina video")}
                    </button>
                  )}
                </div>
              ) : isLister ? (
                <p className="text-sm text-stone-500">Nessun video ancora.</p>
              ) : null}
            </div>
            )}

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


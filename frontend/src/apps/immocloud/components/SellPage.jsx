/* OMNIA — B2C Sell Page (M3.S5 v2)
 *
 * Authenticated B2C users (account_type='b2c') can create/edit/submit one free
 * private property listing. If not logged in, redirects to registration with
 * intent=sell prefilled. Shows current listing status and any rejection notes.
 *
 * Media: up to 30 photos + optional floor plan (planimetria) via B2C upload-tmp.
 *
 * MOVE-ONLY split: sellConstants · sellPayload · SellFormPrimitives · SellListingForm.
 */
import React, { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import { useAuth, formatApiErrorDetail } from "../../../shared/lib/auth";
import B2CStagingPanel from "./B2CStagingPanel";
import CloudPageHero from "./CloudPageHero";
import ListingPreviewModal from "./ListingPreviewModal";
import SellDocPromoRail from "./SellDocPromoRail";
import SellListingForm from "./SellListingForm";
import {
  B2C_FEATURES,
  B2C_MAX_PHOTOS,
  B2C_MEDIA_UPLOAD,
  STAGING_PENDING_KEY,
  empty,
} from "./sellConstants";
import { buildListingPayload } from "./sellPayload";
import {
  ListingStatsPanel,
  StatusBadge,
} from "./SellFormPrimitives";

export default function SellPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();
  const { user } = useAuth();
  const [listings, setListings] = useState([]);
  const [editing, setEditing] = useState(null); // listing object or null
  const [form, setForm] = useState(empty);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);

  const [boostCatalog, setBoostCatalog] = useState([]);
  const [publishCatalog, setPublishCatalog] = useState([]);
  const [publishMeta, setPublishMeta] = useState({ free_max: 2, used_slots: 0, unused_credits: 0 });
  const [boostBusy, setBoostBusy] = useState(null); // product_key being purchased
  const [publishBusy, setPublishBusy] = useState(null);
  const [showSlotPaywall, setShowSlotPaywall] = useState(false);
  const [stagingBusy, setStagingBusy] = useState(false);
  const [stagingStatus, setStagingStatus] = useState(""); // progress / wait message after Stripe return
  const [waitTipKey, setWaitTipKey] = useState("cloud.sell.staging_wait_tip");
  const [statsById, setStatsById] = useState({}); // pid → stats payload
  const [previewListing, setPreviewListing] = useState(null); // listing opened in anteprima
  const [previewVideoUrl, setPreviewVideoUrl] = useState(null);
  const stagingPollRef = useRef(null);
  const stagingResumeRef = useRef(false);
  const payReturnRef = useRef(false);

  // Redirect if not logged in or not a B2C user
  useEffect(() => {
    if (user === null) return; // still loading
    if (!user || user.account_type !== "b2c") {
      nav(`/${lang}/cloud/area?intent=sell&next=${encodeURIComponent(`/${lang}/cloud/account/sell`)}`, { replace: true });
    }
  }, [user, lang, nav]);

  const reloadListings = async () => {
    const r = await api.get("/cloud/me/properties");
    const items = r.data.items || [];
    setListings(items);
    const entries = await Promise.all(
      items.map(async (l) => {
        try {
          const s = await api.get(`/cloud/me/properties/${l.id}/stats`, {
            params: { days: 30 },
          });
          return [l.id, s.data];
        } catch {
          return [
            l.id,
            {
              lifetime: {
                views: l.view_count || 0,
                leads: l.lead_count || 0,
              },
              period: { views: 0, leads: 0, contact_rate: null },
              series: [],
            },
          ];
        }
      }),
    );
    setStatsById(Object.fromEntries(entries));
    return items;
  };

  const reloadPublishMeta = async () => {
    try {
      const r = await api.get("/billing/b2c/listing-publish");
      setPublishCatalog(r.data.products || []);
      setPublishMeta({
        free_max: r.data.free_max ?? 2,
        used_slots: r.data.used_slots ?? 0,
        unused_credits: r.data.unused_credits ?? 0,
      });
    } catch {
      /* catalog optional offline */
    }
  };

  // Load listings + boost/publish catalog + per-listing stats (D-093 / A-029)
  useEffect(() => {
    if (user && user.account_type === "b2c") {
      reloadListings().catch(() => {});
      api.get("/billing/b2c/boosts")
        .then((r) => setBoostCatalog(r.data.products || []))
        .catch(() => {});
      reloadPublishMeta();
    }
  }, [user]);

  // P-011 — after Stripe return: start/poll staging job, then refresh photos
  useEffect(() => {
    if (!user || user.account_type !== "b2c") return undefined;
    if (stagingResumeRef.current) return undefined;
    const params = new URLSearchParams(window.location.search);
    const flag = params.get("staging");
    if (flag === "cancel") {
      stagingResumeRef.current = true;
      nav(`/${lang}/cloud/account/sell`, { replace: true });
      return undefined;
    }
    if (flag !== "ok") return undefined;
    stagingResumeRef.current = true;

    const sid =
      params.get("session_id") ||
      (() => {
        try {
          return sessionStorage.getItem("omnia_b2c_checkout_sid") || "";
        } catch {
          return "";
        }
      })();
    let pending = null;
    try {
      pending = JSON.parse(sessionStorage.getItem(STAGING_PENDING_KEY) || "null");
    } catch {
      pending = null;
    }
    const listingId = pending?.listingId || "";
    const pendingPhotoN = (pending?.photoIndex ?? 0) + 1;
    const pendingModeLabel =
      pending?.mode === "empty"
        ? t("cloud.sell.staging_mode_empty")
        : t("cloud.sell.staging_mode_furnish");
    if (sid) {
      try {
        sessionStorage.setItem("omnia_b2c_checkout_sid", sid);
      } catch {
        /* ignore */
      }
    }
    nav(`/${lang}/cloud/account/sell`, { replace: true });
    if (!sid || !listingId) {
      setError(t("cloud.sell.staging_checkout_error"));
      return undefined;
    }

    let cancelled = false;
    setStagingBusy(true);
    setWaitTipKey("cloud.sell.staging_wait_tip");
    setStagingStatus(
      t("cloud.sell.staging_processing_named", {
        photo: t("cloud.sell.staging_photo_n", { n: pendingPhotoN }),
        mode: pendingModeLabel,
      }),
    );
    setError("");

    const finishOk = async (job) => {
      try {
        sessionStorage.removeItem(STAGING_PENDING_KEY);
      } catch {
        /* ignore */
      }
      await reloadListings().catch(() => {});
      const n = (job?.source_photo_index ?? pending?.photoIndex ?? 0) + 1;
      const modeLab =
        (job?.mode || pending?.mode) === "empty"
          ? t("cloud.sell.staging_mode_empty")
          : t("cloud.sell.staging_mode_furnish");
      setStagingStatus(
        t("cloud.sell.staging_done_named", {
          photo: t("cloud.sell.staging_photo_n", { n }),
          mode: modeLab,
        }),
      );
      setStagingBusy(false);
    };

    const fail = (msg) => {
      setError(msg || t("cloud.sell.staging_checkout_error"));
      setStagingStatus("");
      setStagingBusy(false);
    };

    async function run() {
      try {
        let paid = false;
        for (let i = 0; i < 30 && !cancelled; i += 1) {
          const st = await api.get(`/billing/b2c/status/${sid}`);
          if (st.data?.status === "paid") {
            paid = true;
            break;
          }
          await new Promise((r) => {
            stagingPollRef.current = setTimeout(r, 1500);
          });
        }
        if (cancelled) return;
        if (!paid) {
          fail(t("cloud.sell.staging_payment_pending"));
          return;
        }

        const start = await api.post(`/cloud/me/properties/${listingId}/staging`, {
          session_id: sid,
        });
        const jobId = start.data?.job?.id;
        if (!jobId) {
          fail(t("cloud.sell.staging_checkout_error"));
          return;
        }
        // Preview already generated + attached on pay — no second wait
        if (start.data?.job?.status === "done" || start.data?.saved_photo_id) {
          await finishOk(start.data.job);
          return;
        }

        for (let i = 0; i < 60 && !cancelled; i += 1) {
          const jr = await api.get(`/cloud/me/properties/${listingId}/staging/${jobId}`);
          const status = jr.data?.status;
          if (status === "done") {
            await finishOk(jr.data);
            return;
          }
          if (status === "failed") {
            fail(jr.data?.error || t("cloud.sell.staging_failed"));
            return;
          }
          // Already saved from preview promote — job may already be done on first poll
          if (jr.data?.saved_photo_id) {
            await finishOk(jr.data);
            return;
          }
          setStagingStatus(
            t("cloud.sell.staging_processing_named", {
              photo: t("cloud.sell.staging_photo_n", { n: pendingPhotoN }),
              mode: pendingModeLabel,
            }),
          );
          await new Promise((r) => {
            stagingPollRef.current = setTimeout(r, 2500);
          });
        }
        if (!cancelled) fail(t("cloud.sell.staging_timeout"));
      } catch (e) {
        if (!cancelled) {
          fail(
            formatApiErrorDetail(e?.response?.data?.detail) ||
              t("cloud.sell.staging_checkout_error"),
          );
        }
      }
    }
    run();
    return () => {
      cancelled = true;
      if (stagingPollRef.current) clearTimeout(stagingPollRef.current);
    };
  }, [user, lang, nav, t]);

  // Boost / publish return from Stripe — short wait copy + status poll (webhook fallback)
  useEffect(() => {
    if (!user || user.account_type !== "b2c") return undefined;
    if (payReturnRef.current) return undefined;
    const params = new URLSearchParams(window.location.search);
    const kind = params.get("boost") === "ok"
      ? "boost"
      : params.get("publish") === "ok"
        ? "publish"
        : null;
    if (!kind) return undefined;
    payReturnRef.current = true;
    const sid =
      params.get("session_id") ||
      (() => {
        try {
          return sessionStorage.getItem("omnia_b2c_checkout_sid") || "";
        } catch {
          return "";
        }
      })();
    nav(`/${lang}/cloud/account/sell`, { replace: true });

    let cancelled = false;
    setError("");
    setWaitTipKey("cloud.sell.fulfillment_confirming_tip");
    setStagingBusy(true);
    setStagingStatus(t("cloud.sell.fulfillment_confirming"));

    async function run() {
      try {
        if (sid) {
          for (let i = 0; i < 20 && !cancelled; i += 1) {
            const st = await api.get(`/billing/b2c/status/${sid}`);
            if (st.data?.status === "paid") break;
            await new Promise((r) => {
              stagingPollRef.current = setTimeout(r, 1200);
            });
          }
        } else {
          await new Promise((r) => {
            stagingPollRef.current = setTimeout(r, 1500);
          });
        }
        if (cancelled) return;
        await reloadListings().catch(() => {});
        await reloadPublishMeta().catch(() => {});
        setStagingBusy(false);
        setStagingStatus(
          kind === "boost"
            ? t("cloud.sell.fulfillment_boost_ready")
            : t("cloud.sell.fulfillment_publish_ready"),
        );
      } catch {
        if (!cancelled) {
          setStagingBusy(false);
          setStagingStatus(t("cloud.sell.fulfillment_pending_reload"));
        }
      }
    }
    run();
    return () => {
      cancelled = true;
      if (stagingPollRef.current) clearTimeout(stagingPollRef.current);
    };
  }, [user, lang, nav, t]);

  const buyBoost = async (listingId, productKey) => {
    setBoostBusy(productKey);
    setError("");
    try {
      const origin = window.location.origin;
      const { data } = await api.post("/billing/b2c/checkout", {
        product_key: productKey,
        listing_id: listingId,
        success_url: `${origin}/${lang}/cloud/account/sell?boost=ok`,
        cancel_url: `${origin}/${lang}/cloud/account/sell?boost=cancel`,
      });
      if (data?.checkout_url) {
        window.location.href = data.checkout_url;
        return;
      }
      setError(t("cloud.sell.boost_checkout_error"));
    } catch (e) {
      setError(formatApiErrorDetail(e?.response?.data?.detail) || t("cloud.sell.boost_checkout_error"));
    } finally {
      setBoostBusy(null);
    }
  };

  const buyPublishProduct = async (productKey, listingId = null) => {
    setPublishBusy(productKey);
    setError("");
    try {
      const origin = window.location.origin;
      const body = {
        product_key: productKey,
        success_url: `${origin}/${lang}/cloud/account/sell?publish=ok`,
        cancel_url: `${origin}/${lang}/cloud/account/sell?publish=cancel`,
      };
      if (listingId) body.listing_id = listingId;
      const { data } = await api.post("/billing/b2c/checkout", body);
      if (data?.checkout_url) {
        window.location.href = data.checkout_url;
        return;
      }
      setError(t("cloud.sell.publish_checkout_error"));
    } catch (e) {
      setError(formatApiErrorDetail(e?.response?.data?.detail) || t("cloud.sell.publish_checkout_error"));
    } finally {
      setPublishBusy(null);
    }
  };

  const boostActive = (l) => {
    if (!l?.boost_tier || !l?.boost_until) return null;
    const until = Date.parse(l.boost_until);
    if (Number.isNaN(until) || until <= Date.now()) return null;
    return l.boost_tier;
  };

  const startNew = () => {
    setEditing(null);
    setForm({
      ...empty,
      contact_display_name: user?.name?.split?.(" ")?.[0] || "",
      contact_phone: user?.phone || "",
      contact_show_email: true,
    });
    setShowForm(true);
    setError("");
  };

  const startEdit = (listing) => {
    setEditing(listing);
    const cp = listing.contact_public || {};
    const feats = listing.features || {};
    setForm({
      ...empty,
      title: listing.title || "",
      description: listing.description || "",
      property_type: listing.property_type || "appartamento",
      operation: listing.operation || "sale",
      city: listing.city || "",
      zone: listing.zone || "",
      address: listing.address || "",
      street_number: listing.street_number || "",
      postal_code: listing.postal_code || "",
      price: listing.price ?? "",
      rent_monthly: listing.rent_monthly ?? "",
      condo_fees: listing.condo_fees ?? "",
      surface_sqm: listing.surface_sqm ?? "",
      rooms: listing.rooms ?? "",
      bedrooms: listing.bedrooms ?? "",
      bathrooms: listing.bathrooms ?? "",
      floor: listing.floor ?? "",
      total_floors: listing.total_floors ?? "",
      year_built: listing.year_built ?? "",
      condition: listing.condition || "",
      energy: {
        energy_class: listing.energy?.energy_class || "",
        heating: listing.energy?.heating || "",
      },
      features: Object.fromEntries(B2C_FEATURES.map((k) => [k, Boolean(feats[k])])),
      photos: Array.isArray(listing.photos) ? listing.photos : [],
      floor_plan_url: listing.floor_plan_url || "",
      contact_display_name: cp.display_name || user?.name?.split?.(" ")?.[0] || "",
      contact_show_email: cp.show_email !== false,
      contact_show_phone: Boolean(cp.show_phone),
      contact_show_whatsapp: Boolean(cp.show_whatsapp),
      contact_phone: cp.phone || "",
      contact_whatsapp: cp.whatsapp || "",
    });
    setShowForm(true);
    setError("");
    // Scroll form into view so "Modifica" is never a no-op
    requestAnimationFrame(() => {
      document.querySelector('[data-testid="sell-form"]')?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  };

  const save = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      const payload = buildListingPayload(form);
      if (payload.photos.length > B2C_MAX_PHOTOS) {
        setError(t("cloud.sell.err_photos_limit"));
        setBusy(false);
        return;
      }

      if (editing) {
        await api.patch(`/cloud/me/properties/${editing.id}`, payload);
      } else {
        await api.post("/cloud/me/properties", payload);
      }
      setShowForm(false);
      setEditing(null);
      setShowSlotPaywall(false);
      await reloadListings();
      await reloadPublishMeta();
    } catch (e) {
      const detail = e?.response?.data?.detail;
      const code = typeof detail === "object" ? detail?.code : detail;
      if (code === "free_tier_listing_limit_reached" || code === "premium_listing_sku_required") {
        setShowSlotPaywall(true);
        setShowForm(false);
        await reloadPublishMeta();
      }
      const formatted = formatApiErrorDetail(detail);
      if (!e?.response) {
        setError(t("cloud.sell.err_save_network"));
      } else if (formatted === "csrf_failed") {
        setError(t("cloud.sell.err_save_csrf"));
      } else {
        setError(formatted || t("cloud.sell.err_save"));
      }
    } finally { setBusy(false); }
  };

  const openPreview = async (listing) => {
    setPreviewListing(listing);
    setPreviewVideoUrl(null);
    if (!listing?.id) return;
    try {
      const { data } = await api.get(`/cloud/me/properties/${listing.id}/video`);
      if (data?.status === "ready" && data?.id) {
        const rel =
          (data.download_url && String(data.download_url)) ||
          `/api/app/videos/${data.id}/download`;
        const base = process.env.REACT_APP_BACKEND_URL || "";
        setPreviewVideoUrl(
          rel.startsWith("http://") || rel.startsWith("https://")
            ? rel
            : `${base}${rel.startsWith("/") ? rel : `/${rel}`}`
        );
      }
    } catch {
      /* nessun video */
    }
    setError("");
  };

  const confirmSubmitFromPreview = async () => {
    if (!previewListing?.id) return;
    setBusy(true); setError("");
    try {
      await api.post(`/cloud/me/properties/${previewListing.id}/submit`);
      setPreviewListing(null);
      const r = await api.get("/cloud/me/properties");
      setListings(r.data.items || []);
    } catch (e) {
      setError(formatApiErrorDetail(e?.response?.data?.detail));
    } finally { setBusy(false); }
  };

  const deleteListing = async (pid) => {
    if (!window.confirm(t("cloud.sell.confirm_delete"))) return;
    setBusy(true); setError("");
    try {
      await api.delete(`/cloud/me/properties/${pid}`);
      setListings(listings.filter((l) => l.id !== pid));
    } catch (e) {
      setError(formatApiErrorDetail(e?.response?.data?.detail));
    } finally { setBusy(false); }
  };

  if (user === null) {
    return <div className="max-w-3xl mx-auto p-6 text-stone-500 text-sm">{t("common.loading")}</div>;
  }
  if (!user || user.account_type !== "b2c") {
    return null; // redirecting
  }

  const slotListings = listings.filter(
    (l) => l.status !== "withdrawn" && l.moderation_status !== "rejected",
  );
  const freeMax = publishMeta.free_max || 2;
  const usedSlots = publishMeta.used_slots ?? slotListings.length;
  const unusedCredits = publishMeta.unused_credits || 0;
  const canCreateFree = usedSlots < freeMax || unusedCredits > 0;
  const slotProducts = publishCatalog.filter((p) => p.listing_slot);
  const addonProducts = publishCatalog.filter((p) => p.listing_addon);

  return (
    <div data-testid="sell-page">
      <CloudPageHero
        eyebrow="ImmobilCloud · Vendi"
        title={t("cloud.sell.title")}
        subtitle={t(
          "cloud.sell.subtitle_scout",
          "Pubblica su ImmobilCloud. Completa l’annuncio: Scout — il nostro fiore all’occhiello — lo legge come un acquirente e ti dice cosa manca."
        )}
        image="/cloud/scout.jpg"
      />

      <div className="max-w-6xl mx-auto px-5 sm:px-8 md:px-12 lg:px-16 py-10">
      <div
        data-testid="sell-scout-banner"
        className="mb-8 rounded-2xl border border-[#C19A6B]/35 bg-[#f7f4ef] px-5 py-4 sm:px-6 sm:py-5"
      >
        <p className="text-[10px] uppercase tracking-[0.28em] text-[#C19A6B] mb-1">
          {t("cloud.sell.scout_eyebrow", "Scout · venditore")}
        </p>
        <p
          className="text-lg sm:text-xl font-light text-[#0B1E3F] leading-snug"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        >
          {t(
            "cloud.sell.scout_title",
            "Più l’annuncio è completo, più Scout convince chi cerca casa."
          )}
        </p>
        <p className="text-sm text-stone-600 mt-1.5 max-w-3xl">
          {t(
            "cloud.sell.scout_text",
            "Foto chiare, APE, metri, prezzo onesto: in scheda pubblica puoi «Guardare con gli occhi di Scout» e vedere cosa migliora prima della visita."
          )}
        </p>
      </div>
      <div className="lg:grid lg:grid-cols-12 lg:gap-8 lg:items-start">
      <div className="lg:col-span-8 min-w-0">
      <div className="mb-5 flex flex-wrap gap-2">
        <Link
          to={`/${lang}/cloud/account/messages`}
          data-testid="sell-goto-messages"
          className="px-4 py-2 text-[11px] uppercase tracking-widest border border-stone-300 rounded-lg text-stone-700 hover:border-[#0B1E3F] hover:text-[#0B1E3F]"
        >
          {t("cloud.sell.goto_messages")}
        </Link>
        <Link
          to={`/${lang}/cloud/account`}
          data-testid="sell-goto-account"
          className="px-4 py-2 text-[11px] uppercase tracking-widest border border-stone-300 rounded-lg text-stone-700 hover:border-[#0B1E3F]"
        >
          {t("cloud.sell.goto_account")}
        </Link>
      </div>
      {error && (
        <div data-testid="sell-error" className="mb-4 text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-xl px-4 py-3">
          {error}
        </div>
      )}
      {stagingStatus && (
        <div
          data-testid="sell-staging-status"
          className={`mb-4 text-xs rounded-xl px-4 py-3 border ${
            stagingBusy
              ? "text-stone-800 bg-amber-50 border-amber-200"
              : "text-stone-800 bg-stone-50 border-stone-200"
          }`}
          role="status"
          aria-live="polite"
        >
          <p className="font-medium">{stagingStatus}</p>
          {stagingBusy ? (
            <p className="mt-1.5 text-stone-600 leading-relaxed" data-testid="sell-staging-wait-tip">
              {t(waitTipKey)}
            </p>
          ) : null}
        </div>
      )}

      {/* Existing listings */}
      {listings.length > 0 && (
        <section data-testid="sell-listings" className="mb-8 space-y-3">
          {listings.map((l) => (
            <article
              key={l.id}
              data-testid={`listing-${l.id}`}
              className="bg-white border border-stone-200 rounded-2xl p-5"
            >
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div className="min-w-0 flex-1">
                  <h2 className="text-base font-medium text-stone-900">{l.title || t("cloud.sell.untitled")}</h2>
                  <p className="text-xs text-stone-600 mt-0.5">
                    {l.city} · {l.property_type}
                    {l.operation === "rent" && l.rent_monthly ? ` · € ${l.rent_monthly.toLocaleString("it-IT")}/mese` :
                     l.price ? ` · € ${l.price.toLocaleString("it-IT")}` : ""}
                  </p>
                  {(l.reference_code || l.client_code) && (
                    <p className="text-[11px] text-stone-500 mt-1 font-mono" data-testid={`listing-codes-${l.id}`}>
                      {l.reference_code ? `${t("cloud.sell.listing_code")}: ${l.reference_code}` : null}
                      {l.reference_code && l.client_code ? " · " : null}
                      {l.client_code ? `${t("cloud.sell.client_code")}: ${l.client_code}` : null}
                    </p>
                  )}
                  {(l.photos?.length > 0 || l.floor_plan_url) && (
                    <p className="text-[11px] text-stone-500 mt-1" data-testid={`listing-media-${l.id}`}>
                      {l.photos?.length > 0 ? `${l.photos.length} ${t("cloud.sell.photos_count")}` : null}
                      {l.photos?.length > 0 && l.floor_plan_url ? " · " : null}
                      {l.floor_plan_url ? t("cloud.sell.has_floor_plan") : null}
                    </p>
                  )}
                  <StatusBadge status={l.moderation_status} listingStatus={l.status} notes={l.moderation_notes} />
                  <ListingStatsPanel stats={statsById[l.id]} t={t} />
                  {boostActive(l) && (
                    <p className="text-[11px] text-emerald-800 mt-1" data-testid={`boost-active-${l.id}`}>
                      {t("cloud.sell.boost_active", {
                        tier: String(boostActive(l)).toUpperCase(),
                        until: new Date(l.boost_until).toLocaleDateString(lang),
                      })}
                      {(l.boost_impression_count || 0) > 0
                        ? ` · ${t("cloud.sell.boost_impressions", { n: l.boost_impression_count })}`
                        : ""}
                    </p>
                  )}
                </div>
                <div className="flex gap-2 flex-wrap">
                  <button
                    type="button"
                    data-testid={`edit-${l.id}`}
                    onClick={() => startEdit(l)}
                    className="px-3 py-1.5 text-[11px] uppercase tracking-widest border border-stone-300 rounded hover:bg-stone-50"
                  >
                    {t("common.edit")}
                  </button>
                  <button
                    type="button"
                    data-testid={`preview-${l.id}`}
                    onClick={() => openPreview(l)}
                    className="px-3 py-1.5 text-[11px] uppercase tracking-widest border border-stone-300 rounded hover:bg-stone-50"
                  >
                    {t("cloud.sell.preview_btn")}
                  </button>
                  {l.moderation_status === "approved" && l.status === "active" && (
                    <Link
                      to={`/${lang}/cloud/property/${l.id}`}
                      data-testid={`view-live-${l.id}`}
                      className="px-3 py-1.5 text-[11px] uppercase tracking-widest bg-[#0B1E3F] text-white rounded hover:bg-[#C19A6B]"
                    >
                      {t("cloud.sell.view_live_btn", "Vedi online")}
                    </Link>
                  )}
                  {!(l.moderation_status === "approved" && l.status === "active") && (
                    <button
                      type="button"
                      data-testid={`submit-${l.id}`}
                      onClick={() => openPreview(l)}
                      disabled={busy}
                      className="px-3 py-1.5 text-[11px] uppercase tracking-widest bg-[#0B1E3F] text-white rounded hover:bg-[#C19A6B] disabled:opacity-50"
                    >
                      {l.moderation_status === "rejected"
                        ? t("cloud.sell.resubmit")
                        : t("cloud.sell.submit_review")}
                    </button>
                  )}
                  <button
                    type="button"
                    data-testid={`delete-${l.id}`}
                    onClick={() => deleteListing(l.id)}
                    className="px-3 py-1.5 text-[11px] uppercase tracking-widest text-rose-700 border border-rose-200 rounded hover:bg-rose-50"
                  >
                    {t("common.delete")}
                  </button>
                </div>
              </div>
              <B2CStagingPanel
                listingId={l.id}
                photos={l.photos || []}
                busy={stagingBusy}
                setBusy={setStagingBusy}
                onStatus={setStagingStatus}
                onError={setError}
                onPaidAttached={() => reloadListings().catch(() => {})}
                testIdPrefix={`staging-${l.id}`}
              />
              {addonProducts.length > 0 && (
                <div className="mt-4 pt-4 border-t border-stone-100" data-testid={`addon-panel-${l.id}`}>
                  <p className="text-[11px] uppercase tracking-widest text-stone-500 mb-2">
                    {t("cloud.sell.addon_title")}
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {addonProducts.map((p) => {
                      const bought =
                        (p.listing_addon === "hide_address" && l.hide_address_paid) ||
                        (p.listing_addon === "photo_pack" && (l.photo_pack_extra || 0) >= 10);
                      return (
                        <button
                          key={p.key}
                          type="button"
                          data-testid={`addon-buy-${p.key}`}
                          disabled={!!publishBusy || bought}
                          onClick={() => buyPublishProduct(p.key, l.id)}
                          className="text-left px-3 py-2.5 border border-stone-200 rounded hover:border-[#0B1E3F] hover:bg-stone-50 disabled:opacity-50 transition"
                        >
                          <div className="text-xs font-medium text-stone-900">{p.label_it}</div>
                          <div className="text-sm text-[#0B1E3F] mt-0.5">
                            € {Number(p.price_eur).toLocaleString("it-IT", { minimumFractionDigits: 2 })}
                          </div>
                          <div className="text-[10px] uppercase tracking-widest text-stone-500 mt-1">
                            {bought
                              ? t("cloud.sell.addon_owned")
                              : publishBusy === p.key
                                ? t("common.saving")
                                : t("cloud.sell.boost_cta")}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
              {boostCatalog.length > 0 && (
                <div className="mt-4 pt-4 border-t border-stone-100" data-testid={`boost-panel-${l.id}`}>
                  <p className="text-[11px] uppercase tracking-widest text-stone-500 mb-2">
                    {t("cloud.sell.boost_title")}
                  </p>
                  <p className="text-xs text-stone-600 mb-3">{t("cloud.sell.boost_subtitle")}</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                    {boostCatalog.map((p) => (
                      <button
                        key={p.key}
                        type="button"
                        data-testid={`boost-buy-${p.key}`}
                        disabled={!!boostBusy}
                        onClick={() => buyBoost(l.id, p.key)}
                        className="text-left px-3 py-2.5 border border-stone-200 rounded hover:border-[#0B1E3F] hover:bg-stone-50 disabled:opacity-50 transition"
                      >
                        <div className="text-xs font-medium text-stone-900">{p.label_it}</div>
                        <div className="text-sm text-[#0B1E3F] mt-0.5">
                          € {Number(p.price_eur).toLocaleString("it-IT", { minimumFractionDigits: 2 })}
                        </div>
                        <div className="text-[10px] uppercase tracking-widest text-stone-500 mt-1">
                          {boostBusy === p.key ? t("common.saving") : t("cloud.sell.boost_cta")}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </article>
          ))}
        </section>
      )}

      {/* CTA new listing — fino a 2 gratis; oltre: paywall slot */}
      {!showForm && canCreateFree && (
        <button
          data-testid="sell-new-btn"
          onClick={startNew}
          className="w-full md:w-auto px-6 py-3 bg-[#0B1E3F] text-white text-sm uppercase tracking-widest rounded hover:bg-[#C19A6B] transition"
        >
          + {t("cloud.sell.create_listing")}
        </button>
      )}
      {!showForm && (!canCreateFree || showSlotPaywall) && slotProducts.length > 0 && (
        <div
          data-testid="sell-slot-paywall"
          className="mt-4 mb-6 border border-stone-200 rounded-2xl p-5 bg-stone-50"
        >
          <p className="text-sm font-medium text-stone-900">{t("cloud.sell.slot_paywall_title")}</p>
          <p className="text-xs text-stone-600 mt-1 mb-3">
            {t("cloud.sell.slot_paywall_subtitle", { free: freeMax })}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {slotProducts.map((p) => (
              <button
                key={p.key}
                type="button"
                data-testid={`slot-buy-${p.key}`}
                disabled={!!publishBusy}
                onClick={() => buyPublishProduct(p.key)}
                className="text-left px-3 py-2.5 border border-stone-200 bg-white rounded hover:border-[#0B1E3F] disabled:opacity-50"
              >
                <div className="text-xs font-medium text-stone-900">{p.label_it}</div>
                <div className="text-sm text-[#0B1E3F] mt-0.5">
                  € {Number(p.price_eur).toLocaleString("it-IT", { minimumFractionDigits: 2 })}
                </div>
                <div className="text-[10px] uppercase tracking-widest text-stone-500 mt-1">
                  {publishBusy === p.key ? t("common.saving") : t("cloud.sell.boost_cta")}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
      {!showForm && usedSlots > 0 && (
        <p data-testid="sell-limit-notice" className="text-xs text-stone-500 italic mt-2">
          {t("cloud.sell.free_limit_notice", {
            used: usedSlots,
            free: freeMax,
            credits: unusedCredits,
          })}
        </p>
      )}

      {/* Form */}
      {showForm && (
        <SellListingForm
          form={form}
          setForm={setForm}
          editing={editing}
          busy={busy}
          user={user}
          save={save}
          onCancel={() => { setShowForm(false); setEditing(null); }}
          stagingBusy={stagingBusy}
        />
      )}
      </div>

      <SellDocPromoRail className="mt-8 lg:mt-0 lg:col-span-4 lg:sticky lg:top-24" />
      </div>
      </div>

      <ListingPreviewModal
        open={!!previewListing}
        listing={previewListing}
        videoUrl={previewVideoUrl}
        busy={busy}
        onClose={() => { setPreviewListing(null); setPreviewVideoUrl(null); }}
        onConfirm={confirmSubmitFromPreview}
        showConfirm={!(previewListing?.moderation_status === "approved" && previewListing?.status === "active")}
        confirmLabel={
          previewListing?.moderation_status === "rejected"
            ? t("cloud.sell.resubmit")
            : t("cloud.sell.preview_confirm")
        }
      />
    </div>
  );
}


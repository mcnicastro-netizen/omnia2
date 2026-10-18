import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import { formatApiErrorDetail } from "../../../shared/lib/auth";

const STAGING_PENDING_KEY = "omnia_staging_pending";

/**
 * B2C Virtual Staging — choose photo + mode, free preview, then pay €0,90 to save.
 */
export default function B2CStagingPanel({
  listingId,
  photos = [],
  busy,
  setBusy,
  onStatus,
  onError,
  onPaidAttached,
  testIdPrefix = "staging",
}) {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const usable = useMemo(
    () => (photos || []).map((p, i) => ({ ...p, _idx: i })).filter((p) => p?.url && p.upload_status !== "error"),
    [photos],
  );
  const [photoId, setPhotoId] = useState(usable[0]?.id || "");
  // reverse = svuota+ri-arreda (case reale: foto già arredate). empty = solo svuota.
  // Non usare "standard" (assume stanza già vuota) — è la causa tipica di "Arreda non funziona".
  const [mode, setMode] = useState("reverse"); // reverse | empty
  const [roomType, setRoomType] = useState("bedroom");
  const [style, setStyle] = useState("modern");
  const [preview, setPreview] = useState(null); // { jobId, url, photoId, photoIndex, mode }
  const [localBusy, setLocalBusy] = useState(false);
  const [stageHint, setStageHint] = useState("");

  const selected = usable.find((p) => p.id === photoId) || usable[0];
  const selectedIndex = selected?._idx ?? 0;
  const selectedLabel = t("cloud.sell.staging_photo_n", { n: selectedIndex + 1 });
  const modeLabel =
    mode === "empty" ? t("cloud.sell.staging_mode_empty") : t("cloud.sell.staging_mode_furnish");

  const roomOptions = [
    { key: "bedroom", label: t("cloud.sell.staging_room_bedroom", { defaultValue: "Camera" }) },
    { key: "living", label: t("cloud.sell.staging_room_living", { defaultValue: "Soggiorno" }) },
    { key: "kitchen", label: t("cloud.sell.staging_room_kitchen", { defaultValue: "Cucina" }) },
    { key: "dining", label: t("cloud.sell.staging_room_dining", { defaultValue: "Pranzo" }) },
  ];
  const styleOptions = [
    { key: "modern", label: t("cloud.sell.staging_style_modern", { defaultValue: "Moderno" }) },
    { key: "scandi", label: t("cloud.sell.staging_style_scandi", { defaultValue: "Scandi" }) },
    { key: "classic", label: t("cloud.sell.staging_style_classic", { defaultValue: "Classico" }) },
    { key: "luxury", label: t("cloud.sell.staging_style_luxury", { defaultValue: "Luxury" }) },
  ];

  const stageLabel = (stages) => {
    const running = (stages || []).find((s) => s.status === "running");
    if (!running) return "";
    const map = {
      sam2_mask: t("cloud.sell.staging_stage_mask", { defaultValue: "Analisi stanza…" }),
      furniture_removal: t("cloud.sell.staging_stage_empty", {
        defaultValue: "Svuotamento accurato (può richiedere qualche minuto)…",
      }),
      flux_inpaint: t("cloud.sell.staging_stage_furnish", { defaultValue: "Arredamento virtuale…" }),
      upscale: t("cloud.sell.staging_stage_upscale", { defaultValue: "Rifinitura…" }),
    };
    return map[running.name] || "";
  };

  const runBusy = busy || localBusy;

  const startPreview = async () => {
    if (!listingId || !selected?.id) {
      onError?.(t("cloud.sell.staging_need_listing"));
      return;
    }
    setLocalBusy(true);
    setBusy?.(true);
    onError?.("");
    onStatus?.(
      t("cloud.sell.staging_preview_processing", {
        photo: selectedLabel,
        mode: modeLabel,
      }),
    );
    setPreview(null);
    setStageHint("");
    try {
      const { data } = await api.post(`/cloud/me/properties/${listingId}/staging/preview`, {
        photo_id: selected.id,
        mode,
        room_type: roomType,
        style,
      });
      const jobId = data?.job?.id;
      if (!jobId) throw new Error("no_job");
      let done = null;
      // Sequential erase can take 3–5 minutes — poll ~7.5 min
      for (let i = 0; i < 180; i += 1) {
        const jr = await api.get(`/cloud/me/properties/${listingId}/staging/${jobId}`);
        if (jr.data?.status === "done") {
          done = jr.data;
          break;
        }
        if (jr.data?.status === "failed") {
          throw new Error(jr.data?.error || "staging_failed");
        }
        const hint = stageLabel(jr.data?.stages);
        setStageHint(hint);
        onStatus?.(
          hint ||
            t("cloud.sell.staging_preview_processing", {
              photo: selectedLabel,
              mode: modeLabel,
            }),
        );
        await new Promise((r) => setTimeout(r, 2500));
      }
      if (!done) {
        onError?.(t("cloud.sell.staging_timeout"));
        onStatus?.("");
        setStageHint("");
        return;
      }
      const url = done.variant_url || done.variants?.[0]?.url;
      if (!url) {
        throw new Error(t("cloud.sell.staging_checkout_error"));
      }
      setPreview({
        jobId,
        url,
        photoId: done.source_photo_id || selected.id,
        photoIndex: done.source_photo_index ?? selectedIndex,
        mode: done.mode || mode,
        sourceUrl: done.source_url || selected.url,
      });
      setStageHint("");
      onStatus?.(
        t("cloud.sell.staging_preview_ready", {
          photo: t("cloud.sell.staging_photo_n", {
            n: (done.source_photo_index ?? selectedIndex) + 1,
          }),
          mode: mode === "empty" ? t("cloud.sell.staging_mode_empty") : t("cloud.sell.staging_mode_furnish"),
        }),
      );
    } catch (e) {
      onError?.(
        formatApiErrorDetail(e?.response?.data?.detail) ||
          e?.message ||
          t("cloud.sell.staging_checkout_error"),
      );
      onStatus?.("");
      setStageHint("");
    } finally {
      setLocalBusy(false);
      setBusy?.(false);
    }
  };

  const payToSave = async () => {
    if (!listingId || !preview?.jobId) return;
    setLocalBusy(true);
    setBusy?.(true);
    onError?.("");
    try {
      try {
        sessionStorage.setItem(
          STAGING_PENDING_KEY,
          JSON.stringify({
            listingId,
            previewJobId: preview.jobId,
            photoId: preview.photoId,
            mode: preview.mode,
            photoIndex: preview.photoIndex,
          }),
        );
      } catch {
        /* ignore */
      }
      const origin = window.location.origin;
      const { data } = await api.post("/billing/b2c/checkout", {
        product_key: "b2c_staging_render",
        listing_id: listingId,
        preview_job_id: preview.jobId,
        photo_id: preview.photoId,
        staging_mode: preview.mode,
        success_url: `${origin}/${lang}/cloud/account/sell?staging=ok`,
        cancel_url: `${origin}/${lang}/cloud/account/sell?staging=cancel`,
      });
      if (data?.checkout_url) {
        if (data.session_id) {
          try {
            sessionStorage.setItem("omnia_b2c_checkout_sid", data.session_id);
          } catch {
            /* ignore */
          }
        }
        window.location.href = data.checkout_url;
        return;
      }
      onError?.(t("cloud.sell.staging_checkout_error"));
    } catch (e) {
      onError?.(formatApiErrorDetail(e?.response?.data?.detail) || t("cloud.sell.staging_checkout_error"));
    } finally {
      setLocalBusy(false);
      setBusy?.(false);
    }
  };

  if (!usable.length) {
    return (
      <div data-testid={`${testIdPrefix}-panel`} className="mt-4 pt-4 border-t border-stone-100">
        <p className="text-[11px] uppercase tracking-widest text-stone-500 mb-2">
          {t("cloud.sell.staging_title")}
        </p>
        <p className="text-[11px] text-stone-500">{t("cloud.sell.staging_need_photos")}</p>
      </div>
    );
  }

  return (
    <div data-testid={`${testIdPrefix}-panel`} className="mt-4 pt-4 border-t border-stone-100 space-y-3">
      <div>
        <p className="text-[11px] uppercase tracking-widest text-stone-500 mb-1">
          {t("cloud.sell.staging_title")}
        </p>
        <p className="text-xs text-stone-600">{t("cloud.sell.staging_subtitle_v2")}</p>
      </div>

      <div>
        <p className="text-[11px] text-stone-500 mb-2">{t("cloud.sell.staging_pick_photo")}</p>
        <div className="grid grid-cols-3 sm:grid-cols-4 gap-2" data-testid={`${testIdPrefix}-photo-grid`}>
          {usable.map((p) => {
            const active = (photoId || usable[0]?.id) === p.id;
            return (
              <button
                key={p.id || p._idx}
                type="button"
                data-testid={`${testIdPrefix}-pick-${p._idx}`}
                onClick={() => setPhotoId(p.id)}
                className={`relative aspect-[4/3] rounded overflow-hidden border-2 ${
                  active ? "border-[#0B1E3F]" : "border-stone-200"
                }`}
              >
                <img src={p.url} alt="" className="w-full h-full object-cover" />
                <span className="absolute bottom-1 left-1 bg-black/70 text-white text-[9px] px-1.5 py-0.5 rounded">
                  {t("cloud.sell.staging_photo_n", { n: p._idx + 1 })}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex flex-wrap gap-2" data-testid={`${testIdPrefix}-mode`}>
        <button
          type="button"
          data-testid={`${testIdPrefix}-mode-standard`}
          onClick={() => setMode("reverse")}
          className={`px-3 py-1.5 text-[11px] uppercase tracking-widest rounded border ${
            mode === "reverse"
              ? "bg-[#0B1E3F] text-white border-[#0B1E3F]"
              : "border-stone-300 text-stone-700 hover:bg-stone-50"
          }`}
        >
          {t("cloud.sell.staging_mode_furnish")}
        </button>
        <button
          type="button"
          data-testid={`${testIdPrefix}-mode-empty`}
          onClick={() => setMode("empty")}
          className={`px-3 py-1.5 text-[11px] uppercase tracking-widest rounded border ${
            mode === "empty"
              ? "bg-[#0B1E3F] text-white border-[#0B1E3F]"
              : "border-stone-300 text-stone-700 hover:bg-stone-50"
          }`}
        >
          {t("cloud.sell.staging_mode_empty")}
        </button>
      </div>

      {mode === "reverse" ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" data-testid={`${testIdPrefix}-options`}>
          <label className="block">
            <span className="text-[10px] uppercase tracking-widest text-stone-500">
              {t("cloud.sell.staging_room_label", { defaultValue: "Tipo stanza" })}
            </span>
            <select
              data-testid={`${testIdPrefix}-room`}
              value={roomType}
              onChange={(e) => setRoomType(e.target.value)}
              className="mt-1 w-full text-xs border border-stone-300 rounded px-2 py-1.5 bg-white"
            >
              {roomOptions.map((o) => (
                <option key={o.key} value={o.key}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-[10px] uppercase tracking-widest text-stone-500">
              {t("cloud.sell.staging_style_label", { defaultValue: "Stile" })}
            </span>
            <select
              data-testid={`${testIdPrefix}-style`}
              value={style}
              onChange={(e) => setStyle(e.target.value)}
              className="mt-1 w-full text-xs border border-stone-300 rounded px-2 py-1.5 bg-white"
            >
              {styleOptions.map((o) => (
                <option key={o.key} value={o.key}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      ) : null}

      {!preview?.url ? (
        <div className="space-y-2">
          <button
            type="button"
            data-testid={`${testIdPrefix}-preview-btn`}
            disabled={runBusy || !listingId}
            onClick={startPreview}
            className="px-4 py-2 text-xs uppercase tracking-widest border border-[#0B1E3F] text-[#0B1E3F] rounded hover:bg-[#0B1E3F] hover:text-white disabled:opacity-40 transition"
          >
            {runBusy ? t("common.saving") : t("cloud.sell.staging_preview_cta")}
          </button>
          {runBusy && stageHint ? (
            <p className="text-[11px] text-stone-500" data-testid={`${testIdPrefix}-stage-hint`}>
              {stageHint}
            </p>
          ) : null}
        </div>
      ) : (
        <div className="space-y-3" data-testid={`${testIdPrefix}-preview-result`}>
          <p className="text-xs text-stone-700 font-medium">
            {t("cloud.sell.staging_preview_ready", {
              photo: t("cloud.sell.staging_photo_n", { n: (preview.photoIndex ?? 0) + 1 }),
              mode:
                preview.mode === "empty"
                  ? t("cloud.sell.staging_mode_empty")
                  : t("cloud.sell.staging_mode_furnish"),
            })}
          </p>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-1">
                {t("cloud.sell.staging_before")}
              </p>
              <img
                src={preview.sourceUrl}
                alt=""
                className="w-full aspect-[4/3] object-cover rounded border border-stone-200"
              />
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-1">
                {t("cloud.sell.staging_after")}
              </p>
              <img
                src={preview.url}
                alt=""
                data-testid={`${testIdPrefix}-preview-img`}
                className="w-full aspect-[4/3] object-cover rounded border border-stone-200"
              />
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              data-testid={`${testIdPrefix}-pay-btn`}
              disabled={runBusy}
              onClick={payToSave}
              className="px-4 py-2 text-xs uppercase tracking-widest bg-[#0B1E3F] text-white rounded hover:bg-[#C19A6B] disabled:opacity-40"
            >
              {runBusy ? t("common.saving") : t("cloud.sell.staging_pay_cta")}
            </button>
            <button
              type="button"
              data-testid={`${testIdPrefix}-discard-btn`}
              disabled={runBusy}
              onClick={() => {
                setPreview(null);
                onStatus?.("");
                onPaidAttached?.();
              }}
              className="px-4 py-2 text-xs uppercase tracking-widest border border-stone-300 rounded hover:bg-stone-50"
            >
              {t("cloud.sell.staging_discard")}
            </button>
          </div>
          <p className="text-[11px] text-stone-500">{t("cloud.sell.staging_pay_hint")}</p>
        </div>
      )}
      {!listingId && (
        <p className="text-[11px] text-stone-500">{t("cloud.sell.staging_need_listing")}</p>
      )}
    </div>
  );
}

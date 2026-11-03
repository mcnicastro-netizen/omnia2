import React, { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, resolveMediaUrl } from "../../../shared/lib/api";
import { formatApiErrorDetail } from "../../../shared/lib/auth";

const STAGING_PENDING_KEY = "omnia_staging_pending";

function formatElapsed(sec) {
  const s = Math.max(0, Math.floor(sec || 0));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${String(r).padStart(2, "0")}`;
}

function isPublishableVariant(v) {
  if (!v?.url) return false;
  const verdict = String(v.qa_verdict || "").toUpperCase();
  if (verdict === "REJECT" || verdict === "RETRY" || verdict === "MANUAL_REVIEW") return false;
  if (Array.isArray(v.hard_issues) && v.hard_issues.length) return false;
  if (verdict === "ACCEPT") return true;
  return v.publishable !== false;
}

const ROOM_TAXONOMY_LABELS = {
  living_room: "Soggiorno",
  living: "Soggiorno",
  bedroom: "Camera",
  kitchen: "Cucina",
  bathroom: "Bagno",
  dining_room: "Pranzo",
  dining: "Pranzo",
  office: "Studio",
  hallway: "Corridoio",
  studio: "Monolocale/studio",
  other: "Altro",
  uncertain: "Incerto",
};

/**
 * B2C Virtual Staging — choose photo + mode, free preview, then pay €1,49 to save.
 */
export default function B2CStagingPanel({
  listingId,
  photos = [],
  busy,
  setBusy,
  onStatus,
  onError,
  onPaidAttached,
  /** Optional: persist current form photos to the listing before preview (avoids listing_has_no_photos). */
  onEnsurePhotosSaved = null,
  testIdPrefix = "staging",
}) {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const usable = useMemo(
    () => (photos || []).map((p, i) => ({ ...p, _idx: i })).filter((p) => p?.url && p.upload_status !== "error"),
    [photos],
  );
  const [photoId, setPhotoId] = useState(usable[0]?.id || "");
  // reverse = restyle | empty = svuota | standard = furnish empty room
  const [mode, setMode] = useState("reverse");
  const [roomType, setRoomType] = useState("auto");
  const [roomConfirmed, setRoomConfirmed] = useState(false);
  const [detectedRoom, setDetectedRoom] = useState(null);
  const [style, setStyle] = useState("modern");
  const [multiStyle, setMultiStyle] = useState(true);
  const [preview, setPreview] = useState(null);
  const [localBusy, setLocalBusy] = useState(false);
  const [stageHint, setStageHint] = useState("");
  const [stageRows, setStageRows] = useState([]);
  const [elapsedSec, setElapsedSec] = useState(0);
  const [startedAt, setStartedAt] = useState(null);
  const [archError, setArchError] = useState("");
  const [reportSent, setReportSent] = useState(false);
  const [comparePct, setComparePct] = useState(50);

  const selected = usable.find((p) => p.id === photoId) || usable[0];
  const selectedIndex = selected?._idx ?? 0;
  const selectedLabel = t("cloud.sell.staging_photo_n", { n: selectedIndex + 1 });
  const modeLabel =
    mode === "empty"
      ? t("cloud.sell.staging_mode_empty")
      : mode === "standard"
        ? t("cloud.sell.staging_mode_furnish_empty", { defaultValue: "Arreda (stanza vuota)" })
        : t("cloud.sell.staging_mode_restyle", { defaultValue: "Sostituisci arredi" });

  const roomOptions = [
    { key: "auto", label: t("cloud.sell.staging_room_auto", { defaultValue: "Rileva automaticamente" }) },
    { key: "living", label: t("cloud.sell.staging_room_living", { defaultValue: "Soggiorno" }) },
    { key: "bedroom", label: t("cloud.sell.staging_room_bedroom", { defaultValue: "Camera" }) },
    { key: "kitchen", label: t("cloud.sell.staging_room_kitchen", { defaultValue: "Cucina" }) },
    { key: "dining", label: t("cloud.sell.staging_room_dining", { defaultValue: "Pranzo" }) },
    { key: "office", label: t("cloud.sell.staging_room_office", { defaultValue: "Studio" }) },
  ];
  const modeOptions = [
    {
      key: "reverse",
      label: t("cloud.sell.staging_mode_restyle", { defaultValue: "Sostituisci arredi" }),
      hint: t("cloud.sell.staging_mode_restyle_hint", {
        defaultValue: "Rinnova i mobili senza cambiare la funzione della stanza",
      }),
    },
    {
      key: "empty",
      label: t("cloud.sell.staging_mode_empty"),
      hint: t("cloud.sell.staging_mode_empty_hint", {
        defaultValue: "Rimuove solo arredi mobili, preserva architettura",
      }),
    },
    {
      key: "standard",
      label: t("cloud.sell.staging_mode_furnish_empty", { defaultValue: "Arreda (stanza vuota)" }),
      hint: t("cloud.sell.staging_mode_furnish_hint", {
        defaultValue: "Inserisce arredi in una stanza già vuota",
      }),
    },
  ];
  const styleOptions = [
    { key: "modern", label: t("cloud.sell.staging_style_modern", { defaultValue: "Moderno" }) },
    { key: "scandi", label: t("cloud.sell.staging_style_scandi", { defaultValue: "Scandi" }) },
    { key: "classic", label: t("cloud.sell.staging_style_classic", { defaultValue: "Classico" }) },
    { key: "luxury", label: t("cloud.sell.staging_style_luxury", { defaultValue: "Luxury" }) },
  ];

  const detectedLabel = (() => {
    if (!detectedRoom) return null;
    const tax = detectedRoom.room_type || detectedRoom.room_type_internal;
    const conf = detectedRoom.room_type_confidence;
    const name =
      ROOM_TAXONOMY_LABELS[tax] ||
      roomOptions.find((o) => o.key === detectedRoom.room_type_internal)?.label ||
      tax;
    const pct = typeof conf === "number" ? ` · ${Math.round(conf * 100)}%` : "";
    return `${name}${pct}`;
  })();

  const stageLabel = (stages) => {
    const running = (stages || []).find((s) => s.status === "running");
    if (!running) return "";
    if (running.name === "sam2_mask") {
      if (String(running.note || "").includes("analysis")) {
        return t("cloud.sell.staging_stage_analysis", {
          defaultValue: "Analisi ambiente e vincoli architettonici…",
        });
      }
      return t("cloud.sell.staging_stage_mask", { defaultValue: "Preparazione…" });
    }
    if (running.name === "furniture_removal") {
      return t("cloud.sell.staging_stage_empty", {
        defaultValue: "Svuotamento accurato (può richiedere qualche minuto)…",
      });
    }
    if (running.name === "flux_inpaint") {
      if (mode === "empty") {
        return t("cloud.sell.staging_stage_empty", {
          defaultValue: "Svuotamento accurato (può richiedere qualche minuto)…",
        });
      }
      return t("cloud.sell.staging_stage_furnish", {
        defaultValue: multiStyle
          ? "Arredamento AI — 4 stili in parallelo…"
          : "Arredamento virtuale AI…",
      });
    }
    if (running.name === "upscale") {
      return t("cloud.sell.staging_stage_upscale", { defaultValue: "Controllo qualità…" });
    }
    return "";
  };

  const stagingErrorMessage = (err) => {
    const detail = err?.response?.data?.detail;
    const code =
      (detail && typeof detail === "object" && (detail.error || detail.code)) ||
      (typeof detail === "string" ? detail : null);
    if (code === "listing_has_no_photos") {
      return t("cloud.sell.staging_err_no_photos", {
        defaultValue:
          "Salva l'annuncio con le foto caricate, poi riprova Genera anteprima.",
      });
    }
    if (code === "preview_daily_cap") {
      return (
        (detail && typeof detail === "object" && detail.message) ||
        t("cloud.sell.staging_err_daily_cap", {
          defaultValue: "Hai raggiunto il limite di 3 anteprime staging al giorno.",
        })
      );
    }
    return (
      formatApiErrorDetail(detail) ||
      err?.message ||
      t("cloud.sell.staging_checkout_error")
    );
  };

  const runBusy = busy || localBusy;

  const startPreview = async () => {
    if (!listingId) {
      onError?.(t("cloud.sell.staging_need_listing"));
      return;
    }
    if (!selected?.url) {
      onError?.(
        t("cloud.sell.staging_err_no_photos", {
          defaultValue: "Seleziona una foto caricata prima di generare l'anteprima.",
        }),
      );
      return;
    }
    setLocalBusy(true);
    setBusy?.(true);
    onError?.("");
    setArchError("");
    setDetectedRoom(null);
    setReportSent(false);
    setStartedAt(Date.now());
    setElapsedSec(0);
    setStageRows([]);
    onStatus?.(
      t("cloud.sell.staging_preview_processing", {
        photo: selectedLabel,
        mode: modeLabel,
      }),
    );
    setPreview(null);
    setStageHint("");
    try {
      if (typeof onEnsurePhotosSaved === "function") {
        setStageHint(
          t("cloud.sell.staging_stage_mask", { defaultValue: "Salvataggio foto…" }),
        );
        await onEnsurePhotosSaved();
      }
      const wantMulti = mode === "reverse" && multiStyle;
      const { data } = await api.post(`/cloud/me/properties/${listingId}/staging/preview`, {
        photo_id: selected.id || undefined,
        mode,
        room_type: roomType || "auto",
        room_type_confirmed: Boolean(roomConfirmed && roomType && roomType !== "auto"),
        style,
        variant_mode: wantMulti ? "multi_style" : "same_style",
        num_variants: wantMulti ? 4 : 1,
        styles: wantMulti ? ["modern", "scandi", "classic", "luxury"] : undefined,
      });
      const jobId = data?.job?.id;
      if (!jobId) throw new Error("no_job");
      let done = null;
      for (let i = 0; i < 200; i += 1) {
        const jr = await api.get(`/cloud/me/properties/${listingId}/staging/${jobId}`);
        if (jr.data?.room_analysis) setDetectedRoom(jr.data.room_analysis);
        if (jr.data?.status === "done") {
          done = jr.data;
          setStageRows(jr.data?.stages || []);
          break;
        }
        if (jr.data?.status === "failed") {
          const errMsg = jr.data?.error || "";
          if (String(errMsg).includes("architecture_reject")) {
            setArchError(
              t("cloud.sell.staging_arch_reject", {
                defaultValue:
                  "Risultato scartato: non rispetta l'architettura dell'immobile. Nessun addebito — riprova o conferma il tipo stanza.",
              }),
            );
          }
          throw new Error(
            errMsg ||
              t("cloud.sell.staging_preview_failed", {
                defaultValue: "Anteprima fallita. Nessun addebito: puoi riprovare gratis.",
              }),
          );
        }
        setStageRows(jr.data?.stages || []);
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
        onError?.(
          t("cloud.sell.staging_preview_timeout", {
            defaultValue:
              "L'anteprima sta impiegando troppo. Nessun pagamento in corso: riprova tra un minuto.",
          }),
        );
        onStatus?.("");
        setStageHint("");
        return;
      }
      if (done.room_analysis) setDetectedRoom(done.room_analysis);
      const variants = (done.variants || []).filter((v) => isPublishableVariant(v));
      const url = variants[0]?.url || done.variant_url;
      if (!url || !variants.length) {
        setArchError(
          t("cloud.sell.staging_arch_reject", {
            defaultValue:
              "Nessuna variante ha superato i controlli architettonici. Non pubblicabile.",
          }),
        );
        throw new Error(
          t("cloud.sell.staging_arch_reject", {
            defaultValue:
              "Nessuna variante ha superato i controlli architettonici. Non pubblicabile.",
          }),
        );
      }
      setPreview({
        jobId,
        url,
        photoId: done.source_photo_id || selected.id,
        photoIndex: done.source_photo_index ?? selectedIndex,
        mode: done.mode || mode,
        sourceUrl: done.source_url || selected.url,
        variants,
        selectedStyle: variants[0]?.style || style,
        roomType: done.room_type || variants[0]?.room_type,
        qaSummary: done.qa_summary,
        pipelineId: done.pipeline_id,
      });
      setComparePct(50);
      setStageHint("");
      onStatus?.(
        t("cloud.sell.staging_preview_ready", {
          photo: t("cloud.sell.staging_photo_n", {
            n: (done.source_photo_index ?? selectedIndex) + 1,
          }),
          mode: modeLabel,
        }),
      );
    } catch (e) {
      onError?.(stagingErrorMessage(e));
      onStatus?.("");
      setStageHint("");
    } finally {
      setLocalBusy(false);
      setBusy?.(false);
      setStartedAt(null);
    }
  };

  useEffect(() => {
    if (!localBusy || !startedAt) return undefined;
    const tick = () => setElapsedSec(Math.floor((Date.now() - startedAt) / 1000));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [localBusy, startedAt]);

  const payToSave = async () => {
    if (!listingId || !preview?.jobId) return;
    if (!preview.variants?.some(isPublishableVariant)) {
      setArchError(
        t("cloud.sell.staging_arch_reject", {
          defaultValue: "Questa anteprima non è pubblicabile: non ha superato i controlli.",
        }),
      );
      return;
    }
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

  const reportUnfaithful = async () => {
    if (!preview?.jobId || reportSent) return;
    try {
      await api.post(`/cloud/me/properties/${listingId}/staging/${preview.jobId}/report`, {
        reason: "architecture_unfaithful",
        note: "Segnalazione utente: risultato non fedele all'immobile",
      }).catch(() => null);
    } catch {
      /* best-effort */
    }
    setReportSent(true);
    onStatus?.(
      t("cloud.sell.staging_report_thanks", {
        defaultValue: "Segnalazione registrata. Grazie — aiuta a migliorare ImmobiliCloud.",
      }),
    );
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
                <img src={resolveMediaUrl(p.url)} alt="" className="w-full h-full object-cover" />
                <span className="absolute bottom-1 left-1 bg-black/70 text-white text-[9px] px-1.5 py-0.5 rounded">
                  {t("cloud.sell.staging_photo_n", { n: p._idx + 1 })}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="space-y-2" data-testid={`${testIdPrefix}-mode`}>
        <p className="text-[10px] uppercase tracking-widest text-stone-500">
          {t("cloud.sell.staging_mode_label", { defaultValue: "Modalità" })}
        </p>
        <div className="flex flex-wrap gap-2">
          {modeOptions.map((opt) => (
            <button
              key={opt.key}
              type="button"
              data-testid={`${testIdPrefix}-mode-${opt.key}`}
              title={opt.hint}
              onClick={() => setMode(opt.key)}
              className={`px-3 py-1.5 text-[11px] uppercase tracking-widest rounded border ${
                mode === opt.key
                  ? "bg-[#0B1E3F] text-white border-[#0B1E3F]"
                  : "border-stone-300 text-stone-700 hover:bg-stone-50"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <p className="text-[11px] text-stone-500">
          {modeOptions.find((o) => o.key === mode)?.hint}
        </p>
      </div>

      <div className="space-y-3" data-testid={`${testIdPrefix}-options`}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label className="block">
            <span className="text-[10px] uppercase tracking-widest text-stone-500">
              {t("cloud.sell.staging_room_label", { defaultValue: "Tipo stanza" })}
            </span>
            <select
              data-testid={`${testIdPrefix}-room`}
              value={roomType}
              onChange={(e) => {
                setRoomType(e.target.value);
                setRoomConfirmed(e.target.value !== "auto");
              }}
              className="mt-1 w-full text-xs border border-stone-300 rounded px-2 py-1.5 bg-white"
            >
              {roomOptions.map((o) => (
                <option key={o.key} value={o.key}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          {mode !== "empty" ? (
            <label className="block">
              <span className="text-[10px] uppercase tracking-widest text-stone-500">
                {t("cloud.sell.staging_style_label", { defaultValue: "Stile" })}
              </span>
              <select
                data-testid={`${testIdPrefix}-style`}
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                disabled={mode === "reverse" && multiStyle}
                className="mt-1 w-full text-xs border border-stone-300 rounded px-2 py-1.5 bg-white disabled:opacity-50"
              >
                {styleOptions.map((o) => (
                  <option key={o.key} value={o.key}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
        </div>
        {roomType !== "auto" ? (
          <label className="flex items-start gap-2 text-xs text-stone-700 cursor-pointer">
            <input
              type="checkbox"
              data-testid={`${testIdPrefix}-room-confirm`}
              checked={roomConfirmed}
              onChange={(e) => setRoomConfirmed(e.target.checked)}
              className="mt-0.5"
            />
            <span>
              {t("cloud.sell.staging_room_confirm", {
                defaultValue: "Confermo il tipo stanza selezionato (vincolante per l'AI)",
              })}
            </span>
          </label>
        ) : null}
        {mode === "reverse" ? (
          <label className="flex items-start gap-2 text-xs text-stone-700 cursor-pointer">
            <input
              type="checkbox"
              data-testid={`${testIdPrefix}-multi-style`}
              checked={multiStyle}
              onChange={(e) => setMultiStyle(e.target.checked)}
              className="mt-0.5"
            />
            <span>
              {t("cloud.sell.staging_multi_style", {
                defaultValue: "Mostra 4 stili (moderno, scandi, classico, luxury) e scegli quello che preferisci",
              })}
            </span>
          </label>
        ) : null}
      </div>

      {detectedLabel ? (
        <p className="text-[11px] text-stone-600" data-testid={`${testIdPrefix}-detected-room`}>
          {t("cloud.sell.staging_detected_room", {
            defaultValue: "Ambiente riconosciuto",
          })}
          {": "}
          <span className="font-medium text-stone-800">{detectedLabel}</span>
          {detectedRoom?.needs_user_confirm ? (
            <span className="text-amber-700">
              {" — "}
              {t("cloud.sell.staging_confirm_room_hint", {
                defaultValue: "conferma il tipo se l'AI non è sicura",
              })}
            </span>
          ) : null}
        </p>
      ) : null}

      {archError ? (
        <div
          className="rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-[11px] text-red-800"
          data-testid={`${testIdPrefix}-arch-error`}
          role="alert"
        >
          {archError}
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
            {runBusy
              ? t("cloud.sell.staging_preview_busy", { defaultValue: "Anteprima in corso…" })
              : t("cloud.sell.staging_preview_cta")}
          </button>
          {runBusy ? (
            <div
              className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2.5"
              data-testid={`${testIdPrefix}-wait`}
              role="status"
              aria-live="polite"
            >
              {stageHint ? (
                <p className="text-[11px] font-medium text-stone-800" data-testid={`${testIdPrefix}-stage-hint`}>
                  {stageHint}
                </p>
              ) : null}
              <p className={`text-[11px] text-stone-600 leading-relaxed ${stageHint ? "mt-1" : ""}`}>
                {t("cloud.sell.staging_preview_wait_tip")}
              </p>
              <p className="mt-1 text-[10px] uppercase tracking-widest text-stone-500" data-testid={`${testIdPrefix}-elapsed`}>
                {t("cloud.sell.staging_elapsed", { defaultValue: "Tempo" })}: {formatElapsed(elapsedSec)}
                {stageRows?.length ? ` · ${stageRows.filter((s) => s.status === "done").length}/${stageRows.length}` : ""}
              </p>
            </div>
          ) : null}
        </div>
      ) : (
        <div className="space-y-3" data-testid={`${testIdPrefix}-preview-result`}>
          <p className="text-xs text-stone-700 font-medium">
            {t("cloud.sell.staging_preview_ready", {
              photo: t("cloud.sell.staging_photo_n", { n: (preview.photoIndex ?? 0) + 1 }),
              mode: modeLabel,
            })}
          </p>
          {preview.roomType || preview.qaSummary ? (
            <p className="text-[11px] text-stone-600" data-testid={`${testIdPrefix}-qa-ok`}>
              {t("cloud.sell.staging_qa_passed", {
                defaultValue: "Controlli architettonici superati",
              })}
              {preview.roomType
                ? ` · ${ROOM_TAXONOMY_LABELS[preview.roomType] || preview.roomType}`
                : ""}
              {preview.pipelineId ? ` · ${preview.pipelineId}` : ""}
            </p>
          ) : null}

          <div className="relative aspect-[4/3] rounded overflow-hidden border border-stone-200 select-none" data-testid={`${testIdPrefix}-compare`}>
            <img
              src={resolveMediaUrl(preview.url)}
              alt=""
              className="absolute inset-0 w-full h-full object-cover"
            />
            <div
              className="absolute inset-0 overflow-hidden"
              style={{ width: `${comparePct}%` }}
            >
              <img
                src={resolveMediaUrl(preview.sourceUrl)}
                alt=""
                className="absolute inset-0 h-full object-cover"
                style={{ width: `${10000 / Math.max(comparePct, 1)}%`, maxWidth: "none" }}
              />
            </div>
            <input
              type="range"
              min={5}
              max={95}
              value={comparePct}
              onChange={(e) => setComparePct(Number(e.target.value))}
              className="absolute bottom-2 left-2 right-2 z-10"
              data-testid={`${testIdPrefix}-compare-slider`}
              aria-label="Prima / dopo"
            />
            <span className="absolute top-2 left-2 bg-black/70 text-white text-[9px] px-1.5 py-0.5 rounded">
              {t("cloud.sell.staging_before")}
            </span>
            <span className="absolute top-2 right-2 bg-black/70 text-white text-[9px] px-1.5 py-0.5 rounded">
              {t("cloud.sell.staging_after")}
            </span>
          </div>

          {preview.variants?.length > 1 ? (
            <div data-testid={`${testIdPrefix}-variants`}>
              <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-2">
                {t("cloud.sell.staging_pick_style", { defaultValue: "Scegli lo stile" })}
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {preview.variants.map((v) => {
                  const active = preview.url === v.url;
                  const label =
                    styleOptions.find((o) => o.key === v.style)?.label || v.style || "—";
                  return (
                    <button
                      key={`${v.style}-${v.url}`}
                      type="button"
                      data-testid={`${testIdPrefix}-variant-${v.style || "x"}`}
                      onClick={() =>
                        setPreview((p) =>
                          p ? { ...p, url: v.url, selectedStyle: v.style || p.selectedStyle } : p,
                        )
                      }
                      className={`text-left rounded border overflow-hidden ${
                        active ? "border-[#0B1E3F] ring-1 ring-[#0B1E3F]" : "border-stone-200"
                      }`}
                    >
                      <img src={resolveMediaUrl(v.url)} alt="" className="w-full aspect-[4/3] object-cover" />
                      <span className="block px-1.5 py-1 text-[10px] uppercase tracking-widest text-stone-600">
                        {label}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : null}
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
              data-testid={`${testIdPrefix}-retry-btn`}
              disabled={runBusy}
              onClick={() => {
                setPreview(null);
                setArchError("");
                startPreview();
              }}
              className="px-4 py-2 text-xs uppercase tracking-widest border border-stone-300 rounded hover:bg-stone-50"
            >
              {t("cloud.sell.staging_regenerate", { defaultValue: "Rigenera" })}
            </button>
            <button
              type="button"
              data-testid={`${testIdPrefix}-discard-btn`}
              disabled={runBusy}
              onClick={() => {
                setPreview(null);
                setArchError("");
                onStatus?.("");
                onPaidAttached?.();
              }}
              className="px-4 py-2 text-xs uppercase tracking-widest border border-stone-300 rounded hover:bg-stone-50"
            >
              {t("cloud.sell.staging_discard")}
            </button>
            <button
              type="button"
              data-testid={`${testIdPrefix}-report-btn`}
              disabled={runBusy || reportSent}
              onClick={reportUnfaithful}
              className="px-4 py-2 text-xs uppercase tracking-widest border border-amber-300 text-amber-800 rounded hover:bg-amber-50 disabled:opacity-40"
            >
              {reportSent
                ? t("cloud.sell.staging_report_sent", { defaultValue: "Segnalato" })
                : t("cloud.sell.staging_report", { defaultValue: "Segnala non fedele" })}
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

/**
 * B2C micro-tour (Ken Burns) — destinato al flusso Vendi dopo le foto.
 * Genera / riproduce il video 15s dalle immagini dell'annuncio salvato.
 */
import React, { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function B2CVideoTourPanel({
  listingId,
  photoCount = 0,
  testIdPrefix = "sell-video",
  onError,
}) {
  const { t } = useTranslation();
  const [busy, setBusy] = useState(false);
  const [videoUrl, setVideoUrl] = useState(null);
  const [status, setStatus] = useState("");
  const [err, setErr] = useState("");

  const resolvePlayUrl = (data) => {
    if (!data?.id) return null;
    const rel =
      (data.download_url && String(data.download_url)) ||
      `/api/app/videos/${data.id}/download`;
    if (rel.startsWith("http://") || rel.startsWith("https://")) return rel;
    return `${BACKEND_URL}${rel.startsWith("/") ? rel : `/${rel}`}`;
  };

  const loadExisting = useCallback(async () => {
    if (!listingId) return;
    try {
      const { data } = await api.get(`/cloud/me/properties/${listingId}/video`);
      if (data?.status === "ready" && data?.id) {
        setVideoUrl(resolvePlayUrl(data));
        setStatus("ready");
        setErr("");
      } else if (data?.status === "pending" || data?.status === "processing") {
        setStatus(data.status);
      } else if (data?.status === "failed") {
        setStatus("failed");
        setVideoUrl(null);
        if (data?.error === "video_expired") {
          setErr(
            t(
              "cloud.sell.video_expired",
              "Il video precedente non è più disponibile (redeploy). Rigeneralo dalle foto."
            )
          );
        }
      }
    } catch {
      /* 404 = nessun video ancora */
    }
  }, [listingId, t]);

  useEffect(() => {
    loadExisting();
  }, [loadExisting]);

  const generate = async () => {
    if (!listingId || busy) return;
    if (photoCount < 1) {
      const msg = t(
        "cloud.sell.video_need_photos",
        "Carica almeno una foto (meglio 3+) prima del video tour."
      );
      setErr(msg);
      onError?.(msg);
      return;
    }
    setBusy(true);
    setErr("");
    setStatus("pending");
    try {
      const { data } = await api.post(`/cloud/me/properties/${listingId}/kenburns`, {
        duration_s: 15,
      });
      const vid = data.video_id;
      const poll = async (n = 0) => {
        if (n > 50) {
          setErr(t("cloud.sell.video_timeout", "Generazione troppo lenta. Riprova."));
          setStatus("failed");
          return;
        }
        const st = await api.get(`/cloud/videos/${vid}`);
        if (st.data.status === "ready") {
          setVideoUrl(resolvePlayUrl(st.data));
          setStatus("ready");
          return;
        }
        if (st.data.status === "failed") {
          const detail = st.data.error || "generation_failed";
          const msg =
            detail === "no_photos_downloaded"
              ? t(
                  "cloud.sell.video_no_photos",
                  "Non siamo riusciti a leggere le foto. Salva l'annuncio e riprova."
                )
              : detail === "video_expired"
                ? t(
                    "cloud.sell.video_expired",
                    "Il video precedente non è più disponibile. Rigeneralo dalle foto."
                  )
                : t("cloud.sell.video_failed", "Video non generato. Riprova.");
          setErr(msg);
          setStatus("failed");
          onError?.(msg);
          return;
        }
        setStatus(st.data.status || "processing");
        await new Promise((r) => setTimeout(r, 1500));
        return poll(n + 1);
      };
      await poll();
    } catch (e) {
      const msg =
        e?.response?.data?.detail ||
        t("cloud.sell.video_failed", "Video tour non disponibile. Riprova.");
      setErr(typeof msg === "string" ? msg : JSON.stringify(msg));
      setStatus("failed");
      onError?.(typeof msg === "string" ? msg : "video_failed");
    } finally {
      setBusy(false);
    }
  };

  if (!listingId) {
    return (
      <p className="text-[11px] text-stone-500 mt-3" data-testid={`${testIdPrefix}-need-listing`}>
        {t(
          "cloud.sell.video_need_listing",
          "Salva l'annuncio per generare il video tour dalle foto."
        )}
      </p>
    );
  }

  return (
    <div
      data-testid={testIdPrefix}
      className="mt-4 rounded-xl border border-stone-200 bg-[#f7f4ef] px-4 py-3 space-y-2"
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-[10px] uppercase tracking-[0.22em] text-[#C19A6B]">
            {t("cloud.sell.video_eyebrow", "Video tour")}
          </p>
          <p className="text-sm text-[#0B1E3F] font-medium mt-0.5">
            {t("cloud.sell.video_title", "Micro-tour 15s dalle tue foto")}
          </p>
          <p className="text-xs text-stone-600 mt-1 leading-relaxed">
            {t(
              "cloud.sell.video_hint",
              "Subito dopo le immagini: un video automatico per la scheda pubblica. Più foto nitide = risultato migliore."
            )}
          </p>
        </div>
        {!videoUrl && (
          <button
            type="button"
            data-testid={`${testIdPrefix}-generate`}
            disabled={busy || photoCount < 1}
            onClick={generate}
            className="shrink-0 px-3 py-1.5 text-[11px] uppercase tracking-widest bg-[#0B1E3F] text-white rounded-lg hover:bg-[#C19A6B] disabled:opacity-50 transition"
          >
            {busy
              ? t("cloud.sell.video_generating", "Generazione…")
              : t("cloud.sell.video_generate", "Genera video 15s")}
          </button>
        )}
      </div>
      {status && status !== "ready" && !err && (
        <p className="text-[11px] text-stone-500" data-testid={`${testIdPrefix}-status`}>
          {status === "processing" || status === "pending"
            ? t("cloud.sell.video_status_working", "Preparazione video in corso…")
            : status}
        </p>
      )}
      {err && (
        <p className="text-xs text-rose-700" data-testid={`${testIdPrefix}-error`}>
          {err}
        </p>
      )}
      {videoUrl && (
        <div className="space-y-2">
          <div className="mx-auto w-full max-w-2xl rounded-lg overflow-hidden bg-stone-900">
            <video
              data-testid={`${testIdPrefix}-player`}
              src={videoUrl}
              controls
              playsInline
              preload="metadata"
              onError={() => {
                setVideoUrl(null);
                setStatus("failed");
                setErr(
                  t(
                    "cloud.sell.video_expired",
                    "Il video non si riproduce. Rigeneralo dalle foto."
                  )
                );
              }}
              className="block w-full aspect-video object-contain object-center bg-stone-900"
            />
          </div>
          <button
            type="button"
            data-testid={`${testIdPrefix}-regen`}
            disabled={busy}
            onClick={() => {
              setVideoUrl(null);
              generate();
            }}
            className="text-[11px] uppercase tracking-widest text-[#C19A6B] hover:text-[#0B1E3F]"
          >
            {t("cloud.sell.video_regen", "Rigenera video")}
          </button>
        </div>
      )}
      {!videoUrl && status === "failed" && (
        <button
          type="button"
          data-testid={`${testIdPrefix}-regen-failed`}
          disabled={busy || photoCount < 1}
          onClick={generate}
          className="text-[11px] uppercase tracking-widest text-[#C19A6B] hover:text-[#0B1E3F] disabled:opacity-50"
        >
          {t("cloud.sell.video_regen", "Rigenera video")}
        </button>
      )}
    </div>
  );
}

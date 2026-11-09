/* OMNIA — SellPage form primitives (MOVE-ONLY from SellPage.jsx). */
import React, { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, resolveMediaUrl } from "../../../shared/lib/api";
import { formatApiErrorDetail } from "../../../shared/lib/auth";
import { B2C_MEDIA_UPLOAD } from "./sellConstants";

export const inputCls = "w-full px-3 py-2 border border-stone-300 rounded text-sm focus:outline-none focus:border-[#0B1E3F]";

export function Field({ label, children, required }) {
  return (
    <div>
      <label className="block text-xs uppercase tracking-widest text-stone-500 mb-1.5">
        {label}{required && " *"}
      </label>
      {children}
    </div>
  );
}

export function FloorPlanUploader({ url, onChange }) {
  const { t } = useTranslation();
  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [err, setErr] = useState("");

  const resizeToBlob = (file) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const maxW = 2000;
        let { width, height } = img;
        if (width > maxW) {
          height = Math.round((height * maxW) / width);
          width = maxW;
        }
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        canvas.getContext("2d").drawImage(img, 0, 0, width, height);
        canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error("toBlob failed"))), "image/jpeg", 0.88);
      };
      img.onerror = reject;
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });

  const handleFile = async (file) => {
    if (!file) return;
    const mime = (file.type || "").toLowerCase();
    const name = file.name || "";
    if (mime === "image/heic" || mime === "image/heif" || /\.hei[cf]$/i.test(name)) {
      setErr(t("cloud.sell.err_floor_plan_upload") + " (HEIC non supportato — usa JPEG/PNG)");
      return;
    }
    const okMime = mime.startsWith("image/");
    const okExt = /\.(jpe?g|png|webp)$/i.test(name);
    if (!okMime && !okExt) return;
    setUploading(true);
    setErr("");
    try {
      const blob = await resizeToBlob(file);
      const fd = new FormData();
      fd.append("file", blob, (file.name || "planimetria").replace(/\.[^.]+$/, "") + ".jpg");
      fd.append("kind", "floor_plan");
      // Do NOT set Content-Type: axios/browser must add the multipart boundary.
      const { data } = await api.post(B2C_MEDIA_UPLOAD, fd, { timeout: 45000 });
      onChange(data.url);
    } catch (e) {
      setErr(formatApiErrorDetail(e?.response?.data?.detail) || t("cloud.sell.err_floor_plan_upload"));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div data-testid="floor-plan-uploader" className="space-y-3">
      {!url ? (
        <div
          role="button"
          tabIndex={0}
          data-testid="floor-plan-dropzone"
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); inputRef.current?.click(); } }}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            if (e.dataTransfer.files?.[0]) handleFile(e.dataTransfer.files[0]);
          }}
          className="border-2 border-dashed border-stone-300 rounded-lg p-5 text-center cursor-pointer hover:border-stone-500 hover:bg-stone-50 transition"
        >
          <p className="text-sm text-stone-700 font-medium">
            {uploading ? t("common.saving") : t("cloud.sell.floor_plan_drop")}
          </p>
          <p className="text-xs text-stone-500 mt-1">{t("cloud.sell.floor_plan_formats")}</p>
        </div>
      ) : (
        <div className="relative border border-stone-200 rounded-lg overflow-hidden bg-stone-50 max-w-md">
          <img
            src={resolveMediaUrl(url)}
            alt={t("cloud.sell.f_floor_plan")}
            data-testid="floor-plan-preview"
            className="w-full max-h-64 object-contain bg-white"
          />
          <button
            type="button"
            data-testid="floor-plan-remove"
            onClick={() => onChange("")}
            className="absolute top-2 right-2 bg-red-600 text-white text-xs px-2 py-1 rounded hover:bg-red-700"
          >
            {t("common.delete")}
          </button>
        </div>
      )}
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        data-testid="floor-plan-file-input"
        className="hidden"
        onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
      />
      {err && <p className="text-xs text-rose-700" data-testid="floor-plan-error">{err}</p>}
    </div>
  );
}

export function ListingStatsPanel({ stats, t }) {
  if (!stats) {
    return (
      <p className="text-[11px] text-stone-400 mt-2" data-testid="listing-stats-loading">
        {t("cloud.sell.stats_loading")}
      </p>
    );
  }
  const life = stats.lifetime || {};
  const period = stats.period || {};
  const series = stats.series || [];
  const maxViews = Math.max(1, ...series.map((d) => d.views || 0));
  return (
    <div
      data-testid="listing-stats"
      className="mt-3 rounded-xl bg-[#f7f4ef] border border-stone-200 px-3 py-3"
    >
      <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-2">
        {t("cloud.sell.stats_title")}
      </p>
      <div className="flex flex-wrap gap-4 text-sm text-[#0B1E3F]">
        <div data-testid="stat-views-life">
          <span className="font-medium">{Number(life.views || 0).toLocaleString("it-IT")}</span>
          <span className="text-[11px] text-stone-500 ml-1">{t("cloud.sell.stats_views")}</span>
        </div>
        <div data-testid="stat-leads-life">
          <span className="font-medium">{Number(life.leads || 0).toLocaleString("it-IT")}</span>
          <span className="text-[11px] text-stone-500 ml-1">{t("cloud.sell.stats_leads")}</span>
        </div>
        <div data-testid="stat-period-30">
          <span className="font-medium">{Number(period.views || 0).toLocaleString("it-IT")}</span>
          <span className="text-[11px] text-stone-500 ml-1">{t("cloud.sell.stats_views_30")}</span>
        </div>
        {period.contact_rate != null && (
          <div data-testid="stat-contact-rate">
            <span className="font-medium">{period.contact_rate}%</span>
            <span className="text-[11px] text-stone-500 ml-1">{t("cloud.sell.stats_rate")}</span>
          </div>
        )}
      </div>
      {series.length > 0 && (
        <div
          className="mt-3 flex items-end gap-[2px] h-10"
          data-testid="listing-stats-spark"
          aria-hidden
        >
          {series.map((d) => (
            <span
              key={d.day}
              title={`${d.day}: ${d.views} view`}
              className="flex-1 min-w-0 rounded-sm bg-[#0B1E3F]/70"
              style={{ height: `${Math.max(8, Math.round((100 * (d.views || 0)) / maxViews))}%` }}
            />
          ))}
        </div>
      )}
      <p className="text-[10px] text-stone-500 mt-2 leading-snug">{t("cloud.sell.stats_note")}</p>
    </div>
  );
}

export function StatusBadge({ status, listingStatus, notes }) {
  const { t } = useTranslation();
  const key = status || "none";
  const config = {
    none: { cls: "bg-stone-100 text-stone-800 border-stone-200", label: t("cloud.sell.status_draft") },
    pending: { cls: "bg-amber-100 text-amber-800 border-amber-200", label: t("cloud.sell.status_pending") },
    approved: { cls: "bg-emerald-100 text-emerald-800 border-emerald-200", label: t("cloud.sell.status_approved") },
    rejected: { cls: "bg-rose-100 text-rose-800 border-rose-200", label: t("cloud.sell.status_rejected") },
  }[key] || { cls: "bg-stone-100 text-stone-800 border-stone-200", label: key };
  return (
    <div className="mt-2 flex items-center gap-2 flex-wrap">
      <span data-testid={`status-${key}`}
        className={`inline-block text-[10px] uppercase tracking-widest px-2 py-1 rounded border ${config.cls}`}>
        {config.label}
      </span>
      {listingStatus === "active" && status === "approved" && (
        <span className="text-[10px] text-emerald-700">✓ {t("cloud.sell.status_live")}</span>
      )}
      {status === "rejected" && notes && (
        <span data-testid="rejection-notes" className="text-[11px] text-rose-700 italic">&ldquo;{notes}&rdquo;</span>
      )}
      {status === "pending" && String(notes || "").startsWith("safety_gate:") && (
        <span data-testid="safety-held-hint" className="text-[11px] text-amber-800">
          {t("cloud.sell.safety_held_hint")}
        </span>
      )}
    </div>
  );
}

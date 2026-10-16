import React, { useRef, useState } from "react";
import { api } from "../../../shared/lib/api";

/**
 * PhotoUploader — drag&drop JPEG/PNG/WebP upload with client-side resize.
 *
 * O5 / D-104 — stati espliciti pending → success | error + retry.
 * H10 — upload Object Storage; base64 solo fallback blob piccoli.
 *
 * Props:
 *   photos: [{ id, url, caption?, order, is_cover, upload_status?, upload_error? }]
 *   onChange: (newPhotos) => void
 *   max: max number of photos (default 60)
 *   uploadUrl: override upload endpoint
 *   uploadExtraFields: optional FormData fields
 *   onStage: optional virtual-staging callback
 */

const UPLOAD_CONCURRENCY = 4;
const MAX_W = 1600;
const JPEG_QUALITY = 0.82;

function isHeicLike(file) {
  const t = (file.type || "").toLowerCase();
  if (t === "image/heic" || t === "image/heif") return true;
  return /\.hei[cf]$/i.test(file.name || "");
}

function isLikelyRasterImage(file) {
  if (isHeicLike(file)) return false;
  const t = (file.type || "").toLowerCase();
  if (t === "image/jpeg" || t === "image/png" || t === "image/webp" || t === "image/jpg") {
    return true;
  }
  // Desktop folders often yield empty MIME — fall back to extension.
  if (!t || t === "application/octet-stream") {
    return /\.(jpe?g|png|webp)$/i.test(file.name || "");
  }
  return t.startsWith("image/") && !t.includes("svg");
}

async function resizeToBlob(file) {
  let bitmap = null;
  if (typeof createImageBitmap === "function") {
    try {
      bitmap = await createImageBitmap(file);
    } catch {
      bitmap = null;
    }
  }
  if (bitmap) {
    let { width, height } = bitmap;
    if (width > MAX_W) {
      height = Math.round((height * MAX_W) / width);
      width = MAX_W;
    }
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    canvas.getContext("2d").drawImage(bitmap, 0, 0, width, height);
    bitmap.close?.();
    const blob = await new Promise((resolve, reject) => {
      canvas.toBlob(
        (b) => (b ? resolve(b) : reject(new Error("toBlob failed"))),
        "image/jpeg",
        JPEG_QUALITY
      );
    });
    return blob;
  }

  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        let { width, height } = img;
        if (width > MAX_W) {
          height = Math.round((height * MAX_W) / width);
          width = MAX_W;
        }
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        canvas.getContext("2d").drawImage(img, 0, 0, width, height);
        canvas.toBlob(
          (blob) => (blob ? resolve(blob) : reject(new Error("toBlob failed"))),
          "image/jpeg",
          JPEG_QUALITY
        );
      };
      img.onerror = () => reject(new Error("decode_failed"));
    };
    reader.onerror = () => reject(new Error("read_failed"));
    reader.readAsDataURL(file);
  });
}

function blobToDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

/** Run async work over items with a concurrency cap. */
async function mapPool(items, limit, worker) {
  const results = new Array(items.length);
  let next = 0;
  const runners = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (next < items.length) {
      const i = next;
      next += 1;
      results[i] = await worker(items[i], i);
    }
  });
  await Promise.all(runners);
  return results;
}

export default function PhotoUploader({
  photos = [],
  onChange,
  max = 60,
  onStage = null,
  uploadUrl = "/app/properties/photos/upload-tmp",
  uploadExtraFields = null,
}) {
  const fileInput = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [batchHint, setBatchHint] = useState("");

  const uploadBlob = async (blob, name) => {
    const fd = new FormData();
    fd.append("file", blob, name.replace(/\.[^.]+$/, "") + ".jpg");
    if (uploadExtraFields) {
      Object.entries(uploadExtraFields).forEach(([k, v]) => {
        if (v != null) fd.append(k, String(v));
      });
    }
    // Do NOT set Content-Type: axios/browser must add the multipart boundary.
    const { data } = await api.post(uploadUrl, fd, { timeout: 45000 });
    return data.url;
  };

  const patchPhoto = (id, patch) => {
    onChange(photos.map((p) => (p.id === id ? { ...p, ...patch } : p)));
  };

  const uploadOne = async (photo, blob, fileName) => {
    patchPhoto(photo.id, { upload_status: "pending", upload_error: null });
    try {
      let url;
      try {
        url = await uploadBlob(blob, fileName);
      } catch (err) {
        if (blob.size > 600 * 1024) throw err;
        url = await blobToDataUrl(blob);
      }
      patchPhoto(photo.id, {
        url,
        upload_status: "success",
        upload_error: null,
        _blob: undefined,
        _fileName: undefined,
      });
      return true;
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || "upload_failed";
      patchPhoto(photo.id, {
        upload_status: "error",
        upload_error: typeof msg === "string" ? msg : "upload_failed",
      });
      return false;
    }
  };

  const handleFiles = async (files) => {
    const remaining = max - photos.length;
    const filesArr = Array.from(files).slice(0, remaining);
    if (!filesArr.length) return;
    setUploading(true);
    setBatchHint("");

    const skipped = [];
    const staged = [];

    for (const file of filesArr) {
      if (isHeicLike(file)) {
        skipped.push(`«${file.name}» (HEIC non supportato — esporta JPEG/PNG)`);
        continue;
      }
      if (!isLikelyRasterImage(file)) {
        skipped.push(`«${file.name}» (formato non supportato)`);
        continue;
      }
      try {
        const blob = await resizeToBlob(file);
        const preview = await blobToDataUrl(blob);
        const id = crypto.randomUUID ? crypto.randomUUID() : String(Math.random()).slice(2);
        staged.push({
          id,
          url: preview,
          caption: file.name.replace(/\.[^.]+$/, ""),
          order: photos.length + staged.length,
          is_cover: photos.length + staged.length === 0,
          upload_status: "pending",
          upload_error: null,
          _blob: blob,
          _fileName: file.name,
        });
      } catch {
        skipped.push(`«${file.name}» (non leggibile — prova JPEG/PNG)`);
      }
    }

    if (skipped.length) {
      setBatchHint(
        skipped.length === 1
          ? `Saltata: ${skipped[0]}`
          : `${skipped.length} file saltati: ${skipped.slice(0, 3).join("; ")}${
              skipped.length > 3 ? "…" : ""
            }`
      );
    }

    if (!staged.length) {
      setUploading(false);
      return;
    }

    const next = [...photos, ...staged];
    onChange(next);

    await mapPool(staged, UPLOAD_CONCURRENCY, async (item) => {
      try {
        let url;
        try {
          url = await uploadBlob(item._blob, item._fileName);
        } catch (err) {
          if (item._blob.size > 600 * 1024) throw err;
          url = item.url;
        }
        const idx = next.findIndex((p) => p.id === item.id);
        if (idx >= 0) {
          next[idx] = {
            ...next[idx],
            url,
            upload_status: "success",
            upload_error: null,
          };
          delete next[idx]._blob;
          delete next[idx]._fileName;
        }
        onChange([...next]);
      } catch (err) {
        const msg = err?.response?.data?.detail || err?.message || "upload_failed";
        const idx = next.findIndex((p) => p.id === item.id);
        if (idx >= 0) {
          next[idx] = {
            ...next[idx],
            upload_status: "error",
            upload_error: typeof msg === "string" ? msg : "upload_failed",
          };
        }
        onChange([...next]);
      }
    });

    setUploading(false);
  };

  const retryUpload = async (idx) => {
    const photo = photos[idx];
    if (!photo) return;
    setUploading(true);
    try {
      let blob = photo._blob;
      if (!blob && typeof photo.url === "string" && photo.url.startsWith("data:")) {
        const res = await fetch(photo.url);
        blob = await res.blob();
      }
      if (!blob) {
        patchPhoto(photo.id, { upload_status: "error", upload_error: "retry_needs_reselect" });
        return;
      }
      await uploadOne(photo, blob, photo._fileName || `${photo.caption || "foto"}.jpg`);
    } finally {
      setUploading(false);
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files?.length) handleFiles(e.dataTransfer.files);
  };

  const removePhoto = (idx) => {
    const newPhotos = photos.filter((_, i) => i !== idx).map((p, i) => ({ ...p, order: i }));
    if (newPhotos.length > 0 && !newPhotos.some((p) => p.is_cover)) {
      newPhotos[0].is_cover = true;
    }
    onChange(newPhotos);
  };

  const setCover = (idx) => {
    onChange(photos.map((p, i) => ({ ...p, is_cover: i === idx })));
  };

  const move = (idx, dir) => {
    const newIdx = idx + dir;
    if (newIdx < 0 || newIdx >= photos.length) return;
    const newPhotos = [...photos];
    [newPhotos[idx], newPhotos[newIdx]] = [newPhotos[newIdx], newPhotos[idx]];
    onChange(newPhotos.map((p, i) => ({ ...p, order: i })));
  };

  return (
    <div data-testid="photo-uploader" className="space-y-4">
      <div
        data-testid="photo-dropzone"
        role="button"
        tabIndex={0}
        aria-label="Carica foto: trascina qui i file JPEG, PNG o WebP, oppure premi Invio per selezionarli"
        onClick={() => !uploading && fileInput.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            fileInput.current?.click();
          }
        }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
        className="border-2 border-dashed border-stone-300 rounded-lg p-6 text-center cursor-pointer hover:border-stone-500 hover:bg-stone-50 transition focus:outline-none focus:border-stone-700"
      >
        <p className="text-sm text-stone-700 font-medium">
          Trascina qui le foto JPEG / PNG / WebP
        </p>
        <p className="text-xs text-stone-500 mt-1">
          {uploading
            ? "Caricamento in corso…"
            : `oppure clicca per selezionarle (max ${max} foto, ridotte automaticamente a 1600px)`}
        </p>
        <p className="text-[11px] text-stone-400 mt-2">
          HEIC (iPhone) non supportato: esporta o converti in JPEG prima di caricare.
        </p>
      </div>
      <input
        ref={fileInput}
        type="file"
        accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
        multiple
        data-testid="photo-file-input"
        onChange={(e) => {
          if (e.target.files?.length) handleFiles(e.target.files);
          e.target.value = "";
        }}
        className="hidden"
      />

      {batchHint ? (
        <p data-testid="photo-batch-hint" className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-3 py-2">
          {batchHint}
        </p>
      ) : null}

      {photos.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {photos.map((p, idx) => (
            <div
              key={p.id || idx}
              data-testid={`photo-thumb-${idx}`}
              className={`relative group rounded-lg overflow-hidden border-2 ${
                p.upload_status === "error"
                  ? "border-rose-400"
                  : p.is_cover
                    ? "border-amber-500"
                    : "border-stone-200"
              }`}
            >
              <div className="aspect-[4/3] bg-stone-100">
                <img src={p.url} alt={p.caption || `Foto immobile ${p.order + 1}`} className="w-full h-full object-cover" />
              </div>
              {p.upload_status === "pending" && (
                <span
                  data-testid={`photo-status-pending-${idx}`}
                  className="absolute top-1 right-1 bg-stone-800/80 text-white text-[9px] uppercase tracking-widest px-1.5 py-0.5 rounded"
                >
                  Pending
                </span>
              )}
              {p.upload_status === "error" && (
                <button
                  type="button"
                  data-testid={`photo-retry-${idx}`}
                  onClick={() => retryUpload(idx)}
                  className="absolute inset-x-1 bottom-1 bg-rose-600 text-white text-[10px] uppercase tracking-widest px-2 py-1 rounded"
                >
                  Riprova
                </button>
              )}
              {p.is_cover && p.upload_status !== "error" && (
                <span className="absolute top-1 left-1 bg-amber-500 text-white text-[9px] uppercase tracking-widest px-1.5 py-0.5 rounded">
                  ★ Cover
                </span>
              )}
              <div className="absolute inset-0 bg-stone-900/0 group-hover:bg-stone-900/60 transition opacity-0 group-hover:opacity-100 flex items-center justify-center gap-1">
                {!p.is_cover && (
                  <button
                    type="button"
                    onClick={() => setCover(idx)}
                    data-testid={`photo-set-cover-${idx}`}
                    title="Imposta come copertina"
                    className="bg-amber-500 text-white text-xs px-2 py-1 rounded hover:bg-amber-600"
                  >
                    ★
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => move(idx, -1)}
                  disabled={idx === 0}
                  className="bg-stone-700 text-white text-xs px-2 py-1 rounded hover:bg-stone-900 disabled:opacity-30"
                  title="Sposta a sinistra"
                >
                  ←
                </button>
                <button
                  type="button"
                  onClick={() => move(idx, 1)}
                  disabled={idx === photos.length - 1}
                  className="bg-stone-700 text-white text-xs px-2 py-1 rounded hover:bg-stone-900 disabled:opacity-30"
                  title="Sposta a destra"
                >
                  →
                </button>
                <button
                  type="button"
                  onClick={() => removePhoto(idx)}
                  data-testid={`photo-remove-${idx}`}
                  title="Elimina"
                  className="bg-red-600 text-white text-xs px-2 py-1 rounded hover:bg-red-700"
                >
                  ✕
                </button>
                {onStage && (
                  <button
                    type="button"
                    onClick={() => onStage(p, idx)}
                    data-testid={`photo-stage-${idx}`}
                    title="Arreda questa foto con l'AI (Virtual Staging)"
                    className="bg-emerald-700 text-white text-xs px-2 py-1 rounded hover:bg-emerald-800"
                  >
                    🪄
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {photos.length > 0 && (
        <p className="text-xs text-stone-500">
          {photos.length} / {max} foto · La prima con la stella ★ è la copertina (mostrata in lista immobili)
          {photos.some((p) => p.upload_status === "error")
            ? " · Una o più foto in errore: usa Riprova"
            : ""}
        </p>
      )}
    </div>
  );
}

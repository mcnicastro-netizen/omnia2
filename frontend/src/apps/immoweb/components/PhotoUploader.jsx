import React, { useRef } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";

/**
 * PhotoUploader — drag&drop JPEG/PNG upload with client-side resize.
 *
 * H10 — Photos are uploaded to Object Storage (multipart) and only the media
 * URL is stored in the property document. Base64 data-URL is kept as a
 * fallback if the storage upload fails (preview resilience).
 *
 * Props:
 *   photos: [{ id, url, caption?, order, is_cover }]
 *   onChange: (newPhotos) => void
 *   max: max number of photos (default 15)
 */
export default function PhotoUploader({ photos = [], onChange, max = 15, onStage = null }) {
  const { t } = useTranslation();
  const fileInput = useRef(null);

  const resizeToBlob = (file) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const maxW = 1600;
        let { width, height } = img;
        if (width > maxW) {
          height = Math.round((height * maxW) / width);
          width = maxW;
        }
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, width, height);
        canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error("toBlob failed"))), "image/jpeg", 0.82);
      };
      img.onerror = reject;
      img.src = e.target.result;
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });

  const blobToDataUrl = (blob) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });

  const uploadBlob = async (blob, name) => {
    const fd = new FormData();
    fd.append("file", blob, name.replace(/\.[^.]+$/, "") + ".jpg");
    const { data } = await api.post("/app/properties/photos/upload-tmp", fd, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 45000,
    });
    return data.url;
  };

  const handleFiles = async (files) => {
    const remaining = max - photos.length;
    const filesArr = Array.from(files).slice(0, remaining);
    const newPhotos = [...photos];
    for (const file of filesArr) {
      if (!file.type.startsWith("image/")) continue;
      try {
        const blob = await resizeToBlob(file);
        let url;
        try {
          url = await uploadBlob(blob, file.name);
        } catch {
          // R4 — fallback base64 solo per blob piccoli: mai payload JSON enormi
          if (blob.size > 600 * 1024) continue;
          url = await blobToDataUrl(blob);
        }
        newPhotos.push({
          id: crypto.randomUUID ? crypto.randomUUID() : String(Math.random()).slice(2),
          url,
          caption: file.name.replace(/\.[^.]+$/, ""),
          order: newPhotos.length,
          is_cover: newPhotos.length === 0, // first photo = cover by default
        });
      } catch {
        // skip on error
      }
    }
    onChange(newPhotos);
  };

  const onDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files?.length) handleFiles(e.dataTransfer.files);
  };

  const removePhoto = (idx) => {
    const newPhotos = photos.filter((_, i) => i !== idx).map((p, i) => ({ ...p, order: i }));
    // if removed cover, set first as cover
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
      {/* Dropzone */}
      <div
        data-testid="photo-dropzone"
        role="button"
        tabIndex={0}
        aria-label="Carica foto: trascina qui i file JPEG o PNG, oppure premi Invio per selezionarli"
        onClick={() => fileInput.current?.click()}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.current?.click(); } }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
        className="border-2 border-dashed border-stone-300 rounded-lg p-6 text-center cursor-pointer hover:border-stone-500 hover:bg-stone-50 transition focus:outline-none focus:border-stone-700"
      >
        <p className="text-sm text-stone-700 font-medium">
          📷 Trascina qui le foto JPEG / PNG
        </p>
        <p className="text-xs text-stone-500 mt-1">
          oppure clicca per selezionarle (max {max} foto, ridotte automaticamente a 1600px)
        </p>
      </div>
      <input
        ref={fileInput}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        multiple
        data-testid="photo-file-input"
        onChange={(e) => e.target.files?.length && handleFiles(e.target.files)}
        className="hidden"
      />

      {/* Grid */}
      {photos.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {photos.map((p, idx) => (
            <div
              key={p.id || idx}
              data-testid={`photo-thumb-${idx}`}
              className={`relative group rounded-lg overflow-hidden border-2 ${
                p.is_cover ? "border-amber-500" : "border-stone-200"
              }`}
            >
              <div className="aspect-[4/3] bg-stone-100">
                <img src={p.url} alt={p.caption || `Foto immobile ${p.order + 1}`} className="w-full h-full object-cover" />
              </div>
              {p.is_cover && (
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
        </p>
      )}
    </div>
  );
}

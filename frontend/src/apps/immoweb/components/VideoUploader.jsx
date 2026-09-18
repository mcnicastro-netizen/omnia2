import React, { useRef, useState } from "react";
import { api } from "../../../shared/lib/api";

/**
 * VideoUploader — MP4 / WEBM / MOV for property listings.
 * Max 3 videos · 80 MB each · Object Storage (no base64 fallback).
 */
const ACCEPT = "video/mp4,video/webm,video/quicktime,.mp4,.webm,.mov";
const ALLOWED = new Set(["video/mp4", "video/webm", "video/quicktime"]);
const MAX_BYTES = 80 * 1024 * 1024;

function formatMb(n) {
  if (n == null) return "";
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export default function VideoUploader({
  videos = [],
  onChange,
  max = 3,
  uploadUrl = "/app/properties/videos/upload-tmp",
}) {
  const fileInput = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const handleFiles = async (files) => {
    setError("");
    const remaining = max - videos.length;
    if (remaining <= 0) {
      setError(`Massimo ${max} video per immobile.`);
      return;
    }
    const filesArr = Array.from(files).slice(0, remaining);
    const next = [...videos];
    setBusy(true);
    try {
      for (const file of filesArr) {
        const ct = (file.type || "").toLowerCase();
        if (!ALLOWED.has(ct)) {
          setError("Formato non supportato. Usa MP4, WEBM o MOV.");
          continue;
        }
        if (file.size > MAX_BYTES) {
          setError(`«${file.name}» supera i 80 MB.`);
          continue;
        }
        try {
          const fd = new FormData();
          fd.append("file", file, file.name);
          const { data } = await api.post(uploadUrl, fd, {
            headers: { "Content-Type": "multipart/form-data" },
            timeout: 180000,
          });
          next.push({
            id: data.id || (crypto.randomUUID ? crypto.randomUUID() : String(Math.random()).slice(2)),
            url: data.url,
            caption: file.name.replace(/\.[^.]+$/, ""),
            order: next.length,
            content_type: data.content_type || ct,
            size_bytes: data.size_bytes != null ? data.size_bytes : file.size,
          });
        } catch (err) {
          const detail = err?.response?.data?.detail;
          const code = typeof detail === "string" ? detail : detail?.error;
          if (code === "file_too_large" || err?.response?.status === 413) {
            setError(`«${file.name}» troppo grande (max 80 MB).`);
          } else if (code === "unsupported_media_type" || err?.response?.status === 415) {
            setError("Formato non supportato. Usa MP4, WEBM o MOV.");
          } else {
            setError(`Caricamento fallito per «${file.name}». Riprova.`);
          }
        }
      }
      onChange(next);
    } finally {
      setBusy(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  };

  const removeAt = (idx) => {
    onChange(
      videos.filter((_, i) => i !== idx).map((v, i) => ({ ...v, order: i })),
    );
  };

  const move = (idx, dir) => {
    const newIdx = idx + dir;
    if (newIdx < 0 || newIdx >= videos.length) return;
    const copy = [...videos];
    [copy[idx], copy[newIdx]] = [copy[newIdx], copy[idx]];
    onChange(copy.map((v, i) => ({ ...v, order: i })));
  };

  return (
    <div data-testid="video-uploader" className="space-y-4">
      <div
        data-testid="video-dropzone"
        role="button"
        tabIndex={0}
        aria-label="Carica video: trascina MP4, WEBM o MOV, oppure premi Invio"
        onClick={() => !busy && fileInput.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            if (!busy) fileInput.current?.click();
          }
        }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          if (!busy && e.dataTransfer.files?.length) handleFiles(e.dataTransfer.files);
        }}
        className={`border-2 border-dashed rounded-lg p-6 text-center transition focus:outline-none focus:border-stone-700 ${
          busy
            ? "border-stone-200 bg-stone-50 cursor-wait opacity-70"
            : "border-stone-300 cursor-pointer hover:border-stone-500 hover:bg-stone-50"
        }`}
      >
        <p className="text-sm text-stone-700 font-medium">
          {busy ? "Caricamento video in corso…" : "Trascina qui i video MP4 / WEBM / MOV"}
        </p>
        <p className="text-xs text-stone-500 mt-1">
          oppure clicca per selezionarli (max {max} video · 80 MB ciascuno)
        </p>
      </div>
      <input
        ref={fileInput}
        type="file"
        accept={ACCEPT}
        multiple
        disabled={busy}
        data-testid="video-file-input"
        onChange={(e) => e.target.files?.length && handleFiles(e.target.files)}
        className="hidden"
      />

      {error && (
        <p data-testid="video-upload-error" className="text-sm text-red-700" role="alert">
          {error}
        </p>
      )}

      {videos.length > 0 && (
        <ul className="space-y-3">
          {videos.map((v, idx) => (
            <li
              key={v.id || idx}
              data-testid={`video-item-${idx}`}
              className="rounded-lg border border-stone-200 overflow-hidden bg-stone-50"
            >
              <div className="aspect-video bg-stone-900">
                <video
                  src={v.url}
                  controls
                  preload="metadata"
                  className="w-full h-full object-contain"
                >
                  Il tuo browser non riproduce questo video.
                </video>
              </div>
              <div className="flex items-center justify-between gap-2 px-3 py-2">
                <div className="min-w-0">
                  <p className="text-sm text-stone-800 truncate">
                    {v.caption || `Video ${idx + 1}`}
                  </p>
                  <p className="text-xs text-stone-500">
                    {(v.content_type || "video").replace("video/", "").toUpperCase()}
                    {v.size_bytes != null ? ` · ${formatMb(v.size_bytes)}` : ""}
                  </p>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <button
                    type="button"
                    onClick={() => move(idx, -1)}
                    disabled={idx === 0}
                    className="bg-stone-700 text-white text-xs px-2 py-1 rounded hover:bg-stone-900 disabled:opacity-30"
                    title="Sposta su"
                  >
                    ↑
                  </button>
                  <button
                    type="button"
                    onClick={() => move(idx, 1)}
                    disabled={idx === videos.length - 1}
                    className="bg-stone-700 text-white text-xs px-2 py-1 rounded hover:bg-stone-900 disabled:opacity-30"
                    title="Sposta giù"
                  >
                    ↓
                  </button>
                  <button
                    type="button"
                    onClick={() => removeAt(idx)}
                    data-testid={`video-remove-${idx}`}
                    title="Elimina"
                    className="bg-red-600 text-white text-xs px-2 py-1 rounded hover:bg-red-700"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      {videos.length > 0 && (
        <p className="text-xs text-stone-500">
          {videos.length} / {max} video · L&apos;ordine è quello mostrato sull&apos;annuncio
        </p>
      )}
    </div>
  );
}

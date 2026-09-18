import React, { useRef, useState } from "react";
import { api } from "../../../shared/lib/api";

/**
 * FloorPlanUploader — planimetrie JPEG / PNG / WebP / PDF.
 * Max 5 file · 15 MB ciascuno · Object Storage.
 */
const ACCEPT = "image/jpeg,image/png,image/webp,application/pdf,.jpg,.jpeg,.png,.webp,.pdf";
const ALLOWED = new Set(["image/jpeg", "image/png", "image/webp", "application/pdf"]);
const MAX_BYTES = 15 * 1024 * 1024;
const MAX_W = 2000;

function sniffType(file) {
  const ct = (file.type || "").toLowerCase();
  if (ALLOWED.has(ct)) return ct;
  const name = (file.name || "").toLowerCase();
  if (name.endsWith(".pdf")) return "application/pdf";
  if (name.endsWith(".png")) return "image/png";
  if (name.endsWith(".webp")) return "image/webp";
  if (name.endsWith(".jpg") || name.endsWith(".jpeg")) return "image/jpeg";
  return ct;
}

function isPdf(plan) {
  const ct = (plan.content_type || "").toLowerCase();
  if (ct === "application/pdf") return true;
  return (plan.url || "").toLowerCase().includes(".pdf");
}

function formatMb(n) {
  if (n == null) return "";
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

function resizeImageToJpeg(file) {
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
          0.88
        );
      };
      img.onerror = reject;
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export default function FloorPlanUploader({
  plans = [],
  onChange,
  max = 5,
  uploadUrl = "/app/properties/floor-plans/upload-tmp",
}) {
  const fileInput = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const handleFiles = async (files) => {
    setError("");
    const remaining = max - plans.length;
    if (remaining <= 0) {
      setError(`Massimo ${max} planimetrie per immobile.`);
      return;
    }
    const filesArr = Array.from(files).slice(0, remaining);
    const next = [...plans];
    setBusy(true);
    try {
      for (const file of filesArr) {
        const ct = sniffType(file);
        if (!ALLOWED.has(ct)) {
          setError("Formato non supportato. Usa JPEG, PNG, WebP o PDF.");
          continue;
        }
        if (file.size > MAX_BYTES) {
          setError(`«${file.name}» supera i 15 MB.`);
          continue;
        }
        try {
          let uploadBlob = file;
          let uploadName = file.name || "planimetria";
          let uploadCt = ct;
          if (ct.startsWith("image/")) {
            uploadBlob = await resizeImageToJpeg(file);
            uploadName = uploadName.replace(/\.[^.]+$/, "") + ".jpg";
            uploadCt = "image/jpeg";
          }
          const fd = new FormData();
          fd.append("file", uploadBlob, uploadName);
          const { data } = await api.post(uploadUrl, fd, {
            headers: { "Content-Type": "multipart/form-data" },
            timeout: 60000,
          });
          next.push({
            id: data.id || (crypto.randomUUID ? crypto.randomUUID() : String(Math.random()).slice(2)),
            url: data.url,
            caption: (file.name || "planimetria").replace(/\.[^.]+$/, ""),
            order: next.length,
            content_type: data.content_type || uploadCt,
            size_bytes: data.size_bytes != null ? data.size_bytes : uploadBlob.size,
          });
        } catch (err) {
          const detail = err?.response?.data?.detail;
          const code = typeof detail === "string" ? detail : detail?.error;
          if (code === "file_too_large" || err?.response?.status === 413) {
            setError(`«${file.name}» troppo grande (max 15 MB).`);
          } else if (code === "unsupported_media_type" || err?.response?.status === 415) {
            setError("Formato non supportato. Usa JPEG, PNG, WebP o PDF.");
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
    onChange(plans.filter((_, i) => i !== idx).map((p, i) => ({ ...p, order: i })));
  };

  return (
    <div data-testid="floor-plan-uploader" className="space-y-3">
      <div
        role="button"
        tabIndex={0}
        data-testid="floor-plan-dropzone"
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
        className={`border-2 border-dashed border-stone-300 rounded-lg p-5 text-center transition ${
          busy ? "opacity-50 cursor-wait" : "cursor-pointer hover:border-stone-500 hover:bg-stone-50"
        }`}
      >
        <p className="text-sm text-stone-700 font-medium">
          {busy ? "Caricamento…" : "Trascina qui le planimetrie"}
        </p>
        <p className="text-xs text-stone-500 mt-1">
          oppure clicca per selezionarle · JPEG / PNG / WebP / PDF · max 15 MB · fino a {max}
        </p>
        <input
          ref={fileInput}
          type="file"
          accept={ACCEPT}
          multiple
          className="hidden"
          data-testid="floor-plan-input"
          onChange={(e) => e.target.files?.length && handleFiles(e.target.files)}
        />
      </div>

      {error && (
        <p data-testid="floor-plan-error" className="text-xs text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">
          {error}
        </p>
      )}

      {plans.length > 0 && (
        <ul data-testid="floor-plan-list" className="space-y-2">
          {plans.map((p, idx) => (
            <li
              key={p.id || idx}
              data-testid={`floor-plan-item-${idx}`}
              className="flex items-center gap-3 border border-stone-200 rounded-lg p-2 bg-white"
            >
              {isPdf(p) ? (
                <a
                  href={p.url}
                  target="_blank"
                  rel="noreferrer"
                  className="w-14 h-14 flex items-center justify-center bg-stone-100 text-[10px] uppercase tracking-widest text-stone-700 rounded shrink-0 hover:bg-stone-200"
                >
                  PDF
                </a>
              ) : (
                <a href={p.url} target="_blank" rel="noreferrer" className="shrink-0">
                  <img
                    src={p.url}
                    alt={p.caption || `Planimetria ${idx + 1}`}
                    className="w-14 h-14 object-cover rounded"
                  />
                </a>
              )}
              <div className="flex-1 min-w-0">
                <div className="text-sm text-stone-800 truncate">{p.caption || `Planimetria ${idx + 1}`}</div>
                <div className="text-[10px] text-stone-500 uppercase tracking-widest">
                  {isPdf(p) ? "PDF" : "Immagine"}
                  {p.size_bytes != null ? ` · ${formatMb(p.size_bytes)}` : ""}
                </div>
              </div>
              <button
                type="button"
                data-testid={`floor-plan-remove-${idx}`}
                onClick={() => removeAt(idx)}
                className="text-[10px] uppercase tracking-widest text-red-600 hover:text-red-800 px-2"
              >
                Rimuovi
              </button>
            </li>
          ))}
        </ul>
      )}

      {plans.length > 0 && (
        <p className="text-[10px] text-stone-400">{plans.length} / {max} planimetrie</p>
      )}
    </div>
  );
}

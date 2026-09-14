/*
 * OMNIA — M5.S4.2 StagingStudio (componente riusabile Virtual Staging)
 *
 * Usato da: VirtualStagingPage (standalone) + PropertyFormPage (modale "Arreda questa foto").
 * Supporta: Reverse Staging, 1-4 varianti parallele (stesso stile o multi-stile),
 * prompt CRM-aware (via propertyId), salvataggio render come foto annuncio.
 */
import React, { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../../shared/lib/api";

const POLL_INTERVAL = 3500;
const MAX_MB = 12;
const DEFAULT_MULTI = ["modern", "classic", "scandi", "luxury"];

const STAGE_LABELS = {
  sam2_mask: "Segmentazione stanza (SAM 2)",
  furniture_removal: "Rimozione arredo esistente (Reverse)",
  flux_inpaint: "Arredamento AI (Flux)",
  upscale: "Upscale 4x (Real-ESRGAN)",
};

const STAGE_STATUS_LABEL = {
  queued: "In coda",
  running: "Elaborazione...",
  done: "Completato",
  failed: "Errore",
};

const dataUrlToBlob = (dataUrl) => {
  const [meta, b64] = dataUrl.split(",");
  const mime = (meta.match(/:(.*?);/) || [])[1] || "image/jpeg";
  const bin = atob(b64);
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  return new Blob([arr], { type: mime });
};

export default function StagingStudio({ propertyId = null, initialImage = null, onAddPhoto = null }) {
  const [styles, setStyles] = useState({ styles: [], room_types: [] });
  const [selectedStyle, setSelectedStyle] = useState("modern");
  const [selectedRoom, setSelectedRoom] = useState("living");
  const [mode, setMode] = useState("standard");
  const [variantChoice, setVariantChoice] = useState("single"); // single | same4 | multi4
  const [multiStyles, setMultiStyles] = useState(DEFAULT_MULTI);
  const [uploading, setUploading] = useState(false);
  const [sourceUrl, setSourceUrl] = useState("");
  const [sourcePreview, setSourcePreview] = useState("");
  const [generating, setGenerating] = useState(false);
  const [currentJob, setCurrentJob] = useState(null);
  const [error, setError] = useState("");
  const [savedVariants, setSavedVariants] = useState({});
  const [savingVariant, setSavingVariant] = useState(null);
  const pollRef = useRef(null);
  const fileInputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const r = await api.get("/app/staging/styles");
        setStyles(r.data);
      } catch (e) {
        console.error("Failed to load styles:", e);
      }
    })();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  // Preload the source image (dataURL → upload to fal; http URL → use directly)
  useEffect(() => {
    if (!initialImage) return;
    if (initialImage.startsWith("data:")) {
      setSourcePreview(initialImage);
      setUploading(true);
      (async () => {
        try {
          const blob = dataUrlToBlob(initialImage);
          const fd = new FormData();
          fd.append("file", blob, "photo.jpg");
          const r = await api.post("/app/staging/upload", fd, {
            headers: { "Content-Type": "multipart/form-data" },
          });
          setSourceUrl(r.data.url);
        } catch (e) {
          setError("Upload fallito: " + (e.response?.data?.detail || e.message));
        } finally {
          setUploading(false);
        }
      })();
    } else {
      setSourcePreview(initialImage);
      setSourceUrl(initialImage);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialImage]);

  const startPolling = useCallback((jobId) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const r = await api.get(`/app/staging/jobs/${jobId}`);
        setCurrentJob(r.data);
        if (r.data.status === "done" || r.data.status === "failed") {
          clearInterval(pollRef.current);
          pollRef.current = null;
          setGenerating(false);
        }
      } catch (e) {
        console.error("Poll failed:", e);
      }
    }, POLL_INTERVAL);
  }, []);

  const handleFile = useCallback(async (file) => {
    if (!file) return;
    setError("");
    if (!/^image\/(jpe?g|png|webp)$/.test(file.type)) {
      setError("Formato non supportato. Usa JPG, PNG o WEBP.");
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setError(`File troppo grande (max ${MAX_MB} MB).`);
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => setSourcePreview(e.target.result);
    reader.readAsDataURL(file);

    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const r = await api.post("/app/staging/upload", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setSourceUrl(r.data.url);
    } catch (e) {
      setError("Upload fallito: " + (e.response?.data?.detail || e.message));
    } finally {
      setUploading(false);
    }
  }, []);

  const toggleMultiStyle = (key) => {
    setMultiStyles((cur) => {
      if (cur.includes(key)) return cur.length > 1 ? cur.filter((k) => k !== key) : cur;
      return cur.length < 4 ? [...cur, key] : cur;
    });
  };

  const handleGenerate = async () => {
    if (!sourceUrl || generating) return;
    setError("");
    setGenerating(true);
    setCurrentJob(null);
    setSavedVariants({});
    const payload = {
      image_url: sourceUrl,
      room_type: selectedRoom,
      mode,
      property_id: propertyId || undefined,
      style: variantChoice === "multi4" ? multiStyles[0] : selectedStyle,
      num_variants: variantChoice === "single" ? 1 : variantChoice === "same4" ? 4 : multiStyles.length,
      variant_mode: variantChoice === "multi4" ? "multi_style" : "same_style",
      styles: variantChoice === "multi4" ? multiStyles : undefined,
    };
    try {
      const r = await api.post("/app/staging/generate", payload);
      setCurrentJob(r.data);
      startPolling(r.data.id);
    } catch (e) {
      setError("Generazione fallita: " + (e.response?.data?.detail || e.message));
      setGenerating(false);
    }
  };

  const handleDownload = async (variantIdx) => {
    if (!currentJob?.id) return;
    try {
      const r = await api.get(`/app/staging/jobs/${currentJob.id}/download?variant=${variantIdx}`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([r.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `omnia-staging-${currentJob.id.slice(0, 8)}-v${variantIdx}.jpg`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (e) {
      setError("Download fallito: " + e.message);
    }
  };

  const handleSaveVariant = async (variantIdx) => {
    if (!currentJob?.id || savingVariant !== null) return;
    setSavingVariant(variantIdx);
    setError("");
    try {
      if (onAddPhoto) {
        const r = await api.get(`/app/staging/jobs/${currentJob.id}/variants/${variantIdx}/dataurl`);
        onAddPhoto({ url: r.data.data_url, caption: r.data.caption });
      } else if (propertyId) {
        await api.post(`/app/staging/jobs/${currentJob.id}/save-to-property`, {
          variant_index: variantIdx,
        });
      }
      setSavedVariants((s) => ({ ...s, [variantIdx]: true }));
    } catch (e) {
      setError("Salvataggio fallito: " + (e.response?.data?.detail || e.message));
    } finally {
      setSavingVariant(null);
    }
  };

  const handleReset = () => {
    setSourceUrl("");
    setSourcePreview("");
    setCurrentJob(null);
    setError("");
    setSavedVariants({});
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    setGenerating(false);
  };

  const styleLabel = (key) => styles.styles.find((s) => s.key === key)?.label || key;
  const estRenders = variantChoice === "single" ? 1 : variantChoice === "same4" ? 4 : multiStyles.length;
  const estCost = ((mode === "reverse" ? 0.05 : 0) + 0.001 + estRenders * 0.055).toFixed(2);
  const canSave = Boolean(onAddPhoto || propertyId);

  return (
    <div data-testid="staging-studio" className="space-y-6 font-sans">
      {/* ─── Step 1: source photo ─── */}
      <section className="bg-white border border-stone-200 p-6">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-stone-700 mb-4">
          1. Foto della stanza
        </h2>
        {!sourcePreview ? (
          <div
            data-testid="staging-dropzone"
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files?.[0]); }}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed transition-colors p-12 text-center cursor-pointer ${
              dragOver ? "border-amber-500 bg-amber-50" : "border-stone-300 hover:border-stone-400 bg-stone-50"
            }`}
          >
            <p className="text-stone-500 text-sm mb-2">Trascina qui la foto oppure clicca per selezionare</p>
            <p className="text-stone-400 text-xs">JPG · PNG · WEBP · max {MAX_MB} MB</p>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              data-testid="staging-file-input"
              onChange={(e) => handleFile(e.target.files?.[0])}
              className="hidden"
            />
          </div>
        ) : (
          <div className="flex flex-col sm:flex-row gap-6 items-start">
            <img
              src={sourcePreview}
              alt="Sorgente"
              data-testid="staging-source-preview"
              className="w-full sm:w-64 h-auto object-cover border border-stone-200"
            />
            <div className="flex-1 space-y-3">
              {uploading && <p className="text-sm text-amber-700">⏳ Upload in corso...</p>}
              {sourceUrl && !uploading && (
                <p className="text-sm text-emerald-700">✓ Foto pronta per il rendering</p>
              )}
              {!initialImage && (
                <button
                  onClick={handleReset}
                  data-testid="staging-reset-btn"
                  className="text-xs uppercase tracking-widest text-stone-500 hover:text-stone-700 border border-stone-300 px-3 py-1.5"
                >
                  Cambia foto
                </button>
              )}
            </div>
          </div>
        )}
      </section>

      {/* ─── Step 2: params ─── */}
      {sourceUrl && (
        <section className="bg-white border border-stone-200 p-6">
          <h2 className="text-sm font-semibold uppercase tracking-widest text-stone-700 mb-4">
            2. Impostazioni rendering
          </h2>

          {/* Mode toggle */}
          <div className="mb-5">
            <label className="block text-xs uppercase tracking-widest text-stone-500 mb-2">Stato della stanza</label>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setMode("standard")}
                data-testid="staging-mode-standard"
                className={`px-4 py-2 text-sm border transition ${
                  mode === "standard" ? "bg-stone-900 text-white border-stone-900" : "bg-white text-stone-700 border-stone-300 hover:border-stone-500"
                }`}
              >
                🏠 Stanza vuota
              </button>
              <button
                onClick={() => setMode("reverse")}
                data-testid="staging-mode-reverse"
                className={`px-4 py-2 text-sm border transition ${
                  mode === "reverse" ? "bg-stone-900 text-white border-stone-900" : "bg-white text-stone-700 border-stone-300 hover:border-stone-500"
                }`}
              >
                🔄 Già arredata → svuota e ri-arreda
              </button>
            </div>
            {mode === "reverse" && (
              <p className="text-xs text-stone-500 mt-2">
                Reverse Staging: l&apos;AI rimuove l&apos;arredo esistente e ri-arreda con lo stile scelto.
              </p>
            )}
          </div>

          {/* Variant choice */}
          <div className="mb-5">
            <label className="block text-xs uppercase tracking-widest text-stone-500 mb-2">Varianti</label>
            <div className="flex flex-wrap gap-2">
              {[
                { key: "single", label: "1 render" },
                { key: "same4", label: "4 varianti · stesso stile" },
                { key: "multi4", label: "4 stili diversi" },
              ].map((v) => (
                <button
                  key={v.key}
                  onClick={() => setVariantChoice(v.key)}
                  data-testid={`staging-variants-${v.key}`}
                  className={`px-4 py-2 text-sm border transition ${
                    variantChoice === v.key ? "bg-amber-700 text-white border-amber-700" : "bg-white text-stone-700 border-stone-300 hover:border-stone-500"
                  }`}
                >
                  {v.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <label className="block text-xs uppercase tracking-widest text-stone-500 mb-2">
                {variantChoice === "multi4" ? "Stili (max 4)" : "Stile arredamento"}
              </label>
              <div className="flex flex-wrap gap-2">
                {styles.styles.map((s) => {
                  const active = variantChoice === "multi4" ? multiStyles.includes(s.key) : selectedStyle === s.key;
                  return (
                    <button
                      key={s.key}
                      onClick={() => (variantChoice === "multi4" ? toggleMultiStyle(s.key) : setSelectedStyle(s.key))}
                      data-testid={`staging-style-${s.key}`}
                      className={`px-4 py-2 text-sm transition border ${
                        active ? "bg-stone-900 text-white border-stone-900" : "bg-white text-stone-700 border-stone-300 hover:border-stone-500"
                      }`}
                    >
                      {s.label}
                    </button>
                  );
                })}
              </div>
            </div>
            <div>
              <label className="block text-xs uppercase tracking-widest text-stone-500 mb-2">Tipo di stanza</label>
              <div className="flex flex-wrap gap-2">
                {styles.room_types.map((r) => (
                  <button
                    key={r.key}
                    onClick={() => setSelectedRoom(r.key)}
                    data-testid={`staging-room-${r.key}`}
                    className={`px-4 py-2 text-sm transition border ${
                      selectedRoom === r.key ? "bg-stone-900 text-white border-stone-900" : "bg-white text-stone-700 border-stone-300 hover:border-stone-500"
                    }`}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {propertyId && (
            <p className="mt-4 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-2">
              ✨ Prompt CRM-aware attivo: l&apos;AI ottimizzerà l&apos;arredamento per zona, prezzo e target buyer di questo immobile.
            </p>
          )}

          <div className="mt-6 pt-5 border-t border-stone-100 flex items-center justify-between flex-wrap gap-3">
            <p className="text-xs text-stone-500">
              Tempo stimato: {estRenders > 1 ? "90-180" : "60-120"} secondi · Costo: ~${estCost}
            </p>
            <button
              onClick={handleGenerate}
              disabled={!sourceUrl || generating || uploading}
              data-testid="staging-generate-btn"
              className="bg-amber-700 hover:bg-amber-800 disabled:bg-stone-300 text-white text-sm uppercase tracking-widest px-6 py-3 transition"
            >
              {generating ? "Generazione in corso..." : "Genera con AI"}
            </button>
          </div>
        </section>
      )}

      {/* ─── Step 3: progress + results ─── */}
      {currentJob && (
        <section data-testid="staging-progress" className="bg-white border border-stone-200 p-6">
          <h2 className="text-sm font-semibold uppercase tracking-widest text-stone-700 mb-4">3. Pipeline AI</h2>
          {currentJob.crm_context && (
            <p className="text-xs text-emerald-700 mb-3">✨ Contesto CRM: {currentJob.crm_context}</p>
          )}
          <div className="space-y-3">
            {currentJob.stages.map((s, i) => (
              <div key={s.name} data-testid={`staging-stage-${i}`} className="flex items-center justify-between border border-stone-100 px-4 py-3">
                <div className="flex items-center gap-3">
                  <span className="text-sm text-stone-700">{i + 1} · {STAGE_LABELS[s.name] || s.name}</span>
                  {s.status === "running" && <span className="inline-block w-3 h-3 rounded-full bg-amber-500 animate-pulse" />}
                  {s.status === "done" && <span className="text-emerald-600">✓</span>}
                  {s.status === "failed" && <span className="text-red-600">✗</span>}
                </div>
                <div className="text-xs text-stone-500 flex items-center gap-4">
                  <span>{STAGE_STATUS_LABEL[s.status]}</span>
                  {s.duration_ms && <span>{(s.duration_ms / 1000).toFixed(1)}s</span>}
                  {s.cost_usd && <span>${s.cost_usd.toFixed(3)}</span>}
                </div>
              </div>
            ))}
            {currentJob.error && (
              <div className="border border-red-300 bg-red-50 text-red-700 px-4 py-3 text-sm">{currentJob.error}</div>
            )}
          </div>

          {currentJob.status === "done" && (currentJob.variants || []).length > 0 && (
            <div className="mt-6 pt-6 border-t border-stone-100">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <p className="text-xs uppercase tracking-widest text-stone-500 mb-2">Prima</p>
                  <img src={sourcePreview} alt="Prima" className="w-full border border-stone-200" />
                </div>
                {currentJob.variants.map((v, i) => (
                  <div key={i} data-testid={`staging-variant-${i}`}>
                    <p className="text-xs uppercase tracking-widest text-emerald-700 mb-2">
                      Variante {i + 1} · {styleLabel(v.style)}
                    </p>
                    <img src={v.url} alt={`Variante ${i + 1}`} data-testid={`staging-result-img-${i}`} className="w-full border border-emerald-300" />
                    <div className="mt-2 flex flex-wrap gap-2">
                      <button
                        onClick={() => handleDownload(i)}
                        data-testid={`staging-download-btn-${i}`}
                        className="bg-stone-900 hover:bg-stone-700 text-white text-xs uppercase tracking-widest px-3 py-2"
                      >
                        ⬇ Scarica
                      </button>
                      {canSave && (
                        <button
                          onClick={() => handleSaveVariant(i)}
                          disabled={savedVariants[i] || savingVariant !== null}
                          data-testid={`staging-save-variant-${i}`}
                          className={`text-xs uppercase tracking-widest px-3 py-2 transition ${
                            savedVariants[i]
                              ? "bg-emerald-100 text-emerald-700 border border-emerald-300 cursor-default"
                              : "bg-emerald-700 hover:bg-emerald-800 disabled:bg-stone-300 text-white"
                          }`}
                        >
                          {savedVariants[i] ? "✓ Aggiunta all'annuncio" : savingVariant === i ? "Salvataggio..." : "➕ Aggiungi all'annuncio"}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              <p className="mt-5 text-xs text-stone-500">
                Costo totale: ${(currentJob.cost_total_usd || 0).toFixed(3)} · Job {currentJob.id.slice(0, 8)} · Watermark &quot;Render virtuale OMNIA&quot; applicato su download e salvataggio (conformità AGCM).
              </p>
            </div>
          )}
        </section>
      )}

      {error && (
        <div data-testid="staging-error" className="border border-red-300 bg-red-50 text-red-700 px-4 py-3 text-sm">
          {error}
        </div>
      )}
    </div>
  );
}

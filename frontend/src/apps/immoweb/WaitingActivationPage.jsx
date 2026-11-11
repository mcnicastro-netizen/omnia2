import React, { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth, formatApiErrorDetail } from "../../shared/lib/auth";
import { api } from "../../shared/lib/api";
import Brand from "../../shared/components/Brand";

function isPdfName(name = "") {
  return String(name).toLowerCase().endsWith(".pdf");
}

function isImageName(name = "", type = "") {
  const n = String(name).toLowerCase();
  const t = String(type).toLowerCase();
  if (t.startsWith("image/")) return true;
  return [".png", ".jpg", ".jpeg", ".webp"].some((e) => n.endsWith(e));
}

function DocPreview({ title, doc, local, hasDoc, upBusy, agencyReady, inputTestId, onPick, t }) {
  const [remoteUrl, setRemoteUrl] = useState("");
  const filename = local?.name || doc?.filename || "";
  const kind =
    local?.kind ||
    (isPdfName(filename) ? "pdf" : isImageName(filename) ? "image" : "file");
  const src = local?.url || remoteUrl;
  const shown = Boolean(hasDoc && (src || filename));

  useEffect(() => {
    let cancelled = false;
    let created = "";
    // Se non c'è blob locale, scarica via API auth (ops-kyc non è su /api/media pubblico;
    // iframe diretto sarebbe anche bloccato da X-Frame-Options).
    if (local?.url || !doc?.id) {
      setRemoteUrl((prev) => {
        if (prev) {
          try {
            URL.revokeObjectURL(prev);
          } catch {
            /* ignore */
          }
        }
        return "";
      });
      return undefined;
    }
    (async () => {
      try {
        const r = await api.get(`/app/agencies/me/kyc/documents/${doc.id}/file`, {
          responseType: "blob",
          timeout: 60000,
        });
        if (cancelled) return;
        created = URL.createObjectURL(r.data);
        setRemoteUrl((prev) => {
          if (prev) {
            try {
              URL.revokeObjectURL(prev);
            } catch {
              /* ignore */
            }
          }
          return created;
        });
      } catch {
        if (!cancelled) setRemoteUrl("");
      }
    })();
    return () => {
      cancelled = true;
      if (created) {
        try {
          URL.revokeObjectURL(created);
        } catch {
          /* ignore */
        }
      }
    };
  }, [doc?.id, local?.url]);

  return (
    <div
      className={`rounded-md border px-3 py-3 ${
        hasDoc ? "border-emerald-300 bg-emerald-50/70" : "border-stone-200 bg-stone-50"
      }`}
      data-testid={inputTestId.replace("upload", "status")}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs font-medium text-stone-800 normal-case tracking-normal">
          {title}:{" "}
          {hasDoc ? (
            <span className="text-emerald-800">✓ {filename || "caricato"}</span>
          ) : (
            <span className="text-amber-800">manca</span>
          )}
        </p>
        <label className="inline-flex">
          <span className="sr-only">
            {hasDoc ? "Sostituisci" : "Carica"} {title}
          </span>
          <input
            type="file"
            accept="application/pdf,image/png,image/jpeg,image/webp,.pdf,.png,.jpg,.jpeg,.webp"
            disabled={upBusy || !agencyReady}
            data-testid={inputTestId}
            className="sr-only"
            onChange={(e) => {
              const f = e.target.files?.[0];
              onPick(f);
              e.target.value = "";
            }}
          />
          <span
            className={`cursor-pointer text-[10px] uppercase tracking-widest px-3 py-2 border ${
              upBusy || !agencyReady
                ? "opacity-40 pointer-events-none border-stone-300 text-stone-400"
                : "border-[#0B1E3F] text-[#0B1E3F] hover:bg-white"
            }`}
          >
            {hasDoc ? "Sostituisci" : "Carica file"}
          </span>
        </label>
      </div>

      {shown && src ? (
        <div
          className="mt-3 border border-stone-200 bg-white overflow-hidden"
          data-testid={`${inputTestId}-preview`}
        >
          {kind === "image" ? (
            <img
              src={src}
              alt={filename || title}
              className="w-full max-h-56 object-contain bg-stone-50"
            />
          ) : kind === "pdf" ? (
            <iframe title={filename || title} src={src} className="w-full h-56 bg-stone-50" />
          ) : (
            <div className="px-3 py-6 text-center text-xs text-stone-600">{filename}</div>
          )}
          <div className="flex items-center justify-between gap-2 px-3 py-2 border-t border-stone-100">
            <span className="text-[11px] text-stone-600 truncate">{filename}</span>
            <a
              href={src}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 text-[10px] uppercase tracking-widest text-[#1F6B5C] underline"
              data-testid={`${inputTestId}-open`}
            >
              {t("waiting_activation.open_preview", "Apri anteprima")}
            </a>
          </div>
        </div>
      ) : hasDoc && !src ? (
        <p className="mt-2 text-[11px] text-stone-500 normal-case tracking-normal">
          {t("waiting_activation.preview_loading", "Carico anteprima…")}
        </p>
      ) : null}
    </div>
  );
}

/**
 * Sala d'attesa CRM (D-157 gestionale):
 * 1) upload KYC (visura + CI) con anteprima
 * 2) pagamento Stripe
 * 3) attesa Super Admin → password gestionale
 */
export default function WaitingActivationPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const { user, logout, refresh } = useAuth();
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const [agency, setAgency] = useState(null);
  const [paid, setPaid] = useState(false);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [checking, setChecking] = useState(false);
  const [payBusy, setPayBusy] = useState(false);
  const [upBusy, setUpBusy] = useState(false);
  const [localPreviews, setLocalPreviews] = useState({});

  const revokeLocal = useCallback((docType) => {
    setLocalPreviews((prev) => {
      const cur = prev[docType];
      if (cur?.url) {
        try {
          URL.revokeObjectURL(cur.url);
        } catch {
          /* ignore */
        }
      }
      const next = { ...prev };
      delete next[docType];
      return next;
    });
  }, []);

  useEffect(
    () => () => {
      Object.values(localPreviews).forEach((p) => {
        if (p?.url) {
          try {
            URL.revokeObjectURL(p.url);
          } catch {
            /* ignore */
          }
        }
      });
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const loadStatus = useCallback(async () => {
    setErr("");
    try {
      if (typeof refresh === "function") await refresh();
      const r = await api.get("/app/agencies/me");
      const a = r.data;
      setAgency(a);
      const st = a?.activation_status || "active";
      if (st === "active" || user?.role === "super_admin") {
        nav(`/${lang}/app/dashboard`, { replace: true });
        return a;
      }
      try {
        const sub = await api.get("/billing/subscription");
        const s = sub.data?.subscription;
        const ok =
          s && ["active", "trialing", "paid"].includes(String(s.status || "").toLowerCase());
        setPaid(Boolean(ok) || searchParams.get("paid") === "1");
      } catch {
        setPaid(searchParams.get("paid") === "1");
      }
      return a;
    } catch (e) {
      if (e?.response?.status === 404) {
        setErr(
          t(
            "waiting_activation.still_pending",
            "Agenzia ancora in verifica oppure sessione non allineata. Riprova tra un minuto o esci e rientra."
          )
        );
        return null;
      }
      setErr(t("waiting_activation.load_error", "Non riesco a caricare lo stato agenzia."));
      return null;
    }
  }, [lang, nav, refresh, searchParams, t, user?.role]);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const kyc = agency?.kyc || {};
  const kycDocs = Array.isArray(kyc?.documents) ? kyc.documents : [];
  const visuraDoc = [...kycDocs].reverse().find((d) => d?.doc_type === "visura_camerale");
  const idDoc = [...kycDocs].reverse().find((d) => d?.doc_type === "documento_identita");
  const hasVisura = Boolean(kyc?.checklist?.visura_camerale || visuraDoc);
  const hasId = Boolean(kyc?.checklist?.id_titolare || idDoc);
  const kycReady = hasVisura && hasId;
  const readyForOps = kycReady && paid;

  const fileLooksOk = (file) => {
    const ct = (file.type || "").toLowerCase().split(";")[0].trim();
    const name = (file.name || "").toLowerCase();
    if (name.endsWith(".heic") || name.endsWith(".heif") || ct.includes("heic") || ct.includes("heif")) {
      return {
        ok: false,
        msg: t(
          "waiting_activation.doc_heic_error",
          "HEIC non supportato. Su iPhone: Impostazioni → Fotocamera → Formati → Compatibilità massima (JPG), oppure esporta PDF."
        ),
      };
    }
    const okMime = ["application/pdf", "image/png", "image/jpeg", "image/jpg", "image/webp"];
    const okExt = [".pdf", ".png", ".jpg", ".jpeg", ".webp"];
    if (!ct || ct === "application/octet-stream" || ct === "binary/octet-stream") {
      if (okExt.some((e) => name.endsWith(e))) return { ok: true };
      return {
        ok: false,
        msg: t(
          "waiting_activation.doc_type_error",
          "Formato non supportato. Usa PDF, PNG, JPG o WebP."
        ),
      };
    }
    if (okMime.includes(ct) || okExt.some((e) => name.endsWith(e))) return { ok: true };
    return {
      ok: false,
      msg: t(
        "waiting_activation.doc_type_error",
        "Formato non supportato. Usa PDF, PNG, JPG o WebP (niente HEIC/GIF)."
      ),
    };
  };

  const uploadKyc = async (docType, file) => {
    if (!file) return;
    setUpBusy(true);
    setMsg("");
    const check = fileLooksOk(file);
    if (!check.ok) {
      setMsg(check.msg);
      setUpBusy(false);
      return;
    }
    if (file.size > 8 * 1024 * 1024) {
      setMsg(t("waiting_activation.doc_size_error", "File troppo grande (max 8 MB)."));
      setUpBusy(false);
      return;
    }

    // Anteprima locale immediata → certezza visiva prima della risposta API
    try {
      const prev = localPreviews[docType]?.url;
      if (prev) URL.revokeObjectURL(prev);
    } catch {
      /* ignore */
    }
    const localUrl = URL.createObjectURL(file);
    const kind = isPdfName(file.name) || file.type === "application/pdf"
      ? "pdf"
      : isImageName(file.name, file.type)
        ? "image"
        : "file";
    setLocalPreviews((p) => ({
      ...p,
      [docType]: { url: localUrl, name: file.name, kind },
    }));

    try {
      if (typeof refresh === "function") await refresh();
      const fd = new FormData();
      fd.append("file", file, file.name);
      fd.append("doc_type", docType);
      await api.post("/app/agencies/me/kyc/documents", fd, { timeout: 60000 });
      setMsg(
        t("waiting_activation.doc_ok_named", "Caricato: {{name}}").replace(
          "{{name}}",
          file.name || docType
        )
      );
      await loadStatus();
    } catch (e) {
      revokeLocal(docType);
      setMsg(formatApiErrorDetail(e?.response?.data?.detail) || "Upload fallito");
    } finally {
      setUpBusy(false);
    }
  };

  const startPay = async () => {
    setPayBusy(true);
    setMsg("");
    try {
      const tier = agency?.preferred_plan_tier || "pro";
      const r = await api.post("/billing/checkout", {
        plan_tier: tier,
        billing_cycle: "monthly",
      });
      const url = r.data?.checkout_url;
      if (!url) throw new Error("no_checkout_url");
      window.location.href = url;
    } catch (e) {
      const d = e?.response?.data?.detail;
      setMsg(
        (typeof d === "object" && (d.message || d.error)) ||
          d ||
          t("waiting_activation.pay_error", "Checkout non disponibile. Riprova o contatta Ops.")
      );
      setPayBusy(false);
    }
  };

  const onLogout = async () => {
    await logout();
    nav(`/${lang}/login`, { replace: true });
  };

  return (
    <div
      data-testid="waiting-activation"
      className="min-h-screen bg-gradient-to-b from-[#f7f4ef] to-stone-100 flex flex-col"
    >
      <header className="px-6 py-4 flex items-center justify-between border-b border-stone-200/80 bg-white/70 backdrop-blur">
        <Brand>OMNIA</Brand>
        <button
          type="button"
          onClick={onLogout}
          className="text-xs uppercase tracking-widest text-stone-600 hover:text-[#0B1E3F]"
        >
          {t("common.logout", "Esci")}
        </button>
      </header>
      <main className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="max-w-lg w-full space-y-6">
          <div className="text-center space-y-3">
            <p className="text-[10px] uppercase tracking-[0.35em] text-[#C19A6B]">
              {t("waiting_activation.eyebrow", "Attivazione in corso")}
            </p>
            <h1
              className="text-3xl text-[#0B1E3F] tracking-tight"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {t("waiting_activation.title", "Completa registrazione e pagamento")}
            </h1>
            <p className="text-stone-600 text-sm leading-relaxed">
              {t(
                "waiting_activation.body_gestionale",
                "Per {{name}}: carica visura e documento, paga il pacchetto, poi il Super Admin verifica e ti invia la password per il gestionale."
              ).replace("{{name}}", agency?.display_name || "…")}
            </p>
            {agency?.preferred_plan_tier ? (
              <p className="text-sm text-stone-700">
                {t("waiting_activation.plan", "Piano")}:{" "}
                <span className="font-medium uppercase">{agency.preferred_plan_tier}</span>
              </p>
            ) : null}
          </div>

          <section className="bg-white border border-stone-200 rounded-lg px-4 py-4 space-y-3">
            <h2 className="text-[10px] uppercase tracking-widest text-stone-500">
              1 · {t("waiting_activation.kyc_title", "Identificazione (PDF o JPG)")}
            </h2>
            <p className="text-xs text-stone-500 normal-case tracking-normal">
              {t(
                "waiting_activation.kyc_formats",
                "Formati: PDF, PNG, JPG, WebP (max 8 MB). Niente HEIC da iPhone — usa «Compatibilità massima» o esporta JPG/PDF."
              )}
            </p>
            <div className="space-y-3">
              <DocPreview
                title="Visura camerale"
                doc={visuraDoc}
                local={localPreviews.visura_camerale}
                hasDoc={hasVisura}
                upBusy={upBusy}
                agencyReady={Boolean(agency)}
                inputTestId="waiting-upload-visura"
                onPick={(f) => uploadKyc("visura_camerale", f)}
                t={t}
              />
              <DocPreview
                title="Documento identità"
                doc={idDoc}
                local={localPreviews.documento_identita}
                hasDoc={hasId}
                upBusy={upBusy}
                agencyReady={Boolean(agency)}
                inputTestId="waiting-upload-id"
                onPick={(f) => uploadKyc("documento_identita", f)}
                t={t}
              />
            </div>
            {upBusy ? (
              <p className="text-xs text-stone-500" data-testid="waiting-upload-busy">
                {t("common.loading")}
              </p>
            ) : null}
            {!agency ? (
              <p className="text-xs text-amber-800">
                {t(
                  "waiting_activation.need_agency_session",
                  "Sessione agenzia non pronta. Clicca «Controlla di nuovo» oppure esci e rientra con la password scelta al signup."
                )}
              </p>
            ) : null}
          </section>

          <section className="bg-white border border-stone-200 rounded-lg px-4 py-4 space-y-3">
            <h2 className="text-[10px] uppercase tracking-widest text-stone-500">
              2 · {t("waiting_activation.pay_title", "Pagamento pacchetto")}
            </h2>
            <p className="text-sm text-stone-600">
              {paid
                ? t("waiting_activation.paid_ok", "Pagamento ricevuto.")
                : t("waiting_activation.paid_need", "Completa il checkout Stripe prima della verifica Ops.")}
            </p>
            {!paid ? (
              <button
                type="button"
                data-testid="waiting-pay"
                disabled={payBusy || !kycReady}
                onClick={startPay}
                className="w-full text-xs uppercase tracking-widest px-4 py-3 rounded bg-[#0B1E3F] text-white disabled:opacity-40"
              >
                {payBusy
                  ? t("common.loading")
                  : t("waiting_activation.pay_cta", "Paga e invia richiesta")}
              </button>
            ) : null}
            {!kycReady && !paid ? (
              <p className="text-xs text-amber-800">
                {t("waiting_activation.pay_need_kyc", "Carica prima visura e documento.")}
              </p>
            ) : null}
          </section>

          <section className="bg-white border border-stone-200 rounded-lg px-4 py-4 space-y-2 text-center">
            <h2 className="text-[10px] uppercase tracking-widest text-stone-500">
              3 · {t("waiting_activation.ops_title", "Verifica Super Admin")}
            </h2>
            <p className="text-sm text-stone-600">
              {readyForOps
                ? t(
                    "waiting_activation.ops_ready",
                    "Richiesta completa. Ti arriverà l’email con la password quando l’account sarà attivato."
                  )
                : t(
                    "waiting_activation.ops_wait",
                    "Completa documenti e pagamento per far partire la verifica."
                  )}
            </p>
          </section>

          {err ? (
            <p className="text-sm text-amber-900 bg-amber-50 border border-amber-200 rounded px-3 py-2">
              {err}
            </p>
          ) : null}
          {msg ? <p className="text-sm text-[#0B1E3F]">{msg}</p> : null}

          <div className="flex flex-wrap gap-3 justify-center pt-2">
            <Link
              to={`/${lang}/cloud`}
              className="text-xs uppercase tracking-widest px-4 py-2.5 rounded border border-stone-300 bg-white"
            >
              {t("waiting_activation.cta_cloud", "Vai a ImmobilCloud")}
            </Link>
            <button
              type="button"
              data-testid="waiting-refresh"
              disabled={checking}
              onClick={async () => {
                setChecking(true);
                try {
                  await loadStatus();
                } finally {
                  setChecking(false);
                }
              }}
              className="text-xs uppercase tracking-widest px-4 py-2.5 rounded border border-stone-300 bg-white text-stone-700 disabled:opacity-50"
            >
              {checking
                ? t("common.loading", "Caricamento…")
                : t("waiting_activation.refresh", "Controlla di nuovo")}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

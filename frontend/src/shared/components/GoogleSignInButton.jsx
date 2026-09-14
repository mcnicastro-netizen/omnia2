import React, { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../lib/api";

/**
 * Google Sign-In button (GIS). Hidden when GOOGLE_CLIENT_ID is not configured.
 */
export default function GoogleSignInButton({
  onSuccess,
  onError,
  label = "Continua con Google",
  disabled = false,
}) {
  const [enabled, setEnabled] = useState(false);
  const [clientId, setClientId] = useState(null);
  const [busy, setBusy] = useState(false);
  const btnRef = useRef(null);
  const handled = useRef(false);

  const finish = useCallback(
    async (credential) => {
      if (!credential || handled.current) return;
      handled.current = true;
      setBusy(true);
      try {
        await onSuccess?.(credential);
      } catch (err) {
        handled.current = false;
        const detail = err?.response?.data?.detail;
        onError?.(
          detail === "use_google_sign_in"
            ? "Usa Continua con Google per questo account."
            : detail === "google_token_invalid"
            ? "Accesso Google non riuscito. Riprova."
            : detail === "google_auth_not_configured"
            ? "Accesso Google non ancora configurato."
            : typeof detail === "string"
            ? detail
            : "Accesso Google non riuscito."
        );
      } finally {
        setBusy(false);
      }
    },
    [onSuccess, onError]
  );

  useEffect(() => {
    let cancelled = false;
    api
      .get("/auth/google/config")
      .then((r) => {
        if (cancelled) return;
        setEnabled(Boolean(r.data?.enabled && r.data?.client_id));
        setClientId(r.data?.client_id || null);
      })
      .catch(() => {
        if (!cancelled) setEnabled(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!enabled || !clientId || !btnRef.current) return;

    const render = () => {
      if (!window.google?.accounts?.id || !btnRef.current) return;
      btnRef.current.innerHTML = "";
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: (resp) => finish(resp?.credential),
        auto_select: false,
        cancel_on_tap_outside: true,
      });
      window.google.accounts.id.renderButton(btnRef.current, {
        theme: "outline",
        size: "large",
        text: "continue_with",
        shape: "rectangular",
        width: btnRef.current.offsetWidth || 320,
        locale: "it",
      });
    };

    if (window.google?.accounts?.id) {
      render();
      return undefined;
    }

    const existing = document.querySelector("script[data-omnia-gis]");
    if (existing) {
      existing.addEventListener("load", render);
      return () => existing.removeEventListener("load", render);
    }

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.dataset.omniaGis = "1";
    script.onload = render;
    document.head.appendChild(script);
    return undefined;
  }, [enabled, clientId, finish]);

  if (!enabled) return null;

  return (
    <div className="space-y-3" data-testid="google-sign-in">
      <div className="relative flex items-center gap-3 my-2">
        <div className="flex-1 h-px bg-stone-200" />
        <span className="text-[10px] font-sans uppercase tracking-widest text-stone-400">oppure</span>
        <div className="flex-1 h-px bg-stone-200" />
      </div>
      <div
        ref={btnRef}
        className={`w-full flex justify-center min-h-[44px] ${disabled || busy ? "opacity-50 pointer-events-none" : ""}`}
        aria-label={label}
      />
      {busy ? (
        <p className="text-center text-xs font-sans text-stone-500">Accesso con Google…</p>
      ) : null}
    </div>
  );
}

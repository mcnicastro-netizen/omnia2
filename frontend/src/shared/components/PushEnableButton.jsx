import React, { useEffect, useState } from "react";
import { api } from "../lib/api";

function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = window.atob(base64);
  const out = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
  return out;
}

/**
 * Enable browser Web Push for B2C alerts (nuovi annunci / ribassi).
 * Idealista/Immobiliare win on app push — we close the gap in-browser.
 */
export default function PushEnableButton() {
  const [status, setStatus] = useState("idle"); // idle|unsupported|ready|on|err
  const [msg, setMsg] = useState("");

  useEffect(() => {
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
      setStatus("unsupported");
      return;
    }
    setStatus("ready");
  }, []);

  const enable = async () => {
    setMsg("");
    try {
      const perm = await Notification.requestPermission();
      if (perm !== "granted") {
        setMsg("Permesso notifiche negato dal browser.");
        setStatus("err");
        return;
      }
      const { data } = await api.get("/cloud/me/push/vapid-public-key");
      const reg = await navigator.serviceWorker.register("/sw-push.js");
      await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(data.public_key),
      });
      await api.post("/cloud/me/push/subscribe", {
        subscription: sub.toJSON(),
        user_agent: navigator.userAgent,
      });
      setStatus("on");
      setMsg("Push attivo: ti avvisiamo su nuovi match e ribassi.");
    } catch (e) {
      setStatus("err");
      setMsg(e?.response?.data?.detail || e?.message || "Attivazione push non riuscita");
    }
  };

  if (status === "unsupported") {
    return (
      <p className="text-xs text-stone-500" data-testid="push-unsupported">
        Questo browser non supporta le notifiche push.
      </p>
    );
  }

  return (
    <div data-testid="push-enable" className="space-y-2">
      {status !== "on" ? (
        <button
          type="button"
          data-testid="push-enable-btn"
          onClick={enable}
          className="px-4 py-2 text-xs uppercase tracking-widest bg-[#0B1E3F] text-white rounded hover:bg-[#C19A6B]"
        >
          Attiva alert push sul browser
        </button>
      ) : (
        <p className="text-xs text-emerald-700 font-medium">Push attivo</p>
      )}
      {msg && <p className="text-xs text-stone-600">{msg}</p>}
    </div>
  );
}

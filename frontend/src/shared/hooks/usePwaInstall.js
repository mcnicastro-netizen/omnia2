import { useCallback, useEffect, useState } from "react";

/**
 * Chrome/Edge: beforeinstallprompt → prompt().
 * iOS Safari: no event → show manual “Aggiungi a Home”.
 * Already standalone: installed.
 */
export default function usePwaInstall() {
  const [deferred, setDeferred] = useState(null);
  const [installed, setInstalled] = useState(false);
  const [iosHint, setIosHint] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    const standalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      window.navigator.standalone === true;
    setInstalled(!!standalone);

    const ua = window.navigator.userAgent || "";
    const isIOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
    const isSafari = /Safari/.test(ua) && !/CriOS|FxiOS|EdgiOS|Chrome/.test(ua);
    setIosHint(isIOS && !standalone);

    const onBip = (e) => {
      e.preventDefault();
      setDeferred(e);
    };
    const onInstalled = () => {
      setInstalled(true);
      setDeferred(null);
    };
    window.addEventListener("beforeinstallprompt", onBip);
    window.addEventListener("appinstalled", onInstalled);
    return () => {
      window.removeEventListener("beforeinstallprompt", onBip);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  const canPrompt = !!deferred && !installed;

  const promptInstall = useCallback(async () => {
    if (!deferred) return { ok: false, reason: iosHint ? "ios" : "unavailable" };
    try {
      deferred.prompt();
      const choice = await deferred.userChoice;
      setDeferred(null);
      if (choice?.outcome === "accepted") {
        setInstalled(true);
        return { ok: true };
      }
      return { ok: false, reason: "dismissed" };
    } catch {
      return { ok: false, reason: "error" };
    }
  }, [deferred, iosHint]);

  return { installed, canPrompt, iosHint, promptInstall };
}

import { useCallback, useEffect, useState } from "react";
import {
  getDeferredInstallPrompt,
  promptPwaInstall,
  subscribeInstallPrompt,
} from "../lib/pwa";

/**
 * Chrome/Edge Android: beforeinstallprompt → dialog nativo «Installa».
 * iOS Safari: istruzioni Condividi → Aggiungi a Home (Apple non permette auto-install).
 */
export default function usePwaInstall() {
  const [canPrompt, setCanPrompt] = useState(!!getDeferredInstallPrompt());
  const [installed, setInstalled] = useState(false);
  const [iosHint, setIosHint] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    const standalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      window.navigator.standalone === true;
    setInstalled(!!standalone);

    const ua = window.navigator.userAgent || "";
    const ios =
      /iPad|iPhone|iPod/.test(ua) ||
      (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
    const mobile = ios || /Android|Mobile/i.test(ua);
    setIsMobile(mobile);
    setIosHint(ios && !standalone);

    const unsub = subscribeInstallPrompt((ev) => {
      setCanPrompt(!!ev && !standalone);
    });
    const onInstalled = () => {
      setInstalled(true);
      setCanPrompt(false);
    };
    window.addEventListener("omnia:pwa-installed", onInstalled);
    window.addEventListener("appinstalled", onInstalled);
    return () => {
      unsub();
      window.removeEventListener("omnia:pwa-installed", onInstalled);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  const promptInstall = useCallback(async () => {
    const res = await promptPwaInstall();
    if (res.ok && res.reason !== "already") setInstalled(true);
    if (res.ok || res.reason === "dismissed") setCanPrompt(false);
    return res;
  }, []);

  return { installed, canPrompt, iosHint, isMobile, promptInstall };
}

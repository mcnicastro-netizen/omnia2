/** ImmobilCloud PWA — SW + early capture of beforeinstallprompt (D-142/D-143). */

let deferredPrompt = null;
const listeners = new Set();

function emit() {
  listeners.forEach((fn) => {
    try {
      fn(deferredPrompt);
    } catch (_) {}
  });
}

function isStandalone() {
  if (typeof window === "undefined") return false;
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true
  );
}

export function getDeferredInstallPrompt() {
  return deferredPrompt;
}

export function subscribeInstallPrompt(fn) {
  listeners.add(fn);
  fn(deferredPrompt);
  return () => listeners.delete(fn);
}

export async function promptPwaInstall() {
  if (isStandalone()) return { ok: true, reason: "already" };
  if (!deferredPrompt) {
    const ua = typeof navigator !== "undefined" ? navigator.userAgent || "" : "";
    const ios =
      /iPad|iPhone|iPod/.test(ua) ||
      (typeof navigator !== "undefined" &&
        navigator.platform === "MacIntel" &&
        navigator.maxTouchPoints > 1);
    return { ok: false, reason: ios ? "ios" : "unavailable" };
  }
  try {
    deferredPrompt.prompt();
    const choice = await deferredPrompt.userChoice;
    deferredPrompt = null;
    emit();
    if (choice?.outcome === "accepted") return { ok: true, reason: "accepted" };
    return { ok: false, reason: "dismissed" };
  } catch {
    return { ok: false, reason: "error" };
  }
}

export function registerImmocloudPwa() {
  if (typeof window === "undefined") return;

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    emit();
    window.dispatchEvent(new CustomEvent("omnia:pwa-prompt-ready"));
  });

  window.addEventListener("appinstalled", () => {
    deferredPrompt = null;
    emit();
    window.dispatchEvent(new CustomEvent("omnia:pwa-installed"));
  });

  if (!("serviceWorker" in navigator)) return;
  const run = () => {
    navigator.serviceWorker.register("/sw-push.js").catch(() => undefined);
  };
  if (document.readyState === "complete") run();
  else window.addEventListener("load", run, { once: true });
}

export function pwaInstallUrl(lang = "it") {
  const origin = typeof window !== "undefined" ? window.location.origin : "https://cloud.omniarealestateecosystem.it";
  return `${origin}/${lang}/cloud/app`;
}

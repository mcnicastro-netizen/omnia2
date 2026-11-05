/** Register ImmobilCloud PWA service worker (same file as push). Safe no-op if unsupported. */
export function registerImmocloudPwa() {
  if (typeof window === "undefined" || !("serviceWorker" in navigator)) return;
  const run = () => {
    navigator.serviceWorker.register("/sw-push.js").catch(() => undefined);
  };
  if (document.readyState === "complete") run();
  else window.addEventListener("load", run, { once: true });
}

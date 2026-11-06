/**
 * Scroll a #section under the sticky TopNav (min-h ~132px).
 * Native scrollIntoView / scroll-mt alone leaves the title under the header.
 */
export function stickyHeaderOffsetPx() {
  if (typeof document === "undefined") return 140;
  const header = document.querySelector("header.sticky");
  const h = header?.getBoundingClientRect?.().height;
  // +4px di respiro sotto la nav sticky (misurata ~132–145px)
  return Math.ceil((h && h > 0 ? h : 132) + 4);
}

export function scrollToAnchor(idOrHash, { behavior = "smooth" } = {}) {
  if (typeof window === "undefined" || typeof document === "undefined") {
    return false;
  }
  const id = String(idOrHash || "").replace(/^#/, "");
  if (!id) return false;
  const el = document.getElementById(id);
  if (!el) return false;
  const top =
    el.getBoundingClientRect().top + window.scrollY - stickyHeaderOffsetPx();
  window.scrollTo({ top: Math.max(0, top), behavior });
  return true;
}

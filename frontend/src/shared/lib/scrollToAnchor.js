/**
 * Scroll #id so the section top sits flush under the sticky TopNav.
 * Uses instant scroll (auto): reliable with rapid nav clicks; no race.
 */
export function stickyHeaderOffsetPx() {
  if (typeof document === "undefined") return 72;
  const header = document.querySelector("header.sticky");
  const h = header?.offsetHeight || header?.getBoundingClientRect?.().height;
  return Math.round(h && h > 0 ? h : 72);
}

export function scrollToAnchor(idOrHash) {
  if (typeof window === "undefined" || typeof document === "undefined") {
    return false;
  }
  const id = String(idOrHash || "").replace(/^#/, "");
  if (!id) return false;
  const el = document.getElementById(id);
  if (!el) return false;

  const offset = stickyHeaderOffsetPx();
  const y = Math.round(
    el.getBoundingClientRect().top + window.scrollY - offset,
  );
  window.scrollTo({ top: Math.max(0, y), behavior: "auto" });

  // Second pass after layout (fonts/images) settles
  requestAnimationFrame(() => {
    const y2 = Math.round(
      el.getBoundingClientRect().top + window.scrollY - stickyHeaderOffsetPx(),
    );
    if (Math.abs(el.getBoundingClientRect().top - stickyHeaderOffsetPx()) > 1) {
      window.scrollTo({ top: Math.max(0, y2), behavior: "auto" });
    }
  });
  return true;
}

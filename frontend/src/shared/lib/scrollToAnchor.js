/**
 * Scroll to a #section accounting for sticky TopNav.
 * align: "start" = top sezione sotto la nav
 * align: "center" = centra il target (o un figlio [data-scroll-focus]) nel viewport utile
 */
export function stickyHeaderOffsetPx() {
  if (typeof document === "undefined") return 140;
  const header = document.querySelector("header.sticky");
  const h = header?.getBoundingClientRect?.().height;
  return Math.ceil((h && h > 0 ? h : 132) + 4);
}

export function scrollToAnchor(
  idOrHash,
  { behavior = "smooth", align = "start" } = {},
) {
  if (typeof window === "undefined" || typeof document === "undefined") {
    return false;
  }
  const id = String(idOrHash || "").replace(/^#/, "");
  if (!id) return false;
  const el = document.getElementById(id);
  if (!el) return false;

  const header = stickyHeaderOffsetPx();
  const focus =
    el.querySelector("[data-scroll-focus]") ||
    (align === "center" ? el : null) ||
    el;

  if (align === "center") {
    const rect = focus.getBoundingClientRect();
    const viewH = Math.max(120, window.innerHeight - header);
    const focusCenter = rect.top + window.scrollY + rect.height / 2;
    const top = focusCenter - header - viewH / 2;
    window.scrollTo({ top: Math.max(0, top), behavior });
    return true;
  }

  const top =
    el.getBoundingClientRect().top + window.scrollY - header;
  window.scrollTo({ top: Math.max(0, top), behavior });
  return true;
}

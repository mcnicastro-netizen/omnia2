export const THEME = {
  bg: "bg-[#fbf9f5]",
  card: "bg-white",
  text: "text-[#1c1917]",
  muted: "text-[#78716c]",
  primary: "bg-[#0B1E3F]",
  primaryText: "text-white",
  accent: "bg-[#C19A6B]",
  accentText: "text-white",
  cream: "bg-[#f7f4ef]",
  navy: "#0B1E3F",
  brass: "#C19A6B",
  champagne: "#E8D5B5",
};

/** Shared input look for Immocloud forms */
export const FIELD =
  "w-full px-3 py-2.5 bg-white border border-stone-200 rounded-lg text-sm outline-none focus:border-[#0B1E3F] transition";

export const BTN_PRIMARY =
  "inline-flex items-center justify-center px-5 py-2.5 bg-[#0B1E3F] text-white text-xs uppercase tracking-widest rounded-lg hover:bg-[#C19A6B] transition disabled:opacity-50";

export const BTN_ACCENT =
  "inline-flex items-center justify-center px-5 py-2.5 bg-[#C19A6B] text-white text-xs uppercase tracking-widest rounded-lg hover:bg-[#0B1E3F] transition disabled:opacity-50";

export function formatEUR(n) {
  if (n == null) return "—";
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}

export const THEME = {
  bg: "bg-[#fbf9f5]", card: "bg-white", text: "text-[#1c1917]", muted: "text-[#78716c]",
  primary: "bg-[#0B1E3F]", primaryText: "text-white", accent: "bg-[#C19A6B]", accentText: "text-white",
};

export function formatEUR(n) {
  if (n == null) return "—";
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}

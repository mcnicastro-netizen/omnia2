/* OMNIA — PropertyDetail helpers (MOVE-ONLY). */
export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api/cloud`;

export function formatPrice(p) {
  if (!p) return "";
  const v = p.operation === "rent" ? p.rent_monthly : p.price;
  if (!v) return "";
  return p.operation === "rent"
    ? `€ ${Number(v).toLocaleString("it-IT")}/mese`
    : `€ ${Number(v).toLocaleString("it-IT")}`;
}

// Stima rapida rata: mutuo 25 anni, LTV 80%, TAN indicativo 3.6% (allineato al comparatore)
export function estimateInstallment(price) {
  const loan = price * 0.8;
  const i = 0.036 / 12;
  const n = 300;
  return (loan * i) / (1 - Math.pow(1 + i, -n));
}

export function waHref(raw) {
  const digits = String(raw || "").replace(/[^\d]/g, "");
  return digits ? `https://wa.me/${digits}` : null;
}


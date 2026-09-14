import React from "react";
import { useTranslation } from "react-i18next";
import { formatEUR } from "../cloudTheme";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function PropertyCard({ p }) {
  const { t } = useTranslation();
  const cover = p.cover_url ? `${BACKEND_URL}${p.cover_url}` : null;
  const price = p.operation === "rent"
    ? `${formatEUR(p.rent_monthly)}/mese`
    : formatEUR(p.price);
  return (
    <article data-testid={`cloud-card-${p.id}`}
      className="bg-white rounded-xl overflow-hidden border border-stone-200 hover:shadow-lg hover:-translate-y-0.5 transition-all">
      <div className="aspect-[4/3] bg-stone-100 relative">
        {cover ? (
          <img src={cover} alt={p.title} className="w-full h-full object-cover" loading="lazy" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-stone-300 text-5xl">⌂</div>
        )}
        {p.energy_class && (
          <span className="absolute top-3 right-3 text-[10px] uppercase tracking-widest bg-white/90 backdrop-blur px-2 py-1 rounded">
            {t("cloud.energy")}: {p.energy_class}
          </span>
        )}
        {p.operation === "rent" && (
          <span className="absolute top-3 left-3 text-[10px] uppercase tracking-widest bg-[#C19A6B] text-white px-2 py-1 rounded">
            {t("cloud.op_rent")}
          </span>
        )}
      </div>
      <div className="p-4">
        <p className="text-xl font-semibold text-[#0B1E3F]" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
          {price}
        </p>
        <h3 className="text-sm font-medium text-stone-900 mt-1 line-clamp-2">{p.title}</h3>
        <p className="text-xs text-stone-500 mt-1">
          {p.city}{p.zone && ` · ${p.zone}`}
        </p>
        <div className="flex items-center gap-3 mt-3 text-xs text-stone-600">
          {p.surface_sqm && <span>{p.surface_sqm} m²</span>}
          {p.rooms && <span>· {p.rooms} {t("cloud.rooms_short")}</span>}
          {p.bathrooms && <span>· {p.bathrooms} {t("cloud.baths_short")}</span>}
        </div>
        {p.agency && (
          <p className="text-[10px] uppercase tracking-widest text-stone-400 mt-3 pt-2 border-t border-stone-100">
            {t("cloud.by_agency")}: <span className="text-stone-700">{p.agency.name}</span>
          </p>
        )}
      </div>
    </article>
  );
}

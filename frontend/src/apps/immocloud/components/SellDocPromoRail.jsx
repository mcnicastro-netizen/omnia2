import React from "react";
import { useTranslation } from "react-i18next";

/**
 * Vertical promo rail for B2C sell / publish flow.
 * Visual only for now — routes wired later.
 */
export default function SellDocPromoRail({ className = "" }) {
  const { t } = useTranslation();

  const boxes = [
    {
      key: "ape",
      tag: t("cloud.sell.promo_ape_tag"),
      title: t("cloud.sell.promo_ape_title"),
      desc: t("cloud.sell.promo_ape_desc"),
      accent: "#1F6B5C",
      wash: "linear-gradient(145deg, rgba(31,107,92,0.14) 0%, rgba(245,241,232,0.92) 55%, #F5F1E8 100%)",
    },
    {
      key: "planimetria",
      tag: t("cloud.sell.promo_plan_tag"),
      title: t("cloud.sell.promo_plan_title"),
      desc: t("cloud.sell.promo_plan_desc"),
      accent: "#C8A653",
      wash: "linear-gradient(145deg, rgba(200,166,83,0.18) 0%, rgba(245,241,232,0.94) 55%, #F5F1E8 100%)",
    },
    {
      key: "atti",
      tag: t("cloud.sell.promo_atti_tag"),
      title: t("cloud.sell.promo_atti_title"),
      desc: t("cloud.sell.promo_atti_desc"),
      accent: "#0B1E3F",
      wash: "linear-gradient(145deg, rgba(11,30,63,0.12) 0%, rgba(245,241,232,0.94) 55%, #F5F1E8 100%)",
    },
  ];

  return (
    <aside
      data-testid="sell-promo-rail"
      className={`flex flex-col gap-3 ${className}`}
      aria-label={t("cloud.sell.promo_rail_label")}
    >
      <p className="text-[10px] font-sans uppercase tracking-[0.28em] text-[#0B1E3F]/55 px-0.5">
        {t("cloud.sell.promo_rail_label")}
      </p>
      {boxes.map((box) => (
        <div
          key={box.key}
          data-testid={`sell-promo-${box.key}`}
          className="group relative overflow-hidden rounded-2xl border px-4 py-4 sm:px-5 sm:py-5 transition duration-300 hover:-translate-y-0.5 hover:shadow-[0_16px_36px_rgba(11,30,63,0.12)]"
          style={{
            borderColor: `${box.accent}40`,
            background: box.wash,
          }}
        >
          <div
            className="pointer-events-none absolute inset-y-3 left-0 w-[3px] rounded-r-full opacity-90 transition group-hover:opacity-100"
            style={{ background: box.accent }}
            aria-hidden
          />
          <p
            className="pl-2 text-[10px] font-sans uppercase tracking-[0.28em] mb-1.5"
            style={{ color: box.accent }}
          >
            {box.tag}
          </p>
          <h2
            className="pl-2 text-lg tracking-tight text-[#0B1E3F] mb-1.5 leading-snug"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            {box.title}
          </h2>
          <p className="pl-2 text-[13px] sm:text-sm font-sans leading-relaxed text-[#0B1E3F]/68">
            {box.desc}
          </p>
          <p
            className="pl-2 mt-3 text-[10px] font-sans uppercase tracking-[0.22em] opacity-70 group-hover:opacity-100 transition"
            style={{ color: box.accent }}
          >
            {t("cloud.sell.promo_soon")}
          </p>
        </div>
      ))}
    </aside>
  );
}

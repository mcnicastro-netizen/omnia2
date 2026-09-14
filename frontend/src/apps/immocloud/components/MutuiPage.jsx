/* OMNIA — M5.S5 Mutui page (portale B2C ImmobilCloud) */
import React from "react";
import { useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import MortgageComparator from "../../../shared/components/MortgageComparator";

export default function MutuiPage() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const initialPrice = params.get("price") ? Number(params.get("price")) : null;

  return (
    <div data-testid="mutui-page" className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
      <header className="mb-8">
        <p className="text-[10px] font-sans uppercase tracking-[0.3em] text-[#C19A6B] mb-2">
          ImmobilCloud · {t("mutui.badge")}
        </p>
        <h1 className="text-4xl sm:text-5xl font-light tracking-tight mb-3" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
          {t("mutui.title")}
        </h1>
        <p className="text-base text-stone-600 max-w-2xl">{t("mutui.subtitle")}</p>
      </header>
      <MortgageComparator publicMode initialPrice={initialPrice} />
    </div>
  );
}

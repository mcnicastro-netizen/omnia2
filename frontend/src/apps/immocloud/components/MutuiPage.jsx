/* OMNIA — M5.S5 Mutui page (portale B2C ImmobilCloud) */
import React from "react";
import { useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import MortgageComparator from "../../../shared/components/MortgageComparator";
import CloudPageHero from "./CloudPageHero";

export default function MutuiPage() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const initialPrice = params.get("price") ? Number(params.get("price")) : null;

  return (
    <div data-testid="mutui-page">
      <CloudPageHero
        eyebrow="ImmobilCloud · Mutuo"
        title={t("mutui.title")}
        subtitle={t("mutui.subtitle")}
        image="/cloud/intent-mortgage.jpg"
      />
      <div className="max-w-5xl mx-auto px-5 sm:px-8 md:px-16 py-10">
        <MortgageComparator publicMode initialPrice={initialPrice} />
      </div>
    </div>
  );
}

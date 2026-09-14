/* OMNIA — M5.S5 Mutui tool (CRM agenti) */
import React from "react";
import { useTranslation } from "react-i18next";
import AgencyShell from "../components/AgencyShell";
import MortgageComparator from "../../../shared/components/MortgageComparator";

export default function MutuiToolPage() {
  const { t } = useTranslation();
  return (
    <AgencyShell current="mutui">
      <section data-testid="mutui-tool-page" className="max-w-5xl space-y-6">
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-amber-700 mb-1">OMNIA · {t("mutui.badge")}</p>
          <h1 className="text-3xl md:text-4xl tracking-tight" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            {t("mutui.title")}
          </h1>
          <p className="text-sm text-stone-500 mt-2 max-w-2xl">{t("mutui.agent_subtitle")}</p>
        </div>
        <MortgageComparator />
      </section>
    </AgencyShell>
  );
}

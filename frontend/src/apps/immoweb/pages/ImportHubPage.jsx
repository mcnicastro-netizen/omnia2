import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import AgencyShell from "../components/AgencyShell";
import Brand from "../../../shared/components/Brand";

/**
 * Hub unico Importa — tre porte (A XML gestionale · B/C immobili · D/E clienti).
 * Nessun nome competitor (D-051).
 */
export default function ImportHubPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);

  const cards = [
    {
      id: "a",
      to: `/${lang}/app/import/xml`,
      label: t("import.form_a_label"),
      hint: t("import.form_a_hint"),
      body: t("import.hub_a_body"),
      cta: t("import.hub_open_a"),
      testid: "import-hub-a",
    },
    {
      id: "bc",
      to: `/${lang}/app/properties/import`,
      label: t("import.form_bc_label"),
      hint: t("import.form_bc_hint"),
      body: t("import.hub_bc_body"),
      cta: t("import.hub_open_bc"),
      testid: "import-hub-bc",
    },
    {
      id: "de",
      to: `/${lang}/app/clients/import`,
      label: t("import.form_de_label"),
      hint: t("import.form_de_hint"),
      body: t("import.hub_de_body"),
      cta: t("import.hub_open_de"),
      testid: "import-hub-de",
    },
  ];

  return (
    <AgencyShell current="import">
      <section data-testid="import-hub-page" className="space-y-8 max-w-4xl">
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-2">
            <Brand>ImmoWeb · Migrazione</Brand>
          </p>
          <h1
            className="text-3xl md:text-4xl tracking-tight"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            {t("import.hub_title")}
          </h1>
          <p className="text-sm text-stone-600 mt-2 max-w-2xl">
            {t("import.hub_subtitle")}
          </p>
        </div>

        <ul className="grid gap-4 sm:grid-cols-1 md:grid-cols-3">
          {cards.map((card) => (
            <li key={card.id}>
              <Link
                to={card.to}
                data-testid={card.testid}
                className="flex h-full flex-col rounded-lg border border-stone-200 bg-white p-5 hover:border-stone-400 hover:shadow-sm transition"
              >
                <span className="text-[10px] uppercase tracking-widest text-stone-500">
                  {card.hint}
                </span>
                <span
                  className="mt-2 text-xl text-stone-900 tracking-tight"
                  style={{ fontFamily: "'Fraunces', Georgia, serif" }}
                >
                  {card.label}
                </span>
                <p className="mt-3 flex-1 text-sm text-stone-600 leading-relaxed">
                  {card.body}
                </p>
                <span className="mt-4 text-[11px] uppercase tracking-widest text-stone-800 border-b border-stone-400 self-start">
                  {card.cta} →
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </AgencyShell>
  );
}

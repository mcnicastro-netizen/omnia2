import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

/**
 * Cross-link fra le tre porte di import. Zero nomi competitor (D-051).
 * current: "a" | "bc" | "de"
 */
export default function ImportFormsCrossLinks({ current }) {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);

  const items = [
    {
      id: "a",
      to: `/${lang}/app/import`,
      label: t("import.form_a_label"),
      hint: t("import.form_a_hint"),
      testid: "import-cross-a",
    },
    {
      id: "bc",
      to: `/${lang}/app/properties/import`,
      label: t("import.form_bc_label"),
      hint: t("import.form_bc_hint"),
      testid: "import-cross-bc",
    },
    {
      id: "de",
      to: `/${lang}/app/clients/import`,
      label: t("import.form_de_label"),
      hint: t("import.form_de_hint"),
      testid: "import-cross-de",
    },
  ];

  return (
    <nav
      data-testid="import-forms-cross-links"
      aria-label={t("import.forms_cross_title")}
      className="mt-4 rounded-lg border border-stone-200 bg-stone-50 px-4 py-3"
    >
      <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-2">
        {t("import.forms_cross_title")}
      </p>
      <ul className="grid gap-2 sm:grid-cols-3">
        {items.map((item) => {
          const active = item.id === current;
          const body = (
            <>
              <span className="block text-sm font-medium text-stone-900">{item.label}</span>
              <span className="block text-xs text-stone-500 mt-0.5">{item.hint}</span>
            </>
          );
          return (
            <li key={item.id}>
              {active ? (
                <div
                  data-testid={item.testid}
                  data-active="true"
                  className="block rounded-md border border-stone-300 bg-white px-3 py-2"
                >
                  {body}
                </div>
              ) : (
                <Link
                  to={item.to}
                  data-testid={item.testid}
                  className="block rounded-md border border-transparent px-3 py-2 hover:border-stone-300 hover:bg-white"
                >
                  {body}
                </Link>
              )}
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

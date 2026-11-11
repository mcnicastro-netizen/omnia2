import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { useTranslation } from "react-i18next";

/**
 * ProtectedRoute: gates children behind authentication.
 * Optional: allowedRoles — restrict to specific roles.
 * H7 — mirrors backend role aliases (D-041): franchising roles inherit permissions.
 */
const ROLE_ALIASES = {
  agency_admin: ["agency_admin", "branch_admin", "group_admin"],
  agent: ["agent", "branch_agent", "branch_admin", "group_admin"],
};

export default function ProtectedRoute({ children, allowedRoles }) {
  const { user } = useAuth();
  const location = useLocation();
  const { i18n, t } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const expandedRoles = allowedRoles
    ? [...new Set(allowedRoles.flatMap((r) => ROLE_ALIASES[r] || [r]))]
    : null;

  if (user === null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-stone-50 text-stone-600 font-sans text-sm uppercase tracking-widest">
        {t("common.loading")}
      </div>
    );
  }
  if (user === false) {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/${lang}/login?next=${next}`} replace />;
  }
  if (expandedRoles && !expandedRoles.includes(user.role)) {
    // CRM: sessione cloud/client o Super Admin senza ruolo → login gestionale (no 403 morto)
    const onCrm = (location.pathname || "").includes("/app/");
    const crmRoles = ["agency_admin", "agent", "branch_admin", "branch_agent", "group_admin", "super_admin"];
    if (onCrm && !crmRoles.includes(user.role)) {
      const next = encodeURIComponent(location.pathname + location.search);
      return (
        <Navigate
          to={`/${lang}/login?from=app&next=${next}&reason=role`}
          replace
        />
      );
    }
    return (
      <div
        className="min-h-screen flex flex-col items-center justify-center bg-stone-50 text-stone-900 p-8"
        style={{ fontFamily: "'Fraunces', Georgia, serif" }}
      >
        <h1 className="text-5xl mb-4">403</h1>
        <p className="text-stone-600 font-sans">{t("auth.forbidden")}</p>
        <a
          href={`/${lang}/login?from=app&next=${encodeURIComponent(`/${lang}/app/dashboard`)}`}
          className="mt-6 text-xs font-sans uppercase tracking-widest text-[#0B1E3F] underline"
        >
          {t("auth.login_gestionale", "Accedi al gestionale")}
        </a>
      </div>
    );
  }
  return children;
}

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
    return (
      <div
        className="min-h-screen flex flex-col items-center justify-center bg-stone-50 text-stone-900 p-8"
        style={{ fontFamily: "'Fraunces', Georgia, serif" }}
      >
        <h1 className="text-5xl mb-4">403</h1>
        <p className="text-stone-600 font-sans">{t("auth.forbidden")}</p>
      </div>
    );
  }
  return children;
}

import React, { Suspense, lazy } from "react";
import "@/App.css";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useParams,
  useLocation,
} from "react-router-dom";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";

import "@/shared/i18n/config";
import { SUPPORTED_LANGS, DEFAULT_LANG } from "@/shared/i18n/config";
import { AuthProvider } from "@/shared/lib/auth";
import ErrorBoundary from "@/shared/components/ErrorBoundary";
import ProtectedRoute from "@/shared/components/ProtectedRoute";
import { Toaster } from "@/components/ui/sonner";

// M16 — code splitting: ogni app/pagina è un chunk separato caricato on-demand
const LandingApp = lazy(() => import("@/apps/landing/LandingApp"));
const AgenziesLandingPage = lazy(() => import("@/apps/landing/AgenziesLandingPage"));
const DomainVerifyPage = lazy(() => import("@/apps/landing/DomainVerifyPage"));
const DomainSovereigntyPolicyPage = lazy(() => import("@/apps/landing/DomainSovereigntyPolicyPage"));
const WidgetsShowcasePage = lazy(() => import("@/pages/WidgetsShowcasePage"));
const ImmocloudApp = lazy(() => import("@/apps/immocloud/ImmocloudApp"));
const ImmowebApp = lazy(() => import("@/apps/immoweb/ImmowebApp"));
const DashboardPage = lazy(() => import("@/apps/immoweb/DashboardPage"));
const OnboardingWizard = lazy(() => import("@/apps/immoweb/OnboardingWizard"));
const MembersPage = lazy(() => import("@/apps/immoweb/MembersPage"));
const SettingsPage = lazy(() => import("@/apps/immoweb/SettingsPage"));
const PropertiesPage = lazy(() => import("@/apps/immoweb/PropertiesPage"));
const PropertyFormPage = lazy(() => import("@/apps/immoweb/PropertyFormPage"));
const PropertyImportPage = lazy(() => import("@/apps/immoweb/PropertyImportPage"));
const ClientsPage = lazy(() => import("@/apps/immoweb/ClientsPage"));
const ClientFormPage = lazy(() => import("@/apps/immoweb/ClientFormPage"));
const ClientImportPage = lazy(() => import("@/apps/immoweb/ClientImportPage"));
const MatchesPage = lazy(() => import("@/apps/immoweb/MatchesPage"));
const MatchLeadScorePage = lazy(() => import("@/apps/immoweb/MatchLeadScorePage"));
const WebsitePage = lazy(() => import("@/apps/immoweb/WebsitePage"));
const ModerationPage = lazy(() => import("@/apps/immoweb/ModerationPage"));
const VirtualStagingPage = lazy(() => import("@/apps/immoweb/pages/VirtualStagingPage"));
const FascicoloPage = lazy(() => import("@/apps/immoweb/pages/FascicoloPage"));
const MutuiToolPage = lazy(() => import("@/apps/immoweb/pages/MutuiToolPage"));
const GroupPage = lazy(() => import("@/apps/immoweb/pages/GroupPage"));
const ApiKeysPage = lazy(() => import("@/apps/immoweb/pages/ApiKeysPage"));
const BillingPage = lazy(() => import("@/apps/immoweb/pages/BillingPage"));
const ImportXmlPage = lazy(() => import("@/apps/immoweb/pages/ImportXmlPage"));
const PublishingPage = lazy(() => import("@/apps/immoweb/pages/PublishingPage"));
const PortalWizardPage = lazy(() => import("@/apps/immoweb/pages/PortalWizardPage"));
const SocialPublisherPage = lazy(() => import("@/apps/immoweb/pages/SocialPublisherPage"));
const HalKnowledgePage = lazy(() => import("@/apps/immoweb/pages/HalKnowledgePage"));
const BrandLabPage = lazy(() => import("@/apps/immoweb/pages/BrandLabPage"));
const AcademyApp = lazy(() => import("@/apps/academy/AcademyApp"));
const LegalApp = lazy(() => import("@/apps/legal/LegalApp"));
const LoginPage = lazy(() => import("@/apps/auth/LoginPage"));
const RegisterPage = lazy(() => import("@/apps/auth/RegisterPage"));
const ForgotPasswordPage = lazy(() => import("@/apps/auth/ForgotPasswordPage"));
const ResetPasswordPage = lazy(() => import("@/apps/auth/ResetPasswordPage"));
const AcceptInvitePage = lazy(() => import("@/apps/auth/AcceptInvitePage"));

function RouteFallback() {
  return (
    <div
      data-testid="route-loading"
      className="min-h-screen flex items-center justify-center bg-stone-50 text-stone-500 font-sans text-sm uppercase tracking-widest"
    >
      …
    </div>
  );
}


function LangSync({ children }) {
  const { lang } = useParams();
  const location = useLocation();
  const { i18n } = useTranslation();
  useEffect(() => {
    if (lang && SUPPORTED_LANGS.includes(lang)) {
      if (i18n.language?.slice(0, 2) !== lang) i18n.changeLanguage(lang);
      document.documentElement.lang = lang;
    }
  }, [lang, i18n]);
  // M10 — unknown lang prefix (e.g. /fr/...) → redirect to default lang
  if (lang && !SUPPORTED_LANGS.includes(lang)) {
    const rest = location.pathname.replace(/^\/[^/]+/, "");
    const target = /^[a-z]{2}(-[A-Za-z]{2})?$/.test(lang)
      ? `/${DEFAULT_LANG}${rest}`
      : `/${DEFAULT_LANG}${location.pathname}`;
    return <Navigate to={target + location.search} replace />;
  }
  return children;
}

function RootRedirect() {
  const { i18n } = useTranslation();
  const detected = (i18n.language || DEFAULT_LANG).slice(0, 2);
  const lang = SUPPORTED_LANGS.includes(detected) ? detected : DEFAULT_LANG;
  return <Navigate to={`/${lang}`} replace />;
}

function NotFound() {
  const location = useLocation();
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  return (
    <div
      data-testid="not-found"
      className="min-h-screen flex flex-col items-center justify-center bg-stone-50 text-stone-900 p-8"
      style={{ fontFamily: "'Fraunces', Georgia, serif" }}
    >
      <h1 className="text-7xl tracking-tight mb-4">404</h1>
      <p className="text-stone-600 mb-8 font-sans">
        {t("common.error")} — <code>{location.pathname}</code>
      </p>
      <a
        href={`/${lang}`}
        className="text-sm font-sans uppercase tracking-widest bg-stone-900 text-stone-50 px-6 py-3 hover:bg-stone-700"
      >
        ← {t("nav.landing")}
      </a>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <ErrorBoundary>
        <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route path="/" element={<RootRedirect />} />
          <Route
            path="/:lang/*"
            element={
              <LangSync>
                <Routes>
                  <Route index element={<LandingApp />} />

                  {/* Founders 50 — landing for B2B agencies */}
                  <Route path="agenzie" element={<AgenziesLandingPage />} />

                  {/* M2.5.4b — Domain Ownership Checker (Domain Sovereignty Kit) */}
                  <Route path="verifica-dominio" element={<DomainVerifyPage />} />

                  {/* M2.5.5 — Domain Sovereignty Policy (public) */}
                  <Route path="domain-sovereignty-policy" element={<DomainSovereigntyPolicyPage />} />

                  {/* M2.5.3 — Track B widgets showcase (public) */}
                  <Route path="widgets" element={<WidgetsShowcasePage />} />

                  {/* Auth pages (public) */}
                  <Route path="login" element={<LoginPage />} />
                  <Route path="register" element={<RegisterPage />} />
                  <Route path="forgot-password" element={<ForgotPasswordPage />} />
                  <Route path="reset-password" element={<ResetPasswordPage />} />
                  <Route path="accept-invite" element={<AcceptInvitePage />} />

                  {/* B2C portal */}
                  <Route path="cloud/*" element={<ImmocloudApp />} />

                  {/* B2B agency app */}
                  <Route path="app" element={<ImmowebApp />} />
                  <Route
                    path="app/onboarding"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "client"]}>
                        <OnboardingWizard />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="app/dashboard"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "agent"]}>
                        <DashboardPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="app/group"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "group_admin"]}>
                        <GroupPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="app/api-keys"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "group_admin", "branch_admin"]}>
                        <ApiKeysPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="app/import"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "group_admin", "branch_admin"]}>
                        <ImportXmlPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="app/publishing"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "group_admin", "branch_admin"]}>
                        <PublishingPage />
                      </ProtectedRoute>
                    }
                  />
                  {/* M2.6d — Universal Portal Wizard (self-service custom portali) */}
                  <Route
                    path="app/publishing/wizard"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "group_admin", "branch_admin"]}>
                        <PortalWizardPage />
                      </ProtectedRoute>
                    }
                  />
                  {/* M2.6c — Social Publisher (FB Page, IG Business, Telegram) */}
                  <Route
                    path="app/publishing/social"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "group_admin", "branch_admin"]}>
                        <SocialPublisherPage />
                      </ProtectedRoute>
                    }
                  />
                  {/* M5.S2 — HAL Knowledge (RAG su documentazione OMNIA) */}
                  <Route
                    path="app/hal-knowledge"
                    element={
                      <ProtectedRoute>
                        <HalKnowledgePage />
                      </ProtectedRoute>
                    }
                  />
                  {/* Brand Lab — internal creative repository (super_admin only) */}
                  <Route
                    path="app/brand-lab"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin"]}>
                        <BrandLabPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="app/members"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "agent"]}>
                        <MembersPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="app/settings"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin"]}>
                        <SettingsPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="app/settings/billing"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "group_admin"]}>
                        <BillingPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="app/properties"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "agent"]}>
                        <PropertiesPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="app/properties/import"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "agent"]}>
                        <PropertyImportPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="app/properties/new"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "agent"]}>
                        <PropertyFormPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="app/mutui"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "agent"]}>
                        <MutuiToolPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="app/properties/:id/fascicolo"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "agent"]}>
                        <FascicoloPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="app/properties/:id"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "agent"]}>
                        <PropertyFormPage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Clients (CRM) */}
                  <Route
                    path="app/clients"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "agent"]}>
                        <ClientsPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="app/clients/new"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "agent"]}>
                        <ClientFormPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="app/clients/import"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "agent"]}>
                        <ClientImportPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="app/clients/:id"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "agent"]}>
                        <ClientFormPage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Matches (M2.S4) */}
                  <Route
                    path="app/matches"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "agent"]}>
                        <MatchesPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="app/matches/lead"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "agent"]}>
                        <MatchLeadScorePage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Website / Brand Studio (M2.S5 Layer D) */}
                  <Route
                    path="app/website"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin"]}>
                        <WebsitePage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Virtual Staging (M5.S4.1) — arreda foto vuote con AI */}
                  <Route
                    path="app/staging"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin", "agency_admin", "agent"]}>
                        <VirtualStagingPage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Moderation (M3.S5 v2) — admin reviews B2C private listings */}
                  <Route
                    path="app/moderation"
                    element={
                      <ProtectedRoute allowedRoles={["super_admin"]}>
                        <ModerationPage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Academy */}
                  <Route path="learn/*" element={<AcademyApp />} />

                  {/* AL Legal (M5.S3) — accessible to all authenticated users (agents + B2C) */}
                  <Route
                    path="legal"
                    element={
                      <ProtectedRoute>
                        <LegalApp />
                      </ProtectedRoute>
                    }
                  />

                  <Route path="*" element={<NotFound />} />
                </Routes>
              </LangSync>
            }
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
        </Suspense>
        </ErrorBoundary>
        <Toaster position="top-right" richColors />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;

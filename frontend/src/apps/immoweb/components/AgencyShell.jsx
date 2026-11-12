import React, { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../../shared/lib/auth";
import { api } from "../../../shared/lib/api";
import Brand from "../../../shared/components/Brand";
import OmniaLogo from "../../../shared/components/OmniaLogo";
import LanguageSwitcher from "../../../shared/components/LanguageSwitcher";
import AlChatWidget from "./AlChatWidget";
import NotificationBell from "../../../shared/components/NotificationBell";
import BackButton, { isCrmDashboardPath } from "./BackButton";
import ForceChangePasswordModal from "./ForceChangePasswordModal";

/**
 * AgencyShell — shared sidebar+topbar layout for all authenticated ImmoWeb pages.
 * Loads /agencies/me once. If no agency → redirect to onboarding.
 */
export default function AgencyShell({ children, current = "dashboard", showBack }) {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const location = useLocation();
  const [agency, setAgency] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [myAgencies, setMyAgencies] = useState([]);

  const backVisible =
    typeof showBack === "boolean"
      ? showBack
      : !isCrmDashboardPath(location.pathname);

  // M5 — multi-agency switcher: carica l'elenco solo se l'utente ha più agenzie
  useEffect(() => {
    if ((user?.agency_ids || []).length < 2) return;
    api.get("/auth/my-agencies").then((r) => setMyAgencies(r.data.items || [])).catch(() => {});
  }, [user?.agency_ids]);

  const switchAgency = async (agencyId) => {
    try {
      await api.post("/auth/active-agency", { agency_id: agencyId });
      window.location.reload();
    } catch {
      // noop
    }
  };

  // D-162 — Super Admin fuori CRM salvo impersonazione cabina
  // Eccezioni interne (non CRM cliente): brand-lab
  const path = location.pathname || "";
  const superAdminInternal =
    path.includes("/app/brand-lab") || path.includes("/app/ops");
  useEffect(() => {
    if (
      user?.role === "super_admin" &&
      !user?.ops_impersonation &&
      !superAdminInternal
    ) {
      nav(`/${lang}/app/ops`, { replace: true });
    }
  }, [user?.role, user?.ops_impersonation, lang, nav, superAdminInternal]);

  useEffect(() => {
    // Super Admin in pagina interna (brand-lab): niente CRM / waiting
    if (user?.role === "super_admin" && !user?.ops_impersonation) {
      if (superAdminInternal) {
        setAgency(false);
      }
      return;
    }
    let mounted = true;
    api
      .get("/app/agencies/me")
      .then((r) => {
        if (!mounted) return;
        const a = r.data;
        setAgency(a);
        // Pending CRM: sala d'attesa (titolare / agent)
        const st = a?.activation_status || "active";
        const path = location.pathname || "";
        const onWaiting = path.includes("/app/waiting-activation");
        if (st === "pending" && !onWaiting) {
          nav(`/${lang}/app/waiting-activation`, { replace: true });
          return;
        }
        // D-168 — post-Attiva: Avvio prima della dashboard operativa (admin)
        const journey = a?.setup_journey || {};
        const avvioOpen =
          st === "active" &&
          journey?.status !== "completed" &&
          (user?.role === "agency_admin" ||
            user?.role === "branch_admin" ||
            user?.role === "group_admin" ||
            Boolean(user?.ops_impersonation));
        const onAvvio = path.includes("/app/avvio");
        const onDash = /\/app\/dashboard\/?$/.test(path);
        if (avvioOpen && onDash && !onAvvio) {
          nav(`/${lang}/app/avvio`, { replace: true });
        }
      })
      .catch((err) => {
        if (!mounted) return;
        if (err?.response?.status === 404) {
          // No agency yet — redirect agency_admin to onboarding.
          if (user?.role === "agency_admin") {
            nav(`/${lang}/app/onboarding`, { replace: true });
          } else {
            setAgency(false); // no agency for agent users (shouldn't happen normally)
          }
        } else {
          setAgency(false);
        }
      });
    return () => {
      mounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang, user?.role, user?.ops_impersonation, location.pathname, superAdminInternal]);

  const onLogout = async () => {
    await logout();
    nav(`/${lang}/login`, { replace: true });
  };

  const impersonating = Boolean(user?.ops_impersonation);
  const isGroupAdmin = user?.role === "group_admin" || (user?.role === "super_admin" && impersonating);
  const isAgencyAdmin =
    user?.role === "agency_admin" ||
    user?.role === "branch_admin" ||
    isGroupAdmin ||
    (user?.role === "super_admin" && impersonating);
  const journeyIncomplete =
    agency &&
    agency !== false &&
    (agency.activation_status || "active") === "active" &&
    (agency.setup_journey || {}).status !== "completed";

  const navItems = [
    ...(isAgencyAdmin && journeyIncomplete
      ? [{ key: "avvio", to: `/${lang}/app/avvio`, label: "Avvio", icon: "①", cluster: "avvio" }]
      : []),
    { key: "dashboard", to: `/${lang}/app/dashboard`, label: t("immoweb_app.nav_dashboard"), icon: "▦", cluster: "operativo" },
    ...(isGroupAdmin
      ? [{ key: "group", to: `/${lang}/app/group`, label: t("immoweb_app.nav_group") || "Gruppo", icon: "🏢", cluster: "amministrazione" }]
      : []),
    ...(isAgencyAdmin
      ? [{ key: "import", to: `/${lang}/app/import`, label: t("immoweb_app.nav_import") || "Importa", icon: "⇪", cluster: "pubblicazione" }]
      : []),
    ...(isAgencyAdmin
      ? [{ key: "publishing", to: `/${lang}/app/publishing`, label: t("immoweb_app.nav_publishing") || "Pubblicità su portali", icon: "📡", cluster: "pubblicazione" }]
      : []),
    { key: "properties", to: `/${lang}/app/properties`, label: t("immoweb_app.nav_properties"), icon: "🏠", cluster: "operativo" },
    { key: "clients", to: `/${lang}/app/clients`, label: t("immoweb_app.nav_clients"), icon: "👥", cluster: "operativo" },
    { key: "requests", to: `/${lang}/app/requests`, label: t("immoweb_app.nav_requests") || "Richieste", icon: "⎘", cluster: "operativo" },
    { key: "activities", to: `/${lang}/app/activities`, label: t("immoweb_app.nav_activities") || "Attività", icon: "☑", cluster: "operativo" },
    ...(isAgencyAdmin
      ? [{ key: "trash", to: `/${lang}/app/trash`, label: t("immoweb_app.nav_trash") || "Cestino", icon: "🗑", cluster: "amministrazione" }]
      : []),
    { key: "matches", to: `/${lang}/app/matches`, label: t("immoweb_app.nav_matches"), icon: "✦", cluster: "operativo" },
    { key: "mandates", to: `/${lang}/app/mandate-opportunities`, label: t("immoweb_app.nav_mandates") || "Mandati", icon: "◆", cluster: "operativo" },
    // A-034 R4 — Analytics A/B fuori nav primaria (link in Impostazioni)
    { key: "mls", to: `/${lang}/app/mls`, label: "MLS", icon: "⧉", cluster: "pubblicazione" },
    ...(isAgencyAdmin
      ? [{ key: "website", to: `/${lang}/app/website`, label: t("immoweb_app.nav_website") || "Sito web", icon: "🎨", cluster: "pubblicazione" }]
      : []),
    // Strumenti commerciali restano in evidenza (D-168)
    { key: "staging", to: `/${lang}/app/staging`, label: "Virtual Staging", icon: "✨", cluster: "strumenti" },
    { key: "mutui", to: `/${lang}/app/mutui`, label: t("mutui.nav") || "Mutui", icon: "💰", cluster: "strumenti" },
    { key: "modulistica", to: `/${lang}/app/modulistica`, label: "Modulistica", icon: "📑", cluster: "strumenti" },
    { key: "legal", to: `/${lang}/legal`, label: "HAL Legal", icon: "⚖", cluster: "intelligenza" },
    { key: "hal-knowledge", to: `/${lang}/app/hal-knowledge`, label: "Guida HAL", icon: "📚", cluster: "intelligenza" },
    { key: "members", to: `/${lang}/app/members`, label: t("immoweb_app.nav_members"), icon: "✉", cluster: "amministrazione" },
    ...(isAgencyAdmin
      ? [{ key: "billing", to: `/${lang}/app/settings/billing`, label: "Piano & Crediti", icon: "💳", cluster: "amministrazione" }]
      : []),
    ...(isAgencyAdmin
      ? [{ key: "settings", to: `/${lang}/app/settings`, label: t("immoweb_app.nav_settings"), icon: "⚙", cluster: "amministrazione" }]
      : []),
  ];

  const NAV_CLUSTERS = [
    { id: "avvio", label: "Avvio" },
    { id: "operativo", label: "Operativo" },
    { id: "pubblicazione", label: "Pubblicazione" },
    { id: "strumenti", label: "Strumenti" },
    { id: "intelligenza", label: "Intelligenza" },
    { id: "amministrazione", label: "Amministrazione" },
  ];
  const clusteredNav = NAV_CLUSTERS
    .map((cl) => ({ ...cl, items: navItems.filter((i) => i.cluster === cl.id) }))
    .filter((cl) => cl.items.length > 0);

  if (agency === null) {
    return (
      <div
        className="min-h-screen flex items-center justify-center bg-stone-50 text-stone-500 font-sans text-sm uppercase tracking-widest"
        data-testid="agency-shell-loading"
      >
        {t("common.loading")}
      </div>
    );
  }

  const imp = user?.ops_impersonation;
  const exitImpersonation = async () => {
    try {
      await api.post("/app/ops/bridge/impersonate/exit");
      window.location.href = `/${lang}/app/ops`;
    } catch {
      nav(`/${lang}/app/ops`);
    }
  };

  return (
    <div
      data-testid="agency-shell"
      className="min-h-screen bg-stone-50 text-stone-900 flex"
      style={{ fontFamily: "'Inter', system-ui, sans-serif" }}
    >
      <ForceChangePasswordModal />
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 bg-stone-900/50 z-30 md:hidden"
          aria-label="Close sidebar"
        />
      )}

      {/* Sidebar */}
      <aside
        data-testid="agency-sidebar"
        className={`fixed md:static inset-y-0 left-0 z-40 w-64 bg-[#0B1E3F] text-stone-100 flex flex-col transform transition-transform md:transform-none ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        <div className="px-6 py-6 border-b border-stone-700/40">
          <Link
            to={`/${lang}`}
            className="flex items-center gap-2 text-lg tracking-tight font-medium text-stone-50"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            <OmniaLogo variant="mark" size="sm" inverted={true} />
            <span>
              <Brand>OMNIA</Brand>
              <span className="text-stone-400">·</span>
              <Brand className="font-light text-stone-300">app</Brand>
            </span>
          </Link>
          {user?.role === "super_admin" && imp ? (
            <div className="mt-2 space-y-1" data-testid="impersonation-badge">
              <p className="text-xs text-amber-300 truncate">
                Vista CRM · {imp.agency_name || agency?.display_name || "agenzia"}
              </p>
              <button
                type="button"
                onClick={exitImpersonation}
                className="text-[10px] uppercase tracking-widest text-[#C19A6B] hover:text-white underline"
                data-testid="impersonation-exit"
              >
                Torna alla cabina
              </button>
            </div>
          ) : null}
          {user?.role === "super_admin" && !imp ? (
            <p className="mt-2 text-xs text-[#C19A6B] truncate" data-testid="agency-name">
              Founder · piattaforma
            </p>
          ) : null}
          {user?.role !== "super_admin" && agency && myAgencies.length < 2 && (
            <p className="mt-2 text-xs text-stone-400 truncate" data-testid="agency-name">
              {agency.display_name}
            </p>
          )}
          {user?.role !== "super_admin" && myAgencies.length >= 2 && (
            <select
              data-testid="agency-switcher"
              value={user?.active_agency_id || user?.agency_ids?.[0] || ""}
              onChange={(e) => switchAgency(e.target.value)}
              className="mt-2 w-full bg-[#0B1E3F] border border-stone-600 rounded px-2 py-1 text-xs text-stone-300 cursor-pointer"
              aria-label="Cambia agenzia attiva"
            >
              {myAgencies.map((a) => (
                <option key={a.id} value={a.id}>{a.display_name}</option>
              ))}
            </select>
          )}
        </div>

        <nav className="flex-1 px-3 py-4 space-y-4 overflow-y-auto" data-testid="agency-nav-clusters">
          {clusteredNav.map((cluster) => (
            <div key={cluster.id} data-testid={`nav-cluster-${cluster.id}`}>
              <p className="px-3 mb-1.5 text-[9px] uppercase tracking-[0.2em] text-stone-500">
                {cluster.label}
              </p>
              <div className="space-y-0.5">
                {cluster.items.map((item) => {
                  const isActive = current === item.key && !item.locked;
                  return (
                    <Link
                      key={item.key}
                      to={item.locked ? "#" : item.to}
                      data-testid={`sidebar-nav-${item.key}`}
                      onClick={(e) => {
                        if (item.locked) e.preventDefault();
                        setSidebarOpen(false);
                      }}
                      className={`flex items-center justify-between gap-3 px-3 py-2 rounded-md text-sm transition ${
                        isActive
                          ? "bg-stone-100/10 text-stone-50 font-medium"
                          : item.locked
                          ? "text-stone-500 cursor-not-allowed"
                          : "text-stone-300 hover:bg-stone-100/5 hover:text-stone-50"
                      }`}
                    >
                      <span className="flex items-center gap-3">
                        <span className="text-base w-5 inline-block text-center" aria-hidden="true">
                          {item.icon}
                        </span>
                        <span>{item.label}</span>
                      </span>
                      {item.locked && (
                        <span className="text-[9px] uppercase tracking-widest text-amber-500">
                          M2.S4
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        <div className="px-3 py-4 border-t border-stone-700/40 space-y-3">
          <div className="px-3 text-xs text-stone-400">
            {user?.name}
          </div>
          <div className="px-3 text-[10px] uppercase tracking-widest text-stone-500">
            {user?.role}
          </div>
          <button
            data-testid="sidebar-logout"
            onClick={onLogout}
            className="w-full text-left px-3 py-2.5 rounded-md text-sm text-stone-300 hover:bg-stone-100/5 hover:text-stone-50 transition"
          >
            ← {t("immoweb_app.nav_logout")}
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 min-w-0 flex flex-col">
        {/* Topbar */}
        <header
          data-testid="agency-topbar"
          className="sticky top-0 z-20 bg-stone-50/95 backdrop-blur border-b border-stone-200 px-4 md:px-8 py-3 flex items-center justify-between gap-4"
        >
          <button
            onClick={() => setSidebarOpen(true)}
            className="md:hidden text-stone-700 text-xl px-2"
            aria-label="Open menu"
            data-testid="open-sidebar"
          >
            ☰
          </button>
          <div className="flex-1 min-w-0">
            <p className="text-[10px] uppercase tracking-widest text-stone-500">
              {user?.role === "super_admin"
                ? "Area Founder"
                : t("immoweb_app.agency_label")}
            </p>
            <p className="text-sm font-semibold text-stone-900 truncate" data-testid="shell-context-label">
              {user?.role === "super_admin"
                ? "OMNIA · Ops (non un’agenzia cliente)"
                : agency?.display_name || "—"}
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {backVisible && (
              <BackButton className="border border-stone-200 rounded-md px-2.5 py-1.5 bg-white hover:bg-stone-100" />
            )}
            <NotificationBell />
            <LanguageSwitcher />
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 px-4 md:px-8 py-6 md:py-10 max-w-screen-2xl w-full mx-auto">
          {children}
        </main>
      </div>
      {/* Widget HAL (CRM): nascosto su Guida HAL — lì c’è già la chat della guida */}
      {current !== "hal-knowledge" && current !== "legal" ? <AlChatWidget /> : null}
    </div>
  );
}

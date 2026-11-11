import React from "react";
import { Link, NavLink, Outlet, useParams } from "react-router-dom";
import Brand from "../../../shared/components/Brand";
import OmniaLogo from "../../../shared/components/OmniaLogo";
import { useAuth } from "../../../shared/lib/auth";

/**
 * Cabina di regia Super Admin — shell dedicata (fuori dallo shell CRM agenzia).
 */
const NAV = [
  { to: "ingresso", end: true, label: "Ingresso", hint: "Coda e salute" },
  { to: "clienti", label: "Clienti", hint: "Agenzie e B2C" },
  { to: "fornitori", label: "Fornitori", hint: "Provider esterni" },
  { to: "api", label: "API", hint: "Chiavi e circuiti" },
  { to: "listino", label: "Listino", hint: "Prezzi B2B/B2C" },
  { to: "finanze", label: "Finanze", hint: "Costi e incassi" },
  { to: "contenuti", label: "Contenuti", hint: "Moderazione" },
  { to: "piattaforma", label: "Piattaforma", hint: "Backup e gate" },
];

const EXTRA_LINKS = [
  { toSuffix: "/legal", label: "Ops Legal", hint: "HAL Legal costi" },
];

export default function FounderBridgeShell() {
  const { lang: langParam } = useParams();
  const lang = langParam || "it";
  const { user, logout } = useAuth();
  const base = `/${lang}/app/ops`;

  return (
    <div
      data-testid="founder-bridge-shell"
      className="min-h-screen bg-[#f4f1ec] text-stone-900 flex"
      style={{ fontFamily: "'Inter', system-ui, sans-serif" }}
    >
      <aside
        data-testid="founder-bridge-nav"
        className="w-60 shrink-0 bg-[#0B1E3F] text-stone-100 flex flex-col min-h-screen"
      >
        <div className="px-5 py-6 border-b border-white/10">
          <Link to={base} className="flex items-center gap-2 text-stone-50">
            <OmniaLogo variant="mark" size="sm" inverted />
            <span style={{ fontFamily: "'Fraunces', Georgia, serif" }} className="text-lg tracking-tight">
              <Brand>OMNIA</Brand>
            </span>
          </Link>
          <p className="mt-2 text-[10px] uppercase tracking-[0.25em] text-[#C19A6B]">
            Cabina di regia
          </p>
          <p className="mt-1 text-xs text-stone-400 truncate" title={user?.email || ""}>
            {user?.email || "super_admin"}
          </p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to === "ingresso" ? base : `${base}/${item.to}`}
              end={item.end}
              data-testid={`bridge-nav-${item.to}`}
              className={({ isActive }) =>
                `block rounded-md px-3 py-2.5 transition ${
                  isActive
                    ? "bg-white/10 text-white"
                    : "text-stone-300 hover:bg-white/5 hover:text-white"
                }`
              }
            >
              <span className="block text-sm font-medium">{item.label}</span>
              <span className="block text-[10px] uppercase tracking-widest text-stone-500 mt-0.5">
                {item.hint}
              </span>
            </NavLink>
          ))}
          {EXTRA_LINKS.map((item) => (
            <Link
              key={item.toSuffix}
              to={`${base}${item.toSuffix}`}
              data-testid={`bridge-nav-extra${item.toSuffix.replace("/", "-")}`}
              className="block rounded-md px-3 py-2.5 text-stone-300 hover:bg-white/5 hover:text-white transition"
            >
              <span className="block text-sm font-medium">{item.label}</span>
              <span className="block text-[10px] uppercase tracking-widest text-stone-500 mt-0.5">
                {item.hint}
              </span>
            </Link>
          ))}
        </nav>

        <div className="px-4 py-4 border-t border-white/10 space-y-2">
          <Link
            to={`/${lang}`}
            className="block text-[10px] uppercase tracking-widest text-stone-400 hover:text-stone-200"
          >
            ← Sito pubblico
          </Link>
          <button
            type="button"
            onClick={() => logout?.()}
            className="text-[10px] uppercase tracking-widest text-stone-500 hover:text-stone-300"
          >
            Esci
          </button>
        </div>
      </aside>

      <main className="flex-1 min-w-0 overflow-x-auto">
        <div className="max-w-6xl mx-auto px-6 md:px-10 py-8 md:py-10">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

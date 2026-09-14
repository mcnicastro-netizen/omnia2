import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import LanguageSwitcher from "./LanguageSwitcher";

/**
 * MobileNav — hamburger menu drawer for screens < md.
 *
 * Props:
 *   - lang: current language code
 *   - links: [{ to: "/it/cloud", label: "Trova casa" }, ...]
 *   - theme: "light" | "dark" | "cream"   (controls colors)
 */
const themes = {
  light: {
    btn: "text-stone-900",
    drawer: "bg-stone-50 text-stone-900",
    border: "border-stone-200",
    hover: "hover:text-stone-500",
  },
  dark: {
    btn: "text-stone-100",
    drawer: "bg-[#0e1419] text-stone-100",
    border: "border-stone-800",
    hover: "hover:text-stone-400",
  },
  cream: {
    btn: "text-stone-900",
    drawer: "bg-[#fdf6e3] text-stone-900",
    border: "border-amber-900/20",
    hover: "hover:text-amber-700",
  },
};

export default function MobileNav({ lang, links = [], theme = "light" }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const T = themes[theme] || themes.light;

  // Lock body scroll when drawer open
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <div className="md:hidden flex items-center gap-3">
      <LanguageSwitcher />
      <button
        data-testid="mobile-nav-toggle"
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label="Toggle navigation"
        className={`inline-flex flex-col gap-[5px] w-8 h-8 items-center justify-center ${T.btn}`}
      >
        <span
          className={`block h-[2px] w-6 bg-current transition-transform ${
            open ? "translate-y-[7px] rotate-45" : ""
          }`}
        />
        <span
          className={`block h-[2px] w-6 bg-current transition-opacity ${
            open ? "opacity-0" : ""
          }`}
        />
        <span
          className={`block h-[2px] w-6 bg-current transition-transform ${
            open ? "-translate-y-[7px] -rotate-45" : ""
          }`}
        />
      </button>

      {open && (
        <div
          data-testid="mobile-nav-drawer"
          className={`fixed inset-0 z-50 ${T.drawer} flex flex-col`}
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        >
          <div className={`flex items-center justify-between px-5 py-6 border-b ${T.border}`}>
            <Link
              to={`/${lang}`}
              onClick={() => setOpen(false)}
              translate="no"
              className="notranslate text-2xl tracking-tight font-medium"
            >
              OMNIA
            </Link>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close"
              className={`text-3xl leading-none ${T.btn}`}
            >
              ×
            </button>
          </div>
          <nav className="flex-1 px-5 py-10 flex flex-col gap-6 text-3xl tracking-tight">
            {links.map((l) => (
              <Link
                key={l.to}
                to={l.to}
                onClick={() => setOpen(false)}
                className={`transition ${T.hover}`}
              >
                {l.label}
              </Link>
            ))}
          </nav>
          <footer className={`px-5 py-6 border-t ${T.border} text-xs uppercase tracking-widest font-sans opacity-70`}>
            <span translate="no" className="notranslate">omniarealestateecosystem.it</span>
          </footer>
        </div>
      )}
    </div>
  );
}

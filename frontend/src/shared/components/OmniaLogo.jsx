/**
 * OmniaLogo — logo canonico OMNIA Real Estate Lab.
 *
 * Vincolo White Label (D-041): questo componente va usato SOLO su
 * interfacce OMNIA-branded (auth, landing pubbliche OMNIA, footer
 * copyright). NON usarlo dentro il dashboard agenzia dove il brand
 * è quello dell'agenzia via ThemeRegistry.
 *
 * Props:
 * - variant: "full" (default, logo + wordmark) | "mark" (solo simbolo)
 * - size: "sm" (24) | "md" (40) | "nav" (64) | "lg" (72) | "xl" (120)
 * - inverted: bool — su sfondi scuri applica filtro invert
 * - className: string per override wrapper
 */
import React from "react";

const HEIGHT_MAP = {
  sm: 24,
  md: 40,
  nav: 72,
  lg: 72,
  xl: 120,
};

export default function OmniaLogo({
  variant = "full",
  size = "md",
  inverted = false,
  className = "",
  alt = "OMNIA Real Estate Lab",
}) {
  const src = variant === "mark" ? "/omnia-mark.png" : "/omnia-logo.png";
  const px = HEIGHT_MAP[size] || HEIGHT_MAP.md;

  return (
    <img
      src={src}
      alt={alt}
      draggable={false}
      loading="eager"
      data-testid={`omnia-logo-${variant}`}
      className={`select-none ${className}`}
      style={{
        height: `${px}px`,
        width: "auto",
        filter: inverted ? "invert(1)" : undefined,
      }}
    />
  );
}

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
 * - size: "sm" (24px) | "md" (40px) | "lg" (72px) | "xl" (120px)
 * - inverted: bool — su sfondi scuri applica filtro invert
 * - showTagline: bool — mostra tagline "Real Estate Lab" sotto (solo variant=full)
 * - className: string per override wrapper
 */
import React from "react";

const SIZE_MAP = {
  sm: 24,
  md: 40,
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
  const px = SIZE_MAP[size] || SIZE_MAP.md;
  const src = variant === "mark" ? "/omnia-mark.png" : "/omnia-logo.png";
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

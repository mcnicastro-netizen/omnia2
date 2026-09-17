import React from "react";

/**
 * Compact page banner shared across ImmobilCloud B2C surfaces.
 * Matches home visual language: navy, brass, Fraunces, photography.
 */
export default function CloudPageHero({
  eyebrow = "ImmobilCloud",
  title,
  subtitle,
  image = "/cloud/living.jpg",
  children,
  testId = "cloud-page-hero",
  compact = false,
}) {
  return (
    <section
      data-testid={testId}
      className={`relative overflow-hidden ${compact ? "min-h-[200px]" : "min-h-[260px] md:min-h-[300px]"}`}
    >
      <img
        src={image}
        alt=""
        className="absolute inset-0 w-full h-full object-cover scale-105"
      />
      <div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(105deg, rgba(11,30,63,0.92) 0%, rgba(11,30,63,0.72) 55%, rgba(11,30,63,0.45) 100%)",
        }}
      />
      <div className="relative max-w-6xl mx-auto px-5 sm:px-8 md:px-16 py-10 md:py-14">
        <p className="text-[11px] uppercase tracking-[0.32em] text-[#E8D5B5] mb-3">
          {eyebrow}
          {eyebrow === "ImmobilCloud" && (
            <sup className="text-[7px] ml-0.5">™</sup>
          )}
        </p>
        <h1
          className="text-3xl sm:text-4xl md:text-5xl font-light tracking-tight text-white max-w-2xl leading-[1.05]"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        >
          {title}
        </h1>
        {subtitle && (
          <p className="mt-3 text-base text-white/75 max-w-xl leading-relaxed">
            {subtitle}
          </p>
        )}
        {children && <div className="mt-6">{children}</div>}
      </div>
    </section>
  );
}

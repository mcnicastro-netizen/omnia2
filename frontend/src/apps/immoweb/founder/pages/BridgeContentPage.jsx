import React from "react";
import { Link, useParams } from "react-router-dom";

export default function BridgeContentPage() {
  const { lang: langParam } = useParams();
  const lang = langParam || "it";

  const cards = [
    {
      to: `/${lang}/app/moderation`,
      title: "Moderazione UGC",
      body: "Annunci privati in verifica, safety gate, publish/reject.",
      testid: "bridge-link-moderation",
    },
    {
      to: `/${lang}/app/ops/legal`,
      title: "Ops Legal",
      body: "Consumi e qualità HAL Legal, audit domande.",
      testid: "bridge-link-legal",
    },
    {
      to: `/${lang}/app/brand-lab`,
      title: "Brand Lab",
      body: "Asset creativi e repository interno Founder.",
      testid: "bridge-link-brand",
    },
  ];

  return (
    <div data-testid="bridge-contenuti" className="space-y-8">
      <header>
        <h1
          className="text-3xl text-[#0B1E3F] tracking-tight"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        >
          Contenuti & rischio
        </h1>
        <p className="mt-2 text-sm text-stone-600 max-w-2xl">
          Strumenti già vivi sulla piattaforma — aperti dalla cabina, non mescolati al CRM
          agenzia.
        </p>
      </header>

      <ul className="grid md:grid-cols-3 gap-4">
        {cards.map((c) => (
          <li key={c.to}>
            <Link
              to={c.to}
              data-testid={c.testid}
              className="block h-full bg-white border border-stone-200 rounded-lg px-5 py-5 hover:border-[#0B1E3F]/40 transition"
            >
              <p className="text-lg text-[#0B1E3F]" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                {c.title}
              </p>
              <p className="mt-2 text-sm text-stone-600">{c.body}</p>
              <p className="mt-4 text-[10px] uppercase tracking-widest text-[#C19A6B]">Apri →</p>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

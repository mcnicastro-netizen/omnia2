/* OMNIA — PropertyDetail Schema.org JSON-LD (MOVE-ONLY). */
import React from "react";

/* Schema.org RealEstateListing JSON-LD for SEO + sharing rich previews */
export default function SchemaOrgJsonLd({ prop, publicUrl }) {
  const data = {
    "@context": "https://schema.org",
    "@type": "RealEstateListing",
    name: prop.title,
    description: prop.description,
    url: publicUrl,
    address: {
      "@type": "PostalAddress",
      addressLocality: prop.city,
      addressRegion: prop.province,
      postalCode: prop.postal_code,
      addressCountry: "IT",
    },
    ...(prop.lat && prop.lng ? {
      geo: { "@type": "GeoCoordinates", latitude: prop.lat, longitude: prop.lng }
    } : {}),
    ...(prop.price ? {
      offers: { "@type": "Offer", price: prop.price, priceCurrency: "EUR" }
    } : {}),
    ...(prop.surface_sqm ? {
      floorSize: { "@type": "QuantitativeValue", value: prop.surface_sqm, unitCode: "MTK" }
    } : {}),
  };
  return (
    <script
      type="application/ld+json"
      data-testid="schema-jsonld"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, "\\u003c") }}
    />
  );
}

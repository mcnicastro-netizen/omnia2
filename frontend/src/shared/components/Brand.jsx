/**
 * Brand — wraps brand names / technical codes so browser auto-translate
 * (Chrome / Edge / Safari) doesn't mangle them (e.g. "IT" → "esso").
 */
import React from "react";

export default function Brand({ children, as: Tag = "span", className = "" }) {
  return (
    <Tag translate="no" className={`notranslate ${className}`}>
      {children}
    </Tag>
  );
}

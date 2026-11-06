import React, { useEffect, useState } from "react";
import QRCode from "qrcode";

/** QR code client-side (nessuna API esterna). */
export default function PwaQrCode({ url, size = 220, testid = "pwa-qr" }) {
  const [src, setSrc] = useState("");

  useEffect(() => {
    let cancelled = false;
    if (!url) return undefined;
    QRCode.toDataURL(url, {
      width: size * 2,
      margin: 2,
      color: { dark: "#0B1E3F", light: "#FFFFFF" },
      errorCorrectionLevel: "M",
    })
      .then((data) => {
        if (!cancelled) setSrc(data);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [url, size]);

  if (!src) {
    return (
      <div
        data-testid={testid}
        className="bg-white rounded-xl animate-pulse"
        style={{ width: size, height: size }}
        aria-hidden
      />
    );
  }

  return (
    <img
      src={src}
      alt="QR code ImmobilCloud app"
      width={size}
      height={size}
      data-testid={testid}
      className="rounded-xl bg-white p-2 shadow-sm"
    />
  );
}

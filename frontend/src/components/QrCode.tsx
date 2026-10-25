"use client";

import { useEffect, useState } from "react";
import QRCode from "qrcode";

export default function QrCode({ value, size = 140 }: { value: string; size?: number }) {
  const [svg, setSvg] = useState<string>("");
  useEffect(() => {
    QRCode.toString(value, { type: "svg", margin: 0, errorCorrectionLevel: "M", color: { dark: "#111111", light: "#ffffff" } })
      .then(setSvg)
      .catch(() => setSvg(""));
  }, [value]);
  return (
    <div
      style={{ width: size, height: size }}
      className="shrink-0 [&>svg]:h-full [&>svg]:w-full"
      aria-hidden
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}

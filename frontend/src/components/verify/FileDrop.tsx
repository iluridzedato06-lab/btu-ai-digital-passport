"use client";

import { useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { sha256Hex } from "@/lib/hash";

/** Hashes a dropped PDF locally. The file never leaves the browser. */
export default function FileDrop({ onHash }: { onHash: (hash: string, name: string) => void }) {
  const t = useTranslations("verify.file");
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handle(file?: File | null) {
    if (!file) return;
    if (file.type && file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      setError(t("notPdf"));
      return;
    }
    setError(null);
    setBusy(true);
    try {
      const hash = await sha256Hex(await file.arrayBuffer());
      onHash(hash, file.name);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => input.current?.click()}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && input.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setOver(false);
          handle(e.dataTransfer.files?.[0]);
        }}
        className={`flex cursor-pointer flex-col items-center justify-center border-2 border-dashed px-6 py-10 text-center transition-colors ${
          over ? "border-magenta bg-magenta/5" : "border-ink/40 hover:border-ink"
        }`}
      >
        <svg width="34" height="40" viewBox="0 0 34 40" aria-hidden className="mb-3">
          <path d="M2 2h20l10 10v26H2z" fill="none" stroke="#111" strokeWidth="2.5" />
          <path d="M22 2v10h10" fill="none" stroke="#111" strokeWidth="2.5" />
          <text x="17" y="31" textAnchor="middle" fontSize="9" fontWeight="800" fontFamily="Montserrat, sans-serif">PDF</text>
        </svg>
        <span className="font-semibold">{busy ? t("hashing") : t("drop")}</span>
        <span className="mt-1 text-sm text-muted underline underline-offset-4">{t("choose")}</span>
        <input
          ref={input}
          type="file"
          accept="application/pdf,.pdf"
          className="sr-only"
          onChange={(e) => handle(e.target.files?.[0])}
        />
      </div>
      {error && <p role="alert" className="mt-2 text-sm text-bad">{error}</p>}
    </div>
  );
}

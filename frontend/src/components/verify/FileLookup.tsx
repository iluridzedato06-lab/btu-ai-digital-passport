"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";
import { api, type VerifyResult } from "@/lib/api";
import FileDrop from "./FileDrop";

export default function FileLookup() {
  const t = useTranslations("verify");
  const router = useRouter();
  const [msg, setMsg] = useState<string | null>(null);

  return (
    <div>
      <FileDrop
        onHash={async (hash) => {
          setMsg(null);
          try {
            const r = await api<VerifyResult>(`/public/verify/by-hash/${hash}`);
            if (r.status === "not_found" || !r.verification_code) {
              setMsg(t("file.unknown"));
              return;
            }
            router.push(`/verify/${r.verification_code}`);
          } catch {
            setMsg(t("rateLimited"));
          }
        }}
      />
      {msg && <p role="status" className="mt-3 border-l-8 border-bad bg-bad-bg p-4 font-semibold">{msg}</p>}
    </div>
  );
}

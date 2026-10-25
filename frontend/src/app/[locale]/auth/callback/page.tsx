"use client";

import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { Link, useRouter } from "@/i18n/navigation";
import { api } from "@/lib/api";

export default function Callback() {
  const t = useTranslations("auth");
  const router = useRouter();
  const [failed, setFailed] = useState(false);
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return;
    ran.current = true;
    const params = new URLSearchParams(window.location.hash.slice(1));
    const token = params.get("token");
    // Remove the token from the address bar and history immediately.
    window.history.replaceState(null, "", window.location.pathname);
    if (!token) {
      setFailed(true);
      return;
    }
    api<{ role: string }>("/auth/magic-link/consume", { json: { token } })
      .then((r) => {
        router.replace(r.role === "admin" || r.role === "staff" ? "/admin" : "/dashboard");
        router.refresh();
      })
      .catch(() => setFailed(true));
  }, [router]);

  return (
    <div className="mx-auto max-w-xl px-4 py-24 sm:px-6">
      {failed ? (
        <div className="border-l-8 border-bad bg-bad-bg p-6" role="alert">
          <p className="font-display text-xl font-extrabold">{t("callbackFailed")}</p>
          <Link href="/login" className="btn btn-dark mt-5">{t("requestNew")}</Link>
        </div>
      ) : (
        <p className="flex items-center gap-3 text-lg" aria-live="polite">
          <span className="inline-block h-5 w-5 animate-spin border-2 border-ink border-t-transparent" aria-hidden />
          {t("callbackWorking")}
        </p>
      )}
    </div>
  );
}

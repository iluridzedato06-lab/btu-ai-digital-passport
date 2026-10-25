"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Link, usePathname, useRouter } from "@/i18n/navigation";
import { api, type Me } from "@/lib/api";

export default function AuthNav() {
  const t = useTranslations("common.nav");
  const router = useRouter();
  const pathname = usePathname();
  const [me, setMe] = useState<Me | null>(null);

  // Re-check on every navigation so the header reflects sign-in / sign-out immediately.
  useEffect(() => {
    api<Me>("/me").then(setMe).catch(() => setMe({ authenticated: false, role: "anon", student: null, passport: null }));
  }, [pathname]);

  if (!me) return <span className="h-10 w-36" aria-hidden />;

  if (!me.authenticated) {
    return (
      <Link href="/login" className="btn btn-dark !py-2 !px-4 text-sm">
        {t("signIn")}
      </Link>
    );
  }

  const staff = me.role === "admin" || me.role === "staff";
  return (
    <div className="flex items-center gap-4 text-sm">
      {staff && (
        <Link href="/admin" className="font-semibold hover:text-magenta">
          {t("admin")}
        </Link>
      )}
      {me.student && (
        <Link href="/dashboard" className="font-semibold hover:text-magenta">
          {t("dashboard")}
        </Link>
      )}
      <button
        type="button"
        className="btn btn-ghost !py-2 !px-3 text-sm"
        onClick={async () => {
          await api("/auth/logout", { method: "POST" }).catch(() => null);
          router.push("/");
          router.refresh();
          setMe({ authenticated: false, role: "anon", student: null, passport: null });
        }}
      >
        {t("signOut")}
      </button>
    </div>
  );
}

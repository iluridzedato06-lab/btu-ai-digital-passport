"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Link, usePathname, useRouter } from "@/i18n/navigation";
import { api, type Me } from "@/lib/api";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const t = useTranslations("admin");
  const router = useRouter();
  const pathname = usePathname();
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    api<Me>("/me")
      .then((m) => {
        if (!m.authenticated) router.replace("/login");
        else setMe(m);
      })
      .catch(() => router.replace("/login"));
  }, [router]);

  if (!me) return null;
  if (me.role !== "admin" && me.role !== "staff") {
    return <p className="mx-auto max-w-3xl px-4 py-20 text-lg sm:px-6">{t("forbidden")}</p>;
  }

  const items = [
    ["/admin", t("nav.overview")],
    ["/admin/sync", t("nav.sync")],
    ["/admin/students", t("nav.students")],
    ["/admin/audit", t("nav.audit")],
    ["/admin/catalog", t("nav.catalog")],
  ] as const;

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b-2 border-ink pb-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-magenta">{me.email} · {me.role}</p>
          <h1 className="font-display text-3xl font-black">{t("title")}</h1>
        </div>
        <nav className="flex flex-wrap gap-1 text-sm font-semibold" aria-label="Admin">
          {items.map(([href, label]) => {
            const active = href === "/admin" ? pathname === "/admin" : pathname.startsWith(href);
            return (
              <Link key={href} href={href} className={`px-3 py-2 ${active ? "bg-ink text-white" : "hover:bg-fog"}`}>
                {label}
              </Link>
            );
          })}
        </nav>
      </div>
      <div className="pt-8">{children}</div>
    </div>
  );
}

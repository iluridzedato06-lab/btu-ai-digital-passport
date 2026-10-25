"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { useApi } from "@/components/admin/useApi";

type Student = { id: string; student_number: string; first_name: string; last_name: string; email: string;
  passport_id: string | null; latest_version: number; stamp_count: number; consent: boolean };

export default function Students() {
  const t = useTranslations("admin.students");
  const [q, setQ] = useState("");
  const [query, setQuery] = useState("");
  useEffect(() => {
    const id = setTimeout(() => setQuery(q), 250);
    return () => clearTimeout(id);
  }, [q]);
  const { data } = useApi<Student[]>(`/admin/students?q=${encodeURIComponent(query)}`);

  return (
    <div>
      <input className="field max-w-xl" placeholder={t("search")} value={q} onChange={(e) => setQ(e.target.value)} aria-label={t("search")} />
      <div className="mt-6 overflow-x-auto">
        <table className="table-basic min-w-[760px]">
          <thead>
            <tr><th>{t("name")}</th><th>{t("number")}</th><th>{t("email")}</th><th>{t("passport")}</th><th>{t("stamps")}</th><th>{t("version")}</th></tr>
          </thead>
          <tbody>
            {data?.map((s) => (
              <tr key={s.id}>
                <td><Link href={`/admin/students/${s.id}`} className="font-semibold underline underline-offset-4">{s.first_name} {s.last_name}</Link></td>
                <td>{s.student_number}</td>
                <td className="text-muted">{s.email}</td>
                <td className="font-display font-bold">{s.passport_id ?? "—"}</td>
                <td>{s.stamp_count}</td>
                <td>{s.latest_version ? `v${s.latest_version}` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {data && data.length === 0 && <p className="mt-4 text-muted">{t("none")}</p>}
      </div>
    </div>
  );
}

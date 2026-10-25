"use client";

import { useTranslations } from "next-intl";
import { useApi } from "@/components/admin/useApi";
import Stamp from "@/components/Stamp";

type Skill = { skill_code: string; name_en: string; name_ka: string; stamp_type: "FOCUSED" | "APPLIED" | "ADVANCED";
  description_en: string; default_earned_through: string; is_active: boolean; holders: number };

export default function Catalog() {
  const t = useTranslations("admin.catalog");
  const ts = useTranslations("stamps");
  const { data } = useApi<Skill[]>("/admin/catalog");
  return (
    <div>
      <p className="text-muted">{t("lead")}</p>
      <div className="mt-6 overflow-x-auto">
        <table className="table-basic min-w-[880px]">
          <thead><tr><th /><th>{t("code")}</th><th>{t("skill")}</th><th>{t("type")}</th><th>{t("holders")}</th><th>{t("active")}</th></tr></thead>
          <tbody>
            {data?.map((s) => (
              <tr key={s.skill_code}>
                <td className="w-28"><Stamp type={s.stamp_type} className="!h-10" alt="" /></td>
                <td className="font-semibold">{s.skill_code}</td>
                <td>{s.name_en}<div className="text-xs text-muted">{s.name_ka}</div><div className="mt-1 text-xs text-muted">{s.description_en}</div></td>
                <td>{ts(`${s.stamp_type}.title`)}</td>
                <td>{s.holders}</td>
                <td>{s.is_active ? "✓" : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

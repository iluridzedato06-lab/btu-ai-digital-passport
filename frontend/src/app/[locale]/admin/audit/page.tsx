"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { useApi } from "@/components/admin/useApi";
import { fmtDateTime } from "@/lib/format";

type Entry = { id: string; created_at: string; actor: string; action: string; target_type: string; target_id: string; metadata: Record<string, unknown> };

export default function Audit() {
  const t = useTranslations("admin.audit");
  const [f, setF] = useState("");
  const [q, setQ] = useState("");
  useEffect(() => {
    const id = setTimeout(() => setQ(f), 250);
    return () => clearTimeout(id);
  }, [f]);
  const { data } = useApi<Entry[]>(`/admin/audit?action=${encodeURIComponent(q)}`, 10000);
  return (
    <div>
      <input className="field max-w-md" placeholder={t("filter")} value={f} onChange={(e) => setF(e.target.value)} aria-label={t("filter")} />
      <div className="mt-6 overflow-x-auto">
        <table className="table-basic min-w-[880px]">
          <thead><tr><th>{t("when")}</th><th>{t("action")}</th><th>{t("actor")}</th><th>{t("target")}</th><th>{t("details")}</th></tr></thead>
          <tbody>
            {data?.map((a) => (
              <tr key={a.id}>
                <td className="whitespace-nowrap text-muted">{fmtDateTime(a.created_at)}</td>
                <td className="font-semibold">{a.action}</td>
                <td>{a.actor}</td>
                <td className="text-muted">{a.target_type}</td>
                <td className="mono text-xs">{JSON.stringify(a.metadata)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

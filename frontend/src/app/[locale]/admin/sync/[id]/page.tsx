"use client";

import { use } from "react";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { useApi } from "@/components/admin/useApi";
import { fmtDateTime } from "@/lib/format";

type Run = { id: string; status: string; adapter: string; triggered_by: string; started_at: string | null; finished_at: string | null;
  rows_seen: number; rows_created: number; rows_updated: number; rows_errors: number; versions_issued: number; versions_anchored: number;
  error: string; events: { message: string; level?: string }[] };

export default function RunDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const t = useTranslations("admin.sync");
  const { data } = useApi<Run>(`/admin/sync-runs/${id}`, 4000);
  if (!data) return null;
  return (
    <div className="space-y-8">
      <Link href="/admin/sync" className="text-sm underline">← {t("runs")}</Link>
      <h2 className="font-display text-2xl font-black">{t("detail")}</h2>
      <dl className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
        {Object.entries({
          [t("status")]: data.status, [t("by")]: data.triggered_by, Adapter: data.adapter,
          [t("started")]: fmtDateTime(data.started_at), [t("rows")]: data.rows_seen,
          Created: data.rows_created, Updated: data.rows_updated, [t("errors")]: data.rows_errors,
          [t("issued")]: data.versions_issued, [t("anchored")]: data.versions_anchored,
        }).map(([k, v]) => (
          <div key={k} className="border border-line p-3"><dt className="text-muted">{k}</dt><dd className="font-semibold">{String(v)}</dd></div>
        ))}
      </dl>
      {data.error && <pre className="overflow-x-auto bg-bad-bg p-4 text-sm text-bad">{data.error}</pre>}
      <section>
        <h3 className="font-display text-lg font-black">{t("events")}</h3>
        <ul className="mt-3 space-y-1 text-sm">
          {data.events.map((e, i) => (
            <li key={i} className={e.level === "error" ? "text-bad" : ""}>• {e.message}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}

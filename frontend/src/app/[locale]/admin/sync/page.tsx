"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { useApi } from "@/components/admin/useApi";
import { api, ApiError } from "@/lib/api";
import { fmtDateTime } from "@/lib/format";

type Run = { id: string; status: string; adapter: string; triggered_by: string; created_at: string; started_at: string | null;
  rows_seen: number; rows_errors: number; versions_issued: number; versions_anchored: number; error: string };
type Row = { tab: string; row_key: string; row_number: number; status: string; message: string };
type Withdrawal = { award_id: string; student_number: string; student: string; skill: string; requested_at: string; in_version: number | null };

const STATUS_COLOR: Record<string, string> = { ok: "text-ok", partial: "text-warn", failed: "text-bad", running: "text-btu-blue", requested: "text-muted" };

export default function SyncPage() {
  const t = useTranslations("admin.sync");
  const runs = useApi<Run[]>("/admin/sync-runs", 4000);
  const errors = useApi<Row[]>("/admin/sheet-rows?status=ERROR", 8000);
  const wd = useApi<Withdrawal[]>("/admin/withdrawals", 8000);
  const [msg, setMsg] = useState<string | null>(null);

  async function act(path: string) {
    setMsg(null);
    try {
      await api(path, { method: "POST" });
      wd.reload();
      runs.reload();
    } catch (e) {
      setMsg((e as ApiError).message);
    }
  }

  return (
    <div className="space-y-12">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="font-display text-2xl font-black">{t("title")}</h2>
          <p className="text-muted">{t("lead")}</p>
        </div>
        <button
          className="btn btn-dark"
          onClick={async () => {
            await act("/admin/sync-runs");
            setMsg(t("requested"));
          }}
        >
          {t("run")}
        </button>
      </div>
      {msg && <p role="status" className="border-l-4 border-orange bg-warn-bg p-3 text-sm">{msg}</p>}

      <section>
        <h3 className="font-display text-lg font-black">{t("withdrawals")}</h3>
        <p className="text-sm text-muted">{t("withdrawalsLead")}</p>
        {wd.data && wd.data.length > 0 ? (
          <table className="table-basic mt-3">
            <tbody>
              {wd.data.map((w) => (
                <tr key={w.award_id}>
                  <td className="font-semibold">{w.award_id}</td>
                  <td>{w.student} <span className="text-muted">({w.student_number})</span></td>
                  <td>{w.skill}</td>
                  <td className="text-muted">{fmtDateTime(w.requested_at)}</td>
                  <td className="space-x-2 text-right whitespace-nowrap">
                    <button className="btn btn-dark !px-3 !py-1.5 text-sm" onClick={() => act(`/admin/awards/${w.award_id}/withdraw`)}>{t("approve")}</button>
                    <button className="btn btn-ghost !px-3 !py-1.5 text-sm" onClick={() => act(`/admin/awards/${w.award_id}/keep`)}>{t("keep")}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <p className="mt-3 text-sm text-muted">{t("noWithdrawals")}</p>}
      </section>

      <section>
        <h3 className="font-display text-lg font-black">{t("errorRows")}</h3>
        {errors.data && errors.data.length > 0 ? (
          <table className="table-basic mt-3">
            <thead><tr><th>{t("tab")}</th><th>{t("row")}</th><th>{t("key")}</th><th>{t("message")}</th></tr></thead>
            <tbody>
              {errors.data.map((r) => (
                <tr key={`${r.tab}-${r.row_key}`}>
                  <td>{r.tab}</td><td>{r.row_number}</td><td className="font-semibold">{r.row_key}</td><td className="text-bad">{r.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <p className="mt-3 text-sm text-muted">{t("noErrors")}</p>}
      </section>

      <section>
        <h3 className="font-display text-lg font-black">{t("runs")}</h3>
        <div className="overflow-x-auto">
          <table className="table-basic mt-3 min-w-[760px]">
            <thead>
              <tr><th>{t("started")}</th><th>{t("status")}</th><th>{t("by")}</th><th>{t("rows")}</th><th>{t("errors")}</th><th>{t("issued")}</th><th>{t("anchored")}</th></tr>
            </thead>
            <tbody>
              {runs.data?.map((r) => (
                <tr key={r.id}>
                  <td><Link href={`/admin/sync/${r.id}`} className="underline underline-offset-4">{fmtDateTime(r.started_at ?? r.created_at)}</Link></td>
                  <td className={`font-semibold ${STATUS_COLOR[r.status] ?? ""}`}>{r.status}</td>
                  <td className="text-muted">{r.triggered_by}</td>
                  <td>{r.rows_seen}</td>
                  <td className={r.rows_errors ? "text-bad" : ""}>{r.rows_errors}</td>
                  <td>{r.versions_issued}</td>
                  <td>{r.versions_anchored}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

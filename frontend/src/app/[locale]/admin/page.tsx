"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { useApi } from "@/components/admin/useApi";
import { fmtDateTime } from "@/lib/format";

type Overview = {
  students: number; passports: number; versions_anchored: number; versions_pending: number; versions_failed: number;
  stamps: number; sheet_errors: number; withdrawals_pending: number;
  last_sync: null | { id: string; status: string; finished_at: string | null; started_at: string | null; versions_issued: number; rows_errors: number };
  worker_last_seen: string | null;
  issuer: { chain_name: string; chain_id: number; contract_address: string | null; issuer_addresses: { address: string }[]; owner_address: string | null };
  recent_audit: { id: string; created_at: string; actor: string; action: string; metadata: Record<string, unknown> }[];
};

export default function AdminOverview() {
  const t = useTranslations("admin.overview");
  const { data } = useApi<Overview>("/admin/overview", 10000);
  if (!data) return null;

  const tiles: [string, number, string?, string?][] = [
    [t("students"), data.students, "/admin/students"],
    [t("passports"), data.passports, "/admin/students"],
    [t("anchored"), data.versions_anchored],
    [t("pending"), data.versions_pending, undefined, data.versions_pending ? "text-warn" : ""],
    [t("failed"), data.versions_failed, undefined, data.versions_failed ? "text-bad" : ""],
    [t("stamps"), data.stamps],
    [t("sheetErrors"), data.sheet_errors, "/admin/sync", data.sheet_errors ? "text-bad" : ""],
    [t("withdrawals"), data.withdrawals_pending, "/admin/sync", data.withdrawals_pending ? "text-warn" : ""],
  ];

  return (
    <div className="space-y-10">
      <div className="grid grid-cols-2 gap-px border-2 border-ink bg-ink md:grid-cols-4">
        {tiles.map(([label, value, href, color]) => {
          const body = (
            <>
              <div className={`font-numeric text-5xl leading-none ${color ?? ""}`}>{value}</div>
              <div className="mt-2 text-sm text-muted">{label}</div>
            </>
          );
          return href ? (
            <Link key={label} href={href} className="bg-paper p-5 hover:bg-fog">{body}</Link>
          ) : (
            <div key={label} className="bg-paper p-5">{body}</div>
          );
        })}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="border-2 border-ink p-5">
          <h2 className="font-display font-black">{t("lastSync")}</h2>
          {data.last_sync ? (
            <p className="mt-2 text-sm">
              <Link href={`/admin/sync/${data.last_sync.id}`} className="font-semibold underline">{data.last_sync.status}</Link>{" "}
              · {fmtDateTime(data.last_sync.finished_at ?? data.last_sync.started_at)} · +{data.last_sync.versions_issued} / {data.last_sync.rows_errors} err
            </p>
          ) : <p className="mt-2 text-sm text-muted">{t("never")}</p>}
          <p className="mt-3 text-sm text-muted">{t("worker")}: {data.worker_last_seen ? fmtDateTime(data.worker_last_seen) : t("never")}</p>
        </div>
        <div className="border-2 border-ink p-5">
          <h2 className="font-display font-black">{t("issuer")}</h2>
          <dl className="mt-2 space-y-1 text-sm">
            <div><dt className="inline text-muted">Chain: </dt><dd className="inline">{data.issuer.chain_name} ({data.issuer.chain_id})</dd></div>
            <div><dt className="inline text-muted">Contract: </dt><dd className="mono inline">{data.issuer.contract_address ?? "—"}</dd></div>
            <div><dt className="inline text-muted">Issuer: </dt><dd className="mono inline">{data.issuer.issuer_addresses.map((a) => a.address).join(", ") || "—"}</dd></div>
          </dl>
        </div>
      </div>

      <section>
        <h2 className="font-display text-xl font-black">{t("recent")}</h2>
        <table className="table-basic mt-3">
          <tbody>
            {data.recent_audit.map((a) => (
              <tr key={a.id}>
                <td className="whitespace-nowrap text-muted">{fmtDateTime(a.created_at)}</td>
                <td className="font-semibold">{a.action}</td>
                <td>{a.actor}</td>
                <td className="mono text-muted">{Object.entries(a.metadata).slice(0, 3).map(([k, v]) => `${k}=${String(v)}`).join(" ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

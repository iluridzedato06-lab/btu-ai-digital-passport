"use client";

import { use, useState } from "react";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { useApi } from "@/components/admin/useApi";
import { api, ApiError, type VersionSummary } from "@/lib/api";
import { fmtDate, fmtDateTime, shortHash } from "@/lib/format";
import Stamp from "@/components/Stamp";

type Detail = {
  id: string; student_number: string; first_name: string; last_name: string; first_name_ka: string; last_name_ka: string;
  email: string; programme: string; consent: boolean; passport_id: string | null; first_issued_on?: string;
  awards: { award_id: string; skill: string; stamp_type: "FOCUSED" | "APPLIED" | "ADVANCED"; earned_through: string; date_earned: string;
    confirmed_by: string; withdrawn_at: string | null; withdraw_requested: boolean; first_version: number | null }[];
  versions: VersionSummary[];
};

export default function StudentDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const t = useTranslations("admin.students");
  const td = useTranslations("dashboard");
  const { data, reload } = useApi<Detail>(`/admin/students/${id}`, 5000);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  if (!data) return null;

  return (
    <div className="space-y-10">
      <Link href="/admin/students" className="text-sm underline">← {t("name")}</Link>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="font-display text-3xl font-black">{data.first_name} {data.last_name}</h2>
          <p className="text-muted">{data.first_name_ka} {data.last_name_ka} · {data.student_number} · {data.email} · {data.programme}</p>
          <p className="mt-2 font-display text-lg font-extrabold">{data.passport_id ?? "—"} {data.first_issued_on && <span className="font-normal text-muted">· {fmtDate(data.first_issued_on)}</span>}</p>
        </div>
        <button
          className="btn btn-dark"
          disabled={busy}
          onClick={async () => {
            if (!confirm(t("reissueConfirm"))) return;
            setBusy(true);
            setMsg(null);
            try {
              await api(`/admin/students/${id}/reissue`, { method: "POST" });
              reload();
            } catch (e) {
              setMsg((e as ApiError).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          {t("reissue")}
        </button>
      </div>
      {msg && <p className="border-l-4 border-bad bg-bad-bg p-3 text-sm">{msg}</p>}

      <section>
        <h3 className="font-display text-xl font-black">{t("awards")}</h3>
        <table className="table-basic mt-3">
          <tbody>
            {data.awards.map((a) => (
              <tr key={a.award_id} className={a.withdrawn_at ? "opacity-50" : ""}>
                <td className="w-28"><Stamp type={a.stamp_type} className="!h-10" alt="" /></td>
                <td className="font-semibold">{a.skill}<div className="text-xs font-normal text-muted">{a.award_id}</div></td>
                <td>{a.earned_through}</td>
                <td>{fmtDate(a.date_earned)}</td>
                <td className="text-muted">{a.confirmed_by}</td>
                <td>{a.first_version ? `v${a.first_version}` : "—"}
                  {a.withdrawn_at && <span className="tag ml-2 text-bad">{t("withdrawn")}</span>}
                  {a.withdraw_requested && !a.withdrawn_at && <span className="tag ml-2 text-warn">{t("withdrawRequested")}</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h3 className="font-display text-xl font-black">{t("versions")}</h3>
        <div className="overflow-x-auto">
          <table className="table-basic mt-3 min-w-[760px]">
            <thead><tr><th>{td("colVersion")}</th><th>{td("colIssued")}</th><th>{td("colCode")}</th><th>{td("colStatus")}</th><th>SHA-256</th><th /></tr></thead>
            <tbody>
              {data.versions.map((v) => (
                <tr key={v.id}>
                  <td><Link href={`/admin/versions/${v.id}`} className="font-display font-extrabold underline">v{v.version_number}</Link></td>
                  <td>{fmtDateTime(v.issued_at ?? v.created_at)}<div className="text-xs text-muted">{v.trigger_reason}</div></td>
                  <td className="font-display font-bold tracking-wider">{v.verification_code}</td>
                  <td>
                    {v.revoked_at ? <span className="tag text-bad">{td("revoked")}</span>
                      : v.status === "anchored" ? (v.is_latest_valid ? <span className="tag text-ok">{td("latest")}</span> : <span className="tag text-muted">{td("superseded")}</span>)
                      : v.status === "anchor_failed" ? <span className="tag text-bad">{td("failed")}</span>
                      : <span className="tag text-warn">{td("pending")}</span>}
                  </td>
                  <td className="mono">{shortHash(v.pdf_sha256)}</td>
                  <td className="text-right"><a href={`/api/admin/versions/${v.id}/download`} className="font-semibold underline">PDF</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

"use client";

import { use, useState } from "react";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { useApi } from "@/components/admin/useApi";
import { api, ApiError, type VersionSummary } from "@/lib/api";
import { fmtDateTime } from "@/lib/format";

type Detail = VersionSummary & {
  passport_id: string; student_id: string; holder: { first_name: string; last_name: string };
  snapshot: Record<string, unknown>; issuer_signature: string; revoked_by: string; is_latest_valid: boolean;
  revocations: { tx_hash: string; status: string; reason: string; error: string; created_at: string }[];
};

export default function VersionDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const t = useTranslations("admin.version");
  const tv = useTranslations("verify.chain");
  const { data, reload } = useApi<Detail>(`/admin/versions/${id}`);
  const [reason, setReason] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  if (!data) return null;

  async function post(path: string, json?: unknown) {
    setBusy(true);
    setMsg(null);
    try {
      await api(path, { method: "POST", json });
      reload();
    } catch (e) {
      setMsg((e as ApiError).message);
    } finally {
      setBusy(false);
    }
  }

  const a = data.anchor;
  return (
    <div className="space-y-10">
      <Link href={`/admin/students/${data.student_id}`} className="text-sm underline">← {data.holder.first_name} {data.holder.last_name}</Link>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="font-display text-3xl font-black">{data.passport_id} · {t("title", { n: data.version_number })}</h2>
          <p className="text-muted">{data.status} · {data.trigger_reason} · {fmtDateTime(data.issued_at ?? data.created_at)}</p>
          {data.verification_code && <Link href={`/verify/${data.verification_code}`} className="mt-1 inline-block font-display font-bold tracking-wider underline">{data.verification_code}</Link>}
        </div>
        <a href={`/api/admin/versions/${data.id}/download`} className="btn btn-orange">{t("download")}</a>
      </div>
      {msg && <p className="border-l-4 border-bad bg-bad-bg p-3 text-sm">{msg}</p>}

      <dl className="divide-y divide-line border-y border-line text-sm">
        {[
          ["SHA-256", data.pdf_sha256],
          [tv("tx"), a?.tx_hash],
          [tv("block"), a?.block_number],
          [tv("contract"), a?.contract],
          [tv("issuer"), a?.issuer_address],
          [t("attempts"), a?.attempts],
          [t("lastError"), a?.last_error],
          [t("signature"), data.issuer_signature],
        ].map(([k, v]) => (
          <div key={k as string} className="grid gap-1 py-3 md:grid-cols-[220px_1fr]">
            <dt className="text-muted">{k}</dt><dd className="mono">{v === null || v === undefined || v === "" ? "—" : String(v)}</dd>
          </div>
        ))}
      </dl>

      <div className="grid gap-6 md:grid-cols-2">
        {data.status !== "anchored" && (
          <div className="border-2 border-ink p-5">
            <button className="btn btn-dark" disabled={busy} onClick={() => post(`/admin/versions/${id}/reanchor`)}>{t("reanchor")}</button>
          </div>
        )}
        {data.status === "anchored" && !data.revoked_at && (
          <div className="border-2 border-bad p-5">
            <label htmlFor="reason" className="block text-sm font-semibold">{t("revokeReason")}</label>
            <input id="reason" className="field mt-2" value={reason} onChange={(e) => setReason(e.target.value)} maxLength={200} />
            <button className="btn mt-3 border-bad bg-bad text-white" disabled={busy || reason.trim().length < 5}
              onClick={() => confirm(`${t("revoke")}?`) && post(`/admin/versions/${id}/revoke`, { reason })}>
              {t("revokeConfirm")}
            </button>
          </div>
        )}
        {data.revoked_at && (
          <p className="border-l-8 border-bad bg-bad-bg p-4 text-sm">Revoked {fmtDateTime(data.revoked_at)} by {data.revoked_by}: {data.revoke_reason}</p>
        )}
      </div>

      <section>
        <h3 className="font-display text-lg font-black">{t("snapshot")}</h3>
        <pre className="mt-3 max-h-[480px] overflow-auto bg-fog p-4 text-xs">{JSON.stringify(data.snapshot, null, 2)}</pre>
      </section>
    </div>
  );
}

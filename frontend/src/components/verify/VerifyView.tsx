"use client";

import { useCallback, useEffect, useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { api, ApiError, type VerifyResult } from "@/lib/api";
import { hashesEqual } from "@/lib/hash";
import { fmtDate, fmtDateTime } from "@/lib/format";
import Stamp from "@/components/Stamp";
import StatusBanner from "./StatusBanner";
import FileDrop from "./FileDrop";

type FileState =
  | { kind: "match"; hash: string; name: string }
  | { kind: "mismatch"; hash: string; name: string; other?: VerifyResult }
  | null;

export default function VerifyView({ code }: { code: string }) {
  const t = useTranslations("verify");
  const ts = useTranslations("stamps");
  const locale = useLocale();
  const [data, setData] = useState<VerifyResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<FileState>(null);

  useEffect(() => {
    let alive = true;
    setData(null);
    setError(null);
    api<VerifyResult>(`/public/verify/${encodeURIComponent(code)}`)
      .then((d) => alive && setData(d))
      .catch((e: ApiError) => alive && setError(e.status === 429 ? t("rateLimited") : e.message));
    return () => {
      alive = false;
    };
  }, [code, t]);

  const onHash = useCallback(
    async (hash: string, name: string) => {
      if (data?.pdf_sha256 && hashesEqual(hash, data.pdf_sha256)) {
        setFile({ kind: "match", hash, name });
        return;
      }
      let other: VerifyResult | undefined;
      try {
        const r = await api<VerifyResult>(`/public/verify/by-hash/${hash}`);
        if (r.status !== "not_found") other = r;
      } catch {
        /* ignore */
      }
      setFile({ kind: "mismatch", hash, name, other });
    },
    [data],
  );

  if (error) return <p role="alert" className="border-l-8 border-bad bg-bad-bg p-5 text-bad">{error}</p>;
  if (!data)
    return (
      <p className="flex items-center gap-3 p-5 text-muted" aria-live="polite">
        <span className="inline-block h-4 w-4 animate-spin border-2 border-ink border-t-transparent" aria-hidden />
        {t("checking")}
      </p>
    );

  const st = data.status;
  const banner = (
    <StatusBanner
      status={st}
      title={t(`status.${st}.title`)}
      body={t(`status.${st}.body`, { latest: data.latest_valid_version ?? data.latest_version ?? "" })}
    />
  );
  if (st === "not_found") {
    return (
      <div className="space-y-6">
        {banner}
        <Link href="/verify" className="btn btn-ghost">{t("again")}</Link>
      </div>
    );
  }

  const checks = data.checks || {};
  return (
    <div className="space-y-10">
      {banner}

      {data.revocation && (
        <p className="border-2 border-bad p-4 text-sm">
          <b>{t("revokedReason")}:</b> {data.revocation.reason}
        </p>
      )}

      {/* Holder card, styled like the passport page */}
      <div className="frame">
        <div className="sheet grid gap-6 p-6 md:grid-cols-[1.3fr_1fr] md:p-8">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-muted">{t("holder")}</p>
            <p className="mt-1 font-display text-3xl font-black uppercase leading-tight md:text-4xl">
              {data.holder?.first_name} <span className="font-light">{data.holder?.last_name}</span>
            </p>
          </div>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-4 text-sm">
            <div>
              <dt className="text-muted">{t("passportId")}</dt>
              <dd className="font-display font-extrabold">{data.passport_id}</dd>
            </div>
            <div>
              <dt className="text-muted">{t("version")}</dt>
              <dd className="font-display font-extrabold">{t("versionOf", { n: data.version ?? "", m: data.latest_version ?? "" })}</dd>
            </div>
            <div>
              <dt className="text-muted">{t("firstIssued")}</dt>
              <dd className="font-semibold">{fmtDate(data.first_issued_on, locale)}</dd>
            </div>
            <div>
              <dt className="text-muted">{t("versionIssued")}</dt>
              <dd className="font-semibold">{data.issued_at ? fmtDateTime(data.issued_at) : fmtDate(data.version_issued_on)}</dd>
            </div>
            <div className="col-span-2">
              <dt className="text-muted">{t("code")}</dt>
              <dd className="font-display font-extrabold tracking-[0.15em]">{data.verification_code}</dd>
            </div>
          </dl>
        </div>
      </div>

      {/* Authenticity */}
      {data.checks && Object.keys(checks).length > 0 && (
        <section>
          <h2 className="font-display text-2xl font-black">{t("authenticity")}</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            {[
              ["documentAuthentic", data.document_authentic, ["record_on_chain", "document_hash_matches", "code_hash_matches", "not_revoked_on_chain"]],
              ["issuerAuthentic", data.issuer_authentic, ["issuer_authorised_by_contract", "issuer_published_by_btu", "chain_consistent"]],
            ].map(([label, ok, keys]) => (
              <div key={label as string} className={`border-2 p-5 ${ok ? "border-ok" : "border-bad"}`}>
                <div className="flex items-center justify-between gap-3">
                  <h3 className="font-display text-lg font-extrabold">{t(label as string)}</h3>
                  <span className={`tag ${ok ? "text-ok" : "text-bad"}`}>{ok ? t("passed") : t("failed")}</span>
                </div>
                <ul className="mt-3 space-y-1.5 text-sm">
                  {(keys as string[]).map((k) => (
                    <li key={k} className="flex gap-2">
                      <span aria-hidden className={checks[k] ? "text-ok" : "text-bad"}>{checks[k] ? "✓" : "✕"}</span>
                      <span>{t(`checks.${k}`)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* File check */}
      <section className="grid gap-6 md:grid-cols-2">
        <div>
          <h2 className="font-display text-2xl font-black">{t("file.title")}</h2>
          <p className="mt-2 text-muted">{t("file.body")}</p>
          {file && (
            <div className={`mt-4 border-l-8 p-4 ${file.kind === "match" ? "border-ok bg-ok-bg" : "border-bad bg-bad-bg"}`} role="status">
              <p className="font-semibold">
                {file.kind === "match"
                  ? t("file.match")
                  : file.other
                    ? t("file.otherVersion", { version: `${file.other.passport_id} v${file.other.version}` })
                    : t("file.mismatch")}
              </p>
              <p className="mt-2 text-xs text-muted">{file.name}</p>
              <p className="mt-1 text-xs"><span className="text-muted">{t("file.yourHash")}:</span> <span className="mono">{file.hash}</span></p>
            </div>
          )}
        </div>
        <FileDrop onHash={onHash} />
      </section>

      {/* Stamps */}
      <section>
        <h2 className="font-display text-2xl font-black">{t("stamps")}</h2>
        {data.stamps && data.stamps.length > 0 ? (
          <ul className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.stamps.map((s, i) => (
              <li key={i} className="flex gap-4 border border-line p-4">
                <div className="flex w-24 shrink-0 items-center justify-center">
                  <Stamp type={s.stamp_type} className="!h-14" alt={ts(`${s.stamp_type}.title`)} />
                </div>
                <div className="min-w-0">
                  <p className="font-display font-extrabold leading-tight">
                    {locale === "ka" && s.skill_name_ka ? s.skill_name_ka : s.skill_name}
                  </p>
                  <p className="text-xs uppercase tracking-wide text-muted">{ts(`${s.stamp_type}.title`)}</p>
                  <p className="mt-2 text-sm">{s.earned_through}</p>
                  <p className="text-sm text-muted">{fmtDate(s.date_earned)}</p>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-muted">{t("noStamps")}</p>
        )}
      </section>

      {/* Chain record */}
      {data.chain && (
        <section>
          <h2 className="font-display text-2xl font-black">{t("chain.title")}</h2>
          <dl className="mt-4 divide-y divide-line border-y border-line text-sm">
            {[
              [t("chain.network"), `${data.chain.chain_name} (${data.chain.chain_id})`],
              [t("chain.contract"), data.chain.contract],
              [t("chain.tx"), data.chain.tx_hash],
              [t("chain.block"), data.chain.block_number],
              [t("chain.issuer"), data.chain.issuer_address],
              [t("chain.hash"), data.pdf_sha256],
            ].map(([k, v]) => (
              <div key={k as string} className="grid gap-1 py-3 md:grid-cols-[220px_1fr]">
                <dt className="text-muted">{k}</dt>
                <dd className="mono">{v ?? "—"}</dd>
              </div>
            ))}
          </dl>
          {data.chain.explorer_url && (
            <a href={data.chain.explorer_url} className="mt-3 inline-block font-semibold underline underline-offset-4" rel="noopener" target="_blank">
              {t("chain.explorer")}
            </a>
          )}
        </section>
      )}

      <Link href="/verify" className="btn btn-ghost">{t("again")}</Link>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { Link, useRouter } from "@/i18n/navigation";
import { api, type Me, type VersionSummary } from "@/lib/api";
import { fmtDate, shortHash } from "@/lib/format";
import Stamp from "@/components/Stamp";
import QrCode from "@/components/QrCode";

function VersionStatus({ v }: { v: VersionSummary }) {
  const t = useTranslations("dashboard");
  if (v.revoked_at) return <span className="tag text-bad">{t("revoked")}</span>;
  if (v.status === "anchor_failed") return <span className="tag text-bad">{t("failed")}</span>;
  if (v.status !== "anchored") return <span className="tag text-warn">{t("pending")}</span>;
  if (v.is_latest_valid) return <span className="tag text-ok">{t("latest")}</span>;
  return <span className="tag text-muted">{t("superseded")}</span>;
}

export default function Dashboard() {
  const t = useTranslations("dashboard");
  const tc = useTranslations("common");
  const ts = useTranslations("stamps");
  const tv = useTranslations("verify");
  const locale = useLocale();
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    const load = () =>
      api<Me>("/me")
        .then((m) => {
          if (!m.authenticated) {
            router.replace("/login");
            return;
          }
          setMe(m);
          // Keep polling while a version is waiting for the chain.
          if (m.passport?.versions.some((v) => v.status !== "anchored" && v.status !== "anchor_failed") || (m.student?.pending_stamps.length ?? 0) > 0) {
            timer = setTimeout(load, 5000);
          }
        })
        .catch(() => router.replace("/login"));
    load();
    return () => clearTimeout(timer);
  }, [router]);

  if (!me) return <p className="mx-auto max-w-7xl px-4 py-16 text-muted sm:px-6">{tc("loading")}</p>;

  if (!me.student) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
        <h1 className="font-display text-3xl font-black">{t("title")}</h1>
        <p className="mt-4 text-muted">{t("notStudent")}</p>
        {(me.role === "admin" || me.role === "staff") && <Link href="/admin" className="btn btn-dark mt-6">{tc("nav.admin")}</Link>}
      </div>
    );
  }

  const s = me.student;
  const p = me.passport;
  const name = locale === "ka" && s.first_name_ka ? s.first_name_ka : s.first_name;
  const latest = p?.versions.find((v) => v.is_latest_valid) ?? p?.versions[0];
  const slots = p ? [...p.stamps, ...Array(Math.max(0, 10 - p.stamps.length)).fill(null)].slice(0, Math.max(10, p.stamps.length)) : [];

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6">
      <p className="text-sm font-semibold uppercase tracking-widest text-magenta">{t("hello", { name })}</p>
      <h1 className="mt-2 font-display text-4xl font-black tracking-tight">{t("title")}</h1>

      {!p ? (
        <div className="mt-10 border-2 border-ink p-8">
          <h2 className="font-display text-2xl font-black">{t("noPassport")}</h2>
          <p className="mt-2 text-muted">{t("noPassportBody")}</p>
        </div>
      ) : (
        <>
          {/* Cover-like summary */}
          <div className="frame mt-8 !bg-slate">
            <div className="sheet grid gap-8 p-6 md:grid-cols-[1fr_auto] md:p-10">
              <div>
                <div className="font-display leading-[0.95]">
                  <div className="text-3xl font-black md:text-5xl">AI SKILLS</div>
                  <div className="text-3xl font-light md:text-5xl">DIGITAL PASSPORT</div>
                </div>
                <div className="rule-top my-6" />
                <dl className="grid gap-x-10 gap-y-3 sm:grid-cols-2">
                  <div><dt className="text-xs font-bold uppercase tracking-widest text-muted">{tv("holder")}</dt>
                    <dd className="font-display text-xl font-extrabold uppercase">{p.holder.first_name} {p.holder.last_name}</dd></div>
                  <div><dt className="text-xs font-bold uppercase tracking-widest text-muted">{t("passportId")}</dt>
                    <dd className="font-display text-xl font-extrabold">{p.passport_id}</dd></div>
                  <div><dt className="text-xs font-bold uppercase tracking-widest text-muted">{t("firstIssued")}</dt>
                    <dd className="font-semibold">{fmtDate(p.first_issued_on)}</dd></div>
                  <div><dt className="text-xs font-bold uppercase tracking-widest text-muted">{t("latestVersion")}</dt>
                    <dd className="font-semibold">v{p.latest_valid_version ?? "—"} · {t("stamps", { count: p.stamps.length })}</dd></div>
                </dl>
                {latest && latest.status === "anchored" && (
                  <a href={`/api/me/passport/versions/${latest.version_number}/download`} className="btn btn-orange mt-8">
                    {tc("download")} · v{latest.version_number}
                  </a>
                )}
              </div>
              {latest?.verify_url && (
                <div className="flex flex-col items-start gap-3 md:items-end">
                  <QrCode value={latest.verify_url} />
                  <span className="font-display text-lg font-extrabold tracking-[0.15em]">{latest.verification_code}</span>
                </div>
              )}
            </div>
          </div>

          {/* Pending */}
          {s.pending_stamps.length > 0 && (
            <div className="mt-8 border-l-8 border-orange bg-warn-bg p-5">
              <p className="font-display font-extrabold">{t("pendingTitle")}</p>
              <p className="text-sm">{t("pendingBody")}</p>
              <ul className="mt-2 list-inside list-disc text-sm">
                {s.pending_stamps.map((x) => <li key={x.skill_name}>{x.skill_name}</li>)}
              </ul>
            </div>
          )}

          {/* Stamp grid like page 3 of the passport */}
          <section className="mt-14">
            <h2 className="font-display text-2xl font-black uppercase">{t("stampsTitle")}</h2>
            <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
              {slots.map((st, i) => (
                <div key={i} className="flex min-h-56 flex-col rounded-lg border border-line">
                  <div className="border-b border-line py-1 text-center text-xs text-muted">{st ? fmtDate(st.date_earned) : " "}</div>
                  {st && (
                    <div className="flex flex-1 flex-col items-center px-3 pb-4 pt-4 text-center">
                      <div className="flex h-24 items-center"><Stamp type={st.stamp_type} alt="" /></div>
                      <p className="mt-2 font-display text-sm font-extrabold uppercase leading-tight">
                        {locale === "ka" && st.skill_name_ka ? st.skill_name_ka : st.skill_name}
                      </p>
                      <p className="mt-1 text-xs uppercase text-muted">{ts(`${st.stamp_type}.title`)}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* Share */}
          {latest?.verify_url && (
            <section className="mt-14 grid gap-6 border-2 border-ink p-6 md:grid-cols-[1fr_auto] md:items-center">
              <div>
                <h2 className="font-display text-xl font-black">{t("share")}</h2>
                <p className="mt-2 text-muted">{t("shareBody")}</p>
                <p className="mono mt-3">{latest.verify_url}</p>
              </div>
              <button
                type="button"
                className="btn btn-dark"
                onClick={() => {
                  navigator.clipboard?.writeText(latest.verify_url!).then(() => {
                    setCopied(true);
                    setTimeout(() => setCopied(false), 2000);
                  });
                }}
              >
                {copied ? tc("copied") : t("copyLink")}
              </button>
            </section>
          )}

          {/* Versions */}
          <section className="mt-14">
            <h2 className="font-display text-2xl font-black">{t("versionsTitle")}</h2>
            <p className="mt-1 text-muted">{t("versionsLead")}</p>
            <div className="mt-5 overflow-x-auto">
              <table className="table-basic min-w-[720px]">
                <thead>
                  <tr>
                    <th>{t("colVersion")}</th>
                    <th>{t("colIssued")}</th>
                    <th>{t("colCode")}</th>
                    <th>{t("colStatus")}</th>
                    <th>{t("fingerprint")}</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {p.versions.map((v) => (
                    <tr key={v.id}>
                      <td className="font-display font-extrabold">v{v.version_number}</td>
                      <td>{fmtDate(v.issued_at ?? v.created_at)}</td>
                      <td>
                        {v.verification_code && (
                          <Link href={`/verify/${v.verification_code}`} className="font-display font-bold tracking-wider underline underline-offset-4">
                            {v.verification_code}
                          </Link>
                        )}
                      </td>
                      <td><VersionStatus v={v} /></td>
                      <td className="mono" title={v.pdf_sha256}>{shortHash(v.pdf_sha256)}</td>
                      <td className="text-right">
                        <a href={`/api/me/passport/versions/${v.version_number}/download`} className="font-semibold underline underline-offset-4">
                          PDF
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

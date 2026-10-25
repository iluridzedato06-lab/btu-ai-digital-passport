import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import CodeEntry from "@/components/CodeEntry";
import Stamp from "@/components/Stamp";
import { serverGet } from "@/lib/server-api";

type Stats = { passports: number; versions_anchored: number; stamps: number; skills_in_catalog: number };

export const dynamic = "force-dynamic";

export default async function Home({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("home");
  const ts = await getTranslations("stamps");
  const stats = await serverGet<Stats>("/public/stats");

  const steps = [1, 2, 3, 4] as const;
  const types = ["FOCUSED", "APPLIED", "ADVANCED"] as const;

  return (
    <>
      {/* Hero: typographic, modelled on the passport cover */}
      <section className="border-b-2 border-ink">
        <div className="mx-auto grid max-w-7xl items-center gap-12 px-4 py-14 sm:px-6 lg:grid-cols-[1.1fr_1fr] lg:py-20">
          <div>
            <p className="mb-6 flex items-center gap-3 text-xs font-bold uppercase tracking-[0.2em] text-muted">
              <span className="inline-block h-[3px] w-10 bg-orange" aria-hidden />
              {t("eyebrow")}
            </p>
            <h1 className="font-display leading-[0.92] tracking-tight">
              <span className="caps-latin block text-5xl font-black uppercase sm:text-6xl lg:text-7xl">{t("title1")}</span>
              <span className="caps-latin block text-[2.6rem] font-light uppercase sm:text-6xl lg:text-[4.1rem]">{t("title2")}</span>
            </h1>
            <p className="mt-7 max-w-xl text-lg leading-relaxed text-muted">{t("lead")}</p>
            <div className="mt-9 max-w-xl">
              <CodeEntry label={t("codeLabel")} />
            </div>
            <p className="mt-6 text-sm">
              {t("orStudent")}{" "}
              <Link href="/login" className="font-semibold underline decoration-magenta decoration-2 underline-offset-4 hover:text-magenta">
                {t("studentLink")}
              </Link>
            </p>
          </div>
          <div className="frame !bg-slate">
            <div className="sheet relative overflow-hidden px-6 pb-6 pt-8">
              <div className="flex items-start justify-between">
                <div className="font-display leading-none">
                  <div className="text-2xl font-black">AI SKILLS</div>
                  <div className="text-2xl font-light">DIGITAL PASSPORT</div>
                </div>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src="/stamps/asterisk.svg" alt="" className="h-8 w-8" />
              </div>
              <div className="rule-top mt-5" />
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/stamps/cover-stickers.svg" alt="" className="mx-auto mt-4 w-full max-w-md" />
              <div className="mt-2 flex items-end justify-between">
                <div className="bg-orange px-2.5 py-1.5 font-display text-sm leading-tight">
                  <div className="font-light">AI SKILLS</div>
                  <div className="font-extrabold">DIGITAL PASSPORT</div>
                </div>
                <span className="text-xs tracking-wide">PASSPORT ID: <b>BTU-AI-2026-00001</b></span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6">
        <h2 className="font-display text-3xl font-black tracking-tight md:text-4xl">{t("how.title")}</h2>
        <ol className="mt-10 grid gap-8 md:grid-cols-4">
          {steps.map((n) => (
            <li key={n} className="border-t-4 border-ink pt-5">
              <span className="font-numeric text-5xl leading-none text-orange">0{n}</span>
              <h3 className="mt-3 font-display text-lg font-extrabold">{t(`how.s${n}t`)}</h3>
              <p className="mt-2 text-[15px] leading-relaxed text-muted">{t(`how.s${n}d`)}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* Stamp types */}
      <section className="bg-fog">
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6">
          <div className="max-w-2xl">
            <h2 className="font-display text-3xl font-black tracking-tight md:text-4xl">{t("stampsTitle")}</h2>
            <p className="mt-3 text-lg text-muted">{t("stampsLead")}</p>
          </div>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {types.map((type) => (
              <article key={type} className="flex flex-col border-2 border-ink bg-paper p-6">
                <div className="flex h-24 items-center">
                  <Stamp type={type} alt={ts(`${type}.title`)} />
                </div>
                <h3 className="mt-5 font-display text-xl font-extrabold">{ts(`${type}.title`)}</h3>
                <p className="text-sm font-medium uppercase tracking-wide text-muted">{ts(`${type}.subtitle`)}</p>
                <p className="mt-4 text-[15px] leading-relaxed">{ts(`${type}.body`)}</p>
                <p className="mt-auto pt-4 text-sm">
                  <b>{ts("representsLabel")}:</b> {ts(`${type}.represents`)}
                </p>
              </article>
            ))}
          </div>
          <p className="mt-6 max-w-4xl border-l-4 border-orange bg-paper p-4 text-sm leading-relaxed">{ts("important")}</p>
        </div>
      </section>

      {/* Trust */}
      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6">
        <h2 className="font-display text-3xl font-black tracking-tight md:text-4xl">{t("trust.title")}</h2>
        <div className="mt-10 grid gap-10 md:grid-cols-3">
          {[1, 2, 3].map((n) => (
            <div key={n}>
              <div className="h-1 w-14 bg-magenta" aria-hidden />
              <h3 className="mt-4 font-display text-lg font-extrabold">{t(`trust.t${n}`)}</h3>
              <p className="mt-2 leading-relaxed text-muted">{t(`trust.d${n}`)}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Numbers, BTU-style */}
      {stats && (
        <section className="border-y-2 border-ink">
          <div className="mx-auto grid max-w-7xl grid-cols-2 px-4 sm:px-6 md:grid-cols-4">
            {[
              [stats.passports, t("numbers.passports")],
              [stats.stamps, t("numbers.stamps")],
              [stats.versions_anchored, t("numbers.versions")],
              [stats.skills_in_catalog, t("numbers.skills")],
            ].map(([value, label], i) => (
              <div key={i} className={`py-8 ${i > 0 ? "md:border-l md:border-line md:pl-8" : ""}`}>
                <div className="font-numeric text-6xl leading-none">{value}</div>
                <div className="mt-2 text-sm font-medium text-muted">{label}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Employers */}
      <section className="mx-auto max-w-7xl px-4 pt-20 sm:px-6">
        <div className="grid items-center gap-8 bg-ink p-8 text-white md:grid-cols-[1fr_auto] md:p-12">
          <div>
            <h2 className="font-display text-2xl font-black md:text-3xl">{t("employers.title")}</h2>
            <p className="mt-3 max-w-2xl leading-relaxed text-white/80">{t("employers.body")}</p>
          </div>
          <Link href="/verify" className="btn btn-orange">
            {t("employers.cta")}
          </Link>
        </div>
      </section>
    </>
  );
}

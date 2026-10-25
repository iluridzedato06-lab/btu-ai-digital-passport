import { getTranslations, setRequestLocale } from "next-intl/server";
import PageTitle from "@/components/PageTitle";
import Stamp from "@/components/Stamp";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "about" });
  return { title: t("title") };
}

export default async function AboutPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("about");
  const ts = await getTranslations("stamps");
  const grows = t.raw("grows") as string[];
  const faq = t.raw("faq") as { q: string; a: string }[];
  const types = ["FOCUSED", "APPLIED", "ADVANCED"] as const;

  return (
    <>
      <PageTitle title={t("title")} lead={t("lead")} />
      <div className="mx-auto grid max-w-7xl gap-14 px-4 py-14 sm:px-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-6 text-lg leading-relaxed">
          <p>{t("p1")}</p>
          <p>{t("p2")}</p>
          <p>{t("p3")}</p>
          <div className="flex gap-3 pt-2" aria-hidden>
            {Array.from({ length: 9 }).map((_, i) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img key={i} src="/stamps/asterisk.svg" alt="" className="h-5 w-5" />
            ))}
          </div>
        </div>
        <aside className="h-fit border-2 border-ink p-6">
          <h2 className="font-display text-lg font-black uppercase">{t("growsTitle")}</h2>
          <ol className="mt-5 space-y-4">
            {grows.map((g, i) => (
              <li key={g} className="flex items-center gap-4">
                <span className="font-numeric text-3xl leading-none text-orange">{i + 1}</span>
                <span className="font-display font-bold">{g}</span>
              </li>
            ))}
          </ol>
        </aside>
      </div>

      <section className="bg-fog">
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
          <div className="grid gap-6 md:grid-cols-3">
            {types.map((type) => (
              <article key={type} className="border-2 border-ink bg-paper p-6">
                <div className="flex h-24 items-center"><Stamp type={type} alt="" /></div>
                <h3 className="mt-4 font-display text-xl font-extrabold">{ts(`${type}.title`)}</h3>
                <p className="text-sm font-medium uppercase tracking-wide text-muted">{ts(`${type}.subtitle`)}</p>
                <p className="mt-3 text-[15px] leading-relaxed">{ts(`${type}.body`)}</p>
                <p className="mt-3 text-sm"><b>{ts("representsLabel")}:</b> {ts(`${type}.represents`)}</p>
              </article>
            ))}
          </div>
          <p className="mt-6 border-l-4 border-orange bg-paper p-4 text-sm leading-relaxed">{ts("important")}</p>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
        <h2 className="font-display text-3xl font-black">{t("versionsTitle")}</h2>
        <p className="mt-4 max-w-3xl text-lg leading-relaxed text-muted">{t("versionsBody")}</p>
      </section>

      <section className="mx-auto max-w-7xl px-4 sm:px-6">
        <h2 className="font-display text-3xl font-black">{t("faqTitle")}</h2>
        <div className="mt-6 divide-y divide-line border-y-2 border-ink">
          {faq.map((f) => (
            <details key={f.q} className="group py-5">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-display text-lg font-bold">
                {f.q}
                <span className="text-2xl leading-none text-orange transition-transform group-open:rotate-45" aria-hidden>+</span>
              </summary>
              <p className="mt-3 max-w-3xl leading-relaxed text-muted">{f.a}</p>
            </details>
          ))}
        </div>
      </section>
    </>
  );
}

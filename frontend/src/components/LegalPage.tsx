import { getTranslations } from "next-intl/server";
import PageTitle from "./PageTitle";

export const LEGAL_UPDATED = "2026-10-24";

export default async function LegalPage({ kind }: { kind: "terms" | "privacy" }) {
  const t = await getTranslations("legal");
  const sections = t.raw(`${kind}.sections`) as { h: string; p: string }[];
  return (
    <>
      <PageTitle title={t(`${kind}.title`)} lead={t("updated", { date: "24.10.2026" })} />
      <article className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
        {sections.map((s) => (
          <section key={s.h} className="mb-9">
            <h2 className="font-display text-xl font-extrabold">{s.h}</h2>
            <p className="mt-2 leading-relaxed text-ink/85">{s.p}</p>
          </section>
        ))}
      </article>
    </>
  );
}

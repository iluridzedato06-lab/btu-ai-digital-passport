import { getTranslations, setRequestLocale } from "next-intl/server";
import CodeEntry from "@/components/CodeEntry";
import FileLookup from "@/components/verify/FileLookup";
import PageTitle from "@/components/PageTitle";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "verify" });
  return { title: t("title") };
}

export default async function VerifyPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("verify");
  return (
    <>
      <PageTitle title={t("title")} lead={t("lead")} />
      <div className="mx-auto grid max-w-7xl gap-14 px-4 py-12 sm:px-6 lg:grid-cols-[1.2fr_1fr]">
        <div className="space-y-12">
          <CodeEntry />
          <div>
            <h2 className="font-display text-xl font-black">{t("byFile.title")}</h2>
            <p className="mb-4 mt-1 text-muted">{t("byFile.body")}</p>
            <FileLookup />
          </div>
        </div>
        <aside className="h-fit border-2 border-ink p-6">
          <h2 className="font-display text-lg font-black">{t("howTitle")}</h2>
          <ol className="mt-4 space-y-4">
            {[t("how1"), t("how2"), t("how3")].map((s, i) => (
              <li key={i} className="flex gap-4">
                <span className="font-numeric text-3xl leading-none text-orange">{i + 1}</span>
                <span className="text-[15px] leading-relaxed">{s}</span>
              </li>
            ))}
          </ol>
          <p className="mt-6 border-t border-line pt-4 text-sm text-muted">{t("file.body")}</p>
        </aside>
      </div>
    </>
  );
}

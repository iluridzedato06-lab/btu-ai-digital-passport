import { getTranslations, setRequestLocale } from "next-intl/server";
import VerifyView from "@/components/verify/VerifyView";
import PageTitle from "@/components/PageTitle";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "verify" });
  return { title: t("title"), robots: { index: false, follow: false } };
}

export default async function VerifyCodePage({ params }: { params: Promise<{ locale: string; code: string }> }) {
  const { locale, code } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("verify");
  const shown = decodeURIComponent(code).toUpperCase().slice(0, 20);
  return (
    <>
      <PageTitle title={t("title")} eyebrow={`${t("code")}: ${shown}`} />
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6">
        <VerifyView code={shown} />
      </div>
    </>
  );
}

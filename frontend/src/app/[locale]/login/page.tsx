import { getTranslations, setRequestLocale } from "next-intl/server";
import LoginForm from "@/components/auth/LoginForm";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "auth" });
  return { title: t("title"), robots: { index: false } };
}

export default async function LoginPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("auth");
  return (
    <div className="mx-auto grid max-w-7xl gap-12 px-4 py-16 sm:px-6 lg:grid-cols-2">
      <div>
        <h1 className="font-display text-4xl font-black tracking-tight md:text-5xl">{t("title")}</h1>
        <p className="mt-4 max-w-lg text-lg text-muted">{t("lead")}</p>
        <div className="mt-10 max-w-lg">
          <LoginForm devHint={process.env.NODE_ENV !== "production" || process.env.SHOW_DEV_HINTS === "1"} />
        </div>
      </div>
      <div className="frame hidden !bg-slate lg:block">
        <div className="sheet flex h-full flex-col justify-between p-8">
          <div className="font-display leading-none">
            <div className="text-4xl font-black">AI SKILLS</div>
            <div className="text-4xl font-light">DIGITAL PASSPORT</div>
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/stamps/cover-stickers.svg" alt="" className="mx-auto w-4/5" />
          <p className="text-sm text-muted">{t("noPassword")}</p>
        </div>
      </div>
    </div>
  );
}

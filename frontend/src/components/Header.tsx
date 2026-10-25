import { getLocale, getTranslations } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import LocaleSwitcher from "./LocaleSwitcher";
import AuthNav from "./AuthNav";

export default async function Header() {
  const t = await getTranslations("common");
  const locale = await getLocale();
  return (
    <header className="border-b-2 border-ink bg-paper">
      <div className="bg-night text-[13px] text-white/80">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-1.5 sm:px-6">
          <span className="truncate">{t("university")}</span>
          <div className="flex items-center gap-4">
            <a href="https://btu.edu.ge" className="hover:text-white" rel="noopener">
              {t("btuSite")}
            </a>
            <LocaleSwitcher current={locale} label={t("switchTo")} />
          </div>
        </div>
      </div>
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-8 gap-y-3 px-4 py-3 sm:px-6">
        <Link href="/" className="flex items-center gap-3" aria-label={t("siteName")}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/btu-logo.svg" alt="BTU" width={44} height={44} className="h-11 w-11" />
          <span className="font-display leading-none">
            <span className="block text-[15px] font-black tracking-tight">AI SKILLS</span>
            <span className="block text-[15px] font-light tracking-tight">DIGITAL PASSPORT</span>
          </span>
        </Link>
        <nav className="flex flex-1 flex-wrap items-center gap-x-6 gap-y-2 text-[15px] font-medium" aria-label="Main">
          <Link href="/verify" className="hover:text-magenta">{t("nav.verify")}</Link>
          <Link href="/about" className="hover:text-magenta">{t("nav.about")}</Link>
          <Link href="/issuer" className="hover:text-magenta">{t("nav.issuer")}</Link>
          <span className="flex-1" />
          <AuthNav />
        </nav>
      </div>
    </header>
  );
}

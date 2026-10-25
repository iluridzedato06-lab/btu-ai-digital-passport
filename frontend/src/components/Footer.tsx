import { getTranslations } from "next-intl/server";
import { Link } from "@/i18n/navigation";

export default async function Footer() {
  const t = await getTranslations("common");
  const year = new Date().getFullYear();
  return (
    <footer className="mt-24 bg-night text-white/75">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 md:grid-cols-4">
        <div className="md:col-span-2">
          <div className="flex items-center gap-3">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/btu-logo.svg" alt="" width={40} height={40} className="h-10 w-10" />
            <span className="font-display text-sm font-extrabold uppercase tracking-wide text-white">{t("university")}</span>
          </div>
          <p className="mt-5 max-w-md text-sm leading-relaxed">{t("footer.note")}</p>
          <p className="mt-5 text-sm">
            {t("footer.address")}
            <br />
            <a href="tel:+995322195015" className="hover:text-white">{t("footer.phone")}</a>
          </p>
        </div>
        <div>
          <h2 className="mb-3 text-xs font-bold uppercase tracking-widest text-orange">{t("footer.passport")}</h2>
          <ul className="space-y-2 text-sm">
            <li><Link href="/verify" className="hover:text-white">{t("footer.verify")}</Link></li>
            <li><Link href="/about" className="hover:text-white">{t("footer.about")}</Link></li>
            <li><Link href="/issuer" className="hover:text-white">{t("footer.issuer")}</Link></li>
          </ul>
        </div>
        <div>
          <h2 className="mb-3 text-xs font-bold uppercase tracking-widest text-orange">{t("footer.legal")}</h2>
          <ul className="space-y-2 text-sm">
            <li><Link href="/terms" className="hover:text-white">{t("footer.terms")}</Link></li>
            <li><Link href="/privacy" className="hover:text-white">{t("footer.privacy")}</Link></li>
            <li><a href="https://btu.edu.ge" className="hover:text-white" rel="noopener">btu.edu.ge</a></li>
          </ul>
        </div>
      </div>
      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 text-xs sm:px-6">
          <span className="font-display font-extrabold uppercase tracking-wider text-white">Business and Technology University</span>
          <span>{t("footer.rights", { year })}</span>
        </div>
      </div>
    </footer>
  );
}

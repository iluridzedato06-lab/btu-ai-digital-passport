import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";

export default function NotFound() {
  const t = useTranslations("common");
  return (
    <div className="mx-auto max-w-3xl px-4 py-24 sm:px-6">
      <p className="font-numeric text-8xl leading-none text-orange">404</p>
      <h1 className="mt-4 font-display text-3xl font-black">{t("notFound")}</h1>
      <p className="mt-2 text-muted">{t("notFoundBody")}</p>
      <Link href="/" className="btn btn-dark mt-8">{t("goHome")}</Link>
    </div>
  );
}

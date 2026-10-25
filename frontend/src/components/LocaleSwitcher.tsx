"use client";

import { useParams } from "next/navigation";
import { usePathname, useRouter } from "@/i18n/navigation";

export default function LocaleSwitcher({ current, label }: { current: string; label: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useParams();
  const next = current === "ka" ? "en" : "ka";
  return (
    <button
      type="button"
      lang={next}
      className="font-semibold text-white hover:text-orange"
      onClick={() =>
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        router.replace({ pathname, params } as any, { locale: next })
      }
    >
      {label}
    </button>
  );
}

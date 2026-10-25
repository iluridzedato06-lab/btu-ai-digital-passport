import { defineRouting } from "next-intl/routing";

export const routing = defineRouting({
  locales: ["ka", "en"],
  defaultLocale: "ka",
  localePrefix: "always",
});

export type Locale = (typeof routing.locales)[number];

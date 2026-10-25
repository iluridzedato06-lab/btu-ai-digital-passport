"use client";

import { useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { api, ApiError } from "@/lib/api";

export default function LoginForm({ devHint }: { devHint: boolean }) {
  const t = useTranslations("auth");
  const locale = useLocale();
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "sent">("idle");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const value = email.trim().toLowerCase();
    if (!value.endsWith("@btu.edu.ge")) {
      setError(t("domainError"));
      return;
    }
    setError(null);
    setState("sending");
    try {
      await api("/auth/magic-link/request", { json: { email: value, locale } });
      setState("sent");
    } catch (err) {
      const e2 = err as ApiError;
      setError(e2.status === 429 ? t("rateLimited") : e2.code === "domain_not_allowed" ? t("domainError") : e2.message);
      setState("idle");
    }
  }

  if (state === "sent") {
    return (
      <div className="border-l-8 border-ok bg-ok-bg p-6" role="status">
        <p className="font-display text-xl font-extrabold">{t("sentTitle")}</p>
        <p className="mt-2">{t("sentBody", { email: email.trim().toLowerCase() })}</p>
        {devHint && <p className="mt-4 text-sm text-muted">{t("devHint")}</p>}
      </div>
    );
  }

  return (
    <form onSubmit={submit} noValidate className="space-y-4">
      <div>
        <label htmlFor="email" className="mb-2 block text-sm font-semibold">{t("email")}</label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          required
          placeholder={t("emailPlaceholder")}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="field text-lg"
          aria-invalid={!!error}
        />
      </div>
      {error && <p role="alert" className="text-sm font-medium text-bad">{error}</p>}
      <button type="submit" disabled={state === "sending"} className="btn btn-dark w-full sm:w-auto">
        {state === "sending" ? t("sending") : t("submit")}
      </button>
      <p className="text-sm text-muted">{t("noPassword")}</p>
    </form>
  );
}

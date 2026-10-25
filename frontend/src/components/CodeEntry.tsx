"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";
import { formatPartial, normalizeCode, formatCode } from "@/lib/code-format";

export default function CodeEntry({ initial = "", compact = false, label }: { initial?: string; compact?: boolean; label?: string }) {
  const t = useTranslations("verify");
  const router = useRouter();
  const [value, setValue] = useState(formatPartial(initial));
  const [error, setError] = useState<string | null>(null);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const code = normalizeCode(value);
    if (!code) {
      setError(t("invalidFormat"));
      return;
    }
    setError(null);
    router.push(`/verify/${formatCode(code)}`);
  }

  return (
    <form onSubmit={submit} noValidate className="w-full">
      <label htmlFor="code" className="mb-2 block text-sm font-semibold">
        {label ?? t("codeLabel")}
      </label>
      <div className={`flex ${compact ? "flex-row" : "flex-col sm:flex-row"} gap-3`}>
        <input
          id="code"
          name="code"
          inputMode="text"
          autoComplete="off"
          autoCapitalize="characters"
          spellCheck={false}
          maxLength={14}
          placeholder={t("placeholder")}
          value={value}
          onChange={(e) => {
            setValue(formatPartial(e.target.value));
            setError(null);
          }}
          aria-invalid={!!error}
          aria-describedby={error ? "code-error" : undefined}
          className="field code-field flex-1 text-xl"
        />
        <button type="submit" className="btn btn-dark text-base">
          {t("submit")}
        </button>
      </div>
      {error && (
        <p id="code-error" role="alert" className="mt-2 text-sm font-medium text-bad">
          {error}
        </p>
      )}
    </form>
  );
}

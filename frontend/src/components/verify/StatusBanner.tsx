import type { VerifyResult } from "@/lib/api";

const STYLE: Record<VerifyResult["status"], { box: string; icon: "ok" | "warn" | "bad" | "info" }> = {
  valid_latest: { box: "bg-ok-bg border-ok text-ok", icon: "ok" },
  valid_superseded: { box: "bg-warn-bg border-warn text-warn", icon: "warn" },
  revoked: { box: "bg-bad-bg border-bad text-bad", icon: "bad" },
  invalid: { box: "bg-bad-bg border-bad text-bad", icon: "bad" },
  not_found: { box: "bg-fog border-ink text-ink", icon: "bad" },
  pending: { box: "bg-warn-bg border-warn text-warn", icon: "info" },
  chain_unavailable: { box: "bg-warn-bg border-warn text-warn", icon: "info" },
};

function Icon({ kind }: { kind: "ok" | "warn" | "bad" | "info" }) {
  if (kind === "ok")
    return (
      <svg width="40" height="40" viewBox="0 0 40 40" aria-hidden>
        <circle cx="20" cy="20" r="18" fill="none" stroke="currentColor" strokeWidth="3" />
        <path d="M12 20.5l5.5 5.5L29 14" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="square" />
      </svg>
    );
  if (kind === "bad")
    return (
      <svg width="40" height="40" viewBox="0 0 40 40" aria-hidden>
        <circle cx="20" cy="20" r="18" fill="none" stroke="currentColor" strokeWidth="3" />
        <path d="M13 13l14 14M27 13L13 27" stroke="currentColor" strokeWidth="3.5" />
      </svg>
    );
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" aria-hidden>
      <path d="M20 3l18 33H2z" fill="none" stroke="currentColor" strokeWidth="3" strokeLinejoin="round" />
      <path d="M20 15v10M20 29v3" stroke="currentColor" strokeWidth="3.5" />
    </svg>
  );
}

export default function StatusBanner({ status, title, body }: { status: VerifyResult["status"]; title: string; body: string }) {
  const s = STYLE[status];
  return (
    <div role="status" className={`flex items-start gap-4 border-l-8 p-5 ${s.box}`}>
      <div className="shrink-0">
        <Icon kind={s.icon} />
      </div>
      <div>
        <p className="font-display text-xl font-extrabold md:text-2xl">{title}</p>
        <p className="mt-1 text-ink/80">{body}</p>
      </div>
    </div>
  );
}

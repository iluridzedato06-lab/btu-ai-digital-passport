"use client";

export class ApiError extends Error {
  status: number;
  code: string;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const m = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return m ? decodeURIComponent(m[1]) : null;
}

async function ensureCsrf(): Promise<string> {
  let token = readCookie("csrftoken");
  if (!token) {
    const r = await fetch("/api/auth/csrf", { credentials: "same-origin" });
    const j = await r.json().catch(() => ({}));
    token = readCookie("csrftoken") || j.csrfToken || "";
  }
  return token || "";
}

export async function api<T = unknown>(path: string, init: RequestInit & { json?: unknown } = {}): Promise<T> {
  const method = (init.method || (init.json !== undefined ? "POST" : "GET")).toUpperCase();
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  let body = init.body;
  if (init.json !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(init.json);
  }
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    headers.set("X-CSRFToken", await ensureCsrf());
  }
  const res = await fetch(`/api${path}`, { ...init, method, headers, body, credentials: "same-origin", cache: "no-store" });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    throw new ApiError(res.status, data?.error || "error", data?.detail || res.statusText);
  }
  return data as T;
}

export type Role = "anon" | "student" | "staff" | "admin" | "none";

export interface Stamp {
  skill_name: string;
  skill_name_ka?: string;
  stamp_type: "FOCUSED" | "APPLIED" | "ADVANCED";
  description: string;
  earned_through: string;
  date_earned: string;
}

export interface AnchorInfo {
  status: string;
  chain_id: number;
  contract: string;
  tx_hash: string | null;
  block_number: number | null;
  block_timestamp: string | null;
  issuer_address: string;
  explorer_url: string;
  attempts: number;
  last_error: string;
}

export interface VersionSummary {
  id: string;
  version_number: number;
  status: "rendered" | "anchoring" | "anchored" | "anchor_failed";
  trigger_reason: string;
  created_at: string;
  issued_at: string | null;
  pdf_sha256: string;
  pdf_size: number;
  revoked_at: string | null;
  revoke_reason: string;
  award_count: number;
  anchor: AnchorInfo | null;
  verification_code?: string;
  verify_url?: string;
  is_latest_valid?: boolean;
}

export interface Me {
  authenticated: boolean;
  email?: string;
  role: Role;
  student: null | {
    student_number: string;
    first_name: string;
    last_name: string;
    first_name_ka: string;
    last_name_ka: string;
    programme: string;
    pending_stamps: Stamp[];
  };
  passport: null | {
    passport_id: string;
    first_issued_on: string;
    holder: { first_name: string; last_name: string };
    latest_valid_version: number | null;
    stamps: Stamp[];
    versions: VersionSummary[];
  };
}

export interface VerifyResult {
  status: "valid_latest" | "valid_superseded" | "revoked" | "invalid" | "not_found" | "pending" | "chain_unavailable";
  passport_id?: string;
  holder?: { first_name: string; last_name: string };
  version?: number;
  latest_version?: number;
  latest_valid_version?: number | null;
  first_issued_on?: string;
  version_issued_on?: string;
  issued_at?: string | null;
  verification_code?: string;
  pdf_sha256?: string;
  stamps?: Stamp[];
  revocation?: { revoked_at: string | null; reason: string } | null;
  checks?: Record<string, boolean>;
  document_authentic?: boolean;
  issuer_authentic?: boolean;
  chain?: {
    chain_id: number;
    chain_name: string;
    contract: string;
    tx_hash: string | null;
    block_number: number | null;
    explorer_url: string;
    reachable: boolean;
    issuer_address?: string;
    anchored_at?: number;
    latest_version_on_chain?: number;
  } | null;
}

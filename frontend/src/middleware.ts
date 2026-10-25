import createMiddleware from "next-intl/middleware";
import { NextResponse, type NextRequest } from "next/server";
import { routing } from "./i18n/routing";

const intl = createMiddleware(routing);

function buildCsp(nonce: string) {
  const dev = process.env.NODE_ENV !== "production";
  return [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${dev ? " 'unsafe-eval'" : ""}`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    `connect-src 'self'${dev ? " ws: wss:" : ""}`,
    "worker-src 'self' blob:",
    "frame-ancestors 'none'",
    "form-action 'self'",
    "base-uri 'self'",
    "object-src 'none'",
  ].join("; ");
}

export default function middleware(req: NextRequest) {
  const nonce = btoa(crypto.randomUUID());
  const csp = buildCsp(nonce);
  const intlRes = intl(req);

  // Redirects (e.g. "/" -> "/ka") need no rendering, just the header.
  if (!intlRes.headers.get("x-middleware-next") && !intlRes.headers.get("x-middleware-rewrite")) {
    intlRes.headers.set("Content-Security-Policy", csp);
    return intlRes;
  }

  // Forward the nonce to the renderer so Next.js tags its own scripts with it.
  const requestHeaders = new Headers(req.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("content-security-policy", csp);
  const rewrite = intlRes.headers.get("x-middleware-rewrite");
  const res = rewrite
    ? NextResponse.rewrite(new URL(rewrite), { request: { headers: requestHeaders } })
    : NextResponse.next({ request: { headers: requestHeaders } });

  intlRes.headers.forEach((value, key) => {
    if (key.startsWith("x-middleware-") || key === "set-cookie") return;
    res.headers.set(key, value);
  });
  for (const cookie of intlRes.headers.getSetCookie()) res.headers.append("set-cookie", cookie);
  res.headers.set("Content-Security-Policy", csp);
  return res;
}

export const config = {
  matcher: ["/((?!api|django-admin|django-static|_next|_vercel|\\.well-known|.*\\..*).*)"],
};

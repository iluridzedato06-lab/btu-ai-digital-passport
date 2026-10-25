// Must stay in sync with backend/apps/core/codes.py
export const ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";
const VALID = new RegExp(`^[${ALPHABET}]{12}$`);

export function normalizeCode(raw: string): string | null {
  const s = raw
    .replace(/[\s\-_.]/g, "")
    .toUpperCase()
    .replace(/[IL]/g, "1")
    .replace(/O/g, "0");
  return VALID.test(s) ? s : null;
}

/** Live formatting while typing: keeps allowed characters and inserts dashes. */
export function formatPartial(raw: string): string {
  const s = raw
    .toUpperCase()
    .replace(/[IL]/g, "1")
    .replace(/O/g, "0")
    .replace(new RegExp(`[^${ALPHABET}]`, "g"), "")
    .slice(0, 12);
  return s.replace(/(.{4})(?=.)/g, "$1-");
}

export function formatCode(code: string): string {
  return code.replace(/(.{4})(?=.)/g, "$1-");
}

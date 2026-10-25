import { describe, expect, it } from "vitest";
import { formatCode, formatPartial, normalizeCode } from "./code-format";
import { hashesEqual, sha256Hex } from "./hash";
import en from "../../messages/en.json";
import ka from "../../messages/ka.json";

describe("verification code format", () => {
  it("normalises dashes, case and confusable letters", () => {
    expect(normalizeCode("7kq2-m9xd-4trb")).toBe("7KQ2M9XD4TRB");
    expect(normalizeCode("OIL0 0000 0000")).toBe("011000000000");
  });
  it("rejects wrong length and U", () => {
    expect(normalizeCode("7KQ2-M9XD")).toBeNull();
    expect(normalizeCode("UUUU-UUUU-UUUU")).toBeNull();
  });
  it("formats while typing", () => {
    expect(formatPartial("7kq2m9")).toBe("7KQ2-M9");
    expect(formatCode("7KQ2M9XD4TRB")).toBe("7KQ2-M9XD-4TRB");
  });
});

describe("client-side hashing", () => {
  it("computes sha256 like the server", async () => {
    const h = await sha256Hex(new TextEncoder().encode("abc"));
    expect(h).toBe("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
  });
  it("detects a single changed byte", async () => {
    const a = new TextEncoder().encode("%PDF-1.7 passport");
    const b = new Uint8Array(a);
    b[5] ^= 1;
    expect(hashesEqual(await sha256Hex(a), await sha256Hex(b))).toBe(false);
  });
});

describe("translations", () => {
  function keys(o: Record<string, unknown>, p = ""): string[] {
    return Object.entries(o).flatMap(([k, v]) =>
      v && typeof v === "object" && !Array.isArray(v) ? keys(v as Record<string, unknown>, `${p}${k}.`) : [`${p}${k}`],
    );
  }
  it("Georgian and English have the same keys", () => {
    expect(keys(ka).sort()).toEqual(keys(en).sort());
  });
});

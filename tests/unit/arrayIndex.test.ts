import { describe, it, expect } from "vitest";
import { parseArrayIndexToken } from "../../src/internal/arrayIndex";

describe("parseArrayIndexToken", () => {
  it("accepts canonical non-negative base-10 integers", () => {
    expect(parseArrayIndexToken("0")).toEqual({ ok: true, value: 0 });
    expect(parseArrayIndexToken("1")).toEqual({ ok: true, value: 1 });
    expect(parseArrayIndexToken("42")).toEqual({ ok: true, value: 42 });
  });

  it("rejects leading zeros (except '0')", () => {
    const r = parseArrayIndexToken("01");
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.kind).toBe("TypeMismatch");
  });

  it("rejects non-digits / negative / decimal / empty", () => {
    for (const tok of ["", "-1", "1.0", "foo", " 1", "1 "]) {
      const r = parseArrayIndexToken(tok);
      expect(r.ok).toBe(false);
      if (!r.ok) expect(r.kind).toBe("TypeMismatch");
    }
  });
});
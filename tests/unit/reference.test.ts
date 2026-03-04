import { describe, it, expect } from "vitest";
import { resolveLocalRef } from "../../src/public/reference";
import type { JSONValue } from "../../src/public/types";

describe("resolveLocalRef", () => {
  it('"#" => whole document', () => {
    const doc: JSONValue = { a: 1 };
    expect(resolveLocalRef(doc, "#")).toEqual({ ok: true, value: doc });
  });

  it('"#/a" resolves via pointer', () => {
    const doc: JSONValue = { a: { b: 2 } };
    expect(resolveLocalRef(doc, "#/a/b")).toEqual({ ok: true, value: 2 });
  });

  it('"#/missing" => NotFound', () => {
    const doc: JSONValue = { a: 1 };
    const r = resolveLocalRef(doc, "#/b");
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.kind).toBe("NotFound");
  });

  it("escaped fragment tokens are unescaped via pointer parsing", () => {
    const doc: JSONValue = { a: { "~": 1, "/": 2, "b/c": 3, "d~e": 4 } };
    expect(resolveLocalRef(doc, "#/a/~0")).toEqual({ ok: true, value: 1 });
    expect(resolveLocalRef(doc, "#/a/~1")).toEqual({ ok: true, value: 2 });
    expect(resolveLocalRef(doc, "#/a/b~1c")).toEqual({ ok: true, value: 3 });
    expect(resolveLocalRef(doc, "#/a/d~0e")).toEqual({ ok: true, value: 4 });
  });

  it("invalid escaped fragments => InvalidPointer", () => {
    const doc: JSONValue = { a: 1 };
    for (const ref of ["#/~", "#/~2", "#/a/~2"]) {
      const r = resolveLocalRef(doc, ref);
      expect(r.ok).toBe(false);
      if (!r.ok) expect(r.kind).toBe("InvalidPointer");
    }
  });

  it("unsupported forms => InvalidPointer", () => {
    const doc: JSONValue = { a: 1 };
    for (const ref of ["", "#foo", "other.json#/a", "http://x/y#/a"]) {
      const r = resolveLocalRef(doc, ref);
      expect(r.ok).toBe(false);
      if (!r.ok) expect(r.kind).toBe("InvalidPointer");
    }
  });
});

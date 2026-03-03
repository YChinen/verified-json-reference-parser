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

  it("unsupported forms => InvalidPointer", () => {
    const doc: JSONValue = { a: 1 };
    for (const ref of ["", "#foo", "other.json#/a", "http://x/y#/a"]) {
      const r = resolveLocalRef(doc, ref);
      expect(r.ok).toBe(false);
      if (!r.ok) expect(r.kind).toBe("InvalidPointer");
    }
  });
});
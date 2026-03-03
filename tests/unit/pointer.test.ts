import { describe, it, expect } from "vitest";
import { parsePointer, formatPointer, get } from "../../src/public/pointer";
import type { JSONValue } from "../../src/public/types";

describe("JSON Pointer: parse/format", () => {
  it('parsePointer("") = []', () => {
    expect(parsePointer("")).toEqual({ ok: true, value: [] });
  });

  it('formatPointer([]) = ""', () => {
    expect(formatPointer([])).toBe("");
  });

  it('parsePointer("/") = [""] (empty token)', () => {
    expect(parsePointer("/")).toEqual({ ok: true, value: [""] });
  });

  it("round-trip: parse(format(ptr)) = ptr", () => {
    const ptrs = [[], ["a"], ["a", "b"], [""], ["a~b", "c/d"]];
    for (const p of ptrs) {
      const s = formatPointer(p);
      const r = parsePointer(s);
      expect(r.ok).toBe(true);
      if (r.ok) expect(r.value).toEqual(p);
    }
  });

  it("rejects non-empty pointer not starting with '/'", () => {
    const r = parsePointer("a");
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.kind).toBe("InvalidPointer");
  });

  it("rejects invalid ~ escapes in segments", () => {
    const r = parsePointer("/a~2b");
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.kind).toBe("InvalidPointer");
  });
});

describe("JSON Pointer: get", () => {
  it("object traversal success", () => {
    const doc: JSONValue = { a: { b: 1 } };
    const p = parsePointer("/a/b");
    expect(p.ok).toBe(true);
    if (!p.ok) return;

    expect(get(doc, p.value)).toEqual({ ok: true, value: 1 });
  });

  it("object missing key => NotFound", () => {
    const doc: JSONValue = { a: {} };
    const p = parsePointer("/a/b");
    if (!p.ok) throw new Error("parse failed");
    const r = get(doc, p.value);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.kind).toBe("NotFound");
  });

  it("primitive traversal => TypeMismatch", () => {
    const doc: JSONValue = { a: 1 };
    const p = parsePointer("/a/b");
    if (!p.ok) throw new Error("parse failed");
    const r = get(doc, p.value);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.kind).toBe("TypeMismatch");
  });

  it("array numeric index success", () => {
    const doc: JSONValue = { a: ["x", "y"] };
    const p = parsePointer("/a/1");
    if (!p.ok) throw new Error("parse failed");
    expect(get(doc, p.value)).toEqual({ ok: true, value: "y" });
  });

  it("array out-of-bounds => NotFound", () => {
    const doc: JSONValue = ["x"];
    const p = parsePointer("/1");
    if (!p.ok) throw new Error("parse failed");
    const r = get(doc, p.value);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.kind).toBe("NotFound");
  });

  it("array non-numeric token => TypeMismatch", () => {
    const doc: JSONValue = ["x"];
    const p = parsePointer("/foo");
    if (!p.ok) throw new Error("parse failed");
    const r = get(doc, p.value);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.kind).toBe("TypeMismatch");
  });

  it("array leading-zero token => TypeMismatch", () => {
    const doc: JSONValue = ["x", "y"];
    const p = parsePointer("/01");
    if (!p.ok) throw new Error("parse failed");
    const r = get(doc, p.value);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.kind).toBe("TypeMismatch");
  });

  it('empty token selects empty-key property: pointer "/"', () => {
    const doc: JSONValue = { "": 123 };
    const p = parsePointer("/");
    if (!p.ok) throw new Error("parse failed");
    expect(get(doc, p.value)).toEqual({ ok: true, value: 123 });
  });
});
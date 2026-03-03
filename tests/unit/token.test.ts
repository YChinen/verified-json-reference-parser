import { describe, it, expect } from "vitest";
import { escapeToken, unescapeToken } from "../../src/internal/token";

describe("token escape/unescape", () => {
  it("escapeToken: ~ and /", () => {
    expect(escapeToken("a~b/c")).toBe("a~0b~1c");
  });

  it("unescapeToken: ~0 and ~1", () => {
    const r = unescapeToken("a~0b~1c");
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.value).toBe("a~b/c");
  });

  it("unescapeToken rejects invalid ~ escape", () => {
    expect(unescapeToken("~2").ok).toBe(false);
    expect(unescapeToken("~").ok).toBe(false);
    expect(unescapeToken("a~9b").ok).toBe(false);
  });

  it("round-trip: unescape(escape(x)) = x", () => {
    const samples = ["", "abc", "~", "/", "a~b/c", "~~//~~"];
    for (const s of samples) {
      const r = unescapeToken(escapeToken(s));
      expect(r.ok).toBe(true);
      if (r.ok) expect(r.value).toBe(s);
    }
  });
});
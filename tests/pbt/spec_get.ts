// tests/pbt/spec_get.ts
import type { JSONValue, Result } from "../../src/public/types";

function err<T = never>(kind: "InvalidPointer" | "TypeMismatch" | "NotFound"): Result<T> {
  return { ok: false, kind };
}
function ok<T>(value: T): Result<T> {
  return { ok: true, value };
}

export function specParseArrayIndexToken(token: string): number | null {
  if (token.length === 0) return null;

  // digits only
  for (let i = 0; i < token.length; i++) {
    const c = token.charCodeAt(i);
    if (c < 0x30 || c > 0x39) return null;
  }

  // no leading zeros unless exactly "0"
  if (token.length > 1 && token.charCodeAt(0) === 0x30) return null;

  const n = Number(token);
  if (!Number.isSafeInteger(n) || n < 0) return null;
  return n;
}

export function specGet(doc: JSONValue, tokens: readonly string[]): Result<JSONValue> {
  let cur: JSONValue = doc;

  for (const token of tokens) {
    if (Array.isArray(cur)) {
      const idx = specParseArrayIndexToken(token);
      if (idx === null) return err("TypeMismatch");
      if (idx < 0 || idx >= cur.length) return err("NotFound");
      cur = cur[idx] as JSONValue;
      continue;
    }

    if (cur !== null && typeof cur === "object") {
      const obj = cur as { [k: string]: JSONValue };
      if (!Object.prototype.hasOwnProperty.call(obj, token)) return err("NotFound");
      cur = obj[token] as JSONValue;
      continue;
    }

    return err("TypeMismatch");
  }

  return ok(cur);
}
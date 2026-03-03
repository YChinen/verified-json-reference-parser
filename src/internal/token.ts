import { ok, err } from "../public/types.js";
import type { Result } from "../public/types.js";

/**
 * Escape a JSON Pointer token (RFC 6901).
 * - "~" => "~0"
 * - "/" => "~1"
 */
export function escapeToken(token: string): string {
  // Order matters: escape "~" first to avoid double-escaping.
  return token.replace(/~/g, "~0").replace(/\//g, "~1");
}

/**
 * Unescape a JSON Pointer token (RFC 6901).
 * - "~1" => "/"
 * - "~0" => "~"
 *
 * Any other "~" sequence is invalid (e.g. "~2", trailing "~").
 */
export function unescapeToken(token: string): Result<string> {
  // Fast path: no "~" means nothing to unescape and cannot be invalid.
  if (!token.includes("~")) return ok(token);

  let out = "";
  for (let i = 0; i < token.length; i++) {
    const ch = token.charCodeAt(i);
    if (ch !== 0x7e /* "~" */) {
      out += token[i];
      continue;
    }

    // "~" must be followed by "0" or "1"
    if (i + 1 >= token.length) return err("InvalidPointer");
    const next = token.charCodeAt(i + 1);

    if (next === 0x30 /* "0" */) {
      out += "~";
      i++; // consume next
      continue;
    }
    if (next === 0x31 /* "1" */) {
      out += "/";
      i++; // consume next
      continue;
    }

    return err("InvalidPointer");
  }

  return ok(out);
}
import { ok, err } from "./types.js";
import type { Result, JSONValue, Pointer } from "./types.js";
import { escapeToken, unescapeToken } from "../internal/token.js";
import { parseArrayIndexToken } from "../internal/arrayIndex.js";

/**
 * Parse a JSON Pointer string (RFC 6901) into a token array.
 *
 * - "" => []
 * - Otherwise must start with "/"
 * - "/" => [""] (empty token selects empty-key property)
 *
 * Returns `InvalidPointer` for malformed pointer syntax or invalid token
 * escapes. This function does not inspect any JSON document.
 */
export function parsePointer(pointerString: string): Result<Pointer> {
  if (pointerString === "") return ok([]);

  if (!pointerString.startsWith("/")) return err("InvalidPointer");

  // Split into segments. Leading "/" produces an empty first segment; skip it.
  const rawSegments = pointerString.split("/").slice(1);

  const tokens: string[] = [];
  for (const seg of rawSegments) {
    const u = unescapeToken(seg);
    if (!u.ok) return u; // InvalidPointer
    tokens.push(u.value);
  }

  return ok(tokens);
}

/**
 * Format a token array into a JSON Pointer string (RFC 6901).
 *
 * - [] => ""
 * - Otherwise: "/" + escape(token1) + "/" + escape(token2) + ...
 *
 * The operation is total for the internal `Pointer` representation.
 */
export function formatPointer(pointer: Pointer): string {
  if (pointer.length === 0) return "";
  return "/" + pointer.map(escapeToken).join("/");
}

/**
 * Evaluate a JSON Pointer against a JSON document.
 *
 * Returns:
 * - ok(value) on success
 * - NotFound if a property / element does not exist
 * - TypeMismatch if traversal is invalid for the current value shape
 *
 * Important Phase 1 distinction:
 * - Invalid array index token format during array traversal is `TypeMismatch`
 * - Missing object keys and out-of-bounds array indices are `NotFound`
 */
export function get(doc: JSONValue, pointer: Pointer): Result<JSONValue> {
  let cur: JSONValue = doc;

  for (const token of pointer) {
    // Array case
    if (Array.isArray(cur)) {
      const idxR = parseArrayIndexToken(token);
      if (!idxR.ok) return idxR; // TypeMismatch

      const idx = idxR.value;
      if (idx < 0 || idx >= cur.length) return err("NotFound");

      cur = cur[idx] as JSONValue;
      continue;
    }

    // Object case (exclude null)
    if (cur !== null && typeof cur === "object") {
      // At this point, cur is either an object or (handled above) an array.
      const obj = cur as { [key: string]: JSONValue };

      // Property existence must distinguish between missing vs present undefined.
      // In JSON model, properties map to JSONValue; undefined is treated as missing.
      if (!Object.prototype.hasOwnProperty.call(obj, token)) return err("NotFound");

      cur = obj[token] as JSONValue;
      continue;
    }

    // Primitive case
    return err("TypeMismatch");
  }

  return ok(cur);
}

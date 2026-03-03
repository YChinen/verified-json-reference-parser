import { ok, err } from "../public/types.js";
import type { Result } from "../public/types.js";

/**
 * Parse an array index token for pointer evaluation.
 *
 * Semantics (Phase 1):
 * - Token must be a base-10 non-negative integer in canonical form.
 * - Digits only: /^[0-9]+$/
 * - No leading zeros unless the token is exactly "0".
 *
 * Valid:  "0", "1", "42"
 * Invalid: "", "01", "-1", "1.0", "foo"
 *
 * Failures are classified as TypeMismatch (not InvalidPointer),
 * because the pointer string itself may be syntactically valid.
 */
export function parseArrayIndexToken(token: string): Result<number> {
  if (token.length === 0) return err("TypeMismatch");

  // Digits only
  for (let i = 0; i < token.length; i++) {
    const c = token.charCodeAt(i);
    if (c < 0x30 /* '0' */ || c > 0x39 /* '9' */) return err("TypeMismatch");
  }

  // No leading zeros unless token is exactly "0"
  if (token.length > 1 && token.charCodeAt(0) === 0x30 /* '0' */) {
    return err("TypeMismatch");
  }

  // Convert to number. Note: arrays in JS can't have length > 2^32-1 anyway.
  const n = Number(token);

  // Guard against weirdness (Number("...") should be safe after digit check),
  // but keep it explicit.
  if (!Number.isSafeInteger(n) || n < 0) return err("TypeMismatch");

  return ok(n);
}
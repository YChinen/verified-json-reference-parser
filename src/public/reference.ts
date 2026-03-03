import { ok, err } from "./types";
import type { JSONValue, Result } from "./types";
import { parsePointer, get } from "./pointer";

/**
 * Resolve a local JSON Reference against a JSON document.
 *
 * Phase 1 supported forms:
 * - "#": whole document
 * - "#/...": JSON Pointer fragment
 *
 * Unsupported forms (Phase 1):
 * - non-local references (e.g. "other.json#/x")
 * - non-pointer fragments
 *
 * All failures are explicit via Result.
 */
export function resolveLocalRef(doc: JSONValue, refString: string): Result<JSONValue> {
  // Whole document reference
  if (refString === "#") return ok(doc);

  // Pointer fragment form
  if (refString.startsWith("#/")) {
    const pointerString = refString.slice(1); // drop leading "#", leaving "/..."
    const p = parsePointer(pointerString);
    if (!p.ok) return p; // InvalidPointer
    return get(doc, p.value);
  }

  // Everything else is unsupported in Phase 1
  return err("InvalidPointer");
}
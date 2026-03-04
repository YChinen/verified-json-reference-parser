import { ok, err } from "./types.js";
import type { JSONValue, Result } from "./types.js";
import { parsePointer, get } from "./pointer.js";

/**
 * Resolve a local JSON Reference against a JSON document.
 *
 * Phase 1 supported forms:
 * - "#": whole document
 * - "#/...": JSON Pointer fragment evaluated within the same document
 *
 * Unsupported forms (Phase 1):
 * - non-local references (e.g. "other.json#/x")
 * - non-pointer fragments
 *
 * All failures are explicit via Result. Unsupported or malformed reference
 * forms are classified as `InvalidPointer`.
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

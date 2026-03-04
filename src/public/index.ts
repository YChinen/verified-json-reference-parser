/**
 * Public API surface for the Phase 1 semantic core.
 *
 * Exposes JSON value types, JSON Pointer operations, and local reference
 * resolution without exporting internal helper utilities.
 */
export type {
  JSONPrimitive,
  JSONValue,
  Pointer,
  Result,
  ErrorKind,
} from "./types.js";

export { ok, err, isOk, isErr } from "./types.js";

export { parsePointer, formatPointer, get } from "./pointer.js";

export { resolveLocalRef } from "./reference.js";

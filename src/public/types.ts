/**
 * JSON value model used by this library.
 *
 * Notes:
 * - Objects are represented as string-keyed maps.
 * - Arrays are standard JS arrays.
 */
export type JSONPrimitive = null | boolean | number | string;

export type JSONValue =
  | JSONPrimitive
  | JSONValue[]
  | { [key: string]: JSONValue };

/**
 * Internal JSON Pointer representation (RFC 6901).
 * Empty pointer string "" is represented as [].
 */
export type Pointer = readonly string[];

/**
 * Explicit result type for all semantic operations.
 * The semantic core must not throw exceptions.
 */
export type Result<T> =
  | { ok: true; value: T }
  | { ok: false; kind: ErrorKind };

export type ErrorKind = "InvalidPointer" | "TypeMismatch" | "NotFound";

/**
 * Helper constructors (optional but convenient).
 * Keep them tiny and allocation-friendly.
 */
export const ok = <T>(value: T): Result<T> => ({ ok: true, value });

export const err = <T = never>(kind: ErrorKind): Result<T> => ({
  ok: false,
  kind,
});

/**
 * Type guard helpers.
 */
export const isOk = <T>(r: Result<T>): r is { ok: true; value: T } => r.ok;

export const isErr = <T>(
  r: Result<T>
): r is { ok: false; kind: ErrorKind } => !r.ok;
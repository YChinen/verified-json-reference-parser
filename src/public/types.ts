/**
 * JSON value model used by this library.
 *
 * Notes:
 * - Objects are represented as string-keyed maps.
 * - Arrays are standard JS arrays.
 */
export type JSONPrimitive = null | boolean | number | string;

/**
 * Recursive JSON value domain used by the semantic core.
 */
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

/**
 * Closed set of Phase 1 error kinds.
 */
export type ErrorKind = "InvalidPointer" | "TypeMismatch" | "NotFound";

/**
 * Construct a successful semantic result.
 */
export const ok = <T>(value: T): Result<T> => ({ ok: true, value });

/**
 * Construct a failed semantic result.
 */
export const err = <T = never>(kind: ErrorKind): Result<T> => ({
  ok: false,
  kind,
});

/**
 * Type guard for successful results.
 */
export const isOk = <T>(r: Result<T>): r is { ok: true; value: T } => r.ok;

/**
 * Type guard for failed results.
 */
export const isErr = <T>(
  r: Result<T>
): r is { ok: false; kind: ErrorKind } => !r.ok;

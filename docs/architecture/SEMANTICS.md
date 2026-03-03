# SEMANTICS

This document defines the formal semantic contract of `verified-json-reference-parser`.

The objective is to keep the semantic core:

* Small
* Explicit
* Deterministic
* Mechanically checkable
* Stable once fixed

This document is normative for Phase 1.

---

# 1. Domain Model

## 1.1 JSON Value

We assume the standard JSON value domain:

* `null`
* boolean
* number
* string
* array
* object

Objects are treated as finite mappings from strings to JSON values.
Arrays are finite ordered sequences of JSON values.

---

## 1.2 Pointer Representation

Internally, a JSON Pointer is represented as:

```
Pointer := readonly string[]
```

The empty pointer string `""` is represented as:

```
[]
```

and refers to the entire document.

---

# 2. Result Type

All semantic operations return an explicit `Result<T>`.

```
Result<T> :=
  | { ok: true; value: T }
  | { ok: false; kind: "InvalidPointer" }
  | { ok: false; kind: "TypeMismatch" }
  | { ok: false; kind: "NotFound" }
```

### Error Categories

* **InvalidPointer**

  * Pointer or reference string is syntactically invalid.
  * Unsupported reference forms.
  * Invalid escape sequences.
  * Invalid array index token format.

* **TypeMismatch**

  * Attempting to traverse into a primitive value.
  * Attempting to apply a non-numeric token to an array.

* **NotFound**

  * The path is valid but the property or array element does not exist.

### Design Guarantees

* No implicit `undefined`
* No thrown exceptions in the semantic core
* Explicit and exhaustive outcome classification
* Deterministic results for identical inputs

---

# 3. JSON Pointer Semantics (RFC 6901)

## 3.1 Pointer String Syntax

A pointer string is either:

* `""` (empty string), referring to the whole document
* A string beginning with `/`, followed by segments separated by `/`

Example:

```
/a/b/0
```

Strings not satisfying this form produce:

```
{ ok: false, kind: "InvalidPointer" }
```

---

## 3.2 Escaping and Unescaping

### Escaping Rules

When formatting tokens:

* `~` → `~0`
* `/` → `~1`

### Unescaping Rules

When parsing segments:

* `~1` → `/`
* `~0` → `~`

Any other `~` sequence results in:

```
InvalidPointer
```

---

## 3.3 parsePointer

```
parsePointer(pointerString) -> Result<Pointer>
```

Rules:

1. If `pointerString === ""`:

   ```
   { ok: true, value: [] }
   ```

2. Otherwise:

   * Must begin with `/`
   * Split into segments by `/`
   * Unescape each segment
   * If any segment is invalid → `InvalidPointer`

---

## 3.4 formatPointer

```
formatPointer(pointer) -> string
```

Rules:

* `[]` → `""`
* Otherwise:

  * Escape each token
  * Join with `/`
  * Prefix with `/`

---

# 4. Pointer Evaluation

## 4.1 get

```
get(doc, pointer) -> Result<JSONValue>
```

Evaluation proceeds left-to-right over tokens.

---

## 4.2 Object Traversal

If the current value is an object:

* The token selects a property by exact string match.
* If the property does not exist → `NotFound`.

---

## 4.3 Array Traversal

If the current value is an array:

### Index Token Requirements

A token is interpreted as an array index **if and only if**:

* It consists solely of decimal digits (`0-9`)
* It does not contain a leading zero unless the token is exactly `"0"`

Valid examples:

* `"0"`
* `"1"`
* `"42"`

Invalid examples:

* `"01"` (leading zero)
* `"-1"`
* `"1.0"`
* `"foo"`

If the token fails numeric validation → `TypeMismatch`.

If the token is valid but the index is out of bounds → `NotFound`.

---

## 4.4 Primitive Traversal

If the current value is a primitive (null, boolean, number, string):

* Any further token → `TypeMismatch`.

---

# 5. Local JSON Reference Semantics

## 5.1 resolveLocalRef

```
resolveLocalRef(doc, refString) -> Result<JSONValue>
```

Supported forms (Phase 1):

* `"#"` → whole document
* `"#/..."` → interpreted as a JSON Pointer

Resolution steps:

1. If `refString === "#"`:

   ```
   { ok: true, value: doc }
   ```

2. If `refString` begins with `"#/"`:

   * Extract fragment after `#`
   * Parse as JSON Pointer
   * Evaluate via `get`

3. Otherwise:

   ```
   { ok: false, kind: "InvalidPointer" }
   ```

Non-local references (e.g. `other.json#/x`) are not supported in Phase 1.

---

# 6. Verified Invariants

The following invariants are intended to be mechanically checked (Rocq) and continuously validated (Z3):

1. Escape round-trip:

   ```
   unescape(escape(x)) = x
   ```

2. Pointer round-trip:

   ```
   parsePointer(formatPointer(ptr)).value = ptr
   ```

3. Determinism:
   Identical inputs always produce identical results.

4. No implicit coercion:

   * No numeric normalization of tokens
   * No silent fallback behaviors

---

# 7. Explicit Non-Goals

This document does not define:

* JSON Schema keyword semantics
* External reference fetching
* Network operations
* Full RFC 3986 URI semantics
* URI normalization rules

---

# 8. Stability Commitment

Once the semantic core is formally fixed:

* Observable behavior will not change silently.
* Any semantic change must be explicitly documented.
* Regression tests must reflect updated semantics.
* Public semantic guarantees will remain stable.

---


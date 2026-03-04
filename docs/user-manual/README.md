# User Manual

This manual is for application developers who want to use
`verified-json-reference-parser` as a small, deterministic core for JSON Pointer
and local JSON Reference handling.

Phase 1 scope:

* JSON Pointer parsing and formatting
* Pointer evaluation over JSON values
* Local JSON Reference resolution for `#` and `#/...`

Out of scope in Phase 1:

* External reference loading
* RFC 3986 URI resolution
* Full JSON Schema validation

Japanese version: [README_ja.md](./README_ja.md)

---

## 1. What This Library Provides

The public API is intentionally small:

* `parsePointer(pointerString)`
* `formatPointer(pointer)`
* `get(doc, pointer)`
* `resolveLocalRef(doc, refString)`

All core operations are:

* Pure
* Deterministic
* Explicit about failure via `Result<T>`

The library does not throw semantic errors from the core API. Instead, it
returns one of:

* `{ ok: true, value: ... }`
* `{ ok: false, kind: "InvalidPointer" }`
* `{ ok: false, kind: "TypeMismatch" }`
* `{ ok: false, kind: "NotFound" }`

---

## 2. Installation

```bash
npm install verified-json-reference-parser
```

This package is designed to be embedded into JSON Schema tooling or other code
that needs stable reference-handling behavior.

---

## 3. Basic Usage

### Parse and format a pointer

```ts
import { parsePointer, formatPointer } from "verified-json-reference-parser";

const parsed = parsePointer("/a/b~1c");
if (parsed.ok) {
  console.log(parsed.value); // ["a", "b/c"]
  console.log(formatPointer(parsed.value)); // "/a/b~1c"
}
```

### Evaluate a pointer

```ts
import { parsePointer, get } from "verified-json-reference-parser";

const doc = {
  defs: {
    user: { name: "Ada" },
  },
};

const ptr = parsePointer("/defs/user/name");
if (ptr.ok) {
  const result = get(doc, ptr.value);
  console.log(result); // { ok: true, value: "Ada" }
}
```

### Resolve a local reference

```ts
import { resolveLocalRef } from "verified-json-reference-parser";

const doc = {
  defs: {
    user: { name: "Ada" },
  },
};

console.log(resolveLocalRef(doc, "#"));
console.log(resolveLocalRef(doc, "#/defs/user"));
```

---

## 4. Semantic Model

### JSON Pointer

The library follows RFC 6901 Phase 1 behavior:

* `""` means the whole document
* Non-empty pointers must start with `/`
* `~0` unescapes to `~`
* `~1` unescapes to `/`
* Any other `~` escape is `InvalidPointer`

### Pointer evaluation

Evaluation is left-to-right.

For objects:

* Tokens select properties by exact key match
* Missing keys yield `NotFound`

For arrays:

* Tokens must be canonical non-negative base-10 indices
* `"0"` is valid
* `"01"`, `"-1"`, `"1.0"` are invalid as array indices
* Invalid array index tokens yield `TypeMismatch`
* Out-of-bounds indices yield `NotFound`

For primitives:

* Any further traversal yields `TypeMismatch`

### Local references

Supported forms:

* `#`
* `#/...`

Everything else is outside Phase 1 and yields `InvalidPointer`.

---

## 5. Error Handling Guide

Use the error kind to distinguish the failure class:

* `InvalidPointer`: the pointer or local ref syntax is invalid
* `TypeMismatch`: traversal shape is wrong for the current JSON value
* `NotFound`: the path is valid, but the selected member does not exist

Example:

```ts
import { parsePointer, get } from "verified-json-reference-parser";

const doc = { items: ["a"] };
const p = parsePointer("/items/01");

if (p.ok) {
  const r = get(doc, p.value);
  // { ok: false, kind: "TypeMismatch" }
}
```

`"01"` is not treated as a syntax error in the pointer itself. It only becomes a
`TypeMismatch` when that token is used against an array.

---

## 6. Practical Integration Notes

This library is a semantic core, not a full resolver.

Typical usage inside a JSON Schema engine:

1. Parse or receive a local `$ref`
2. Call `resolveLocalRef` for Phase 1-supported forms
3. Propagate the explicit `Result`
4. Keep higher-level schema loading and URI resolution outside this library

Recommended practice:

* Treat the result kinds as part of your control flow
* Do not coerce `TypeMismatch` and `NotFound` into the same condition
* Keep network and external document logic in a separate layer

---

## 7. Current Verification Status

The runtime library stays small, but development-time verification is stronger
than a typical utility package.

The project currently uses:

* Unit tests
* Property-based tests
* A pure Python reference model
* A Z3-backed oracle for concrete Phase 1 cases
* Differential testing against the TypeScript implementation

This verification layer is development-only and is not required at runtime.

---

## 8. Limits And Non-Goals

Do not expect this library to:

* Fetch remote documents
* Resolve non-local references
* Implement full RFC 3986 processing
* Validate full JSON Schema documents
* Produce rich validator-style diagnostics

If you need those features, build them around this semantic core rather than
inside it.

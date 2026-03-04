# Formal Specification

## Overview

This document describes the **formal specification and machine-checked Rocq proofs** used in this project.

The goal of the formal specification is to precisely define key semantic properties of the JSON Pointer implementation and verify them using a proof assistant.

This project uses **Rocq** to formalize and verify selected invariants of the JSON Pointer semantics defined in **RFC 6901**.
It also uses separate Z3-based verification tooling for differential validation of concrete Phase 1 cases, but that Z3 layer is not itself a Rocq proof artifact.

Formal verification is applied to critical components where subtle implementation bugs may lead to incorrect pointer resolution.

---

## Scope of Formal Verification

Formal verification in this project currently focuses on the **core pointer token and pointer representation semantics**.

The following components are formalized:

* Pointer token escaping and unescaping
* Pointer parsing
* Pointer formatting
* Round-trip invariants between parsing and formatting

The goal is to ensure that the internal pointer representation behaves predictably and consistently.

---

## Formal Model

The formal model represents JSON Pointer concepts using Rocq data structures.

### Token Model

Pointer tokens are modeled as strings.

Two fundamental operations are defined:

* `escapeToken : string → string`
* `unescapeToken : string → Result string`

These correspond to the escape rules defined in RFC 6901:

* `"~"` → `"~0"`
* `"/"` → `"~1"`

---

### Pointer Representation

Pointers are modeled as sequences of tokens.

```
Pointer := list string
```

An empty pointer (`""`) corresponds to the empty list.

---

### Parsing and Formatting

Two functions define the conversion between string pointers and the internal representation:

```
parsePointer  : string → Result Pointer
formatPointer : Pointer → string
```

These correspond to the parsing and formatting logic implemented in the TypeScript codebase.

---

## Proven Properties

The following properties are currently machine-checked using Rocq.

### Token Round-Trip

Escaping a token and then unescaping it returns the original token.

```
unescapeToken (escapeToken t) = Ok t
```

This ensures that the escaping mechanism is reversible.

---

### Pointer Round-Trip

Formatting a pointer and then parsing it returns the original pointer.

```
parsePointer (formatPointer p) = Ok p
```

This property guarantees consistency between the textual and internal pointer representations.

---

## Relationship to the Implementation

The Rocq model corresponds directly to the semantic core implemented in TypeScript.

The goal is to ensure that the following layers remain consistent:

```
TypeScript implementation
        ↓
Formal specification (Rocq)
        ↓
Machine-checked proofs
```

The formal model serves as a precise reference for the intended semantics of the implementation.

---

## Verification Philosophy

Formal verification in this project focuses on **semantic invariants** rather than attempting to verify the entire runtime implementation.

Key principles include:

* Verifying small but critical semantic properties
* Keeping the formal model simple and maintainable
* Complementing proofs with property-based testing and differential testing

This layered approach helps balance correctness guarantees with practical development workflows.

---

## Limitations

The current formal specification does **not** attempt to verify:

* the entire JSON evaluation algorithm in Rocq
* the JavaScript runtime environment
* performance characteristics
* memory safety guarantees
* the Z3 oracle implementation itself

Instead, it focuses on correctness of core pointer semantics.

---

## Future Work

Potential areas for further formalization include:

* formal modeling of JSON values
* deeper Rocq verification of pointer evaluation (`get`)
* formal semantics for array index handling
* alignment proofs between the Rocq model and the TypeScript implementation

Formal verification may be extended incrementally as the project evolves.

---

## References

* RFC 6901 — JSON Pointer
* Rocq proof assistant documentation

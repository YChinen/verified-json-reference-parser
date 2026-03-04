# Threat Model

## Overview

This document describes the threat model for this project.

The library implements parsing and evaluation of **JSON Pointer (RFC 6901)** and Phase 1 local JSON Reference resolution.
It processes JSON documents and pointer strings that may originate from **untrusted input**.

The goal of this document is to clarify:

* what assets the project aims to protect
* which inputs are considered untrusted
* the attack surface exposed by the library
* known threat classes
* mitigation strategies

---

## Assets

The primary asset protected by this project is:

**Correct and predictable evaluation of JSON Pointer semantics.**

Specifically, the library aims to ensure:

* JSON Pointer strings are parsed according to RFC 6901
* pointer evaluation produces deterministic results
* malformed inputs are rejected explicitly

Incorrect pointer resolution may cause downstream systems to behave incorrectly, particularly when pointer resolution is used for configuration processing, data validation, or policy evaluation.

---

## Trust Model

### Trusted Components

The following components are assumed to behave correctly:

* The JavaScript runtime environment
* Standard library behavior of the host platform
* The TypeScript implementation of the library itself

### Untrusted Inputs

The following inputs are treated as **untrusted** and may be adversarial:

* JSON Pointer strings
* local reference strings (`#`, `#/...`, and malformed variants)
* JSON documents provided to semantic evaluation functions

Applications using this library should assume that these inputs may be malformed or intentionally crafted.

---

## Attack Surface

The primary attack surfaces exposed by this library are:

### JSON Pointer Parsing

The parser processes externally supplied pointer strings.
Malformed escape sequences or unexpected input structures may be used to attempt to bypass validation or trigger incorrect parsing behavior.

### Pointer Evaluation

Pointer evaluation traverses JSON documents according to parsed tokens.
Incorrect traversal logic could lead to incorrect resolution results.

### Local Reference Resolution

Local reference resolution splits fragments and dispatches into pointer parsing and evaluation.
Incorrect classification of supported and unsupported reference forms could lead to incorrect resolution results.

---

## Threat Classes

### Denial of Service (DoS)

Adversarial inputs may attempt to cause excessive resource consumption.

Examples include:

* extremely long pointer strings
* very large numbers of pointer segments
* deeply nested JSON structures

Applications using this library should consider applying input size limits.

---

### Prototype Pollution

JavaScript object traversal may expose risks related to prototype inheritance.

The library performs explicit property checks when resolving object properties to avoid traversing inherited properties.

However, applications that use pointer tokens to perform object mutation should take care to avoid special keys such as:

* `__proto__`
* `constructor`
* `prototype`

---

### Specification Ambiguity

Differences in interpretation of the JSON Pointer specification may lead to inconsistent behavior across implementations.

This implementation aims to follow **RFC 6901** strictly.
Malformed escape sequences and invalid pointer formats are rejected rather than interpreted permissively.

---

### Implementation Bugs

Incorrect parsing or evaluation logic could lead to incorrect pointer resolution.

Such bugs may result in inconsistent behavior or incorrect results in applications that rely on pointer semantics.

---

## Security Measures

This project incorporates several mechanisms intended to reduce the likelihood of security issues.

### Explicit Error Handling

The semantic core avoids throwing exceptions and instead uses explicit result types to represent success or failure.

This approach ensures that invalid inputs are handled explicitly rather than causing unexpected runtime failures.

---

### Strict Parsing Behavior

Malformed pointer inputs are rejected explicitly instead of being interpreted leniently.

This prevents ambiguous parsing behavior.

---

### Property Traversal Checks

Object traversal uses explicit property existence checks to avoid accessing inherited properties.

---

### Machine-Checked Invariants

Some core invariants of the JSON Pointer semantics are **formally verified using Rocq**.

These include round-trip properties between pointer parsing and formatting, as well as token escaping semantics.

Machine-checked proofs help reduce the risk of logic errors in critical parts of the implementation.

---

### Additional Verification

The project also employs:

* property-based testing
* differential testing
* counterexample search
* a Z3-backed oracle for concrete Phase 1 cases

These techniques help identify unexpected edge cases.

---

## Non-Goals

This library does **not** attempt to address:

* security issues in the host runtime
* vulnerabilities in applications using the library
* misuse of pointer tokens for object mutation

Applications integrating this library are responsible for applying appropriate validation and access controls in their own security context.

---

## Future Considerations

As the project evolves, additional areas that may require security review include:

* mutation APIs (e.g., pointer-based updates)
* integration with JSON Reference or JSON Schema systems
* support for extended pointer semantics

Threat modeling will be updated as new features are introduced.

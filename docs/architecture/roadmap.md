# roadmap.md

# Roadmap

This document outlines the development direction of `verified-json-reference-parser`.

The project prioritizes practical assurance over theoretical completeness.

---

## Guiding Principles

* Keep the semantic core small and sharp.
* Formally specify critical invariants.
* Use SMT-based differential testing for practical robustness.
* Avoid scope creep into full JSON Schema validation.
* Stabilize semantics before optimizing APIs.

---

# Phase 1 — Verified JSON Pointer Core

**Goal:** Establish a stable, formally specified JSON Pointer core.

### Scope

* RFC 6901 parsing
* Escaping / unescaping
* Pointer formatting
* Deterministic pointer evaluation (`get`)
* Local JSON Reference (`#`, `#/...`)

### Verification

* Rocq:

  * `unescape(escape(x)) = x`
  * `parse(format(ptr)) = ptr`
  * Deterministic evaluation

* Z3:

  * Counterexample generation
  * Differential testing against TypeScript implementation
  * Z3-backed oracle for concrete Phase 1 cases

### Exit Criteria

* Stable core API
* Differential test suite in CI
* Formal invariants documented

---

# Phase 2 — Verification Hardening

**Goal:** Harden and scale the existing Z3-backed verification workflow.

### Scope

* Performance and robustness improvements for the Z3 oracle
* Counterexample minimization
* Automatic regression corpus growth
* Stronger parity checks between the Python baseline and the Z3 oracle

### Explicit Non-Goals

* Full RFC 3986 verification
* External reference fetching
* JSON Schema keyword evaluation

### Exit Criteria

* Z3 oracle continues to produce consistent results with TS implementation
* Counterexamples automatically captured
* Clear semantic boundary enforced

---

# Phase 3 — URI Handling (Subset)

**Goal:** Add practical URI resolution without expanding verification scope.

### Scope

* RFC 3986 subset sufficient for:

  * Base URI resolution
  * `$id` handling
* Delegation to stable URI libraries where appropriate

### Non-Goals

* Full formal verification of RFC 3986
* Complete URI normalization proofs

---

# Phase 4 — Stabilization

**Goal:** Freeze semantic core and stabilize API.

### Tasks

* Finalize core invariants
* Lock public API surface
* Mark semantic layer as stable
* Reduce internal refactoring risk

---

# Long-Term Vision

This project also serves as:

* A case study in verification-oriented library design
* A foundation for structured JSON Schema engines
* A practical exploration of formally constrained core components

The semantic core is intended to remain stable once formally fixed.

---

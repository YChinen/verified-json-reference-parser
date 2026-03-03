[![CI](https://github.com/YChinen/verified-json-reference-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/YChinen/verified-json-reference-parser/actions/workflows/ci.yml)

# verified-json-reference-parser

> A practically verified core for JSON Reference resolution in JSON Schema engines.

---

## Overview

`verified-json-reference-parser` provides a formally specified and mechanically checked core for:

* JSON Pointer (RFC 6901)
* Local JSON Reference resolution (`$ref`)
* The foundational components required by JSON Schema engines

This project focuses on **practical assurance**, not absolute formal completeness.

Its goal is to reduce subtle inconsistencies in reference handling while remaining usable in production environments.

---

## Why This Exists

JSON Schema implementations rely heavily on:

* JSON Pointer parsing and evaluation
* `$ref` fragment resolution
* URI-based reference resolution

These areas are small but error-prone.
Even minor inconsistencies can lead to:

* Incorrect `$ref` resolution
* Divergent behavior between validators
* Misleading error paths
* Hard-to-debug schema issues

Most existing implementations are pragmatic but not formally specified.

This project aims to provide a **verification-backed semantic core** that can serve as a reliable foundation.

---

## What “Verified” Means in This Project

This project does **not** claim complete formal verification of all related RFCs.

Instead, “verified” means:

* Core semantics are formally specified.
* Critical invariants are mechanically checked.
* TypeScript implementation is continuously validated against the formal model.
* SMT-backed counterexample generation is used for differential testing.
* Discovered counterexamples are minimized and added to regression tests.

The focus is on practical, enforceable guarantees.

---

## Current Scope (Phase 1)

### RFC 6901 — JSON Pointer

* Pointer parsing
* Pointer formatting
* Token escaping and unescaping
* Deterministic pointer evaluation (`get`)

Design principles:

* Internal representation: `readonly string[]` (token array)
* Invalid escape sequences are rejected
* Evaluation semantics are deterministic
* No implicit coercion beyond RFC requirements

---

### Local JSON References

* `#`
* `#/...`
* Fragment splitting
* Pointer-based resolution within a document

External document loading is intentionally out of scope at this stage.

---

## Verification Strategy

### Rocq (Coq)

Used to formally specify and mechanically check:

* `unescape(escape(x)) = x`
* `parse(format(ptr)) = ptr`
* Deterministic evaluation semantics

The formal layer defines and stabilizes the semantic core.

---

### Z3 (SMT-based Testing)

Used for:

* Counterexample generation
* Differential testing against the TypeScript implementation
* Regression corpus growth

Z3 is used as a semantic stress-testing engine rather than a full proof system.

---

## Roadmap

### Phase 2

* URI resolution (RFC 3986 subset)
* Base URI handling
* `$id` integration

### Phase 3

* Extended JSON Reference resolution
* External reference resolution hooks
* Advanced resolution strategies

---

## Non-Goals (for Now)

* Full formal verification of RFC 3986
* Network fetching
* Complete JSON Schema validation
* Error message specification semantics

This library strictly focuses on reference resolution correctness.

---

## Intended Usage

This project is designed as:

* A foundational component for JSON Schema validators
* A verification-backed reference implementation
* A case study in verification-oriented library design

---

## Design Philosophy

* Practical assurance over theoretical completeness
* Small, well-defined semantic core
* Explicit invariants
* Continuous differential validation
* Stability once semantics are frozen

The core semantic layer is intended to remain stable once formally fixed.

---

## Status

Experimental but actively developed.

The semantic core may evolve until formally stabilized.
After stabilization, breaking changes will be minimized.

---

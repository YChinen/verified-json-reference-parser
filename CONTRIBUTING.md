# CONTRIBUTING

Thank you for your interest in contributing to `verified-json-reference-parser`.

This project prioritizes semantic stability and practical assurance over rapid feature expansion.

Before submitting a pull request, please read the guidelines below.

---

## 1. Scope and Boundaries

This library intentionally focuses on:

* JSON Pointer (RFC 6901)
* Local JSON Reference resolution (`#`, `#/...`)

The following are out of scope:

* JSON Schema keyword evaluation
* External reference fetching
* Full RFC 3986 implementation
* Network features

Pull requests that expand scope beyond these boundaries may be declined.

---

## 2. Semantic Stability First

The core semantic layer is the foundation of this project.

Contributions must not:

* Change observable behavior without clear justification
* Introduce implicit coercion or hidden normalization
* Expand semantics silently

If a change modifies behavior, it must:

* Be explicitly documented
* Include new regression tests
* Pass differential verification

---

## 3. Verification Requirements

All behavioral changes must satisfy:

* Unit tests
* Golden tests (if applicable)
* Differential testing against the Z3 oracle

If semantics are modified, corresponding updates may be required in:

* Formal specifications (Rocq)
* Z3 verification models

---

## 4. Public API Policy

The public API surface is intentionally minimal.

* Avoid adding new exported functions unless strictly necessary.
* Internal helpers must remain internal.
* Breaking changes require discussion.

---

## 5. Code Style and Principles

* Core logic must remain pure and side-effect free.
* Avoid runtime dependencies in the semantic core.
* Keep the implementation small and explicit.
* Prefer clarity over cleverness.

---

## 6. Verification Layer

The `verification/` directory:

* Is development-only.
* Is not distributed in npm packages.
* Must not introduce runtime dependencies.

Z3 serves as a constrained semantic oracle, not a full execution engine.

---

## 7. Philosophy

This project favors:

* Small, sharp semantics
* Explicit invariants
* Practical verification
* Long-term stability

Feature growth is secondary to semantic clarity.

---

## 8. Discussion First

For significant changes, open an issue before submitting a pull request.

Semantic changes should be discussed in advance.

---

This project aims to remain small, stable, and principled.

> If in doubt, prefer preserving semantic clarity over adding new capabilities.

---

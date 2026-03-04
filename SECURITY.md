# Security Policy

> Japanese version: SECURITY_ja.md

## Supported Versions

This project is currently under active development.
Only the latest version on the `main` branch is considered supported.

Security fixes will be applied to the latest development version.

---

## Reporting a Vulnerability

If you believe you have found a security vulnerability, please report it **privately**.

Preferred reporting method:

* GitHub Security Advisory (Private vulnerability report)

Please **do not open a public issue** for security vulnerabilities.

When reporting a vulnerability, please include:

* The affected input (JSON document and/or JSON Pointer)
* Expected behavior
* Actual behavior
* Potential impact (e.g., denial of service, incorrect resolution)

We will acknowledge reports as soon as possible and investigate the issue.

---

## Scope

This library processes **JSON Pointer strings and JSON documents** that may originate from untrusted sources.

The primary security-relevant surfaces are:

* JSON Pointer parsing
* Pointer evaluation against JSON documents
* Local JSON Reference resolution
* Handling of malformed or adversarial inputs

This library does **not execute code** and does not interact with external systems such as filesystems or networks.

---

## Security Considerations

### Input Size

Very large JSON Pointer strings or deeply nested documents may lead to increased memory usage or processing time.

Applications using this library should apply appropriate input size limits when processing untrusted data.

---

### Prototype Pollution

This library does not perform object mutation operations.

Pointer evaluation uses explicit property checks (e.g. `hasOwnProperty`) to avoid traversing inherited properties.

However, applications that use pointer tokens for object mutation should take care to avoid special keys such as:

* `__proto__`
* `constructor`
* `prototype`

---

### Strict Specification Handling

This implementation follows the semantics defined in **RFC 6901 (JSON Pointer)**.

Malformed escape sequences and invalid pointer formats are rejected rather than interpreted permissively.
This design prevents ambiguous pointer resolution behavior.

---

## Security Properties

The implementation is designed with the following properties:

* No exceptions are thrown by the semantic core (explicit `Result` type is used).
* Invalid inputs are handled through explicit error values.
* Pointer token escaping and unescaping semantics are formally specified.

Some core invariants of the JSON Pointer semantics are **machine-verified using Rocq**.

These include properties such as round-trip guarantees for token escaping and pointer formatting.

The development-only verification layer also includes a Z3-backed oracle and differential tests for concrete Phase 1 cases.

---

## Disclosure Policy

When a vulnerability is confirmed:

1. A fix will be prepared and tested.
2. A security advisory may be published.
3. A patched version will be released.

Responsible disclosure is appreciated.

# Developer Manual

This manual is for contributors who need to understand how the repository is
structured, how the Phase 1 semantic core is verified, and how to make changes
without breaking the semantic contract.

Phase 1 scope:

* JSON Pointer parsing and formatting
* Deterministic pointer evaluation
* Local JSON Reference resolution for `#` and `#/...`

Japanese version: [README_ja.md](./README_ja.md)

Normative semantics: [../architecture/SEMANTICS.md](../architecture/SEMANTICS.md)

---

## 1. Repository Map

Core runtime code:

* `src/public/types.ts`
* `src/public/pointer.ts`
* `src/public/reference.ts`
* `src/internal/token.ts`
* `src/internal/arrayIndex.ts`

Tests:

* `tests/unit/*.test.ts`
* `tests/pbt/spec_get.ts`
* `tests/pbt/get.pbt.test.ts`

Verification tooling:

* `verification/z3/spec.py`
* `verification/z3/z3_model.py`
* `verification/z3/oracle.py`
* `verification/z3/diff.mjs`
* `verification/z3/find_cases.py`
* `verification/z3/find_counterexample.py`
* `verification/z3/find_counterexample_vocab.py`

Architecture and semantics docs:

* `docs/architecture/ARCHITECTURE.md`
* `docs/architecture/SEMANTICS.md`
* `docs/architecture/roadmap.md`

---

## 2. Core Behavioral Contract

Treat the semantics document as normative.

In particular, preserve these invariants unless the task explicitly changes
behavior:

* Internal pointer representation is `readonly string[]`
* `""` parses to `[]`
* Non-empty pointer strings must start with `/`
* Only `~0` and `~1` are valid unescape forms
* `get` is pure, deterministic, and left-to-right
* Invalid array index token format during traversal is `TypeMismatch`
* Missing object keys and out-of-bounds array indices are `NotFound`
* `resolveLocalRef` supports only `#` and `#/...` in Phase 1

If semantics change:

1. Update runtime code
2. Update tests
3. Update verification tooling if needed
4. Update docs

---

## 3. Runtime Layer Responsibilities

### `src/public/pointer.ts`

Owns:

* `parsePointer`
* `formatPointer`
* `get`

Key expectations:

* No semantic exceptions
* Clear separation between syntax errors and traversal errors
* No coercive behavior

### `src/public/reference.ts`

Owns:

* `resolveLocalRef`

Phase 1 behavior:

* `#` returns the whole document
* `#/...` resolves through pointer parsing plus `get`
* Other forms return `InvalidPointer`

---

## 4. Verification Stack

The repository uses several layers of development-time assurance.

### Unit tests

Target boundary behavior and edge cases directly.

### Property-based tests

`tests/pbt/get.pbt.test.ts` compares the runtime implementation with the
TypeScript spec model in `tests/pbt/spec_get.ts`.

### Python reference model

`verification/z3/spec.py` remains the simplest executable baseline for Phase 1
semantics. Keep it small and easy to inspect.

### Z3-backed oracle

`verification/z3/z3_model.py` evaluates concrete Phase 1 cases with SMT-backed
decision logic and reconstructs the final `Result<JSONValue>`.

`verification/z3/oracle.py` is the CLI adapter. During migration and debugging
it can dispatch to either:

* the Python baseline
* the Z3-backed oracle

### Differential verification

`verification/z3/diff.mjs` compares the built TypeScript implementation in
`dist/` against the oracle across the verification corpus.

### Counterexample search

`find_counterexample.py` and `find_counterexample_vocab.py` search for semantic
mismatches using bounded pools and solver-assisted selection.

---

## 5. How To Work On Semantics Safely

Recommended workflow:

1. Read the affected runtime file and matching tests
2. Re-read the semantics doc
3. Make the smallest behavior change that fits the contract
4. Update or add focused tests
5. Refresh verification tooling or corpus if the observable behavior changed
6. Run the smallest sufficient verification set

When touching pointer semantics, also inspect:

* array index classification
* escape / unescape handling
* `resolveLocalRef` edge cases

---

## 6. Verification Commands

Install dependencies:

```bash
npm install
python -m pip install -r verification/z3/requirements.txt
```

Build:

```bash
npm run build
```

Type-check:

```bash
npm run typecheck
```

Run tests:

```bash
npm run test:run
```

Run differential verification:

```bash
npm run verify:z3
```

Run Python-side parity checks directly:

```bash
python verification/z3/check_oracle_parity.py
python verification/z3/test_z3_model.py
```

Run counterexample search:

```bash
python verification/z3/find_counterexample.py
python verification/z3/find_counterexample_vocab.py
```

---

## 7. Editing Rules For Verification Tooling

When editing `verification/z3/`:

* Keep runtime semantics out of the verification layer
* Keep `spec.py` as a readable baseline, even if Z3 oracle coverage expands
* Do not silently change corpus meaning without refreshing generated cases
* Prefer one shared semantic source per concern rather than duplicating logic

Remember:

* `diff.mjs` reads from `dist/`, not `src/`
* the verifier is development-only
* performance matters, but semantic clarity matters more

---

## 8. Common Failure Modes

Watch for these mistakes:

* Treating bad array index tokens as `InvalidPointer`
* Returning `TypeMismatch` for missing object properties
* Collapsing `NotFound` and `TypeMismatch`
* Extending `resolveLocalRef` beyond `#` and `#/...` without updating docs and tests
* Changing runtime semantics without updating the verification corpus

---

## 9. Contribution Checklist

Before finishing semantic or verification work, verify:

* Public API remains intentionally small
* Result shapes are unchanged unless explicitly intended
* Runtime code stays pure and deterministic
* Tests cover the changed boundary
* Verification scripts still match the runtime contract
* English and Japanese docs remain aligned if documentation was updated

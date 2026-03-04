# AGENTS.md

## Purpose

This repository implements a small, verification-oriented core for JSON Reference handling in JSON Schema engines.

Current Phase 1 scope:

- JSON Pointer parsing and formatting (RFC 6901)
- Deterministic pointer evaluation over JSON values
- Local JSON Reference resolution for `#` and `#/...`

Out of scope unless the user explicitly asks for a scope expansion:

- Full JSON Schema validation
- External document loading or network fetching
- Full RFC 3986 URI resolution
- Rich error reporting beyond the current semantic result kinds

When making changes, optimize for semantic clarity and stability rather than feature breadth.

## Project Map

Core TypeScript implementation:

- `src/public/types.ts`: canonical `JSONValue`, `Pointer`, `Result`, and error kinds
- `src/public/pointer.ts`: `parsePointer`, `formatPointer`, `get`
- `src/public/reference.ts`: `resolveLocalRef`
- `src/internal/token.ts`: token escape/unescape rules
- `src/internal/arrayIndex.ts`: canonical array index parsing
- `src/public/index.ts`, `src/index.ts`: public exports

Tests:

- `tests/unit/*.test.ts`: unit coverage for edge cases and invariants
- `tests/pbt/get.pbt.test.ts`: property-based differential check between `get` and `specGet`
- `tests/pbt/spec_get.ts`: executable reference model for pointer traversal

Verification and proof artifacts:

- `verification/z3/`: corpus generation, oracle, and differential checking
- `verification/z3/diff.mjs`: compares built JS output in `dist/` against the oracle
- `proof/rocq/`: Rocq proofs and proof documentation

Docs:

- `README.md`: product-level overview and scope
- `CONTRIBUTING.md`: contribution constraints
- `docs/architecture/ARCHITECTURE.md`: layer boundaries and verification role
- `docs/architecture/SEMANTICS.md`: normative Phase 1 semantics

## Semantic Contract

Treat `docs/architecture/SEMANTICS.md` as the normative behavioral contract for Phase 1.

Important invariants visible in the current implementation:

- Internal pointer representation is `readonly string[]`
- The empty pointer string `""` maps to `[]`
- Non-empty pointer strings must start with `/`
- Token unescaping only accepts `~0` and `~1`
- Pointer evaluation is pure, deterministic, and left-to-right
- Array indices must be canonical base-10 non-negative integers
- Leading zeros are rejected except for `"0"`
- The semantic core must not throw; it returns `Result<T>`
- Error kinds are intentionally small and explicit: `InvalidPointer`, `TypeMismatch`, `NotFound`

Preserve these unless the task is explicitly about changing semantics. If semantics change, update code, tests, and the relevant docs together.

## Working Rules For Agents

Before changing behavior:

- Read the relevant implementation file plus the matching tests
- Check whether the behavior is already documented in `README.md`, `CONTRIBUTING.md`, or `docs/architecture/SEMANTICS.md`
- Distinguish syntax errors from traversal errors carefully; this codebase relies on that split

When editing implementation:

- Keep the core logic pure and side-effect free
- Avoid adding runtime dependencies
- Keep public API surface minimal; do not export new helpers unless necessary
- Prefer explicit branches over clever abstractions
- Preserve ESM import style with `.js` extension in TS source, matching the current build setup

When editing semantics:

- Update unit tests for the changed edge cases
- Update `tests/pbt/spec_get.ts` if `get` semantics changed
- Update the normative semantics doc if the observable contract changed
- Check whether verification scripts or corpora need refresh

When editing verification tooling:

- Remember `verification/` is development-only and not part of the runtime package
- `verification/z3/diff.mjs` reads from `dist/`, so build first
- The current Python oracle mirrors the traversal semantics and is the comparison baseline for `diff.mjs`

## Commands

Install dependencies:

```bash
npm install
```

Build:

```bash
npm run build
```

Type-check:

```bash
npm run typecheck
```

Run tests once:

```bash
npm run test:run
```

Run interactive tests:

```bash
npm test
```

Run Z3 differential verification:

```bash
npm run verify:z3
```

Notes:

- `verify:z3` runs `npm run build` first, then compares built output with the oracle
- Z3-related scripts may require Python dependencies from `verification/z3/requirements.txt`
- Example usage lives in `examples/smoke.ts` and assumes `dist/` has been built

## Testing Expectations

For a pure documentation change:

- No test run is required unless the user asks for it

For TypeScript implementation changes in `src/`:

- Run `npm run test:run`
- Run `npm run typecheck`

For changes affecting pointer traversal or result classification:

- Run `npm run test:run`
- Run `npm run typecheck`
- Run `npm run verify:z3` if environment dependencies are available

If you cannot run a verification step, say so explicitly in the final response.

## Common Pitfalls

- Do not classify array-token format failures as `InvalidPointer`; in current semantics they are `TypeMismatch`
- Do not treat missing object keys as `TypeMismatch`; they are `NotFound`
- Do not introduce implicit coercions for arrays, numbers, or object access
- Do not read from `dist/` as the source of truth when editing behavior; update `src/` instead
- Do not assume empty docs files under `docs/` contain authoritative guidance; rely on the populated files above

## Preferred Change Pattern

For behavioral work, use this order:

1. Read the relevant source and tests
2. Confirm the intended semantics from `docs/architecture/SEMANTICS.md`
3. Edit implementation
4. Edit or add tests
5. Update docs if behavior changed
6. Run the smallest sufficient verification set

## Review Checklist

Before finishing, verify:

- Public API remains intentionally small
- Result shapes and error kinds remain explicit
- Core functions stay pure and deterministic
- Tests cover the changed boundary condition
- Docs and implementation do not contradict each other

import json
import os
import subprocess
from typing import Any, Dict, List

from z3 import Int, Optimize, If, sat

from pools import DOCS, REFS_LIST, TOKENS_LIST
from spec import eval_case, kind_of_result
from z3_model import z3_eval_case

JSONValue = Any


def impl_kinds_batch(cases: List[Dict[str, Any]]) -> List[str]:
    inp = "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases).encode("utf-8")
    p = subprocess.run(
        ["node", "verification/z3/impl_kind.mjs"],
        input=inp,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if p.returncode != 0:
        raise RuntimeError(f"node failed: {p.stderr.decode('utf-8', errors='replace')}")

    out_lines = p.stdout.decode("utf-8", errors="replace").splitlines()
    kinds: List[str] = []
    for line in out_lines:
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        kinds.append(obj.get("kind", "InvalidPointer"))

    if len(kinds) != len(cases):
        raise RuntimeError(f"unexpected output lines: got {len(kinds)} expected {len(cases)}")
    return kinds


KIND_TO_INT = {"Ok": 0, "NotFound": 1, "TypeMismatch": 2, "InvalidPointer": 3}
INT_TO_KIND = {v: k for k, v in KIND_TO_INT.items()}


def doc_size(doc: JSONValue) -> int:
    if doc is None or isinstance(doc, (bool, int, float, str)):
        return 1
    if isinstance(doc, list):
        return 1 + sum(doc_size(x) for x in doc)
    if isinstance(doc, dict):
        return 1 + sum(doc_size(v) for v in doc.values())
    return 1


def path_cost(case: Dict[str, Any]) -> int:
    if case.get("op") == "resolveLocalRef":
        return len(case["ref"])
    return len(case["tokens"])


def op_cost(case: Dict[str, Any]) -> int:
    return 1 if case.get("op") == "resolveLocalRef" else 0


def build_cases() -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    for doc in DOCS:
        for tokens in TOKENS_LIST:
            cases.append({"op": "get", "doc": doc, "tokens": tokens})
        for ref in REFS_LIST:
            cases.append({"op": "resolveLocalRef", "doc": doc, "ref": ref})
    return cases


def piecewise_cost(case_var: Int, values: List[int]):
    expr = None
    for idx, value in enumerate(values):
        expr = If(case_var == idx, value, expr) if expr is not None else If(case_var == idx, value, value)
    return expr


def main():
    all_cases = build_cases()
    impl_kinds = impl_kinds_batch(all_cases)
    spec_kinds = [kind_of_result(eval_case(case)) for case in all_cases]

    if os.environ.get("CHECK_Z3_ORACLE") == "1":
        z3_kinds = [kind_of_result(z3_eval_case(case)) for case in all_cases]
        oracle_mismatches = [
            idx for idx, (spec_kind, z3_kind) in enumerate(zip(spec_kinds, z3_kinds)) if spec_kind != z3_kind
        ]
        if oracle_mismatches:
            idx = oracle_mismatches[0]
            raise RuntimeError(
                f"z3 oracle mismatch at case {idx}: spec={spec_kinds[idx]} z3={z3_kinds[idx]} "
                f"case={json.dumps(all_cases[idx], ensure_ascii=False)}"
            )

    mismatch_indices = [idx for idx, (impl, spec) in enumerate(zip(impl_kinds, spec_kinds)) if impl != spec]

    if not mismatch_indices:
        print("UNSAT: no counterexample in current pools.")
        return

    mismatch_cases = [all_cases[idx] for idx in mismatch_indices]
    mismatch_impl_kinds = [impl_kinds[idx] for idx in mismatch_indices]
    mismatch_spec_kinds = [spec_kinds[idx] for idx in mismatch_indices]

    case_var = Int("mismatch_idx")

    opt = Optimize()
    opt.add(case_var >= 0, case_var < len(mismatch_cases))
    opt.minimize(piecewise_cost(case_var, [path_cost(case) for case in mismatch_cases]))
    opt.minimize(piecewise_cost(case_var, [doc_size(case["doc"]) for case in mismatch_cases]))
    opt.minimize(piecewise_cost(case_var, [op_cost(case) for case in mismatch_cases]))

    result = opt.check()
    if result != sat:
        raise RuntimeError("expected SAT once mismatches are prefiltered")

    model = opt.model()
    idx = model[case_var].as_long()
    case = mismatch_cases[idx]
    impl_kind = mismatch_impl_kinds[idx]
    spec_kind = mismatch_spec_kinds[idx]

    print("SAT: found counterexample")
    print("case_idx:", idx)
    print("op:", case.get("op"))
    print("implKind:", impl_kind, "specKind:", spec_kind)
    print("case:", json.dumps(case, ensure_ascii=False))


if __name__ == "__main__":
    main()

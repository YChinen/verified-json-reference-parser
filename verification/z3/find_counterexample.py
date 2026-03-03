import json
import subprocess
from typing import Any, Dict, List, Tuple

from z3 import Int, Optimize, If, Or, sat

JSONValue = Any

# -----------------------------
# Candidate pools (reuse/align with find_cases.py)
# -----------------------------
DOCS: List[JSONValue] = [
    None, True, False, 0, 1, "", "a",
    [], [0], [1, 2], ["x", "y"],
    {}, {"a": 1}, {"": 123}, {"a": {"b": 2}}, {"a": ["x", "y"]}, {"a": {"": 9}},
    {"a": []}, {"a": [0]}, {"a": {"b": [1, 2]}},

    # success-path boosters
    {"a": {"b": [10, 20]}},
    {"a": [{"b": 1}, {"b": 2}]},
    {"": {"x": {"y": 3}}},
    [{"a": 1}, {"a": 2}],
    {"a": {"b": {"c": [0, 1]}}},
    {"a": {"": {"x": [7, 8]}}},
]

# --- nasty/edge-case boosters (object<->array alternation, empty keys, numeric-like keys) ---
DOCS += [
    {"a": [{"b": [0, 1]}, {"b": [2]}]},
    {"a": {"b": [{"c": 0}, {"c": 1}]}},
    {"": {"": [{"": 1}] }},
    [{"": {"a": [1]}}, {"": {"a": [2]}}],
    {"a": [[], [0], [0, 1]]},
    {"a": {"b": {"c": {"d": 1}}}},
    {"a": [{"b": {}}, {"b": {"c": 1}}]},
    {"a": {"0": [1, 2]}},
    {"a": {"01": [1]}},
    {"a": [{"01": 1}]},
]

TOKENS_LIST: List[List[str]] = [
    [], [""], ["a"], ["b"], ["missing"],
    ["a", "b"], ["a", ""], ["a", "missing"],
    ["a", "0"], ["a", "1"],
    ["0"], ["1"], ["01"], ["foo"],
    ["a", "01"], ["a", "foo"],
    ["a", "0", "b"], ["a", "1", "0"],

    # deeper success-paths
    ["a", "b", "0"],
    ["a", "b", "1"],
    ["a", "0", "b"],
    ["a", "1", "b"],
    ["", "x"],
    ["", "x", "y"],
    ["a", "", "x"],
    ["a", "b", "c", "1"],
]

# --- nasty token boosters (leading zeros, empty tokens, deeper paths) ---
TOKENS_LIST += [
    ["a", "0", "b", "0"],
    ["a", "0", "b", "01"],
    ["a", "0", "b", ""],
    ["a", "b", "c", "0"],
    ["a", "b", "c", "01"],
    ["", ""],
    ["", "0"],
    ["a", "00"],
    ["a", "000"],
    ["-0"],
    ["a", "-1"],
]

# -----------------------------
# Spec (python reference semantics)
# -----------------------------
def spec_parse_array_index_token(token: str):
    if token == "":
        return None
    if not token.isdigit():
        return None
    if len(token) > 1 and token[0] == "0":
        return None
    return int(token, 10)

def spec_kind(doc: JSONValue, tokens: List[str]) -> str:
    cur = doc
    for tok in tokens:
        if isinstance(cur, list):
            idx = spec_parse_array_index_token(tok)
            if idx is None:
                return "TypeMismatch"
            if idx < 0 or idx >= len(cur):
                return "NotFound"
            cur = cur[idx]
        elif isinstance(cur, dict):
            if tok not in cur:
                return "NotFound"
            cur = cur[tok]
        else:
            return "TypeMismatch"
    return "Ok"

# -----------------------------
# Impl (TS) kinds via Node batch
# -----------------------------
def impl_kinds_batch(cases: List[Dict[str, Any]]) -> List[str]:
    """
    Calls node verification/z3/impl_kind.mjs
    Input: JSONL of {doc,tokens}
    Output: JSONL of {kind}
    """
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

# -----------------------------
# Z3 model: choose (d, t) s.t. impl != spec, minimize size
# -----------------------------
KIND_TO_INT = {"Ok": 0, "NotFound": 1, "TypeMismatch": 2, "InvalidPointer": 3}
INT_TO_KIND = {v: k for k, v in KIND_TO_INT.items()}

def doc_size(doc: JSONValue) -> int:
    # very rough "complexity" metric for minimization
    if doc is None or isinstance(doc, (bool, int, float, str)):
        return 1
    if isinstance(doc, list):
        return 1 + sum(doc_size(x) for x in doc)
    if isinstance(doc, dict):
        return 1 + sum(doc_size(v) for v in doc.values())
    return 1

def main():
    # Build full tables
    all_cases: List[Dict[str, Any]] = []
    for di, d in enumerate(DOCS):
        for ti, toks in enumerate(TOKENS_LIST):
            all_cases.append({"doc": d, "tokens": toks})

    implKinds = impl_kinds_batch(all_cases)

    # Build specKinds in the same ordering
    specKinds: List[str] = []
    for di, d in enumerate(DOCS):
        for ti, toks in enumerate(TOKENS_LIST):
            specKinds.append(spec_kind(d, toks))

    # Create Z3 vars
    d = Int("d")
    t = Int("t")

    opt = Optimize()
    opt.add(d >= 0, d < len(DOCS))
    opt.add(t >= 0, t < len(TOKENS_LIST))

    # encode impl/spec kind as piecewise constants of (d,t)
    # Since pools are finite, we can use a big If-chain safely at this size.
    def kind_at(table: List[str]):
        expr = None
        idx = 0
        for di in range(len(DOCS)):
            for ti in range(len(TOKENS_LIST)):
                k = KIND_TO_INT[table[idx]]
                cond = (d == di) & (t == ti)
                expr = If(cond, k, expr) if expr is not None else If(cond, k, k)
                idx += 1
        return expr

    implExpr = kind_at(implKinds)
    specExpr = kind_at(specKinds)

    # mismatch constraint
    opt.add(implExpr != specExpr)

    # minimize token length then doc complexity
    tokLens = [len(x) for x in TOKENS_LIST]
    docSizes = [doc_size(x) for x in DOCS]

    tokLenExpr = None
    for ti, L in enumerate(tokLens):
        tokLenExpr = If(t == ti, L, tokLenExpr) if tokLenExpr is not None else If(t == ti, L, L)

    docSizeExpr = None
    for di, S in enumerate(docSizes):
        docSizeExpr = If(d == di, S, docSizeExpr) if docSizeExpr is not None else If(d == di, S, S)

    opt.minimize(tokLenExpr)
    opt.minimize(docSizeExpr)

    r = opt.check()
    if r != sat:
        print("UNSAT: no counterexample in current pools.")
        return

    m = opt.model()
    di = m[d].as_long()
    ti = m[t].as_long()

    case = {"doc": DOCS[di], "tokens": TOKENS_LIST[ti]}
    implK = implKinds[di * len(TOKENS_LIST) + ti]
    specK = specKinds[di * len(TOKENS_LIST) + ti]

    print("SAT: found counterexample")
    print("doc_idx:", di, "tok_idx:", ti)
    print("implKind:", implK, "specKind:", specK)
    print("case:", json.dumps(case, ensure_ascii=False))

if __name__ == "__main__":
    main()
import json
from typing import Any, Dict, List, Tuple

from z3 import Int, Solver, sat, Or

# --- Import oracle semantics (python implementation) ---
# Keep oracle semantics in one place. If you have oracle.py, you can import from it.
def err(kind: str) -> Dict[str, Any]:
    return {"ok": False, "kind": kind}

def ok(value: Any) -> Dict[str, Any]:
    return {"ok": True, "value": value}

def parse_array_index_token(token: str):
    if token == "":
        return None
    if not token.isdigit():
        return None
    if len(token) > 1 and token[0] == "0":
        return None
    return int(token, 10)

def py_get(doc: Any, tokens: List[str]) -> Dict[str, Any]:
    cur = doc
    for token in tokens:
        if isinstance(cur, list):
            idx = parse_array_index_token(token)
            if idx is None:
                return err("TypeMismatch")
            if idx < 0 or idx >= len(cur):
                return err("NotFound")
            cur = cur[idx]
        elif isinstance(cur, dict):
            if token not in cur:
                return err("NotFound")
            cur = cur[token]
        else:
            return err("TypeMismatch")
    return ok(cur)

# --- Candidate pool (small, nasty, high-signal) ---
DOCS: List[Any] = [
    None,
    True,
    False,
    0,
    1,
    "",
    "a",
    [],
    [0],
    [1, 2],
    ["x", "y"],
    {},
    {"a": 1},
    {"": 123},
    {"a": {"b": 2}},
    {"a": ["x", "y"]},
    {"a": {"": 9}},
    {"a": []},
    {"a": [0]},
    {"a": {"b": [1, 2]}},
]

DOCS += [
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
    [],                 # whole doc
    [""],               # empty-key
    ["a"],
    ["b"],
    ["missing"],
    ["a", "b"],
    ["a", ""],
    ["a", "missing"],
    ["a", "0"],
    ["a", "1"],
    ["0"],              # array index at root
    ["1"],
    ["01"],             # leading zero: TypeMismatch (array only)
    ["foo"],            # TypeMismatch (array only)
    ["a", "01"],        # leading zero under array
    ["a", "foo"],       # TypeMismatch under array
    ["a", "0", "b"],    # traverse into primitive etc.
    ["a", "1", "0"],
]

TOKENS_LIST += [
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

def to_case(doc_idx: int, tok_idx: int) -> Dict[str, Any]:
    return {"doc": DOCS[doc_idx], "tokens": TOKENS_LIST[tok_idx]}

def main():
    out_path = "verification/z3/corpus/generated.jsonl"
    max_cases = 500

    # Coverage targets: try to ensure we have examples for each kind
    targets = {"Ok": 100, "NotFound": 130, "TypeMismatch": 150}
    counts = {"Ok": 0, "NotFound": 0, "TypeMismatch": 0}

    s = Solver()
    d = Int("d")
    t = Int("t")

    s.add(d >= 0, d < len(DOCS))
    s.add(t >= 0, t < len(TOKENS_LIST))

    # Block already-produced (d,t) pairs
    blocks: List[Any] = []

    produced: List[Dict[str, Any]] = []

    while len(produced) < max_cases and s.check() == sat:
        m = s.model()
        di = m[d].as_long()
        ti = m[t].as_long()

        case = to_case(di, ti)
        res = py_get(case["doc"], case["tokens"])

        # Classify by kind
        if res["ok"]:
            k = "Ok"
        else:
            k = res["kind"]

        # Heuristic: focus on NotFound / TypeMismatch, but keep some Ok
        accept = True
        if k in counts and counts[k] >= targets.get(k, 0):
            # deprioritize if target reached
            accept = False

        if accept:
            produced.append(case)
            counts[k] = counts.get(k, 0) + 1

        # block this exact pair to enumerate next
        blocks.append(Or(d != di, t != ti))
        s.add(blocks[-1])

    # Write (overwrite) corpus
    with open(out_path, "w", encoding="utf-8") as f:
        for c in produced:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"wrote {len(produced)} cases -> {out_path}")
    print("coverage:", counts)

if __name__ == "__main__":
    main()
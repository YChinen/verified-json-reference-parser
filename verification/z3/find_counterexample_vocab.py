import json
import subprocess
from typing import Any, Dict, List, Tuple

from z3 import Int, Optimize, If, sat

JSONValue = Any

# -----------------------------
# Pools
# -----------------------------
DOCS: List[JSONValue] = [
    None, True, False, 0, 1, "", "a",
    [], [0], [1, 2], ["x", "y"],
    {}, {"a": 1}, {"": 123}, {"a": {"b": 2}}, {"a": ["x", "y"]}, {"a": {"": 9}},
    {"a": []}, {"a": [0]}, {"a": {"b": [1, 2]}},

    # boosters
    {"a": {"b": [10, 20]}},
    {"a": [{"b": 1}, {"b": 2}]},
    {"": {"x": {"y": 3}}},
    [{"a": 1}, {"a": 2}],
    {"a": {"b": {"c": [0, 1]}}},
    {"a": {"": {"x": [7, 8]}}},
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

# token vocabulary (unescaped tokens)
VOCAB: List[str] = ["", "a", "b", "c", "0", "1", "01", "00", "foo", "-1", "-0"]

MAX_LEN = 6  # token length upper bound

# -----------------------------
# Spec semantics (kind only)
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
# Impl kinds via Node batch (TS dist)
# -----------------------------
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

# -----------------------------
# Enumerate tokens via vocab indices
# -----------------------------
def decode_tokens(L: int, idxs: List[int]) -> List[str]:
    return [VOCAB[idxs[i]] for i in range(L)]

def token_len_cost(L: int) -> int:
    return L

def token_lex_cost(L: int, idxs: List[int]) -> int:
    # a small lexicographic cost to bias toward smaller indices after length minimization
    base = len(VOCAB)
    cost = 0
    for i in range(L):
        cost = cost * base + idxs[i]
    return cost

# -----------------------------
# Z3 helper: piecewise select a table entry by (d, L, v0..v5)
# -----------------------------
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

def main():
    # Build evaluation table for all combinations:
    # doc_idx in [0..|DOCS|-1]
    # L in [0..MAX_LEN]
    # v0..v5 in [0..|VOCAB|-1]
    #
    # NOTE: total combos = |DOCS| * sum_{L=0..MAX_LEN} |VOCAB|^L
    # With MAX_LEN=6 and |VOCAB|=11, this is large.
    # So we will cap enumeration by sampling v-tuples per L (still Z3-minimizable).
    #
    # Practical strategy:
    # - fully enumerate L=0..3
    # - sample for L=4..6
    FULL_ENUM_UP_TO = 3
    SAMPLES_PER_L = 2000

    tables: List[Tuple[int,int,Tuple[int,...],str,str]] = []
    cases_for_impl: List[Dict[str, Any]] = []

    import random
    random.seed(0)

    for di, doc in enumerate(DOCS):
        for L in range(0, MAX_LEN + 1):
            if L <= FULL_ENUM_UP_TO:
                # full enumeration for this L
                total = len(VOCAB) ** L
                for n in range(total):
                    idxs = []
                    x = n
                    for _ in range(L):
                        idxs.append(x % len(VOCAB))
                        x //= len(VOCAB)
                    idxs_t = tuple(idxs)
                    toks = decode_tokens(L, idxs)
                    sk = spec_kind(doc, toks)
                    tables.append((di, L, idxs_t, sk, ""))  # impl to fill later
                    cases_for_impl.append({"doc": doc, "tokens": toks})
            else:
                # sample
                for _ in range(SAMPLES_PER_L):
                    idxs = tuple(random.randrange(0, len(VOCAB)) for _ in range(L))
                    toks = decode_tokens(L, list(idxs))
                    sk = spec_kind(doc, toks)
                    tables.append((di, L, idxs, sk, ""))
                    cases_for_impl.append({"doc": doc, "tokens": toks})

    # Batch compute impl kinds for all cases
    implKinds = impl_kinds_batch(cases_for_impl)

    # Fill impl kinds into table
    filled: List[Tuple[int,int,Tuple[int,...],int,int]] = []
    for i, (di, L, idxs, sk, _) in enumerate(tables):
        ik = implKinds[i]
        filled.append((di, L, idxs, KIND_TO_INT.get(ik, 3), KIND_TO_INT[sk]))

    # Z3 vars
    d = Int("d")
    Lz = Int("L")
    vs = [Int(f"v{i}") for i in range(MAX_LEN)]  # v0..v5

    opt = Optimize()
    opt.add(d >= 0, d < len(DOCS))
    opt.add(Lz >= 0, Lz <= MAX_LEN)
    for v in vs:
        opt.add(v >= 0, v < len(VOCAB))

    # piecewise table select
    implExpr = None
    specExpr = None

    def cond_for(di: int, L: int, idxs: Tuple[int,...]):
        c = (d == di) & (Lz == L)
        for i in range(L):
            c = c & (vs[i] == idxs[i])
        # For i >= L, don't care
        return c

    for (di, L, idxs, implK, specK) in filled:
        c = cond_for(di, L, idxs)
        if implExpr is None:
            implExpr = If(c, implK, implK)
            specExpr = If(c, specK, specK)
        else:
            implExpr = If(c, implK, implExpr)
            specExpr = If(c, specK, specExpr)

    # mismatch constraint
    opt.add(implExpr != specExpr)

    # minimize: token length, then doc size, then lex of tokens (by indices)
    docSizes = [doc_size(x) for x in DOCS]
    docSizeExpr = None
    for di, S in enumerate(docSizes):
        docSizeExpr = If(d == di, S, docSizeExpr) if docSizeExpr is not None else If(d == di, S, S)

    # lex cost (only meaningful up to L)
    base = len(VOCAB)
    lexExpr = 0
    for i in range(MAX_LEN):
        lexExpr = If(Lz > i, lexExpr * base + vs[i], lexExpr)

    opt.minimize(Lz)
    opt.minimize(docSizeExpr)
    opt.minimize(lexExpr)

    r = opt.check()
    if r != sat:
        print("UNSAT: no counterexample in current (doc pool x vocab sampling) space.")
        return

    m = opt.model()
    di = m[d].as_long()
    L = m[Lz].as_long()
    idxs = [m[vs[i]].as_long() for i in range(L)]
    toks = decode_tokens(L, idxs)

    # Evaluate true kinds for display (ground)
    implK = None
    specK = None

    # Find matching row in filled table (exact match)
    for (rdi, rL, ridxs, iK, sK) in filled:
        if rdi == di and rL == L and tuple(idxs) == ridxs:
            implK = INT_TO_KIND[iK]
            specK = INT_TO_KIND[sK]
            break

    case = {"doc": DOCS[di], "tokens": toks}
    print("SAT: found counterexample")
    print("doc_idx:", di, "L:", L, "idxs:", idxs)
    print("implKind:", implK, "specKind:", specK)
    print("case:", json.dumps(case, ensure_ascii=False))

if __name__ == "__main__":
    main()
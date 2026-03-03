import json
import sys
from typing import Any, Dict, List

from z3 import Int, Bool, If, Solver, sat

JSONValue = Any

def ok(value: JSONValue) -> Dict[str, Any]:
    return {"ok": True, "value": value}

def err(kind: str) -> Dict[str, Any]:
    return {"ok": False, "kind": kind}

def parse_array_index_token(token: str):
    if token == "":
        return None
    if not token.isdigit():
        return None
    if len(token) > 1 and token[0] == "0":
        return None
    return int(token, 10)

def py_get(doc: JSONValue, tokens: List[str]) -> Dict[str, Any]:
    # This is the semantic oracle entrypoint, but we will compute kind using Z3-shaped logic.
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

def main():
    line = sys.stdin.readline()
    if not line:
        print(json.dumps(err("InvalidPointer")))
        return

    case = json.loads(line)
    doc = case.get("doc")
    tokens = case.get("tokens")

    if not isinstance(tokens, list) or not all(isinstance(t, str) for t in tokens):
        print(json.dumps(err("InvalidPointer"), ensure_ascii=False))
        return

    # For now: return full value like TS expects.
    # (Z3 will be introduced in the next step as a symbolic counterexample finder.)
    out = py_get(doc, tokens)
    print(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main()
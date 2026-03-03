# verification/z3/oracle.py
import json
import sys
from typing import Any, Dict, List, Union

JSONValue = Any

def ok(value):
    return {"ok": True, "value": value}

def err(kind):
    return {"ok": False, "kind": kind}

def is_object(x):
    return isinstance(x, dict)

def is_array(x):
    return isinstance(x, list)

def parse_array_index_token(token: str):
    # digits only
    if token == "":
        return None
    if not token.isdigit():
        return None
    # no leading zeros unless exactly "0"
    if len(token) > 1 and token[0] == "0":
        return None
    # safe integer check (Python int is unbounded; keep it simple)
    return int(token, 10)

def get(doc: JSONValue, tokens: List[str]) -> Dict[str, Any]:
    cur = doc
    for token in tokens:
        if is_array(cur):
            idx = parse_array_index_token(token)
            if idx is None:
                return err("TypeMismatch")
            if idx < 0 or idx >= len(cur):
                return err("NotFound")
            cur = cur[idx]
            continue

        if is_object(cur):
            if token not in cur:
                return err("NotFound")
            cur = cur[token]
            continue

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
        print(json.dumps(err("InvalidPointer")))
        return

    print(json.dumps(get(doc, tokens), ensure_ascii=False))

if __name__ == "__main__":
    main()
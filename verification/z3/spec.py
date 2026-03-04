from typing import Any, Dict, List, Optional, Sequence

JSONValue = Any
Result = Dict[str, Any]


def ok(value: JSONValue) -> Result:
    return {"ok": True, "value": value}


def err(kind: str) -> Result:
    return {"ok": False, "kind": kind}


def kind_of_result(result: Result) -> str:
    return "Ok" if result.get("ok") else result.get("kind", "InvalidPointer")


def parse_array_index_token(token: str) -> Optional[int]:
    if token == "":
        return None
    if not token.isdigit():
        return None
    if len(token) > 1 and token[0] == "0":
        return None
    return int(token, 10)


def escape_token(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def format_pointer(tokens: Sequence[str]) -> str:
    if not tokens:
        return ""
    return "/" + "/".join(escape_token(token) for token in tokens)


def unescape_token(token: str) -> Result:
    out: List[str] = []
    i = 0
    while i < len(token):
        c = token[i]
        if c != "~":
            out.append(c)
            i += 1
            continue

        if i + 1 >= len(token):
            return err("InvalidPointer")

        nxt = token[i + 1]
        if nxt == "0":
            out.append("~")
        elif nxt == "1":
            out.append("/")
        else:
            return err("InvalidPointer")
        i += 2

    return ok("".join(out))


def parse_pointer(pointer_string: str) -> Result:
    if pointer_string == "":
        return ok([])

    if not isinstance(pointer_string, str) or not pointer_string.startswith("/"):
        return err("InvalidPointer")

    raw_segments = pointer_string.split("/")[1:]
    tokens: List[str] = []
    for segment in raw_segments:
        unescaped = unescape_token(segment)
        if not unescaped["ok"]:
            return unescaped
        tokens.append(unescaped["value"])

    return ok(tokens)


def get_result(doc: JSONValue, tokens: Sequence[str]) -> Result:
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


def resolve_local_ref(doc: JSONValue, ref_string: str) -> Result:
    if ref_string == "#":
        return ok(doc)

    if not isinstance(ref_string, str):
        return err("InvalidPointer")

    if ref_string.startswith("#/"):
        parsed = parse_pointer(ref_string[1:])
        if not parsed["ok"]:
            return parsed
        return get_result(doc, parsed["value"])

    return err("InvalidPointer")


def eval_case(case: Dict[str, Any]) -> Result:
    if not isinstance(case, dict) or "doc" not in case:
        return err("InvalidPointer")

    op = case.get("op")
    if op is None:
        if "tokens" in case:
            op = "get"
        elif "ref" in case:
            op = "resolveLocalRef"

    if op == "get":
        tokens = case.get("tokens")
        if not isinstance(tokens, list) or not all(isinstance(t, str) for t in tokens):
            return err("InvalidPointer")
        return get_result(case.get("doc"), tokens)

    if op == "resolveLocalRef":
        ref = case.get("ref")
        if not isinstance(ref, str):
            return err("InvalidPointer")
        return resolve_local_ref(case.get("doc"), ref)

    return err("InvalidPointer")

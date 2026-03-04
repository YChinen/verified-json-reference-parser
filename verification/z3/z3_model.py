from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from z3 import And, BoolRef, If, Int, IntNumRef, IntVal, Or, Solver, sat

from spec import err, ok

JSONValue = Any
Result = Dict[str, Any]

NODE_NULL = 0
NODE_BOOL = 1
NODE_NUMBER = 2
NODE_STRING = 3
NODE_ARRAY = 4
NODE_OBJECT = 5

ERR_NONE = 0
ERR_INVALID_POINTER = 1
ERR_TYPE_MISMATCH = 2
ERR_NOT_FOUND = 3

ERR_INT_TO_KIND = {
    ERR_INVALID_POINTER: "InvalidPointer",
    ERR_TYPE_MISMATCH: "TypeMismatch",
    ERR_NOT_FOUND: "NotFound",
}


@dataclass(frozen=True)
class FlattenedDoc:
    root_id: int
    node_kinds: List[int]
    node_values: List[JSONValue]
    array_edges_by_index: Dict[int, List[tuple[int, int]]]
    object_edges_by_key: Dict[str, List[tuple[int, int]]]


@dataclass(frozen=True)
class ParseResult:
    ok: bool
    kind: Optional[str]
    tokens: Optional[List[str]]


@dataclass(frozen=True)
class EvalResult:
    ok: bool
    kind: Optional[str]
    target_node_id: Optional[int]


def flatten_doc(doc: JSONValue) -> FlattenedDoc:
    node_kinds: List[int] = []
    node_values: List[JSONValue] = []
    array_edges_by_index: Dict[int, List[tuple[int, int]]] = {}
    object_edges_by_key: Dict[str, List[tuple[int, int]]] = {}

    def visit(value: JSONValue) -> int:
        node_id = len(node_kinds)
        node_values.append(value)

        if value is None:
            node_kinds.append(NODE_NULL)
            return node_id
        if isinstance(value, bool):
            node_kinds.append(NODE_BOOL)
            return node_id
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            node_kinds.append(NODE_NUMBER)
            return node_id
        if isinstance(value, str):
            node_kinds.append(NODE_STRING)
            return node_id
        if isinstance(value, list):
            node_kinds.append(NODE_ARRAY)
            for index, child in enumerate(value):
                child_id = visit(child)
                array_edges_by_index.setdefault(index, []).append((node_id, child_id))
            return node_id
        if isinstance(value, dict):
            node_kinds.append(NODE_OBJECT)
            for key, child in value.items():
                child_id = visit(child)
                object_edges_by_key.setdefault(key, []).append((node_id, child_id))
            return node_id
        raise TypeError(f"unsupported JSON value: {type(value)!r}")

    root_id = visit(doc)
    return FlattenedDoc(
        root_id=root_id,
        node_kinds=node_kinds,
        node_values=node_values,
        array_edges_by_index=array_edges_by_index,
        object_edges_by_key=object_edges_by_key,
    )


def lookup_array_child(flat_doc: FlattenedDoc, node_id: int, index: int) -> Optional[int]:
    for parent_id, child_id in flat_doc.array_edges_by_index.get(index, []):
        if parent_id == node_id:
            return child_id
    return None


def lookup_object_child(flat_doc: FlattenedDoc, node_id: int, key: str) -> Optional[int]:
    for parent_id, child_id in flat_doc.object_edges_by_key.get(key, []):
        if parent_id == node_id:
            return child_id
    return None


def _node_kind_expr(flat_doc: FlattenedDoc, node_var):
    expr = IntVal(flat_doc.node_kinds[0])
    for node_id, kind in enumerate(flat_doc.node_kinds):
        expr = If(node_var == node_id, IntVal(kind), expr)
    return expr


def _array_child_exists_expr(flat_doc: FlattenedDoc, node_var, index: int) -> BoolRef:
    edges = flat_doc.array_edges_by_index.get(index, [])
    if not edges:
        return Or(False)
    return Or(*[node_var == parent_id for parent_id, _ in edges])


def _array_child_expr(flat_doc: FlattenedDoc, node_var, index: int):
    edges = flat_doc.array_edges_by_index.get(index, [])
    expr = node_var
    for parent_id, child_id in edges:
        expr = If(node_var == parent_id, IntVal(child_id), expr)
    return expr


def _object_child_exists_expr(flat_doc: FlattenedDoc, node_var, key: str) -> BoolRef:
    edges = flat_doc.object_edges_by_key.get(key, [])
    if not edges:
        return Or(False)
    return Or(*[node_var == parent_id for parent_id, _ in edges])


def _object_child_expr(flat_doc: FlattenedDoc, node_var, key: str):
    edges = flat_doc.object_edges_by_key.get(key, [])
    expr = node_var
    for parent_id, child_id in edges:
        expr = If(node_var == parent_id, IntVal(child_id), expr)
    return expr


def _char_vars(solver: Solver, prefix: str, text: str):
    vars_: List[Any] = []
    for idx, ch in enumerate(text):
        var = Int(f"{prefix}_char_{idx}")
        solver.add(var == ord(ch))
        vars_.append(var)
    return vars_


def _decode_valid_segment(segment: str) -> str:
    out: List[str] = []
    i = 0
    while i < len(segment):
        ch = segment[i]
        if ch != "~":
            out.append(ch)
            i += 1
            continue
        nxt = segment[i + 1]
        out.append("~" if nxt == "0" else "/")
        i += 2
    return "".join(out)


def z3_parse_array_index_token(token: str, prefix: str) -> tuple[bool, Optional[int]]:
    solver = Solver()
    valid_var = Int(f"{prefix}_valid")
    index_var = Int(f"{prefix}_value")

    chars = _char_vars(solver, prefix, token)
    digit_checks = [And(ch >= ord("0"), ch <= ord("9")) for ch in chars]
    no_leading_zero = True
    if len(chars) > 1:
        no_leading_zero = chars[0] != ord("0")

    valid_expr = And(len(chars) > 0, *digit_checks, no_leading_zero)
    solver.add(valid_var == If(valid_expr, IntVal(1), IntVal(0)))

    parsed_index = int(token, 10) if token.isdigit() and token else -1
    safe_expr = parsed_index >= 0 and parsed_index <= (2**53 - 1)
    index_value = parsed_index if safe_expr else -1
    solver.add(index_var == If(valid_expr, IntVal(index_value), IntVal(-1)))

    if solver.check() != sat:
        return False, None

    model = solver.model()
    is_valid = model[valid_var].as_long() == 1
    if not is_valid or index_value < 0:
        return False, None
    return True, model[index_var].as_long()


def z3_parse_pointer(pointer_string: str) -> ParseResult:
    if pointer_string == "":
        return ParseResult(ok=True, kind=None, tokens=[])

    solver = Solver()
    prefix_ok = Int("pointer_prefix_ok")
    solver.add(prefix_ok == If(pointer_string.startswith("/"), IntVal(1), IntVal(0)))
    solver.add(prefix_ok == 1)

    raw_segments = pointer_string.split("/")[1:]

    for seg_idx, segment in enumerate(raw_segments):
        chars = _char_vars(solver, f"segment_{seg_idx}", segment)
        for char_idx, char_var in enumerate(chars):
            if char_idx + 1 < len(chars):
                next_var = chars[char_idx + 1]
                solver.add(
                    If(
                        char_var == ord("~"),
                        Or(next_var == ord("0"), next_var == ord("1")),
                        True,
                    )
                )
            else:
                solver.add(If(char_var == ord("~"), False, True))

    if solver.check() != sat:
        return ParseResult(ok=False, kind="InvalidPointer", tokens=None)

    decoded_tokens = [_decode_valid_segment(segment) for segment in raw_segments]
    return ParseResult(ok=True, kind=None, tokens=decoded_tokens)


def z3_eval_tokens(flat_doc: FlattenedDoc, tokens: Sequence[str]) -> EvalResult:
    solver = Solver()
    cur_vars = [Int(f"cur_{idx}") for idx in range(len(tokens) + 1)]
    err_vars = [Int(f"err_{idx}") for idx in range(len(tokens) + 1)]

    solver.add(cur_vars[0] == flat_doc.root_id)
    solver.add(err_vars[0] == ERR_NONE)

    for idx, token in enumerate(tokens):
        cur_var = cur_vars[idx]
        next_cur_var = cur_vars[idx + 1]
        err_var = err_vars[idx]
        next_err_var = err_vars[idx + 1]

        node_kind = _node_kind_expr(flat_doc, cur_var)
        index_valid, index_value = z3_parse_array_index_token(token, f"step_{idx}_index")
        lookup_index = index_value if index_value is not None else -1
        has_array_child = _array_child_exists_expr(flat_doc, cur_var, lookup_index) if index_valid else Or(False)
        array_child = _array_child_expr(flat_doc, cur_var, lookup_index)
        has_object_child = _object_child_exists_expr(flat_doc, cur_var, token)
        object_child = _object_child_expr(flat_doc, cur_var, token)

        step_error = If(
            node_kind == NODE_ARRAY,
            If(
                index_valid,
                If(has_array_child, IntVal(ERR_NONE), IntVal(ERR_NOT_FOUND)),
                IntVal(ERR_TYPE_MISMATCH),
            ),
            If(
                node_kind == NODE_OBJECT,
                If(has_object_child, IntVal(ERR_NONE), IntVal(ERR_NOT_FOUND)),
                IntVal(ERR_TYPE_MISMATCH),
            ),
        )

        step_target = If(
            node_kind == NODE_ARRAY,
            array_child,
            If(node_kind == NODE_OBJECT, object_child, cur_var),
        )

        solver.add(next_err_var == If(err_var != ERR_NONE, err_var, step_error))
        solver.add(next_cur_var == If(err_var != ERR_NONE, cur_var, If(step_error == ERR_NONE, step_target, cur_var)))

    if solver.check() != sat:
        return EvalResult(ok=False, kind="InvalidPointer", target_node_id=None)

    model = solver.model()
    final_err = model.eval(err_vars[-1], model_completion=True)
    final_err_value = final_err.as_long() if isinstance(final_err, IntNumRef) else ERR_INVALID_POINTER
    if final_err_value != ERR_NONE:
        return EvalResult(ok=False, kind=ERR_INT_TO_KIND[final_err_value], target_node_id=None)

    target = model.eval(cur_vars[-1], model_completion=True)
    target_node_id = target.as_long() if isinstance(target, IntNumRef) else flat_doc.root_id
    return EvalResult(ok=True, kind=None, target_node_id=target_node_id)


def z3_eval_get(doc: JSONValue, tokens: Sequence[str]) -> Result:
    if not isinstance(tokens, list) or not all(isinstance(token, str) for token in tokens):
        return err("InvalidPointer")

    flat_doc = flatten_doc(doc)
    eval_result = z3_eval_tokens(flat_doc, tokens)
    if not eval_result.ok:
        return err(eval_result.kind or "InvalidPointer")
    return ok(flat_doc.node_values[eval_result.target_node_id])


def z3_eval_resolve_local_ref(doc: JSONValue, ref_string: str) -> Result:
    if ref_string == "#":
        return ok(doc)

    if not isinstance(ref_string, str):
        return err("InvalidPointer")

    if not ref_string.startswith("#/"):
        return err("InvalidPointer")

    parse_result = z3_parse_pointer(ref_string[1:])
    if not parse_result.ok:
        return err(parse_result.kind or "InvalidPointer")

    return z3_eval_get(doc, parse_result.tokens or [])


def z3_eval_case(case: Dict[str, Any]) -> Result:
    if not isinstance(case, dict) or "doc" not in case:
        return err("InvalidPointer")

    op = case.get("op")
    if op is None:
        if "tokens" in case:
            op = "get"
        elif "ref" in case:
            op = "resolveLocalRef"

    if op == "get":
        return z3_eval_get(case.get("doc"), case.get("tokens"))

    if op == "resolveLocalRef":
        return z3_eval_resolve_local_ref(case.get("doc"), case.get("ref"))

    return err("InvalidPointer")

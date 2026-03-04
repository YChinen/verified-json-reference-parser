from typing import Any, Dict, List, Set

from spec import format_pointer

JSONValue = Any


DOCS: List[JSONValue] = [
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
    {"a": {"b": [10, 20]}},
    {"a": [{"b": 1}, {"b": 2}]},
    {"": {"x": {"y": 3}}},
    [{"a": 1}, {"a": 2}],
    {"a": {"b": {"c": [0, 1]}}},
    {"a": {"": {"x": [7, 8]}}},
    {"a": [{"b": [0, 1]}, {"b": [2]}]},
    {"a": {"b": [{"c": 0}, {"c": 1}]}},
    {"": {"": [{"": 1}]}},
    [{"": {"a": [1]}}, {"": {"a": [2]}}],
    {"a": [[], [0], [0, 1]]},
    {"a": {"b": {"c": {"d": 1}}}},
    {"a": [{"b": {}}, {"b": {"c": 1}}]},
    {"a": {"0": [1, 2]}},
    {"a": {"01": [1]}},
    {"a": [{"01": 1}]},
    {"a": {"~": 1, "/": 2}},
    {"a": {"b/c": 3, "d~e": 4}},
]


TOKENS_LIST: List[List[str]] = [
    [],
    [""],
    ["a"],
    ["b"],
    ["missing"],
    ["a", "b"],
    ["a", ""],
    ["a", "missing"],
    ["a", "0"],
    ["a", "1"],
    ["0"],
    ["1"],
    ["01"],
    ["foo"],
    ["a", "01"],
    ["a", "foo"],
    ["a", "0", "b"],
    ["a", "1", "0"],
    ["a", "b", "0"],
    ["a", "b", "1"],
    ["a", "1", "b"],
    ["", "x"],
    ["", "x", "y"],
    ["a", "", "x"],
    ["a", "b", "c", "1"],
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
    ["a", "~"],
    ["a", "/"],
    ["a", "b/c"],
    ["a", "d~e"],
]


REF_POINTER_TOKENS: List[List[str]] = [
    [],
    [""],
    ["a"],
    ["b"],
    ["missing"],
    ["a", "b"],
    ["a", ""],
    ["a", "missing"],
    ["a", "0"],
    ["a", "1"],
    ["0"],
    ["1"],
    ["01"],
    ["foo"],
    ["a", "01"],
    ["a", "foo"],
    ["a", "0", "b"],
    ["a", "1", "0"],
    ["a", "b", "0"],
    ["a", "b", "1"],
    ["a", "1", "b"],
    ["", "x"],
    ["", "x", "y"],
    ["a", "", "x"],
    ["a", "b", "c", "1"],
    ["a", "~"],
    ["a", "/"],
    ["a", "b/c"],
    ["a", "d~e"],
]


RAW_INVALID_REFS = [
    "",
    "#foo",
    "other.json#/a",
    "http://x/y#/a",
    "#/~2",
    "#/~",
    "#/a/~2",
    "#/a/~",
]


def make_ref_list() -> List[str]:
    refs = ["#"]
    seen: Set[str] = {"#"}

    for tokens in REF_POINTER_TOKENS:
        ref = "#" + format_pointer(tokens)
        if ref in seen:
            continue
        refs.append(ref)
        seen.add(ref)

    for ref in RAW_INVALID_REFS:
        if ref in seen:
            continue
        refs.append(ref)
        seen.add(ref)

    return refs


REFS_LIST = make_ref_list()

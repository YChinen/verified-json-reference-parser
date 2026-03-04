import json
import os
import sys
from typing import Any, Dict, Iterable, List

from spec import eval_case
from z3_model import z3_eval_case

CORPUS_PATHS = [
    "verification/z3/corpus/seed.jsonl",
    "verification/z3/corpus/generated.jsonl",
    "verification/z3/corpus/regression.jsonl",
]

EXTRA_CASES: List[Dict[str, Any]] = [
    {"op": "resolveLocalRef", "doc": {"a": {"~": 1, "/": 2}}, "ref": "#/a/~0"},
    {"op": "resolveLocalRef", "doc": {"a": {"~": 1, "/": 2}}, "ref": "#/a/~1"},
    {"op": "resolveLocalRef", "doc": {"a": {"b/c": 3}}, "ref": "#/a/b~1c"},
    {"op": "resolveLocalRef", "doc": {"a": 1}, "ref": "#/~"},
    {"op": "resolveLocalRef", "doc": {"a": 1}, "ref": "#/~2"},
    {"op": "resolveLocalRef", "doc": {"a": 1}, "ref": "#/a/~2"},
    {"op": "get", "doc": [0], "tokens": ["01"]},
    {"op": "get", "doc": [0], "tokens": ["0"]},
    {"op": "get", "doc": {"a": {"b": [1, 2]}}, "tokens": ["a", "b", "2"]},
]


def iter_corpus_cases(paths: Iterable[str]) -> Iterable[Dict[str, Any]]:
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                trimmed = line.strip()
                if not trimmed:
                    continue
                yield json.loads(trimmed)


def main() -> int:
    checked = 0
    for case in list(iter_corpus_cases(CORPUS_PATHS)) + EXTRA_CASES:
        spec_result = eval_case(case)
        z3_result = z3_eval_case(case)
        checked += 1
        if spec_result != z3_result:
            print("oracle parity mismatch")
            print("case:", json.dumps(case, ensure_ascii=False))
            print("spec:", json.dumps(spec_result, ensure_ascii=False))
            print("z3:", json.dumps(z3_result, ensure_ascii=False))
            return 1

    print(f"oracle parity OK: {checked} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# verification/z3/gen_cases.py
import json
import random

MAX_CASES = 200

DOC_SAMPLES = [
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
    {},
    {"a": 1},
    {"": 123},
    {"a": {"b": 2}},
    {"a": ["x", "y"]},
    {"a": {"": 9}},
]

TOKENS_SAMPLES = [
    [],                    # whole document
    [""],                  # empty-key
    ["a"],
    ["a", "b"],
    ["a", "0"],
    ["a", "1"],
    ["a", "01"],           # leading-zero -> TypeMismatch (array only)
    ["missing"],
    ["a", "missing"],
    ["0"],                 # array index (if doc is array)
    ["foo"],               # array mismatch (if doc is array)
]

def main():
    path = "verification/z3/corpus/cases.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for _ in range(MAX_CASES):
            case = {
                "doc": random.choice(DOC_SAMPLES),
                "tokens": random.choice(TOKENS_SAMPLES),
            }
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
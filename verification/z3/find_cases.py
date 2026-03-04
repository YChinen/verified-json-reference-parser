import json
from typing import Any, Dict, Iterable, List, Set

from pools import DOCS, REFS_LIST, TOKENS_LIST
from spec import eval_case, kind_of_result


def key_of_case(case: Dict[str, Any]) -> str:
    return json.dumps(case, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def iter_get_cases() -> Iterable[Dict[str, Any]]:
    for doc in DOCS:
        for tokens in TOKENS_LIST:
            yield {"op": "get", "doc": doc, "tokens": tokens}


def iter_ref_cases() -> Iterable[Dict[str, Any]]:
    for doc in DOCS:
        for ref in REFS_LIST:
            yield {"op": "resolveLocalRef", "doc": doc, "ref": ref}


def maybe_accept_case(
    case: Dict[str, Any],
    produced: List[Dict[str, Any]],
    seen: Set[str],
    counts: Dict[str, int],
    targets: Dict[str, int],
) -> None:
    key = key_of_case(case)
    if key in seen:
        return

    kind = kind_of_result(eval_case(case))
    limit = targets.get(kind)
    if limit is not None and counts.get(kind, 0) >= limit:
        return

    produced.append(case)
    seen.add(key)
    counts[kind] = counts.get(kind, 0) + 1


def main():
    out_path = "verification/z3/corpus/generated.jsonl"
    max_cases = 500
    targets = {"Ok": 120, "NotFound": 140, "TypeMismatch": 160, "InvalidPointer": 80}
    counts: Dict[str, int] = {"Ok": 0, "NotFound": 0, "TypeMismatch": 0, "InvalidPointer": 0}

    produced: List[Dict[str, Any]] = []
    seen: Set[str] = set()

    for case in iter_get_cases():
        if len(produced) >= max_cases:
            break
        maybe_accept_case(case, produced, seen, counts, targets)

    for case in iter_ref_cases():
        if len(produced) >= max_cases:
            break
        maybe_accept_case(case, produced, seen, counts, targets)

    with open(out_path, "w", encoding="utf-8") as f:
        for case in produced:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    print(f"wrote {len(produced)} cases -> {out_path}")
    print("coverage:", counts)


if __name__ == "__main__":
    main()

import argparse
import json
import os
from typing import Any, Dict, Set

FAIL_PATH_DEFAULT = "verification/z3/corpus/failures.jsonl"
REG_PATH_DEFAULT = "verification/z3/corpus/regression.jsonl"


def key_of_case(c: Dict[str, Any]) -> str:
    # Canonical-enough for our constrained corpus.
    # If you later need stricter canonicalization, replace this.
    return json.dumps(c, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_existing_keys(path: str) -> Set[str]:
    keys: Set[str] = set()
    if not os.path.exists(path):
        return keys
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                c = json.loads(line)
            except Exception:
                continue
            if isinstance(c, dict) and "doc" in c and "tokens" in c:
                keys.add(key_of_case(c))
    return keys


def main():
    ap = argparse.ArgumentParser(description="Promote diff failures into regression corpus.")
    ap.add_argument("--fail", default=FAIL_PATH_DEFAULT, help="Path to failures.jsonl")
    ap.add_argument("--reg", default=REG_PATH_DEFAULT, help="Path to regression.jsonl")
    ap.add_argument(
        "--clear",
        action="store_true",
        help="Truncate failures file after promotion (use with care).",
    )
    args = ap.parse_args()

    if not os.path.exists(args.fail):
        print(f"missing failures: {args.fail}")
        return

    existing = load_existing_keys(args.reg)

    promoted = 0
    skipped = 0
    total = 0

    os.makedirs(os.path.dirname(args.reg), exist_ok=True)

    with open(args.fail, "r", encoding="utf-8") as fin, open(args.reg, "a", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                obj = json.loads(line)
            except Exception:
                skipped += 1
                continue

            case = obj.get("case") if isinstance(obj, dict) else None
            if not isinstance(case, dict):
                skipped += 1
                continue

            # Expect tokens-based cases
            if "doc" not in case or "tokens" not in case:
                skipped += 1
                continue

            k = key_of_case(case)
            if k in existing:
                skipped += 1
                continue

            fout.write(json.dumps(case, ensure_ascii=False) + "\n")
            existing.add(k)
            promoted += 1

    if args.clear:
        # Truncate failures file
        with open(args.fail, "w", encoding="utf-8") as f:
            f.write("")

    print(f"failures read: {total}")
    print(f"promoted: {promoted}")
    print(f"skipped: {skipped}")
    print(f"regression: {args.reg}")
    if args.clear:
        print(f"cleared: {args.fail}")


if __name__ == "__main__":
    main()
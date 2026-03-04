import argparse
import json
import sys

from spec import err, eval_case
from z3_model import z3_eval_case

def main():
    ap = argparse.ArgumentParser(description="Evaluate a verification case with the selected oracle engine.")
    ap.add_argument("--engine", choices=["python", "z3"], default="z3")
    args = ap.parse_args()

    line = sys.stdin.readline()
    if not line:
        print(json.dumps(err("InvalidPointer"), ensure_ascii=False))
        return

    try:
        case = json.loads(line)
    except json.JSONDecodeError:
        print(json.dumps(err("InvalidPointer"), ensure_ascii=False))
        return

    out = z3_eval_case(case) if args.engine == "z3" else eval_case(case)
    print(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main()

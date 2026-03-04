import json
import sys

from spec import err, eval_case

def main():
    line = sys.stdin.readline()
    if not line:
        print(json.dumps(err("InvalidPointer"), ensure_ascii=False))
        return

    try:
        case = json.loads(line)
    except json.JSONDecodeError:
        print(json.dumps(err("InvalidPointer"), ensure_ascii=False))
        return

    out = eval_case(case)
    print(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main()

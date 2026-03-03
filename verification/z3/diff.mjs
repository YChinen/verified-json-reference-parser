import fs from "node:fs";
import readline from "node:readline";
import { spawnSync } from "node:child_process";
import { get } from "../../dist/index.js";

/**
 * Compare TS implementation vs Python oracle on a corpus of cases.
 *
 * Input: JSONL lines like:
 *   {"doc": <JSONValue>, "ref": "#/a/0"}
 *
 * Oracle protocol:
 *   stdin:  one JSON line (same as case)
 *   stdout: one JSON line representing Result<JSONValue>
 *     - {"ok":true,"value":...}
 *     - {"ok":false,"kind":"InvalidPointer"|"TypeMismatch"|"NotFound"}
 */

const CASES_PATH = "verification/z3/corpus/cases.jsonl";
const FAIL_PATH = "verification/z3/corpus/failures.jsonl";
const ORACLE_CMD = ["python", "verification/z3/oracle.py"];

function stableStringify(x) {
    // For now, JSON.stringify is sufficient because our corpus should be stable.
    // If you later need canonicalization, replace this with a canonical JSON stringifier.
    return JSON.stringify(x);
}

function deepEqualResult(a, b) {
    // Compare Result objects by JSON stringification.
    // Works as long as we keep ordering stable (for objects in values, corpus should be stable).
    return stableStringify(a) === stableStringify(b);
}

function callOracle(caseObj) {
    const input = stableStringify(caseObj) + "\n";
    const r = spawnSync(ORACLE_CMD[0], ORACLE_CMD.slice(1), {
        input,
        encoding: "utf8",
    });

    if (r.error) {
        return { ok: false, kind: "InvalidPointer", _oracleError: String(r.error) };
    }
    if (r.status !== 0) {
        return {
            ok: false,
            kind: "InvalidPointer",
            _oracleStderr: r.stderr?.toString() ?? "",
        };
    }

    const out = (r.stdout ?? "").toString().trim();
    if (!out) {
        return { ok: false, kind: "InvalidPointer", _oracleError: "empty stdout" };
    }

    try {
        return JSON.parse(out);
    } catch {
        return { ok: false, kind: "InvalidPointer", _oracleError: "invalid json" };
    }
}

async function main() {
    if (!fs.existsSync(CASES_PATH)) {
        console.error(`Missing corpus: ${CASES_PATH}`);
        process.exit(2);
    }

    const rl = readline.createInterface({
        input: fs.createReadStream(CASES_PATH, { encoding: "utf8" }),
        crlfDelay: Infinity,
    });

    let total = 0;
    let mismatches = 0;

    const failStream = fs.createWriteStream(FAIL_PATH, { flags: "a" });

    for await (const line of rl) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        total++;
        let caseObj;
        try {
            caseObj = JSON.parse(trimmed);
        } catch {
            mismatches++;
            failStream.write(
                stableStringify({
                    case: { raw: trimmed },
                    impl: { ok: false, kind: "InvalidPointer" },
                    oracle: { ok: false, kind: "InvalidPointer" },
                    note: "invalid input json",
                }) + "\n"
            );
            continue;
        }

        const impl = get(caseObj.doc, caseObj.tokens);
        const oracle = callOracle(caseObj);

        if (!deepEqualResult(impl, oracle)) {
            mismatches++;
            failStream.write(
                stableStringify({
                    case: caseObj,
                    impl,
                    oracle,
                }) + "\n"
            );
        }
    }

    failStream.end();

    console.log(`cases: ${total}`);
    console.log(`mismatches: ${mismatches}`);
    console.log(`failures written to: ${FAIL_PATH}`);

    // Non-zero exit on mismatch (useful for a dedicated workflow)
    process.exit(mismatches === 0 ? 0 : 1);
}

main().catch((e) => {
    console.error(e);
    process.exit(2);
});
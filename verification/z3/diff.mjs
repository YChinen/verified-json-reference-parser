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

const CASES_PATHS = [
    "verification/z3/corpus/seed.jsonl",
    "verification/z3/corpus/generated.jsonl",
    "verification/z3/corpus/regression.jsonl",
];
const FAIL_PATH = "verification/z3/corpus/failures.jsonl";
const ORACLE_CMD = ["python", "verification/z3/oracle.py"];

const seen = new Set();
function keyOf(c) { return JSON.stringify(c); } // doc/tokens限定なら十分

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

const REGRESSION_PATH = "verification/z3/corpus/regression.jsonl";

// CLI flags
const PROMOTE = process.argv.includes("--promote");
const CLEAR_FAILURES = process.argv.includes("--clear-failures");

function ensureDirForFile(path) {
    const dir = path.split("/").slice(0, -1).join("/");
    if (dir) fs.mkdirSync(dir, { recursive: true });
}

function keyOfCase(c) {
    // stable-enough for our constrained corpus
    return JSON.stringify(c);
}

function loadCaseKeysFromJsonl(path) {
    const keys = new Set();
    if (!fs.existsSync(path)) return keys;
    const text = fs.readFileSync(path, "utf8");
    for (const line of text.split("\n")) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        try {
            const c = JSON.parse(trimmed);
            if (c && typeof c === "object" && "doc" in c && "tokens" in c) {
                keys.add(keyOfCase(c));
            }
        } catch {
            // ignore
        }
    }
    return keys;
}

async function main() {
    for (const p of CASES_PATHS) {
        if (!fs.existsSync(p)) {
            console.error(`Missing corpus: ${p}`);
            process.exit(2);
        }
    }

    let total = 0;
    let mismatches = 0;

    const seen = new Set();

    const failStream = fs.createWriteStream(FAIL_PATH, { flags: "a" });

    for (const path of CASES_PATHS) {
        const rl = readline.createInterface({
            input: fs.createReadStream(path, { encoding: "utf8" }),
            crlfDelay: Infinity,
        });

        for await (const line of rl) {
            const trimmed = line.trim();
            if (!trimmed) continue;

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
                        source: path,
                    }) + "\n"
                );
                continue;
            }

            const k = keyOf(caseObj);
            if (seen.has(k)) continue;
            seen.add(k);

            total++;

            const impl = get(caseObj.doc, caseObj.tokens);
            const oracle = callOracle(caseObj);

            if (!deepEqualResult(impl, oracle)) {
                mismatches++;
                failStream.write(
                    stableStringify({
                        case: caseObj,
                        impl,
                        oracle,
                        source: path,
                    }) + "\n"
                );
            }
        }
    }

    failStream.end();

    // Optional: promote mismatches to regression corpus (local use)
    if (PROMOTE) {
        ensureDirForFile(REGRESSION_PATH);

        const existing = loadCaseKeysFromJsonl(REGRESSION_PATH);
        let promoted = 0;
        let skipped = 0;

        // Read back failures we just wrote (append mode). We promote only cases with mismatches.
        if (fs.existsSync(FAIL_PATH)) {
            const text = fs.readFileSync(FAIL_PATH, "utf8");
            const out = fs.createWriteStream(REGRESSION_PATH, { flags: "a" });

            for (const line of text.split("\n")) {
                const trimmed = line.trim();
                if (!trimmed) continue;

                let obj;
                try {
                    obj = JSON.parse(trimmed);
                } catch {
                    skipped++;
                    continue;
                }

                const c = obj?.case;
                if (!c || typeof c !== "object" || !("doc" in c) || !("tokens" in c)) {
                    skipped++;
                    continue;
                }

                const k = keyOfCase(c);
                if (existing.has(k)) {
                    skipped++;
                    continue;
                }

                out.write(JSON.stringify(c) + "\n");
                existing.add(k);
                promoted++;
            }

            out.end();
        }

        console.log(`promoted to regression: ${promoted} (skipped: ${skipped}) -> ${REGRESSION_PATH}`);

        if (CLEAR_FAILURES) {
            fs.writeFileSync(FAIL_PATH, "");
            console.log(`cleared failures: ${FAIL_PATH}`);
        }
    } else if (mismatches > 0) {
        console.log(`Tip: run with --promote to append mismatches into ${REGRESSION_PATH}`);
    }

    console.log(`unique cases: ${total}`);
    console.log(`mismatches: ${mismatches}`);
    console.log(`failures written to: ${FAIL_PATH}`);

    process.exit(mismatches === 0 ? 0 : 1);
}

main().catch((e) => {
    console.error(e);
    process.exit(2);
});
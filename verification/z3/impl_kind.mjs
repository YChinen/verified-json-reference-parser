import readline from "node:readline";
import { get, resolveLocalRef } from "../../dist/index.js";

const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });

function inferOp(obj) {
  if (!obj || typeof obj !== "object") return null;
  if (obj.op === "get" || obj.op === "resolveLocalRef") return obj.op;
  if ("tokens" in obj) return "get";
  if ("ref" in obj) return "resolveLocalRef";
  return null;
}

for await (const line of rl) {
  const trimmed = line.trim();
  if (!trimmed) continue;

  let obj;
  try {
    obj = JSON.parse(trimmed);
  } catch {
    process.stdout.write(JSON.stringify({ kind: "InvalidPointer" }) + "\n");
    continue;
  }

  const doc = obj.doc;
  const op = inferOp(obj);
  let r;

  if (op === "get") {
    const tokens = obj.tokens;
    if (!Array.isArray(tokens) || !tokens.every((t) => typeof t === "string")) {
      process.stdout.write(JSON.stringify({ kind: "InvalidPointer" }) + "\n");
      continue;
    }
    r = get(doc, tokens);
  } else if (op === "resolveLocalRef") {
    const ref = obj.ref;
    if (typeof ref !== "string") {
      process.stdout.write(JSON.stringify({ kind: "InvalidPointer" }) + "\n");
      continue;
    }
    r = resolveLocalRef(doc, ref);
  } else {
    process.stdout.write(JSON.stringify({ kind: "InvalidPointer" }) + "\n");
    continue;
  }

  const kind = r.ok ? "Ok" : r.kind;
  process.stdout.write(JSON.stringify({ kind }) + "\n");
}

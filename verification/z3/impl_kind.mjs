import readline from "node:readline";
import { get } from "../../dist/index.js";

const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });

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
  const tokens = obj.tokens;

  if (!Array.isArray(tokens) || !tokens.every((t) => typeof t === "string")) {
    process.stdout.write(JSON.stringify({ kind: "InvalidPointer" }) + "\n");
    continue;
  }

  const r = get(doc, tokens);

  const kind = r.ok ? "Ok" : r.kind;
  process.stdout.write(JSON.stringify({ kind }) + "\n");
}
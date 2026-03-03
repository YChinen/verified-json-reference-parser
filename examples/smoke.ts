import {
  parsePointer,
  formatPointer,
  get,
  resolveLocalRef,
  type JSONValue,
} from "../dist/index.js"; // build後を想定

// --- Sample JSON document ---
const doc: JSONValue = {
  user: {
    name: "Yuji",
    tags: ["engineer", "verified"],
  },
  "": "empty-key",
};

// --- parse / format ---
const p1 = parsePointer("/user/name");
if (!p1.ok) throw new Error("parse failed");

console.log("Pointer tokens:", p1.value);
console.log("Formatted again:", formatPointer(p1.value));

// --- get ---
const r1 = get(doc, p1.value);
console.log("get /user/name =>", r1);

// --- array index ---
const p2 = parsePointer("/user/tags/1");
if (!p2.ok) throw new Error("parse failed");

console.log("get /user/tags/1 =>", get(doc, p2.value));

// --- leading zero should fail ---
const p3 = parsePointer("/user/tags/01");
if (!p3.ok) throw new Error("parse failed");

console.log("get /user/tags/01 =>", get(doc, p3.value));

// --- empty key ---
const p4 = parsePointer("/");
if (!p4.ok) throw new Error("parse failed");

console.log('get "/" =>', get(doc, p4.value));

// --- resolveLocalRef ---
console.log('resolveLocalRef("#") =>', resolveLocalRef(doc, "#"));
console.log(
  'resolveLocalRef("#/user/name") =>',
  resolveLocalRef(doc, "#/user/name")
);
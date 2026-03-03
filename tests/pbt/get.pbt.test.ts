// tests/pbt/get.pbt.test.ts
import { describe, it, expect } from "vitest";
import fc from "fast-check";

import { get } from "../../src/public/pointer";
import type { JSONValue } from "../../src/public/types";
import { specGet } from "./spec_get";

// Small JSON generator (bounded depth)
const jsonArb: fc.Arbitrary<JSONValue> = fc.letrec((tie) => ({
  json: fc.oneof(
    fc.constant(null),
    fc.boolean(),
    // Keep numbers small/integer-ish to reduce noise
    fc.integer({ min: -3, max: 3 }),
    fc.string({ maxLength: 10 }),
    fc.array(tie("json"), { maxLength: 10 }),
    fc.dictionary(fc.string({ maxLength: 10 }), tie("json"), { maxKeys: 10 })
  ),
})).json as fc.Arbitrary<JSONValue>;

// Token vocabulary: include the nasty ones
const tokenVocab = [
  "", "a", "b", "c",
  "0", "1", "2",
  "01", "00", "000",
  "foo", "-1", "-0",
] as const;

const tokensArb = fc.array(fc.constantFrom(...tokenVocab), { minLength: 0, maxLength: 6 });

describe("PBT: get(doc,tokens) matches specGet(doc,tokens)", () => {
  it("matches Result exactly", () => {
    fc.assert(
      fc.property(jsonArb, tokensArb, (doc, tokens) => {
        const impl = get(doc, tokens);
        const spec = specGet(doc, tokens);
        // Deep compare result object (includes value on Ok)
        expect(impl).toEqual(spec);
      }),
      {
        // Tune as desired; start moderate
        numRuns: 100000,
      }
    );
  });
});
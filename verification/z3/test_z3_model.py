import unittest

from z3_model import z3_eval_case, z3_parse_pointer


class Z3ModelTests(unittest.TestCase):
    def test_parse_pointer_empty(self):
        parsed = z3_parse_pointer("")
        self.assertTrue(parsed.ok)
        self.assertEqual(parsed.tokens, [])

    def test_parse_pointer_requires_leading_slash(self):
        parsed = z3_parse_pointer("a/b")
        self.assertFalse(parsed.ok)
        self.assertEqual(parsed.kind, "InvalidPointer")

    def test_parse_pointer_unescapes(self):
        parsed = z3_parse_pointer("/a/~0/~1/b~1c")
        self.assertTrue(parsed.ok)
        self.assertEqual(parsed.tokens, ["a", "~", "/", "b/c"])

    def test_parse_pointer_rejects_invalid_escape(self):
        parsed = z3_parse_pointer("/a/~2")
        self.assertFalse(parsed.ok)
        self.assertEqual(parsed.kind, "InvalidPointer")

    def test_get_array_index_rules(self):
        self.assertEqual(
            z3_eval_case({"op": "get", "doc": [10], "tokens": ["0"]}),
            {"ok": True, "value": 10},
        )
        self.assertEqual(
            z3_eval_case({"op": "get", "doc": [10], "tokens": ["01"]}),
            {"ok": False, "kind": "TypeMismatch"},
        )

    def test_get_object_lookup(self):
        self.assertEqual(
            z3_eval_case({"op": "get", "doc": {"a": {"b": 2}}, "tokens": ["a", "b"]}),
            {"ok": True, "value": 2},
        )

    def test_get_primitive_descent(self):
        self.assertEqual(
            z3_eval_case({"op": "get", "doc": 1, "tokens": ["a"]}),
            {"ok": False, "kind": "TypeMismatch"},
        )

    def test_resolve_local_ref_whole_doc(self):
        doc = {"a": 1}
        self.assertEqual(
            z3_eval_case({"op": "resolveLocalRef", "doc": doc, "ref": "#"}),
            {"ok": True, "value": doc},
        )

    def test_resolve_local_ref_unsupported(self):
        self.assertEqual(
            z3_eval_case({"op": "resolveLocalRef", "doc": {"a": 1}, "ref": "#foo"}),
            {"ok": False, "kind": "InvalidPointer"},
        )


if __name__ == "__main__":
    unittest.main()

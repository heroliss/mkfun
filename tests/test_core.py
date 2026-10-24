import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from mkfun import (
    MappingError, StructureError, OutputError, ReverseValidationError,
    compile_mapping, flatten, mkfun,
)


class MappingTests(unittest.TestCase):
    def test_shared_json_fixtures(self):
        fixtures = json.loads((Path(__file__).parent / "json-fixtures.json").read_text(encoding="utf8"))
        for fixture in fixtures:
            with self.subTest(fixture=fixture["name"]):
                plan = compile_mapping(fixture["from"], fixture["to"], validate=fixture.get("validate", False))
                if fixture.get("error"):
                    with self.assertRaises(MappingError):
                        plan(fixture["input"])
                else:
                    self.assertEqual(plan(fixture["input"]), fixture["expected"])

    def test_nested_restructure_and_constants(self):
        f = mkfun(["name", "city", "skill"], {"user": {"name": "name", "city": "city"}, "skills": ["skill"], "active": True})
        self.assertEqual(f(["Liss", "上海", "Unity"]), {"user": {"Liss": "Liss", "上海": "上海"}, "skills": ["Unity"], "active": True})

    def test_distinct_sample_tokens_avoid_accidental_key_mapping(self):
        f = mkfun(["姓名", "城市"], {"name": "姓名", "city": "城市"})
        self.assertEqual(f(["Liss", "上海"]), {"name": "Liss", "city": "上海"})

    def test_nested_containers_and_bytes_preserved(self):
        f = mkfun(["x", ("y", b"z")], (b"z", {"x": ["y"]}))
        self.assertEqual(f([7, (8, b"actual")]), (b"actual", {7: [8]}))

    def test_scalar_root_and_empty_containers(self):
        self.assertEqual(mkfun("name", {"item": "name"})(42), {"item": 42})
        self.assertEqual(mkfun([], {"values": [], "flags": {}})([]), {"values": [], "flags": {}})
        self.assertEqual(mkfun(None, None)("new"), "new")

    def test_dict_keys_are_positions_and_can_be_mapped(self):
        f = mkfun({"key": "value"}, ["key", "value"])
        self.assertEqual(f({"new-key": "new-value"}), ["new-key", "new-value"])

    def test_duplicate_examples_use_first_and_explain(self):
        f = mkfun(["x", "x"], ["x", "x"])
        self.assertEqual(f([1, 2]), [1, 1])
        self.assertEqual(len(f.warnings), 1)
        self.assertEqual(f.explain()[1]["source_index"], 0)

    def test_type_sensitive_examples(self):
        self.assertEqual(mkfun([True, 1, "1"], ["1", True, 1.0])(["bool", "number", "str"]), ["str", "bool", "number"])

    def test_strings_are_data_never_code(self):
        hostile = '__import__("os").system("never execute") # { [ \\ "'
        f = mkfun(["token"], {"literal": hostile, "data": "token"})
        self.assertEqual(f([hostile])["literal"], hostile)
        self.assertEqual(f([hostile])["data"], hostile)

    def test_mutating_examples_cannot_change_plan(self):
        source, target = ["x"], {"items": ["x"]}
        f = mkfun(source, target)
        source.append("new")
        target["items"].append("new")
        self.assertEqual(f([1]), {"items": [1]})
        first = f([2])
        first["items"].append(9)
        self.assertEqual(f([2]), {"items": [2]})

    def test_dictionary_key_collision_is_explicit(self):
        f = mkfun(["a", "b"], {"a": 1, "b": 2})
        with self.assertRaises(OutputError):
            f(["same", "same"])

    def test_scalar_slot_cannot_expand_to_container(self):
        f = mkfun(["x"], {(1, "x"): 0})
        # 标量输入不能变成列表，确保结构约束先于输出构造。
        with self.assertRaises(StructureError):
            f([[1]])

    def test_output_amplification_is_bounded(self):
        with self.assertRaisesRegex(OutputError, "预算"):
            mkfun(["x"], ["x"] * 9_999)(["a" * 50_000])

    def test_different_layout_is_rejected_even_with_same_leaf_count(self):
        for bad in [(1, 2), [[1], 2], [1], [1, 2, 3]]:
            with self.subTest(bad=bad), self.assertRaises(StructureError):
                mkfun(["a", "b"], ["b", "a"])(bad)

    def test_cycle_is_rejected_and_shared_noncycle_allowed(self):
        a = []; a.append(a)
        with self.assertRaisesRegex(StructureError, "循环"):
            flatten(a)
        shared = ["x"]
        self.assertEqual(flatten([shared, shared]), ["x", "x"])

    def test_depth_and_node_limits(self):
        deep = "x"
        for _ in range(66):
            deep = [deep]
        with self.assertRaisesRegex(StructureError, "嵌套"):
            flatten(deep)
        with self.assertRaisesRegex(StructureError, "节点"):
            flatten([0] * 10_001)

    def test_supported_scalars_only_without_custom_equality(self):
        class Strange:
            def __eq__(self, other):
                raise AssertionError("must not compare")
            def __repr__(self):
                raise AssertionError("must not stringify")
        with self.assertRaises(StructureError):
            mkfun([Strange()], [])
        with self.assertRaises(StructureError):
            flatten(float("nan"))
        with self.assertRaises(StructureError):
            flatten(1 << 4097)

    def test_set_order_is_stable(self):
        self.assertEqual(flatten({"b", "a", "c"}), ["a", "b", "c"])
        self.assertEqual(mkfun({"x", "y"}, ["y", "x"])({"a", "b"}), ["b", "a"])
        self.assertEqual(mkfun(["x", "y"], {"x", "y"})([2, 2]), {2})

    def test_roundtrip_preserves_nested_data(self):
        f = mkfun(["x", "y"], {"first": "y", "second": "x", "fixed": 0}, True)
        self.assertEqual(f([2, 3]), {"first": 3, "second": 2, "fixed": 0})

    def test_roundtrip_rejects_information_loss(self):
        with self.assertRaises(ReverseValidationError):
            mkfun(["x", "y"], ["x"], True)([2, 3])
        with self.assertRaises(ReverseValidationError):
            mkfun(["x", "y"], {"x", "y"}, True)([2, 2])

    def test_legacy_imports(self):
        from ss import mkfun as old
        from ss_di import di
        self.assertEqual(old(["x"], ["x"])([5]), [5])
        self.assertEqual(di({"a": [1, 2]}), ["a", 1, 2])

    def test_cli_works_and_malformed_json_is_actionable(self):
        p = subprocess.run([sys.executable, "-m", "mkfun", "--explain"], capture_output=True, text=True, encoding="utf8")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)["result"]["profile"]["name"], "Liss")
        bad = subprocess.run([sys.executable, "-m", "mkfun", "--from", "NaN", "--to", "0", "--input", "1"], capture_output=True, text=True, encoding="utf8")
        self.assertEqual(bad.returncode, 2)
        self.assertIn("JSON", bad.stderr)

    def test_cli_json_is_utf8_even_with_legacy_stream_encoding(self):
        env = dict(os.environ, PYTHONIOENCODING="ascii")
        result = subprocess.run([sys.executable, "-m", "mkfun"], capture_output=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout.decode("utf8"))["profile"]["city"], "上海")


if __name__ == "__main__":
    unittest.main()

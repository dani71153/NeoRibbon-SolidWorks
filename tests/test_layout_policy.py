"""Run with python -m unittest discover -s tests (no FreeCAD required)."""

import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "freecad/NeoRibbon/layout_policy.py"
spec = importlib.util.spec_from_file_location("layout_policy", path)
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class LayoutPolicyTests(unittest.TestCase):
    def test_exact_fit_keeps_all_commands_visible(self):
        self.assertEqual(policy.collapsed_groups([200, 150], [80, 80], 350), set())

    def test_trailing_groups_collapse_before_primary_group(self):
        self.assertEqual(policy.collapsed_groups([200, 150, 150], [80] * 3, 400), {1, 2})

    def test_extremely_narrow_window_collapses_all_and_allows_scroll(self):
        self.assertEqual(policy.collapsed_groups([200, 150], [80, 80], 50), {0, 1})

    def test_compaction_never_increases_a_small_group(self):
        self.assertEqual(policy.collapsed_groups([50, 150], [80, 80], 130), {1})

    def test_growing_window_restores_groups(self):
        widths = [200, 150]
        self.assertEqual(policy.collapsed_groups(widths, [80, 80], 250), {1, 0})
        self.assertEqual(policy.collapsed_groups(widths, [80, 80], 500), set())

    def test_empty_ribbon_and_invalid_width_lists(self):
        self.assertEqual(policy.collapsed_groups([], [], 0), set())
        with self.assertRaises(ValueError):
            policy.collapsed_groups([100], [], 100)


if __name__ == "__main__":
    unittest.main()

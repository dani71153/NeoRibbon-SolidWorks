import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location("workflow", Path(__file__).resolve().parents[1] /
                                            "freecad/NeoRibbon/workflow.py")
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


def command(name):
    return SimpleNamespace(name=name, ident=lambda: name)


class WorkflowTests(unittest.TestCase):
    def test_representative_commands(self):
        expected = {"Sketcher_NewSketch": "sketch", "PartDesign_Pad": "features",
                    "Part_Extrude": "features", "PartDesign_Plane": "geometry",
                    "PartDesign_SubShapeBinder": "geometry", "Assembly_CreateJointFixed": "assembly",
                    "Part_CheckGeometry": "inspection", "Std_ViewFitAll": "view"}
        for name, category in expected.items():
            with self.subTest(name=name):
                self.assertEqual(workflow.command_category(name), category)

    def test_split_keeps_every_command_and_source_preferences(self):
        panel = SimpleNamespace(name="Tools", commands=[command("Sketcher_NewSketch"),
                                                       command("PartDesign_Pad"), command("Plugin_Unknown")])
        groups = workflow.default_layout([panel])
        self.assertEqual({name for group in groups for name in group["commands"]},
                         {cmd.name for cmd in panel.commands})
        self.assertTrue(all(group["source"] == "Tools" for group in groups))

    def test_custom_order_and_new_commands_remain_accessible(self):
        defaults = [{"id": "features/Tools", "title": "Tools", "source": "Tools",
                     "category": "features", "commands": ["pad", "pocket", "new"]}]
        saved = [dict(defaults[0], commands=["pocket", "pad", "removed", "pad"])]
        result = workflow.resolve_layout(defaults, saved, {"pad", "pocket", "new"})
        self.assertEqual(result[0]["commands"], ["pocket", "pad", "new"])

    def test_invalid_profile_falls_back_without_losing_commands(self):
        defaults = [{"id": "view/Tools", "title": "Tools", "source": "Tools",
                     "category": "view", "commands": ["known"]}]
        self.assertEqual(workflow.resolve_layout(defaults, [{"category": "bad"}], {"known"}), defaults)

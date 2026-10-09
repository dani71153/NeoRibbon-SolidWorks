import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


class QuickExtrudeTests(unittest.TestCase):
    def setUp(self):
        self.body = Mock(Name="Body")
        self.sketch = Mock(Name="Sketch")
        self.sketch.getParentGeoFeatureGroup.return_value = self.body
        self.doc = Mock()
        self.doc.getObject.side_effect = {"Sketch": self.sketch, "Body": self.body}.get
        self.gui_doc = Mock()
        self.gui_doc.getInEdit.return_value = SimpleNamespace(Object=self.sketch)
        self.app = SimpleNamespace(ActiveDocument=self.doc, Console=Mock())
        self.gui = Mock()
        self.gui.activeDocument.return_value = self.gui_doc
        self.calls = []
        self.gui.runCommand.side_effect = self.run_command
        self.timer = Mock()
        self.timer.singleShot.side_effect = lambda delay, callback: self.calls.append(callback)
        self.modules = patch.dict(sys.modules, {
            "FreeCAD": self.app, "FreeCADGui": self.gui,
            "PySide": SimpleNamespace(), "PySide.QtCore": SimpleNamespace(QTimer=self.timer)})
        self.modules.start()
        path = Path(__file__).parents[1] / "freecad/NeoRibbonSolidWorks/quick_extrude.py"
        spec = importlib.util.spec_from_file_location("quick_extrude_test", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.command = module.QuickExtrudeCommand()

    def tearDown(self):
        self.modules.stop()

    def run_command(self, name):
        if name == "Sketcher_LeaveSketch":
            self.gui_doc.getInEdit.return_value = None

    def test_edit_to_native_pad_preserves_sketch(self):
        self.assertTrue(self.command.IsActive())
        self.command.Activated()
        self.gui.runCommand.assert_called_once_with("Sketcher_LeaveSketch")
        self.assertFalse(self.command.IsActive())
        self.command.Activated()
        self.assertEqual(len(self.calls), 1)
        self.calls[0]()
        self.gui.activateWorkbench.assert_called_once_with("PartDesignWorkbench")
        self.gui.Selection.addSelection.assert_called_once_with(self.sketch)
        self.gui.runCommand.assert_called_with("PartDesign_Pad")
        self.assertFalse(self.command._pending)

    def test_no_body_does_not_close_sketch(self):
        self.sketch.getParentGeoFeatureGroup.return_value = None
        self.assertFalse(self.command.IsActive())
        self.command.Activated()
        self.gui.runCommand.assert_not_called()

    def test_document_switch_aborts_pending_pad(self):
        self.command.Activated()
        self.app.ActiveDocument = Mock()
        self.calls[0]()
        self.gui.activateWorkbench.assert_not_called()
        self.gui.Selection.addSelection.assert_not_called()
        self.assertFalse(self.command._pending)

    def test_failed_exit_does_not_open_pad(self):
        self.gui.runCommand.side_effect = RuntimeError("exit failed")
        self.command.Activated()
        self.assertFalse(self.calls)
        self.assertFalse(self.command._pending)

    def test_selected_sketch_without_edit(self):
        self.gui_doc.getInEdit.return_value = None
        self.gui.Selection.getSelection.return_value = [self.sketch]
        self.command.Activated()
        self.calls[0]()
        self.gui.runCommand.assert_called_once_with("PartDesign_Pad")

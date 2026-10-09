# SPDX-License-Identifier: LGPL-2.1-or-later
"""Finish the current sketch and open FreeCAD's native Pad task."""

import FreeCAD as App
import FreeCADGui as Gui


class QuickExtrudeCommand:
    def __init__(self):
        self._pending = False

    def GetResources(self):
        return {"Pixmap": "PartDesign_Pad", "MenuText": "Extruir",
                "ToolTip": "Salir del croquis y abrir Extrusión (Pad) en Part Design"}

    def _context(self):
        doc = App.ActiveDocument
        gui_doc = Gui.activeDocument()
        if doc is None or gui_doc is None:
            return None
        editing = gui_doc.getInEdit()
        sketch = getattr(editing, "Object", None)
        if editing is None:
            selected = Gui.Selection.getSelection()
            sketch = selected[0] if len(selected) == 1 else None
        if sketch is None or not sketch.isDerivedFrom("Sketcher::SketchObject"):
            return None
        body = sketch.getParentGeoFeatureGroup()
        if body is None or not body.isDerivedFrom("PartDesign::Body"):
            return None
        return doc, sketch, body, editing is not None

    def IsActive(self):
        try:
            return not self._pending and self._context() is not None
        except Exception:
            return False

    def Activated(self):
        if self._pending:
            return
        context = self._context()
        if context is None:
            return
        doc, sketch, body, editing = context
        sketch_name, body_name = sketch.Name, body.Name
        self._pending = True
        try:
            if editing:
                # The native command also releases any active drawing handler.
                Gui.runCommand("Sketcher_LeaveSketch")
            from PySide.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._finish(doc, sketch_name, body_name))
        except Exception as exc:
            self._pending = False
            App.Console.PrintError(f"NeoRibbon: no se pudo abrir Extruir: {exc}\n")

    def _finish(self, doc, sketch_name, body_name):
        try:
            # Never act on a different document or close another editing task.
            if App.ActiveDocument is not doc or Gui.activeDocument().getInEdit() is not None:
                return
            sketch, body = doc.getObject(sketch_name), doc.getObject(body_name)
            if sketch is None or body is None or sketch.getParentGeoFeatureGroup() != body:
                return
            doc.recompute()
            Gui.activateWorkbench("PartDesignWorkbench")
            Gui.activeDocument().activeView().setActiveObject("pdbody", body)
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(sketch)
            Gui.runCommand("PartDesign_Pad")
        except Exception as exc:
            App.Console.PrintError(f"NeoRibbon: no se pudo abrir Extruir: {exc}\n")
        finally:
            self._pending = False

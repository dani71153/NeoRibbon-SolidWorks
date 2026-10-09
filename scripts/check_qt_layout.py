"""Isolated Qt integration checks with in-memory FreeCAD adapters.

Run with Python + PySide6. Does not launch FreeCAD or access user preferences.
This complements, rather than replaces, checks in real FreeCAD 1.1.4.
"""

import os
import importlib
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import PySide6
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtUiTools import QUiLoader

sys.modules.update({"PySide": PySide6, "PySide.QtCore": QtCore,
                    "PySide.QtGui": QtGui, "PySide.QtWidgets": QtWidgets})


class MemoryGroup:
    def __init__(self):
        self.values = {}

    def GetContents(self):
        return [(kind, key, value) for (kind, key), value in self.values.items()]

    def __getattr__(self, method):
        kinds = {"String": "String", "Bool": "Boolean", "Int": "Integer", "Unsigned": "Unsigned"}
        for suffix, kind in kinds.items():
            if method == f"Get{suffix}":
                return lambda key, default=None, k=kind: self.values.get((k, key), default)
            if method == f"Set{suffix}":
                return lambda key, value, k=kind: self.values.__setitem__((k, key), value)
            if method == f"Rem{suffix}":
                return lambda key, k=kind: self.values.pop((k, key), None)
        raise AttributeError(method)


parameters = {}
app = ModuleType("FreeCAD")
app.ParamGet = lambda path: parameters.setdefault(path, MemoryGroup())
app.saveParameter = lambda: None
app.Console = SimpleNamespace(PrintWarning=print, PrintError=print, PrintLog=lambda *_: None)
sys.modules["FreeCAD"] = app
qt_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
window = QtWidgets.QMainWindow()
gui = ModuleType("FreeCADGui")
gui.getMainWindow = lambda: window
gui.getIcon = lambda *_: QtGui.QIcon()
executed = []
gui.runCommand = lambda *args: executed.append(args)
sys.modules["FreeCADGui"] = gui
# A disabled upstream package may already be imported by FreeCAD. It must not
# supply modules to the fork or decide whether this fork is disabled.
upstream = ModuleType("freecad.NeoRibbon")
upstream.__path__ = []
sys.modules["freecad.NeoRibbon"] = upstream

toolbars = {f"Operations group {group}": [f"PartDesign_Pad_{group}_{index}" for index in range(9)]
            for group in range(4)}
toolbars["Sketch tools"] = ["Sketcher_NewSketch"]
toolbars["Snap"] = ["Draft_Snap_Lock"]
workbench = SimpleNamespace(name=lambda: "PartDesignWorkbench", MenuText="Part Design",
                            getToolbarItems=lambda: toolbars)
gui.activeWorkbench = lambda: workbench
gui.listWorkbenches = lambda: {"PartDesignWorkbench": workbench}
gui.listCommands = lambda: list(registry)
registry = {}
for name in [name for commands in toolbars.values() for name in commands]:
    label = f"Complete label for {name}"
    action = QtGui.QAction(label, window)
    if name == "Draft_Snap_Lock":
        action.setCheckable(True)
    registry[name] = SimpleNamespace(getAction=lambda action=action: [action],
                                     getInfo=lambda label=label: {"menuText": label},
                                     getShortcut=lambda: "")
gui.Command = SimpleNamespace(get=lambda name: registry.get(name))


class PreferenceLoader(QUiLoader):
    def createWidget(self, class_name, parent=None, name=""):
        if class_name.startswith("Gui::Pref"):
            class_name = "Q" + class_name.split("Pref", 1)[1]
        return super().createWidget(class_name, parent, name)


def load_ui(path):
    loader = PreferenceLoader()
    widget = loader.load(path)
    for child in widget.findChildren(QtCore.QObject):
        if child.objectName():
            setattr(widget, child.objectName(), child)
    return widget


gui.PySideUic = SimpleNamespace(loadUi=load_ui)

from freecad.NeoRibbonSolidWorks import prefs, profiles
from freecad.NeoRibbonSolidWorks.ribbon_bar import RibbonBar, RibbonDock, SectionOrderDialog
from freecad.NeoRibbonSolidWorks.customize_dialog import CustomizeDialog
from freecad.NeoRibbonSolidWorks.prefs_dialog import PreferencesDialog, PreferencePage


def settle():
    for _ in range(20):
        qt_app.processEvents()


ribbon = RibbonBar(window)
window.setCentralWidget(ribbon)
window.resize(8000, 400)
window.show()
ribbon._tabs.setCurrentIndex(1)
ribbon.refresh(force=True)
settle()
assert len(ribbon._groups) == 4
assert not any(group._compact for group in ribbon._groups), (window.width(), ribbon._scroll.viewport().width(), ribbon._group_widths)
button = ribbon._groups[0].findChild(QtWidgets.QToolButton, "NeoRibbon_btn_PartDesign_Pad_0_0")
assert button.text() == "Complete label for PartDesign_Pad_0_0"
assert button.sizeHint().width() <= button.width(), (button.sizeHint(), button.size())
window.resize(700, 400)
settle()
assert any(group._compact for group in ribbon._groups)
group = next(group for group in ribbon._groups if group._compact)
group._compact_button.click()
settle()
assert group._popup._list.count() == 9
group._popup.close()
window.resize(8000, 400)
settle()
assert not any(group._compact for group in ribbon._groups)

ribbon._tabs.setCurrentIndex(2)
settle()
snap = ribbon._groups[0].findChild(QtWidgets.QToolButton, "NeoRibbon_btn_Draft_Snap_Lock")
snap.click()
assert registry["Draft_Snap_Lock"].getAction()[0].isChecked() and snap.isChecked()

dialog = CustomizeDialog(window)
dialog.group_list.setCurrentRow(0)
dialog.command_list.setCurrentRow(0)
source_name = dialog.command_list.currentItem().data(QtCore.Qt.ItemDataRole.UserRole)
target_id = dialog.groups[1]["id"]
dialog.target.setCurrentIndex(dialog.target.findData(target_id))
dialog._move_command()
assert source_name in dialog.groups[1]["commands"]
dialog.accept()
assert profiles.active_profile() == "custom"
saved = profiles.saved_layout("PartDesignWorkbench")
importlib.reload(profiles)
assert profiles.saved_layout("PartDesignWorkbench") == saved
assert source_name in next(group for group in saved if group["id"] == target_id)["commands"]
prefs.set_button_size("large")
profiles.select_profile("solidworks")
profiles.select_profile("custom")
assert prefs.button_size() == "large"
assert profiles.saved_layout("PartDesignWorkbench") == saved

preferences = PreferencesDialog(window)
preferences.profile.setCurrentIndex(preferences.profile.findData("classic"))
assert profiles.active_profile() == "custom", "Profile selection must remain provisional"
preferences.reject()
assert profiles.active_profile() == "custom"
page = PreferencePage()
page.loadSettings()
page.profile.setCurrentIndex(page.profile.findData("classic"))
page.saveSettings()
assert profiles.active_profile() == "classic" and not prefs.is_enabled()
page.profile.setCurrentIndex(page.profile.findData("custom"))
page.saveSettings()
assert profiles.active_profile() == "custom" and prefs.button_size() == "large"
profiles.select_profile("classic")
assert not prefs.is_enabled()
profiles.select_profile("custom")
assert prefs.is_enabled()
profiles.restore_defaults()
assert profiles.saved_layout("PartDesignWorkbench") is None
assert prefs.button_size() == "medium"
profiles.undo_restore_defaults()
assert prefs.button_size() == "large"
assert profiles.saved_layout("PartDesignWorkbench") == saved
assert all(path.startswith(prefs.PARAM_PATH) or "Themes/UserTokens" in path for path in parameters)

font = QtGui.QFont(qt_app.font())
font.setPointSize(18)
qt_app.setFont(font)
ribbon.refresh(force=True)
settle()
assert ribbon._style.small_btn_height >= ribbon.fontMetrics().height() + 8
assert ribbon.height() >= ribbon._style.ribbon_height + ribbon._tabs.sizeHint().height()
for background, foreground in (("#202020", "#eeeeee"), ("#f0f0f0", "#202020")):
    palette = qt_app.palette()
    for role in (QtGui.QPalette.ColorRole.Window, QtGui.QPalette.ColorRole.Button):
        palette.setColor(role, QtGui.QColor(background))
    for role in (QtGui.QPalette.ColorRole.WindowText, QtGui.QPalette.ColorRole.ButtonText):
        palette.setColor(role, QtGui.QColor(foreground))
    qt_app.setPalette(palette)
    window.menuBar().setPalette(palette)
    ribbon._reapply_theme()
    settle()
    assert ribbon._theme_colors.background == background
dock = RibbonDock(window)
window.addDockWidget(QtCore.Qt.DockWidgetArea.TopDockWidgetArea, dock)
dock.show()
dock.ribbon._tabs.setCurrentIndex(1)
dock.refresh(force=True)
settle()
assert dock.height() == dock.ribbon.height() + 2
assert dock.ribbon.height() >= dock.ribbon._style.ribbon_height + dock.ribbon._tabs.sizeHint().height()
from freecad.NeoRibbonSolidWorks import bootstrap
from freecad.NeoRibbonSolidWorks.toolbar_ctrl import ToolbarController
assert not bootstrap.addon_disabled_by_manager()
bars = []
for name in ("File", "Edit", "View"):
    bar = QtWidgets.QToolBar(name, window)
    bar.setObjectName(name)
    bar.addAction("Test")
    window.addToolBar(bar)
    bar.show()
    bars.append(bar)
settle()
bootstrap._dock = dock
bootstrap._controller = ToolbarController()
bootstrap._show_ribbon()
settle()
assert dock.isVisible() and all(not bar.isVisible() for bar in bars)
refresh = dock.refresh
def fail_refresh(*_args, **_kwargs):
    raise RuntimeError("Injected rendering failure")
dock.refresh = fail_refresh
bootstrap._show_ribbon()
settle()
assert all(bar.isVisible() for bar in bars), "Rendering failure must restore working toolbars"
assert not bootstrap._controller._enabled and not dock.isVisible()
dock.refresh = refresh
bootstrap._show_ribbon()
settle()
assert dock.isVisible() and all(not bar.isVisible() for bar in bars)
bootstrap._hide_ribbon()
settle()
assert all(bar.isVisible() for bar in bars)

# Regression fixtures matching the user's Sketcher and Inspection screenshots.
constraint_names = [f"Sketcher_Constrain{suffix}" for suffix in
                    ("Coincident", "Horizontal", "Parallel", "Perpendicular", "Tangent", "Equal", "Symmetric")]
toolbars["Sketcher constraints"] = constraint_names
for name, label in zip(constraint_names, ("Coincident Constraint", "Horizontal/Vertical Constraint",
        "Parallel Constraint", "Perpendicular Constraint", "Tangent/Collinear Constraint",
        "Equal Constraint", "Symmetric Constraint")):
    action = QtGui.QAction(label, window)
    registry[name] = SimpleNamespace(getAction=lambda action=action: [action],
                                    getInfo=lambda label=label: {"menuText": label}, getShortcut=lambda: "")
toolbars["View"] = ["Std_Measure"]
measure = QtGui.QAction("Measure", window)
measure.setEnabled(False)
registry["Std_Measure"] = SimpleNamespace(getAction=lambda: [measure],
                                        getInfo=lambda: {"menuText": "Measure"}, getShortcut=lambda: "")
profiles.select_profile("solidworks")
ribbon._tabs.setCurrentIndex(0)
ribbon.refresh(force=True)
window.resize(700, 400)
settle()
constraint_group = next(group for group in ribbon._groups if group._panel.name == "Restricciones")
assert len([button for button in constraint_group.findChildren(QtWidgets.QToolButton)
            if button.objectName().startswith("NeoRibbon_btn_")]) == 4
for group in ribbon._groups:
    assert group._title.text() == group._panel.name, (group._title.text(), group._panel.name)
constraint_group._open_section_list()
settle()
assert constraint_group._popup._list.count() == len(constraint_names)
constraint_group._popup.close()
prefs.set_pinned_commands("Sketcher constraints", constraint_names[:6])
ribbon.refresh(force=True)
settle()
constraint_group = next(group for group in ribbon._groups if group._panel.name == "Restricciones")
assert len([button for button in constraint_group.findChildren(QtWidgets.QToolButton)
            if button.objectName().startswith("NeoRibbon_btn_")]) == 6
ribbon._tabs.setCurrentIndex(4)
settle()
assert ribbon._groups[0]._panel.name == "Medición"
assert ribbon._groups[0]._title.text() == "Medición"
measure_button = ribbon._groups[0].findChild(QtWidgets.QToolButton, "NeoRibbon_btn_Std_Measure")
assert measure_button.text() == "Medir" and not measure_button.isEnabled()
order_dialog = SectionOrderDialog(["View"], ["View"], labels={"View": "Medición"})
assert order_dialog._list.item(0).text() == "Medición"
assert order_dialog.names() == ["View"] and order_dialog.visibility() == {"View": True}
window.close()
print(f"PASS (Qt {QtCore.qVersion()}): full titles, localized captions, compact constraints, pins, inspection, profiles, themes, namespace isolation and failure recovery")

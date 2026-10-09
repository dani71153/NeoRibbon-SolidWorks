# NeoRibbon SolidWorks experience: validation

Implemented incrementally on a feature branch without modifying FreeCAD core.

## Completed checks

- `python -m unittest discover -s tests`: 13 passing tests for width allocation,
  category mapping, command retention and customization fallback.
- `python scripts/check_qt_layout.py`: passes with Qt/PySide6 6.12.0, using an
  offscreen Qt platform and in-memory FreeCAD adapters. Covers complete command
  labels, narrow/wide resizing, collapsed-group popups, checkable action state,
  command movement, profile serialization and reload, profile switching,
  provisional preference selection, the loaded preferences UI, reset/undo,
  larger fonts, light/dark palettes and dock height.
- Version 0.4.1 adds isolation from an already imported upstream
  `freecad.NeoRibbon` package and an injected rendering-failure test. Activation
  now builds the ribbon before hiding classic toolbars and restores them if
  rendering fails. The fork's package is `freecad.NeoRibbonSolidWorks`; existing
  preference paths remain unchanged.
- Version 0.4.2 adds screenshot-based Sketcher/Inspection fixtures: complete group
  captions at narrow widths and large fonts, four visible constraints with all
  tools retained in the popup, pins exceeding that limit, localized inspection
  captions with the original disabled action state, and source identifiers
  retained by the section-order dialog.
- Python syntax parsing for all 27 source, probe and test files passes.
- `git diff --check` passes.

The Qt check does not launch FreeCAD, read user.cfg, or modify the user's
preferences. PySide6 was installed in a temporary directory for that check;
it is not a new runtime dependency of the addon.

## FreeCAD 1.1.4 checks still required

The actual FreeCAD executable was unavailable in the execution environment.
Compatibility with its bundled Qt/PySide and real command registry is therefore
not certified by the adapter tests.

| Scenario | Expected result |
| --- | --- |
| Install/start and restart | Single ribbon dock; selected mode and profile persist |
| Sketcher/PartDesign/Part/Draft/Assembly switching | Active commands populate categories; no implicit workbench switch on tab click |
| Sketch editing and construction mode | Buttons track enabled/checked states and changing icons |
| Compound tools in nested and flat modes | Correct child command executes and remains accessible |
| Narrow window and high DPI/font scaling | Groups collapse and expand; titles do not overlap; all commands remain accessible |
| Light/dark theme changes | Tabs, focus buttons and menus retain readable colors |
| Customization Save/Cancel | Save persists order/category/moves; Cancel preserves prior layout |
| Preferences Apply/OK/Cancel | Profile selection applies only on Apply/OK |
| Profile reset and undo, including after restart | Only active profile resets; undo restores layout and settings |
| Classic profile and normal toggle off | Original hidden, floating and docked toolbars restore from the existing snapshot |
| Emergency toolbar recovery | Existing explicit recovery command remains available and separate from profile switching |

Run these checks in a test FreeCAD installation with a backup of its preferences.
The original GUI probes remain available; some change settings or close FreeCAD.

## 0.4.3: Extruir desde Croquis

18 pruebas de lógica aprobadas y comprobación Qt aprobada. Cinco pruebas nuevas verifican edición a Pad con el mismo croquis, prevención de doble activación, croquis sin cuerpo, cambio de documento, fallo al salir y croquis seleccionado fuera de edición. Las APIs de FreeCAD se simulan; queda pendiente probar el ciclo completo en FreeCAD 1.1.4 real.

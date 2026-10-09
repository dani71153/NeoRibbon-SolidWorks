# NeoRibbon

## Objetivo de este fork: SolidWorks Experience

Este fork de [NeoRibbon](https://github.com/robdevtech/NeoRibbon) tiene como objetivo
ofrecer en **FreeCAD 1.1.4** una interfaz y un flujo de trabajo similares a
SolidWorks, sin modificar el núcleo de FreeCAD y preservando las funciones
originales de NeoRibbon.

Las mejoras se centran en etiquetas legibles, tamaños y espaciado coherentes,
una cinta adaptable al ancho de la ventana y compatibilidad con temas claros y
oscuros. Las herramientas se organizan en seis categorías: **Croquis,
Operaciones, Geometría, Ensamblaje, Inspección y Vista**, priorizando los comandos
frecuentes y manteniendo los secundarios accesibles en desplegables.

La personalización incluye los perfiles **SolidWorks, FreeCAD clásico y
Personalizado**, reorganización de comandos y grupos, configuración persistente
y restauración de valores predeterminados con posibilidad de deshacer. El
desarrollo utiliza las APIs públicas de FreeCAD y Qt y busca mantener los cambios
de preferencias reversibles. La validación dentro de FreeCAD 1.1.4 sigue pendiente;
consulta [las verificaciones realizadas](docs/VALIDATION.md).

## NeoRibbon original

Lightweight Office/Fusion-style ribbon for **FreeCAD 1.1+**. The active workbench’s toolbars become compact side-by-side groups (small bottom titles, 3-row button grid)—not one oversized tab per toolbar. Classic toolbars are hidden while enabled and restored on disable. **No pip packages and no vendored ribbon toolkit.**

![NeoRibbon with OpenLight theme](Resources/Media/NeoRibbon_OpenLight.png)

![NeoRibbon with OpenDark theme](Resources/Media/NeoRibbon_OpenDark.png)

## Requirements

- FreeCAD **1.1.0** or newer (Qt6 / PySide via FreeCAD’s `PySide` wrapper)
- No other dependencies

## Important: UI replacement

While NeoRibbon is **enabled**, it intentionally changes FreeCAD’s main-window chrome:

- Classic **toolbars** for the active UI are hidden (mirrored into the ribbon instead)
- FreeCAD’s workbench selector moves into the ribbon’s **Workbench** control

This is reversible at any time:

| Goal | Action | Restart? |
|------|--------|----------|
| Turn NeoRibbon off (keep addon loaded) | **Tools → Toggle NeoRibbon** / toggle shortcut (default **Ctrl+Shift+N**), or uncheck **Enable ribbon** in Preferences then **Apply** | **No** — classic toolbars and the menu bar come back immediately. The next FreeCAD start keeps classic toolbars. |
| Turn NeoRibbon on | **Tools → Toggle NeoRibbon** / toggle shortcut, or check **Enable ribbon** then **Apply** | **No**. The next FreeCAD start shows the ribbon again. |
| Force classic toolbars back | **Restore classic toolbars** in NeoRibbon preferences, or **Tools → Restore classic toolbars** | No |
| Preferences (size, labels, shortcuts, …) | **Edit → Preferences → NeoRibbon** (**Ctrl+,**), or **Tools → NeoRibbon preferences…** | No — Apply/OK takes effect immediately |
| Disable or uninstall via **Addon Manager** | AM writes `ADDON_DISABLED` (or deletes the Mod). NeoRibbon restores classic toolbars in the current session | **Yes** — FreeCAD only unloads/loads Mods at startup. First install and AM Enable also need a restart |

NeoRibbon does not phone home or send telemetry. Preferences and usage counts stay in FreeCAD’s local parameter store (`User parameter:BaseApp/Preferences/Mod/NeoRibbon`).

## Install

### Addon Manager (git URL)

1. **Tools → Addon manager**
2. Install from repository: `https://github.com/robdevtech/NeoRibbon`
3. Restart FreeCAD when prompted — **required**. Addon Manager does not load a new Mod (or re-enable one) until the next startup. NeoRibbon cannot show the dock in that same session.

After this addon is accepted into the official Addon Index, it will also appear in the Addon Manager browse list.

### Manual (development)

1. Copy or symlink this repository into FreeCAD’s **user Mod** directory, named `NeoRibbon`.

   FreeCAD 1.1+ uses a versioned data directory. Find it with:

   ```python
   # in FreeCAD Python console
   App.getUserAppDataDir()
   ```

   Typical Flatpak path:

   ```bash
   ln -s /path/to/NeoRibbon \
     ~/.var/app/org.freecad.FreeCAD/data/FreeCAD/v1-1/Mod/NeoRibbon
   ```

   Typical native path:

   ```bash
   ln -s /path/to/NeoRibbon ~/.local/share/FreeCAD/v1-1/Mod/NeoRibbon
   ```

   Older layouts may use `.../FreeCAD/Mod/` without the `v1-1` segment — use whatever `App.getUserAppDataDir()` reports, then `Mod/NeoRibbon`.

2. Restart FreeCAD.

3. Confirm the Report View shows `NeoRibbon installed` (log level) and a **NeoRibbon** dock appears at the top.

## Usage

| Action | How |
|--------|-----|
| Toggle ribbon | **Tools → Toggle NeoRibbon** (`NeoRibbon_Toggle`; default **Ctrl+Shift+N**, editable in preferences) |
| Toggle large section icon | **Tools → Toggle large section icon** (`NeoRibbon_ToggleLargeIcon`) |
| Toggle button text labels | **Tools → Toggle button text labels** (`NeoRibbon_ToggleButtonLabels`) |
| Preferences | **Edit → Preferences → NeoRibbon** (**Ctrl+,**) or **Tools → NeoRibbon preferences…** (`NeoRibbon_Preferences`) |
| Emergency toolbar restore | **Restore classic toolbars** in NeoRibbon preferences, or **Tools → Restore classic toolbars** (`NeoRibbon_RestoreToolbars`) |

Preferences (stored under `User parameter:BaseApp/Preferences/Mod/NeoRibbon`):

- **Enabled** — show ribbon / hide classic toolbars (**Apply** / **OK** update the live UI)
- **Version** — `NeoRibbon x.y.z` from `package.xml` (bottom of the preferences page and Tools dialog)
- **Promote large** — show the first focus command as a large icon per section (default on)
- **Show button labels** — text beside/under focus-strip icons (default on); section dropdowns always keep labels
- **Button size** — `small` \| `medium` \| `large`
- **Visible commands / section** — most-used commands shown as buttons (default 6); the rest are under **More ▾**
- **Dropdown command children** — compound tools (Rectangle, Arc, …) keep Centered/Rounded/etc. **nested in a dropdown**, or **listed individually** as separate ribbon buttons
- **Ignored toolbars** — semicolon-separated FreeCAD toolbar names to skip permanently
- **Keyboard shortcuts** — toggle ribbon (default `Ctrl+Shift+N`): click the field and press keys, or **Reset**. A valid chord is saved as soon as you record it. A chord already used by FreeCAD is rejected immediately.
- **Restore classic toolbars** — button in preferences (and Tools menu); disables the ribbon and re-docks classic bars, including ones that vanished from **View → Toolbars**. Infrequent recovery, not a shortcut.
- **Section order** — per-workbench group order under `SectionOrder/<workbench>` (semicolon-separated names); new toolbars append after the saved list

**Sections:** click the section footer (except **×**) for a full labeled command list (with shortcuts in parentheses when set); use the **pin** on each row to keep that command in the focus strip. The list stays on-screen if the group is scrolled off the edge. **×** hides the section; **Sections ▾** shows/hides groups and has **Reorder sections…** (checkbox to show/hide; drag or move up/down for order; per workbench). Hidden groups stay in that list so you can turn them back on. **Reset section order** restores the workbench toolbar order.

**Toggles:** ribbon buttons for checkable FreeCAD commands (snap-to-grid, B-spline helpers, and similar) stay visually pressed/checked in sync with the command. Ordinary commands are not faked as toggles.

**Workbench:** NeoRibbon hides the classic toolbar that held FreeCAD’s workbench combo. Use the **Workbench** control at the **left** of the ribbon instead.

## Layout (Addon Academy modern)

### Adaptive group layout

The ribbon offers six workflow tabs: Croquis, Operaciones, Geometría,
Ensamblaje, Inspección and Vista. Only commands from the active workbench are
shown; selecting a category does not activate another workbench. General or
unrecognized tools remain accessible under Vista. Source toolbar pins and
visibility are retained when a toolbar is split across categories.

Focus buttons retain their complete command labels. Button and ribbon heights
account for the current font as well as the selected icon density. When the
window becomes narrower, trailing groups collapse into an icon button; clicking
it opens the existing full command list, including pin controls and compound
commands. Groups expand again when there is room. Very narrow windows retain
horizontal scrolling. This adaptation does not change saved pins or visibility.

The width allocation policy can be checked without FreeCAD:

```console
python -m unittest discover -s tests
```

### Workflow profiles and customization

NeoRibbon preferences offer **SolidWorks**, **FreeCAD clásico** and
**Personalizado**. SolidWorks uses the six workflow tabs. FreeCAD clásico
disables the ribbon and restores native toolbars through the ordinary snapshot
restore path. Personalizado supports command and group ordering, new groups,
moving commands between groups and changing group categories. Open its editor
from preferences or the Sections menu. Save activates Personalizado; Cancel
discards the editor's changes. Commands newly added by a workbench remain
accessible after loading a saved layout.

Profile selection in preferences is provisional until Apply/OK. Customize and
Restore profile are explicit actions that take effect immediately after saving
the editor or pressing the restore button. Restore profile affects only the
active profile and can be undone with **Deshacer**, including after restarting.
The existing emergency **Restore classic toolbars** action remains separate.

Profiles retain independent density, labels, visible-command count, compound
command mode, ignored/hidden toolbars, pins and section order. Custom layouts
are stored per workbench. Shortcuts and the native toolbar snapshot remain
shared. The versioned JSON store `ProfilesV1`, previous store backup,
`OriginalNeoRibbonSettings` and `ActiveProfile` live under NeoRibbon's own
parameter group. Profile reset backups are retained in that store.

For isolated widget integration checks (requires the optional PySide6 dev
dependency; uses in-memory FreeCAD adapters and an offscreen Qt platform):

```console
python scripts/check_qt_layout.py
```

These checks do not certify compatibility with FreeCAD 1.1.4. Validate installation,
workbench switching, sketch editing, Assembly commands, native toolbar restoration,
restart persistence, and compound menus in that actual FreeCAD build before release.

Follows the [Structuring](https://freecad.github.io/Addon-Academy/Topics/Structuring/) modern namespaced layout:

```
NeoRibbon/
├─ freecad/NeoRibbon/     # Python package (__init__.py, init.py, init_gui.py, …)
├─ Resources/
│  ├─ Icons/              # SVG icons (package.xml + commands)
│  ├─ Media/              # README screenshots
│  └─ ui/                 # Preferences .ui
├─ LICENSE-Code           # LGPL-2.1-or-later (Python)
├─ LICENSE-Assets         # LGPL-2.1-or-later (icons / media)
├─ package.xml
├─ pyproject.toml         # optional dev deps (freecad-stubs, pyside6)
├─ README.md
└─ scripts/               # local FreeCAD probes (not loaded by FreeCAD)
```

- Content type in `package.xml` is **`other`** (not a Workbench class). FreeCAD still runs namespaced `freecad/NeoRibbon/init_gui.py` (and `init.py`) for `other`.
- No top-level `Init.py` / `InitGui.py`; no Python package code at the Mod root.
- Only the **active** workbench is inspected (`getToolbarItems`). Other workbenches are never activated for caching.
- Ribbon widgets are plain Qt (`QDockWidget`, `QToolButton`, etc.).
- Classic toolbars are restored immediately on toggle-off, Preferences **Enable ribbon** off (**Apply**/**OK**), `uninstall()`, and when Addon Manager writes `ADDON_DISABLED`. The last UI mode is remembered (`LastMode`): a restart shows the ribbon if it was on, or the user's classic toolbar layout if it was off. Toolbar visibility, row/column positions, and options are saved when the ribbon turns on (only if a full classic strip is visible) and restored when it turns off. NeoRibbon never calls `removeToolBar` (that drops bars from **View → Toolbars**); restore re-docks leftover bars. On quit with the ribbon still on, classic bars are shown first so FreeCAD does not persist an empty toolbar strip; the next launch still re-applies the ribbon. On quit with classic toolbars, the on-screen layout is saved as-is.
- **`init_gui.py`** installs the dock at GUI startup. **`init.py`** only retries install if the main window is already up. First Addon Manager install / AM Enable still need a FreeCAD restart.

## Manual test checklist (FreeCAD 1.1+)

1. Install Mod → ribbon appears; classic toolbars are hidden.
2. Switch Part / PartDesign / Draft → ribbon panels update without a long delay.
3. Toggle NeoRibbon off, or uncheck **Enable ribbon** then **Apply** → classic toolbars return in the user's previous visibility and layout; toolbars you had already hidden stay hidden. Quit and restart: classic stays if you left it off; the ribbon comes back if you left it on.
4. Set an ignored toolbar name → that tab is omitted after refresh.
5. Change button size → buttons update on next refresh.
6. Report View shows no cascade of swallowed exceptions from NeoRibbon.
7. **Sections ▾ → Reorder sections…** — uncheck a group then OK to hide it; check to show again; drag or move up/down reorders; reset restores workbench order (visibility is kept).
8. Toggle a checkable command (e.g. Draft snap, Sketcher helper) — ribbon button stays sunken while on.
9. Scroll the ribbon so a group is near the left/right edge, open its ▾ list — popup stays fully on screen.
10. **Edit → Preferences → NeoRibbon** shows **NeoRibbon x.y.z** at the bottom; Apply/OK updates the live ribbon.
11. Change the toggle shortcut in preferences — it should take effect immediately. A used chord is rejected. **Restore classic toolbars** in that same page disables the ribbon without a keyboard shortcut.
12. Leave classic toolbars on, quit and restart — the strip is intact and **View → Toolbars** still lists them. If bars are missing from that menu, **Restore classic toolbars** re-docks them.
13. Sketcher **Rectangle** chevron lists Centered / Rounded. Switching **Dropdown command children** to **Listed individually** shows those as separate buttons after Apply.

A short automated GUI probe is in [`scripts/smoke_gui.py`](scripts/smoke_gui.py):

```bash
flatpak run org.freecad.FreeCAD /path/to/NeoRibbon/scripts/smoke_gui.py
# expect: NeoRibbon smoke: dock=True / installed=True / panels>0
```

## Support

- Issues: https://github.com/robdevtech/NeoRibbon/issues
- License: LGPL-2.1-or-later — see [LICENSE-Code](LICENSE-Code) and [LICENSE-Assets](LICENSE-Assets)

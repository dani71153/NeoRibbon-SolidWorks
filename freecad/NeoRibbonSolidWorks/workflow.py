"""Workflow categories and editable layouts without GUI dependencies."""

CATEGORIES = (
    ("sketch", "Croquis"),
    ("features", "Operaciones"),
    ("geometry", "Geometría"),
    ("assembly", "Ensamblaje"),
    ("inspection", "Inspección"),
    ("view", "Vista"),
)
CATEGORY_IDS = tuple(key for key, _ in CATEGORIES)


def command_category(name):
    token = name.lower()
    if token.startswith("sketcher_") or "sketch" in token:
        return "sketch"
    if token.startswith(("assembly_", "asm4_", "a2plus_")):
        return "assembly"
    if token.startswith(("measure_", "inspection_")) or any(
        part in token for part in ("measure", "checkgeometry", "validate", "interference")
    ):
        return "inspection"
    if token.startswith(("std_view", "std_zoom", "std_sel", "std_togglevisibility")):
        return "view"
    if token in {"partdesign_plane", "partdesign_line", "partdesign_point", "partdesign_coordinatesystem"} or any(part in token for part in ("datum", "origin", "coordinate", "shapebinder", "subshapebinder")):
        return "geometry"
    if token.startswith("partdesign_"):
        return "features"
    if token.startswith("part_") and any(part in token for part in
            ("extrude", "revolve", "loft", "sweep", "fillet", "chamfer", "cut", "fuse", "common", "boolean")):
        return "features"
    if token.startswith(("part_", "draft_")):
        return "geometry"
    # General and unknown commands remain reachable, rather than being dropped.
    return "view"


def default_layout(panels):
    """Split source toolbars by category while retaining source preference keys."""
    result = []
    for panel in panels:
        buckets = {}
        for command in panel.commands:
            if command.name:
                buckets.setdefault(command_category(command.name), []).append(command.ident())
        for category, commands in buckets.items():
            result.append({"id": f"{category}/{panel.name}", "title": panel.name,
                           "source": panel.name, "category": category, "commands": commands})
    return result


def resolve_layout(defaults, saved, available):
    """Validate customization and retain newly installed or unassigned commands."""
    if not isinstance(saved, list):
        return defaults
    result = []
    used = set()
    group_ids = set()
    for group in saved:
        if not isinstance(group, dict) or group.get("category") not in CATEGORY_IDS:
            continue
        group_id = str(group.get("id", "")).strip()
        if not group_id or group_id in group_ids:
            continue
        group_ids.add(group_id)
        entries = group.get("commands", [])
        if not isinstance(entries, list):
            continue
        commands = [name for name in entries if isinstance(name, str) and name in available and name not in used]
        commands = list(dict.fromkeys(commands))
        used.update(commands)
        result.append({"id": group_id, "title": str(group.get("title") or group_id),
                       "source": str(group.get("source") or group_id),
                       "category": group["category"], "commands": commands})
    for group in defaults:
        missing = [name for name in group["commands"] if name not in used]
        if not missing:
            continue
        used.update(missing)
        target = next((item for item in result if item["id"] == group["id"]), None)
        if target is not None:
            target["commands"].extend(missing)
        else:
            result.append(dict(group, commands=missing))
    return result

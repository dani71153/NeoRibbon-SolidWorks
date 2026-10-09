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

LABEL_TRANSLATIONS = {
    "new sketch": "Nuevo croquis", "create sketch": "Nuevo croquis",
    "edit sketch": "Editar croquis", "attach sketch": "Vincular croquis",
    "reorient sketch": "Reorientar croquis", "validate sketch": "Validar croquis",
    "merge sketches": "Combinar croquis", "leave sketch": "Salir del croquis",
    "close sketch": "Cerrar croquis", "align view to sketch": "Alinear con croquis",
    "toggle section view": "Vista de sección", "line": "Línea", "point": "Punto",
    "polyline": "Polilínea", "rectangle": "Rectángulo", "arc from center": "Arco por centro",
    "circle from center": "Círculo por centro", "coincident constraint": "Coincidencia",
    "horizontal/vertical constraint": "Horizontal/vertical", "parallel constraint": "Paralelismo",
    "perpendicular constraint": "Perpendicularidad", "tangent/collinear constraint": "Tangencia",
    "equal constraint": "Igualdad", "symmetric constraint": "Simetría",
    "dimensional constraints": "Cotas", "measure": "Medir", "check geometry": "Validar geometría",
}


def display_label(text):
    return LABEL_TRANSLATIONS.get(text.strip().lower(), text)


def group_title(source, category, commands):
    """Translate known toolbar captions without changing their persistence keys."""
    if category == "inspection":
        return "Validación" if any("checkgeometry" in name.lower() or "validate" in name.lower()
                                  for name in commands) else "Medición"
    token = source.lower()
    if category == "sketch":
        for marker, label in (("b-spline", "B-splines"), ("bspline", "B-splines"),
                              ("constraint", "Restricciones"), ("edit mode", "Edición"),
                              ("geometr", "Geometría"), ("visual", "Visualización"),
                              ("virtual", "Visualización"), ("tool", "Herramientas")):
            if marker in token:
                return label
        if "sketch" in token:
            return "Croquis"
        if commands and all("sketch" in name.lower() for name in commands):
            return "Croquis"
    return {"file": "Archivo", "edit": "Edición", "view": "Vista", "clipboard": "Portapapeles",
            "structure": "Estructura", "help": "Ayuda", "individual views": "Orientación"}.get(token, source)


def command_category(name):
    token = name.lower()
    if token == "neoribbon_quickextrude":
        return "sketch"
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
            result.append({"id": f"{category}/{panel.name}", "title": group_title(panel.name, category, commands),
                           "source": panel.name, "category": category, "commands": commands})
    return result


def resolve_layout(defaults, saved, available):
    """Validate customization and retain newly installed or unassigned commands."""
    if not isinstance(saved, list):
        return defaults
    result = []
    used = set()
    group_ids = set()
    default_titles = {group["id"]: group["title"] for group in defaults}
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
        title = str(group.get("title") or group_id)
        if title == group.get("source") and group_id in default_titles:
            title = default_titles[group_id]
        result.append({"id": group_id, "title": title,
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

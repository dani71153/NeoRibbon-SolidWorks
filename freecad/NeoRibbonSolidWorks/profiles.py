"""Versioned NeoRibbon profiles; never changes FreeCAD's native toolbar preferences."""

import copy
import json

from freecad.NeoRibbonSolidWorks import prefs

PROFILES = (("solidworks", "SolidWorks"), ("classic", "FreeCAD clásico"),
            ("custom", "Personalizado"))
PROFILE_IDS = tuple(key for key, _ in PROFILES)
SCHEMA_VERSION = 1


def _store():
    raw = prefs.param_group().GetString("ProfilesV1", "")
    try:
        data = json.loads(raw)
        if data.get("version") == SCHEMA_VERSION and isinstance(data.get("profiles"), dict) and all(
            isinstance(entry, dict) for entry in data["profiles"].values()
        ):
            return data
    except (ValueError, TypeError, AttributeError):
        pass
    return {"version": SCHEMA_VERSION, "profiles": {}}


def _save(data):
    group = prefs.param_group()
    previous = group.GetString("ProfilesV1", "")
    if previous:
        group.SetString("ProfilesPrevious", previous)
    group.SetString("ProfilesV1", json.dumps(data, ensure_ascii=False))
    prefs._flush_user_params()


def active_profile():
    value = prefs.param_group().GetString("ActiveProfile", "solidworks")
    return value if value in PROFILE_IDS else "solidworks"


def _string_entries(path):
    import FreeCAD as App
    group = App.ParamGet(f"{prefs.PARAM_PATH}/{path}")
    return {entry[1]: entry[2] for entry in (group.GetContents() or ()) if entry[0] == "String"}


def _settings():
    return {"button_size": prefs.button_size(), "promote_large": prefs.promote_large(),
            "labels": prefs.show_button_labels(), "visible": prefs.visible_per_section(),
            "children": prefs.child_command_mode(), "ignored": prefs.ignored_toolbars_text(),
            "hidden": list(prefs.hidden_sections()), "pins": _string_entries("Pins"),
            "order": _string_entries("SectionOrder")}


def _apply_settings(settings):
    if not isinstance(settings, dict):
        settings = {}
    size = settings.get("button_size", "medium")
    prefs.set_button_size(size if size in prefs.BUTTON_SIZES else "medium")
    prefs.set_promote_large(bool(settings.get("promote_large", True)))
    prefs.set_show_button_labels(bool(settings.get("labels", True)))
    visible = settings.get("visible", 6)
    prefs.set_visible_per_section(visible if isinstance(visible, int) else 6)
    prefs.set_child_command_mode(settings.get("children", "nested"))
    prefs.set_ignored_toolbars_text(str(settings.get("ignored", "")))
    hidden = settings.get("hidden", [])
    prefs.set_hidden_sections([name for name in hidden if isinstance(name, str)] if isinstance(hidden, list) else [])
    import FreeCAD as App
    for path, key in (("Pins", "pins"), ("SectionOrder", "order")):
        group = App.ParamGet(f"{prefs.PARAM_PATH}/{path}")
        for name in _string_entries(path):
            group.RemString(name)
        values = settings.get(key, {})
        if isinstance(values, dict):
            for name, value in values.items():
                if isinstance(name, str) and isinstance(value, str):
                    group.SetString(name, value)


def select_profile(profile):
    if profile not in PROFILE_IDS:
        raise ValueError("Unknown NeoRibbon profile")
    current = active_profile()
    if current == profile:
        return
    data = _store()
    entries = data["profiles"]
    current_entry = entries.setdefault(current, {})
    current_entry["settings"] = _settings()
    if profile not in entries:
        entries[profile] = copy.deepcopy(current_entry) if profile == "custom" else {}
    if not prefs.param_group().GetString("OriginalNeoRibbonSettings", ""):
        prefs.param_group().SetString("OriginalNeoRibbonSettings", json.dumps(_settings()))
    _save(data)
    _apply_settings(entries[profile].get("settings", {}))
    prefs.param_group().SetString("ActiveProfile", profile)
    prefs.set_enabled(profile != "classic")
    from freecad.NeoRibbonSolidWorks import bootstrap
    bootstrap.apply_prefs()


def saved_layout(workbench):
    entry = _store()["profiles"].get(active_profile(), {})
    if not isinstance(entry, dict) or not isinstance(entry.get("layouts", {}), dict):
        return None
    return entry.get("layouts", {}).get(workbench)


def profile_settings(profile):
    if profile == active_profile():
        return _settings()
    entry = _store()["profiles"].get(profile, {})
    return copy.deepcopy(entry.get("settings", {})) if isinstance(entry, dict) else {}


def save_custom_layout(workbench, groups):
    if active_profile() != "custom":
        select_profile("custom")
    data = _store()
    entry = data["profiles"].setdefault("custom", {})
    entry.setdefault("layouts", {})[workbench] = copy.deepcopy(groups)
    _save(data)
    from freecad.NeoRibbonSolidWorks import bootstrap
    bootstrap.apply_prefs()


def restore_defaults():
    data = _store()
    profile = active_profile()
    backup = copy.deepcopy(data["profiles"].get(profile, {}))
    backup["settings"] = _settings()
    data.setdefault("reset_backups", {})[profile] = backup
    data["profiles"][profile] = {}
    _save(data)
    _apply_settings({})
    prefs.set_enabled(profile != "classic")
    from freecad.NeoRibbonSolidWorks import bootstrap
    bootstrap.apply_prefs()


def has_reset_backup():
    backups = _store().get("reset_backups", {})
    return isinstance(backups, dict) and isinstance(backups.get(active_profile()), dict)


def undo_restore_defaults():
    data = _store()
    backups = data.get("reset_backups", {})
    if not isinstance(backups, dict) or active_profile() not in backups:
        return
    restored = backups.pop(active_profile())
    data["profiles"][active_profile()] = restored
    _save(data)
    _apply_settings(restored.get("settings", {}))
    prefs.set_enabled(active_profile() != "classic")
    from freecad.NeoRibbonSolidWorks import bootstrap
    bootstrap.apply_prefs()

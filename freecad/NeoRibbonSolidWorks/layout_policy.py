"""Width allocation for ribbon groups, independent of FreeCAD and Qt."""


def collapsed_groups(widths, compact_widths, available):
    """Collapse trailing groups until they fit; retain scrolling if necessary."""
    if len(widths) != len(compact_widths):
        raise ValueError("Each group needs an expanded and compact width")
    total = sum(widths)
    collapsed = set()
    for index in range(len(widths) - 1, -1, -1):
        if total <= max(0, available):
            break
        saving = max(0, widths[index] - compact_widths[index])
        if saving:
            total -= saving
            collapsed.add(index)
    return collapsed

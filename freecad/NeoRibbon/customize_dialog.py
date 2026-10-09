"""Edit workflow groups and commands on a temporary copy until accepted."""

import copy
import uuid

from PySide.QtCore import Qt
from PySide.QtWidgets import (QAbstractItemView, QComboBox, QDialog, QDialogButtonBox,
                             QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                             QPushButton, QVBoxLayout)

from freecad.NeoRibbon import profiles
from freecad.NeoRibbon.workflow import CATEGORIES, default_layout, resolve_layout
from freecad.NeoRibbon.workbench_map import active_panels, active_workbench_name


class CustomizeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Personalizar NeoRibbon")
        self.resize(760, 520)
        self.workbench = active_workbench_name()
        panels = active_panels()
        self.commands = {cmd.ident(): cmd for panel in panels for cmd in panel.commands if cmd.name}
        self.defaults = default_layout(panels)
        self.groups = copy.deepcopy(resolve_layout(self.defaults, profiles.saved_layout(self.workbench), self.commands))
        self._selected_id = None
        self._loading = False
        root = QVBoxLayout(self)
        hint = QLabel("Arrastra grupos o comandos para cambiar su orden. Mueve comandos entre grupos y elige su categoría. Guardar activa Personalizado.")
        hint.setWordWrap(True)
        root.addWidget(hint)
        lists = QHBoxLayout()
        self.group_list = QListWidget()
        self.group_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.command_list = QListWidget()
        self.command_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        lists.addWidget(self.group_list)
        lists.addWidget(self.command_list)
        root.addLayout(lists)
        details = QHBoxLayout()
        self.title = QLineEdit()
        self.category = QComboBox()
        for key, label in CATEGORIES:
            self.category.addItem(label, key)
        details.addWidget(QLabel("Grupo"))
        details.addWidget(self.title)
        details.addWidget(self.category)
        root.addLayout(details)
        move_row = QHBoxLayout()
        self.target = QComboBox()
        move = QPushButton("Mover comando al grupo")
        move.clicked.connect(self._move_command)
        add = QPushButton("Añadir grupo")
        add.clicked.connect(self._add_group)
        reset = QPushButton("Restaurar distribución")
        reset.clicked.connect(self._reset)
        move_row.addWidget(self.target)
        move_row.addWidget(move)
        move_row.addWidget(add)
        move_row.addWidget(reset)
        root.addLayout(move_row)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
        self.group_list.currentItemChanged.connect(self._select_group)
        self.title.textEdited.connect(self._update_details)
        self.category.currentIndexChanged.connect(self._update_details)
        self._rebuild_groups()

    def _group(self):
        return next((group for group in self.groups if group["id"] == self._selected_id), None)

    def _save_commands(self):
        group = self._group()
        if group is not None:
            group["commands"] = [self.command_list.item(i).data(Qt.ItemDataRole.UserRole)
                                 for i in range(self.command_list.count())]

    def _rebuild_groups(self):
        self._selected_id = None
        self.group_list.clear()
        for group in self.groups:
            item = QListWidgetItem(group["title"])
            item.setData(Qt.ItemDataRole.UserRole, group["id"])
            self.group_list.addItem(item)
        self._rebuild_targets()
        self.group_list.setCurrentRow(0)

    def _rebuild_targets(self):
        self.target.clear()
        for group in self.groups:
            self.target.addItem(group["title"], group["id"])

    def _select_group(self, current, previous):
        self._save_commands()
        self._selected_id = current.data(Qt.ItemDataRole.UserRole) if current else None
        self._loading = True
        self.command_list.clear()
        group = self._group()
        self.title.setEnabled(group is not None)
        self.category.setEnabled(group is not None)
        if group:
            self.title.setText(group["title"])
            self.category.setCurrentIndex(self.category.findData(group["category"]))
            for name in group["commands"]:
                item = QListWidgetItem(self.commands[name].text or name)
                item.setData(Qt.ItemDataRole.UserRole, name)
                self.command_list.addItem(item)
        self._loading = False

    def _update_details(self, *_args):
        group = self._group()
        if self._loading or group is None:
            return
        group["title"] = self.title.text().strip() or "Grupo"
        group["category"] = self.category.currentData()
        self.group_list.currentItem().setText(group["title"])
        self._rebuild_targets()

    def _move_command(self):
        item = self.command_list.currentItem()
        target = next((group for group in self.groups if group["id"] == self.target.currentData()), None)
        if item is None or target is None or target is self._group():
            return
        name = item.data(Qt.ItemDataRole.UserRole)
        self.command_list.takeItem(self.command_list.row(item))
        self._save_commands()
        target["commands"].append(name)

    def _add_group(self):
        self._save_commands()
        # Preserve the current drag order before rebuilding the list.
        self.groups = self._ordered_groups()
        key = f"custom/{uuid.uuid4().hex}"
        self.groups.append({"id": key, "source": key, "title": "Nuevo grupo",
                            "category": self.category.currentData() or "view", "commands": []})
        self._rebuild_groups()
        self.group_list.setCurrentRow(self.group_list.count() - 1)

    def _ordered_groups(self):
        by_id = {group["id"]: group for group in self.groups}
        return [by_id[self.group_list.item(i).data(Qt.ItemDataRole.UserRole)]
                for i in range(self.group_list.count())]

    def _reset(self):
        self.groups = copy.deepcopy(self.defaults)
        self._rebuild_groups()

    def accept(self):
        self._save_commands()
        if self.workbench:
            profiles.save_custom_layout(self.workbench, self._ordered_groups())
        super().accept()


def open_customizer():
    import FreeCADGui as Gui
    CustomizeDialog(Gui.getMainWindow()).exec()

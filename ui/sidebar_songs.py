"""
Songs sidebar: search + list, click loads into editor.
"""
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout, QWidget
)


class SongsSidebar(QWidget):
    def __init__(
        self,
        on_flip: Callable[[], None],
        on_refresh: Callable[[str], None],
        on_item_clicked: Callable[[QListWidgetItem], None],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        nav = QHBoxLayout()
        nav.setContentsMargins(0, 0, 0, 0)
        nav.setSpacing(4)

        self.refresh_btn = QPushButton("🔃")
        self.refresh_btn.setToolTip("Refresh songs list")
        self.refresh_btn.clicked.connect(lambda: on_refresh(self.search.text()))

        self.flip_btn = QPushButton("🎛 / 🎵")
        self.flip_btn.setToolTip("Flip sidebar: Tools ↔ Songs")
        self.flip_btn.clicked.connect(on_flip)

        nav.addWidget(self.refresh_btn)
        nav.addWidget(self.flip_btn)
        nav.addStretch(1)
        layout.addLayout(nav)

        header = QLabel("🎵 Songs Library")
        header.setAlignment(Qt.AlignHCenter)
        layout.addWidget(header)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search songs (title / artist / album / mood)…")
        self.search.textChanged.connect(on_refresh)
        layout.addWidget(self.search)

        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list.itemClicked.connect(on_item_clicked)
        layout.addWidget(self.list, stretch=1)

    def clear(self) -> None:
        self.list.clear()

    def add_item(self, item: QListWidgetItem) -> None:
        self.list.addItem(item)

    def query(self) -> str:
        return self.search.text()

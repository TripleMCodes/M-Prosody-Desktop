"""
Songs sidebar: search + list, click loads into editor.
"""
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout, QWidget, QMenu
)
from PySide6.QtGui import QAction


class SongsSidebar(QWidget):
    def __init__(
        self,
        on_flip: Callable[[], None],
        on_refresh: Callable[[str], None],
        on_item_clicked: Callable[[QListWidgetItem], None],
        on_delete: Callable[[int], None],
        on_view_versions: Callable[[int], None],
        on_upload_song: Callable[[int], None],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.on_delete = on_delete
        self.on_view_versions = on_view_versions
        self.on_upload_song = on_upload_song

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
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.list, stretch=1)

    def clear(self) -> None:
        self.list.clear()

    def add_item(self, item: QListWidgetItem) -> None:
        self.list.addItem(item)

    def query(self) -> str:
        return self.search.text()

    def _show_context_menu(self, position) -> None:
        """Show context menu on right-click."""
        item = self.list.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        view_versions_action = QAction("View Versions", self)
        view_versions_action.triggered.connect(lambda: self._view_versions(item))
        menu.addAction(view_versions_action)
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self._delete_song(item))
        menu.addAction(delete_action)

        upload_song_action = QAction("Upload", self)
        upload_song_action.triggered.connect(lambda: self._upload_song(item))
        menu.addAction(upload_song_action)
        
        menu.exec(self.list.mapToGlobal(position))

    def _delete_song(self, item: QListWidgetItem) -> None:
        """Delete a song by its item."""
        row = item.data(Qt.UserRole)
        if row and len(row) > 0:
            song_id = int(row[0])
            self.on_delete(song_id)

    def _view_versions(self, item: QListWidgetItem) -> None:
        """View versions of a song."""
        row = item.data(Qt.UserRole)
        if row and len(row) > 0:
            song_id = int(row[0])
            self.on_view_versions(song_id)

    def _upload_song(self,  item: QListWidgetItem):
        row = item.data(Qt.UserRole)
        if row and len(row) > 0:
            song_id = int(row[0])
            # print(f"The song id: {song_id}")
            self.on_upload_song(song_id)
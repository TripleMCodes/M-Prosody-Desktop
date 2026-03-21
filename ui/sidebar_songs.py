"""
Songs sidebar: search + list, click loads into editor.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QVBoxLayout, QWidget, QMenu
)
from PySide6.QtGui import QAction, QColor, QIcon, QPixmap


class SongsSidebar(QWidget):
    def __init__(
        self,
        on_flip: Callable[[], None],
        on_refresh: Callable[[str], None],
        on_item_clicked: Callable[[QListWidgetItem], None],
        on_delete: Callable[[int], None],
        on_view_versions: Callable[[int], None],
        on_upload_song: Callable[[int], None],
        on_download: Callable[[], None],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.on_delete = on_delete
        self.on_view_versions = on_view_versions
        self.on_upload_song = on_upload_song
        self.on_download = on_download

        refresh_icon = Path(__file__).parent / "Icons/icons8-refresh-64.png"
        pen_icon = Path(__file__).parent / "Icons/icons8-writing-64.png"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        nav = QHBoxLayout()
        nav.setContentsMargins(0, 0, 0, 0)
        nav.setSpacing(4)

        icon_1 = QIcon(str(refresh_icon))
        self.refresh_btn = QPushButton("")
        self.refresh_btn.setIcon(icon_1)
        self.refresh_btn.setToolTip("Refresh songs list")
        self.refresh_btn.clicked.connect(lambda: on_refresh(self.search.text()))

        # self.flip_btn = QPushButton("🎛 / 🎵")
        # self.flip_btn.setToolTip("Flip sidebar: Tools ↔ Songs")
        # self.flip_btn.clicked.connect(on_flip)

        nav.addWidget(self.refresh_btn)
        # nav.addWidget(self.flip_btn)
        nav.addStretch(1)
        layout.addLayout(nav)

        header = QLabel()
        list_layout = QHBoxLayout()

        icon_label = QLabel()
        pixmap = QPixmap(pen_icon)
        pixmap = pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(pixmap)

        text_label = QLabel("Songs Library")

        list_layout.addStretch()
        list_layout.addWidget(icon_label)
        list_layout.addWidget(text_label)
        list_layout.addStretch()
        list_layout.setAlignment(Qt.AlignCenter)
        
        header.setAlignment(Qt.AlignHCenter)
        layout.addLayout(list_layout)
        layout.setAlignment(Qt.AlignCenter)

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

    def add_item(self, item: QListWidgetItem, state=None, source=None) -> None:
    
        if state == "uploaded":
            item.setBackground(QColor("#a855f7"))  # Neon primary purple
            self.list.addItem(item)
        
        elif state == "dirty":
            item.setBackground(QColor("#432064")) 
            self.list.addItem(item)

            
        elif source == 'web':
            item.setBackground(QColor("#7c3aed"))  # Deep purple
            self.list.addItem(item)

        elif source == 'desktop':
            item.setBackground(QColor("#c084fc"))  # Light purple
            self.list.addItem(item)

        else:
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

        download_song_action = QAction("Download", self)
        download_song_action.triggered.connect(lambda: self._download_song(item))
        menu.addAction(download_song_action)
        
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

    def _download_song(self, item: QListWidgetItem) -> None:
        """Download cloud song"""

        row = item.data(Qt.UserRole)

        try:
            source = row[13]
            # cloud_status = 
            print(f"source value {source}")

            if source == "uploaded":
                print("This song was uploaded and it exist locally, are sure you want to download it?")
           

                QMessageBox.warning(self, "Error", "This song was uploaded and it exist locally. You can't download it")
                return

            elif source == "local_only":
                print("Can't download song, it only exists locally.")
                QMessageBox.warning(self, "Error", "Can't download song, it only exists locally.")
                return
            

        except IndexError as e:
            #This is from cloud songs
            #check main_window.py, method -> refresh_song_list
            source = row[7]
            print(e)
            # print(f'source value {source}')

            data = {
                "cloud_song_id": row[0],
                "title": row[1],
                "artist": row[2],
                "album": row[3],
                "genre": row[4],
                "mood": row[5],
                "lyrics": row[6],
                "source": row[7],
                "cloud_owner": row[8]
            }

            if source == "web":
                # print(f"song data: {data}")
                print("Are sure you want to download this song?")
                results = QMessageBox.question(
            self,
            "Download Song",
            "Are sure you want to download this song?",
            QMessageBox.Yes | QMessageBox.No
            )
        
            elif source == "desktop":
                # print(f"song data: {data}")
                print("Song was uploaded, are sure you want to download it?")
                results = QMessageBox.question(
            self,
            "Download Song",
            "Song was uploaded, are sure you want to download it?",
            QMessageBox.Yes | QMessageBox.No)
            
            if results == QMessageBox.Yes:
                self.on_download(data)
            else:
                return

        except Exception as e:
            print(e)
            return




    def _upload_song(self,  item: QListWidgetItem):
        row = item.data(Qt.UserRole)

        if row and len(row) > 0:
            song_id = int(row[0])
            # print(f"The song id: {song_id}")
            self.on_upload_song(song_id)
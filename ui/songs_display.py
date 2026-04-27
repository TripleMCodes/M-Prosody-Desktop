"""
Songs display widget for showing songs in a card-based grid or list layout.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QScrollArea, QGridLayout, QSpacerItem, QSizePolicy
)
from ui.glass_qss import SONGS_DISLAY_STYLE

class SongCard(QFrame):
    """Individual song card with title, artist, metadata, and actions."""
    
    clicked = Signal(object)  # emits song data
    delete_requested = Signal(object)  # emits song data
    
    def __init__(self, song_data: tuple, icons_dir: Path, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.song_data = song_data
        self.setObjectName("SongCard")
        self.setFrameShape(QFrame.StyledPanel)
        
        # Extract song info
        if len(song_data) >= 7:
            song_id, title, artist, album, genre, mood, lyrics = song_data[:7]
        else:
            song_id, title, artist = song_data[0], song_data[1], song_data[2]
            album, genre, mood, lyrics = "", "", "", ""
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel(f"<b>{title or 'Untitled'}</b>")
        title_label.setStyleSheet("font-size: 14px; color: #a855f7;")
        layout.addWidget(title_label)
        
        # Artist
        artist_label = QLabel(f"<i>{artist or 'Unknown Artist'}</i>")
        artist_label.setStyleSheet("font-size: 12px; color: #999;")
        layout.addWidget(artist_label)
        
        # Metadata row
        meta_parts = []
        if album:
            meta_parts.append(f"Album: {album}")
        if genre:
            meta_parts.append(f"Genre: {genre}")
        if mood:
            meta_parts.append(f"Mood: {mood}")
        
        if meta_parts:
            meta_label = QLabel(" • ".join(meta_parts))
            meta_label.setStyleSheet("font-size: 11px; color: #888;")
            meta_label.setWordWrap(True)
            layout.addWidget(meta_label)
        
        # Lyrics preview
        if lyrics:
            preview = (lyrics.strip().splitlines()[0])[:80]
            preview_label = QLabel(f"<i>\"{preview}{'...' if len(lyrics) > 80 else ''}\"</i>")
            preview_label.setStyleSheet("font-size: 10px; color: #666; margin-top: 6px;")
            preview_label.setWordWrap(True)
            layout.addWidget(preview_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)
        btn_layout.setContentsMargins(0, 8, 0, 0)
        
        view_btn = QPushButton("View")
        view_btn.setObjectName("SongCardBtn")
        view_btn.setMaximumWidth(60)
        view_btn.clicked.connect(lambda: self.clicked.emit(self.song_data))
        btn_layout.addWidget(view_btn)
        
        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("SongCardBtn")
        edit_btn.setMaximumWidth(60)
        edit_btn.clicked.connect(lambda: self.clicked.emit(self.song_data))
        btn_layout.addWidget(edit_btn)
        
        btn_layout.addStretch(1)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("SongCardBtnDanger")
        delete_btn.setMaximumWidth(60)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.song_data))
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)
        
        # Styling
        self.setStyleSheet(SONGS_DISLAY_STYLE)


class SongsDisplayWidget(QWidget):
    """Widget to display a collection of songs in a grid/list layout."""
    
    song_selected = Signal(object)  # emits song data
    song_delete_requested = Signal(object)  # emits song data
    
    def __init__(self, icons_dir: Path, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.icons_dir = icons_dir
        self.songs = []
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Grid container
        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(12)
        
        scroll.setWidget(self.container)
        layout.addWidget(scroll)
    
    def set_songs(self, songs: List[tuple]):
        """Update displayed songs."""
        self.songs = songs
        self._refresh_grid()
    
    def _refresh_grid(self):
        """Clear and rebuild the song grid."""
        # Clear old widgets
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add new song cards (3 columns)
        for idx, song in enumerate(self.songs):
            card = SongCard(song, self.icons_dir)
            card.clicked.connect(self._on_song_selected)
            card.delete_requested.connect(self._on_delete_requested)
            
            row = idx // 3
            col = idx % 3
            self.grid_layout.addWidget(card, row, col)
        
        # Add spacer at the end to push cards to top
        if len(self.songs) > 0:
            num_rows = (len(self.songs) - 1) // 3 + 1
        else:
            num_rows = 0
        
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid_layout.addItem(spacer, num_rows, 0, 1, 3)
    
    def _on_song_selected(self, song_data):
        """Handle song card selection."""
        self.song_selected.emit(song_data)
    
    def _on_delete_requested(self, song_data):
        """Handle delete request."""
        self.song_delete_requested.emit(song_data)
    
    def clear(self):
        """Clear all songs."""
        self.set_songs([])

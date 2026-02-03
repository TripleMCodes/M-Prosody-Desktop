"""
Editor panel: metadata inputs + writing editor + output editor + word count.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QSplitter, QTextEdit, QVBoxLayout, QWidget


class EditorPanel(QWidget):
    def __init__(
        self,
        autosave_cb: Callable[[], None],
        update_word_count_cb: Callable[[], None],
        update_syllables_cb: Callable[[], None],
        wc_icon_path: Path,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)

        self.wc_icon_path = wc_icon_path

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # metadata inputs
        self.song_title_input = QLineEdit()
        self.song_artist_input = QLineEdit()
        self.song_album_input = QLineEdit()
        self.song_genre_input = QLineEdit()
        self.song_mood_input = QLineEdit()

        self.song_title_input.setPlaceholderText("Title")
        self.song_artist_input.setPlaceholderText("Artist")
        self.song_album_input.setPlaceholderText("Album (Optional)")
        self.song_genre_input.setPlaceholderText("Genre (Optional)")
        self.song_mood_input.setPlaceholderText("Mood (Optional)")

        meta_layout = QHBoxLayout()
        meta_layout.addWidget(self.song_title_input)
        meta_layout.addWidget(self.song_artist_input)
        meta_layout.addWidget(self.song_album_input)
        meta_layout.addWidget(self.song_genre_input)
        meta_layout.addWidget(self.song_mood_input)
        self.layout.addLayout(meta_layout)

        # splitter
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setSizes([300, 100])
        self.layout.addWidget(self.splitter)

        self.writing_editor = QTextEdit()
        self.writing_editor.setMinimumSize(400, 300)
        self.writing_editor.setPlaceholderText("Type your lyrics here")
        self.writing_editor.textChanged.connect(update_word_count_cb)
        self.writing_editor.textChanged.connect(update_syllables_cb)
        self.writing_editor.textChanged.connect(autosave_cb)
        self.splitter.addWidget(self.writing_editor)

        self.word_count_label = QLabel(
            f'<img src="{str(self.wc_icon_path)}" width="40" height="40">'
            f'<span style="font-size: 20px;"> ⁚ 0</span>'
        )
        self.word_count_label.setToolTip("word count")
        self.layout.addWidget(self.word_count_label)

        self.display_editor = QTextEdit()
        self.display_editor.setReadOnly(True)
        self.display_editor.setPlaceholderText("Rhymes, words, and lyrics generated will be displayed here...")
        self.splitter.addWidget(self.display_editor)

        self.editors: List[QTextEdit] = [self.writing_editor, self.display_editor]

    def set_word_count(self, count: int) -> None:
        self.word_count_label.setText(
            f'<img src="{str(self.wc_icon_path)}" width="40" height="40">'
            f'<span style="font-size: 20px;"> ⁚ {count}</span>'
        )

    def load_song_fields(self, title: str, artist: str, album: str, genre: str, mood: str) -> None:
        self.song_title_input.setText(title or "")
        self.song_artist_input.setText(artist or "")
        self.song_album_input.setText(album or "")
        self.song_genre_input.setText(genre or "")
        self.song_mood_input.setText(mood or "")

    def load_lyrics(self, lyrics: str) -> None:
        self.writing_editor.blockSignals(True)
        self.writing_editor.setPlainText(lyrics or "")
        self.writing_editor.blockSignals(False)

        cursor = self.writing_editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.writing_editor.setTextCursor(cursor)

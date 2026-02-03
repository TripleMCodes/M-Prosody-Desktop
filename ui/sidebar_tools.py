"""
Tools sidebar: generation controls, lexicon controls, recorder launch, theme/file/save/about buttons, etc.

This is intentionally "UI-only": it doesn't know about DB or editor internals.
The parent MainWindow wires callbacks.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton, QToolButton,
    QVBoxLayout, QWidget
)


class ToolsSidebar(QWidget):
    def __init__(
        self,
        icons_dir: Path,
        on_generate: Callable[[], None],
        on_search_lexicon: Callable[[], None],
        on_launch_recorder: Callable[[], None],
        on_change_font_size: Callable[[], None],
        on_apply_theme: Callable[[], None],
        on_open_file: Callable[[], None],
        on_save: Callable[[], None],
        on_check_flow: Callable[[], None],
        on_about: Callable[[], None],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setContentsMargins(8,8,8,8)
        self.layout.setSpacing(5)

        self.header_label = QLabel("Lyrics and FOS generation")
        self.layout.addWidget(self.header_label, alignment=Qt.AlignHCenter)

        self.prompt_area = QLineEdit()
        self.prompt_area.setPlaceholderText("Enter prompt here")
        self.prompt_area.setFixedSize(300, 30)
        self.layout.addWidget(self.prompt_area)

        self.generate_btn = QPushButton("Generate")
        self.generate_btn.clicked.connect(on_generate)
        self.layout.addWidget(self.generate_btn, alignment=Qt.AlignHCenter)

        # generation options
        gen_layout = QHBoxLayout()
        self.layout.addLayout(gen_layout)

        self.lyric_gen_mode = QRadioButton("Lyric gen mode")
        self.fos_gen_mode = QRadioButton("FOS gen mode")

        lyric_col = QVBoxLayout()
        lyric_col.setSpacing(5)
        lyric_col.addWidget(QLabel("Genres"))

        self.genre_list: List[str] = ["Pop","Alt Pop","Hip Hop","Rap","Trap","Rock","Rnb","Punk","Emo","Indie","Folk"]
        self.genres = QComboBox()
        self.genres.addItems(self.genre_list)
        lyric_col.addWidget(self.genres)
        lyric_col.addWidget(self.lyric_gen_mode, alignment=Qt.AlignHCenter)
        gen_layout.addLayout(lyric_col)

        fos_col = QVBoxLayout()
        fos_col.addWidget(QLabel("Figures of Speech"))
        self.figure_of_speech_list: List[str] = [
            "simile","metaphor","analogy","Analogy","Assonance","Consonance","Pun",
            "Alliteration","Onomatopoeia","Oxymoron","Irony"
        ]
        self.figure_of_speech = QComboBox()
        self.figure_of_speech.addItems(self.figure_of_speech_list)
        fos_col.addWidget(self.figure_of_speech)
        fos_col.addWidget(self.fos_gen_mode, alignment=Qt.AlignHCenter)
        gen_layout.addLayout(fos_col)

        # lexicon
        self.header2_label = QLabel("Rhymes and Lexicon")
        self.layout.addWidget(self.header2_label, alignment=Qt.AlignHCenter)

        self.prompt2_area = QLineEdit()
        self.prompt2_area.setPlaceholderText("Enter word search here")
        self.prompt2_area.setFixedSize(300, 30)
        self.layout.addWidget(self.prompt2_area)

        self.search_btn = QPushButton("Search")
        self.search_btn.setFixedSize(150, 40)
        self.search_btn.clicked.connect(on_search_lexicon)
        self.layout.addWidget(self.search_btn, alignment=Qt.AlignHCenter)

        self.options_list: List[str] = [
            "Rhymes","Slant Rhymes","Synonyms","Antonyms","Homophones","Related",
            "Adjectives described by","Nouns described by","Spelling pattern match",
            "hyponyms","Hypernyms","Sound alike"
        ]
        self.rhymes_n_lexicon = QComboBox()
        self.rhymes_n_lexicon.addItems(self.options_list)
        self.layout.addWidget(self.rhymes_n_lexicon, alignment=Qt.AlignHCenter)

        # recorder
        self.m_label = QLabel("Melody & Flow Recorder")
        self.layout.addWidget(self.m_label, alignment=Qt.AlignHCenter)

        self.launch_btn = QPushButton("Launch M recorder")
        self.launch_btn.clicked.connect(on_launch_recorder)
        self.layout.addWidget(self.launch_btn)

        # font size
        self.font_label = QLabel("Font Size")
        self.layout.addWidget(self.font_label)

        self.font_sizes = ["10","12","14","16","18","20","22","24","26"]
        self.font_size_opt = QComboBox()
        self.font_size_opt.addItems(self.font_sizes)
        self.font_size_opt.currentIndexChanged.connect(on_change_font_size)
        self.layout.addWidget(self.font_size_opt)

        # icon buttons rows
        container_layout = QHBoxLayout()
        self.layout.addLayout(container_layout)

        # theme btn
        self.theme_btn = QPushButton("")
        self.theme_btn.setIcon(QIcon(str(icons_dir / "icons8-dark-mode-48.png")))
        self.theme_btn.setIconSize(QSize(30, 30))
        self.theme_btn.clicked.connect(on_apply_theme)

        # file btn
        self.file_btn = QPushButton("")
        self.file_btn.setIcon(QIcon(str(icons_dir / "icons8-new-document-48.png")))
        self.file_btn.setIconSize(QSize(30, 30))
        self.file_btn.setToolTip("files")
        self.file_btn.clicked.connect(on_open_file)

        container_layout.addWidget(self.theme_btn)
        container_layout.addWidget(self.file_btn)

        container2_layout = QHBoxLayout()
        self.layout.addLayout(container2_layout)

        self.flow_btn = QPushButton("")
        self.flow_btn.setIcon(QIcon(str(icons_dir / "icons8-foursquare-64.png")))
        self.flow_btn.setIconSize(QSize(30, 30))
        self.flow_btn.setToolTip("Check flow")
        self.flow_btn.clicked.connect(on_check_flow)

        self.save_btn = QPushButton("")
        self.save_btn.setIcon(QIcon(str(icons_dir / "icons8-save-64.png")))
        self.save_btn.setIconSize(QSize(30, 30))
        self.save_btn.setToolTip("save")
        self.save_btn.clicked.connect(on_save)

        container2_layout.addWidget(self.save_btn)
        container2_layout.addWidget(self.flow_btn)

        container3_layout = QHBoxLayout()
        self.layout.addLayout(container3_layout)

        self.about_btn = QPushButton("")
        self.about_btn.setIcon(QIcon(str(icons_dir / "icons8-brain-64.png")))
        self.about_btn.setIconSize(QSize(30, 30))
        self.about_btn.setToolTip("About")
        self.about_btn.clicked.connect(on_about)

        container3_layout.addWidget(self.about_btn)

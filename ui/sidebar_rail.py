"""
Collapsed sidebar rail (icons-only), VS Code-ish.
"""
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFrame, QToolButton, QVBoxLayout, QWidget, QPushButton

class SidebarRail(QFrame):
    def __init__(
        self,
        icon_theme,
        icon_file,
        icon_save,
        icon_flow,
        icon_about,
        icon_new_song,
        menu_icon,
        on_expand: Callable[[], None],
        on_theme: Callable[[], None],
        on_file: Callable[[], None],
        on_save: Callable[[], None],
        on_flow: Callable[[], None],
        on_new_song: Callable[[], None],
        on_about: Callable[[], None],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setObjectName("sidebarRail")

        layout = QVBoxLayout(self)
        # layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignTop)

        self.toggle_btn = QToolButton()
        self.toggle_btn.setIcon(menu_icon)
        self.toggle_btn.setFixedSize(40, 40)
        self.toggle_btn.setToolTip("Expand sidebar")
        self.toggle_btn.clicked.connect(on_expand)

        layout.addWidget(self.toggle_btn, alignment=Qt.AlignHCenter)

        layout.addSpacing(6)

        # def make_btn(icon, tip, cb):
        #     b = QToolButton()
        #     b.setIcon(icon)
        #     # b.setIconSize(QSize(26, 26))
        #     b.setToolTip(tip)
        #     b.clicked.connect(cb)
        #     return b



        
        self.theme_btn = QPushButton()
        self.theme_btn.setIcon(icon_theme)
        self.theme_btn.setToolTip("Theme")
        self.theme_btn.clicked.connect(on_theme)


        self.new_song_btn = QPushButton()
        self.new_song_btn.setIcon(icon_new_song)
        self.new_song_btn.setToolTip("clear editor")
        self.new_song_btn.clicked.connect(on_new_song)

        self.open_file = QPushButton()
        self.open_file.setToolTip("Open file")
        self.open_file.clicked.connect(on_file)
        self.open_file.setIcon(icon_file)

        self.save = QPushButton()
        self.save.setToolTip("Save")
        self.save.clicked.connect(on_save)
        self.save.setIcon(icon_save)


        self.check_flow = QPushButton()
        self.check_flow.setToolTip("Check flow")
        self.check_flow.clicked.connect(on_flow)
        self.check_flow.setIcon(icon_flow)

        self.about = QPushButton()
        self.about.setToolTip("About")
        self.about.clicked.connect(on_about)
        self.about.setIcon(icon_about)


        layout.addWidget(self.theme_btn, alignment=Qt.AlignHCenter)
        layout.addWidget(self.new_song_btn, alignment=Qt.AlignHCenter)
        layout.addWidget(self.open_file, alignment=Qt.AlignHCenter)
        layout.addWidget(self.save, alignment=Qt.AlignHCenter)
        layout.addWidget(self.check_flow, alignment=Qt.AlignHCenter)
        layout.addWidget(self.about, alignment=Qt.AlignHCenter)
        layout.addStretch(1)

        self.setFixedWidth(56)

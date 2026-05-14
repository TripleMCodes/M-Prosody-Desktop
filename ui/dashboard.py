import os

from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QScrollArea, QSizePolicy
)
from typing import Optional, Callable, List, Any, Dict
from pathlib import Path
from ui.notifications import NotificationToast
from ui.songs_display import SongsDisplayWidget
from services.glass_builder import glass_card
from services.models import Note, SongPreview
from services.preferences import ThemeManager, Preferences
from services.fetch_rhymes import find_rhymes
from stats_db import Stats
from autodidex_cache import DictionaryCache
from themes_db import Themes
from ui.stats_chart import WritingStatsChart

CONFIG_FILE = Path(__file__).parent.parent / "noteworthy files/config.json"

class LLDashboard(QWidget):
    """
    You plug in real handlers by setting:
      - self.on_open_studio: Callable[[], None]
      - self.on_fetch_rhymes: Callable[[str], list[str]]  (can be async later)
      - self.on_save_note: Callable[[str, str], dict]  -> {message, ok}
      - self.on_delete_note: Callable[[str], dict]
      - self.on_refresh_notes: Callable[[], list[Note]]
    """
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        


        self.prefs = Preferences(CONFIG_FILE)
        self.setWindowTitle("/ɛm ˈprɑːsədi/")
        
        self.theme_mgr = ThemeManager()
        self.theme_mgr.load_themes()
        prefs = self.prefs.load()
        self.stats = Stats()
        self.theme = prefs.theme

        self.setStyleSheet(self.theme_mgr.stylesheet_for(self.theme))
    
        # callbacks (inject from app)
        self.on_open_studio: Optional[Callable[[], None]] = None
        self.on_open_studio_with_song: Optional[Callable[[tuple], None]] = None
        self.on_fetch_rhymes: Optional[Callable[[str], List[str]]] = None
        self.on_save_note: Optional[Callable[[str, str], Dict[str, Any]]] = None
        self.on_update_note: Optional[Callable[[str, str], Dict[str, Any]]] = None
        self.on_delete_note: Optional[Callable[[str], Dict[str, Any]]] = None
        self.on_refresh_notes: Optional[Callable[[], List[Note]]] = None
        self.on_get_stats: Optional[Callable[[], None]] = None
        self.on_search_songs: Optional[Callable[[str], List]] = None

        self._current_note_id: str = ""

        meta_root = QVBoxLayout(self)
        meta_root.setContentsMargins(0, 0, 0, 0)
        meta_root.setSpacing(0)

        header_container = QWidget()
        header_container.setObjectName("headerContainer")

        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(20, 20, 20, 20)
        header_layout.setSpacing(6)

        # LOGO
        logo = QLabel()
        logo_path = os.path.join(
            "ui",
            "Icons",
            "logo_no_bg.png"
        )

        pixmap = QPixmap(logo_path)
        pixmap = pixmap.scaled(
            150, 100,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        logo.setPixmap(pixmap)
        logo.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(logo, alignment=Qt.AlignCenter)

        # IPA HEADER
        header = QLabel("<h1>/ɛm ˈprɑːsədi/</h1>")
        header.setAlignment(Qt.AlignCenter)
        header.setObjectName("ipaHeader")

        header_container.setStyleSheet("""
            #headerContainer {
                border-radius: 16px;
                padding: 10px;

                background-color: transparent;

                border: 1px solid rgba(168, 85, 247, 80);
            }

            #headerContainer:hover {
                background-color: transparent;
            }

            #ipaHeader {
                font-size: 20px;
                font-weight: 600;
                color: #a855f7;
            }
            """)

        header_layout.addWidget(header, alignment=Qt.AlignCenter)
        

        header_layout.addWidget(header, alignment=Qt.AlignCenter)

        root = QHBoxLayout()
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)
        meta_root.addWidget(header_container)
        meta_root.addLayout(root)


        # Two main panels
        self.left_panel = self._build_panel()
        self.right_panel = self._build_panel()

        # root.addLayout(header_layout)
        root.addWidget(self.left_panel)
        root.addWidget(self.right_panel)

        # Toast
        self.toast = NotificationToast(self)
        self.chart = WritingStatsChart(self.stats)
        self.chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.chart.setMinimumHeight(360)

        # Content
        self._build_left_content()
        self._build_right_content()

        # initial demo state (replace with real load)
        self.set_stats(writing_time=0, writing_sessions=0, new_songs=0, num_songs=0)
        self.set_draft(artist="", title="", album="")
        self.set_recent_songs([])

    # Panels
    def _build_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("GlassPanel")

        outer = QVBoxLayout(panel)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(12)

        scroll.setWidget(inner)
        outer.addWidget(scroll)

        panel._inner = inner
        panel._inner_layout = inner_layout
        return panel

    def _left_layout(self) -> QVBoxLayout:
        return self.left_panel._inner_layout

    def _right_layout(self) -> QVBoxLayout:
        return self.right_panel._inner_layout

    # Left content: Search / Scratchpad / RimeSearch
    def _build_left_content(self):
        lay = self._left_layout()

        # Search
        card, c, _ = glass_card("<h2>Search</h2>")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search songs / notes / ideas…")
        c.addWidget(self.search_input)


        search_icon_path = Path(__file__).parent / "Icons/icons8-find-64.png"
        search_icon = QIcon(str(search_icon_path))
        self.search_btn = QPushButton()
        self.search_btn.setIcon(search_icon)
        self.search_btn.setIconSize(QSize(32, 32))
        self.search_btn.setObjectName("GhostBtn")
        self.search_btn.clicked.connect(self._noop_search)
        c.addWidget(self.search_btn)

        lay.addWidget(card)

        # Scratchpad
        sp_card, sp, _ = glass_card("<h2>Scratchpad</h2>")
        row = QHBoxLayout()
        row.setSpacing(10)

        self.notes_list = QListWidget()
        self.notes_list.setMinimumHeight(180)
        self.notes_list.itemClicked.connect(self._note_selected)

        right = QVBoxLayout()
        right.setSpacing(10)

        self.note_editor = QTextEdit()
        self.note_editor.setPlaceholderText("Write a note…")

        btns = QHBoxLayout()
        btns.setSpacing(8)

        new_note_icon_path = Path(__file__).parent / "Icons/icons8-add-new-64.png"
        new_note_icon = QIcon(str(new_note_icon_path))
        self.new_note_btn = QPushButton()
        self.new_note_btn.setToolTip("add new note")
        self.new_note_btn.setIcon(new_note_icon)
        self.new_note_btn.setObjectName("GhostBtn")
        self.new_note_btn.clicked.connect(self.create_note)


        save_icon_path =  Path(__file__).parent / "Icons/icons8-save-64.png"
        save_icon = QIcon(str(save_icon_path))
        self.save_note_btn = QPushButton()
        self.save_note_btn.setToolTip("save note")
        self.save_note_btn.setIcon(save_icon)
        self.save_note_btn.clicked.connect(self.save_note)

        delete_icon_path = Path(__file__).parent / "Icons/icons8-delete-48.png"
        delete_icon = QIcon(str(delete_icon_path))
        self.del_note_btn = QPushButton()
        self.del_note_btn.setToolTip("delete note")
        self.del_note_btn.setIcon(delete_icon)
        self.del_note_btn.setObjectName("GhostBtn")
        self.del_note_btn.clicked.connect(self.delete_selected_note)

        btns.addWidget(self.new_note_btn)
        btns.addStretch(1)
        btns.addWidget(self.del_note_btn)
        btns.addWidget(self.save_note_btn)

        right.addWidget(self.note_editor, 1)
        right.addLayout(btns)

        row.addWidget(self.notes_list, 1)
        row.addLayout(right, 2)

        sp.addLayout(row)
        lay.addWidget(sp_card)

        # RimeSearch
        rs_card, rs, _ = glass_card("<h2>Rime Search</h2>")
        self.rhyme_input = QLineEdit()
        self.rhyme_input.setPlaceholderText("Enter a word to rhyme…")

        rs_row = QHBoxLayout()
        rs_row.setSpacing(10)

        self.rhyme_btn = QPushButton()
        self.rhyme_btn.setIcon(search_icon)
        self.rhyme_btn.setToolTip("find rhyme")
        self.rhyme_btn.clicked.connect(self.find_rhyme)

        self.rhyme_loading = QLabel("")
        self.rhyme_loading.setAlignment(Qt.AlignVCenter)

        rs_row.addWidget(self.rhyme_btn)
        rs_row.addWidget(self.rhyme_loading, 1)

        self.rhyme_list = QListWidget()
        self.rhyme_list.setMinimumHeight(160)

        rs.addWidget(self.rhyme_input)
        rs.addLayout(rs_row)
        rs.addWidget(self.rhyme_list)

        lay.addWidget(rs_card)
        lay.addStretch(1)

    # Right content: Stats / Workspace
    def _build_right_content(self):
        lay = self._right_layout()

        # Stats
        st_card, st, _ = glass_card("<h2>Stats</h2>")
        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)

        self.stat_writing_time = self._stat_tile("<h4>Writing time (recently)</h4>", "0")
        self.stat_sessions = self._stat_tile("<h4>Sessions (recently)</h4>", "0")
        self.stat_new_songs = self._stat_tile("<h4>New songs</h4>", "0")
        self.stat_num_songs = self._stat_tile("<h4>Total songs</h4>", "0")

        stats_row.addWidget(self.stat_writing_time)
        stats_row.addWidget(self.stat_sessions)
        stats_row.addWidget(self.stat_new_songs)
        stats_row.addWidget(self.stat_num_songs)

        st.addLayout(stats_row)
        
        # chart_layout = QHBoxLayout()
        # chart_layout.addWidget(chart)

        lay.addWidget(st_card)
        lay.addWidget(self.chart, 1) 
        
        # Workspace
        ws_card, ws, _ = glass_card("<h2>Workspace</h2>")

        self.draft_label = QLabel("Draft")
        self.draft_label.setStyleSheet("font-weight: 600;")
        ws.addWidget(self.draft_label)

        self.draft_meta = QLabel("—")
        self.draft_meta.setWordWrap(True)
        ws.addWidget(self.draft_meta)

        self.open_studio_btn = QPushButton("Open Studio")
        self.open_studio_btn.clicked.connect(self.open_studio)
        ws.addWidget(self.open_studio_btn)

        rec_title = QLabel("<h2>Recent songs</h2>")
        # rec_title.setStyleSheet("font-weight: 600; margin-top: 8px;")
        ws.addWidget(rec_title)

        icons_dir = Path(__file__).parent / "Icons"
        self.recent_songs_display = SongsDisplayWidget(icons_dir)
        self.recent_songs_display.setMinimumHeight(280)
        self.recent_songs_display.song_selected.connect(self._on_song_card_selected)
        self.recent_songs_display.song_delete_requested.connect(self._on_song_card_delete)
        ws.addWidget(self.recent_songs_display)

        lay.addWidget(ws_card)
        lay.addStretch(1)

    def _stat_tile(self, title: str, value: str) -> QFrame:
        tile = QFrame()
        tile.setObjectName("GlassCard")
        lay = QVBoxLayout(tile)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(2)

        t = QLabel(title)
        t.setStyleSheet("opacity: 0.85;")

        v = QLabel(value)
        v.setStyleSheet("font-size: 20px; font-weight: 700;")

        lay.addWidget(t)
        lay.addWidget(v)

        tile._value_label = v
        return tile
    
    # Public setters
    def set_stats(self, writing_time: int, writing_sessions: int, new_songs: int, num_songs: int):
        self.stat_writing_time._value_label.setText(str(writing_time))
        self.stat_sessions._value_label.setText(str(writing_sessions))
        self.stat_new_songs._value_label.setText(str(new_songs))
        self.stat_num_songs._value_label.setText(str(num_songs))

    def set_draft(self, artist: str, title: str, album: str):
        artist = artist or ""
        title = title or ""
        album = album or ""
        if not (artist or title or album):
            self.draft_meta.setText("No active draft yet.")
        else:
            parts = []
            if title:
                parts.append(f"<b>{title}</b>")
            if artist:
                parts.append(f"by {artist}")
            if album:
                parts.append(f"({album})")
            self.draft_meta.setText(" ".join(parts))

    def update_stats(self):
        
        writing_time, sessions, songs_num, total_songs_num = self.on_get_stats()

        h = writing_time // 3600
        m = (writing_time % 3600) // 60
        s = writing_time % 60
        writing_time = f"{h:02d}:{m:02d}:{s:02d}"

        res = self.stats.add_session(sessions)
        sessions = res.get("new_ses", sessions)
        self.set_stats(writing_time=writing_time, writing_sessions=sessions, new_songs=songs_num, num_songs=total_songs_num)
        self.chart.fetch_data()

    def save_writing_time(self, seconds):
                
        res = self.stats.add_writing_time(seconds)

        if res.get("status"):
            writing_time, sessions, songs_num, total_songs_num = self.on_get_stats()

            h = writing_time // 3600
            m = (writing_time % 3600) // 60
            s = writing_time % 60

            writing_time = f"{h:02d}:{m:02d}:{s:02d}"

            self.set_stats(writing_time=writing_time, writing_sessions=sessions, new_songs=songs_num, num_songs=total_songs_num)
            self.chart.refresh()
            print(f"writing time: {seconds}")
        
        self.toast.show_toast(res.get("message"), "error")

    def set_recent_songs(self, songs: List[SongPreview]):
        """Convert SongPreview objects to tuples and display them."""
        song_tuples = []
        for s in songs:
            # Create a tuple with song info (id, title, artist, ...)
            song_tuples.append((s.id, s.title, s.artist, "", "", "", ""))
        self.recent_songs_display.set_songs(song_tuples)

    def set_notes(self, notes: List[Note]):
        self.notes_list.clear()
        for n in notes:
            preview = (n.content or "").strip().splitlines()[0] if n.content else "(empty)"
            label = preview[:60] + ("…" if len(preview) > 60 else "")
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, n)
            self.notes_list.addItem(item)

    
    def open_studio(self):
        if self.on_open_studio:
            self.on_open_studio()
            self.open_studio_btn.setEnabled(False)
            return
        self.toast.show_toast("Open Studio clicked (wire handler).", "info")

    def create_note(self):
        self._current_note_id = ""
        self.note_editor.setPlainText("")
        self.notes_list.clearSelection()
        self.toast.show_toast("New note.", "info", ms=1400)

    def _note_selected(self, item: QListWidgetItem):
        note: Note = item.data(Qt.UserRole)
        if not note:
            return
        self._current_note_id = note.id
        self.note_editor.setPlainText(note.content or "")

    def refresh_notes(self):
        if not self.on_refresh_notes:
            self.toast.show_toast("No refresh handler wired.", "info")
            return
        notes = self.on_refresh_notes()
        self.set_notes(notes)

    def save_note(self):
        content = self.note_editor.toPlainText().strip()
        if not content:
            self.toast.show_toast("Error - note to save empty.", "error")
            return

        if not self.on_save_note:
            self.toast.show_toast("Save note clicked (wire handler).", "info")
            return
        
        if self._current_note_id:
            res = self.on_update_note(self._current_note_id, content)
            ok = bool(res.get("state", False))
            print(ok)
            msg = res.get("message", "Saved." if ok else "Could not save.")
        else:
            res = self.on_save_note(content)
            ok = bool(res.get("state", False))
            print(ok)
            msg = res.get("message", "Saved." if ok else "Could not save.")

        self.toast.show_toast(msg, "success" if ok else "error")

        # refresh list after save
        if self.on_refresh_notes:
            self.set_notes(self.on_refresh_notes())

    def delete_selected_note(self):
        item = self.notes_list.currentItem()
        if not item:
            self.toast.show_toast("No note selected.", "error")
            return
        note: Note = item.data(Qt.UserRole)
        if not note:
            return

        if not self.on_delete_note:
            self.toast.show_toast("Delete note clicked (wire handler).", "info")
            return

        res = self.on_delete_note(note.id)
        ok = bool(res.get("ok", res.get("state", False)))
        msg = res.get("message", "Deleted." if ok else "Could not delete.")

        self.toast.show_toast(msg, "success" if ok else "error")

        self._current_note_id = ""
        self.note_editor.setPlainText("")

        if self.on_refresh_notes:
            self.set_notes(self.on_refresh_notes())

    def find_rhyme(self):
        word = self.rhyme_input.text().strip()
        if not word:
            self.toast.show_toast("Enter a word first.", "error")
            return

        self.rhyme_list.clear()
        self.rhyme_loading.setText("Searching…")

        def finish():
            self.rhyme_loading.setText("")
            # if not self.on_fetch_rhymes:
            #     self.toast.show_toast("Rhyme search not wired.", "info")
            #     return
            try:
                results = find_rhymes(word)
            except Exception as e:
                self.toast.show_toast(f"Rhyme search failed: {e}", "error")
                return
            
            i = 0
            words_list = results["words"]

            if results["phrasal_rhymes"]:
                for p in results["phrasal_rhymes"]:
                    rhyme, score = p[0], p[1]
                    item = f" {rhyme} -> {score:.2f} \n"
                    self.rhyme_list.addItem(QListWidgetItem(item))

            while i <= len(words_list) - 1:
            
                for r in results["word_rhymes"][words_list[i]]:
                    rhyme, score = r[0], r[1]
                    item = f" {rhyme} -> {score:.2f} \n"
                    self.rhyme_list.addItem(QListWidgetItem(item))
                i += 1

            
        # mimic loading state; replace with real async later
        QTimer.singleShot(150, finish)

    def apply_theme(self, theme):
        self.setStyleSheet(self.theme_mgr.stylesheet_for(theme))
       

    def _noop_search(self):
        q = self.search_input.text().strip()
        if not q:
            self.toast.show_toast("Type something to search.", "info")
        elif not self.on_search_songs:
            self.toast.show_toast(f"Search not wired.", "info")
        else:
            results = self.on_search_songs(q)
            if isinstance(results, dict):
                self.toast.show_toast(f"Search error: {results.get('message', 'Unknown error')}", "error")
                return
            
            if not results:
                self.toast.show_toast(f"No songs found for {q}", "info")
                return
            
            # Display results using the new widget
            self.recent_songs_display.set_songs(results)
            self.toast.show_toast(f"Found {len(results)} song(s)", "success")
    
    def _on_song_card_selected(self, song_data):
        """Handle song card selection (View/Edit button clicked)."""
        if song_data and len(song_data) >= 1:
            # Open studio with the selected song
            if self.on_open_studio_with_song:
                self.on_open_studio_with_song(song_data)
            else:
                self.toast.show_toast("Open studio handler not wired.", "info")
    
    def _on_song_card_delete(self, song_data):
        """Handle song card delete request."""
        if song_data and len(song_data) >= 1:
            song_id = song_data[0]
            title = song_data[1] if len(song_data) > 1 else "Unknown"
            self.toast.show_toast(f"Delete requested: {title}", "info")
            print(f"Delete requested for song: {song_id}")

    # Keep toast positioned on resize
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.toast.isVisible():
            self.toast._reposition()

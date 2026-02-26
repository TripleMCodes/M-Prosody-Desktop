from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QScrollArea, QSizePolicy
)
from typing import Optional, Callable, List, Any, Dict
from pathlib import Path
from ui.notifications import NotificationToast
from services.glass_builder import glass_card
from services.models import Note, SongPreview
from services.preferences import ThemeManager, Preferences
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
        self.theme_mgr = ThemeManager()
        self.theme_mgr.load_themes()
        prefs = self.prefs.load()
        self.stats = Stats()
        self.theme = prefs.theme

        self.setStyleSheet(self.theme_mgr.stylesheet_for(self.theme))
    
        # callbacks (inject from app)
        self.on_open_studio: Optional[Callable[[], None]] = None
        self.on_fetch_rhymes: Optional[Callable[[str], List[str]]] = None
        self.on_save_note: Optional[Callable[[str, str], Dict[str, Any]]] = None
        self.on_update_note: Optional[Callable[[str, str], Dict[str, Any]]] = None
        self.on_delete_note: Optional[Callable[[str], Dict[str, Any]]] = None
        self.on_refresh_notes: Optional[Callable[[], List[Note]]] = None
        self.on_get_stats: Optional[Callable[[], None]] = None

        self._current_note_id: str = ""

        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        # Two main panels
        self.left_panel = self._build_panel()
        self.right_panel = self._build_panel()

        root.addWidget(self.left_panel, 1)
        root.addWidget(self.right_panel, 1)

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

        # Scroll area to mimic Svelte .scrollable
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
        card, c, _ = glass_card("Search")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search songs / notes / ideas…")
        c.addWidget(self.search_input)

        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("GhostBtn")
        self.search_btn.clicked.connect(self._noop_search)
        c.addWidget(self.search_btn)

        lay.addWidget(card)

        # Scratchpad
        sp_card, sp, _ = glass_card("Scratchpad")
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

        self.new_note_btn = QPushButton("New")
        self.new_note_btn.setObjectName("GhostBtn")
        self.new_note_btn.clicked.connect(self.create_note)

        self.save_note_btn = QPushButton("Save")
        self.save_note_btn.clicked.connect(self.save_note)

        self.del_note_btn = QPushButton("Delete")
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
        rs_card, rs, _ = glass_card("Rime Search")
        self.rhyme_input = QLineEdit()
        self.rhyme_input.setPlaceholderText("Enter a word to rhyme…")

        rs_row = QHBoxLayout()
        rs_row.setSpacing(10)

        self.rhyme_btn = QPushButton("Find rhymes")
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
        st_card, st, _ = glass_card("Stats")
        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)

        self.stat_writing_time = self._stat_tile("(recent)Writing time", "0")
        self.stat_sessions = self._stat_tile("(recent)Sessions", "0")
        self.stat_new_songs = self._stat_tile("New songs", "0")
        self.stat_num_songs = self._stat_tile("Total songs", "0")

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
        ws_card, ws, _ = glass_card("Workspace")

        self.draft_label = QLabel("Draft")
        self.draft_label.setStyleSheet("font-weight: 600;")
        ws.addWidget(self.draft_label)

        self.draft_meta = QLabel("—")
        self.draft_meta.setWordWrap(True)
        ws.addWidget(self.draft_meta)

        self.open_studio_btn = QPushButton("Open Studio")
        self.open_studio_btn.clicked.connect(self.open_studio)
        ws.addWidget(self.open_studio_btn)

        rec_title = QLabel("Recent songs")
        rec_title.setStyleSheet("font-weight: 600; margin-top: 8px;")
        ws.addWidget(rec_title)

        self.recent_songs_list = QListWidget()
        self.recent_songs_list.setMinimumHeight(220)
        ws.addWidget(self.recent_songs_list)

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

        m = writing_time // 60
        s = writing_time % 60
        writing_time = f"{m:02d}:{s:02d} min"

        res = self.stats.add_session(sessions)
        sessions = res.get("new_ses", sessions)
        self.set_stats(writing_time=writing_time, writing_sessions=sessions, new_songs=songs_num, num_songs=total_songs_num)
        self.chart.fetch_data()

    def save_writing_time(self, seconds):
                
        res = self.stats.add_writing_time(seconds)

        if res.get("status"):
            writing_time, sessions, songs_num, total_songs_num = self.on_get_stats()

            m = writing_time // 60
            s = writing_time % 60
            writing_time = f"{m:02d}:{s:02d} min"

            self.set_stats(writing_time=writing_time, writing_sessions=sessions, new_songs=songs_num, num_songs=total_songs_num)
            self.chart.refresh()
            print(f"writing time: {seconds}")
        
        self.toast.show_toast(res.get("message"), "error")

    def set_recent_songs(self, songs: List[SongPreview]):
        self.recent_songs_list.clear()
        for s in songs:
            item = QListWidgetItem(f"{s.title} — {s.artist}")
            item.setData(Qt.UserRole, s)
            self.recent_songs_list.addItem(item)

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
            if not self.on_fetch_rhymes:
                self.toast.show_toast("Rhyme search not wired.", "info")
                return
            try:
                results = self.on_fetch_rhymes(word) or []
            except Exception as e:
                self.toast.show_toast(f"Rhyme search failed: {e}", "error")
                return

            for r in results:
                self.rhyme_list.addItem(QListWidgetItem(str(r)))

        # mimic loading state; replace with real async later
        QTimer.singleShot(150, finish)

    def apply_theme(self, theme):
        self.setStyleSheet(self.theme_mgr.stylesheet_for(theme))
       

    def _noop_search(self):
        q = self.search_input.text().strip()
        if not q:
            self.toast.show_toast("Type something to search.", "info")
        else:
            self.toast.show_toast(f"Searching for “{q}”… (wire handler)", "info")

    # Keep toast positioned on resize
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.toast.isVisible():
            self.toast._reposition()

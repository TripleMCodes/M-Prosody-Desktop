from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Dict, Any

from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QScrollArea, QSizePolicy
)


# -----------------------------
# Styling
# -----------------------------
GLASS_QSS = """
/* ===== Theme vars-ish ===== */
QWidget {
    font-family: "Segoe UI";
    color: #f5e9ff;
}

/* Container background can be set by parent app stylesheet; this focuses on the cards */
QFrame#GlassPanel {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(120, 50, 180, 64),
        stop:1 rgba(25, 8, 40, 140)
    );
    border-radius: 22px;
    border: 1px solid rgba(168, 85, 247, 64);
    padding: 18px;
}

QFrame#GlassCard {
    background: rgba(40, 10, 60, 115);
    border-radius: 18px;
    border: 1px solid rgba(168, 85, 247, 55);
    padding: 14px;
}

QLabel#SectionTitle {
    font-size: 16px;
    font-weight: 600;
}

QLineEdit, QTextEdit {
    background: rgba(18, 0, 24, 160);
    border: 1px solid rgba(168, 85, 247, 55);
    border-radius: 12px;
    padding: 10px;
    selection-background-color: rgba(168, 85, 247, 120);
}

QTextEdit {
    min-height: 90px;
}

QPushButton {
    background: rgba(168, 85, 247, 120);
    border: 1px solid rgba(168, 85, 247, 140);
    border-radius: 12px;
    padding: 10px 12px;
    font-weight: 600;
}

QPushButton:hover {
    background: rgba(199, 125, 255, 150);
}

QPushButton:pressed {
    background: rgba(124, 58, 237, 160);
}

QPushButton#GhostBtn {
    background: transparent;
    border: 1px solid rgba(168, 85, 247, 90);
}

QListWidget {
    background: rgba(18, 0, 24, 120);
    border: 1px solid rgba(168, 85, 247, 55);
    border-radius: 12px;
    padding: 6px;
}

QListWidget::item {
    padding: 10px;
    margin: 4px;
    border-radius: 10px;
}

QListWidget::item:selected {
    background: rgba(168, 85, 247, 120);
}

/* Notification toast */
QFrame#Toast {
    background: rgba(18, 0, 24, 210);
    border: 1px solid rgba(168, 85, 247, 120);
    border-radius: 14px;
    padding: 12px 14px;
}
"""


# -----------------------------
# Data models (optional)
# -----------------------------
@dataclass
class Note:
    id: str
    content: str


@dataclass
class SongPreview:
    id: str
    title: str
    artist: str
    album: str = ""


# -----------------------------
# Notification Toast
# -----------------------------
class NotificationToast(QFrame):
    closed = Signal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setVisible(False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        self.icon = QLabel("✅")
        self.icon.setFixedWidth(20)

        self.msg = QLabel("")
        self.msg.setWordWrap(True)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("GhostBtn")
        self.close_btn.setFixedSize(34, 34)
        self.close_btn.clicked.connect(self.hide_toast)

        layout.addWidget(self.icon)
        layout.addWidget(self.msg, 1)
        layout.addWidget(self.close_btn)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide_toast)

    def show_toast(self, message: str, kind: str = "success", ms: int = 2600):
        # kind: "success" | "error" | "info"
        if kind == "error":
            self.icon.setText("⛔")
        elif kind == "info":
            self.icon.setText("ℹ️")
        else:
            self.icon.setText("✅")

        self.msg.setText(message)
        self.setVisible(True)
        self.raise_()

        self._timer.stop()
        self._timer.start(ms)

        # Position bottom-right-ish inside parent
        self._reposition()

    def _reposition(self):
        if not self.parentWidget():
            return
        p = self.parentWidget()
        margin = 18
        w = min(520, max(320, p.width() // 2))
        self.setFixedWidth(w)
        self.adjustSize()
        self.move(p.width() - self.width() - margin, p.height() - self.height() - margin)

    def hide_toast(self):
        self.setVisible(False)
        self.closed.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # keep neat if parent resizes; handled by parent too


# -----------------------------
# Helper: Glass card wrapper
# -----------------------------
def glass_card(title: str) -> tuple[QFrame, QVBoxLayout, QLabel]:
    card = QFrame()
    card.setObjectName("GlassCard")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(14, 14, 14, 14)
    layout.setSpacing(10)

    t = QLabel(title)
    t.setObjectName("SectionTitle")
    layout.addWidget(t)

    return card, layout, t


# -----------------------------
# Dashboard Widget
# -----------------------------
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
        self.setStyleSheet(GLASS_QSS)

        # callbacks (inject from your app)
        self.on_open_studio: Optional[Callable[[], None]] = None
        self.on_fetch_rhymes: Optional[Callable[[str], List[str]]] = None
        self.on_save_note: Optional[Callable[[str, str], Dict[str, Any]]] = None
        self.on_delete_note: Optional[Callable[[str], Dict[str, Any]]] = None
        self.on_refresh_notes: Optional[Callable[[], List[Note]]] = None

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

        # Content
        self._build_left_content()
        self._build_right_content()

        # initial demo state (replace with real load)
        self.set_stats(writing_time=0, writing_sessions=0, new_songs=0, num_songs=0)
        self.set_draft(artist="", title="", album="")
        self.set_recent_songs([])

    # -----------------------------
    # Panels
    # -----------------------------
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

    # -----------------------------
    # Left content: Search / Scratchpad / RimeSearch
    # -----------------------------
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

    # -----------------------------
    # Right content: Stats / Workspace
    # -----------------------------
    def _build_right_content(self):
        lay = self._right_layout()

        # Stats
        st_card, st, _ = glass_card("Stats")
        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)

        self.stat_writing_time = self._stat_tile("Writing time", "0")
        self.stat_sessions = self._stat_tile("Sessions", "0")
        self.stat_new_songs = self._stat_tile("New songs", "0")
        self.stat_num_songs = self._stat_tile("Total songs", "0")

        stats_row.addWidget(self.stat_writing_time)
        stats_row.addWidget(self.stat_sessions)
        stats_row.addWidget(self.stat_new_songs)
        stats_row.addWidget(self.stat_num_songs)

        st.addLayout(stats_row)
        lay.addWidget(st_card)

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

    # -----------------------------
    # Public setters (bind-like)
    # -----------------------------
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

    # -----------------------------
    # Actions (map to your Svelte functions)
    # -----------------------------
    def open_studio(self):
        if self.on_open_studio:
            self.on_open_studio()
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

        res = self.on_save_note(content, self._current_note_id)
        ok = bool(res.get("ok", res.get("state", False)))
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

    def _noop_search(self):
        # placeholder: you can hook this into your local DB search or API
        q = self.search_input.text().strip()
        if not q:
            self.toast.show_toast("Type something to search.", "info")
        else:
            self.toast.show_toast(f"Searching for “{q}”… (wire handler)", "info")

    # -----------------------------
    # Keep toast positioned on resize
    # -----------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.toast.isVisible():
            self.toast._reposition()


# -----------------------------
# Demo runner
# -----------------------------
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    w = LLDashboard()
    w.resize(1200, 720)

    # Demo wiring
    w.on_open_studio = lambda: w.toast.show_toast("Opening Studio…", "success")
    w.on_fetch_rhymes = lambda word: [f"{word} — {x}" for x in ("time", "crime", "slime", "prime", "climb")]
    w.on_refresh_notes = lambda: [
        Note(id="1", content="Hook idea: neon angels in a dead city."),
        Note(id="2", content="Verse concept: rhythms like collapsing stars."),
    ]
    w.on_save_note = lambda content, note_id: {"ok": True, "message": "Note saved."}
    w.on_delete_note = lambda note_id: {"ok": True, "message": "Note deleted."}

    w.set_stats(writing_time=12, writing_sessions=340, new_songs=3, num_songs=28)
    w.set_draft(artist="Triple MC", title="Polaroid Dreams", album="Late Anamnesis II")
    w.set_recent_songs([
        SongPreview(id="a", title="Roswell", artist="The Pretty Wild"),
        SongPreview(id="b", title="Wildfire", artist="Against the Current"),
    ])
    w.set_notes(w.on_refresh_notes())

    w.show()
    sys.exit(app.exec())

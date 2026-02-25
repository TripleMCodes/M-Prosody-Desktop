"""
Main window for Lyrical Lab .

This file keeps orchestration logic, while UI subcomponents live in ui/* and
non-UI helpers live in services/*.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pyphen
import pronouncing
import sounddevice as sd
from scipy.io.wavfile import write

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QThread, Signal, QSize, QTimer
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QListWidgetItem, QMessageBox,
    QSplitter, QWidget, QStackedWidget, QPushButton, QVBoxLayout, QLabel
)

from services.autosave import Autosaver
from services.flow_analysis import alignment_score, get_stress_pattern, highlight_flow
from services.generation import GenerationService
from services.lexicon import LexiconService
from services.lyrics_library import LyricsLibrary, Song
from services.preferences import Preferences, ThemeManager
from ui.editor import EditorPanel
from ui.sidebar_rail import SidebarRail
from ui.sidebar_songs import SongsSidebar
from ui.sidebar_tools import ToolsSidebar
from ui.timer import FloatingTimer
from online_features import LyricalLabAPI  # file
from services.online_gate import OnlineFeatureGate


from recorder import VoiceRecorder


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logging.disable()  


CONFIG_FILE = Path(__file__).parent.parent / "noteworthy files/config.json"
TEMP_FILE = Path(__file__).parent.parent / "noteworthy files/temp.txt"
dic = pyphen.Pyphen(lang="en")


class RecorderThread(QThread):
    finished = Signal(str)

    def __init__(self, duration=0, samplerate=44100, song="recording"):
        super().__init__()
        self.duration = duration
        self.samplerate = samplerate
        self.recording = []
        self.running = False
        self.song_name = song
        self.basepath = Path(__file__).parent
        self.count = 1

    def run(self):
        self.running = True
        with sd.InputStream(samplerate=self.samplerate, channels=1, callback=self.callback):
            while self.running:
                sd.sleep(100)

        filename = self.basepath / f"recording{self.count}.wav"
        audio_data = np.concatenate(self.recording, axis=0)
        write(filename, self.samplerate, audio_data)
        self.finished.emit(str(filename))

    def callback(self, indata, frames, time, status):
        if status:
            self.recording.append(indata.copy())

    def stop(self):
        self.running = False
        self.count += 1


class SidebarMode:
    TOOLS = 0
    SONGS = 1


class MProsody(QWidget):
    theme_changed_signal = Signal(str)
    new_song_saved = Signal()

    def __init__(self):
        super().__init__()

        # --- state ---
        self.search_mode: Optional[str] = None
        self.lyric_mode = "lyric"
        self.fos_mode = "fos"
        self.openning_app = True

        self.sidebar_collapsed = False
        self.sidebar_expanded_width = 200 #340

        self.current_song_id: Optional[int] = None
        self.current_sidebar_face = SidebarMode.TOOLS

        # --- services ---
        self.prefs = Preferences(CONFIG_FILE)
        self.theme_mgr = ThemeManager()
        self.autosaver = Autosaver(TEMP_FILE)
        self.generation = GenerationService()
        self.lexicon = LexiconService()
        self.library = LyricsLibrary()

        # recorder thread (legacy)
        self.m_recorder = RecorderThread()

        # --- main layout ---
        self.main_layout = QHBoxLayout(self)

        # build UI parts
        self._build_editor()
        self._build_sidebars()
        self._build_splitter_layout()

       # writing time tracker
        self.writing_timer = FloatingTimer(parent=None, start_seconds=0)
        self.writing_timer.show()
        self.writing_timer.move(40, 40)
        
        # inactivity detection for pausing
        self.inactivity_timer = QTimer()
        self.inactivity_timer.timeout.connect(self.pause_writing_timer)
        self.inactivity_timeout = 5000  # pause after 5 seconds of inactivity
        
        # connect editor changes to track writing activity
        self.editor.writing_editor.textChanged.connect(self.on_writing_activity)

        
         
        # apply prefs/theme/font + restore autosave
        self.init_wrapper()


        self.api = LyricalLabAPI()
        self.online_gate = OnlineFeatureGate(self.api, parent_window=self)

        # show on startup
        self.online_gate.run_startup_prompt_if_needed()

    # UI building
    def _build_editor(self):
        wc_icon = Path(__file__).parent / "Icons/icons8-word-file-64.png"
        self.editor = EditorPanel(
            autosave_cb=self.autosave,
            update_word_count_cb=self.update_word_count,
            update_syllables_cb=self.update_syllable_counts,
            wc_icon_path=wc_icon,
        )

    def _build_sidebars(self):
        icons_dir = Path(__file__).parent / "Icons"

        self.tools = ToolsSidebar(
            icons_dir=icons_dir,
            on_generate=self.generate,
            on_search_lexicon=self.search_lexicon,
            on_launch_recorder=self.launch_m_recorder,
            on_change_font_size=self.change_font_size,
            on_apply_theme=self.apply_theme,
            on_open_file=self.open_file,
            on_save=self.save_file,
            on_check_flow=lambda: self.check_flow_of_selection(),
            on_about=self.about_app,
        )
        # hook mode radio buttons
        self.tools.lyric_gen_mode.toggled.connect(self.update_search_mode)
        self.tools.fos_gen_mode.toggled.connect(self.update_search_mode)

        self.songs = SongsSidebar(
            on_flip=self.flip_sidebar_face,
            on_refresh=self.refresh_song_list,
            on_item_clicked=self.on_song_clicked,
        )

        # stacked (tools/songs)
        self.sidebar_stack = QStackedWidget()
        self.sidebar_stack.addWidget(self.tools)
        self.sidebar_stack.addWidget(self.songs)
        self.sidebar_stack.setCurrentIndex(SidebarMode.TOOLS)

        # top-left controls for the *expanded* sidebar
        self.toggle_sidebar_btn = QPushButton("☰")
        self.toggle_sidebar_btn.setToolTip("Toggle sidebar")
        self.toggle_sidebar_btn.setFixedSize(36, 36)
        self.toggle_sidebar_btn.clicked.connect(self.toggle_sidebar)

        self.flip_sidebar_btn = QPushButton("🎛 / 🎵")
        self.flip_sidebar_btn.setToolTip("Flip sidebar: Tools ↔ Songs")
        self.flip_sidebar_btn.setFixedSize(36, 36)
        self.flip_sidebar_btn.clicked.connect(self.flip_sidebar_face)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(4)
        top_row.addWidget(self.toggle_sidebar_btn)
        top_row.addWidget(self.flip_sidebar_btn)
        top_row.addStretch(1)

        self.sidebar_shell = QWidget()
        shell_layout = QVBoxLayout(self.sidebar_shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(6)
        shell_layout.addLayout(top_row)
        shell_layout.addWidget(self.sidebar_stack, stretch=1)
        self.sidebar_shell.setMinimumWidth(320)

        # collapsed rail uses icons from tools buttons
        self.sidebar_rail = SidebarRail(
            icon_theme=self.tools.theme_btn.icon(),
            icon_file=self.tools.file_btn.icon(),
            icon_save=self.tools.save_btn.icon(),
            icon_flow=self.tools.flow_btn.icon(),
            icon_about=self.tools.about_btn.icon(),
            on_expand=self.toggle_sidebar,
            on_theme=self.apply_theme,
            on_file=self.open_file,
            on_save=self.save_file,
            on_flow=lambda: self.check_flow_of_selection(),
            on_about=self.about_app,
        )
        self.sidebar_rail.setVisible(False)

        # container holds both shell and rail
        self.sidebar_container = QWidget()
        container_layout = QHBoxLayout(self.sidebar_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container_layout.addWidget(self.sidebar_shell)
        container_layout.addWidget(self.sidebar_rail)

    def _build_splitter_layout(self):
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(self.sidebar_container)
        self.main_splitter.addWidget(self.editor)
        self.main_splitter.setSizes([340, 900])
        self.main_layout.addWidget(self.main_splitter)

    def toggle_timer(self):
        if self.timer.isVisible():
            self.timer.hide()
        else:
            self.timer.show()
            self.timer.raise_()

    def on_writing_activity(self):
        """Called whenever user types in the editor."""
        self.writing_timer.start()
        self.inactivity_timer.stop()
        self.inactivity_timer.start(self.inactivity_timeout)

    def pause_writing_timer(self):
        """Pause timer after inactivity."""
        self.inactivity_timer.stop()
        self.writing_timer.pause()

    def toggle_timer(self):
        if self.writing_timer.isVisible():
            self.writing_timer.hide()
        else:
            self.writing_timer.show()
            self.writing_timer.raise_()

    # Sidebar behaviors
    def set_sidebar_mode(self, mode: int) -> None:
        self.current_sidebar_face = mode
        self.sidebar_stack.setCurrentIndex(mode)
        if mode == SidebarMode.SONGS:
            self.refresh_song_list(self.songs.query())

    def flip_sidebar_face(self):
        next_mode = SidebarMode.SONGS if self.current_sidebar_face == SidebarMode.TOOLS else SidebarMode.TOOLS
        self.set_sidebar_mode(next_mode)

    def toggle_sidebar(self):
        """Collapse/expand sidebar into an icon rail (VS Code-ish)."""
        sizes = self.main_splitter.sizes()
        sidebar_w = sizes[0]

        full_widget = self.sidebar_shell

        if self.sidebar_collapsed:
            self.sidebar_rail.setVisible(False)
            full_widget.setVisible(True)
            target_sidebar = self.sidebar_expanded_width
            self.animate_splitter(sidebar_w, target_sidebar)
            self.sidebar_collapsed = False
            self.toggle_sidebar_btn.setToolTip("Collapse sidebar")
        else:
            if sidebar_w > 80:
                self.sidebar_expanded_width = sidebar_w
            full_widget.setVisible(False)
            self.sidebar_rail.setVisible(True)
            target_sidebar = 56
            self.animate_splitter(sidebar_w, target_sidebar)
            self.sidebar_collapsed = True
            self.toggle_sidebar_btn.setToolTip("Expand sidebar")

    def animate_splitter(self, start_sidebar, end_sidebar, duration=200):
        total = self.main_splitter.size().width()

        anim = QPropertyAnimation(self.main_splitter, b"")
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._splitter_anim = anim

        anim.setStartValue(0.0)
        anim.setEndValue(1.0)

        def on_value_changed(t):
            sidebar = int(start_sidebar + (end_sidebar - start_sidebar) * t)
            editor = max(200, total - sidebar)
            self.main_splitter.setSizes([sidebar, editor])

        anim.valueChanged.connect(on_value_changed)
        anim.start()

    # Preferences / themes / font
    def init_wrapper(self):
        prefs = self.prefs.load()
        self.mode = prefs.theme
        self.font_size = prefs.font_size

        self.theme_mgr.load_themes()
        self.setStyleSheet(self.theme_mgr.stylesheet_for(self.mode))

        # apply font
        self.change_font_size()

        # restore autosave
        last = self.autosaver.load()
        if last:
            for ed in self.editor.editors:
                ed.setText(last)

        self.openning_app = False

    def apply_theme(self):
        # cycle theme
        self.mode = self.theme_mgr.next_theme(getattr(self, "mode", "dark"))
        self.setStyleSheet(self.theme_mgr.stylesheet_for(self.mode))

       
        base = Path(__file__).parent / "Icons"
        l_mode = base / "icons8-light-64.png"
        d_mode = base / "icons8-dark-mode-48.png"
        n_mode = base / "icons8-day-and-night-50.png"

        icon = QIcon(str(d_mode))
        if self.mode == "light":
            icon = QIcon(str(l_mode))
        elif self.mode == "neutral":
            icon = QIcon(str(n_mode))

        self.tools.theme_btn.setIcon(icon)
        self.sidebar_rail.theme_btn.setIcon(icon)
        self.theme_changed_signal.emit(self.mode)
        

    def change_font_size(self):
        if self.openning_app:
            font = QFont("Arial", int(self.font_size))
        else:
            font = QFont("Arial", int(self.tools.font_size_opt.currentText()))

        for editor in self.editor.editors:
            editor.setFont(font)

    # -------------------------
    # Generation / lexicon
    # -------------------------
    def update_search_mode(self):
        if self.tools.fos_gen_mode.isChecked():
            self.search_mode = self.fos_mode
        elif self.tools.lyric_gen_mode.isChecked():
            self.search_mode = self.lyric_mode

    def generate(self):
        if not self.online_gate.require_online("Lyric generation"):
            return
        
        user_prompt = self.tools.prompt_area.text().strip()
        if not user_prompt:
            self.editor.display_editor.setPlainText("Please enter a prompt first!")
            return

        if self.search_mode == self.lyric_mode:
            genre = self.tools.genres.currentText()
            raw_output = self.generation.generate_lyrics(user_prompt, genre)
            if raw_output is None:
                self.editor.display_editor.setText("API request failed, couldn't generate lyrics")
                return

            bullet_items = "".join(
                f"<li>{line.strip()}</li>" for line in raw_output.splitlines() if line.strip()
            )
            formatted = f"🎵 <b>{genre} Lyric Suggestions:</b><br><br><ul>{bullet_items}</ul>"
            self.editor.display_editor.setHtml(formatted)

        elif self.search_mode == self.fos_mode:
            fos = self.tools.figure_of_speech.currentText()
            raw_output = self.generation.generate_fos(user_prompt, fos)
            if raw_output is None:
                self.editor.display_editor.setText("⚠️ API request failed, couldn't generate output")
                return

            numbered_items = "".join(
                f"<li>{line.strip()}</li>" for line in raw_output.splitlines() if line.strip()
            )
            formatted = f"✨ <b>{fos} Suggestions for '{user_prompt}':</b><br><br><ol>{numbered_items}</ol>"
            self.editor.display_editor.setHtml(formatted)

        self.tools.prompt_area.clear()

    def search_lexicon(self):
        if not self.online_gate.require_online("Lyric generation"):
            return
        
        part = self.tools.rhymes_n_lexicon.currentText()
        word = self.tools.prompt2_area.text().strip()
        if not word:
            return

        # map to lexicon service
        opt = self.tools.options_list
        if part == opt[0]:
            res = f"Rhymes with '{word}': {self.lexicon.rhymes(word)}"
        elif part == opt[1]:
            res = f"Slant rhymes for '{word}': {self.lexicon.slant_rhymes(word)}"
        elif part == opt[2]:
            res = f"Synonyms for '{word}': {self.lexicon.synonyms(word)}"
        elif part == opt[3]:
            res = f"Antonyms for '{word}': {self.lexicon.antonyms(word)}"
        elif part == opt[4]:
            res = f"Homophones for '{word}': {self.lexicon.homophones(word)}"
        elif part == opt[5]:
            res = f"Related words for '{word}': {self.lexicon.related(word)}"
        elif part == opt[6]:
            res = f"Adjectives for '{word}': {self.lexicon.adjectives(word)}"
        elif part == opt[7]:
            res = f"Nouns described by '{word}': {self.lexicon.nouns_described_by(word)}"
        elif part == opt[8]:
            res = f"Spelled like '{word}': {self.lexicon.spelled_like(word)}"
        elif part == opt[9]:
            res = f"More specific than '{word}': {self.lexicon.hyponyms(word)}"
        elif part == opt[10]:
            res = f"More general than '{word}': {self.lexicon.hypernyms(word)}"
        else:
            res = f"Sounds like '{word}': {self.lexicon.sounds_like(word)}"

        self.editor.display_editor.setPlainText(res)
        self.tools.prompt2_area.clear()

    # -------------------------
    # Word count / syllables / autosave
    # -------------------------
    def update_word_count(self):
        words_num = len(self.editor.writing_editor.toPlainText().split())
        self.editor.set_word_count(words_num)

    def syllable_count(self, word: str) -> int:
        phones = pronouncing.phones_for_word(word)
        if not phones:
            return len(dic.inserted(word).split("-"))
        return pronouncing.syllable_count(phones[0])

    def update_syllable_counts(self):
        lines = self.editor.writing_editor.toPlainText().splitlines()
        results = []
        # print ("you're writing")
        for line in lines:
            words = line.split()
            results.append(f"{line}({sum(self.syllable_count(w) for w in words)})")
        self.editor.display_editor.setPlainText("\n".join(results) if results else "")

    def autosave(self):
        self.autosaver.maybe_save(self.editor.writing_editor.toPlainText())

    # -------------------------
    # Songs sidebar + DB
    # -------------------------
    def refresh_song_list(self, query: str):
        self.songs.clear()

        songs = self.library.list_songs()
        if isinstance(songs, dict):
            self.songs.add_item(QListWidgetItem(f"{songs.get('message', 'DB error')}"))
            return

        q = (query or "").strip().lower()   
        for row in songs:
            if len(row) < 7:
                continue

            song_id, title, artist, album, genre, mood, lyrics = row[:7]
            hay = " ".join([str(title or ""), str(artist or ""), str(album or ""), str(genre or ""), str(mood or "")]).lower()
            if q and q not in hay:
                continue

            label = f"{title} — {artist}"
            if mood:
                label += f"  ·  {mood}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, row)
            self.songs.add_item(item)

    def on_song_clicked(self, item):
        row = item.data(Qt.UserRole)
        if not row or len(row) < 7:
            return
        song_id, title, artist, album, genre, mood, lyrics = row[:7]
        self.current_song_id = song_id
        self.editor.load_song_fields(title or "", artist or "", album or "", genre or "", mood or "")
        self.editor.load_lyrics(lyrics or "")

    def save_file(self) -> None:
        lyrics = self.editor.writing_editor.toPlainText().strip()
        title = self.editor.song_title_input.text().strip()
        artist = self.editor.song_artist_input.text().strip()

        if not lyrics:
            QMessageBox.warning(self, "Lyrics Required", "Please provide lyrics.")
            return
        if not title:
            QMessageBox.warning(self, "Title Required", "Please provide song title.")
            return
        if not artist:
            QMessageBox.warning(self, "Artist Required", "Please provide artist name.")
            return

        song = Song(
            title=title,
            artist=artist,
            album=self.editor.song_album_input.text().strip(),
            genre=self.editor.song_genre_input.text().strip(),
            mood=self.editor.song_mood_input.text().strip(),
            lyrics=lyrics,
        )
        # print(f"current song id: {self.current_song_id}")
        if self.current_song_id is not None:
            msg = self.library.update_song(self.current_song_id, song)
            self.new_song_saved.emit()
        else:
            msg = self.library.create_song(song)

        if msg.get("state"):
            QMessageBox.information(self, "Done", msg.get("message", "Saved."))
            self.refresh_song_list(self.songs.query())
            self.new_song_saved.emit()
        else:
            QMessageBox.critical(self, "Error", msg.get("message", "Something went wrong."))

    # -------------------------
    # Misc actions
    # -------------------------
    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "open file", "", "Text Files (*.txt);;(*.html);;(*.csv);;(*.py);;(*.md)")
        if not file_name:
            return
        with open(file_name, "r", encoding="utf-8") as f:
            text = f.read()
        for editor in self.editor.editors:
            editor.setText(text)

    def launch_m_recorder(self):
        self.m_recorder = VoiceRecorder()
        self.m_recorder.show()

    def about_app(self):
        about_info = """
        <h2>🎵 Welcome to Lyrical Lab</h2>
        <p><b>Lyrical Lab</b> is the all-in-one songwriting companion for <b>Autodidex</b>.
        This powerful sub-app helps you transform your ideas into polished songs.</p>

        <p>Whether you're battling writer's block or fine-tuning your masterpiece,
        Lyrical Lab has you covered. Generate lyric suggestions in your chosen genre,
        or spark your creativity with a library of figures of speech.</p>

        <p>Explore our <b>Comprehensive Lexicon</b> for instant access to
        rhymes, synonyms, and related words.</p>

        <p>Our unique <b>Flow Analysis</b> tool shows the syllable count of each line
        and highlights stressed and unstressed syllables, helping you perfect rhythm
        and delivery.</p>

        <p>Record melody ideas, save your work, and customize your workspace with
        themes and font sizes. <b>Lyrical Lab</b> is your personal studio for
        precision, purpose, and perfect flow.</p>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("About Lyrical Lab")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(about_info)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    def check_flow_of_selection(self):
        cursor = self.editor.writing_editor.textCursor()
        selected = cursor.selectedText()
        if not selected.strip():
            self.editor.display_editor.setPlainText("⚠️ No text selected.")
            return

        lines = selected.splitlines()
        patterns = [get_stress_pattern(line) for line in lines]
        html = highlight_flow(patterns, lines)

        score = alignment_score(patterns)
        if score is not None:
            html += f"<b>Flow Alignment Score: {score:.2f}</b>"

        self.editor.display_editor.setHtml(html)

from pathlib import Path
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from ui.dashboard import LLDashboard
from scratch_pad_db import ScratchPad
from lyrics_db import Lyrics
from stats_db import Stats
from services.models import Note, SongPreview
from services.lyrics_library import LyricsLibrary
from db_migration_table import MigrationManager

# ── App version (bump this with each release) ─────────────────────────────────
CURRENT_VERSION = "1.0.0"


def check_for_updates_async(parent_window):
    """
    Runs a version check after the dashboard has rendered.
    Called via QTimer — does not block the UI thread.
    Note: dialog.exec() is modal but only runs if an update is available.
    """
    from updater import fetch_version_info, is_newer, VERSION_URL
    from ui.update_dialog import UpdateDialog
    from db_migration_table import MigrationManager, MIGRATIONS
    from PySide6.QtWidgets import QDialog

    info = fetch_version_info(VERSION_URL)

    if not info:
        return  # no network or bad response — silently skip

    remote_version = info.get("version")
    if not remote_version or not info.get("download_url"):
        return

    if not is_newer(remote_version, CURRENT_VERSION):
        return  # already up to date

    # Show the update dialog centred over the dashboard
    dialog = UpdateDialog(
        version_info=info,
        current_version=CURRENT_VERSION,
        parent=parent_window,
    )

    if dialog.exec() == QDialog.Accepted:
        MigrationManager().migrate(MIGRATIONS, app_version=CURRENT_VERSION)

def main():

    window_icon = Path(__file__).parent / "ui" / "Icons" / "logo_no_bg.png"

    scratch_pad = ScratchPad()
    lyrics = Lyrics()

    app = QApplication(sys.argv)
    w = LLDashboard()
    w.setWindowTitle("M-Prosody - Dashboard")
    w.setWindowIcon(QIcon(str(window_icon)))
    w.showMaximized()

    # ── Schedule update check 1.5 s after the window is shown ────────────────
    # Delay lets the dashboard fully render before any network I/O begins.
    QTimer.singleShot(1500, lambda: check_for_updates_async(w))

    def open_studio(song_data=None):
        from ui.main_window import MProsody
        lyrics_library = LyricsLibrary()

        latest_songs = get_lastest_songs()
        
        window = MProsody() 
        window.showMaximized()
        window.theme_changed_signal.connect(w.apply_theme)
        window.new_song_saved.connect(w.update_stats)

        window.new_song_saved.connect(update_dashboard_recent_songs)
        window.recorded_writing_time.connect(w.save_writing_time)
        window.show()
        
        # Load song if provided
        if song_data and len(song_data) >= 7:
            song_id, title, artist, album, genre, mood, lyrics = song_data[:7]
            data = lyrics_library.get_song_by_id(song_id)
            lyrics = data[6]
            window.current_song_id = song_id
            window.editor.load_song_fields(title or "", artist or "", album or "", genre or "", mood or "")
            window.editor.load_lyrics(lyrics or "")

    def get_notes():
        notes = scratch_pad.get_all_content()
        notes_obj_list: Note = []

        for n in notes:
            note = Note(id=n[0], content=n[1])
            notes_obj_list.append(note)
        
        return notes_obj_list

    def create_note(note):
        return scratch_pad.add_content(note)
    
    def delete_note(id): 
        return scratch_pad.delete_content(id)
    
    def update_note(id, note):
        return scratch_pad.update_content(id, note)

    def get_lastest_songs():
        songs = lyrics.get_all_songs()
        songs_obj_list = []

        for s in songs:
            song = SongPreview(id=s[0], title=s[1], artist=s[2])
            songs_obj_list.append(song)
        
        return songs_obj_list
    
    def update_dashboard_recent_songs():
        latest_songs = get_lastest_songs()
        w.set_recent_songs(latest_songs)

    def get_stats():
        stats = Stats()

        ls = lyrics.get_latest_songs_count()
        ts = lyrics.get_all_songs_count()

        # if ls.get("status"):
        #     songs_num = ls.get("message", 0)[0]
        
        # if ts.get('status'):
        #     total_songs_num = ts.get('message', 0)[0]

        songs_num = ls.get("message", [0])[0] if ls.get("status") else 0
        total_songs_num = ts.get("message", [0])[0] if ts.get("status") else 0
            
        stats = stats.get_res_stats()
        writing_time = stats[1]
        sessions = stats[2] 

        return writing_time, sessions, songs_num, total_songs_num
    
    def search_songs(query: str):
        """Search songs by title, artist, or lyrics content."""
        return lyrics.search_songs(query)

    w.on_open_studio = open_studio
    w.on_open_studio_with_song = lambda song_data: open_studio(song_data)
    w.on_refresh_notes = get_notes
    w.on_save_note = create_note
    w.on_update_note = update_note
    w.on_delete_note = delete_note
    w.on_get_stats = get_stats
    w.on_search_songs = search_songs
    writing_time, sessions, songs_num, total_songs_num = get_stats()

    h = writing_time // 3600
    m = (writing_time % 3600) // 60
    s = writing_time % 60
    writing_time = f"{h:02d}:{m:02d}:{s:02d}"
    
    w.set_stats(writing_time=writing_time, writing_sessions=sessions, new_songs=songs_num, num_songs=total_songs_num)
    latest_songs = get_lastest_songs()
    w.set_recent_songs(latest_songs)
    w.set_notes(w.on_refresh_notes())
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

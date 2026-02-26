import sys
from PySide6.QtWidgets import QApplication
from ui.dashboard import LLDashboard
from scratch_pad_db import ScratchPad
from lyrics_db import Lyrics
from stats_db import Stats
from services.models import Note, SongPreview

def main():

    scratch_pad = ScratchPad()
    lyrics = Lyrics()
    
    app = QApplication(sys.argv)
    w = LLDashboard()
    w.resize(1200, 720)

    def open_studio():
        from ui.main_window import MProsody

        window = MProsody() 
        window.theme_changed_signal.connect(w.apply_theme)
        window.new_song_saved.connect(w.update_stats)
        window.recorded_writing_time.connect(w.save_writing_time)
        window.show()

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
    
    def get_stats():
        stats = Stats()

        ls = lyrics.get_latest_songs_count()
        ts = lyrics.get_all_songs_count()

        if ls.get("status"):
            songs_num = ls.get("message", 0)[0]
        
        if ts.get('status'):
            total_songs_num = ts.get('message', 0)[0]
            
        stats = stats.get_res_stats()
        writing_time = stats[1]
        sessions = stats[2]

        return writing_time, sessions, songs_num, total_songs_num
        

    w.on_open_studio = open_studio
    w.on_fetch_rhymes = lambda word: [f"{word} — {x}" for x in ("time", "crime", "slime", "prime", "climb")]
    w.on_refresh_notes = get_notes
    w.on_save_note = create_note
    w.on_update_note = update_note
    w.on_delete_note = delete_note
    w.on_get_stats = get_stats
    writing_time, sessions, songs_num, total_songs_num = get_stats()

    m = writing_time // 60
    s = writing_time % 60
    writing_time = f"{m:02d}:{s:02d} min"
    
    w.set_stats(writing_time=writing_time, writing_sessions=sessions, new_songs=songs_num, num_songs=total_songs_num)
    w.set_draft(artist="Triple MC", title="Polaroid Dreams", album="Late Anamnesis II")
    latest_songs = get_lastest_songs()
    w.set_recent_songs(latest_songs)
    w.set_notes(w.on_refresh_notes())
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()           
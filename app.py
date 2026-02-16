import sys
from PySide6.QtWidgets import QApplication
# from ui.main_window import MProsody
from ui.dashboard import LLDashboard
from services.models import Note, SongPreview

def main():
    # app = QApplication(sys.argv)
    # window = MProsody() 
    # window.show()
    # sys.exit(app.exec())

    app = QApplication(sys.argv)
    w = LLDashboard()
    w.resize(1200, 720)


    def open_studio():
        from ui.main_window import MProsody

        window = MProsody() 
        window.show()


    w.on_open_studio = open_studio
    # w.on_open_studio = lambda: w.toast.show_toast("Opening Studio…", "success")
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



if __name__ == "__main__":
    main()           
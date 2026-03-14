"""
DB-facing wrapper for song persistence.

Uses Lyrics from lyrics_db.py but provides a clearer interface for the UI.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from lyrics_db import Lyrics


SongRow = Tuple[Any, ...]  # (id, title, artist, album, genre, mood, lyrics, ...)


@dataclass
class Song:
    title: str
    artist: str
    album: str = ""
    genre: str = ""
    mood: str = ""
    lyrics: str = ""


class LyricsLibrary:
    def __init__(self):
        self.db = Lyrics()

    def list_songs(self) -> Union[List[SongRow], Dict[str, Any]]:
        return self.db.get_all_songs()

    def create_song(self, song: Song) -> Dict[str, Any]:
        return self.db.save_new_song(song.__dict__)

    def update_song(self, song_id: int, song: Song) -> Dict[str, Any]:
        return self.db.update_song(song.__dict__, song_id)

    def delete_song(self, song_id: int) -> Dict[str, Any]:
        return self.db.delete_song(song_id)

    def get_song_versions(self, song_id: int) -> List[Tuple]:
        return self.db.get_song_versions(song_id)
    
    def get_song_by_id(self, song_id:int) -> tuple | None:
        results =  self.db.get_song_by_id(song_id)
        if results["status"]:
            return results['message']
        return None



testing = LyricsLibrary()


# lst = testing.list_songs()
# print(lst)
# print(testing.get_song_by_id(2))
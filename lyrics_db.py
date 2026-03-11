import sqlite3
from pathlib import Path
import hashlib
from datetime import datetime, timedelta
import logging
logging.basicConfig(level=logging.DEBUG)

class Lyrics():
    """A class that deals with storing and retrieving lyrics."""

    def __init__(self):
        self.db_path = Path(__file__).parent / "lyrical_lab.db"
        self.conn = sqlite3.connect(self.db_path)
        self.conn_cursor = self.conn.cursor()
        self.lyrics_table = "lyrics_table"
        self.lyrics_versions = "lyrics_versions"
        self.local_id = 1 #default
#===============================================select method(s)======================================
#=================================================================================================
    def get_all_songs(self) -> list | dict:
        """Get all songs"""

        query = f"SELECT * FROM {self.lyrics_table};"
        try:
            self.conn_cursor.execute(query)
            songs = self.conn_cursor.fetchall()
            # print(songs)
            return songs
        except sqlite3.DatabaseError as e:
            logging.debug(e)
            return {"message": "Database Error - Please try again."}
        except Exception as e:
            logging.debug(e)
            return {"message": "Error - Please try again."}

    def get_latest_songs_count(self) -> dict:

        one_week_ago = datetime.now() - timedelta(days=7)

        query = f"""SELECT count(*) from (
            SELECT * FROM {self.lyrics_table} WHERE created_at >= "{one_week_ago}");"""
        
        try:
            self.conn_cursor.execute(query)
            songs_num = self.conn_cursor.fetchone()
            return {"message": songs_num, "status": True}
        except sqlite3.DatabaseError as e:
            logging.debug(e)
            return {"message": "Database Error - Please try again."}
        except Exception as e:
            logging.debug(e)
            return {"message": "Error - Please try again."}

    def get_all_songs_count(self) -> dict:

        query = f"""SELECT count(*) from {self.lyrics_table};"""

        try:
            self.conn_cursor.execute(query)
            total_songs_num = self.conn_cursor.fetchone()
            return {"message": total_songs_num, "status": True}
        except sqlite3.DatabaseError as e:
            logging.debug(e)
            return {"message": "Database Error - Please try again."}
        except Exception as e:
            logging.debug(e)
            return {"message": "Error - Please try again."}
        

#===============================================insert method(s)======================================
#=====================================================================================================
    def save_new_song(self, data: dict) -> dict | None | sqlite3.Error:
        """
        Save new song.
        title, artist, lyrics are necessary,
        mood, album, genre are optional
        """
        title, artist, lyrics, mood, genre, album = self._destructure_dict(data)

        is_unique = self._is_unique(str(title))
        if isinstance(is_unique, bool):
            if not is_unique:
                return {"message": f"Song with '{title}' title already exists", "state": False}
        elif isinstance(is_unique, dict):
            return {"message": "Error - Please try again", "state": False}

        lyrics_hash = self._hash_lyrics(lyrics)

        query = f"""
            INSERT INTO {self.lyrics_table}
            (
                title, artist, album, genre, mood, lyrics,
                version, lyrics_hash, hash_algo, local_profile_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        try:
            self.conn_cursor.execute(
                query,
                (
                    title,
                    artist,
                    album,
                    genre,
                    mood,
                    lyrics,
                    1,
                    lyrics_hash,
                    "sha256",
                    self.local_id,
                ),
            )
            self._commit_data()
            return {"message": "Song saved successfully", "state": True}

        except sqlite3.DatabaseError as e:
            logging.debug(e)
            return {"message": "Error - Please try again", "state": False}
    # def save_new_song(self, data:dict) -> dict | None | sqlite3.Error:
    #     """
    #         Save new song.
    #         title, artist, lyircs are necessary,
    #         mood, album, genre are optional
    #     """
    #     title, artist, lyrics, mood, genre, album = self._destructure_dict(data)

    #     query = f"""
    #                 INSERT INTO {self.lyrics_table} (title, artist, album, genre, mood, lyrics, local_profile_id) VALUES (?,?,?,?,?,?,?);
    #             """
        
    #     is_unique = self._is_unique(str(title))
    #     if isinstance(is_unique, bool):
    #         if not is_unique:
    #             return {"message": f"Song with '{title}' title already exists", "state": False}
    #     elif isinstance(is_unique, dict):
    #         return {"message": "Error - Please try again", "state": False}
    #     try:
    #         self.conn_cursor.execute(query, (title, artist, album, genre, mood, lyrics, self.local_id ))
    #         self._commit_data()
    #         return {"message": "Song saved successfully", "state": True}
    #     except sqlite3.DatabaseError as e:
    #         logging.debug(e)
    #         return {"message": "Error - Please try again", "state": True}
#===================================update method(s)===============================================
#==================================================================================================

    def update_song(self, data: dict, song_id: int) -> dict:
        """Update a particular song with versioning support."""
        title, artist, lyrics, mood, genre, album = self._destructure_dict(data)

        current_song = self._get_song_by_id(song_id)
        if not current_song:
            return {"message": "Song not found.", "state": False}

        (
            current_id,
            current_title,
            current_artist,
            current_album,
            current_genre,
            current_mood,
            current_lyrics,
            current_version,
            current_lyrics_hash,
            current_cloud_status,
        ) = current_song

        new_lyrics_hash = self._hash_lyrics(lyrics)
        lyrics_changed = new_lyrics_hash != current_lyrics_hash

        try:
            self.conn_cursor.execute("BEGIN")

            if lyrics_changed:
                # 1. Archive old HEAD into lyrics_versions
                version_query = f"""
                    INSERT INTO {self.lyrics_versions}
                    (lyrics_id, version, lyrics, lyrics_hash, hash_algo, note)
                    VALUES (?, ?, ?, ?, ?, ?);
                """
                self.conn_cursor.execute(
                    version_query,
                    (
                        current_id,
                        current_version,
                        current_lyrics,
                        current_lyrics_hash,
                        "sha256",
                        "manual save",
                    ),
                )

                # 2. Update HEAD with incremented version
                new_version = current_version + 1
                new_cloud_status = "dirty" if current_cloud_status == "uploaded" else current_cloud_status

                update_query = f"""
                    UPDATE {self.lyrics_table}
                    SET title = ?,
                        artist = ?,
                        album = ?,
                        genre = ?,
                        mood = ?,
                        lyrics = ?,
                        version = ?,
                        lyrics_hash = ?,
                        hash_algo = ?,
                        cloud_status = ?,
                        updated_at = datetime('now')
                    WHERE id = ?;
                """

                self.conn_cursor.execute(
                    update_query,
                    (
                        title,
                        artist,
                        album,
                        genre,
                        mood,
                        lyrics,
                        new_version,
                        new_lyrics_hash,
                        "sha256",
                        new_cloud_status,
                        song_id,
                    ),
                )
            else:
                # Lyrics did not change: update metadata only
                update_query = f"""
                    UPDATE {self.lyrics_table}
                    SET title = ?,
                        artist = ?,
                        album = ?,
                        genre = ?,
                        mood = ?,
                        lyrics = ?,
                        updated_at = datetime('now')
                    WHERE id = ?;
                """

                self.conn_cursor.execute(
                    update_query,
                    (
                        title,
                        artist,
                        album,
                        genre,
                        mood,
                        lyrics,
                        song_id,
                    ),
                )

            self._commit_data()
            return {"message": "Song successfully updated", "state": True}

        except sqlite3.DatabaseError as e:
            self.conn.rollback()
            logging.debug(e)
            return {"message": "Database Error - Please try again.", "state": False}

        except sqlite3.DataError as e:
            self.conn.rollback()
            logging.debug(e)
            return {"message": "Error - Please ensure to provide all required fields.", "state": False}
    # def update_song(self, data:dict, id:int) -> dict:
    #     """Update a particular song"""
    #     title, artist, lyrics, mood, genre, album = self._destructure_dict(data)

    #     query = f"""
    #                UPDATE {self.lyrics_table}
    #                 SET title = ?, artist = ?, 
    #                 album = ?, genre = ?, 
    #                 mood = ?, lyrics = ?
    #                 WHERE id = ?;
    #             """
    #     # is_unique = self._is_unique(title)
    #     # if isinstance(is_unique, bool):
    #     #     if not is_unique:
    #     #         return {"message": f"Song with '{title}' title already exists", "state": False}
    #     # if isinstance(is_unique, dict):
    #     #     return {"message": is_unique.get("message"), "state": False}
    #     try:
    #         self.conn_cursor.execute(query, (title, artist, album, genre, mood, lyrics, id,))
    #         self._commit_data()
    #         return {"message": "Song successfully updated", "state": True}
    #     except sqlite3.DatabaseError as e:
    #         logging.debug(e)
    #         return {"message": "Database Error - Please try again.", "state":False}
    #     except sqlite3.DataError as e:
    #         logging.debug(e)
    #         return {"message": "Error - Please ensure to provide all required fields.", "state": False}
#===================================delete method(s)==========================================
#====================================================================================================
    def delete_song(self, id:int) -> dict:
        """
        Docstring for delete_song

        :param id: song id
        :type id: int
        :return: result details
        :rtype: dict
        """

        query = f"DELETE FROM {self.lyrics_table} WHERE id = ?;"
        try:
            self.conn_cursor.execute(query, (id))
            self._commit_data()
            return {"message": f"Song successfully deleted.", "state": True}
        except sqlite3.DatabaseError as e:
            logging.debug(e)
            return {"message": "Database Error - Please try again", "state": False}
        except Exception as e:
            logging.debug(e)
            return {"message": "Error - Please try again", "state": False}
#===================================internal call method(s)==========================================
#====================================================================================================
    
    def _normalize_lyrics(self, lyrics: str) -> str:
        if not lyrics:
            return ""
        lyrics = lyrics.replace("\r\n", "\n").replace("\r", "\n")
        lyrics = "\n".join(line.rstrip() for line in lyrics.split("\n"))
        return lyrics.rstrip("\n")

    
    def _hash_lyrics(self, lyrics: str) -> str:
        normalized = self._normalize_lyrics(lyrics)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _get_song_by_id(self, song_id: int):
        query = f"""
            SELECT id, title, artist, album, genre, mood, lyrics, version, lyrics_hash, cloud_status
            FROM {self.lyrics_table}
            WHERE id = ?;
        """
        self.conn_cursor.execute(query, (song_id,))
        return self.conn_cursor.fetchone()

    def _commit_data(self):
        """Commits data to data base (does not close connection)"""
        self.conn.commit()

    def _is_unique(self, title:str) -> bool | dict:
        """Checks if the title of the song is unique when adding a new song
            True -> song is unique
            False -> song is not unique

        """

        query = f"SELECT * FROM {self.lyrics_table} WHERE title = ? COLLATE NOCASE;"
        try:
            self.conn_cursor.execute(query, (title,))
            song = self.conn_cursor.fetchone()
            logging.debug(song)
            if not song:
                return True
            return False
        except sqlite3.DatabaseError as e:
            logging.debug(e)
            return {"message": "Database Error - Please try again"}
        except Exception as e:
            logging.debug(e)
            return {"message": "Error - Please try again"}
        
    def _destructure_dict(self, data : dict) -> str:
        """Destructure dict with song detail"""

        if not data.get("title"):
            return {"message": "Please provide song title"}
        title = data.get("title")
        if not data.get("artist"):
            return {"message": "Please provide artist name"}
        artist = data.get("artist")
        if not data.get("lyrics"):
            return {"message": "Please provide lyrics"}
        lyrics = data.get("lyrics")

        mood = data.get("mood", "")
        genre = data.get("genre", "")
        album = data.get("album", "")

        return title, artist, lyrics, mood, genre, album

        
        
if __name__ == "__main__":

    l_lab = Lyrics()

    print(l_lab.get_latest_songs_count().get('message')[0])
    print(l_lab.get_all_songs_count())
    # print(l_lab.get_all_songs())

    # res = l_lab.save_new_song(song)
    # logging.debug(res)

    # res = l_lab._is_unique("When time comes")
    # print(res)

    # songs = l_lab.get_all_songs()
    # logging.debug(songs)
    # for song in songs:
    #     logging.debug(song[0])
    #     logging.debug(song[1])
    #     logging.debug(song[2])
    #     logging.debug(song[3])
    #     logging.debug(song[4])
    #     logging.debug(song[5])

    # res = l_lab._is_unique("a lil song")
    # logging.debug(res)

    # res = l_lab._destructure_dict(data=song)
    # logging.debug(res)

    # title, artist, lyrics, mood, genre, album = l_lab._destructure_dict(song)

    # logging.debug(f"title: {title}")
    # logging.debug(f"artist: {artist}")
    # logging.debug(f"lyrics: {lyrics}")
    # logging.debug(f"mood: {mood}")
    # logging.debug(f"genre: {genre}")
    # logging.debug(f"album: {album}")
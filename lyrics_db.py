import re
import sqlite3
from pathlib import Path
import hashlib
from datetime import datetime, timedelta
import logging
import uuid
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
        
        # Add client_uid column if not exists
        try:
            self.conn_cursor.execute("ALTER TABLE lyrics_table ADD COLUMN client_uid TEXT")
        except sqlite3.OperationalError:
            pass  # column already exists
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
    
    def get_song_by_id(self, id:int) -> dict:

        query = f"SELECT * FROM {self.lyrics_table} where id = ?;"
        try:
            self.conn_cursor.execute(query, (id,))
            song = self.conn_cursor.fetchone()
            return {"message": song, "status": True}
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
        
        client_uid = str(uuid.uuid4())

        query = f"""
            INSERT INTO {self.lyrics_table}
            (
                title, artist, album, genre, mood, lyrics,
                version, lyrics_hash, hash_algo, local_profile_id, client_uid
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
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
                    client_uid,
                ),
            )
            self._commit_data()
            return {"message": "Song saved successfully", "state": True}

        except sqlite3.DatabaseError as e:
            logging.debug(e)
            return {"message": "Error - Please try again", "state": False}


    def save_downloaded_song(self, data: dict) -> dict:
        try:
            title = data.get("title")
            artist = data.get("artist")
            lyrics = data.get("lyrics")

            if not title or not artist or not lyrics:
                return {"message": "Missing required fields", "state": False}
                print("Missing required fields")

            album = data.get("album", "")
            genre = data.get("genre", "")
            mood = data.get("mood", "")

            cloud_song_id = data.get("cloud_song_id")
            cloud_owner_user_id = data.get("cloud_owner")

            # Ensure uniqueness
            if not self._is_unique(title):
                title = self._resolve_duplicate_title(title)

            query = f"""
                SELECT 1 FROM {self.lyrics_table}
                WHERE cloud_owner_user_id = ? AND cloud_song_id = ?
            """
            self.conn_cursor.execute(query, (cloud_owner_user_id, cloud_song_id))

            if self.conn_cursor.fetchone():
                return {"message": "Song already exists locally", "state": False}

            lyrics_hash = self._hash_lyrics(lyrics)
            client_uid = str(uuid.uuid4())

            query = f"""
                INSERT INTO {self.lyrics_table}
                (
                    title, artist, album, genre, mood, lyrics,
                    version, lyrics_hash, hash_algo,
                    local_profile_id, cloud_owner_user_id,
                    cloud_song_id, cloud_status, client_uid 
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """

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
                    cloud_owner_user_id,
                    cloud_song_id,
                    "dirty",
                    client_uid,
                ),
            )

            self._commit_data()

            return {"message": "Song downloaded successfully", "state": True}

        except Exception as e:
            print(e)
            logging.exception("Error saving downloaded song")
            return {"message": "Error - Please try again", "state": False}


#===================================update method(s)===============================================
#==================================================================================================

    def update_song(self, data: dict, song_id: int) -> dict:
        """Update a particular song with versioning support."""
        title, artist, lyrics, mood, genre, album = self._destructure_dict(data)

        current_song = self._get_song_by_id(song_id)
        if not current_song:
            return {"message": "Song not found.", "state": False}

        print(current_song)

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
            current_hash_alg,
            local_profile_id,
            clound_owner_user_id,
            cloud_song_id,
            current_cloud_status,
            created_at,
            updated_at,
            clent_uid

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
    

    def update_after_upload(self, owner_id, song_id, client_uid, id):

        query = f"""UPDATE {self.lyrics_table}
            SET cloud_status = 'uploaded',
                cloud_owner_user_id = ?,
                cloud_song_id = ?,
                client_uid = COALESCE(client_uid, ?)
            WHERE id = ?;"""

        try:
            self.conn_cursor.execute(query, (owner_id, song_id, client_uid, id,))
            self._commit_data()
            return {"message": "Song uploaded successfully.", "status": True}
        
        except sqlite3.DatabaseError as e:
            self.conn.rollback()
            logging.debug(e)
            return {"message": "Database Error - Please try again.", "state": False}

        except sqlite3.DataError as e:
            self.conn.rollback()
            logging.debug(e)
            return {"message": "Error - Please ensure to provide all required fields.", "state": False}

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
            self.conn_cursor.execute(query, (id,))
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
            SELECT id, title, artist, album, genre, mood, lyrics, version, lyrics_hash, hash_algo, local_profile_id, cloud_owner_user_id, cloud_song_id, cloud_status, created_at, updated_at, client_uid
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
        
    def get_song_versions(self, song_id: int) -> list:
        """Get all versions of a song."""
        query = f"SELECT id, lyrics_id, version, lyrics, created_at, lyrics_hash, hash_algo FROM {self.lyrics_versions} WHERE lyrics_id = ? ORDER BY version DESC;"
        try:
            self.conn_cursor.execute(query, (song_id,))
            versions = self.conn_cursor.fetchall()
            print("versions")
            print(versions)
            return versions
        except sqlite3.DatabaseError as e:
            logging.debug(e)
            return []
        except Exception as e:
            logging.debug(e)
            return []
        
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

    

    def _resolve_duplicate_title(self, title: str) -> str:
        """
        Ensures a unique title by appending (copy), (copy 2), (copy 3), etc.
        """

        # Get all titles that start with this base title
        query = f"""
            SELECT title FROM {self.lyrics_table}
            WHERE title LIKE ?;
        """

        self.conn_cursor.execute(query, (f"{title}%",))
        existing_titles = [row[0] for row in self.conn_cursor.fetchall()]

        # If no conflict, return original
        if title not in existing_titles:
            return title

        # Pattern to match: Song (copy), Song (copy 2), etc.
        pattern = re.compile(rf"^{re.escape(title)} \(copy(?: (\d+))?\)$")

        max_copy_number = 1  # Start at 1 for "(copy)"

        for existing in existing_titles:
            match = pattern.match(existing)
            if match:
                number = match.group(1)
                if number:
                    max_copy_number = max(max_copy_number, int(number))
                else:
                    max_copy_number = max(max_copy_number, 1)

        # First duplicate → "(copy)"
        if max_copy_number == 1:
            return f"{title} (copy)"

        # Next duplicates → "(copy N)"
        return f"{title} (copy {max_copy_number + 1})"

        
        
if __name__ == "__main__":

    l_lab = Lyrics()

    # print(l_lab.get_latest_songs_count().get('message')[0])
    # print(l_lab.get_all_songs_count())


    # song_data = l_lab.get_song_by_id(3)['message']

    res = l_lab.update_after_upload(1, 2, "713300be-f9eb-4c6b-b4ba-bd77c2072bcd", 1)

    print(res)

    # print(song_data['message'])

    # client_uid = song_data[16] if len(song_data) > 16 else None
    # if not client_uid:
    #     client_uid = str(uuid.uuid4())
    #     print(client_uid)
        # Update local db
        # self.library.db.conn_cursor.execute("UPDATE lyrics_table SET client_uid = ? WHERE id = ?", (client_uid, song_id))
        # self.library.db._commit_data()


    # Prepare data for API
    # data = {
    #     "song_name": song_data[1],
    #     "song_artist": song_data[2],
    #     "song_album": song_data[3] or None,
    #     "song_genre": song_data[4] or "Pop",
    #     "song_mood": song_data[5] or None,
    #     "song_lyrics": song_data[6],
    #     "client_uid": client_uid,
    #     "song_id": song_data[12] if song_data[12] else None  # cloud_song_id
    # }

    # print(data)
    # print(l_lab.get_all_songs())

    # res = l_lab.save_new_song(song)
    # logging.debug(res)

    # res = l_lab._is_unique("When time comes")
    # print(res)

    # songs = l_lab.get_all_songs()
    # logging.debug(songs)
    # for song in songs:
    #     logging.debug(song[0])a
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
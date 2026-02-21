import sqlite3
from pathlib import Path
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
#==================================================================================================
    def save_new_song(self, data:dict) -> dict | None | sqlite3.Error:
        """
            Save new song.
            title, artist, lyircs are necessary,
            mood, album, genre are optional
        """
        title, artist, lyrics, mood, genre, album = self._destructure_dict(data)

        query = f"""
                    INSERT INTO {self.lyrics_table} (title, artist, album, genre, mood, lyrics, local_profile_id) VALUES (?,?,?,?,?,?,?);
                """
        
        is_unique = self._is_unique(str(title))
        if isinstance(is_unique, bool):
            if not is_unique:
                return {"message": f"Song with '{title}' title already exists", "state": False}
        elif isinstance(is_unique, dict):
            return {"message": "Error - Please try again", "state": False}
        try:
            self.conn_cursor.execute(query, (title, artist, album, genre, mood, lyrics, self.local_id ))
            self._commit_data()
            return {"message": "Song saved successfully", "state": True}
        except sqlite3.DatabaseError as e:
            logging.debug(e)
            return {"message": "Error - Please try again", "state": True}
#===================================update method(s)===============================================
#==================================================================================================
    def update_song(self, data:dict, id:int) -> dict:
        """Update a particular song"""
        title, artist, lyrics, mood, genre, album = self._destructure_dict(data)

        query = f"""
                   UPDATE {self.lyrics_table}
                    SET title = ?, artist = ?, 
                    album = ?, genre = ?, 
                    mood = ?, lyrics = ?
                    WHERE id = ?;
                """
        is_unique = self._is_unique(title)
        if isinstance(is_unique, bool):
            if not is_unique:
                return {"message": f"Song with '{title}' title already exists", "state": False}
        if isinstance(is_unique, dict):
            return {"message": is_unique.get("message"), "state": False}
        try:
            self.conn_cursor.execute(query, (title, artist, album, genre, mood, lyrics, id,))
            self._commit_data()
            return {"message": "Song successfully updated", "state": True}
        except sqlite3.DatabaseError as e:
            logging.debug(e)
            return {"message": "Database Error - Please try again.", "state":False}
        except sqlite3.DataError as e:
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
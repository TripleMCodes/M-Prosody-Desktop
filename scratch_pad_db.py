import sqlite3
from pathlib import Path
import logging
logging.basicConfig(level=logging.DEBUG)


class ScratchPad():

    def __init__(self):
        self.db_path = Path(__file__).parent / "lyrical_lab.db"
        self.conn = sqlite3.connect(self.db_path)
        self.conn_cursor = self.conn.cursor()
        self.scratch_pad = "scratch_pad"
        self.local_profile_id = 1 #default
    
    def _commit_data(self):
        """Commits data to data base (does not close connection)"""
        self.conn.commit()


    
    def _is_unique(self, content:str) -> bool | dict:
        """
            Checks if the content unique when adding new content
            True -> content is unique
            False -> content is not unique
        """

        query = f"SELECT * FROM {self.scratch_pad} WHERE content = ? COLLATE NOCASE;"
        try:
            self.conn_cursor.execute(query, (content,))
            content = self.conn_cursor.fetchone()
            logging.debug(content)
            if not content:
                return True
            return False
        except sqlite3.DatabaseError as e:
            logging.debug(e)
            return {"message": "Database Error - Please try again"}
        except Exception as e:
            logging.debug(e)
            return {"message": "Error - Please try again"}

    def get_all_content(self):
        """
            Gets all the scratchpad data
        """

        query = f"""SELECT * FROM {self.scratch_pad};"""
        try:
            self.conn_cursor.execute(query)
            notes = self.conn_cursor.fetchall()
            return notes
        except sqlite3.DatabaseError as e:
            logging.debug(e)
            return {"message": "Database Error - Please try again"}
        except Exception as e:
            logging.debug(e)
            return {"message": "Error - Please try again"}
        

    def add_content(self, content: str) -> dict:
        
        is_unique = self._is_unique(str(content))
        if isinstance(is_unique, bool):
            if not is_unique:
                return {"message": f"Content with already exists", "state": False}
        elif isinstance(is_unique, dict):
            return {"message": "Error - Please try again", "state": False}

        query = f"""INSERT INTO {self.scratch_pad} (content, local_profile_id) VALUES (?, ?);"""

        try:
            self.conn_cursor.execute(query, (content, self.local_profile_id,))
            self._commit_data()
            return {"message": "Note saved successfully."}
        except sqlite3.DatabaseError as e:
            logging.debug(e)
            return {"message": "Database Error - Please try again"}
        except Exception as e:
            logging.debug(e)
            return {"message": "Error - Please try again"}
        
    def update_content(self, old_content: str, new_content: str) -> dict:
        """
        Docstring for update_content
        
        :param self: object reference
        :param old_content: old note to be updated
        :type old_content: str
        :param new_content: new note
        :type new_content: str
        :return: message dict
        :rtype: dict
        """

        is_unique = self._is_unique(str(new_content))
        if isinstance(is_unique, bool):
            if not is_unique:
                return {"message": f"Content with already exists", "state": False}
        elif isinstance(is_unique, dict):
            return {"message": "Error - Please try again", "state": False}
        
        query = """
                UPDATE scratch_pad 
                SET content = ?
                WHERE content = ?;
                    """
        try:
            self.conn_cursor.execute(query, (new_content, old_content))
            self._commit_data()
            return {"message": "Note successfully updated."}
        except sqlite3.DatabaseError as e:
            logging.debug(e)
            return {"message": "Database Error - Please try again"}
        except Exception as e:
            logging.debug(e)
            return {"message": "Error - Please try again"}
        
    def delete_content(self, content:str) -> dict:
        

        query = f"DELETE FROM {self.scratch_pad} WHERE content = ?;"
        try:
            self.conn_cursor.execute(query, (content))
            self._commit_data()
            return {"message": f"Note successfully deleted.", "state": True}
        except sqlite3.DatabaseError as e:
            logging.debug(e)
            return {"message": "Database Error - Please try again", "state": False}
        except Exception as e:
            logging.debug(e)
            return {"message": "Error - Please try again", "state": False}
        

if __name__ == "__main__":
    scratch_pad = ScratchPad()

    logging.debug(scratch_pad.get_all_content())

    res = scratch_pad.add_content("To be or not to be? That is the question. Violence is the answer.")
    print(res)

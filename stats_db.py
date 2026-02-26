import sqlite3
from pathlib import Path
import logging
from datetime import datetime, timedelta
logging.basicConfig(level=logging.DEBUG)

class Stats:

    def __init__(self):
        self.db_path = self.db_path = Path(__file__).parent / "lyrical_lab.db"
        self.conn = sqlite3.connect(self.db_path)
        self.conn_cursor = self.conn.cursor()
        self.stats = "stats"
        self.local_id = 1 #default

    def _commit_data(self):
        """Commits data to data base (does not close connection)"""
        self.conn.commit()

    def get_stats(self) -> list | dict:
        """
        Docstring for get_stats
        
        :param self: Description
        :return: stats info ('id', 'writing time', 'sessions', 'created_at', 'local_profile_id')
        :rtype: list | dict
        """

        query = f"""SELECT * FROM {self.stats};"""

        try:
            self.conn_cursor.execute(query)
            stats_data = self.conn_cursor.fetchall()
            return stats_data
        except sqlite3.DatabaseError as e:
            logging.debug(e)
            return {"message": "Database Error - Please try again", "state": False}
        except Exception as e:
            logging.debug(e)
            return {"message": "Error - Please try again", "state": False}
        
    def get_res_stats(self) -> tuple:
        
        query = f""" SELECT * from {self.stats} ORDER by created_at DESC;"""

        try:
            self.conn_cursor.execute(query)
            stats_data = self.conn_cursor.fetchone()
            return stats_data
        except sqlite3.DatabaseError as e:
            logging.debug(e)
            return {"message": "Database Error - Please try again", "state": False}
        except Exception as e:
            logging.debug(e)
            return {"message": "Error - Please try again", "state": False}

    def add_session(self, session):
        
        date_today = datetime.now().date()
        if self._today_stats():
            #session exists
            session += 1
            query = f"""UPDATE stats
set sessions = ? WHERE created_at = "{date_today}";"""
            try:
                self.conn_cursor.execute(query, (session,))
                self._commit_data()
                return {"message": "Session successfully updated", "status": True, "new_ses": session}
            except sqlite3.DatabaseError as e:
                logging.debug(e)
                return {"message": "Database Error - Please try again", "state": False}
            except Exception as e:
                logging.debug(e)
                return {"message": "Error - Please try again", "state": False}
        else:
            #create new session
            query = f"""INSERT INTO stats ("writing time", "sessions", "created_at", "local_profile_id") VALUES (
	?, ?, ?, ?
);"""
            try:
                self.conn_cursor.execute(query, (0, 1, date_today, self.local_id))
                self._commit_data()
                return {"message": "Session successfully created", "status": True, "new_ses": 1}
            except sqlite3.DatabaseError as e:
                logging.debug(e)
                return {"message": "Database Error - Please try again", "state": False}
            except Exception as e:
                logging.debug(e)
                return {"message": "Error - Please try again", "state": False}

    def add_writing_time(self, seconds):
       
        date_today = datetime.now().date()
        if self._today_stats():
            #writing sessions exists
            query = f"""UPDATE stats
set 'writing time' = ? WHERE created_at = "{date_today}";"""
            seconds = seconds + self.get_writing_time()
            try:
                self.conn_cursor.execute(query, (seconds,))
                self._commit_data()
                return {"message": "Writing time updated", "status": True, "writing_time": seconds}
            except sqlite3.DatabaseError as e:
                logging.debug(e)
                return {"message": "Database Error - Please try again", "state": False}
            except Exception as e:
                logging.debug(e)
                return {"message": "Error - Please try again", "state": False}
        else:
            #create new writing time
            query = f"""INSERT INTO stats ("writing time", "sessions", "created_at", "local_profile_id") VALUES (
	?, ?, ?, ?
);"""
            try:
                self.conn_cursor.execute(query, (seconds, 0, date_today, self.local_id))
                self._commit_data()
                return {"message": "Writing successfully added", "status": True, "writing_time": seconds}
            except sqlite3.DatabaseError as e:
                logging.debug(e)
                return {"message": "Database Error - Please try again", "state": False}
            except Exception as e:
                logging.debug(e)
                return {"message": "Error - Please try again", "state": False}


    def get_writing_time(self) -> int:
        
        date_today = datetime.now().date()
        query = f"SELECT * FROM {self.stats} WHERE created_at = '{date_today}';"

        try:
            self.conn_cursor.execute(query)
            writing_time = self.conn_cursor.fetchone()
            return writing_time[1]
        except sqlite3.DatabaseError as e:
            logging.debug(e)
            return 0
        except Exception as e:
            logging.debug(e)
            return 0
        
    def _today_stats(self) -> bool | dict:
        """
        Docstring for today_stats
        Checks if the session for today's date exits.
        """

        date_today = datetime.now().date()
        query = f"""SELECT * FROM {self.stats}
WHERE created_at = "{date_today}";"""
        try:
            self.conn_cursor.execute(query)
            session_exists = self.conn_cursor.fetchone()
            if session_exists:
                return True
            else:
                return False
        except sqlite3.DatabaseError as e:
            logging.debug(e)
            return {"message": "Database Error - Please try again", "state": False}
        except Exception as e:
            logging.debug(e)
            return {"message": "Error - Please try again", "state": False}


        
if __name__ == "__main__":
    from datetime import datetime, timedelta
    stats = Stats()
    res  = stats.get_stats()
    print(res)

    
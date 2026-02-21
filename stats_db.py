import sqlite3
from pathlib import Path
import logging
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
        
        query = f"""SELECT * FROM {self.stats};"""

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


        
if __name__ == "__main__":
    from datetime import datetime, timedelta
    stats = Stats()

    data = stats.get_stats()
    print(data)
    # one_week_ago = datetime.now() - timedelta(days=7)
    # print(one_week_ago)

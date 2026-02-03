import sqlite3
from pathlib import Path
import logging
logging.basicConfig(level=logging.DEBUG)

class Themes():
    """A class that deals with theme related stuff."""

    def __init__(self):
        self.db_path = Path(__file__).parent / "lyrical_lab.db"
        self.conn = sqlite3.connect(self.db_path)
        self.conn_cursor = self.conn.cursor()
        self.themes_table_name = 'themes'

    def _commit_data(self):
        """Commits data to the data base (does not close connection)"""
        self.conn.commit()

    def get_theme_mode(self, theme:str) -> str:
        """Get theme"""

        query = f"""SELECT {theme} from {self.themes_table_name} 
                    WHERE id = 1;"""
        try:
            self.conn_cursor.execute(query)
            theme_mode = self.conn_cursor.fetchone()[0]
            # logging.debug(theme_mode)
            return theme_mode
        except Exception as e:
            logging.debug(f"An error occurred {e}")
    
    def insert_chosen_theme(self, theme:str):
        """Save chosen theme"""

        query = f"""UPDATE {self.themes_table_name}
                    SET "chosen theme" = ? WHERE id = 1;"""
        try:
            self.conn_cursor.execute(query, (theme,))
            self._commit_data()
            return
        except Exception as e:
            logging.debug(f"An error occurred: {e}")
    
    def get_chosen_theme(self) -> str:
        """Get the chosen theme"""

        query = f"""SELECT "chosen theme" FROM {self.themes_table_name}
                    WHERE ID = 1;"""
        try:
            self.conn_cursor.execute(query)
            mode = self.conn_cursor.fetchone()[0]
            # logging.debug(mode)
            return mode
        except Exception as e:
            logging.debug(f'An error occurred: {e}')
    


if __name__ == "__main__":
    themes = Themes()
    # themes.get_theme_mode("neutral")
    # themes.insert_chosen_theme("neutral")
    themes.get_chosen_theme()

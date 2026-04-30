import sqlite3
from pathlib import Path
import logging
logging.basicConfig(level=logging.DEBUG)


class MigrationTable():
    
    def __init__(self):
        self.db_path = Path(__file__).parent / "lyrical_lab.db"
        self.conn = sqlite3.connect(self.db_path)
        self.conn_cursor = self.conn.cursor()
        self.migration_table_name = 'migration'

    def _commit_data(self):
        """Commits data to the data base (does not close connection)"""
        self.conn.commit() 


    def create_migration_table(self):
        """Creates the migration table if it does not exist"""

        query = f"""CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );"""
        try:
            self.conn_cursor.execute(query)
            self._commit_data()
            return
        except Exception as e:
            logging.debug(f"An error occurred: {e}")

    def store_app_version(self, version:str = "1.0.0"):
        """Stores the app version in the migration table"""

        query = f"""INSERT OR REPLACE INTO meta (key, value)
                    VALUES ('app_version', '{version}');"""
        try:
            self.conn_cursor.execute(query)
            self._commit_data()
            return
        except Exception as e:
            logging.debug(f"An error occurred: {e}")

    def get_app_version(self) -> str:
        """Gets the app version from the migration table"""

        query = f"""SELECT value FROM meta WHERE key = 'app_version';"""
        try:    
            self.conn_cursor.execute(query)
            version = self.conn_cursor.fetchone()[0]
            return version  
        except Exception as e:
            logging.debug(f"An error occurred: {e}")        
    
    def create_migration_table_if_not_exists(self):
        """Creates the migration table if it does not exist and stores the app version"""

        self.create_migration_table()
        if not self.get_app_version():
            self.store_app_version()
    
if __name__ == "__main__":
    migration_table = MigrationTable()
    migration_table.create_migration_table_if_not_exists()
    print(migration_table.get_app_version())
    
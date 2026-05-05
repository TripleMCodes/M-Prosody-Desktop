import sqlite3
from pathlib import Path
import logging
import shutil

logging.basicConfig(level=logging.DEBUG)


class MigrationManager:
    def __init__(self, db_name="lyrical_lab.db"):
        self.db_path = Path(__file__).parent / db_name
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    # -------------------------
    # 🧱 Setup
    # -------------------------
    def initialize(self):
        """Create required tables"""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
            """)

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id TEXT PRIMARY KEY
                );
            """)

    # -------------------------
    # 🧠 Metadata (optional)
    # -------------------------
    def set_db_version(self, version: str):
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO meta (key, value)
                VALUES ('db_version', ?)
            """, (version,))

    def get_db_version(self) -> str | None:
        cur = self.conn.execute("""
            SELECT value FROM meta WHERE key='db_version'
        """)
        row = cur.fetchone()
        return row["value"] if row else None

    # -------------------------
    # 🔁 Migration tracking
    # -------------------------
    def get_applied_migrations(self):
        cur = self.conn.execute("SELECT id FROM migrations")
        return {row["id"] for row in cur.fetchall()}

    def apply_migration(self, migration):
        logging.debug(f"Applying migration: {migration['id']}")

        try:
            with self.conn:  # ✅ atomic transaction
                self.conn.executescript(migration["sql"])
                self.conn.execute(
                    "INSERT INTO migrations (id) VALUES (?)",
                    (migration["id"],)
                )
        except Exception as e:
            logging.error(f"Migration failed: {migration['id']} → {e}")
            raise  # crash early, don't corrupt state

    # -------------------------
    # 🧯 Safety
    # -------------------------
    def backup(self):
        backup_path = self.db_path.with_suffix(".backup.db")
        shutil.copy(self.db_path, backup_path)
        logging.debug(f"Backup created at: {backup_path}")

    # -------------------------
    # 🚀 Migration runner
    # -------------------------
    def migrate(self, migrations, app_version=None):
        self.initialize()

        applied = self.get_applied_migrations()

        # Backup BEFORE any changes
        if self.db_path.exists():
            self.backup()

        for migration in migrations:
            if migration["id"] not in applied:
                self.apply_migration(migration)

        # Optional: store app version AFTER successful migration
        if app_version:
            self.set_db_version(app_version)


# -------------------------
# 📦 Define migrations
# -------------------------
MIGRATIONS = [
    {
        "id": "001_create_notes",
        "sql": """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY,
                content TEXT
            );
        """
    },
    {
        "id": "002_add_created_at",
        "sql": """
            ALTER TABLE notes ADD COLUMN created_at TEXT;
        """
    },
    {
        "id": "003_add_updated_at",
        "sql": """
            ALTER TABLE notes ADD COLUMN updated_at TEXT;
        """
    },
]


if __name__ == "__main__":
    manager = MigrationManager()

    manager.migrate(
        MIGRATIONS,
        app_version="1.0.0"
    )

    print("DB Version:", manager.get_db_version())
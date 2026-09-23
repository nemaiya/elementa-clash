from sqlite3 import Connection, Cursor


import sqlite3

class LocalDatabase:
    def __init__(self, db_path: str = "elementa_local.db") -> None:
        # check_same_thread=False allows background threads to access the DB if needed later
        self.conn: Connection = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor: Cursor = self.conn.cursor()
        self._init_tables()

    def _init_tables(self) -> None:
        _ = self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_cache (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                lastAuth TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def save_user_auth_data(self, username: str, user_id: str, password_hash: str, timestamp: str) -> None:
        """Caches the flattened user data locally for offline/instant verification."""
        _ = self.cursor.execute("""
            INSERT OR REPLACE INTO user_cache (id, username, password, lastAuth)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, password_hash, timestamp))
        self.conn.commit()

    def verify_credentials(self, username: str, password_hash: str) -> tuple[bool, dict[str, str] | None]:
        """
        Checks local cache. Returns a tuple: (Success Boolean, Flat User Data Dictionary)
        """
        _ = self.cursor.execute(
            "SELECT id, username, password, lastAuth FROM user_cache WHERE username = ?",
            (username,)
        )
        row = self.cursor.fetchone()
        
        if row:
            cached_id, cached_user, cached_pass, cached_auth = row
            if cached_pass == password_hash:
                flat_user_data = {
                    "id": cached_id,
                    "username": cached_user,
                    "password": cached_pass,
                    "lastAuth": cached_auth
                }
                return True, flat_user_data
                
        return False, None

    def update_last_auth(self, username: str, timestamp: str) -> None:
        """Updates the local login timestamp."""
        _ = self.cursor.execute(
            "UPDATE user_cache SET lastAuth = ? WHERE username = ?",
            (timestamp, username)
        )
        self.conn.commit()
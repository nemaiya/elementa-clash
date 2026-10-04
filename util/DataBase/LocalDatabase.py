from sqlite3 import Connection, Cursor
from pathlib import Path

parent_dir: Path = Path(__file__).parent
db_path: Path = parent_dir / "elementa_local.db"

import sqlite3

class LocalDatabase:
    def __init__(self, db_path: Path = db_path) -> None:
        # Initialize the SQLite database connection and cursor, and create necessary tables if they don't exist.
        self.conn: Connection = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor: Cursor = self.conn.cursor()
        self._init_tables()

    def _init_tables(self) -> None:
        # Create the user_cache table to store the user's authentication data
        _ = self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_cache (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                lastAuth TEXT NOT NULL
            )
        """)

        # Create the local_settings table to store game settings like music volume, SFX volume, FPS, and font.
        _ = self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS local_settings (
                id INTEGER PRIMARY KEY,
                music_vol REAL,
                sfx_vol REAL,
                fps TEXT,
                font TEXT
                )
        """)

        # Execute the commit to save the changes to the database.
        self.conn.commit()
    
    def save_settings(self, music_vol: float, sfx_vol: float, fps: str, font: str) -> None:
        """Saves the local game settings."""
        # We use id=1 so it always overwrites the same row instead of making new ones
        _ = self.cursor.execute("""
            INSERT OR REPLACE INTO local_settings (id, music_vol, sfx_vol, fps, font)
            VALUES (1, ?, ?, ?, ?)
        """, (music_vol, sfx_vol, fps, font))
        # Execute the commit to save the changes to the database.
        self.conn.commit()

    def get_settings(self) -> dict[str, float | str] | None:
        # Retrieves the saved game settings and returns them as a dictionary."""
        _ = self.cursor.execute(
            "SELECT music_vol, sfx_vol, fps, font FROM local_settings WHERE id = 1"
        )

        row = self.cursor.fetchone()
        
        if row:
            # Unpack the row and return it in the format BasePage expects
            music_vol, sfx_vol, fps, font = row
            return {"music_vol": music_vol,"sfx_vol": sfx_vol,"fps": fps,"font": font}
            
        # Returns None if no settings have been saved yet
        return None

    def save_user_auth_data(self, username: str, user_id: str, password_hash: str, timestamp: str) -> None:
        """Caches the flattened user data locally for offline/instant verification."""
        _ = self.cursor.execute("""
            INSERT OR REPLACE INTO user_cache (id, username, password, lastAuth)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, password_hash, timestamp))
        self.conn.commit()

    def verify_credentials(self, username: str, password_hash: str) -> tuple[bool, dict[str, str] | None]:
        # Retrieve the user's authentication data from the local cache
        _ = self.cursor.execute(
            "SELECT id, username, password, lastAuth FROM user_cache WHERE username = ?",
            (username,)
        )
        # Fetch the user's authentication data from the local cache
        row = self.cursor.fetchone()
        # Check if the user's authentication data is found
        if row:
            cached_id, cached_user, cached_pass, cached_auth = row
            if cached_pass == password_hash: # Compare the password hash with the user's authentication data
                flat_user_data = { "id": cached_id, "username": cached_user, "password": cached_pass, "lastAuth": cached_auth }
                return True, flat_user_data # Return True if the password hash matches the user's authentication data
                
        return False, None # Return False if the password hash does not match the user's authentication data

    def update_last_auth(self, username: str, timestamp: str) -> None:
        """Updates the local login timestamp."""
        _ = self.cursor.execute(
            "UPDATE user_cache SET lastAuth = ? WHERE username = ?",
            (timestamp, username)
        )
        self.conn.commit()
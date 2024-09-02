import sqlite3


class DAO:
    def __init__(self):
        self.conn = sqlite3.connect("youtube_downloader.db")
        self.cursor = self.conn.cursor()

        # Create the playlists table if it doesn't exist
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS playlists (
                playlist_id TEXT PRIMARY KEY,
                last_downloaded_id TEXT
            )
        """
        )
        self.conn.commit()

        # Define destructor to close the connection
        def __del__(self):
            if hasattr(self, "conn"):
                self.conn.close()

    def get_last_downloaded_id(self, playlist_id: str) -> str | None:
        cursor = self.conn.cursor()
        cursor.execute("SELECT last_downloaded_id FROM playlists WHERE playlist_id = ?", (playlist_id,))
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            return None

    def update_last_downloaded_id(self, playlist_id: str, last_downloaded_id: str) -> None:
        self.cursor.execute(
            """
            INSERT OR REPLACE INTO playlists (playlist_id, last_downloaded_id)
            VALUES (?, ?)
            """,
            (playlist_id, last_downloaded_id),
        )
        self.conn.commit()

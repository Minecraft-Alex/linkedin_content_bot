import sqlite3
import logging
from typing import Optional
from datetime import datetime

class Database:
    def __init__(self, db_path: str = "posts.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database and create tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS posted_articles (
                        url TEXT PRIMARY KEY,
                        title TEXT,
                        posted_at TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception as e:
            logging.error(f"Error initializing database: {str(e)}")
            raise

    def is_article_posted(self, url: str) -> bool:
        """Check if an article has already been posted."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT url FROM posted_articles WHERE url = ?", (url,))
                return cursor.fetchone() is not None
        except Exception as e:
            logging.error(f"Error checking article status: {str(e)}")
            return False

    def mark_article_posted(self, url: str, title: str):
        """Mark an article as posted."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO posted_articles (url, title, posted_at) VALUES (?, ?, ?)",
                    (url, title, datetime.now())
                )
                conn.commit()
        except Exception as e:
            logging.error(f"Error marking article as posted: {str(e)}")
            raise

    def get_last_posted_article(self) -> Optional[tuple]:
        """Get the most recently posted article."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT url, title, posted_at FROM posted_articles ORDER BY posted_at DESC LIMIT 1"
                )
                return cursor.fetchone()
        except Exception as e:
            logging.error(f"Error getting last posted article: {str(e)}")
            return None

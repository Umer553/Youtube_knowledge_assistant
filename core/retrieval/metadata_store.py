"""
Metadata Store (SQLite)
Stores video metadata, sentiment analysis results, and chat history.
Complements the vector store with structured data that doesn't need
vector search (e.g., comment counts, sentiment scores, video titles).
"""

import sqlite3
import json
from typing import Optional
from pathlib import Path

from app.config import SQLITE_PATH


class MetadataStore:
    """SQLite-backed metadata store for the application."""

    def __init__(self, db_path: str = str(SQLITE_PATH)):
        self.db_path = db_path
        self._init_tables()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Create tables if they don't exist."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                title TEXT,
                channel TEXT,
                description TEXT,
                duration TEXT,
                published_at TEXT,
                view_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                thumbnail_url TEXT,
                transcript_source TEXT,
                chunk_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sentiment_summaries (
                video_id TEXT PRIMARY KEY,
                total_comments INTEGER,
                positive_count INTEGER,
                negative_count INTEGER,
                neutral_count INTEGER,
                average_compound REAL,
                themes_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos(video_id)
            );

            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                video_context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        conn.close()

    # ── Video Methods ──────────────────────────────────────

    def save_video(self, video_id: str, **kwargs):
        """Insert or update a video record."""
        conn = self._get_conn()
        cursor = conn.cursor()

        # Build dynamic SQL for provided fields
        fields = ['video_id'] + list(kwargs.keys())
        placeholders = ', '.join(['?'] * len(fields))
        updates = ', '.join(f"{k}=excluded.{k}" for k in kwargs.keys())

        values = [video_id] + list(kwargs.values())

        sql = f"""
            INSERT INTO videos ({', '.join(fields)})
            VALUES ({placeholders})
            ON CONFLICT(video_id) DO UPDATE SET {updates}
        """

        cursor.execute(sql, values)
        conn.commit()
        conn.close()

    def get_video(self, video_id: str) -> Optional[dict]:
        """Get video metadata by ID."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos WHERE video_id = ?", (video_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_videos(self) -> list[dict]:
        """Get all stored videos."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def delete_video(self, video_id: str):
        """Delete a video and its associated data."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sentiment_summaries WHERE video_id = ?", (video_id,))
        cursor.execute("DELETE FROM videos WHERE video_id = ?", (video_id,))
        conn.commit()
        conn.close()

    # ── Sentiment Methods ──────────────────────────────────

    def save_sentiment(self, video_id: str, summary) -> None:
        """Save a SentimentSummary to the database."""
        conn = self._get_conn()
        cursor = conn.cursor()

        themes_json = json.dumps(summary.themes) if summary.themes else "[]"

        cursor.execute("""
            INSERT OR REPLACE INTO sentiment_summaries
            (video_id, total_comments, positive_count, negative_count,
             neutral_count, average_compound, themes_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            video_id,
            summary.total_comments,
            summary.positive_count,
            summary.negative_count,
            summary.neutral_count,
            summary.average_compound,
            themes_json,
        ))

        conn.commit()
        conn.close()

    def get_sentiment(self, video_id: str) -> Optional[dict]:
        """Get sentiment summary for a video."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sentiment_summaries WHERE video_id = ?", (video_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            result = dict(row)
            result['themes'] = json.loads(result.get('themes_json', '[]'))
            return result
        return None

    # ── Chat History Methods ───────────────────────────────

    def save_chat_message(self, session_id: str, role: str, content: str, video_context: str = ""):
        """Save a chat message."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_history (session_id, role, content, video_context)
            VALUES (?, ?, ?, ?)
        """, (session_id, role, content, video_context))
        conn.commit()
        conn.close()

    def get_chat_history(self, session_id: str, limit: int = 50) -> list[dict]:
        """Get chat history for a session."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content, created_at 
            FROM chat_history 
            WHERE session_id = ?
            ORDER BY created_at ASC
            LIMIT ?
        """, (session_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

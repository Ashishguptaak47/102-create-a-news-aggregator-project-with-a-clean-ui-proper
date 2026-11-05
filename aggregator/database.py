import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

DB_PATH = os.environ.get("NEWS_DB_PATH", "news.db")


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL DEFAULT 'General',
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            title TEXT NOT NULL,
            link TEXT NOT NULL UNIQUE,
            summary TEXT,
            published_at TEXT,
            image_url TEXT,
            category TEXT NOT NULL,
            is_bookmarked INTEGER DEFAULT 0,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_id) REFERENCES sources (id) ON DELETE CASCADE
        )
        """)
        conn.commit()
        seed_default_sources(conn)


def seed_default_sources(conn: sqlite3.Connection) -> None:
    defaults = [
        ("Hacker News", "https://news.ycombinator.com/rss", "Tech"),
        ("BBC Tech", "http://feeds.bbci.co.uk/news/technology/rss.xml", "Tech"),
        ("Nature Science", "https://www.nature.com/nature.rss", "Science"),
        ("BBC World", "http://feeds.bbci.co.uk/news/world/rss.xml", "World"),
    ]
    cursor = conn.cursor()
    for name, url, category in defaults:
        cursor.execute(
            "INSERT OR IGNORE INTO sources (name, url, category) VALUES (?, ?, ?)",
            (name, url, category),
        )
    conn.commit()


def add_source(name: str, url: str, category: str = "General") -> Optional[int]:
    with get_db_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sources (name, url, category) VALUES (?, ?, ?)",
                (name.strip(), url.strip(), category.strip()),
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None


def get_sources() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM sources WHERE active = 1 ORDER BY name ASC").fetchall()
        return [dict(row) for row in rows]


def upsert_article(article_data: Dict[str, Any]) -> bool:
    with get_db_connection() as conn:
        try:
            conn.execute(
                """
                INSERT INTO articles (source_id, title, link, summary, published_at, image_url, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(link) DO UPDATE SET
                    title = excluded.title,
                    summary = COALESCE(excluded.summary, articles.summary),
                    image_url = COALESCE(excluded.image_url, articles.image_url)
                """,
                (
                    article_data.get("source_id"),
                    article_data["title"],
                    article_data["link"],
                    article_data.get("summary", ""),
                    article_data.get("published_at", datetime.utcnow().isoformat()),
                    article_data.get("image_url"),
                    article_data.get("category", "General"),
                ),
            )
            conn.commit()
            return True
        except Exception:
            return False


def get_articles(
    category: Optional[str] = None,
    search: Optional[str] = None,
    bookmarked_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    query = """
    SELECT a.*, s.name as source_name
    FROM articles a
    LEFT JOIN sources s ON a.source_id = s.id
    WHERE 1=1
    """
    params: List[Any] = []

    if category and category.lower() != "all":
        query += " AND LOWER(a.category) = LOWER(?)"
        params.append(category)

    if search:
        query += " AND (LOWER(a.title) LIKE ? OR LOWER(a.summary) LIKE ?)"
        kw = f"%{search.lower()}%"
        params.extend([kw, kw])

    if bookmarked_only:
        query += " AND a.is_bookmarked = 1"

    query += " ORDER BY a.published_at DESC, a.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def toggle_bookmark(article_id: int) -> Optional[int]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        row = cursor.execute("SELECT is_bookmarked FROM articles WHERE id = ?", (article_id,)).fetchone()
        if not row:
            return None
        new_val = 0 if row["is_bookmarked"] else 1
        cursor.execute("UPDATE articles SET is_bookmarked = ? WHERE id = ?", (new_val, article_id))
        conn.commit()
        return new_val


def toggle_read(article_id: int) -> Optional[int]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        row = cursor.execute("SELECT is_read FROM articles WHERE id = ?", (article_id,)).fetchone()
        if not row:
            return None
        new_val = 0 if row["is_read"] else 1
        cursor.execute("UPDATE articles SET is_read = ? WHERE id = ?", (new_val, article_id))
        conn.commit()
        return new_val

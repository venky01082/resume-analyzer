"""
Database Connection & Storage Adapter
Supports PostgreSQL / Supabase via DATABASE_URL and local zero-config SQLite fallback.
Provides thread-safe connections, query helpers, and JSON backward-compatibility.
"""

import os
import json
import sqlite3
import threading
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

# Default SQLite database path
DEFAULT_SQLITE_PATH = os.path.join(os.path.dirname(__file__), "job_assistant.db")

_db_lock = threading.Lock()
_file_locks: Dict[str, threading.Lock] = {}


def _get_file_lock(filepath: str) -> threading.Lock:
    with _db_lock:
        if filepath not in _file_locks:
            _file_locks[filepath] = threading.Lock()
        return _file_locks[filepath]


def get_database_url() -> Optional[str]:
    """Retrieve database connection URL from environment or Streamlit secrets."""
    # 1. Check OS environment variable
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")
    if db_url and db_url.strip():
        return db_url.strip()

    # 2. Check Streamlit secrets if available
    if HAS_STREAMLIT:
        try:
            if "DATABASE_URL" in st.secrets:
                return str(st.secrets["DATABASE_URL"]).strip()
            if "database" in st.secrets and "url" in st.secrets["database"]:
                return str(st.secrets["database"]["url"]).strip()
        except Exception:
            pass

    return None


def is_postgres() -> bool:
    """Return True if a PostgreSQL/Supabase database URL is configured."""
    url = get_database_url()
    return bool(url and (url.startswith("postgres://") or url.startswith("postgresql://")))


@contextmanager
def get_db_connection():
    """
    Context manager that yields an active database connection and automatically
    commits transactions on success, or rolls back on exception.
    """
    db_url = get_database_url()

    if is_postgres():
        try:
            # Handle SQLAlchemy or psycopg2 postgres connection
            import psycopg2
            from psycopg2.extras import RealDictCursor

            conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
            return
        except Exception as pg_err:
            # If psycopg2 fails to connect, fallback to SQLite and log
            print(f"[DB Warning] PostgreSQL connection failed ({pg_err}). Falling back to local SQLite.")

    # Local SQLite fallback
    with _db_lock:
        conn = sqlite3.connect(DEFAULT_SQLITE_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def execute_query(sql: str, params: Tuple = ()) -> List[Dict[str, Any]]:
    """Execute a SELECT query and return list of dict rows."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        if not rows:
            return []
        if isinstance(rows[0], dict):
            return [dict(r) for r in rows]
        # SQLite Row
        return [dict(r) for r in rows]


def execute_mutation(sql: str, params: Tuple = ()) -> int:
    """Execute an INSERT, UPDATE, or DELETE and return rowcount."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.rowcount


# =========================================================
# BACKWARD COMPATIBILITY: JSON File Reading & Writing
# =========================================================

def read_json_file(filepath: str, default: Any = None) -> Any:
    """Safely read a JSON file with thread safety."""
    if default is None:
        default = {}
    if not os.path.exists(filepath):
        return default

    lock = _get_file_lock(filepath)
    with lock:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return default
                return json.loads(content)
        except Exception:
            return default


def write_json_file(filepath: str, data: Any) -> bool:
    """Safely write data to a JSON file using atomic replacement."""
    lock = _get_file_lock(filepath)
    with lock:
        tmp_file = f"{filepath}.tmp"
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            if os.path.exists(filepath):
                os.replace(tmp_file, filepath)
            else:
                os.rename(tmp_file, filepath)
            return True
        except Exception as e:
            if os.path.exists(tmp_file):
                try:
                    os.remove(tmp_file)
                except Exception:
                    pass
            print(f"Error writing to {filepath}: {e}")
            return False
